"""
Expensive things the deck does to itself while Tachyon watches, each started by a key on the Tachyon stage.

Every workload ends on its own after a few seconds, so a key starts one and nothing has to stop it.
All but one run off the event loop, so the deck keeps drawing (while still sharing the GIL with it);
`EVENT_LOOP_CPU` runs on the loop on purpose, freezing the deck, so the profile can explain the freeze afterwards.
"""

import asyncio
import gc
import tempfile
import time
from collections.abc import Awaitable
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import assert_never

lazy import numpy

SECONDS = 6.0


def nbody_for(seconds: float) -> None:
    """Pure-Python floating point, the shape of the n-body benchmark, until `seconds` pass."""
    bodies = [[0.0, 0.0, 0.0, 0.01, 0.02, 0.0, 1.0], [1.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.001]]
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for _ in range(1000):
            bi, bj = bodies
            dx, dy, dz = bi[0] - bj[0], bi[1] - bj[1], bi[2] - bj[2]
            d2 = dx * dx + dy * dy + dz * dz + 0.01
            mag = 0.01 / (d2 * d2**0.5)
            bi[3] -= dx * bj[6] * mag
            bj[3] += dx * bi[6] * mag
            bi[0] += 0.01 * bi[3]
            bj[0] += 0.01 * bj[3]


def matmul_for(seconds: float) -> None:
    """Compiled code: numpy matrix products, which Tachyon shows as `<native>` frames."""
    rng = numpy.random.default_rng(315)
    a = rng.random((300, 300))
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        a = a @ a
        a /= numpy.abs(a).max()


def blocking_io_for(seconds: float) -> None:
    """Writing and reading a file, and sleeping: wall-clock time that isn't CPU time."""
    deadline = time.monotonic() + seconds
    with tempfile.TemporaryFile() as file:
        while time.monotonic() < deadline:
            file.write(b"x" * 65536)
            file.flush()
            file.seek(0)
            file.read()
            time.sleep(0.05)


def garbage_cycles_for(seconds: float) -> None:
    """Cyclic garbage, which only the cyclic collector frees: Tachyon shows its `<GC>` frames."""

    class Node:
        def __init__(self) -> None:
            self.other: Node | None = None

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for _ in range(10_000):
            a, b = Node(), Node()
            a.other, b.other = b, a
        gc.collect(0)


def exceptions_for(seconds: float) -> None:
    """Raising and catching in a loop, which exception mode samples while nothing else is."""
    empty: dict[str, int] = {}
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            empty["missing"]
        except KeyError:
            nbody_for(0.001)


async def task_fan(seconds: float) -> None:
    """A fan of asyncio tasks, some computing in slices and some waiting, for `--async-aware`."""

    async def crunch() -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            nbody_for(0.002)
            await asyncio.sleep(0)

    async def wait() -> None:
        await asyncio.sleep(seconds)

    async with asyncio.TaskGroup() as group:
        for _ in range(3):
            group.create_task(crunch())
        group.create_task(wait())


@dataclass(frozen=True, slots=True)
class OnThread:
    """Runs in a worker thread, so the deck keeps drawing, though it still shares the GIL with the render loop."""

    run: Callable[[float], None]


@dataclass(frozen=True, slots=True)
class OnLoop:
    """Runs on the event loop itself, which freezes the deck until it's done."""

    run: Callable[[float], None]


@dataclass(frozen=True, slots=True)
class AsTasks:
    """Runs as asyncio tasks on the event loop, taking turns with the deck."""

    run: Callable[[float], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Workload:
    key: str
    name: str
    how: OnThread | OnLoop | AsTasks
    seconds: float = SECONDS


WORKLOADS = (
    Workload("c", "pure-Python CPU, in a thread", OnThread(nbody_for)),
    Workload("C", "pure-Python CPU, on the event loop", OnLoop(nbody_for), seconds=2.0),
    Workload("n", "numpy matmul", OnThread(matmul_for)),
    Workload("i", "blocking I/O", OnThread(blocking_io_for)),
    Workload("a", "asyncio tasks", AsTasks(task_fan)),
    Workload("g", "garbage cycles", OnThread(garbage_cycles_for)),
    Workload("e", "raise and catch", OnThread(exceptions_for)),
)
WORKLOADS_BY_KEY = {workload.key: workload for workload in WORKLOADS}


async def perform(workload: Workload, executor: ThreadPoolExecutor) -> None:
    """Runs `workload` where it says it runs, returning when it's done."""
    match workload.how:
        case OnThread(run=run):
            await asyncio.get_running_loop().run_in_executor(executor, run, workload.seconds)
        case OnLoop(run=run):
            run(workload.seconds)
        case AsTasks(run=run_tasks):
            await run_tasks(workload.seconds)
        case _ as unreachable:
            assert_never(unreachable)
