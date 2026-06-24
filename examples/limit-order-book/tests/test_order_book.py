"""Tests for the price-time-priority limit order book."""

from decimal import Decimal

import pytest

from src.order_book import Fill, OrderBook, Trade


def D(x):
    return Decimal(str(x))


def test_non_crossing_order_rests_and_sets_top_of_book():
    book = OrderBook()
    assert book.best_bid() is None and book.best_ask() is None

    assert book.add_limit_order("buy", "100", 10, "b1") == []
    assert book.add_limit_order("sell", "101", 5, "a1") == []

    assert book.best_bid() == D("100")
    assert book.best_ask() == D("101")
    assert book.spread() == D("1")


def test_aggressive_order_crosses_and_fills():
    book = OrderBook()
    book.add_limit_order("sell", "101", 5, "a1")

    fills = book.add_limit_order("buy", "101", 5, "b1")

    assert fills == [Fill(maker_id="a1", taker_id="b1", price=D("101"), qty=5)]
    # Both orders fully consumed: the book is empty again.
    assert book.best_ask() is None
    assert book.best_bid() is None


def test_time_priority_within_a_price_level():
    book = OrderBook()
    # Two resting asks at the same price; a1 arrived first.
    book.add_limit_order("sell", "101", 5, "a1")
    book.add_limit_order("sell", "101", 5, "a2")

    fills = book.add_limit_order("buy", "101", 5, "buyer")

    # FIFO: the earlier order (a1) fills first, a2 stays untouched.
    assert [f.maker_id for f in fills] == ["a1"]
    assert book.best_ask() == D("101")
    fills2 = book.add_limit_order("buy", "101", 5, "buyer2")
    assert [f.maker_id for f in fills2] == ["a2"]


def test_price_priority_better_price_fills_first():
    book = OrderBook()
    book.add_limit_order("sell", "102", 5, "high")
    book.add_limit_order("sell", "101", 5, "low")  # better (lower) ask

    fills = book.add_limit_order("buy", "102", 5, "buyer")

    # The cheaper ask fills first, and it prints at the maker price (101).
    assert fills == [Fill(maker_id="low", taker_id="buyer", price=D("101"), qty=5)]
    assert book.best_ask() == D("102")


def test_partial_fill_leaves_correctly_sized_resting_remainder():
    book = OrderBook()
    book.add_limit_order("sell", "101", 10, "a1")

    fills = book.add_limit_order("buy", "101", 3, "b1")
    assert fills == [Fill("a1", "b1", D("101"), 3)]

    # 7 left on the ask, still best ask, still owned by a1 (time priority kept).
    assert book.best_ask() == D("101")
    more = book.add_limit_order("buy", "101", 7, "b2")
    assert more == [Fill("a1", "b2", D("101"), 7)]
    assert book.best_ask() is None


def test_aggressor_remainder_rests_on_the_book():
    book = OrderBook()
    book.add_limit_order("sell", "101", 4, "a1")

    fills = book.add_limit_order("buy", "101", 10, "b1")
    assert fills == [Fill("a1", "b1", D("101"), 4)]
    # 6 unfilled units of the buy rest as the new best bid.
    assert book.best_bid() == D("101")
    assert book.best_ask() is None


def test_market_order_sweeps_multiple_levels():
    book = OrderBook()
    book.add_limit_order("sell", "101", 5, "a1")
    book.add_limit_order("sell", "102", 5, "a2")
    book.add_limit_order("sell", "103", 5, "a3")

    fills = book.add_market_order("buy", 12, "mkt")

    # Sweeps cheapest first: 5@101, 5@102, 2@103.
    assert [(f.maker_id, f.price, f.qty) for f in fills] == [
        ("a1", D("101"), 5),
        ("a2", D("102"), 5),
        ("a3", D("103"), 2),
    ]
    assert book.best_ask() == D("103")  # 3 left on a3


def test_market_order_with_insufficient_liquidity_fills_what_it_can():
    book = OrderBook()
    book.add_limit_order("sell", "101", 3, "a1")

    fills = book.add_market_order("buy", 10, "mkt")

    assert fills == [Fill("a1", "mkt", D("101"), 3)]
    # Market order never rests, even with an unfilled remainder.
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_cancel_removes_resting_order_and_reports_found():
    book = OrderBook()
    book.add_limit_order("buy", "100", 5, "b1")

    assert book.cancel("b1") is True
    assert book.best_bid() is None
    # Unknown id returns False; cancelling twice also returns False.
    assert book.cancel("b1") is False
    assert book.cancel("nope") is False


def test_trades_execute_at_the_maker_price_not_the_aggressor_limit():
    book = OrderBook()
    book.add_limit_order("buy", "100", 5, "resting_bid")

    # Aggressive sell willing to go down to 99, but the maker bid is at 100.
    fills = book.add_limit_order("sell", "99", 5, "seller")

    assert fills == [Fill("resting_bid", "seller", D("100"), 5)]


def test_validation_rejects_bad_inputs():
    book = OrderBook()
    with pytest.raises(ValueError):
        book.add_limit_order("buy", "100", 0, "x")  # qty == 0
    with pytest.raises(ValueError):
        book.add_limit_order("buy", "100", -1, "x")  # qty < 0
    with pytest.raises(ValueError):
        book.add_limit_order("buy", "0", 5, "x")  # price == 0
    with pytest.raises(ValueError):
        book.add_limit_order("buy", "-5", 5, "x")  # price < 0
    with pytest.raises(ValueError):
        book.add_limit_order("hold", "100", 5, "x")  # bad side
    with pytest.raises(ValueError):
        book.add_limit_order("buy", 1.5, 5, "x")  # float price rejected
    with pytest.raises(ValueError):
        book.add_market_order("buy", 0, "x")  # market qty must be > 0


def test_trade_alias_is_fill():
    assert Trade is Fill
