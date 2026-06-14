"""Fixtures for the AWS example. Skips if LocalStack is unreachable."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE_ROOT))

# Ensure boto3 has (dummy) creds + endpoint even if the shell didn't export them.
os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:4566")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from src.store import MarketArtifactStore  # noqa: E402


@pytest.fixture
def store():
    """A store backed by freshly-created LocalStack infra, torn down after."""
    s = MarketArtifactStore(bucket="oss-test-artifacts", table="oss-test-markets")
    try:
        s.ensure_infra()
    except Exception as exc:  # pragma: no cover - infra not up
        pytest.skip(f"LocalStack not reachable (run `make up`): {exc}")

    # clean slate
    for mid in s.list_ids():
        s.ddb.delete_item(TableName=s.table, Key={"market_id": {"S": mid}})
    yield s
