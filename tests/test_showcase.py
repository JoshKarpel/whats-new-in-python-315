"""
The showcases' walks through the transitions: each picked in its picker's order, a chapter each, the same every time,
F6's moving on from slide to slide, and F7's opening the grid and closing it onto the next slide.
"""

import asyncio
import itertools
import json
from collections.abc import Awaitable
from collections.abc import Callable
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
from whats_new.components.transitions import GRID_OFFERED
from whats_new.components.transitions import OFF
from whats_new.components.transitions import OFFERED
from whats_new.components.transitions import TRANSITIONS
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.showcase import GRID_EFFECTS
from whats_new.showcase import GRID_START
from whats_new.showcase import START
from whats_new.showcase import grid_showcased
from whats_new.showcase import record_grid_showcase
from whats_new.showcase import record_showcase
from whats_new.showcase import showcased
from whats_new.size import PRESENTING
from whats_new.slides import Slide

FIRST = tuple(TRANSITIONS.items())[:3]
"""A few transitions, F6's first, so a test records in a moment."""
GRID_FIRST = tuple(GRID_EFFECTS.transitions.items())[:3]
"""A few of the grid's transitions, the first F7 lists after `GRID_START`'s."""

type Record = Callable[[tuple[Slide, ...], Host, int, Path], Awaitable[None]]
"""Records a showcase of the first so many of its transitions on the slides to the path."""


def record_slides(slides: tuple[Slide, ...], host: Host, count: int, path: Path) -> Awaitable[None]:
    return record_showcase(slides, host, FIRST[:count], path)


def record_grid(slides: tuple[Slide, ...], host: Host, count: int, path: Path) -> Awaitable[None]:
    return record_grid_showcase(slides, host, GRID_FIRST[:count], path)


SHOWCASES = pytest.mark.parametrize(
    ("record", "names"),
    [
        pytest.param(record_slides, [name for name, _ in FIRST], id="slides"),
        pytest.param(record_grid, [name for name, _ in GRID_FIRST], id="grid"),
    ],
)


def markers(path: Path) -> list[str]:
    return [data for _, code, data in (json.loads(line) for line in path.read_text().splitlines()[1:]) if code == "m"]


def test_the_transitions_follow_where_the_showcase_starts_in_the_order_f6_lists_them() -> None:
    """Moving one option down the picker picks the next transition only while F6 lists them in this order."""
    assert OFFERED[OFFERED.index(START.transition) :] == (START.transition, *TRANSITIONS)


def test_the_grid_transitions_follow_where_the_grid_showcase_starts_in_the_order_f7_lists_them() -> None:
    """Moving one option down F7's picker picks the next of the grid's transitions only while it lists them so."""
    start = GRID_OFFERED.index(GRID_START.grid_transition)
    assert GRID_OFFERED[start : start + 1 + len(GRID_EFFECTS.transitions)] == (
        GRID_START.grid_transition,
        *GRID_EFFECTS.transitions,
    )


@pytest.mark.parametrize(
    ("start", "steps", "names"),
    [
        pytest.param(START, list(showcased(FIRST)), [name for name, _ in FIRST], id="slides"),
        pytest.param(GRID_START, list(grid_showcased(GRID_FIRST)), [name for name, _ in GRID_FIRST], id="grid"),
    ],
)
async def test_each_transition_is_picked_in_turn(
    host: Host, start: Checkpoint, steps: list[AutopilotStep], names: list[str]
) -> None:
    checkpoints: list[Checkpoint] = []

    async def settle(frame: Frame) -> None:
        # The checkpoint is written from an effect, which runs once the autopilot yields to it,
        # so a pick the next pick follows straight away would never be checkpointed.
        await asyncio.sleep(0.05)

    picking = ((step, Screenshot(handler=settle)) if step == KeyPressed(key=Key.Enter) else (step,) for step in steps)
    await app(
        root(SLIDES, host, start, checkpoints.append),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(step for steps in picking for step in steps),
        clock=EXPORT_CLOCK,
    )

    picked = [checkpoint.transition if start is START else checkpoint.grid_transition for checkpoint in checkpoints]
    assert list(dict.fromkeys(picked)) == names
    assert checkpoints[-1].slide == len(names)


@SHOWCASES
async def test_the_showcase_marks_a_chapter_per_transition_in_order(
    host: Host, tmp_path: Path, record: Record, names: list[str]
) -> None:
    path = tmp_path / "showcase.cast"

    await record(SLIDES, host, len(names), path)

    assert markers(path) == [f"{number}. {name}" for number, name in enumerate(names, start=1)]


@SHOWCASES
async def test_the_showcase_ends_with_the_deck_quitting(
    host: Host, tmp_path: Path, record: Record, names: list[str]
) -> None:
    path = tmp_path / "showcase.cast"

    await record(SLIDES, host, 1, path)

    assert json.loads(path.read_text().splitlines()[-1])[1:] == ["x", "0"]


@SHOWCASES
async def test_the_showcase_records_the_same_every_time(
    host: Host, tmp_path: Path, record: Record, names: list[str]
) -> None:
    first, second = tmp_path / "first.cast", tmp_path / "second.cast"

    await record(SLIDES, host, len(names), first)
    await record(SLIDES, host, len(names), second)

    assert first.read_text() == second.read_text()


@SHOWCASES
async def test_the_showcase_needs_a_slide_more_than_there_are_transitions(
    host: Host, tmp_path: Path, record: Record, names: list[str]
) -> None:
    with pytest.raises(ValueError, match="needs 4 slides"):
        await record(SLIDES[:3], host, 3, tmp_path / "showcase.cast")


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


async def test_every_grid_transition_finishes_before_the_grid_showcase_moves_on(host: Host) -> None:
    """
    Each hold has to outlast its transition opening the grid, or the selection moves mid-play,
    and closing it, or the next pick cuts it off.
    """
    transitions = tuple(GRID_EFFECTS.transitions.items())
    landed: list[Frame] = []
    still: list[Frame] = []

    def watched(steps: Iterable[AutopilotStep]) -> Iterator[AutopilotStep]:
        """`steps`, with a screenshot as the grid has opened and as the slide it closed onto is about to move on."""
        for number, step in enumerate(steps):
            if step == KeyPressed(key=Key.Right) or (number > 0 and isinstance(step, (Marker, Quit))):
                yield Screenshot(handler=landed.append)
            yield step

    await app(
        root(SLIDES, host, GRID_START, lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=watched(grid_showcased(transitions)),
        clock=EXPORT_CLOCK,
    )
    await app(
        root(SLIDES, host, replace(GRID_START, grid_transition=OFF), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            *(
                step
                for _ in transitions
                for step in (
                    KeyPressed(key="d"),
                    Screenshot(handler=still.append),
                    KeyPressed(key=Key.Right),
                    KeyPressed(key=Key.Enter),
                    Screenshot(handler=still.append),
                )
            ),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )

    cut_off = [
        f"{name} {way}"
        for (name, _), (opened, closed), (grid, slide) in zip(
            transitions,
            itertools.batched(landed, 2, strict=True),
            itertools.batched(still, 2, strict=True),
            strict=True,
        )
        for way, shown, expected in (("opening", opened, grid), ("closing", closed, slide))
        if stage(shown) != stage(expected)
    ]
    assert cut_off == []


def stage(frame: Frame) -> list[str]:
    """What the stage shows, without the footer's rule and line."""
    return frame.text(ansi=False).splitlines()[:-2]
