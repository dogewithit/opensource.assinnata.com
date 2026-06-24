"""Apply the whole Terragrunt stack against LocalStack once, then assert on it.

The stack is copied into an isolated temp dir so the repo stays clean, applied
with `terragrunt run --all apply`, shared across the module's tests, and
destroyed at the end.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE_ROOT))

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
os.environ.setdefault("AWS_ENDPOINT_URL", ENDPOINT)
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("S3_HOSTNAME", "localhost")

# Share one provider download across every unit so apply does not refetch it.
_CACHE = EXAMPLE_ROOT / ".plugin-cache"
os.environ.setdefault("TF_PLUGIN_CACHE_DIR", str(_CACHE))


def _terragrunt(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    # --parallelism 1 serializes the units. The units share one provider plugin
    # cache, and concurrent `init` would race and corrupt it ("Required plugins
    # are not installed"); serial runs let the first unit warm the cache.
    env = {**os.environ, "TG_NON_INTERACTIVE": "true"}
    return subprocess.run(
        ["terragrunt", *args, "--parallelism", "1", "--no-color"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=1200,
        env=env,
    )


def _localstack_up() -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(f"{ENDPOINT}/_localstack/health", timeout=5) as r:
            return b'"ec2"' in r.read()
    except Exception:
        return False


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    """Apply the stack once for the module, yield the work dir, then destroy."""
    if shutil.which("terragrunt") is None or shutil.which("terraform") is None:
        pytest.skip("terragrunt/terraform not installed")
    if not _localstack_up():
        pytest.skip("LocalStack with ec2 not reachable (run `make up`)")

    _CACHE.mkdir(parents=True, exist_ok=True)
    work = tmp_path_factory.mktemp("tg")
    dest = work / "stack"
    shutil.copytree(
        EXAMPLE_ROOT,
        dest,
        ignore=shutil.ignore_patterns("tests", ".plugin-cache", ".terragrunt-cache"),
    )

    applied = _terragrunt("run", "--all", "apply", cwd=dest)
    if applied.returncode != 0:
        _terragrunt("run", "--all", "destroy", cwd=dest)
        pytest.fail(f"terragrunt apply failed:\n{applied.stdout[-4000:]}\n{applied.stderr[-4000:]}")

    try:
        yield dest
    finally:
        _terragrunt("run", "--all", "destroy", cwd=dest)


@pytest.fixture(scope="module")
def ec2(stack):
    import boto3

    return boto3.client(
        "ec2",
        endpoint_url=ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
