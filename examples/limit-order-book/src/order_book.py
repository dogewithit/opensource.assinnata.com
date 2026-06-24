"""A continuous limit order book with price-time (FIFO) priority.

Design notes
------------
* Prices are :class:`decimal.Decimal`. Using ``Decimal`` keeps price comparisons
  and the executed trade price exact, so there is no float drift on values like
  ``0.1 + 0.2``. Quantities are plain ``int`` (think shares/contracts/lots).
* Matching follows the classic continuous-auction rules:
    - **Price priority**: the best price on the resting side fills first
      (highest bid, lowest ask).
    - **Time priority**: within one price level, the order that arrived first
      fills first (FIFO).
    - Trades print at the **resting (maker)** order's price, never the
      aggressor's limit.
* The engine is deterministic and self-contained: no network, no wall-clock
  reads, no randomness. "Time" is an internal monotonic sequence counter, so a
  given sequence of calls always produces the same fills.

This is a teaching-grade engine. Per price level it keeps a FIFO ``deque`` and
selects the best level with a sorted-key scan, which is simple and correct. A
production engine would index price levels in a heap or an order-statistics tree
for O(log n) best-price access; the matching semantics would be identical.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import count
from typing import Deque, Dict, Iterator, List, Optional, Union

# A price may be supplied as int, str, or Decimal; it is normalised to Decimal.
PriceLike = Union[int, str, Decimal]

BUY = "buy"
SELL = "sell"
_SIDES = (BUY, SELL)


def _to_price(value: PriceLike) -> Decimal:
    """Coerce a user-supplied price into an exact ``Decimal``.

    ``float`` is intentionally rejected: passing ``0.1`` would smuggle binary
    rounding error into the book. Callers should use ``Decimal`` or a string.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        raise ValueError(
            "price must be int, str or Decimal, not float (use Decimal('1.5'))"
        )
    return Decimal(str(value))


@dataclass(frozen=True)
class Fill:
    """One executed trade between a maker (resting) and a taker (aggressor).

    The trade executes at ``price``, which is always the maker's resting price.
    """

    maker_id: str
    taker_id: str
    price: Decimal
    qty: int


# ``Trade`` is a common alias for the same concept; expose both names.
Trade = Fill


@dataclass
class Order:
    """A single order. ``qty`` is the *remaining* (unfilled) quantity."""

    order_id: str
    side: str
    price: Decimal  # for market orders this is a sentinel and unused for resting
    qty: int
    seq: int  # arrival sequence, drives time priority

    @property
    def is_buy(self) -> bool:
        return self.side == BUY


