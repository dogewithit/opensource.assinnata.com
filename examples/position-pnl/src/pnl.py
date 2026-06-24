"""Weighted-average-cost position and P&L engine.

A :class:`Position` consumes a stream of fills and tracks, the way a trading or
risk system does:

* the signed net ``quantity`` (positive = long, negative = short),
* the ``avg_price`` of the currently open position (its weighted-average cost),
* accumulated ``realized_pnl`` (closed P&L net of fees), and
* on demand, the ``unrealized`` mark-to-market of whatever is still open.

Everything is computed with :class:`decimal.Decimal` so the P&L numbers are
exact: no float drift creeps in across a long sequence of fills. The engine is
pure (no IO, no clock, no randomness), so its behaviour is fully determined by
the fills it is given.

Accounting rules
----------------
* Adding to a position in the same direction updates the weighted-average entry
  price and realizes nothing.
* A fill in the opposite direction closes part or all of the open position and
  realizes P&L on the closed quantity against ``avg_price``::

      long  : realized += closed_qty * (sell_price - avg_price)
      short : realized += closed_qty * (avg_price - buy_price)

  The remaining open quantity keeps its original ``avg_price``.
* If an opposite fill is larger than the open position it **flips** it: the old
  position is closed in full (and realized on), then a new position is opened in
  the new direction for the leftover quantity at the fill price.
* Fees always reduce ``realized_pnl``.
"""

from __future__ import annotations

from decimal import Decimal


# Accept the usual numeric inputs but normalize everything to Decimal internally.
Number = Decimal | int | str


