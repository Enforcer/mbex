import pytest
from fastapi.testclient import TestClient

from mbex.api.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def disable_password_hashing() -> None:
    """Use simple implementations to speed up tests."""
    from typing import Any
    from unittest.mock import patch

    import bcrypt

    def fake_hash_pw(password_as_bytes: bytes, _salt: Any) -> bytes:
        return password_as_bytes

    def fake_gensalt(rounds: int) -> bytes:
        return b""

    def fake_checkpw(password_as_bytes, hashed_password: bytes) -> bool:
        return password_as_bytes == hashed_password

    with patch.object(bcrypt, "hashpw", new=fake_hash_pw):
        with patch.object(bcrypt, "gensalt", new=fake_gensalt):
            with patch.object(bcrypt, "checkpw", new=fake_checkpw):
                yield


ids = iter(range(100_000))


@pytest.fixture()
def token(client: TestClient) -> str:
    username = f"test+username+{next(ids)}@enforcer.pl"
    register_response = client.post(
        "/auth/registration",
        json={"username": username, "password": "123"},
    )
    assert register_response.status_code == 204, register_response.json()

    login_response = client.post(
        "/auth/login", json={"username": username, "password": "123"}
    )
    assert login_response.status_code == 200
    return login_response.json()["token"]


@pytest.fixture()
def clear_all() -> None:
    import asyncio

    from mbex import auth, trading, wallets

    cleaning_loop = asyncio.new_event_loop()
    cleaning_loop.run_until_complete(auth.clear())
    cleaning_loop.run_until_complete(wallets.clear())
    trading.clear()
    yield
    cleaning_loop.run_until_complete(auth.clear())
    cleaning_loop.run_until_complete(wallets.clear())
    trading.clear()
