# OHLCV candle aggregator

Resamples a stream of trades (ticks) into fixed-interval OHLCV bars with a
volume-weighted average price, exactly the way a market-data platform builds
time bars off a live feed. Pure Python standard library, deterministic, no
network and no clock.

> **Software engineering** example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- A streaming **trade to OHLCV** aggregator: each trade is floored into its
  interval bucket, and a trade that opens a later bucket closes the prior bar.
- **Exact VWAP** with `decimal.Decimal`, so `sum(price * size) / sum(size)` has
  no binary-float drift.
- Defensive, deterministic logic: non-decreasing timestamps are enforced,
  bad price/size raises, empty gap buckets emit no synthetic candles, and all
  timestamps are passed in so there is nothing to mock.

## Run the tests

```bash
make test-ohlcv-aggregator   # no docker services needed
```

## Reference

Source: [`examples/ohlcv-aggregator`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/ohlcv-aggregator)
