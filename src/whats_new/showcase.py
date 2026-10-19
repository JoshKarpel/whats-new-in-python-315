"""
The showcases, each an asciicast with a chapter per transition: every slide transition F6 offers, played in turn
as the deck moves on from its first slide, and every one of the grid's own transitions F7 offers, each played
opening the grid and closing it again onto the next slide. Each is picked on screen from its picker, one option down
from the last, so the recording shows how to pick a transition as well as what each looks like.

Unlike the deck's recording, they run nothing and wait for nothing real: every moment passes on the frozen clock,
one animation frame at a time, so each comes out the same on every recording.
"""

from collections.abc import Iterable
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from typing import assert_never

from counterweight.app import app
from counterweight.asciicast import Recording
from counterweight.autopilot import AutopilotStep
from counterweight.autopilot import advance
from counterweight.controls import Marker
from counterweight.controls import Quit
from counterweight.events import KeyPressed
from counterweight.keys import Key

from whats_new.checkpoint import Checkpoint
from whats_new.components.frame import TALK_TITLE
from whats_new.components.swipe import SWIPE
from whats_new.components.transitions import GRID_GROUPS
from whats_new.components.transitions import RANDOM
from whats_new.components.transitions import SPEEDS
from whats_new.components.transitions import Crossed
from whats_new.components.transitions import GridTransition
from whats_new.components.transitions import Swiped
from whats_new.components.transitions import Tiled
from whats_new.components.transitions import Transition
from whats_new.components.transitions import Zoomed
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.recording import IDLE_LIMIT
from whats_new.recording import THEME
from whats_new.size import PRESENTING
from whats_new.slides import Slide

PICKING = timedelta(seconds=0.6)
"""How long the picker shows before and after moving down to the next transition, long enough to read its name."""
SETTLED = timedelta(seconds=1)
"""How long the showcase holds on each slide a transition arrives at, before picking the next one."""

START = Checkpoint(slide=0, code_theme="dracula", transition=RANDOM, speed="0.5x")
"""
Where the showcase starts: on the first slide, with `random`, the option just ahead of the transitions, so moving
one option down picks the first,
and each one down after that picks the next, in the order F6 lists them. At half speed, so there's time to see
what each one does.
"""

GRID_EFFECTS = GRID_GROUPS[0]
"""
The grid's own transitions, which the grid's showcase plays. Not F6's effects F7 also offers,
since the slides' showcase already shows what each of those looks like.
"""
GRID_START = Checkpoint(slide=0, code_theme="dracula", speed="0.5x", grid_transition=GRID_EFFECTS.title)
"""
Where the grid's showcase starts: on the first slide, with the bar of the grid's own transitions picked,
which F7 lists just ahead of them, so moving one option down picks the first, and so on, as `START` does for F6.
"""


def duration_of(transition: Transition) -> timedelta:
    """How long `transition` plays at the showcase's speed."""
    match transition:
        case Swiped():
            return SWIPE / SPEEDS[START.speed]
        case Crossed(duration=duration):
            return duration / SPEEDS[START.speed]
        case _ as unreachable:
            assert_never(unreachable)


def grid_duration_of(transition: GridTransition) -> timedelta:
    """How long `transition` plays, opening or closing the grid, at the grid's showcase's speed."""
    match transition:
        case Zoomed():
            return SWIPE / SPEEDS[GRID_START.speed]
        case Tiled(duration=duration) | Crossed(duration=duration):
            return duration / SPEEDS[GRID_START.speed]
        case _ as unreachable:
            assert_never(unreachable)


def showcased(transitions: tuple[tuple[str, Transition], ...]) -> Iterator[AutopilotStep]:
    """
    Each of `transitions`, which must be F6's first options after `random`, in its order: picked from F6's picker,
    then played moving on to the next slide, and held on there.
    """
    for number, (name, transition) in enumerate(transitions, start=1):
        yield Marker(label=f"{number}. {name}")
        yield from picked(Key.F6)
        yield KeyPressed(key=Key.Right)
        yield from advance(duration_of(transition) + SETTLED)
    yield Quit()


def grid_showcased(transitions: tuple[tuple[str, GridTransition], ...]) -> Iterator[AutopilotStep]:
    """
    Each of `transitions`, which must be F7's first options after `GRID_START`'s, in its order: picked from F7's
    picker, then played opening the grid, held on there, and played again closing it onto the next slide.
    """
    for number, (name, transition) in enumerate(transitions, start=1):
        yield Marker(label=f"{number}. {name}")
        yield from picked(Key.F7)
        yield KeyPressed(key="d")
        yield from advance(grid_duration_of(transition) + SETTLED)
        # Onto the next slide rather than back to this one, so each closing lands somewhere new.
        yield KeyPressed(key=Key.Right)
        yield from advance(PICKING)
        yield KeyPressed(key=Key.Enter)
        yield from advance(grid_duration_of(transition) + SETTLED)
    yield Quit()


def picked(key: Key) -> list[AutopilotStep]:
    """The option after the one picked, picked from the picker `key` opens, slowly enough to read both."""
    return [
        KeyPressed(key=key),
        *advance(PICKING),
        KeyPressed(key=Key.Down),
        *advance(PICKING),
        KeyPressed(key=Key.Enter),
    ]


async def record_showcase(
    slides: tuple[Slide, ...], host: Host, transitions: tuple[tuple[str, Transition], ...], path: Path
) -> None:
    """Records `transitions` showcased on `slides` to `path`, which needs a slide more than there are transitions."""
    await record(slides, host, START, len(transitions), showcased(transitions), "slide transitions", path)


async def record_grid_showcase(
    slides: tuple[Slide, ...], host: Host, transitions: tuple[tuple[str, GridTransition], ...], path: Path
) -> None:
    """
    Records the grid's `transitions` showcased on `slides` to `path`,
    which needs a slide more than there are transitions.
    """
    await record(slides, host, GRID_START, len(transitions), grid_showcased(transitions), "grid transitions", path)


async def record(
    slides: tuple[Slide, ...],
    host: Host,
    start: Checkpoint,
    moves: int,
    steps: Iterable[AutopilotStep],
    subtitle: str,
    path: Path,
) -> None:
    """Records the deck from `start` driven by `steps` to `path`, refusing first if it can't move on `moves` times."""
    if len(slides) <= moves:
        raise ValueError(f"showcasing {moves} transitions needs {moves + 1} slides, not {len(slides)}")
    await app(
        root(slides, host, start, lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=steps,
        clock=EXPORT_CLOCK,
        recording=Recording(
            path, title=f"{TALK_TITLE}: {subtitle}", idle_time_limit=IDLE_LIMIT, theme=THEME, input=True
        ),
    )
