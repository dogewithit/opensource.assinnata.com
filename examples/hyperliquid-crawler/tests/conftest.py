"""Shared fixtures. Adds the example root to sys.path so `import src...` works,
and provides a Postgres-backed repository fixture."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE_ROOT))

from src.client import MarketSource  # noqa: E402
from src.db import MarketRepository, connect  # noqa: E402
from src.models import OutcomeMarket  # noqa: E402


SAMPLE_PAYLOAD = {
    "markets": [
        {
            "id": "BTC-100K-2026",
            "question": "Will BTC trade above $100k in 2026?",
            "outcomes": [
                {"label": "YES", "price": "0.62", "volume24h": "1200000"},
                {"label": "NO", "price": "0.38", "volume24h": "1200000"},
            ],
        },
        {
            "id": "ETH-FLIP-2027",
            "question": "Will ETH flip BTC by 2027?",
            "outcomes": [
                {"label": "YES", "price": "0.12"},
                {"label": "NO", "price": "0.88"},
            ],
        },
    ]
}


class FakeSource(MarketSource):
    """In-memory MarketSource so the crawler can be tested without network."""

    def __init__(self, markets: list[OutcomeMarket]) -> None:
        self._markets = markets
        self.calls = 0

    def fetch_markets(self) -> list[OutcomeMarket]:
        self.calls += 1
        return list(self._markets)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: hits the real Hyperliquid API (skips if offline)"
    )


@pytest.fixture
def sample_payload() -> dict:
    return SAMPLE_PAYLOAD


@pytest.fixture
def repo():
    """A clean, migrated repository. Skips if Postgres is unreachable."""
    try:
        conn = connect()
    except Exception as exc:  # pragma: no cover - infra not up
        pytest.skip(f"Postgres not reachable (run `make up`): {exc}")
    r = MarketRepository(conn)
    r.migrate()
    r.truncate()
    try:
        yield r
    finally:
        conn.close()
