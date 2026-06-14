"""Domain model + parsing for Hyperliquid outcome markets.

The crawler depends on this normalized shape, not on the wire format, so the
parser is the single place that knows the API JSON layout (and the only thing
that has to change if the upstream schema moves).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class OutcomeMarket:
    """One outcome of one market at a point in time."""

    market_id: str
    question: str
    outcome: str
    price: Decimal
    volume_24h: Decimal | None = None


def _to_decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"not a numeric value: {value!r}") from exc


def parse_markets(payload: dict) -> list[OutcomeMarket]:
    """Flatten the API payload into one row per (market, outcome).

    Expected shape::

        {
          "markets": [
            {"id": "BTC-100K-2026",
             "question": "Will BTC trade above $100k in 2026?",
             "outcomes": [
               {"label": "YES", "price": "0.62", "volume24h": "1200000"},
               {"label": "NO",  "price": "0.38", "volume24h": "1200000"}
             ]}
          ]
        }
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    markets_raw = payload.get("markets")
    if not isinstance(markets_raw, list):
        raise ValueError("payload missing 'markets' list")

    results: list[OutcomeMarket] = []
    for market in markets_raw:
        market_id = market.get("id")
        question = market.get("question")
        outcomes = market.get("outcomes")
        if not market_id or not question or not isinstance(outcomes, list):
            raise ValueError(f"malformed market entry: {market!r}")

        for oc in outcomes:
            label = oc.get("label")
            if not label or "price" not in oc:
                raise ValueError(f"malformed outcome entry: {oc!r}")
            vol = oc.get("volume24h")
            results.append(
                OutcomeMarket(
                    market_id=str(market_id),
                    question=str(question),
                    outcome=str(label),
                    price=_to_decimal(oc["price"]),
                    volume_24h=_to_decimal(vol) if vol is not None else None,
                )
            )
    return results


def parse_perp_markets(payload: list) -> list[OutcomeMarket]:
    """Parse the real Hyperliquid ``metaAndAssetCtxs`` response.

    The response is a two element list: the first holds the market universe,
    the second holds a parallel list of market contexts (prices, volume). We map
    each live perpetual market into one row with outcome ``PERP``::

        [
          {"universe": [{"name": "BTC", ...}, ...]},
          [{"markPx": "64060.0", "dayNtlVlm": "1358072735.6", ...}, ...]
        ]

    Delisted markets and markets without a mark price are skipped.
    """
    if not (isinstance(payload, list) and len(payload) == 2):
        raise ValueError("expected a two element metaAndAssetCtxs response")

    meta, contexts = payload
    universe = meta.get("universe") if isinstance(meta, dict) else None
    if not isinstance(universe, list) or not isinstance(contexts, list):
        raise ValueError("malformed metaAndAssetCtxs response")
    if len(universe) != len(contexts):
        raise ValueError("universe and context lists must be the same length")

    results: list[OutcomeMarket] = []
    for market, ctx in zip(universe, contexts):
        if market.get("isDelisted"):
            continue
        mark = ctx.get("markPx")
        if mark is None:
            continue
        name = str(market["name"])
        vol = ctx.get("dayNtlVlm")
        results.append(
            OutcomeMarket(
                market_id=name,
                question=f"{name} perpetual",
                outcome="PERP",
                price=_to_decimal(mark),
                volume_24h=_to_decimal(vol) if vol is not None else None,
            )
        )
    return results
