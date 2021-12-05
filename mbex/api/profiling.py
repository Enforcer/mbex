import yappi
from fastapi import APIRouter

profiling_router = APIRouter()


@profiling_router.post("/enable")
def enable():
    yappi.set_clock_type("WALL")
    yappi.start()


@profiling_router.post("/disable")
def disable():
    yappi.stop()
    yappi.get_func_stats().print_all(
        columns={
            0: ("name", 180),
            1: ("ncall", 5),
            2: ("tsub", 8),
            3: ("ttot", 8),
            4: ("tavg", 8),
        }
    )
