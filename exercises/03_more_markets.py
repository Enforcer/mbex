import statistics
import time
import uuid
from datetime import timedelta

import requests
import threading

ROOT = "http://localhost:8000"


def main() -> None:
    markets = ["001-002", "003-004", "005-006", "007-008", "009-010"]
    # markets = []  # uncomment to see how no other trading affects performance
    for market in markets:
        trader_thread = threading.Thread(
            target=trade_on_market,
            args=(market, ),
            daemon=True,
        )
        trader_thread.start()

    time.sleep(3)  # let them register

    token = new_user_token()
    deposit(token, currency="BTC", amount="50")

    latencies = []
    for _ in range(20):
        response = bid(token=token, market="ETH-BTC", price="1", amount="1")
        latencies.append(response.elapsed)
        order_id = response.json()["order_id"]

        time.sleep(0.01)

        response = cancel(token=token, market="ETH-BTC", order_id=order_id)
        latencies.append(response.elapsed)

    print(
        f"Latencies [ms]: {[_s_to_ms(l) for l in latencies]}\n"
        f"max: {_s_to_ms(max(latencies))} ms\n"
        f"min: {_s_to_ms(min(latencies))} ms\n"
        f"avg: {(sum([l.total_seconds() for l in latencies]) / len(latencies)) * 1000:.3f} ms\n"
        f"std dev: {statistics.stdev([l.total_seconds() * 1000 for l in latencies]):.3f} ms"
    )


def trade_on_market(market: str) -> None:
    token = new_user_token()
    base, quote = market.split("-")
    for currency in [base, quote]:
        deposit(token=token, currency=currency, amount="100")

    while True:
        for _ in range(50):
            bid(token=token, market=market, amount="1", price="1")

        ask(token=token, market=market, amount="50", price="1")
        time.sleep(0.001)


def new_user_token() -> str:
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
    return response.json()["token"]


def deposit(token: str, currency: str, amount: str) -> None:
    requests.post(
        ROOT + f"/wallets/balances/{currency}/deposit",
        headers={"Authorization": token},
        json={"amount": amount},
    ).raise_for_status()


def bid(token: str, market: str, amount: str, price: str) -> requests.Response:
    response = requests.post(
        ROOT + f"/trading/{market}/orders",
        headers={"Authorization": token},
        json={
            "volume": amount,
            "price": price,
            "side": "bid",
        }
    )
    response.raise_for_status()
    return response


def ask(token: str, market: str, amount: str, price: str) -> requests.Response:
    response = requests.post(
        ROOT + f"/trading/{market}/orders",
        headers={"Authorization": token},
        json={
            "volume": amount,
            "price": price,
            "side": "ask",
        }
    )
    response.raise_for_status()
    return response


def cancel(token: str, market: str, order_id: str) -> requests.Response:
    response = requests.delete(
        ROOT + f"/trading/{market}/orders/{order_id}",
        headers={"Authorization": token},
    )
    response.raise_for_status()
    return response


def _s_to_ms(td: timedelta) -> str:
    num = td / timedelta(milliseconds=1)
    return f"{num:.3f}"


if __name__ == '__main__':
    main()
