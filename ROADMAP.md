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
| 4 | Terragrunt (VPC + SG + TGW + EC2 modules) | run --all apply + assert vs LocalStack | ✅ |
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

## Trading systems (pure Python, no services)

Software engineering examples that model the core of a trading stack. They run on
the standard library alone, so they need no docker or minikube and their tests are
fast and deterministic:

- **examples/limit-order-book** — a continuous matching engine with price and
  time priority: limit and market orders, partial fills, cancels, and trades that
  print at the resting price. 12 tests.
- **examples/ohlcv-aggregator** — resamples a raw trade stream into fixed interval
  OHLCV candles with a volume weighted average price. 12 tests.
- **examples/position-pnl** — tracks net position, weighted average entry, and
  realized and unrealized P&L from a stream of fills, including a long to short
  flip. 18 tests.

Run them with `make test-limit-order-book`, `make test-ohlcv-aggregator`,
`make test-position-pnl` (no services needed).

## Terragrunt on LocalStack

The old single file Terraform example was replaced by a Terragrunt stack that
reuses the most widely used registry modules, all applied against LocalStack:

- **examples/terragrunt-localstack** — a root config shares one LocalStack wired
  AWS provider, and four units composed through `dependency` blocks: a VPC
  (`terraform-aws-modules/vpc`), a security group
  (`terraform-aws-modules/security-group`), a transit gateway
  (`terraform-aws-modules/transit-gateway`, RAM sharing off since it is Pro
  only), and EC2 nodes via a local `modules/nodes` wrapper around
  `terraform-aws-modules/ec2-instance`. `terragrunt run --all apply` brings it up
  and 8 tests assert every piece with boto3. The EC2 unit pins the AWS provider
  to 5.x (provider 6 dropped arguments the ec2-instance module still uses).

Needs `terragrunt` and `terraform` on the PATH and `make up` (LocalStack now has
`ec2` enabled). Run it with `make test-terragrunt-localstack`.

## Tools shown without an example

These stay on the grid because they are part of the stack, but carry no link and
no negative note. A tool gets a link only once a real tested example exists:

- **AWS Fargate** — serverless compute, not represented by the minikube example.
- **AWS Budgets / Cost Anomaly Detection** — LocalStack Pro only APIs.
- **Feature branch environments** — a way of working, shown through the CI setup.
