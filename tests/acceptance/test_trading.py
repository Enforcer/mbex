from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from requests import HTTPError

from tests.acceptance.api import Api

pytestmark = pytest.mark.usefixtures("disable_password_hashing", "clear_all")


@pytest.fixture()
def api(token: str, client: TestClient) -> Api:
    return Api(client=client, token=token)


def test_placing_bid_lowers_balance_and_makes_order_visible_in_order_book(
    api: Api,
) -> None:
    api.deposit(currency="BTC", amount=Decimal("1"))
    api.bid(volume=Decimal(1), price=Decimal(1), market="ETH-BTC")

    balance = api.balance(currency="BTC")
    assert balance == Decimal("0")
    order_book = api.order_book(market="ETH-BTC")
    assert order_book == {
        "asks": [],
        "bids": [
            {"price": "1", "volume": "1"},
        ],
    }


def test_placing_ask_lowers_balance_and_order_lands_in_order_book(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("1"))
    api.ask(volume=Decimal(1), price=Decimal(1), market="ETH-BTC")

    balance = api.balance(currency="ETH")
    assert balance == Decimal("0")
    order_book = api.order_book(market="ETH-BTC")
    assert order_book == {
        "asks": [
            {"price": "1", "volume": "1"},
        ],
        "bids": [],
    }


def test_cross_order(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("1"))
    api.deposit(currency="BTC", amount=Decimal("1"))
    api.bid(volume=Decimal(1), price=Decimal(1), market="ETH-BTC")
    api.ask(volume=Decimal(1), price=Decimal(1), market="ETH-BTC")

    assert api.balance(currency="ETH") == Decimal("1")
    assert api.balance(currency="BTC") == Decimal("1")
    assert api.order_book(market="ETH-BTC") == {
        "asks": [],
        "bids": [],
    }


def test_cross_order_partial_fill_executing_ask(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("1"))
    api.deposit(currency="BTC", amount=Decimal("1"))
    api.bid(volume=Decimal("0.5"), price=Decimal("1"), market="ETH-BTC")
    api.ask(volume=Decimal("1"), price=Decimal("1"), market="ETH-BTC")

    assert api.balance(currency="ETH") == Decimal("0.5")
    assert api.balance(currency="BTC") == Decimal("1")
    assert api.order_book(market="ETH-BTC") == {
        "asks": [{"price": "1", "volume": "0.5"}],
        "bids": [],
    }


def test_cross_order_partial_fill_executing_bid(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("1"))
    api.deposit(currency="BTC", amount=Decimal("1"))
    api.ask(volume=Decimal("1"), price=Decimal("1"), market="ETH-BTC")
    api.bid(volume=Decimal("0.5"), price=Decimal("1"), market="ETH-BTC")

    assert api.balance(currency="ETH") == Decimal("0.5")
    assert api.balance(currency="BTC") == Decimal("1")
    assert api.order_book(market="ETH-BTC") == {
        "asks": [{"price": "1", "volume": "0.5"}],
        "bids": [],
    }


def test_one_executing_bid_eats_up_all_asks(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("5"))
    api.deposit(currency="BTC", amount=Decimal("5"))
    api.ask(volume=Decimal("0.2"), price=Decimal(1), market="ETH-BTC")
    api.ask(volume=Decimal("0.2"), price=Decimal(3), market="ETH-BTC")
    api.ask(volume=Decimal("0.2"), price=Decimal(2), market="ETH-BTC")
    api.bid(volume=Decimal("0.6"), price=Decimal(3), market="ETH-BTC")

    assert api.balance(currency="ETH") == Decimal("5")
    assert api.balance(currency="BTC") == Decimal("5")
    assert api.order_book(market="ETH-BTC") == {
        "asks": [],
        "bids": [],
    }


def test_one_executing_ask_eats_up_all_bids(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("5"))
    api.deposit(currency="BTC", amount=Decimal("5"))
    api.bid(volume=Decimal("0.2"), price=Decimal(1), market="ETH-BTC")
    api.bid(volume=Decimal("0.2"), price=Decimal(3), market="ETH-BTC")
    api.bid(volume=Decimal("0.2"), price=Decimal(2), market="ETH-BTC")
    api.ask(volume=Decimal("0.6"), price=Decimal(0.5), market="ETH-BTC")

    assert api.balance(currency="ETH") == Decimal("5")
    assert api.balance(currency="BTC") == Decimal("5")
    assert api.order_book(market="ETH-BTC") == {
        "asks": [],
        "bids": [],
    }


def test_cancelling_order_returns_funds_and_empties_order_book(api: Api) -> None:
    api.deposit(currency="ETH", amount=Decimal("2"))
    order_id = api.ask(volume=Decimal("1"), price=Decimal("2"), market="ETH-BTC")

    api.cancel_order(order_id)

    assert api.balance(currency="ETH") == Decimal("2")
    assert api.order_book(market="ETH-BTC") == {
        "asks": [],
        "bids": [],
    }


def test_cant_cancel_not_existing_order(api: Api) -> None:
    try:
        api.cancel_order(order_id="i-dont-exist")
    except HTTPError as exc:
        assert exc.response.status_code == 404
    else:
        pytest.fail("Expected 404")
