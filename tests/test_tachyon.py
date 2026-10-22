"""
The Tachyon stage's profiler modes, each handed to Tachyon itself, since some of its options refuse each other
and on stage the refusal only shows as a pane that exits as soon as `m`'s picker chooses that mode;
the medals its live view draws, which the stage's profiler environment swaps for ranks;
and Tab, which moves the keyboard between the stage and the profiler.
"""

import asyncio
import os
import subprocess
import sys
from collections.abc import Iterator
from collections.abc import Mapping
from dataclasses import replace

import pytest
from counterweight import app
from counterweight.autopilot import AutopilotStep
from counterweight.autopilot import showing
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.paint import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING
from whats_new.tachyon import MODES
from whats_new.tachyon import PROFILER_ENV
from whats_new.tachyon import Mode
from whats_new.tachyon import profiler_argv


@pytest.fixture
def sleeper() -> Iterator[int]:
    """A process for Tachyon to attach to: an event loop, waiting."""
    process = subprocess.Popen((sys.executable, "-c", "import asyncio; asyncio.run(asyncio.sleep(60))"))
    try:
        yield process.pid
    finally:
        process.kill()
        process.wait()


@pytest.mark.parametrize("mode", MODES, ids=[mode.name for mode in MODES])
def test_tachyon_accepts_every_mode(sleeper: int, mode: Mode) -> None:
    # The live TUI needs a terminal, so sample for a moment instead: the options are checked either way.
    argv = tuple(arg for arg in profiler_argv(sleeper, mode) if arg != "--live")
    result = subprocess.run((*argv[:-1], "-d", "1", argv[-1]), capture_output=True, text=True, timeout=30)

    assert result.returncode == 0, result.stderr


TOP_FUNCTIONS = """
from profiling.sampling.live_collector.widgets import HeaderWidget

class Display:
    def add_str(self, line, col, text, attr=0):
        print(text)

stats = [{"func": ("f.py", 1, f"f{n}"), "direct_calls": 10 - n, "sample_pct": 10.0 - n} for n in range(3)]
HeaderWidget(Display(), {"red": 1, "yellow": 2, "green": 3}, None).draw_top_functions(0, 100, stats)
"""


def drawn_top_functions(env: Mapping[str, str]) -> str:
    """What Tachyon's live view draws on its top-functions row, in a fresh interpreter with `env` added."""
    result = subprocess.run(
        (sys.executable, "-c", TOP_FUNCTIONS), env={**os.environ, **env}, capture_output=True, text=True, check=True
    )
    return result.stdout


def test_the_profiler_draws_ranks_instead_of_medals() -> None:
    drawn = drawn_top_functions(PROFILER_ENV)

    assert "#1" in drawn
    assert not any(medal in drawn for medal in "🥇🥈🥉")


def test_tachyon_draws_medals_without_the_profiler_s_environment() -> None:
    # The control: the medals are there to replace, so the test above reaches the row that draws them.
    assert "🥇" in drawn_top_functions({})


PROFILING = (KeyPressed(key="p"), showing("Tachyon Profiler"))
"""Starts the profiler and waits for it to draw, since the pane only takes keys while its program runs."""
TAB = KeyPressed(key=Key.Tab)


@pytest.mark.parametrize(
    ("steps", "running"),
    [
        ((), "idle"),
        ((*PROFILING, TAB), "blocking I/O"),
        ((*PROFILING, TAB, TAB), "idle"),
        ((TAB,), "idle"),
    ],
    ids=[
        "the stage has the keyboard",
        "Tab hands it to the profiler",
        "Tab takes it back",
        "no profiler to hand it to",
    ],
)
async def test_tab_moves_the_keyboard_in_and_out_of_the_profiler(
    host: Host, steps: tuple[AutopilotStep, ...], running: str
) -> None:
    # `c` stops the workload only if it reaches the stage rather than the profiler.
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "Tachyon, live")
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.05)

    autopilot: tuple[AutopilotStep, ...] = (
        KeyPressed(key="w"),
        *(KeyPressed(key=character) for character in "blo"),
        KeyPressed(key=Key.Enter),
        showing("running: blocking I/O"),
        *steps,
        KeyPressed(key="c"),
        Screenshot(handler=settle),
        Screenshot(handler=frames.append),
        Quit(),
    )
    await app(
        # The test process itself, since the profiler needs a real process to attach to.
        root(SLIDES, replace(host, pid=os.getpid()), Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert f"running: {running}" in frames[0].text(ansi=False)
