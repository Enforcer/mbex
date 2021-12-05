import asyncio
import time


async def coro_function() -> None:
    """Basic coroutine function."""
    pass

asyncio.run(coro_function())


# def non_coro_function():
#     """Can't use await inside non-coro function!"""
#     await coro_function()

async def another_coro_function() -> None:
    """Can use 'normal' functions inside coroutines.

    But should you...?
    """
    time.sleep(5)


async def sleeper() -> None:
    """Explicit wait and yield."""
    await asyncio.sleep(5)


async def no_wait() -> None:
    """Scheduling coroutine to run concurrently in 'background'."""
    asyncio.create_task(asyncio.sleep(5))
