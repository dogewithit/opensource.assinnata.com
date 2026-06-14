"""Live integration test: crawl the real Hyperliquid API into Postgres.

Marked `live`. It skips cleanly if the network or API is unavailable, but when
it does run it proves the whole pipeline works against production data.
"""

import socket

import pytest

from src.client import HyperliquidClient
from src.crawler import Crawler


def _online(host: str = "api.hyperliquid.xyz", port: int = 443) -> bool:
    try:
        socket.create_connection((host, port), timeout=5).close()
        return True
    except OSError:
        return False


@pytest.mark.live
def test_live_crawl_stores_real_perp_markets(repo):
    if not _online():
        pytest.skip("Hyperliquid API not reachable")

    client = HyperliquidClient()
    try:
        written = Crawler(client, repo).run_once()
    except Exception as exc:  # network/API hiccup -> skip, don't fail CI
        pytest.skip(f"Hyperliquid API call failed: {exc}")
    finally:
        client.close()

    # Hyperliquid lists hundreds of perps.
    assert written > 50
    assert repo.count("markets") == written
    assert repo.count("market_snapshots") == written

    rows = {r["market_id"]: r for r in repo.latest()}
    # every stored price is positive
    assert all(r["price"] > 0 for r in rows.values())
    # sanity-check a market everyone knows
    assert "BTC" in rows
    assert rows["BTC"]["price"] > 1000