def _to_decimal(value: Number, *, name: str) -> Decimal:
    """Coerce a user-supplied number to Decimal, rejecting junk.

    Going through ``str`` (rather than ``Decimal(float)``) keeps literals like
    ``0.1`` exact instead of binding the binary-float approximation.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):  # bool is an int subclass; almost never intended
        raise ValueError(f"{name} must be numeric, got bool {value!r}")
    if isinstance(value, (int, str)):
        try:
            return Decimal(value)
        except Exception as exc:  # decimal.InvalidOperation and friends
            raise ValueError(f"{name} is not a valid number: {value!r}") from exc
    raise ValueError(f"{name} must be Decimal, int, or str, got {type(value).__name__}")


class Position:
    """Net position and P&L for a single instrument, driven by fills.

    Sign convention: ``quantity > 0`` is long, ``quantity < 0`` is short,
    ``quantity == 0`` is flat. When flat, ``avg_price`` is ``None``.
    """

    def __init__(self) -> None:
        self._quantity: Decimal = Decimal(0)
        # Average cost of the open position. None when flat (no meaningful price).
        self._avg_price: Decimal | None = None
        self._realized_pnl: Decimal = Decimal(0)

    # ------------------------------------------------------------------ #
    # Read-only views
    # ------------------------------------------------------------------ #
    @property
    def quantity(self) -> Decimal:
        """Signed net quantity: positive long, negative short, zero flat."""
        return self._quantity

    @property
    def avg_price(self) -> Decimal | None:
        """Weighted-average cost of the open position, or ``None`` when flat."""
        return self._avg_price

    @property
    def realized_pnl(self) -> Decimal:
        """Cumulative realized P&L, net of all fees applied so far."""
        return self._realized_pnl

    @property
    def is_flat(self) -> bool:
        """True when there is no open position."""
        return self._quantity == 0

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #
    def apply(
        self,
        side: str,
        qty: Number,
        price: Number,
        fee: Number = 0,
    ) -> None:
        """Apply one fill, updating quantity, avg_price and realized_pnl.

        ``side`` is ``"buy"`` or ``"sell"``. ``qty`` and ``price`` must be
        strictly positive; ``fee`` must be non-negative. Fees reduce realized
        P&L regardless of whether the fill opens, adds to, reduces or flips the
        position.
        """
        side = side.lower()
        if side not in ("buy", "sell"):
            raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")

        qty = _to_decimal(qty, name="qty")
        price = _to_decimal(price, name="price")
        fee = _to_decimal(fee, name="fee")

        if qty <= 0:
            raise ValueError(f"qty must be > 0, got {qty}")
        if price <= 0:
            raise ValueError(f"price must be > 0, got {price}")
        if fee < 0:
            raise ValueError(f"fee must be >= 0, got {fee}")

        # Fees are a cost no matter what the fill does to the position.
        self._realized_pnl -= fee

        # Signed quantity of this fill: +qty for a buy, -qty for a sell.
        signed = qty if side == "buy" else -qty

        if self._quantity == 0:
            # Opening a fresh position from flat.
            self._open(signed, price)
            return

        same_direction = (self._quantity > 0) == (signed > 0)
        if same_direction:
            # Add to the open position; reprice the weighted average.
            self._add(signed, price)
            return

        # Opposite direction: this fill reduces, closes, or flips the position.
        open_abs = abs(self._quantity)
        fill_abs = qty
        closing_abs = min(open_abs, fill_abs)

        self._realize_close(closing_abs, price)

        if fill_abs <= open_abs:
            # Pure reduction (or exact close). avg_price of the remainder is
            # unchanged; if we closed it all, go flat.
            self._quantity += signed
            if self._quantity == 0:
                self._avg_price = None
            return

        # Flip: the old position is fully closed, open the leftover in the new
        # direction at the fill price.
        leftover = fill_abs - open_abs
        new_signed = leftover if signed > 0 else -leftover
        self._open(new_signed, price)

    # ------------------------------------------------------------------ #
    # P&L
    # ------------------------------------------------------------------ #
    def unrealized(self, mark_price: Number) -> Decimal:
        """Mark-to-market P&L of the open position against ``mark_price``.

        Zero when flat. Sign follows the position: a long gains when the mark is
        above ``avg_price``, a short gains when it is below.
        """
        if self._quantity == 0 or self._avg_price is None:
            return Decimal(0)
        mark = _to_decimal(mark_price, name="mark_price")
        if mark <= 0:
            raise ValueError(f"mark_price must be > 0, got {mark}")
        # quantity is signed, so this is correct for both longs and shorts.
        return self._quantity * (mark - self._avg_price)

    def total_pnl(self, mark_price: Number) -> Decimal:
        """Realized P&L plus the unrealized mark-to-market at ``mark_price``."""
        return self._realized_pnl + self.unrealized(mark_price)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _open(self, signed_qty: Decimal, price: Decimal) -> None:
        """Open a position from flat; avg_price is just the fill price."""
        self._quantity = signed_qty
        self._avg_price = price

    def _add(self, signed_qty: Decimal, price: Decimal) -> None:
        """Add in the same direction; recompute the weighted-average cost.

        Weighting by absolute quantity keeps the formula identical for longs and
        shorts, then we restore the sign.
        """
        assert self._avg_price is not None  # not flat by construction
        old_abs = abs(self._quantity)
        add_abs = abs(signed_qty)
        new_abs = old_abs + add_abs
        self._avg_price = (self._avg_price * old_abs + price * add_abs) / new_abs
        self._quantity += signed_qty

    def _realize_close(self, closing_abs: Decimal, price: Decimal) -> None:
        """Realize P&L on ``closing_abs`` units closed at ``price``.

        For a long we sell to close (gain when price > avg); for a short we buy
        to close (gain when price < avg). The sign of the open quantity selects
        the right direction.
        """
        assert self._avg_price is not None
        direction = Decimal(1) if self._quantity > 0 else Decimal(-1)
        self._realized_pnl += closing_abs * (price - self._avg_price) * direction

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"Position(quantity={self._quantity}, avg_price={self._avg_price}, "
            f"realized_pnl={self._realized_pnl})"
        )
