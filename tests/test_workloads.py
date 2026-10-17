"""
The Tachyon stage's workloads: each runs until cancelled, and cancelling one stops it,
even pure-Python CPU on the event loop, which freezes it, between its freezes.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta

import pytest

from whats_new.workloads import WORKLOADS
from whats_new.workloads import OnLoop
from whats_new.workloads import OnThread
from whats_new.workloads import Workload
from whats_new.workloads import perform

STOPS_WITHIN = 5.0
"""Seconds a stopped workload gets to finish its current slice: far more than any slice takes."""


@pytest.mark.parametrize(
    "workload",
    [workload for workload in WORKLOADS if not isinstance(workload.how, OnLoop)],
    ids=lambda workload: workload.name,
)
async def test_cancelling_a_workload_stops_it(workload: Workload) -> None:
    executor = ThreadPoolExecutor(max_workers=1)
    task = asyncio.create_task(perform(workload, executor))
    # Lets the workload start: a thread's is submitted, and tasks are created.
    await asyncio.sleep(0)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # A thread that never stops would keep shutdown waiting past the timeout.
    await asyncio.wait_for(asyncio.to_thread(executor.shutdown, wait=True), timeout=STOPS_WITHIN)


async def test_a_workload_runs_until_cancelled() -> None:
    workload = next(workload for workload in WORKLOADS if isinstance(workload.how, OnThread))
    executor = ThreadPoolExecutor(max_workers=1)
    task = asyncio.create_task(perform(workload, executor))

    done, _ = await asyncio.wait({task}, timeout=0.5)

    assert not done
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    executor.shutdown(wait=True)


async def test_the_event_loop_workload_gives_the_loop_back_between_freezes_and_stops_there() -> None:
    workload = next(workload for workload in WORKLOADS if isinstance(workload.how, OnLoop))
    assert isinstance(workload.how, OnLoop)
    quick = replace(workload, how=replace(workload.how, freeze=timedelta(seconds=0.05), breather=timedelta(seconds=1)))
    task = asyncio.create_task(perform(quick, ThreadPoolExecutor(max_workers=1)))

    # Runs the task's first freeze, which ends in the breather, where this coroutine gets the loop back.
    await asyncio.sleep(0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
