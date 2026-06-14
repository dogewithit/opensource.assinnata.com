"""Trade metrics exposed in the Prometheus text format.

Uses an injectable CollectorRegistry so each instance (and each test) is fully
isolated from the process-global default registry.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest


class TradeMetrics:
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.trades_total = Counter(
            "trades_total",
            "Total trades executed",
            ["side"],
            registry=self.registry,
        )
        self.notional_usd = Histogram(
            "trade_notional_usd",
            "Trade notional in USD",
            buckets=(100, 1_000, 10_000, 100_000),
            registry=self.registry,
        )

    def record_trade(self, side: str, notional: float) -> None:
        self.trades_total.labels(side=side).inc()
        self.notional_usd.observe(notional)

    def render(self) -> str:
        """Return the Prometheus text exposition (what a /metrics endpoint serves)."""
        return generate_latest(self.registry).decode("utf-8")
