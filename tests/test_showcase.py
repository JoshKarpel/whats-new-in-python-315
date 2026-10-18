"""The showcase's walk through the transitions: each picked in F6's order, a chapter each, the same every time."""

import asyncio
import json
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from counterweight.app import app
from counterweight.autopilot import AutopilotStep
from counterweight.controls import Marker
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.components.transitions import OFF
from whats_new.components.transitions import OFFERED
from whats_new.components.transitions import TRANSITIONS
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.showcase import START
from whats_new.showcase import record_showcase
from whats_new.showcase import showcased
from whats_new.size import PRESENTING

FIRST = tuple(TRANSITIONS.items())[:3]
"""A few transitions, F6's first, so a test records in a moment."""


def markers(path: Path) -> list[str]:
    return [data for _, code, data in (json.loads(line) for line in path.read_text().splitlines()[1:]) if code == "m"]


def test_the_transitions_follow_where_the_showcase_starts_in_the_order_f6_lists_them() -> None:
    """Moving one option down the picker picks the next transition only while F6 lists them in this order."""
    assert OFFERED[OFFERED.index(START.transition) :] == (START.transition, *TRANSITIONS)


async def test_each_transition_is_picked_in_turn(host: Host) -> None:
    checkpoints: list[Checkpoint] = []

    async def settle(frame: Frame) -> None:
        # The checkpoint is written from an effect, which runs once the autopilot yields to it,
        # so a pick the next pick follows straight away would never be checkpointed.
        await asyncio.sleep(0.05)

    picking = (
        (step, Screenshot(handler=settle)) if step == KeyPressed(key=Key.Enter) else (step,)
        for step in showcased(FIRST)
    )
    await app(
        root(SLIDES, host, START, checkpoints.append),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(step for steps in picking for step in steps),
        clock=EXPORT_CLOCK,
    )

    picked = [checkpoint.transition for checkpoint in checkpoints]
    assert list(dict.fromkeys(picked)) == [name for name, _ in FIRST]
    assert checkpoints[-1].slide == len(FIRST)


async def test_the_showcase_marks_a_chapter_per_transition_in_order(host: Host, tmp_path: Path) -> None:
    path = tmp_path / "transitions.cast"

    await record_showcase(SLIDES, host, FIRST, path)

    assert markers(path) == [f"{number}. {name}" for number, (name, _) in enumerate(FIRST, start=1)]


async def test_the_showcase_ends_with_the_deck_quitting(host: Host, tmp_path: Path) -> None:
    path = tmp_path / "transitions.cast"

    await record_showcase(SLIDES, host, FIRST[:1], path)

    assert json.loads(path.read_text().splitlines()[-1])[1:] == ["x", "0"]


async def test_the_showcase_records_the_same_every_time(host: Host, tmp_path: Path) -> None:
    first, second = tmp_path / "first.cast", tmp_path / "second.cast"

    await record_showcase(SLIDES, host, FIRST, first)
    await record_showcase(SLIDES, host, FIRST, second)

    assert first.read_text() == second.read_text()


async def test_the_showcase_needs_a_slide_more_than_there_are_transitions(host: Host, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="needs 4 slides"):
        await record_showcase(SLIDES[:3], host, FIRST, tmp_path / "transitions.cast")


async def test_every_transition_finishes_before_the_showcase_moves_on(host: Host) -> None:
    """Each hold has to outlast its transition at the showcase's speed, or the next pick cuts it off mid-play."""
    transitions = tuple(TRANSITIONS.items())
    landed: list[Frame] = []
    still: list[Frame] = []

    def watched(steps: Iterable[AutopilotStep]) -> Iterator[AutopilotStep]:
        """`steps`, with a screenshot of where each transition landed, taken as the showcase is about to move on."""
        for number, step in enumerate(steps):
            if number > 0 and isinstance(step, (Marker, Quit)):
                yield Screenshot(handler=landed.append)
            yield step

    await app(
        root(SLIDES, host, START, lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=watched(showcased(transitions)),
        clock=EXPORT_CLOCK,
    )
    await app(
        root(SLIDES, host, replace(START, transition=OFF), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            *(step for _ in transitions for step in (KeyPressed(key=Key.Right), Screenshot(handler=still.append))),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )

    cut_off = [
        name
        for (name, _), shown, expected in zip(transitions, landed, still, strict=True)
        if stage(shown) != stage(expected)
    ]
    assert cut_off == []


def stage(frame: Frame) -> list[str]:
    """What the stage shows, without the footer's rule and line."""
    return frame.text(ansi=False).splitlines()[:-2]
