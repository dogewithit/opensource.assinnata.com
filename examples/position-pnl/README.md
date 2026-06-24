# Position and P&L engine

Tracks a signed net position and its realized and unrealized P&L from a stream
of fills, using weighted-average-cost accounting and exact Decimal arithmetic.

> **Software engineering** example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- Weighted-average-cost entry pricing: adding in the same direction reprices the
  open position and realizes nothing, while opposite fills realize P&L on the
  closed quantity against the average cost.
- Correct **position flips**: a fill larger than the open opposite position
  closes it in full, realizes that P&L, and opens a new position in the other
  direction at the fill price.
- Exact P&L with `decimal.Decimal` end to end (no float drift), fees that always
  reduce realized P&L, and a pure deterministic core with no IO, clock, or
  randomness.

## Run the tests

```bash
make test-position-pnl   # no docker services needed
```

## Reference

Source: [`examples/position-pnl`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/position-pnl)
