"""Run terraform (via tflocal) against LocalStack in an isolated temp workdir."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE_ROOT))

os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:4566")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
# Use plain localhost for S3 (avoids the s3.localhost.localstack.cloud DNS lookup
# that fails offline); pairs with s3_use_path_style in main.tf.
os.environ.setdefault("S3_HOSTNAME", "localhost")


def _tflocal(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tflocal", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=600,
    )


@pytest.fixture
def applied_stack(tmp_path):
    """Copy main.tf to a temp dir, `tflocal apply`, yield outputs, then destroy."""
    if shutil.which("tflocal") is None or shutil.which("terraform") is None:
        pytest.skip("terraform/tflocal not installed")

    shutil.copy(EXAMPLE_ROOT / "main.tf", tmp_path / "main.tf")

    init = _tflocal("init", "-input=false", "-no-color", cwd=tmp_path)
    if init.returncode != 0:
        if "ConnectionError" in init.stderr or "connection refused" in init.stderr.lower():
            pytest.skip("LocalStack not reachable (run `make up`)")
        pytest.fail(f"terraform init failed:\n{init.stdout}\n{init.stderr}")

    apply = _tflocal("apply", "-auto-approve", "-input=false", "-no-color", cwd=tmp_path)
    if apply.returncode != 0:
        if "connection refused" in apply.stderr.lower():
            pytest.skip("LocalStack not reachable (run `make up`)")
        pytest.fail(f"terraform apply failed:\n{apply.stdout}\n{apply.stderr}")

    try:
        yield tmp_path
    finally:
        _tflocal("destroy", "-auto-approve", "-input=false", "-no-color", cwd=tmp_path)
