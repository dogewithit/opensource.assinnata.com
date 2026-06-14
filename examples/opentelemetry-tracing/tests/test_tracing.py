"""Assert spans + attributes via the in-memory exporter."""

import pytest
from opentelemetry.trace import StatusCode

from src.tracing import execute_trade


def test_successful_trade_emits_ok_span_with_attributes(spans):
    result = execute_trade(
        {"market_id": "BTC-100K-2026", "side": "buy", "qty": 3, "price": 100}
    )
    assert result["notional"] == 300

    finished = spans.get_finished_spans()
    assert len(finished) == 1
    span = finished[0]
    assert span.name == "execute_trade"
    assert span.status.status_code == StatusCode.OK
    assert span.attributes["trade.market_id"] == "BTC-100K-2026"
    assert span.attributes["trade.side"] == "buy"
    assert span.attributes["trade.notional"] == 300


def test_invalid_qty_records_error_span(spans):
    with pytest.raises(ValueError, match="qty must be positive"):
        execute_trade({"market_id": "X", "side": "buy", "qty": 0, "price": 100})

    finished = spans.get_finished_spans()
    assert len(finished) == 1
    assert finished[0].status.status_code == StatusCode.ERROR


def test_invalid_price_records_error_span(spans):
    with pytest.raises(ValueError, match="price must be positive"):
        execute_trade({"market_id": "X", "side": "sell", "qty": 1, "price": 0})

    assert spans.get_finished_spans()[0].status.status_code == StatusCode.ERROR
