"""Test fixtures for the kubernetes-minikube example.

These tests run against a real cluster reachable through the kube context named
``oss``. If that context is missing the whole module skips cleanly so the
example never fails on a machine without a cluster.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE_ROOT))

from src import deploy  # noqa: E402

CONTEXT = "oss"


def _context_available() -> bool:
    """Return True when the ``oss`` kube context can be loaded."""

    try:
        from kubernetes import config

        contexts, _ = config.list_kube_config_contexts()
        return any(c["name"] == CONTEXT for c in contexts)
    except Exception:
        return False


@pytest.fixture(scope="session")
def clients() -> deploy.Clients:
    """Kubernetes API clients bound to the ``oss`` context."""

    if not _context_available():
        pytest.skip(f"kube context {CONTEXT!r} is not available")
    return deploy.load_clients(context=CONTEXT)


@pytest.fixture
def namespace(clients: deploy.Clients):
    """A unique throwaway namespace, always torn down after the test.

    Using a random suffix lets several test runs coexist and guarantees we
    never collide with anything already in the cluster.
    """

    name = f"oss-k8s-demo-{uuid.uuid4().hex[:8]}"
    deploy.create_namespace(clients, name)
    try:
        yield name
    finally:
        deploy.delete_namespace(clients, name, wait=True)
