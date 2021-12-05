import pytest
from fastapi.testclient import TestClient


def test_registers_returns_204_upon_success(client: TestClient) -> None:
    response = client.post(
        "/auth/registration",
        json={
            "username": "test@enforcer.pl",
            "password": "Password1!",
        },
    )

    assert response.status_code == 204


def test_registration_fails_if_email_already_taken(client: TestClient) -> None:
    client.post(
        "/auth/registration",
        json={
            "username": "test@enforcer.pl",
            "password": "Password1!",
        },
    )
    response = client.post(
        "/auth/registration",
        json={
            "username": "test@enforcer.pl",
            "password": "Password1!",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"errors": ["Email already taken"]}


def test_can_login_after_registration(client: TestClient) -> None:
    client.post(
        "/auth/registration",
        json={
            "username": "test+1@enforcer.pl",
            "password": "Password1!",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "test+1@enforcer.pl",
            "password": "Password1!",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json()["token"], str)


def test_cannot_login_using_invalid_creds(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={
            "username": "test+2@enforcer.pl",
            "password": "NO!",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"errors": ["Credentials invalid"]}


@pytest.fixture(autouse=True)
def clear() -> None:
    import asyncio

    from mbex import auth

    cleaning_loop = asyncio.new_event_loop()

    cleaning_loop.run_until_complete(auth.clear())
    yield
    cleaning_loop.run_until_complete(auth.clear())
