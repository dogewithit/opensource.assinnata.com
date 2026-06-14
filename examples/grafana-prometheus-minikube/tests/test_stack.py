"""End to end checks against the live Prometheus and Grafana HTTP APIs."""

from __future__ import annotations

import time

import httpx


def _query_targets_up(prometheus_url: str, timeout: float = 60.0) -> list[dict]:
    """Poll the targets endpoint until at least one target reports up."""
    deadline = time.time() + timeout
    last: list[dict] = []
    while time.time() < deadline:
        response = httpx.get(f"{prometheus_url}/api/v1/targets", timeout=5.0)
        response.raise_for_status()
        active = response.json()["data"]["activeTargets"]
        last = active
        if any(t["health"] == "up" for t in active):
            return active
        time.sleep(2.0)
    return last


def test_prometheus_healthy(stack):
    response = httpx.get(f"{stack['prometheus_url']}/-/healthy", timeout=5.0)
    assert response.status_code == 200


def test_prometheus_has_up_target(stack):
    targets = _query_targets_up(stack["prometheus_url"])
    assert any(t["health"] == "up" for t in targets), targets


def test_prometheus_query_up(stack):
    deadline = time.time() + 60.0
    while time.time() < deadline:
        response = httpx.get(
            f"{stack['prometheus_url']}/api/v1/query",
            params={"query": "up"},
            timeout=5.0,
        )
        response.raise_for_status()
        payload = response.json()
        if payload["status"] == "success" and payload["data"]["result"]:
            assert payload["data"]["result"][0]["value"][1] is not None
            return
        time.sleep(2.0)
    raise AssertionError("query 'up' never returned a result")


def test_grafana_health(stack):
    response = httpx.get(
        f"{stack['grafana_url']}/api/health",
        auth=stack["grafana_auth"],
        timeout=5.0,
    )
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_grafana_datasource_provisioned(stack):
    response = httpx.get(
        f"{stack['grafana_url']}/api/datasources",
        auth=stack["grafana_auth"],
        timeout=5.0,
    )
    response.raise_for_status()
    datasources = response.json()
    assert any(d["type"] == "prometheus" for d in datasources), datasources


def test_grafana_dashboard_in_search(stack):
    response = httpx.get(
        f"{stack['grafana_url']}/api/search",
        params={"type": "dash-db"},
        auth=stack["grafana_auth"],
        timeout=5.0,
    )
    response.raise_for_status()
    results = response.json()
    assert any(d.get("uid") == "oss-overview" for d in results), results


def test_grafana_dashboard_by_uid(stack):
    response = httpx.get(
        f"{stack['grafana_url']}/api/dashboards/uid/oss-overview",
        auth=stack["grafana_auth"],
        timeout=5.0,
    )
    assert response.status_code == 200
    title = response.json()["dashboard"]["title"]
    assert title == "OSS Overview", title
