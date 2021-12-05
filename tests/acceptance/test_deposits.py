import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("disable_password_hashing", "clear_all")


def test_should_return_401_in_case_of_lack_of_jwt_token(client: TestClient) -> None:
    response = client.get("/wallets/balances/BTC")

    assert response.status_code == 401


def test_initial_balance_is_0(token: str, client: TestClient) -> None:
    response = client.get("/wallets/balances/BTC", headers={"Authorization": token})

    assert response.status_code == 200
    assert response.json() == {"balance": "0"}


def test_balance_increases_after_depositing_some_crypto(
    token: str, client: TestClient
) -> None:
    response = client.post(
        "/wallets/balances/BTC/deposit",
        headers={"Authorization": token},
        json={"amount": "1.00000001"},
    )
    assert response.status_code == 202

    balance_response = client.get(
        "/wallets/balances/BTC", headers={"Authorization": token}
    )
    assert balance_response.status_code == 200
    assert balance_response.json() == {"balance": "1.00000001"}
