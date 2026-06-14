"""Persistence tests — run against the docker Postgres (`make up`)."""

from decimal import Decimal

from src.models import OutcomeMarket


def _market(price: str, vol: str | None = "100") -> OutcomeMarket:
    return OutcomeMarket(
        market_id="BTC-100K-2026",
        question="Will BTC trade above $100k in 2026?",
        outcome="YES",
        price=Decimal(price),
        volume_24h=Decimal(vol) if vol is not None else None,
    )


def test_upsert_inserts_rows(repo):
    no_outcome = OutcomeMarket(
        market_id="BTC-100K-2026",
        question="Will BTC trade above $100k in 2026?",
        outcome="NO",
        price=Decimal("0.38"),
        volume_24h=Decimal("100"),
    )
    written = repo.upsert_markets([_market("0.62"), no_outcome])
    assert written == 2
    assert repo.count("markets") == 2
    assert repo.count("market_snapshots") == 2


def test_upsert_is_idempotent_on_market_outcome(repo):
    repo.upsert_markets([_market("0.62")])
    repo.upsert_markets([_market("0.71")])  # same (market_id, outcome)

    rows = repo.latest()
    assert len(rows) == 1                       # not duplicated
    assert rows[0]["price"] == Decimal("0.71")  # updated to latest


def test_snapshots_accumulate_history(repo):
    repo.upsert_markets([_market("0.62")])
    repo.upsert_markets([_market("0.71")])
    repo.upsert_markets([_market("0.55")])

    assert repo.count("markets") == 1        # latest-state stays single row
    assert repo.count("market_snapshots") == 3  # full time series retained


def test_null_volume_persists(repo):
    repo.upsert_markets([_market("0.62", vol=None)])
    assert repo.latest()[0]["volume_24h"] is None
