"""Crawler orchestration: pull from a MarketSource, persist to Postgres."""

from __future__ import annotations

from .client import MarketSource
from .db import MarketRepository


class Crawler:
    def __init__(self, source: MarketSource, repo: MarketRepository) -> None:
        self.source = source
        self.repo = repo

    def run_once(self) -> int:
        """Fetch the current outcome markets and persist them.

        Returns the number of (market, outcome) rows written.
        """
        markets = self.source.fetch_markets()
        return self.repo.upsert_markets(markets)
