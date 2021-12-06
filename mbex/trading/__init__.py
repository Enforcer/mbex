import abc
import asyncio
import time
from collections import defaultdict, deque
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Protocol, Tuple, Type

from attr import define

from mbex import auth, wallets


class Side(Enum):
    ask = "ask"
    bid = "bid"


MARKETS = defaultdict(lambda: {Side.bid: [], Side.ask: []})


@define
class LimitOrder(abc.ABC):
    price: Decimal
    volume: Decimal
    timestamp: int
    user_id: auth.UserId
    order_id: str

    @abc.abstractmethod
    def matches(self, other: "LimitOrder") -> bool:
        raise NotImplementedError


class Ask(LimitOrder):
    def matches(self, other: "LimitOrder") -> bool:
        assert isinstance(other, Bid)
        return self.price <= other.price


class Bid(LimitOrder):
    def matches(self, other: "LimitOrder") -> bool:
        assert isinstance(other, Ask)
        return self.price >= other.price


@define(frozen=True)
class Trade:
    price: Decimal
    volume: Decimal
    bid_user_id: auth.UserId
    ask_user_id: auth.UserId
    bid_price: Decimal


@define(frozen=True)
class Market:
    base: wallets.CurrencyCode
    quote: wallets.CurrencyCode

    def __str__(self) -> str:
        return f"{self.base}-{self.quote}"


def clear() -> None:
    MARKETS.clear()
    restart_processes()


class TasksScheduler(Protocol):
    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        ...


from multiprocessing import Process, Queue


def market_main(in_q: Queue, out_q: Queue) -> None:
    book = {Side.bid: [], Side.ask: []}

    while True:
        action, *others = in_q.get()
        if action == "order_book":
            asks_volume_by_price = defaultdict(Decimal)
            for ask in book[Side.ask]:
                asks_volume_by_price[ask.price] += ask.volume

            bids_volume_by_price = defaultdict(Decimal)
            for bid in book[Side.bid]:
                bids_volume_by_price[bid.price] += bid.volume

            out_q.put((asks_volume_by_price, bids_volume_by_price))
        elif action == "cancel_order":
            order_id, user_id, market = others
            try:
                order = [
                    o
                    for o in book[Side.bid]
                    if (o.order_id, o.user_id) == (order_id, user_id)
                ].pop()
                side = Side.bid
                currency_to_credit = market.quote
                volume_to_credit = order.price * order.volume
            except IndexError:
                try:
                    order = [
                        o
                        for o in book[Side.ask]
                        if (o.order_id, o.user_id) == (order_id, user_id)
                    ].pop()
                except IndexError:
                    out_q.put(None)
                    continue

                side = Side.ask
                currency_to_credit = market.base
                volume_to_credit = order.volume

            book[side].remove(order)

            out_q.put((currency_to_credit, volume_to_credit))
        elif action == "place_order":
            new_order, side, other_side = others

            trades = deque([])
            other_side_orders = book[other_side]
            while (
                len(other_side_orders) > 0
                and new_order.matches(other_side_orders[0])
                and new_order.volume > 0
            ):
                time.sleep(0.001)  # simulate it's actually CPU heavy
                other_order: LimitOrder = other_side_orders[0]
                matched_vol = min(other_order.volume, new_order.volume)
                other_order.volume -= matched_vol
                new_order.volume -= matched_vol
                # remove order present in order book if it was filled completely
                if other_order.volume == 0:
                    other_side_orders.remove(other_order)

                if side == side.bid:
                    bid_price = new_order.price
                    bid_user_id = new_order.user_id
                    ask_user_id = other_order.user_id
                else:
                    bid_price = other_order.price
                    bid_user_id = other_order.user_id
                    ask_user_id = new_order.user_id

                trades.append(
                    Trade(
                        price=new_order.price,
                        volume=matched_vol,
                        bid_user_id=bid_user_id,
                        ask_user_id=ask_user_id,
                        bid_price=bid_price,
                    )
                )

            # add new order to the order book if hasn't been filled yet
            if new_order.volume > 0:
                book[side].append(new_order)
                multiplier = -1 if side == side.bid else 1
                book[side].sort(
                    key=lambda order: (order.price * multiplier, order.timestamp)
                )

            out_q.put(trades)


MARKET_PROCESS = {}
def restart_processes():
    if MARKET_PROCESS:
        for proc, _in, _out in MARKET_PROCESS.values():
            proc.kill()

    for market in ["001-002", "003-004", "005-006", "007-008", "009-010", "ETH-BTC"]:
        in_q = Queue()
        out_q = Queue()
        proc = Process(target=market_main, args=(in_q, out_q), daemon=True)
        MARKET_PROCESS[market] = proc, in_q, out_q
        proc.start()


async def place_order(
    market: Market,
    price: Decimal,
    volume: Decimal,
    side: Side,
    user_id: auth.UserId,
    order_id: str,
    tasks: TasksScheduler,
) -> None:
    if not MARKET_PROCESS:
        restart_processes()

    order_cls: Type[LimitOrder]
    if side == Side.bid:
        currency = market.quote
        value = price * volume
        other_side = Side.ask
        order_cls = Bid
    else:
        currency = market.base
        value = volume
        other_side = Side.bid
        order_cls = Ask

    await wallets.debit(user_id, currency, value)

    new_order = order_cls(
        price=price,
        timestamp=time.time(),
        volume=volume,
        user_id=user_id,
        order_id=order_id,
    )

    _proc, in_q, out_q = MARKET_PROCESS[str(market)]
    await asyncio.get_event_loop().run_in_executor(
        None,
        in_q.put,
        ("place_order", new_order, side, other_side),
    )
    trades = await asyncio.get_event_loop().run_in_executor(
        None,
        out_q.get
    )

    for trade in trades:
        await wallets.credit(
            user_id=trade.bid_user_id, currency_code=market.base, amount=trade.volume
        )
        await wallets.credit(
            user_id=trade.ask_user_id,
            currency_code=market.quote,
            amount=trade.volume * trade.price,
        )
        price_diff = trade.bid_price - trade.price
        if price_diff > 0:
            await wallets.credit(
                user_id=trade.bid_user_id,
                currency_code=market.quote,
                amount=trade.volume * price_diff,
            )


class NoSuchOrder(Exception):
    pass


async def cancel_order(
    market: Market, user_id: auth.UserId, order_id: str, tasks: TasksScheduler
) -> None:
    if not MARKET_PROCESS:
        restart_processes()

    _proc, in_q, out_q = MARKET_PROCESS[str(market)]
    in_q.put(("cancel_order", order_id, user_id, market))
    res = out_q.get()
    if res is None:
        raise NoSuchOrder
    else:
        currency_to_credit, volume_to_credit = res

    await wallets.credit(
        user_id=user_id, currency_code=currency_to_credit, amount=volume_to_credit
    )


def order_book(market: Market) -> Tuple[dict[Decimal, Decimal], dict[Decimal, Decimal]]:
    _proc, in_q, out_q = MARKET_PROCESS[str(market)]
    in_q.put(("order_book", ))
    asks_volume_by_price, bids_volume_by_price = out_q.get()

    return asks_volume_by_price, bids_volume_by_price
