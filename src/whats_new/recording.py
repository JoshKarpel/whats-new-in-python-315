"""
The recording: the whole deck presented by an autopilot at the presenting size, as an asciicast
that asciinema-player plays back, with a chapter per slide.

Unlike the export, it runs things: each slide's tour, and then its runs, after its last reveal step.
Those take real time, which the autopilot waits out by watching the screen, so the recording comes out a little
different every time, and nothing regenerates it on commit as the export is.
So does an animation a reveal step plays: the autopilot waits for its last frame (`Slide.ends_showing`),
since a hold cut short of the end would never show where it lands. The holds are paced by the frozen clock,
so each lasts exactly as long on every recording.
"""

import re
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

from counterweight.app import app
from counterweight.asciicast import Recording
from counterweight.asciicast import Theme
from counterweight.autopilot import AutopilotStep
from counterweight.autopilot import WaitFor
from counterweight.controls import Marker
from counterweight.controls import Quit
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame
from counterweight.paint import SVG_BACKGROUND
from counterweight.paint import SVG_FOREGROUND
from counterweight.styles import DEFAULT_PALETTE

from whats_new.checkpoint import Checkpoint
from whats_new.components.frame import TALK_TITLE
from whats_new.components.run_pane import NUMBER_KEYS
from whats_new.components.run_pane import RUN_TIMEOUT
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.runs import Capability
from whats_new.runs import Run
from whats_new.size import PRESENTING
from whats_new.slides import Slide
from whats_new.tours import hold
from whats_new.tours import showing

REVEAL = timedelta(seconds=3)
"""How long the recording holds on each reveal step, to read it."""
AFTER_RUN = timedelta(seconds=3)
"""How long it holds on a run's output once the run ends."""
IDLE_LIMIT = timedelta(seconds=3)
"""
The longest pause a player shows, which cuts short a run's silences.
No shorter than the holds, which draw nothing on a slide with nothing animating.
"""

START = Checkpoint(slide=0, code_theme="dracula", transition="swipe", easing="ease-in-out", zooms_grid=True)
"""Where the recording starts, and the code theme and slide transition it presents in."""

THEME = Theme(foreground=SVG_FOREGROUND, background=SVG_BACKGROUND, palette=DEFAULT_PALETTE[:16])
"""The colors the export's screenshots draw the terminal's own colors in, so the two look alike."""

IN_PROGRESS = re.compile(r"(starting|running)$")
FINISHED = re.compile(r"(exited -?\d+|ended by .+|failed to start: .+|cancelled|timed out)$")
"""How the run pane's line of names ends, after the outcome of the run it shows (`outcome_text`)."""


def outcome_shows(pattern: re.Pattern[str], first: Run) -> WaitFor:
    """
    Waits until the run pane's line of names, found by the slide's `first` run, ends with an outcome matching `pattern`.
    The line, rather than the whole screen, so a run's output or the slide's code saying "running" doesn't count.
    """

    def condition(frame: Frame) -> bool:
        return any(
            f" 1 {first.label}" in line and pattern.search(line.rstrip())
            for line in frame.text(ansi=False).splitlines()
        )

    return WaitFor(condition, timeout=RUN_TIMEOUT + timedelta(seconds=10))


def run_all(slide: Slide, capabilities: frozenset[Capability]) -> Iterator[AutopilotStep]:
    """
    Each of `slide`'s runs that this machine can run, in order, each held on once it ends.
    A run's key leaves the last run's outcome showing until the new run starts, so the autopilot waits for the new
    run to show as in progress before waiting for it to finish; the pane shows `starting` for at least a frame.
    """
    for key, run in zip(NUMBER_KEYS, slide.runs, strict=False):
        if run.needs - capabilities:
            continue
        yield KeyPressed(key=key)
        yield outcome_shows(IN_PROGRESS, slide.runs[0])
        yield outcome_shows(FINISHED, slide.runs[0])
        yield from hold(AFTER_RUN)


def presented(slides: tuple[Slide, ...], capabilities: frozenset[Capability]) -> Iterator[AutopilotStep]:
    """
    The deck presented from its first slide: each reveal step played out, held on and toured, then the slide's runs.
    """
    for index, slide in enumerate(slides):
        yield Marker(label=f"{index + 1}. {slide.title}")
        for step in range(slide.steps):
            if step > 0:
                yield KeyPressed(key=Key.Space)
            if (end := slide.ends_showing(step)) is not None:
                yield showing(end)
            yield from hold(REVEAL)
            yield from slide.tour(step)
        yield from run_all(slide, capabilities)
        if index < len(slides) - 1:
            yield KeyPressed(key=Key.Right)
    yield Quit()


async def record(slides: tuple[Slide, ...], host: Host, capabilities: frozenset[Capability], path: Path) -> None:
    await app(
        root(slides, host, START, lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=presented(slides, capabilities),
        clock=EXPORT_CLOCK,
        recording=Recording(path, title=TALK_TITLE, idle_time_limit=IDLE_LIMIT, theme=THEME, input=True),
    )
