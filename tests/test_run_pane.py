"""The run pane's keys beyond running: Up and Down scroll its output, and its border pulses while a run is in progress."""

import asyncio

from counterweight.app import app
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.components.run_pane import LIT
from whats_new.components.run_pane import PULSE
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING

LIT_ANSI = f"38;2;{LIT.red};{LIT.green};{LIT.blue}m"


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
        "Disjoint bases",
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


async def test_the_border_pulses_while_a_run_is_in_progress(host: Host) -> None:
    # The overhead harness runs the example nine times, which takes seconds.
    frames: list[Frame] = []
    await drive(
        host,
        "Tracing vs sampling: the overhead",
        (
            Screenshot(handler=frames.append),
            KeyPressed(key="1"),
            *(Screenshot(handler=settle) for _ in range(2)),
            AdvanceClock(by=PULSE / 2),
            Screenshot(handler=frames.append),
        ),
    )

    before, running = (frame.text(ansi=True) for frame in frames)
    assert LIT_ANSI not in before
    assert LIT_ANSI in running


async def test_the_border_rests_between_breaths(host: Host) -> None:
    frames: list[Frame] = []
    await drive(
        host,
        "Tracing vs sampling: the overhead",
        (
            KeyPressed(key="1"),
            *(Screenshot(handler=settle) for _ in range(2)),
            AdvanceClock(by=PULSE),
            Screenshot(handler=frames.append),
        ),
    )

    assert LIT_ANSI not in frames[0].text(ansi=True)
