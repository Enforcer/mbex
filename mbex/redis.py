from contextlib import asynccontextmanager
from typing import Iterator

import aioredis


@asynccontextmanager
async def conn() -> Iterator[aioredis.Redis]:
    client = aioredis.from_url("redis://localhost")
    async with client.client() as connection:
        yield connection

    await client.close()
    await client.connection_pool.disconnect()
