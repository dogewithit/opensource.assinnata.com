-- Hyperliquid outcome-markets crawler schema.
-- `markets` holds the latest known state (idempotent upsert target).
-- `market_snapshots` is an append-only time series for historical analysis.

CREATE TABLE IF NOT EXISTS markets (
    market_id   TEXT        NOT NULL,
    outcome     TEXT        NOT NULL,
    question    TEXT        NOT NULL,
    price       NUMERIC     NOT NULL,
    volume_24h  NUMERIC,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (market_id, outcome)
);

CREATE TABLE IF NOT EXISTS market_snapshots (
    id          BIGSERIAL   PRIMARY KEY,
    market_id   TEXT        NOT NULL,
    outcome     TEXT        NOT NULL,
    price       NUMERIC     NOT NULL,
    volume_24h  NUMERIC,
    snapshot_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_market
    ON market_snapshots (market_id, outcome, snapshot_at DESC);
