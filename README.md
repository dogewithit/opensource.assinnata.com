# opensource.assinnata.com

**Live at [assinnata.com](https://assinnata.com)** (Cloudflare Pages, auto-deployed on every green push to main).

An open source site showcasing the tools [Matteo Assinnata](https://linkedin.com/in/assinnata),
Trading Infrastructure Engineer, uses day to day, **with a tested code example
behind each one**. A tool links to an example only when that example passes its
tests locally against LocalStack 4.14, Postgres, or a minikube cluster. See
[ROADMAP.md](ROADMAP.md).

## Structure

```
.
├── frontend/                        # Astro static site (the showcase)
├── examples/
│   ├── hyperliquid-crawler/         # live Hyperliquid markets -> Postgres        (18 tests)
│   ├── aws-localstack/              # S3 + DynamoDB market artifact store          (5 tests)
│   ├── terraform-localstack/        # Terraform via tflocal, apply + assert        (3 tests)
│   ├── opentelemetry-tracing/       # OTel spans, in memory exporter               (3 tests)
│   ├── prometheus-metrics/          # Prometheus metrics + exposition format       (3 tests)
│   ├── kubernetes-minikube/         # Deployment + Service + scaling on minikube   (4 tests)
│   └── grafana-prometheus-minikube/ # Prometheus + Grafana dashboards on minikube  (7 tests)
├── docker-compose.yml               # LocalStack 4.14 + Postgres 16
├── Makefile                         # make up / test / down / minikube-up
└── .github/workflows/ci.yml         # runs every suite in CI
```

Each example is `examples/{project}/{src,tests}` with its own `requirements.txt`
and `README.md`.

## Validate everything locally

```bash
make up            # start LocalStack 4.14 + Postgres 16 (Postgres on host :55432)
make minikube-up   # start a minikube cluster (for the Kubernetes and Grafana examples)
make test          # run all 43 tests across every example
make down          # tear down
```

Run one example: `make test-hyperliquid-crawler`.

Requirements: Docker + Compose, Python 3.12+, Terraform (`brew install
hashicorp/tap/terraform`), and minikube + kubectl (`brew install minikube
kubectl`) for the Kubernetes and Grafana examples.

## Frontend

```bash
make frontend          # or: cd frontend && npm install && npm run dev
```

Content is data-driven in `frontend/src/data/`:
- `tools.ts` — tools, categories, proficiency, and the tested-example link per tool
- `site.ts` — profile, summary, links

## License

MIT — see [LICENSE](LICENSE).
