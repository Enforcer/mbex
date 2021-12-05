import time
import uuid
from datetime import timedelta

import requests
import threading

ROOT = "http://localhost:8000"
MAX_ACCEPTED_LATENCY = timedelta(milliseconds=50)


def main() -> None:
    other_clients_thread = threading.Thread(target=keep_registering, daemon=True)
    other_clients_thread.start()

    login = f"{uuid.uuid4()}@enforcer.pl"
    requests.post(ROOT + "/auth/registration", json={
        "username": login,
        "password": "PASSWORD",
    }).raise_for_status()
    response = requests.post(ROOT + "/auth/login", json={
        "username": login,
        "password": "PASSWORD",
    })
    response.raise_for_status()
    token = response.json()["token"]
    requests.post(
        ROOT + "/wallets/balances/BTC/deposit",
        headers={"Authorization": token},
        json={"amount": "50"},
    ).raise_for_status()

    latencies = []
    for _ in range(10):
        response = requests.post(
            ROOT + "/trading/ETH-BTC/orders",
            headers={"Authorization": token},
            json={
                "volume": "1",
                "price": "1",
                "side": "bid",
            }
        )
        response.raise_for_status()
        _check_latency(response)
        latencies.append(response.elapsed)
        order_id = response.json()["order_id"]

        time.sleep(0.01)

        response = requests.delete(
            ROOT + f"/trading/ETH-BTC/orders/{order_id}",
            headers={"Authorization": token},
        )
        response.raise_for_status()
        _check_latency(response)
        latencies.append(response.elapsed)

    print(
        f"Latencies [ms]: {[_s_to_ms(l) for l in latencies]}\n"
        f"max: {_s_to_ms(max(latencies))} ms\n"
        f"min: {_s_to_ms(min(latencies))} ms\n"
        f"avg: {(sum([l.total_seconds() for l in latencies]) / len(latencies)) * 1000:.3f} ms"
    )


def keep_registering() -> None:
    while True:
        requests.post(ROOT + "/auth/registration", json={
                "username": f"{uuid.uuid4()}@enforcer.pl",
                "password": "PASSWORD",
        }).raise_for_status()


def _check_latency(response) -> None:
    assert response.elapsed <= MAX_ACCEPTED_LATENCY, f"Request lasted for {_s_to_ms(response.elapsed)} ms, {_s_to_ms(MAX_ACCEPTED_LATENCY)} ms is maximum allowed!"


def _s_to_ms(td: timedelta) -> str:
    num = td / timedelta(milliseconds=1)
    return f"{num:.3f}"


if __name__ == '__main__':
    main()
