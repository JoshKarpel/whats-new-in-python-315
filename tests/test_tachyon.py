"""
The Tachyon stage's profiler modes, each handed to Tachyon itself, since some of its options refuse each other
and on stage the refusal only shows as a pane that exits as soon as `m` reaches that mode.
"""

import subprocess
import sys
from collections.abc import Iterator

import pytest

from whats_new.tachyon import MODES
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


@pytest.mark.parametrize("mode", range(len(MODES)), ids=[name for name, _ in MODES])
def test_tachyon_accepts_every_mode(sleeper: int, mode: int) -> None:
    # The live TUI needs a terminal, so sample for a moment instead: the options are checked either way.
    argv = tuple(arg for arg in profiler_argv(sleeper, mode) if arg != "--live")
    result = subprocess.run((*argv[:-1], "-d", "1", argv[-1]), capture_output=True, text=True, timeout=30)

    assert result.returncode == 0, result.stderr
