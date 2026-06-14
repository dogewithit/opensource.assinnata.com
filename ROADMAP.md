# Roadmap

Goal: every tool shown on **opensource.assinnata.com** links to a **real, tested
software example** in this repo. An example without tests that pass locally
(against LocalStack 4.14 + Postgres) is **rejected** — it does not ship and its
tool card does not get an example link.

## Repository structure

```
.
├── frontend/                 # Astro static site (the showcase)
├── examples/
│   └── {project}/
│       ├── src/              # the example implementation
│       ├── tests/            # pytest suite — REQUIRED, run in CI + `make test`
│       ├── requirements.txt
│       └── README.md         # what it shows + GitHub reference link
├── docker-compose.yml        # LocalStack 4.14 + Postgres 16
├── Makefile                  # make up / test / down
└── ROADMAP.md
```

## Definition of done (per example)

1. Lives in `examples/{project}/` with `src/` + `tests/`.
2. `make test-{project}` passes locally against the docker stack.
3. Has a `README.md` with a one-line "what it demonstrates" and a GitHub link.
4. The matching tool card in `frontend/src/data/tools.ts` carries the example
   reference (repo path + GitHub URL). Untested tools carry **no** link and are
   marked `rejected` with a reason.

## Steps

| # | Element | Local validation | Status |
|---|---------|------------------|--------|
| 1 | Foundation: structure, docker-compose, Makefile | `make up` healthy | ✅ |
| 2 | **Hyperliquid outcome-markets crawler** → Postgres | pytest + Postgres | ▶ in progress |
| 3 | AWS (S3 + DynamoDB) | pytest + LocalStack | ⏳ |
| 4 | Terraform (tflocal) | apply + assert vs LocalStack | ⏳ |
| 5 | OpenTelemetry instrumentation | pytest in-memory exporter | ⏳ |
| 6 | Prometheus metrics endpoint | pytest exposition format | ⏳ |
| 7 | Wire frontend cards → example links | `npm run build` | ⏳ |
| 8 | CI: GitHub Actions runs all suites | green workflow | ⏳ |
| 9 | Create GitHub repo + push | links resolve | ⏳ |

## Kubernetes and Grafana on minikube

Added later, validated on a local minikube cluster (profile `oss`):

- **examples/kubernetes-minikube** — deploys a Deployment + Service, waits for
  rollout, scales it, and reaches the service from inside the cluster. Backs the
  Kubernetes and Amazon EKS cards. 4 tests.
- **examples/grafana-prometheus-minikube** — deploys Prometheus + Grafana with a
  provisioned datasource and dashboard, tested through their HTTP APIs. Backs the
  Grafana card. 7 tests.

Run them with `make minikube-up` then `make test-kubernetes-minikube` /
`make test-grafana-prometheus-minikube`.

## Tools shown without an example

These stay on the grid because they are part of the stack, but carry no link and
no negative note. A tool gets a link only once a real tested example exists:

- **AWS Fargate** — serverless compute, not represented by the minikube example.
- **AWS Budgets / Cost Anomaly Detection** — LocalStack Pro only APIs.
- **Feature branch environments** — a way of working, shown through the CI setup.
