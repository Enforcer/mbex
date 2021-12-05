from contextlib import asynccontextmanager
from typing import Iterator

import aioredis
from aioredis import Redis


@asynccontextmanager
async def conn() -> Iterator[Redis]:
    client = aioredis.from_url("redis://localhost")
    async with client.client() as connection:
        yield connection

    await client.close()
    await client.connection_pool.disconnect()
