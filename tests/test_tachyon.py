"""
The Tachyon stage's profiler modes, each handed to Tachyon itself, since some of its options refuse each other
and on stage the refusal only shows as a pane that exits as soon as `m`'s picker chooses that mode;
and the medals its live view draws, which the stage's profiler environment swaps for ranks.
"""

import os
import subprocess
import sys
from collections.abc import Iterator
from collections.abc import Mapping

import pytest

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
