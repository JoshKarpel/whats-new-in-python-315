"""
Expensive things the deck does to itself while Tachyon watches, one at a time, chosen on the Tachyon stage.

A workload runs until the stage picks another one, or none. Each is a loop that asks `is_stopped`
between slices of work, so stopping one takes effect within a slice.
All but one run off the event loop, so the deck keeps drawing (while still sharing the GIL with it);
pure-Python CPU on the event loop runs there on purpose, freezing the deck, so the profile can explain the freeze.
It freezes a few seconds at a time and gives the loop back between freezes, since a deck that never
gets its loop back can't hear the key that would stop it.
"""

import asyncio
import gc
import os
import tempfile
import threading
import time
from collections.abc import Awaitable
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from typing import assert_never

# OpenBLAS's fork handler joins its worker threads, and it deadlocked the deck forking a new profiler mid-matmul:
# the join waited on a worker that never woke, with the GIL held. With one thread there are no workers to join.
# It must be set before numpy first loads OpenBLAS, which the lazy import below defers to the first matmul.
os.environ["OPENBLAS_NUM_THREADS"] = "1"

lazy import numpy

type IsStopped = Callable[[], bool]
type Bodies = list[list[float]]


def new_bodies() -> Bodies:
    """Two bodies' position, velocity and mass, for `nbody_steps` to move."""
    return [[0.0, 0.0, 0.0, 0.01, 0.02, 0.0, 1.0], [1.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.001]]


def nbody_steps(bodies: Bodies, steps: int) -> None:
    """Pure-Python floating point, the shape of the n-body benchmark: `steps` steps of two bodies' motion."""
    for _ in range(steps):
        bi, bj = bodies
        dx, dy, dz = bi[0] - bj[0], bi[1] - bj[1], bi[2] - bj[2]
        d2 = dx * dx + dy * dy + dz * dz + 0.01
        mag = 0.01 / (d2 * d2**0.5)
        bi[3] -= dx * bj[6] * mag
        bj[3] += dx * bi[6] * mag
        bi[0] += 0.01 * bi[3]
        bj[0] += 0.01 * bj[3]


def handle_key_error(total: float, steps: int) -> float:
    """
    Arithmetic done while a `KeyError` is being handled, under a name of its own,
    so a profile tells the exception workload's samples from `nbody_steps`'s.
    """
    for step in range(steps):
        total = (total + step) * 0.5
    return total


def has_passed(deadline: float) -> bool:
    """Whether `time.monotonic()` has reached `deadline`: an `IsStopped` for a freeze that ends on its own."""
    return time.monotonic() >= deadline


def nbody(is_stopped: IsStopped) -> None:
    """n-body steps, a thousand at a time, until stopped."""
    bodies = new_bodies()
    while not is_stopped():
        nbody_steps(bodies, 1000)


def matmul(is_stopped: IsStopped) -> None:
    """Compiled code: numpy matrix products, which Tachyon shows as `<native>` frames."""
    rng = numpy.random.default_rng(315)
    a = rng.random((300, 300))
    while not is_stopped():
        a = a @ a
        a /= numpy.abs(a).max()


def blocking_io(is_stopped: IsStopped) -> None:
    """Writing and reading a file, and sleeping: wall-clock time that isn't CPU time."""
    with tempfile.TemporaryFile() as file:
        while not is_stopped():
            file.write(b"x" * 65536)
            file.flush()
            file.seek(0)
            file.read()
            time.sleep(0.05)


def garbage_cycles(is_stopped: IsStopped) -> None:
    """Cyclic garbage, which only the cyclic collector frees: Tachyon shows its `<GC>` frames."""

    class Node:
        def __init__(self) -> None:
            self.other: Node | None = None

    while not is_stopped():
        for _ in range(10_000):
            a, b = Node(), Node()
            a.other, b.other = b, a
        gc.collect(0)


def exceptions(is_stopped: IsStopped) -> None:
    """Raising and catching in a loop, which exception mode samples while nothing else is."""
    empty: dict[str, int] = {}
    total = 0.0
    while not is_stopped():
        try:
            empty["missing"]
        except KeyError:
            total = handle_key_error(total, 5000)


async def task_fan() -> None:
    """A fan of asyncio tasks, some computing in slices and some waiting, until cancelled, for `--async-aware`."""

    async def crunch() -> None:
        bodies = new_bodies()
        while True:
            nbody_steps(bodies, 2000)
            await asyncio.sleep(0)

    async def wait() -> None:
        await asyncio.Event().wait()

    async with asyncio.TaskGroup() as group:
        for _ in range(3):
            group.create_task(crunch())
        group.create_task(wait())


@dataclass(frozen=True, slots=True)
class OnThread:
    """
    Runs in a worker thread until stopped, so the deck keeps drawing,
    though it still shares the GIL with the render loop.
    """

    run: Callable[[IsStopped], None]


@dataclass(frozen=True, slots=True)
class OnLoop:
    """
    Runs on the event loop itself, which freezes the deck, for `freeze` at a time, then gives the loop back for
    `breather`, long enough to draw a frame and read the keys pressed during the freeze, one of which may stop it.
    """

    run: Callable[[IsStopped], None]
    freeze: timedelta
    breather: timedelta


@dataclass(frozen=True, slots=True)
class AsTasks:
    """Runs as asyncio tasks on the event loop, taking turns with the deck, until cancelled."""

    run: Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Workload:
    name: str
    description: str
    """What it does and what to look for, as the workload picker shows it under the name."""
    how: OnThread | OnLoop | AsTasks


WORKLOADS = (
    Workload("pure-Python CPU, in a thread", "n-body floating point: the hot function and lines", OnThread(nbody)),
    Workload(
        "pure-Python CPU, on the event loop",
        "the same, on the loop: freezes the deck, pausing every 5 seconds",
        OnLoop(nbody, freeze=timedelta(seconds=5), breather=timedelta(seconds=0.25)),
    ),
    Workload("numpy matmul", "compiled matrix products: <native> frames", OnThread(matmul)),
    Workload("blocking I/O", "file writes and sleeps: wall time that isn't CPU", OnThread(blocking_io)),
    Workload("asyncio tasks", "tasks computing and waiting: try async-aware mode", AsTasks(task_fan)),
    Workload("garbage cycles", "garbage only the cyclic collector frees: <GC> frames", OnThread(garbage_cycles)),
    Workload("raise and catch", "a KeyError in a loop: try exception mode", OnThread(exceptions)),
)
WORKLOADS_BY_NAME = {workload.name: workload for workload in WORKLOADS}


async def perform(workload: Workload, executor: ThreadPoolExecutor) -> None:
    """
    Runs `workload` where it says it runs until cancelled. Cancelling stops a thread's workload too,
    though the thread finishes its current slice after this returns; it lands on a loop workload between freezes.
    """
    match workload.how:
        case OnThread(run=run):
            stop = threading.Event()
            try:
                await asyncio.get_running_loop().run_in_executor(executor, run, stop.is_set)
            finally:
                stop.set()
        case OnLoop(run=run, freeze=freeze, breather=breather):
            while True:
                run(partial(has_passed, time.monotonic() + freeze.total_seconds()))
                await asyncio.sleep(breather.total_seconds())
        case AsTasks(run=run_tasks):
            await run_tasks()
        case _ as unreachable:
            assert_never(unreachable)
