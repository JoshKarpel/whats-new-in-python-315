"""
The showcase: every slide transition F6 offers, played in turn as the deck moves on from its first slide,
as an asciicast with a chapter per transition. Each is picked on screen from F6's picker, one option down from
the last, so the recording shows how to pick a transition as well as what each looks like.

Unlike the deck's recording, it runs nothing and waits for nothing real: every moment passes on the frozen clock,
one animation frame at a time, so it comes out the same on every recording.
"""

from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from typing import assert_never

from counterweight.app import app
from counterweight.asciicast import Recording
from counterweight.autopilot import AutopilotStep
from counterweight.controls import Marker
from counterweight.controls import Quit
from counterweight.events import KeyPressed
from counterweight.keys import Key

from whats_new.checkpoint import Checkpoint
from whats_new.components.frame import TALK_TITLE
from whats_new.components.swipe import SWIPE
from whats_new.components.transitions import RANDOM
from whats_new.components.transitions import SPEEDS
from whats_new.components.transitions import Crossed
from whats_new.components.transitions import Swiped
from whats_new.components.transitions import Transition
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.recording import IDLE_LIMIT
from whats_new.recording import THEME
from whats_new.size import PRESENTING
from whats_new.slides import Slide
from whats_new.tours import hold

PICKING = timedelta(seconds=0.6)
"""How long the picker shows before and after moving down to the next transition, long enough to read its name."""
SETTLED = timedelta(seconds=1)
"""How long the showcase holds on each slide a transition arrives at, before picking the next one."""

START = Checkpoint(slide=0, code_theme="dracula", transition=RANDOM, easing="ease-in-out", speed="0.5x")
"""
Where the showcase starts: on the first slide, with `random`, the option just ahead of the transitions, so moving
one option down picks the first,
and each one down after that picks the next, in the order F6 lists them. At half speed, so there's time to see
what each one does.
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


def showcased(transitions: tuple[tuple[str, Transition], ...]) -> Iterator[AutopilotStep]:
    """
    Each of `transitions`, which must be F6's first options after `random`, in its order: picked from F6's picker,
    then played moving on to the next slide, and held on there.
    """
    for number, (name, transition) in enumerate(transitions, start=1):
        yield Marker(label=f"{number}. {name}")
        yield KeyPressed(key=Key.F6)
        yield from hold(PICKING)
        yield KeyPressed(key=Key.Down)
        yield from hold(PICKING)
        yield KeyPressed(key=Key.Enter)
        yield KeyPressed(key=Key.Right)
        yield from hold(duration_of(transition) + SETTLED)
    yield Quit()


async def record_showcase(
    slides: tuple[Slide, ...], host: Host, transitions: tuple[tuple[str, Transition], ...], path: Path
) -> None:
    """Records `transitions` showcased on `slides` to `path`, which needs a slide more than there are transitions."""
    if len(slides) <= len(transitions):
        raise ValueError(
            f"showcasing {len(transitions)} transitions needs {len(transitions) + 1} slides, not {len(slides)}"
        )
    await app(
        root(slides, host, START, lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=showcased(transitions),
        clock=EXPORT_CLOCK,
        recording=Recording(
            path, title=f"{TALK_TITLE}: slide transitions", idle_time_limit=IDLE_LIMIT, theme=THEME, input=True
        ),
    )
