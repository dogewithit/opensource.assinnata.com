"""Tests for the OHLCV candle aggregator.

Everything here is deterministic: timestamps are supplied by the test, so there
is no clock, no sleep and no network.
"""

from decimal import Decimal

import pytest

from src.candles import Candle, CandleAggregator


def test_single_bucket_ohlc():
    """One bucket yields open=first, close=last, high/low from the trades."""
    agg = CandleAggregator(interval_seconds=60)
    # All four trades fall inside the [0, 60) bucket.
    assert agg.add(0, 100, 1) == []
    assert agg.add(10, 120, 1) == []
    assert agg.add(20, 90, 1) == []
    assert agg.add(30, 110, 1) == []

    candle = agg.flush()
    assert candle.start == 0
    assert candle.open == Decimal("100")
    assert candle.high == Decimal("120")
    assert candle.low == Decimal("90")
    assert candle.close == Decimal("110")


def test_volume_is_sum_of_sizes():
    """Volume is the sum of all trade sizes in the bucket."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(0, 100, 2)
    agg.add(5, 101, 3)
    agg.add(10, 102, 5)
    candle = agg.flush()
    assert candle.volume == Decimal("10")


def test_vwap_is_volume_weighted():
    """VWAP weights price by size: (100*1 + 200*3) / (1+3) = 700/4 = 175."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(0, 100, 1)
    agg.add(10, 200, 3)
    candle = agg.flush()
    assert candle.vwap == Decimal("175")
    # Plain (unweighted) mean would be 150, so this proves the weighting.
    assert candle.vwap != Decimal("150")


def test_vwap_is_exact_with_decimals():
    """VWAP stays exact where binary floats would drift (0.1-style prices)."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(0, "0.1", 1)
    agg.add(1, "0.2", 1)
    candle = agg.flush()
    # (0.1*1 + 0.2*1) / 2 == 0.15 exactly under Decimal.
    assert candle.vwap == Decimal("0.15")


def test_trade_count():
    """trade_count counts the trades folded into the bucket."""
    agg = CandleAggregator(interval_seconds=60)
    for i in range(5):
        agg.add(i, 100 + i, 1)
    candle = agg.flush()
    assert candle.trade_count == 5


def test_crossing_bucket_closes_prior_candle():
    """A trade in a later bucket closes and returns the prior candle from add()."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(10, 100, 1)
    agg.add(20, 110, 2)
    # 75 lands in the [60, 120) bucket and closes the [0, 60) bucket.
    closed = agg.add(75, 200, 1)
    assert len(closed) == 1
    first = closed[0]
    assert isinstance(first, Candle)
    assert first.start == 0
    assert first.open == Decimal("100")
    assert first.close == Decimal("110")
    assert first.volume == Decimal("3")

    # The in-progress bar is now the new bucket.
    second = agg.flush()
    assert second.start == 60
    assert second.open == Decimal("200")


def test_bucket_boundary_is_floored():
    """A trade exactly on a boundary (t == interval) opens the next bucket."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(59, 100, 1)
    # t=60 belongs to [60, 120), not [0, 60), so the first bucket closes.
    closed = agg.add(60, 105, 1)
    assert len(closed) == 1
    assert closed[0].start == 0
    assert agg.flush().start == 60


def test_gap_does_not_emit_empty_candles():
    """Buckets with no trades produce no synthetic candles."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(10, 100, 1)  # bucket 0
    # Jump several intervals ahead to bucket 300; buckets 60..240 are empty.
    closed = agg.add(305, 130, 1)  # bucket 300
    assert len(closed) == 1  # only the one real prior bucket, no empties
    assert closed[0].start == 0
    assert agg.flush().start == 300


def test_flush_returns_final_then_none():
    """flush() returns the in-progress bar once, then None."""
    agg = CandleAggregator(interval_seconds=60)
    assert agg.flush() is None  # nothing seen yet
    agg.add(0, 100, 1)
    candle = agg.flush()
    assert candle is not None
    assert candle.start == 0
    # No in-progress bar remains after a flush.
    assert agg.flush() is None


def test_out_of_order_timestamp_raises():
    """A strictly decreasing timestamp is rejected."""
    agg = CandleAggregator(interval_seconds=60)
    agg.add(100, 100, 1)
    with pytest.raises(ValueError):
        agg.add(99, 101, 1)
    # Equal timestamp is allowed (non-decreasing order).
    assert agg.add(100, 102, 1) == []


def test_bad_size_and_price_raise():
    """Non-positive size or price is rejected."""
    agg = CandleAggregator(interval_seconds=60)
    with pytest.raises(ValueError):
        agg.add(0, 100, 0)
    with pytest.raises(ValueError):
        agg.add(0, 100, -1)
    with pytest.raises(ValueError):
        agg.add(0, 0, 1)
    with pytest.raises(ValueError):
        agg.add(0, -100, 1)


def test_invalid_interval_raises():
    """A non-positive interval is rejected at construction."""
    with pytest.raises(ValueError):
        CandleAggregator(interval_seconds=0)
    with pytest.raises(ValueError):
        CandleAggregator(interval_seconds=-60)
