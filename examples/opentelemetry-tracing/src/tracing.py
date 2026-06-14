"""A trade-execution function instrumented with OpenTelemetry spans.

The function pulls its tracer from the global provider at call time, so the same
code emits to an in-memory exporter in tests and to an OTLP collector in prod —
only the provider wiring changes.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


def execute_trade(order: dict) -> dict:
    """Execute a trade, emitting a span with trade attributes.

    Raises ValueError on an invalid order (recorded on the span as ERROR).
    """
    tracer = trace.get_tracer("oss.example.trading")
    with tracer.start_as_current_span("execute_trade") as span:
        span.set_attribute("trade.market_id", str(order.get("market_id", "")))
        span.set_attribute("trade.side", str(order.get("side", "")))

        qty = order.get("qty", 0)
        price = order.get("price", 0)

        if qty <= 0:
            span.set_status(Status(StatusCode.ERROR, "qty must be positive"))
            raise ValueError("qty must be positive")
        if price <= 0:
            span.set_status(Status(StatusCode.ERROR, "price must be positive"))
            raise ValueError("price must be positive")

        notional = qty * price
        span.set_attribute("trade.notional", notional)
        span.set_status(Status(StatusCode.OK))
        return {"market_id": order["market_id"], "notional": notional}
