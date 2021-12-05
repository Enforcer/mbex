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


class TasksScheduler(Protocol):
    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        ...


PROCESSES = {}


from concurrent.futures import ProcessPoolExecutor

pool = ProcessPoolExecutor()


def _place_order(new_order, side, other_side_orders, this_side_orders):
    trades = deque([])
    while (
        len(other_side_orders) > 0
        and new_order.matches(other_side_orders[0])
        and new_order.volume > 0
    ):
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
        this_side_orders.append(new_order)
        multiplier = -1 if side == side.bid else 1
        this_side_orders.sort(
            key=lambda order: (order.price * multiplier, order.timestamp)
        )

    return trades, this_side_orders, other_side_orders


async def place_order(
    market: Market,
    price: Decimal,
    volume: Decimal,
    side: Side,
    user_id: auth.UserId,
    order_id: str,
    tasks: TasksScheduler,
) -> None:
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

    other_side_orders = MARKETS[market][other_side]
    this_side_orders = MARKETS[market][side]
    (
        trades,
        this_side_orders,
        other_side_orders,
    ) = await asyncio.get_event_loop().run_in_executor(
        pool, _place_order, new_order, side, other_side_orders, this_side_orders
    )
    MARKETS[market][other_side] = other_side_orders
    MARKETS[market][side] = this_side_orders

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


def _cancel_order(all_orders, order_id, user_id, market):
    try:
        order = [
            o
            for o in all_orders[Side.bid]
            if (o.order_id, o.user_id) == (order_id, user_id)
        ].pop()
        side = Side.bid
        currency_to_credit = market.quote
        volume_to_credit = order.price * order.volume
    except IndexError:
        try:
            order = [
                o
                for o in all_orders[Side.ask]
                if (o.order_id, o.user_id) == (order_id, user_id)
            ].pop()
        except IndexError:
            raise NoSuchOrder

        side = Side.ask
        currency_to_credit = market.base
        volume_to_credit = order.volume

    all_orders[side].remove(order)

    return all_orders, currency_to_credit, volume_to_credit


async def cancel_order(
    market: Market, user_id: auth.UserId, order_id: str, tasks: TasksScheduler
) -> None:
    all_orders = MARKETS[market]

    (
        all_orders,
        currency_to_credit,
        volume_to_credit,
    ) = await asyncio.get_event_loop().run_in_executor(
        pool,
        _cancel_order,
        all_orders,
        order_id,
        user_id,
        market,
    )

    MARKETS[market] = all_orders

    await wallets.credit(
        user_id=user_id, currency_code=currency_to_credit, amount=volume_to_credit
    )


def order_book(market: Market) -> Tuple[dict[Decimal, Decimal], dict[Decimal, Decimal]]:
    asks_volume_by_price = defaultdict(Decimal)
    for ask in MARKETS[market][Side.ask]:
        asks_volume_by_price[ask.price] += ask.volume

    bids_volume_by_price = defaultdict(Decimal)
    for bid in MARKETS[market][Side.bid]:
        bids_volume_by_price[bid.price] += bid.volume

    return asks_volume_by_price, bids_volume_by_price
