"""CLI entrypoint: crawl Hyperliquid outcome markets into Postgres.

    python -m src            # from examples/hyperliquid-crawler/
"""

from __future__ import annotations

import os
import sys

from .client import HyperliquidClient
from .crawler import Crawler
from .db import MarketRepository, connect


def main() -> int:
    base_url = os.environ.get("HYPERLIQUID_API_URL", "https://api.hyperliquid.xyz")
    conn = connect()
    try:
        repo = MarketRepository(conn)
        repo.migrate()
        client = HyperliquidClient(base_url=base_url)
        try:
            written = Crawler(client, repo).run_once()
        finally:
            client.close()
        print(f"crawled and stored {written} outcome rows")
        print(f"markets={repo.count('markets')} snapshots={repo.count('market_snapshots')}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
