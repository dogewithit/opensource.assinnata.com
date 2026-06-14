"""Parsing tests — no DB, no network."""

from decimal import Decimal

import pytest

from src.models import OutcomeMarket, parse_markets


def test_parse_flattens_to_one_row_per_outcome(sample_payload):
    markets = parse_markets(sample_payload)
    assert len(markets) == 4  # 2 markets x 2 outcomes
    assert OutcomeMarket(
        market_id="BTC-100K-2026",
        question="Will BTC trade above $100k in 2026?",
        outcome="YES",
        price=Decimal("0.62"),
        volume_24h=Decimal("1200000"),
    ) in markets


def test_parse_allows_missing_volume(sample_payload):
    eth_yes = next(
        m for m in parse_markets(sample_payload)
        if m.market_id == "ETH-FLIP-2027" and m.outcome == "YES"
    )
    assert eth_yes.volume_24h is None
    assert eth_yes.price == Decimal("0.12")


def test_parse_prices_are_decimal_not_float(sample_payload):
    # floats would corrupt probabilities; we require exact Decimal.
    for m in parse_markets(sample_payload):
        assert isinstance(m.price, Decimal)


@pytest.mark.parametrize(
    "bad",
    [
        {},                                   # no markets key
        {"markets": "nope"},                  # markets not a list
        {"markets": [{"id": "x"}]},           # missing question/outcomes
        {"markets": [{"id": "x", "question": "q", "outcomes": [{"label": "Y"}]}]},  # no price
        {"markets": [{"id": "x", "question": "q", "outcomes": [{"label": "Y", "price": "abc"}]}]},  # bad price
    ],
)
def test_parse_rejects_malformed_payloads(bad):
    with pytest.raises(ValueError):
        parse_markets(bad)
