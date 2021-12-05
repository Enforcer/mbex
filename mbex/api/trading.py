import os
import time
from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mbex import auth, trading
from mbex.api.auth import current_user_id

trading_router = APIRouter()


class Order(BaseModel):
    volume: Decimal
    price: Decimal
    side: trading.Side


@trading_router.delete("/{market}/orders/{order_id}")
async def cancel_order(
    market: str,
    order_id: str,
    user_id: auth.UserId = Depends(current_user_id),
) -> Response:
    market = _market_from_str(market)
    tasks = BackgroundTasks()
    try:
        await trading.cancel_order(
            market=market,
            user_id=user_id,
            order_id=order_id,
            tasks=tasks,
        )
    except trading.NoSuchOrder:
        return Response(status_code=404)

    return Response(status_code=202, background=tasks)


@trading_router.post("/{market}/orders")
async def place_order(
    order: Order,
    market: str,
    user_id: auth.UserId = Depends(current_user_id),
) -> Response:
    market = _market_from_str(market)
    order_id = f"{user_id}-{time.time()}-{os.getpid()}"
    tasks = BackgroundTasks()
    await trading.place_order(
        market=market,
        price=order.price,
        volume=order.volume,
        side=order.side,
        user_id=user_id,
        order_id=order_id,
        tasks=tasks,
    )

    return JSONResponse({"order_id": order_id}, status_code=202, background=tasks)


@trading_router.get("/{market}/order_book")
async def order_book(market: str) -> JSONResponse:
    asks_volume_by_price, bids_volume_by_price = trading.order_book(
        _market_from_str(market)
    )

    return JSONResponse(
        {
            "asks": [
                {"price": str(price), "volume": str(volume)}
                for price, volume in asks_volume_by_price.items()
            ],
            "bids": [
                {"price": str(price), "volume": str(volume)}
                for price, volume in bids_volume_by_price.items()
            ],
        }
    )


def _market_from_str(market_str) -> trading.Market:
    return trading.Market(*market_str.split("-"))
