# Prometheus trade metrics

Trade counters and a notional histogram exposed in the **Prometheus** text
format, validated by asserting on the exposition output.

> **Prometheus** tool example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- A labelled `trades_total` counter and a `trade_notional_usd` histogram.
- Per-instance `CollectorRegistry` (no process-global state — clean tests).
- `render()` produces exactly what a `/metrics` endpoint would serve.

## Run the tests

```bash
make test-prometheus-metrics   # no docker services needed
```

## Reference

Source: [`examples/prometheus-metrics`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/prometheus-metrics)
· prometheus_client: <https://github.com/prometheus/client_python>
