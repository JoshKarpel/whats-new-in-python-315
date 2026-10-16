"""
Animations play on the app's clock: a live one starts from its first frame and ends on its last,
and one that isn't live (a thumbnail) is its last frame from the start.
"""

import re
from datetime import timedelta

import pytest
from counterweight.app import app
from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import AdvanceClock
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.output import Frame
from counterweight.styles import Color
from counterweight.styles.utilities import *

from whats_new.components.look import CARD_EDGE
from whats_new.components.look import PULSE_PERIOD
from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import SHINE_PERIOD
from whats_new.components.look import SHINE_SWEEP
from whats_new.components.look import SPARK_STEP
from whats_new.components.look import made_with_claude
from whats_new.components.look import pulse
from whats_new.components.look import title_card
from whats_new.diagrams import task_group
from whats_new.export import EXPORT_CLOCK
from whats_new.size import PRESENTING

FINISHED = "✗ cancelled"
"""What the race shows only once it's over."""


async def frames_of(drawing: Div | Component, by: timedelta = task_group.RACE) -> tuple[str, str]:
    """`drawing` as it mounts, and after the clock moves on `by`, by default past the end of the race's animation."""

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
            AdvanceClock(by=by),
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


async def test_the_claude_credit_turns_its_spark_while_live() -> None:
    mounted, later = await frames_of(made_with_claude(True), by=SPARK_STEP * 1.5)

    assert "✻ built" in mounted
    assert "✽ built" in later


async def test_the_claude_credit_holds_its_spark_still_when_not_live() -> None:
    _, later = await frames_of(made_with_claude(False), by=SPARK_STEP * 1.5)

    assert "✻ built" in later


async def card_colors(drawing: Component, by: timedelta, glyphs: str) -> list[str]:
    """The foreground color of each of `drawing`'s cells drawn as one of `glyphs`, after the clock moves `by`."""

    @component
    def alone() -> Div:
        return Div(style=row | full, children=(drawing,))

    frames: list[Frame] = []
    await app(
        alone(),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(AdvanceClock(by=by), Screenshot(handler=frames.append), Quit()),
        clock=EXPORT_CLOCK,
    )
    return re.findall(rf"\x1b\[38;2;(\d+;\d+;\d+)m(?:\x1b\[[0-9;]*m)*[{glyphs}]", frames[0].text(ansi=True))


def rgb(color: Color) -> str:
    """`color` as an ANSI truecolor escape spells it."""
    return f"{color.red};{color.green};{color.blue}"


@pytest.mark.parametrize("is_live", [True, False], ids=["live", "a thumbnail"])
async def test_a_title_cards_border_pulses(is_live: bool) -> None:
    card = title_card("Typing", is_live=is_live)

    assert await card_colors(card, PULSE_PERIOD / 8, "━┃┏┓┗┛") != await card_colors(card, PULSE_PERIOD / 4, "━┃┏┓┗┛")


@pytest.mark.parametrize(("is_live", "is_shining"), [(True, True), (False, False)], ids=["live", "a thumbnail"])
async def test_a_shine_crosses_the_title_only_while_live(is_live: bool, is_shining: bool) -> None:
    title = await card_colors(title_card("Typing", is_live=is_live), SHINE_PERIOD * SHINE_SWEEP / 2, "Typing")

    assert any(color != rgb(PYTHON_YELLOW) for color in title) == is_shining


@pytest.mark.parametrize(
    ("phase", "expected"),
    [(0.0, CARD_EDGE), (0.25, PYTHON_BLUE), (0.5, CARD_EDGE), (0.75, PYTHON_YELLOW)],
    ids=["slate at rest", "out to blue", "back through slate", "out to yellow"],
)
def test_the_pulse_swings_between_blue_and_yellow_through_slate(phase: float, expected: Color) -> None:
    # Within a unit per channel: sin(pi) is 1e-16, not 0, and `Color.blend` truncates to an int.
    color = pulse(phase)

    assert all(abs(a - b) <= 1 for a, b in zip(color, expected, strict=True))
