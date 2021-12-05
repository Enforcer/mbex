import time
import uuid
import pathlib
import statistics
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
    requests.post(
        ROOT + "/wallets/balances/ETH/deposit",
        headers={"Authorization": token},
        json={"amount": "50"},
    ).raise_for_status()

    cancel_latencies = []
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
        cancel_latencies.append(response.elapsed)

    print("=*= CANCEL LATENCIES =*=")
    print(
        f"Latencies [ms]: {[_s_to_ms(l) for l in cancel_latencies]}\n"
        f"max: {_s_to_ms(max(cancel_latencies))} ms\n"
        f"min: {_s_to_ms(min(cancel_latencies))} ms\n"
        f"avg: {(sum([l.total_seconds() for l in cancel_latencies]) / len(cancel_latencies)) * 1000:.3f} ms\n"
        f"std dev: {statistics.stdev([l.total_seconds() * 1000 for l in cancel_latencies]):.3f} ms"
    )

    place_order_latencies = []
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
        place_order_latencies.append(response.elapsed)

        time.sleep(0.01)

        response = requests.post(
            ROOT + "/trading/ETH-BTC/orders",
            headers={"Authorization": token},
            json={
                "volume": "1",
                "price": "1",
                "side": "ask",
            },
            timeout=1,
        )
        response.raise_for_status()
        place_order_latencies.append(response.elapsed)

    print("=*= PLACE ORDER LATENCIES =*=")
    print(
        f"Latencies [ms]: {[_s_to_ms(l) for l in place_order_latencies]}\n"
        f"max: {_s_to_ms(max(place_order_latencies))} ms\n"
        f"min: {_s_to_ms(min(place_order_latencies))} ms\n"
        f"avg: {(sum([l.total_seconds() for l in place_order_latencies]) / len(place_order_latencies)) * 1000:.3f} ms\n"
        f"std dev: {statistics.stdev([l.total_seconds() * 1000 for l in place_order_latencies]):.3f} ms"
    )


def _s_to_ms(td: timedelta) -> str:
    num = td / timedelta(milliseconds=1)
    return f"{num:.3f}"


if __name__ == '__main__':
    main()
