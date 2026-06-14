# OpenTelemetry trade tracing

A trade-execution function instrumented with **OpenTelemetry** spans, verified
with an in-memory span exporter — no collector required to test.

> **OpenTelemetry** tool example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- Spans with domain attributes (`trade.market_id`, `trade.side`, `trade.notional`).
- OK vs ERROR span status, including error recording on invalid orders.
- Provider-agnostic code: in-memory exporter in tests, OTLP collector in prod.

## Run the tests

```bash
make test-opentelemetry-tracing   # no docker services needed
```

## Reference

Source: [`examples/opentelemetry-tracing`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/opentelemetry-tracing)
· OpenTelemetry Python: <https://opentelemetry.io/docs/languages/python/>
