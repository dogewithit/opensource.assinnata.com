# Kubernetes orchestration on minikube

Deploys a real workload to Kubernetes with the official Python client and proves
it actually runs. The same `deploy.py` code drives a local minikube cluster or a
production cluster. The only thing that changes is the kube context you point it
at.

> **Kubernetes** tool example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- Driving the cluster with the official `kubernetes` Python client, selecting an
  explicit context with `config.load_kube_config(context="oss")` so the target
  is never ambiguous.
- The full workload lifecycle in plain functions: create a namespace, apply a
  Deployment (image `nginx:alpine`, 2 replicas) plus a ClusterIP Service on port
  80, wait for the rollout, scale, and tear everything down.
- Waiting on a rollout the way Kubernetes itself thinks about readiness, by
  polling until `available_replicas` equals the desired count. A readiness probe
  on each pod makes that count meaningful.
- Reaching the Service from inside the cluster. A throwaway pod curls the in
  cluster DNS name of the Service and the test asserts it gets nginx content
  back, which shows the Service really routes to the pods.
- A clean teardown. Deleting the namespace removes the Deployment, the Service,
  the pods, and the probe pod in one call, so the cluster is left as it was
  found.

## Prerequisites

A running minikube cluster reachable through the kube context named `oss`. You
do not need `make up`. As long as minikube is running and the context exists the
tests will run against it. If the context is missing the tests skip cleanly.

## Run the tests

```bash
pip install -r requirements.txt
pytest tests -v
```

The first run can take a little while because the cluster pulls the
`nginx:alpine` and `busybox` images. Rollouts are given a generous timeout so
that first pull does not cause a flake. Every test uses a unique namespace such
as `oss-k8s-demo-1a2b3c4d` and deletes it on teardown.

## Reference

Source: <https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/kubernetes-minikube>
· kubernetes Python client: <https://github.com/kubernetes-client/python>
