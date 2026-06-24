"""Resample a trade stream into fixed-interval OHLCV bars with VWAP.

This is the time-bar builder a market-data platform runs over a tick stream:
each incoming trade is dropped into the time bucket it belongs to, and when a
trade opens a *later* bucket the in-progress bar is closed and emitted.

Design notes a reviewer should know:

* Prices and sizes are kept as ``decimal.Decimal`` internally so the
  volume-weighted average price is exact (no float drift). Inputs may be
  ``int``, ``float`` or ``str`` and are converted via ``str()`` first, which is
  the safe way to build a ``Decimal`` from a float literal.
* Trades are assumed to arrive in non-decreasing timestamp order (as they do off
  an ordered feed). A strictly out-of-order timestamp raises ``ValueError``
  rather than silently corrupting a closed bar.
* Empty buckets are skipped: if no trade lands in some interval, no synthetic
  zero-volume candle is emitted. Bars only exist where trades happened.
* There are no clock calls and no I/O. Every timestamp is supplied by the
  caller, so the aggregator is fully deterministic and unit-testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal


def _to_decimal(value) -> Decimal:
    """Convert an int/float/str/Decimal into a Decimal without float drift.

    Going through ``str`` first means ``0.1`` becomes ``Decimal('0.1')`` rather
    than the long binary-float expansion ``Decimal('0.1000000000000000055...')``.
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True)
class Candle:
    """A closed OHLCV bar for one time bucket.

    Attributes:
        start: Epoch second at which the bucket opens (floored to the interval).
        open: Price of the first trade in the bucket.
        high: Highest trade price in the bucket.
        low: Lowest trade price in the bucket.
        close: Price of the last trade in the bucket.
        volume: Sum of trade sizes in the bucket.
        vwap: Volume-weighted average price, ``sum(price * size) / sum(size)``.
        trade_count: Number of trades that fell into the bucket.
    """

    start: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Decimal
    trade_count: int


class _Bucket:
    """Mutable accumulator for the candle currently being built."""

    __slots__ = (
        "start",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "_notional",
        "trade_count",
    )

    def __init__(self, start: int, price: Decimal, size: Decimal) -> None:
        self.start = start
        self.open = price
        self.high = price
        self.low = price
        self.close = price
        self.volume = size
        # Running sum of price * size, used to derive the VWAP on close.
        self._notional = price * size
        self.trade_count = 1

    def update(self, price: Decimal, size: Decimal) -> None:
        """Fold one more trade into this in-progress bar."""
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.close = price
        self.volume += size
        self._notional += price * size
        self.trade_count += 1

    def to_candle(self) -> Candle:
        """Freeze the accumulator into an immutable closed candle."""
        # volume is always > 0 here: every trade carries size > 0 and a bucket
        # only exists once at least one trade has landed in it.
        vwap = self._notional / self.volume
        return Candle(
            start=self.start,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            vwap=vwap,
            trade_count=self.trade_count,
        )


class CandleAggregator:
    """Turn a stream of trades into fixed-interval OHLCV candles.

    Usage:
        agg = CandleAggregator(interval_seconds=60)
        for ts, price, size in trades:        # timestamps non-decreasing
            for candle in agg.add(ts, price, size):
                emit(candle)                  # a prior bucket just closed
        final = agg.flush()                   # in-progress bar, or None
    """

    def __init__(self, interval_seconds: int) -> None:
        if not isinstance(interval_seconds, int) or isinstance(interval_seconds, bool):
            raise ValueError("interval_seconds must be an int")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.interval = interval_seconds
        self._current: _Bucket | None = None
        self._last_ts: float | None = None

    def _bucket_start(self, timestamp: float) -> int:
        """Floor a timestamp to the start of its interval bucket."""
        return int(math.floor(timestamp / self.interval)) * self.interval

    def add(self, timestamp: float, price, size) -> list[Candle]:
        """Add one trade. Return any candles that closed because of it.

        A candle closes when this trade opens a strictly later bucket than the
        one in progress. Because empty buckets are skipped, ``add`` returns at
        most one candle (the previous in-progress bar); it returns an empty list
        while a bucket is still filling.
        """
        if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be a number")
        if math.isnan(timestamp) or math.isinf(timestamp):
            raise ValueError("timestamp must be finite")

        # Enforce non-decreasing arrival order so we never reopen a closed bar.
        if self._last_ts is not None and timestamp < self._last_ts:
            raise ValueError(
                f"out-of-order timestamp {timestamp!r} < {self._last_ts!r}"
            )
        self._last_ts = timestamp

        price = _to_decimal(price)
        size = _to_decimal(size)
        if price <= 0:
            raise ValueError("price must be positive")
        if size <= 0:
            raise ValueError("size must be positive")

        start = self._bucket_start(timestamp)
        closed: list[Candle] = []

        if self._current is None:
            self._current = _Bucket(start, price, size)
            return closed

        if start > self._current.start:
            # The trade belongs to a later bucket: close the current bar and
            # open a fresh one. Intervening empty buckets emit nothing.
            closed.append(self._current.to_candle())
            self._current = _Bucket(start, price, size)
        else:
            # Same bucket (start == current.start); fold the trade in.
            self._current.update(price, size)

        return closed

    def flush(self) -> Candle | None:
        """Close and return the in-progress bar, or None if no trades were seen.

        After flush the aggregator holds no in-progress bar, so a subsequent
        flush returns None until more trades arrive.
        """
        if self._current is None:
            return None
        candle = self._current.to_candle()
        self._current = None
        return candle
