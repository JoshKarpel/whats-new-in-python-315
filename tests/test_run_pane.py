"""
The run pane's keys beyond running: Up and Down scroll its output,
and a light goes around its border while a run is in progress.
"""

import asyncio

from counterweight import app
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.geometry import Position
from counterweight.keys import Key
from counterweight.paint import Frame
from counterweight.styles import AnyColor

from whats_new.checkpoint import Checkpoint
from whats_new.components.run_pane import ORBIT
from whats_new.components.run_pane import RESTING
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING


def index_of(title: str) -> int:
    return next(index for index, slide in enumerate(SLIDES) if slide.title == title)


async def settle(frame: Frame) -> None:
    await asyncio.sleep(0.25)


async def drive(host: Host, title: str, autopilot: tuple[AnyEvent | AnyControl, ...]) -> None:
    await app(
        root(SLIDES, host, Checkpoint(slide=index_of(title)), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(*autopilot, Quit()),
        clock=EXPORT_CLOCK,
    )


def box_lines(frame: Frame) -> list[str]:
    """The lines inside the run box, which is the last rounded box on the slide."""
    lines = frame.text(ansi=False).split("\n")
    top = max(index for index, line in enumerate(lines) if "╭" in line)
    bottom = max(index for index, line in enumerate(lines) if "╰" in line)
    return lines[top + 1 : bottom]


async def test_up_scrolls_the_output_back_a_line(host: Host) -> None:
    # Its traceback is longer than its short box, which sticks to the end of it.
    frames: list[Frame] = []
    await drive(
        host,
        "Unpacking async sources: not like that",
        (
            KeyPressed(key="1"),
            *(Screenshot(handler=settle) for _ in range(20)),
            Screenshot(handler=frames.append),
            KeyPressed(key=Key.Up),
            Screenshot(handler=frames.append),
            KeyPressed(key=Key.Down),
            Screenshot(handler=frames.append),
        ),
    )

    at_end, scrolled_up, back = (box_lines(frame) for frame in frames)
    assert scrolled_up[1:] == at_end[:-1]
    assert back == at_end


ROUNDED = frozenset("╭╮╰╯─│")


def box_border(frame: Frame) -> list[AnyColor]:
    """The colors of the run box's border cells, in reading order. The run box is the last rounded box on the slide."""
    lines = frame.text(ansi=False).split("\n")
    top = max(index for index, line in enumerate(lines) if "╭" in line)
    bottom = max(index for index, line in enumerate(lines) if "╰" in line)
    columns, _ = PRESENTING.dimensions
    return [
        cell.style.foreground
        for y in range(top, bottom + 1)
        for x in range(columns)
        if (cell := frame.paint.get(Position(x, y))) is not None and cell.grapheme in ROUNDED
    ]


async def test_a_light_goes_around_the_border_while_a_run_is_in_progress(host: Host) -> None:
    # The overhead harness runs the example nine times, which takes seconds.
    frames: list[Frame] = []
    await drive(
        host,
        "Tracing vs sampling: the overhead",
        (
            Screenshot(handler=frames.append),
            KeyPressed(key="1"),
            *(Screenshot(handler=settle) for _ in range(2)),
            AdvanceClock(by=ORBIT / 4),
            Screenshot(handler=frames.append),
            AdvanceClock(by=ORBIT / 4),
            Screenshot(handler=frames.append),
        ),
    )

    before, quarter, half = (box_border(frame) for frame in frames)
    assert set(before) == {RESTING}
    assert set(quarter) != {RESTING}
    assert quarter != half
