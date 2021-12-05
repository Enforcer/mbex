from decimal import Decimal
from typing import Literal

from mbex.auth import UserId
from mbex import redis

CurrencyCode = Literal["ETH", "BTC"]
REDIS_KEY_TPL = "balance_{user_id}_{currency_code}"


async def clear() -> None:
    async with redis.conn() as conn:
        keys = await conn.keys("balance_*")
        if keys:
            await conn.delete(*keys)


async def balance(user_id: UserId, currency_code: CurrencyCode) -> Decimal:
    key = REDIS_KEY_TPL.format(user_id=user_id, currency_code=currency_code)
    async with redis.conn() as conn:
        raw = await conn.get(key)

    if raw:
        return Decimal(raw.decode())
    else:
        return Decimal("0")


async def credit(user_id: UserId, currency_code: CurrencyCode, amount: Decimal) -> None:
    key = REDIS_KEY_TPL.format(user_id=user_id, currency_code=currency_code)
    async with redis.conn() as conn:
        raw = await conn.get(key)

        if raw:
            balance = Decimal(raw.decode())
        else:
            balance = Decimal("0")

        new_balance = balance + amount
        await conn.set(key, str(new_balance))


class NotEnough(Exception):
    pass


async def debit(user_id: UserId, currency_code: CurrencyCode, amount: Decimal) -> None:
    key = REDIS_KEY_TPL.format(user_id=user_id, currency_code=currency_code)
    async with redis.conn() as conn:
        raw = await conn.get(key)

        if raw:
            balance = Decimal(raw.decode())
        else:
            balance = Decimal("0")

        if amount > balance:
            raise NotEnough
        else:
            new_balance = balance - amount
            await conn.set(key, str(new_balance))
