"""Deploy and manage an nginx workload on Kubernetes with the official client.

This module is a small, production shaped wrapper around the ``kubernetes``
Python client. It shows the full lifecycle of a workload:

1. create a namespace,
2. apply a Deployment plus a ClusterIP Service,
3. wait for the rollout to become available,
4. optionally reach the Service from inside the cluster,
5. scale the Deployment,
6. delete the namespace (which removes everything it contains).

The same code that runs against a local minikube cluster also runs against a
real cluster. The only difference is the kube context you point it at.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

# Defaults used by the example. Override them per call when you need to.
DEFAULT_IMAGE = "nginx:alpine"
DEFAULT_REPLICAS = 2
DEFAULT_APP_LABEL = "oss-nginx"
DEFAULT_SERVICE_PORT = 80


@dataclass
class Clients:
    """Bundle of the API clients this module uses.

    Building these once and passing them around keeps the functions easy to
    test and avoids re-loading the kube config on every call.
    """

    core: client.CoreV1Api
    apps: client.AppsV1Api


def load_clients(context: str = "oss") -> Clients:
    """Load the kube config for ``context`` and return ready to use clients.

    ``config.load_kube_config`` reads the usual ``~/.kube/config``. Selecting an
    explicit context makes the target cluster obvious and prevents accidentally
    talking to whatever happens to be current.
    """

    config.load_kube_config(context=context)
    return Clients(core=client.CoreV1Api(), apps=client.AppsV1Api())


def create_namespace(clients: Clients, namespace: str) -> None:
    """Create ``namespace`` if it does not already exist.

    The function is idempotent. A 409 (already exists) is treated as success so
    the example can be run repeatedly without manual cleanup.
    """

    body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
    try:
        clients.core.create_namespace(body=body)
    except ApiException as exc:
        if exc.status != 409:
            raise


def _deployment_manifest(
    name: str,
    image: str,
    replicas: int,
    app_label: str,
) -> client.V1Deployment:
    """Build the Deployment object for the nginx workload."""

    labels = {"app": app_label}
    container = client.V1Container(
        name=name,
        image=image,
        ports=[client.V1ContainerPort(container_port=80)],
        # A readiness probe lets Kubernetes mark a pod available only once it
        # actually serves traffic, which is what ``available_replicas`` counts.
        readiness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path="/", port=80),
            initial_delay_seconds=1,
            period_seconds=2,
        ),
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=labels),
        spec=client.V1PodSpec(containers=[container]),
    )
    spec = client.V1DeploymentSpec(
        replicas=replicas,
        selector=client.V1LabelSelector(match_labels=labels),
        template=template,
    )
    return client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name, labels=labels),
        spec=spec,
    )


def _service_manifest(
    name: str,
    app_label: str,
    port: int,
) -> client.V1Service:
    """Build a ClusterIP Service that targets the workload pods."""

    spec = client.V1ServiceSpec(
        selector={"app": app_label},
        ports=[client.V1ServicePort(port=port, target_port=80)],
        type="ClusterIP",
    )
    return client.V1Service(
        metadata=client.V1ObjectMeta(name=name),
        spec=spec,
    )


def apply_deployment(
    clients: Clients,
    namespace: str,
    name: str = "web",
    image: str = DEFAULT_IMAGE,
    replicas: int = DEFAULT_REPLICAS,
    app_label: str = DEFAULT_APP_LABEL,
    service_port: int = DEFAULT_SERVICE_PORT,
) -> None:
    """Create the Deployment and Service in ``namespace``.

    Both creates are idempotent: a 409 means the object is already there, which
    is fine for a demo that may be run more than once.
    """

    deployment = _deployment_manifest(name, image, replicas, app_label)
    service = _service_manifest(name, app_label, service_port)

    try:
        clients.apps.create_namespaced_deployment(namespace=namespace, body=deployment)
    except ApiException as exc:
        if exc.status != 409:
            raise

    try:
        clients.core.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as exc:
        if exc.status != 409:
            raise


def wait_for_rollout(
    clients: Clients,
    namespace: str,
    name: str = "web",
    timeout: float = 120.0,
    poll_interval: float = 2.0,
) -> client.V1Deployment:
    """Block until the Deployment has ``available_replicas == spec.replicas``.

    Returns the final Deployment object. Raises ``TimeoutError`` if the rollout
    does not converge in time, which keeps tests from hanging forever when an
    image pull or scheduling problem occurs.
    """

    deadline = time.monotonic() + timeout
    while True:
        dep = clients.apps.read_namespaced_deployment(name=name, namespace=namespace)
        desired = dep.spec.replicas or 0
        available = (dep.status.available_replicas or 0) if dep.status else 0
        if desired > 0 and available == desired:
            return dep
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Deployment {namespace}/{name} did not reach {desired} available "
                f"replicas within {timeout}s (last seen {available})."
            )
        time.sleep(poll_interval)


def scale_deployment(
    clients: Clients,
    namespace: str,
    replicas: int,
    name: str = "web",
) -> None:
    """Set the desired replica count on the Deployment.

    A JSON merge patch on ``spec.replicas`` is the lightweight way to scale
    without sending the whole object back to the API server.
    """

    clients.apps.patch_namespaced_deployment_scale(
        name=name,
        namespace=namespace,
        body={"spec": {"replicas": replicas}},
    )


def list_pod_phases(
    clients: Clients,
    namespace: str,
    app_label: str = DEFAULT_APP_LABEL,
) -> list[str]:
    """Return the ``status.phase`` of every workload pod (e.g. ``Running``)."""

    pods = clients.core.list_namespaced_pod(
        namespace=namespace,
        label_selector=f"app={app_label}",
    )
    return [p.status.phase for p in pods.items]


def fetch_via_service(
    clients: Clients,
    namespace: str,
    service_name: str = "web",
    service_port: int = DEFAULT_SERVICE_PORT,
) -> str:
    """Curl the Service from inside the cluster and return the response body.

    This proves the Service actually load balances to the pods. It runs a
    throwaway pod, execs ``wget`` against the in cluster DNS name of the
    Service, and returns whatever the Service served.
    """

    pod_name = "oss-curl"
    url = f"http://{service_name}.{namespace}.svc.cluster.local:{service_port}/"
    probe = client.V1Pod(
        metadata=client.V1ObjectMeta(name=pod_name),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=[
                client.V1Container(
                    name="curl",
                    image="busybox:1.36",
                    command=["sleep", "300"],
                )
            ],
        ),
    )
    try:
        clients.core.create_namespaced_pod(namespace=namespace, body=probe)
    except ApiException as exc:
        if exc.status != 409:
            raise

    _wait_for_pod_running(clients, namespace, pod_name)

    resp = stream(
        clients.core.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=["wget", "-q", "-O", "-", url],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    return resp


def _wait_for_pod_running(
    clients: Clients,
    namespace: str,
    pod_name: str,
    timeout: float = 60.0,
    poll_interval: float = 2.0,
) -> None:
    """Wait until a single pod reaches the ``Running`` phase."""

    deadline = time.monotonic() + timeout
    while True:
        pod = clients.core.read_namespaced_pod(name=pod_name, namespace=namespace)
        if pod.status and pod.status.phase == "Running":
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Pod {namespace}/{pod_name} did not reach Running within {timeout}s."
            )
        time.sleep(poll_interval)


def delete_namespace(
    clients: Clients,
    namespace: str,
    wait: bool = True,
    timeout: float = 120.0,
    poll_interval: float = 2.0,
) -> None:
    """Delete ``namespace`` and everything in it.

    Deleting the namespace is the cleanest teardown: it removes the Deployment,
    the Service, the pods, and any probe pods in one call. When ``wait`` is set
    the function blocks until the namespace is gone so the cluster is left
    clean.
    """

    try:
        clients.core.delete_namespace(name=namespace)
    except ApiException as exc:
        if exc.status == 404:
            return
        raise

    if not wait:
        return

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            clients.core.read_namespace(name=namespace)
        except ApiException as exc:
            if exc.status == 404:
                return
            raise
        time.sleep(poll_interval)
    raise TimeoutError(f"Namespace {namespace} was not deleted within {timeout}s.")
