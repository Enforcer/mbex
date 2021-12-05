from decimal import Decimal
from typing import Literal

from attr import attrib, define
from fastapi.testclient import TestClient

OrderId = str


@define
class Api:
    _client: TestClient
    _token: str
    _auth_header: dict = attrib(init=False)

    def __attrs_post_init__(self) -> None:
        self._auth_header = {"Authorization": self._token}

    def deposit(self, currency: str, amount: Decimal = Decimal(1)) -> None:
        response = self._client.post(
            f"/wallets/balances/{currency}/deposit",
            headers=self._auth_header,
            json={"amount": f"{amount}"},
        )
        assert response.status_code == 202, "Deposit failed"

    def balance(self, currency: str) -> Decimal:
        response = self._client.get(
            f"/wallets/balances/{currency}",
            headers=self._auth_header,
        )
        assert response.status_code == 200
        return Decimal(response.json()["balance"])

    def bid(
        self,
        volume: Decimal,
        price: Decimal,
        market="ETH-BTC",
    ) -> OrderId:
        return self._place_order(volume=volume, price=price, market=market, side="bid")

    def ask(
        self,
        volume: Decimal,
        price: Decimal,
        market="ETH-BTC",
    ) -> OrderId:
        return self._place_order(volume=volume, price=price, market=market, side="ask")

    def _place_order(
        self,
        volume: Decimal,
        price: Decimal,
        market="ETH-BTC",
        side: Literal["bid", "ask"] = "bid",
    ) -> OrderId:
        response = self._client.post(
            f"trading/{market}/orders",
            headers=self._auth_header,
            json={
                "volume": str(volume),
                "price": str(price),
                "side": side,
            },
        )
        assert response.status_code == 202
        return response.json()["order_id"]

    def cancel_order(self, order_id: OrderId, market="ETH-BTC") -> None:
        response = self._client.delete(
            f"trading/{market}/orders/{order_id}",
            headers=self._auth_header,
        )
        response.raise_for_status()
        assert response.status_code == 202

    def order_book(self, market="ETH-BTC") -> dict:
        response = self._client.get(f"trading/{market}/order_book")
        assert response.status_code == 200
        return response.json()
