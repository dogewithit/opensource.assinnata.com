"""HTTP client for the Hyperliquid info API.

The crawler depends on the ``MarketSource`` protocol, not on this concrete
client, so tests can substitute a fake source with no network access.

The default source is the real, live perpetual markets endpoint
(``metaAndAssetCtxs``); ``fetch_markets`` returns those so the crawler stores
real data out of the box.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from .models import OutcomeMarket, parse_markets, parse_perp_markets


class MarketSource(Protocol):
    """Anything the crawler can pull markets from."""

    def fetch_markets(self) -> list[OutcomeMarket]: ...


class HyperliquidClient:
    """Pulls live markets from the Hyperliquid info endpoint."""

    def __init__(
        self,
        base_url: str = "https://api.hyperliquid.xyz",
        http: httpx.Client | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = http or httpx.Client(timeout=timeout)

    def _post_info(self, body: dict):
        resp = self._http.post(f"{self.base_url}/info", json=body)
        resp.raise_for_status()
        return resp.json()

    def fetch_perp_markets(self) -> list[OutcomeMarket]:
        """The live perpetual markets (real data)."""
        return parse_perp_markets(self._post_info({"type": "metaAndAssetCtxs"}))

    def fetch_outcome_markets(self) -> list[OutcomeMarket]:
        """Outcome/prediction markets, for venues that expose them in the
        documented outcome shape parsed by ``parse_markets``."""
        return parse_markets(self._post_info({"type": "outcomeMarkets"}))

    def fetch_markets(self) -> list[OutcomeMarket]:
        # default crawl target = real live perpetual markets
        return self.fetch_perp_markets()

    def close(self) -> None:
        self._http.close()
