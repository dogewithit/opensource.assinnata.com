"""Session fixtures that bring the stack up once and tear it down at the end."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.stack import (  # noqa: E402
    PortForward,
    apply_manifests,
    delete_namespace,
    kubectl_available,
    wait_for_rollout,
)


def _wait_for_http(url: str, timeout: float = 120.0, **kwargs) -> httpx.Response:
    """Poll an endpoint with backoff until it answers with 200."""
    deadline = time.time() + timeout
    delay = 1.0
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0, **kwargs)
            if response.status_code == 200:
                return response
            last_error = RuntimeError(f"{url} returned {response.status_code}")
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(delay)
        delay = min(delay * 1.5, 5.0)
    raise RuntimeError(f"endpoint {url} never became healthy: {last_error}")


@pytest.fixture(scope="session")
def stack():
    """Apply the manifests, port-forward both services, then clean up."""
    if not kubectl_available():
        pytest.skip("kubectl or the 'oss' context is not available")

    apply_manifests()
    wait_for_rollout("prometheus", timeout=300)
    wait_for_rollout("grafana", timeout=300)

    prometheus_pf = PortForward("prometheus", 9090).start()
    grafana_pf = PortForward("grafana", 3000).start()

    # Make sure both APIs really answer before any test runs.
    _wait_for_http(f"{prometheus_pf.base_url}/-/healthy")
    _wait_for_http(f"{grafana_pf.base_url}/api/health")

    try:
        yield {
            "prometheus_url": prometheus_pf.base_url,
            "grafana_url": grafana_pf.base_url,
            "grafana_auth": ("admin", "admin"),
        }
    finally:
        prometheus_pf.stop()
        grafana_pf.stop()
        delete_namespace()
