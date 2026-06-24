# Limit order book

A continuous limit order book and matching engine that fills crossing orders by
price-time priority: the best price wins, and orders resting at the same price
fill in arrival order (FIFO). Trades print at the resting (maker) order's price.

> **Software engineering** example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- **Price-time priority** matching: best price first, then FIFO within a level,
  with trades executing at the maker's resting price.
- Limit, market, and cancel flows with **partial fills** that preserve the
  remaining quantity and the resting order's time priority.
- Exact pricing with `decimal.Decimal` (float prices are rejected), no network,
  no clock reads, and a deterministic internal sequence counter for replayable
  matching.

## Run the tests

```bash
make test-limit-order-book   # no docker services needed
```

## Reference

Source: [`examples/limit-order-book`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/limit-order-book)
