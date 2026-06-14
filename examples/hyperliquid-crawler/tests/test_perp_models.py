"""Offline parsing tests for the real metaAndAssetCtxs shape."""

from decimal import Decimal

import pytest

from src.models import parse_perp_markets

# A trimmed but real-shaped metaAndAssetCtxs response.
PERP_SAMPLE = [
    {
        "universe": [
            {"name": "BTC", "szDecimals": 5, "maxLeverage": 40},
            {"name": "ETH", "szDecimals": 4, "maxLeverage": 25},
            {"name": "MATIC", "szDecimals": 1, "maxLeverage": 20, "isDelisted": True},
            {"name": "NOPRICE", "szDecimals": 2, "maxLeverage": 5},
        ]
    },
    [
        {"markPx": "64060.0", "dayNtlVlm": "1358072735.67", "funding": "0.0000125"},
        {"markPx": "3420.5", "dayNtlVlm": "880123456.0"},
        {"markPx": "0.55", "dayNtlVlm": "1000.0"},  # delisted -> skipped
        {"markPx": None, "dayNtlVlm": "0"},          # no price -> skipped
    ],
]


def test_parse_perp_maps_universe_to_contexts():
    markets = parse_perp_markets(PERP_SAMPLE)
    # delisted + no-price entries are skipped
    assert [m.market_id for m in markets] == ["BTC", "ETH"]

    btc = markets[0]
    assert btc.outcome == "PERP"
    assert btc.question == "BTC perpetual"
    assert btc.price == Decimal("64060.0")
    assert btc.volume_24h == Decimal("1358072735.67")


def test_parse_perp_rejects_wrong_shape():
    for bad in ([], [{}], [{"universe": []}], "nope"):
        with pytest.raises(ValueError):
            parse_perp_markets(bad)


def test_parse_perp_requires_matching_lengths():
    with pytest.raises(ValueError):
        parse_perp_markets([{"universe": [{"name": "BTC"}]}, []])


def test_parse_perp_rejects_entry_missing_name():
    bad = [{"universe": [{"szDecimals": 5}]}, [{"markPx": "1", "dayNtlVlm": "1"}]]
    with pytest.raises(ValueError):
        parse_perp_markets(bad)


def test_parse_perp_rejects_non_dict_entry():
    bad = [{"universe": ["BTC"]}, [{"markPx": "1"}]]
    with pytest.raises(ValueError):
        parse_perp_markets(bad)
