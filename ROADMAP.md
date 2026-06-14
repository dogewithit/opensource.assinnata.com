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

## Rejected (no local test harness — honoring the tested-or-rejected rule)

These tools stay on the grid for honesty about the stack, but get **no example
link** until a tested example exists:

- **Amazon EKS / AWS Fargate / Kubernetes** — not reproducible on LocalStack
  community; would need `kind`/a real cluster to test meaningfully.
- **Grafana** — dashboards are JSON config, not unit-testable in isolation.
- **AWS Budgets / Cost Anomaly Detection** — LocalStack Pro-only APIs.

Revisit if/when a credible local test exists for each.
