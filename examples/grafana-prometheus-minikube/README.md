# Grafana and Prometheus on minikube

This example stands up a small monitoring stack on a local minikube cluster and
then proves it works by talking to the real HTTP APIs. It deploys Prometheus,
deploys Grafana, provisions a Grafana datasource that points at Prometheus, and
provisions a Grafana dashboard with a known uid. The tests confirm that
Prometheus is scraping, that the datasource is wired up, and that the dashboard
landed in Grafana.

Reference: https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/grafana-prometheus-minikube

## What it demonstrates

The stack stays light so it fits comfortably on a 4GB cluster. Instead of the
full kube-prometheus-stack helm chart, everything is a plain Deployment plus a
Service, all living in the `oss-monitoring` namespace.

* Prometheus runs with a ConfigMap holding `prometheus.yml`. The only scrape job
  targets Prometheus itself, so there is always at least one healthy target.
* Grafana runs with three ConfigMaps mounted into its provisioning folders. One
  defines a Prometheus datasource, one registers a file based dashboard
  provider, and one carries the dashboard JSON. The dashboard uses the uid
  `oss-overview` so the tests can fetch it directly.

Provisioning means Grafana picks all of this up automatically on startup. There
is no manual clicking in the UI and no API calls to create resources.

## What the tests check

The tests reach the services with `kubectl port-forward` running as a
subprocess. They cover the following:

* Prometheus answers `/-/healthy` with 200.
* Prometheus reports at least one target whose health is up.
* The `up` query returns a successful result with data.
* Grafana answers `/api/health` with 200 and a database status of ok.
* Grafana lists a Prometheus datasource.
* The provisioned dashboard shows up in search and can be fetched by its uid,
  with the expected title.

## Images used

* Prometheus: `prom/prometheus:v2.53.1`
* Grafana: `grafana/grafana:11.1.4`

## How to run

You need a running minikube cluster reachable through the `oss` kube context.
The tests skip cleanly when that context is missing, so they are safe to run in
an environment without a cluster.

```bash
pip install -r requirements.txt
pytest tests -v
```

The session fixture applies the manifests, waits for both Deployments to roll
out, starts the port forwards, and runs the checks. When the session ends it
stops the port forwards and deletes the `oss-monitoring` namespace, so the
cluster is left clean.

First runs can be slow because the container images have to be pulled. The
rollout waits and the HTTP polling both use generous timeouts with backoff to
ride that out.

## Layout

```
manifests/
  namespace.yaml      the oss-monitoring namespace
  prometheus.yaml     ConfigMap, Deployment, Service
  grafana.yaml        Deployment, Service, provisioning ConfigMaps
src/
  stack.py            apply, rollout wait, port-forward, teardown helpers
tests/
  conftest.py         session fixture that brings the stack up and down
  test_stack.py       the API checks
```
