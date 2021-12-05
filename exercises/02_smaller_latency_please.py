import time
import uuid
import pathlib
from datetime import timedelta

import requests


ROOT = "http://localhost:8000"

directory = pathlib.Path(__file__).parent / "files"


def main() -> None:
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
            },
            timeout=1,
        )
        response.raise_for_status()
        order_id = response.json()["order_id"]

        time.sleep(0.01)

        response = requests.delete(
            ROOT + f"/trading/ETH-BTC/orders/{order_id}",
            headers={"Authorization": token},
            timeout=1,
        )
        response.raise_for_status()
        latencies.append(response.elapsed)

    print(
        f"Latencies [ms]: {[_s_to_ms(l) for l in latencies]}\n"
        f"max: {_s_to_ms(max(latencies))} ms\n"
        f"min: {_s_to_ms(min(latencies))} ms\n"
        f"avg: {(sum([l.total_seconds() for l in latencies]) / len(latencies)) * 1000:.3f} ms"
    )


def _s_to_ms(td: timedelta) -> str:
    num = td / timedelta(milliseconds=1)
    return f"{num:.3f}"


if __name__ == '__main__':
    main()