class OrderBook:
    """A price-time-priority continuous limit order book.

    Public API
    ----------
    add_limit_order(side, price, qty, order_id) -> list[Fill]
    add_market_order(side, qty, order_id)        -> list[Fill]
    cancel(order_id)                             -> bool
    best_bid() / best_ask()                      -> Decimal | None
    spread()                                     -> Decimal | None
    """

    def __init__(self) -> None:
        # price -> FIFO queue of resting orders at that price.
        self._bids: Dict[Decimal, Deque[Order]] = {}
        self._asks: Dict[Decimal, Deque[Order]] = {}
        # order_id -> resting Order, for O(1) cancel lookups.
        self._index: Dict[str, Order] = {}
        # Monotonic arrival counter. This is the engine's notion of "time"; it
        # never reads the wall clock, which keeps replays deterministic.
        self._seq: Iterator[int] = count()

    # ----------------------------------------------------------------- helpers
    def _book_for(self, side: str) -> Dict[Decimal, Deque[Order]]:
        return self._bids if side == BUY else self._asks

    @staticmethod
    def _validate(side: str, qty: int) -> None:
        if side not in _SIDES:
            raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
        if not isinstance(qty, int) or isinstance(qty, bool):
            raise ValueError(f"qty must be an int, got {qty!r}")
        if qty <= 0:
            raise ValueError(f"qty must be > 0, got {qty}")

    def _best_resting_price(
        self, book: Dict[Decimal, Deque[Order]]
    ) -> Optional[Decimal]:
        """Best price on a book side: highest for bids, lowest for asks.

        Empty price levels are pruned lazily, so any non-empty level is live.
        """
        if not book:
            return None
        # bids: best == max price; asks: best == min price.
        if book is self._bids:
            return max(book)
        return min(book)

    def _rest(self, order: Order) -> None:
        """Place an order's remaining quantity onto the book (FIFO at its price)."""
        book = self._book_for(order.side)
        book.setdefault(order.price, deque()).append(order)
        self._index[order.order_id] = order

    # ----------------------------------------------------------------- matching
    def _match(
        self,
        taker: Order,
        limit_price: Optional[Decimal],
    ) -> List[Fill]:
        """Match ``taker`` against the opposite side, best price first.

        ``limit_price`` is the worst acceptable price for the taker, or ``None``
        for a market order (accept any price). Returns the fills produced and
        mutates ``taker.qty`` down to the unfilled remainder.
        """
        opposite = self._asks if taker.is_buy else self._bids
        fills: List[Fill] = []

        while taker.qty > 0 and opposite:
            best_price = self._best_resting_price(opposite)
            assert best_price is not None  # opposite is non-empty here

            if limit_price is not None:
                # A buy crosses asks priced <= its limit; a sell crosses bids
                # priced >= its limit. Otherwise we stop: nothing more crosses.
                crosses = (
                    best_price <= limit_price
                    if taker.is_buy
                    else best_price >= limit_price
                )
                if not crosses:
                    break

            level = opposite[best_price]
            # FIFO within the level: oldest resting order fills first.
            while taker.qty > 0 and level:
                maker = level[0]
                traded = min(taker.qty, maker.qty)
                # Trade prints at the maker's (resting) price.
                fills.append(
                    Fill(
                        maker_id=maker.order_id,
                        taker_id=taker.order_id,
                        price=maker.price,
                        qty=traded,
                    )
                )
                taker.qty -= traded
                maker.qty -= traded
                if maker.qty == 0:
                    # Fully consumed: drop it and forget its id.
                    level.popleft()
                    self._index.pop(maker.order_id, None)
                # A partially filled maker keeps its place at the head of the
                # queue, preserving its time priority.

            if not level:
                # Prune the emptied price level so best-price scans stay correct.
                del opposite[best_price]

        return fills

    # ------------------------------------------------------------------- public
    def add_limit_order(
        self, side: str, price: PriceLike, qty: int, order_id: str
    ) -> List[Fill]:
        """Submit a limit order. Returns the fills it generated.

        It matches against any crossing resting orders (best price first, FIFO
        within a level), then rests any unfilled remainder on the book.
        """
        self._validate(side, qty)
        price_d = _to_price(price)
        if price_d <= 0:
            raise ValueError(f"price must be > 0, got {price_d}")

        taker = Order(order_id, side, price_d, qty, next(self._seq))
        fills = self._match(taker, limit_price=price_d)
        if taker.qty > 0:
            self._rest(taker)
        return fills

    def add_market_order(self, side: str, qty: int, order_id: str) -> List[Fill]:
        """Submit a market order. Returns the fills it generated.

        It sweeps the opposite side from the best price until filled or the book
        is exhausted, and never rests. If liquidity is insufficient it simply
        fills what it can.
        """
        self._validate(side, qty)
        # Sentinel price; market orders never rest, so it is informational only.
        taker = Order(order_id, side, Decimal(0), qty, next(self._seq))
        return self._match(taker, limit_price=None)

    def cancel(self, order_id: str) -> bool:
        """Remove a resting order. Returns ``True`` if it was found."""
        order = self._index.pop(order_id, None)
        if order is None:
            return False
        book = self._book_for(order.side)
        level = book.get(order.price)
        if level is not None:
            try:
                level.remove(order)
            except ValueError:
                pass
            if not level:
                del book[order.price]
        return True

    # ------------------------------------------------------------- market data
    def best_bid(self) -> Optional[Decimal]:
        """Highest resting buy price, or ``None`` if there are no bids."""
        return self._best_resting_price(self._bids)

    def best_ask(self) -> Optional[Decimal]:
        """Lowest resting sell price, or ``None`` if there are no asks."""
        return self._best_resting_price(self._asks)

    def spread(self) -> Optional[Decimal]:
        """Best ask minus best bid, or ``None`` if either side is empty."""
        bid, ask = self.best_bid(), self.best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid
