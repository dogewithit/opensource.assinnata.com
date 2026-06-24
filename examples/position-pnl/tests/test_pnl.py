"""Tests for the weighted-average-cost position and P&L engine.

P&L numbers are asserted exactly: the engine uses Decimal end to end, so there
is no float fuzz to tolerate.
"""

from decimal import Decimal

import pytest

from src.pnl import Position


def D(x: str) -> Decimal:
    return Decimal(x)


def test_buy_twice_builds_weighted_average_entry():
    # Buy 10 @ 100, then 30 @ 120 -> avg = (10*100 + 30*120) / 40 = 115.
    pos = Position()
    pos.apply("buy", 10, 100)
    pos.apply("buy", 30, 120)

    assert pos.quantity == D("40")
    assert pos.avg_price == D("115")
    assert pos.realized_pnl == D("0")  # adding never realizes


def test_partial_sell_realizes_pnl_and_keeps_avg_price():
    # Long 10 @ 100, sell 4 @ 130 -> realize 4 * (130 - 100) = 120.
    pos = Position()
    pos.apply("buy", 10, 100)
    pos.apply("sell", 4, 130)

    assert pos.quantity == D("6")
    assert pos.avg_price == D("100")  # remainder keeps original cost
    assert pos.realized_pnl == D("120")


def test_full_close_realizes_total_and_goes_flat():
    # Long 10 @ 100, sell 10 @ 90 -> realize 10 * (90 - 100) = -100, then flat.
    pos = Position()
    pos.apply("buy", 10, 100)
    pos.apply("sell", 10, 90)

    assert pos.quantity == D("0")
    assert pos.is_flat
    assert pos.avg_price is None  # flat -> no meaningful price
    assert pos.realized_pnl == D("-100")


def test_flip_long_to_short():
    # Long 5 @ 100, sell 8 @ 110: close 5 (realize 5*(110-100)=50), open short 3
    # at 110.
    pos = Position()
    pos.apply("buy", 5, 100)
    pos.apply("sell", 8, 110)

    assert pos.quantity == D("-3")  # now short 3
    assert pos.avg_price == D("110")  # new position priced at the fill
    assert pos.realized_pnl == D("50")
    # The new short marked at its own entry shows no unrealized P&L yet.
    assert pos.unrealized(110) == D("0")


def test_flip_short_to_long():
    # Short 5 @ 100, buy 8 @ 90: close short 5 (realize 5*(100-90)=50), open
    # long 3 at 90.
    pos = Position()
    pos.apply("sell", 5, 100)
    pos.apply("buy", 8, 90)

    assert pos.quantity == D("3")
    assert pos.avg_price == D("90")
    assert pos.realized_pnl == D("50")


def test_short_side_pnl_profit_when_buy_below_sell():
    # Sell 10 @ 100 to open, buy 10 @ 80 to close -> profit 10*(100-80)=200.
    pos = Position()
    pos.apply("sell", 10, 100)
    assert pos.quantity == D("-10")
    assert pos.avg_price == D("100")

    pos.apply("buy", 10, 80)
    assert pos.is_flat
    assert pos.realized_pnl == D("200")


def test_fees_reduce_realized_pnl():
    # Buy 10 @ 100 (fee 1), sell 10 @ 110 (fee 2): gross 100, fees 3 -> 97.
    pos = Position()
    pos.apply("buy", 10, 100, fee=1)
    pos.apply("sell", 10, 110, fee=2)

    assert pos.realized_pnl == D("97")


def test_fee_applies_even_when_only_opening():
    # A fill that just opens still books its fee against realized P&L.
    pos = Position()
    pos.apply("buy", 10, 100, fee="0.5")

    assert pos.realized_pnl == D("-0.5")
    assert pos.quantity == D("10")
    assert pos.avg_price == D("100")


def test_unrealized_marks_open_position_and_is_zero_when_flat():
    pos = Position()
    assert pos.unrealized(123) == D("0")  # flat

    pos.apply("buy", 10, 100)
    assert pos.unrealized(105) == D("50")  # long gains as mark rises
    assert pos.unrealized(95) == D("-50")  # and loses as it falls

    pos.apply("sell", 10, 100)  # close flat
    assert pos.unrealized(999) == D("0")


def test_unrealized_for_short_position():
    # Short 10 @ 100: gains when mark drops below entry.
    pos = Position()
    pos.apply("sell", 10, 100)
    assert pos.unrealized(90) == D("100")  # 10 * (100 - 90)
    assert pos.unrealized(110) == D("-100")


def test_total_pnl_sums_realized_and_unrealized():
    # Long 10 @ 100, sell 4 @ 130 -> realized 120, remainder long 6 @ 100.
    pos = Position()
    pos.apply("buy", 10, 100)
    pos.apply("sell", 4, 130)

    # At mark 120: unrealized = 6 * (120 - 100) = 120; total = 240.
    assert pos.unrealized(120) == D("120")
    assert pos.total_pnl(120) == D("240")
    assert pos.total_pnl(120) == pos.realized_pnl + pos.unrealized(120)


def test_decimal_inputs_stay_exact():
    # Three buys of 0.1 @ prices that float math would smear; Decimal stays exact.
    pos = Position()
    pos.apply("buy", "0.1", "100.10")
    pos.apply("buy", "0.2", "100.40")  # avg = (0.1*100.10 + 0.2*100.40)/0.3
    assert pos.quantity == D("0.3")
    assert pos.avg_price == D("100.30")


@pytest.mark.parametrize(
    "side,qty,price,fee",
    [
        ("buy", 0, 100, 0),  # qty must be > 0
        ("buy", -1, 100, 0),
        ("buy", 10, 0, 0),  # price must be > 0
        ("buy", 10, -5, 0),
        ("buy", 10, 100, -1),  # fee must be >= 0
    ],
)
def test_invalid_inputs_raise_value_error(side, qty, price, fee):
    pos = Position()
    with pytest.raises(ValueError):
        pos.apply(side, qty, price, fee=fee)


def test_invalid_side_raises():
    pos = Position()
    with pytest.raises(ValueError):
        pos.apply("hold", 10, 100)
