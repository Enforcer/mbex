from fastapi import FastAPI

from mbex.api.auth import auth_router
from mbex.api.profiling import profiling_router
from mbex.api.trading import trading_router
from mbex.api.wallets import wallets_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    app.include_router(wallets_router, prefix="/wallets")
    app.include_router(trading_router, prefix="/trading")
    app.include_router(profiling_router, prefix="/profiling")
    return app
