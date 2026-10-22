"""
Walks the whole deck headless at the presenting size: every reveal step of every slide, then the grid through
every row, catching slides that crash, and checking that showing them started nothing.
"""

import asyncio
import re
from collections.abc import Callable
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

from counterweight import app
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.paint import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.components.grid import COLUMNS
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING
from whats_new.slides import sections

PEP_MENTION = re.compile(r"PEP (\d+)")
SETTLE_CYCLES = 4
SETTLE_PAUSE = timedelta(milliseconds=20)


def child_pids() -> set[int]:
    return {int(pid) for task in Path("/proc/self/task").iterdir() for pid in (task / "children").read_text().split()}


def recorder(frames: list[tuple[int, Frame]], index: int) -> Callable[[Frame], None]:
    """
    A screenshot handler that appends its frame to `frames`, tagged with `index`.
    A closure rather than a `functools.partial`: the app logs each handler's repr, and a partial's includes `frames`,
    every frame so far, which makes each record bigger than the last.
    """

    def record(frame: Frame) -> None:
        frames.append((index, frame))

    return record


async def sample_children(spawned: set[int]) -> None:
    """
    Records the deck's children after yielding the loop a moment:
    the autopilot never suspends between cycles on its own, so without this, effects would never get to run.
    """
    await asyncio.sleep(SETTLE_PAUSE.total_seconds())
    spawned.update(child_pids())


def walk(frames: list[tuple[int, Frame]], spawned: set[int] | None = None) -> Iterator[AnyEvent | AnyControl]:
    """
    Every step of every slide, then the grid through every row.
    With `spawned`, each slide's last step stays up for a few more render cycles, sampling the deck's children in each:
    the app hangs every child up as it quits, so only a sample taken while a slide shows can see one it started,
    and a run waits a couple of cycles for its box to be laid out before it starts.
    """
    for index, slide in enumerate(SLIDES):
        for step in range(slide.steps):
            yield Screenshot(handler=recorder(frames, index))
            if step < slide.steps - 1:
                yield KeyPressed(key=Key.Space)
        if spawned is not None:
            for _ in range(SETTLE_CYCLES):
                yield Screenshot(handler=lambda frame: sample_children(spawned))
        yield KeyPressed(key=Key.Right)
    # The grid opens on the last slide; walk the selection back up through every row of every section.
    yield KeyPressed(key="d")
    for _ in range(sum(-(-len(section) // COLUMNS) for section in sections(SLIDES))):
        yield Screenshot(handler=recorder(frames, -1))
        yield KeyPressed(key=Key.Up)
    yield KeyPressed(key=Key.Escape)
    yield Quit()


async def test_every_slide_renders_and_starts_nothing(host: Host) -> None:
    before = child_pids()
    frames: list[tuple[int, Frame]] = []
    spawned: set[int] = set()

    await app(
        root(SLIDES, host, Checkpoint(slide=0), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=walk(frames, spawned),
        clock=EXPORT_CLOCK,
    )

    assert sum(1 for index, _ in frames if index >= 0) == sum(slide.steps for slide in SLIDES)
    assert spawned <= before


async def test_every_cited_pep_is_linked(host: Host) -> None:
    frames: list[tuple[int, Frame]] = []

    await app(
        root(SLIDES, host, Checkpoint(slide=0), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=walk(frames),
        clock=EXPORT_CLOCK,
    )

    unlinked = {
        (SLIDES[index].title, int(number))
        for index, frame in frames
        if index >= 0
        for number in PEP_MENTION.findall(frame.text(ansi=False))
        if int(number) not in SLIDES[index].peps
    }
    assert not unlinked


async def test_no_box_is_cut_off(host: Host) -> None:
    """
    A box that overflows the bottom of the screen loses its bottom edge: code blocks and nodes (heavy borders) and
    run panes (rounded ones) must close every top corner they open.
    """
    frames: list[tuple[int, Frame]] = []

    await app(
        root(SLIDES, host, Checkpoint(slide=0), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=walk(frames),
        clock=EXPORT_CLOCK,
    )

    cut_off = sorted(
        {
            SLIDES[index].title
            for index, frame in frames
            if index >= 0
            for text in (frame.text(ansi=False),)
            if text.count("┏") != text.count("┗") or text.count("╭") != text.count("╰")
        }
    )
    assert not cut_off
