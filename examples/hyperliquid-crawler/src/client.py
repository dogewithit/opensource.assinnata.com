"""HTTP client for the Hyperliquid info API.

The crawler depends on the ``MarketSource`` protocol, not on this concrete
client, so tests can substitute a fake source with no network access.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from .models import OutcomeMarket, parse_markets


class MarketSource(Protocol):
    """Anything the crawler can pull outcome markets from."""

    def fetch_markets(self) -> list[OutcomeMarket]: ...


class HyperliquidClient:
    """Pulls outcome markets from the Hyperliquid info endpoint."""

    def __init__(
        self,
        base_url: str = "https://api.hyperliquid.xyz",
        request_type: str = "outcomeMarkets",
        http: httpx.Client | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.request_type = request_type
        self._http = http or httpx.Client(timeout=timeout)

    def fetch_raw(self) -> dict:
        resp = self._http.post(
            f"{self.base_url}/info", json={"type": self.request_type}
        )
        resp.raise_for_status()
        return resp.json()

    def fetch_markets(self) -> list[OutcomeMarket]:
        return parse_markets(self.fetch_raw())

    def close(self) -> None:
        self._http.close()
