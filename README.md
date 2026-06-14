# opensource.assinnata.com

**Live at [assinnata.com](https://assinnata.com)** (Cloudflare Pages, auto-deployed on every green push to main).

An open source site showcasing the tools [Matteo Assinnata](https://linkedin.com/in/assinnata)
— Trading Infrastructure Engineer — uses day-to-day, **with a tested code example
behind each one**. An example that doesn't pass its tests locally (against
LocalStack 4.14 + Postgres) is rejected and gets no link. See [ROADMAP.md](ROADMAP.md).

## Structure

```
.
├── frontend/                    # Astro static site (the showcase)
├── examples/
│   ├── hyperliquid-crawler/     # Hyperliquid outcome markets -> Postgres   (14 tests)
│   ├── aws-localstack/          # S3 + DynamoDB market-artifact store         (5 tests)
│   ├── terraform-localstack/    # Terraform via tflocal, apply + assert       (3 tests)
│   ├── opentelemetry-tracing/   # OTel spans, in-memory exporter              (3 tests)
│   └── prometheus-metrics/      # Prometheus metrics + exposition format      (3 tests)
├── docker-compose.yml           # LocalStack 4.14 + Postgres 16
├── Makefile                     # make up / test / down
└── .github/workflows/ci.yml     # runs every suite in CI (the tested-or-rejected gate)
```

Each example is `examples/{project}/{src,tests}` with its own `requirements.txt`
and `README.md`.

## Validate everything locally

```bash
make up      # start LocalStack 4.14 + Postgres 16 (Postgres on host :55432)
make test    # run all 28 tests across every example
make down    # tear down
```

Run one example: `make test-hyperliquid-crawler`.

Requirements: Docker + Compose, Python 3.12+, and Terraform (for the Terraform
example) — `brew install hashicorp/tap/terraform`.

## Frontend

```bash
make frontend          # or: cd frontend && npm install && npm run dev
```

Content is data-driven in `frontend/src/data/`:
- `tools.ts` — tools, categories, proficiency, and the tested-example link per tool
- `site.ts` — profile, summary, links

## License

MIT — see [LICENSE](LICENSE).
