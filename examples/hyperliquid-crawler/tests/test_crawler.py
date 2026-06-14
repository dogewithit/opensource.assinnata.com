"""End-to-end crawler test: FakeSource -> Crawler -> Postgres."""

from src.crawler import Crawler
from src.models import parse_markets


def test_run_once_persists_all_outcomes(repo, sample_payload):
    from conftest import FakeSource

    source = FakeSource(parse_markets(sample_payload))
    crawler = Crawler(source, repo)

    written = crawler.run_once()

    assert written == 4
    assert source.calls == 1
    assert repo.count("markets") == 4
    assert repo.count("market_snapshots") == 4

    rows = {(r["market_id"], r["outcome"]): r for r in repo.latest()}
    assert ("BTC-100K-2026", "YES") in rows
    assert ("ETH-FLIP-2027", "NO") in rows


def test_repeated_runs_keep_latest_state_and_grow_history(repo, sample_payload):
    from conftest import FakeSource

    source = FakeSource(parse_markets(sample_payload))
    crawler = Crawler(source, repo)

    crawler.run_once()
    crawler.run_once()

    assert repo.count("markets") == 4          # idempotent latest state
    assert repo.count("market_snapshots") == 8  # 2 crawls of history
