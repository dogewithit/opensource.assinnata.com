"""End to end tests for the nginx deploy example against the ``oss`` cluster.

Each test gets a fresh namespace from the ``namespace`` fixture and that
namespace is deleted on teardown, so the cluster is always left clean.
"""

from __future__ import annotations

from src import deploy

ROLLOUT_TIMEOUT = 120.0


def test_deployment_reports_available_replicas(clients, namespace):
    """After deploy the Deployment reports the desired ready replicas."""

    deploy.apply_deployment(clients, namespace, replicas=2)
    dep = deploy.wait_for_rollout(
        clients, namespace, name="web", timeout=ROLLOUT_TIMEOUT
    )

    assert dep.spec.replicas == 2
    assert dep.status.available_replicas == 2
    assert dep.status.ready_replicas == 2


def test_pods_are_running(clients, namespace):
    """Every workload pod reaches the Running phase."""

    deploy.apply_deployment(clients, namespace, replicas=2)
    deploy.wait_for_rollout(clients, namespace, name="web", timeout=ROLLOUT_TIMEOUT)

    phases = deploy.list_pod_phases(clients, namespace)
    assert len(phases) == 2
    assert all(phase == "Running" for phase in phases)


def test_scaling_converges(clients, namespace):
    """Scaling the Deployment to 3 replicas converges to 3 available."""

    deploy.apply_deployment(clients, namespace, replicas=2)
    deploy.wait_for_rollout(clients, namespace, name="web", timeout=ROLLOUT_TIMEOUT)

    deploy.scale_deployment(clients, namespace, replicas=3)
    dep = deploy.wait_for_rollout(
        clients, namespace, name="web", timeout=ROLLOUT_TIMEOUT
    )

    assert dep.spec.replicas == 3
    assert dep.status.available_replicas == 3


def test_service_serves_nginx(clients, namespace):
    """Reaching the Service from inside the cluster returns nginx content."""

    deploy.apply_deployment(clients, namespace, replicas=2)
    deploy.wait_for_rollout(clients, namespace, name="web", timeout=ROLLOUT_TIMEOUT)

    body = deploy.fetch_via_service(clients, namespace, service_name="web")
    assert "nginx" in body.lower()
