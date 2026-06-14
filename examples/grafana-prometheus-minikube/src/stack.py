"""Helpers to drive a Prometheus + Grafana stack on minikube.

Everything goes through the kubectl CLI as a subprocess so the example stays
easy to read and mirrors what you would type by hand. The cluster is targeted
with the `oss` kube context and lives in the `oss-monitoring` namespace.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from pathlib import Path

CONTEXT = "oss"
NAMESPACE = "oss-monitoring"

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFESTS_DIR = REPO_ROOT / "manifests"


def kubectl_available() -> bool:
    """Return True when a kubectl binary and the `oss` context both exist."""
    if shutil.which("kubectl") is None:
        return False
    result = subprocess.run(
        ["kubectl", "config", "get-contexts", "-o", "name"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return CONTEXT in result.stdout.split()


def _kubectl(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["kubectl", "--context", CONTEXT, *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def apply_manifests() -> None:
    """Apply the namespace first, then Prometheus and Grafana."""
    _kubectl("apply", "-f", str(MANIFESTS_DIR / "namespace.yaml"))
    _kubectl("apply", "-f", str(MANIFESTS_DIR / "prometheus.yaml"))
    _kubectl("apply", "-f", str(MANIFESTS_DIR / "grafana.yaml"))


def wait_for_rollout(deployment: str, timeout: int = 300) -> None:
    """Block until a Deployment finishes rolling out.

    Image pulls on the very first run can be slow, so the timeout is generous.
    """
    _kubectl(
        "-n",
        NAMESPACE,
        "rollout",
        "status",
        f"deployment/{deployment}",
        f"--timeout={timeout}s",
    )


def delete_namespace() -> None:
    """Delete the whole namespace, ignoring errors during teardown."""
    _kubectl("delete", "namespace", NAMESPACE, "--ignore-not-found", check=False)


def _free_port() -> int:
    """Ask the OS for a free local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class PortForward:
    """A `kubectl port-forward` running as a background subprocess.

    Use it as a context manager or call start() and stop() directly. The local
    port is chosen by the OS so parallel runs do not collide.
    """

    def __init__(self, service: str, remote_port: int):
        self.service = service
        self.remote_port = remote_port
        self.local_port = _free_port()
        self._proc: subprocess.Popen | None = None

    def start(self) -> "PortForward":
        cmd = [
            "kubectl",
            "--context",
            CONTEXT,
            "-n",
            NAMESPACE,
            "port-forward",
            f"service/{self.service}",
            f"{self.local_port}:{self.remote_port}",
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._wait_until_listening()
        return self

    def _wait_until_listening(self, timeout: float = 30.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._proc is not None and self._proc.poll() is not None:
                out, err = self._proc.communicate()
                raise RuntimeError(
                    "port-forward exited early: "
                    f"{err.decode(errors='replace') or out.decode(errors='replace')}"
                )
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex(("127.0.0.1", self.local_port)) == 0:
                    return
            time.sleep(0.5)
        raise RuntimeError(
            f"port-forward to {self.service}:{self.remote_port} did not become ready"
        )

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.local_port}"

    def stop(self) -> None:
        if self._proc is None:
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=10)
        self._proc = None

    def __enter__(self) -> "PortForward":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()
