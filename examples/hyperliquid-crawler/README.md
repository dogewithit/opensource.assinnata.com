# Hyperliquid markets crawler

Crawls live market data from the Hyperliquid info API and stores it in Postgres:
latest state plus an append-only snapshot history.

By default it pulls Hyperliquid's **live perpetual markets** (`metaAndAssetCtxs`,
~180 markets with mark price and 24h volume) — Hyperliquid's public API does not
expose prediction/outcome markets, so this crawls the real markets that exist. A
generic outcome-market parser (`parse_markets`) is also included for venues that
do expose that shape.

> **Software Engineering** example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- A clean **fetch → parse → persist** pipeline with the network behind a
  `MarketSource` protocol, so the crawler is testable without hitting the API.
- **Idempotent upserts** into a latest-state `markets` table keyed on
  `(market_id, outcome)`, plus an append-only `market_snapshots` time series.
- Exact-decimal price handling (no floats for probabilities).

## Layout

```
src/
  models.py    # OutcomeMarket + parse_markets() — the only API-shape-aware code
  client.py    # HyperliquidClient (httpx) + MarketSource protocol
  db.py         # pg8000 connection + MarketRepository (migrate/upsert/query)
  crawler.py    # fetch -> persist orchestration
  __main__.py   # CLI entrypoint
tests/          # pytest — parsing (no IO) + DB/crawler (against docker Postgres)
schema.sql
```

## Run the tests (required — untested examples are rejected)

From the repo root:

```bash
make up                       # LocalStack 4.14 + Postgres 16
make test-hyperliquid-crawler
```

18 tests: payload parsing/validation (both shapes), upsert idempotency,
snapshot history, an end-to-end crawl through a fake source, and a **live test**
that hits `api.hyperliquid.xyz` and stores real markets (skips if offline).

## Run it for real

```bash
cp .env.example .env          # DATABASE_URL -> docker Postgres on :55432
python -m src                 # from this directory, venv active
```

## Note on the API shape

`parse_markets()` targets a documented outcome-market JSON contract (see its
docstring). If the upstream Hyperliquid schema differs, that one function is the
only place to adjust — the storage layer and tests are unaffected.

## Reference

Source: [`examples/hyperliquid-crawler`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/hyperliquid-crawler)
· Hyperliquid API: <https://hyperliquid.gitbook.io/hyperliquid-docs>
