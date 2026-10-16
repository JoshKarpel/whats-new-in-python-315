"""
Animations play on the app's clock: a live one starts from its first frame and ends on its last,
and one that isn't live (a thumbnail) is its last frame from the start.
"""

from counterweight.app import app
from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import AdvanceClock
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.output import Frame
from counterweight.styles.utilities import *

from whats_new.diagrams import task_group
from whats_new.export import EXPORT_CLOCK
from whats_new.size import PRESENTING

FINISHED = "✗ cancelled"
"""What the race shows only once it's over."""


async def frames_of(drawing: Div | Component) -> tuple[str, str]:
    """`drawing` as it mounts, and after the clock moves on past the end of its animation."""

    @component
    def alone() -> Div:
        return Div(style=row | full, children=(drawing,))

    frames: list[Frame] = []
    await app(
        alone(),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            Screenshot(handler=frames.append),
            AdvanceClock(by=task_group.RACE),
            Screenshot(handler=frames.append),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )
    mounted, finished = (frame.text(ansi=False) for frame in frames)
    return mounted, finished


async def test_a_live_animation_starts_at_its_first_frame_and_ends_at_its_last() -> None:
    mounted, finished = await frames_of(task_group.task_group(1, True))

    assert FINISHED not in mounted
    assert FINISHED in finished


async def test_an_animation_that_isnt_live_shows_its_last_frame_at_once() -> None:
    mounted, _ = await frames_of(task_group.task_group(1, False))

    assert FINISHED in mounted
