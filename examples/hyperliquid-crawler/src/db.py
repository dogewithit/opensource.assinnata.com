"""Postgres persistence for outcome markets (pg8000, pure-Python driver).

`markets` is upserted (idempotent latest state); every crawl also appends to
`market_snapshots` for a historical time series.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import pg8000.dbapi

from .models import OutcomeMarket

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


def connect(database_url: str | None = None) -> pg8000.dbapi.Connection:
    """Open a connection from a postgresql:// URL (env DATABASE_URL by default)."""
    url = database_url or os.environ.get(
        "DATABASE_URL", "postgresql://app:app@localhost:55432/markets"
    )
    parts = urlparse(url)
    return pg8000.dbapi.connect(
        user=parts.username or "app",
        password=parts.password or "app",
        host=parts.hostname or "localhost",
        port=parts.port or 5432,
        database=(parts.path or "/markets").lstrip("/") or "markets",
    )


class MarketRepository:
    """Data-access layer for outcome markets."""

    def __init__(self, conn: pg8000.dbapi.Connection) -> None:
        self.conn = conn

    def migrate(self) -> None:
        """Apply schema.sql (idempotent)."""
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

    def upsert_markets(self, markets: list[OutcomeMarket]) -> int:
        """Upsert latest state and append a snapshot for each row.

        Returns the number of rows written. Idempotent on (market_id, outcome):
        re-running updates price/volume rather than duplicating.
        """
        cur = self.conn.cursor()
        for m in markets:
            cur.execute(
                """
                INSERT INTO markets
                    (market_id, outcome, question, price, volume_24h, updated_at)
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (market_id, outcome) DO UPDATE SET
                    question   = EXCLUDED.question,
                    price      = EXCLUDED.price,
                    volume_24h = EXCLUDED.volume_24h,
                    updated_at = now()
                """,
                (m.market_id, m.outcome, m.question, m.price, m.volume_24h),
            )
            cur.execute(
                """
                INSERT INTO market_snapshots
                    (market_id, outcome, price, volume_24h)
                VALUES (%s, %s, %s, %s)
                """,
                (m.market_id, m.outcome, m.price, m.volume_24h),
            )
        self.conn.commit()
        return len(markets)

    def latest(self) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT market_id, outcome, question, price, volume_24h "
            "FROM markets ORDER BY market_id, outcome"
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def count(self, table: str) -> int:
        if table not in ("markets", "market_snapshots"):
            raise ValueError(f"unknown table: {table}")
        cur = self.conn.cursor()
        cur.execute(f"SELECT count(*) FROM {table}")
        return int(cur.fetchone()[0])

    def truncate(self) -> None:
        cur = self.conn.cursor()
        cur.execute("TRUNCATE markets, market_snapshots RESTART IDENTITY")
        self.conn.commit()
