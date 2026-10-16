"""
The HTML export: the deck driven headless at the presenting size, one SVG screenshot per reveal step, in one page.

It must be deterministic, or the pre-commit hook that regenerates it would rewrite the file on every commit:
the clock is frozen and hidden, and moved on by a fixed amount after each reveal step to finish the step's
animation, and nothing runs, since mounting starts nothing.
"""

import subprocess
from collections.abc import Callable
from collections.abc import Iterator
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from html import escape
from pathlib import Path

from counterweight.app import app
from counterweight.clock import FrozenClock
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING
from whats_new.slides import Slide

EXPORT_CLOCK = FrozenClock(datetime(2026, 10, 1, 12, 0, tzinfo=UTC))
SETTLE = timedelta(minutes=1)
"""
How far the export moves the clock on after each reveal step, which finishes any animation the step started,
so each screenshot shows where the step ends up rather than its first frame.
"""

PAGE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>What's New in Python 3.15</title>
<style>
body {{ background: #0d1117; color: #c9d1d9; font-family: system-ui, sans-serif; margin: 2em auto; max-width: 70em; }}
h1 {{ font-weight: 600; }}
figure {{ margin: 0 0 2em; }}
figcaption {{ color: #8b949e; margin-bottom: 0.5em; }}
svg {{ display: block; width: 100%; height: auto; }}
</style>
</head>
<body>
<h1>What's New in Python 3.15</h1>
{figures}
</body>
</html>
"""


def collector(collect: list[tuple[str, Frame]], caption: str) -> Callable[[Frame], None]:
    """A screenshot handler that appends its frame to `collect`, captioned."""

    def handler(frame: Frame) -> None:
        collect.append((caption, frame))

    return handler


def autopilot(slides: tuple[Slide, ...], collect: list[tuple[str, Frame]]) -> Iterator[AnyEvent | AnyControl]:
    """Screenshots every step of every slide, starting from the first, then quits."""
    for index, slide in enumerate(slides):
        for step in range(slide.steps):
            caption = f"{index + 1}. {slide.title}" + (f" ({step + 1}/{slide.steps})" if slide.steps > 1 else "")
            yield Screenshot(handler=collector(collect, caption))
            if step < slide.steps - 1:
                yield KeyPressed(key=Key.Space)
                yield AdvanceClock(by=SETTLE)
        yield KeyPressed(key=Key.Right)
    yield Quit()


async def screenshots(slides: tuple[Slide, ...], host: Host) -> list[tuple[str, Frame]]:
    collected: list[tuple[str, Frame]] = []
    await app(
        root(slides, host, Checkpoint(slide=0), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot(slides, collected),
        clock=EXPORT_CLOCK,
    )
    return collected


def page(frames: list[tuple[str, Frame]]) -> str:
    figures = "\n".join(
        f"<figure>\n<figcaption>{escape(caption)}</figcaption>\n{frame.svg()}\n</figure>" for caption, frame in frames
    )
    return PAGE.format(figures=figures)


def write_tracked(path: Path, html: str) -> None:
    """
    Writes `html` to `path` in the repository, and marks a newly created file intent-to-add,
    so the pre-commit hook fails on the first export as it does on any other rewrite.
    """
    is_new = not path.exists()
    path.write_text(html)
    if is_new:
        subprocess.run(["git", "add", "--intent-to-add", str(path)], check=True)
