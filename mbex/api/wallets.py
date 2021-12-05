from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mbex import auth, wallets
from mbex.api.auth import current_user_id

wallets_router = APIRouter()


@wallets_router.get("/balances/{currency}")
async def get_balance(
    currency: wallets.CurrencyCode, user_id: auth.UserId = Depends(current_user_id)
) -> JSONResponse:
    balance = await wallets.balance(user_id, currency)
    return JSONResponse({"balance": f"{balance:f}"})


class Deposit(BaseModel):
    amount: Decimal


@wallets_router.post("/balances/{currency}/deposit")
async def deposit(
    currency: wallets.CurrencyCode,
    payload: Deposit,
    user_id: auth.UserId = Depends(current_user_id),
) -> JSONResponse:
    await wallets.credit(user_id, currency, payload.amount)
    return JSONResponse(status_code=202)
