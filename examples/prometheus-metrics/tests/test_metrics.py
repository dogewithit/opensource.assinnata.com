"""Validate counters, histograms, and the text exposition format."""

from src.metrics import TradeMetrics


def test_counter_increments_per_side():
    m = TradeMetrics()
    m.record_trade("buy", 300)
    m.record_trade("buy", 500)
    m.record_trade("sell", 200)

    assert m.trades_total.labels(side="buy")._value.get() == 2
    assert m.trades_total.labels(side="sell")._value.get() == 1


def test_render_contains_help_type_and_values():
    m = TradeMetrics()
    m.record_trade("buy", 300)
    out = m.render()

    assert "# HELP trades_total Total trades executed" in out
    assert "# TYPE trades_total counter" in out
    assert 'trades_total{side="buy"} 1.0' in out


def test_histogram_records_notional():
    m = TradeMetrics()
    for n in (150, 5_000, 250_000):
        m.record_trade("buy", n)
    out = m.render()

    assert "trade_notional_usd_count 3.0" in out
    assert "trade_notional_usd_sum 255150.0" in out
    # 150 falls in the <=1000 bucket
    assert 'trade_notional_usd_bucket{le="1000.0"} 1.0' in out
