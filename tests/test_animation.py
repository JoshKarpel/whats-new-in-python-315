"""
Animations play on the app's clock: a live one starts from its first frame and ends on its last,
and one that isn't live (a thumbnail) is its last frame from the start.
"""

import re
from datetime import timedelta

import pytest
from counterweight import app
from counterweight.animation import FRAME_INTERVAL
from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import AdvanceClock
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.hooks import use_clock
from counterweight.paint import Frame
from counterweight.styles import Color
from counterweight.styles.utilities import *

from whats_new.components.grid import thumbnail
from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import SHINE_PERIOD
from whats_new.components.look import SHINE_SWEEP
from whats_new.components.look import SPARK_STEP
from whats_new.components.look import TURN_PERIOD
from whats_new.components.look import made_with_claude
from whats_new.components.look import title_card
from whats_new.deck import SLIDES
from whats_new.diagrams import task_group
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.sections.tachyon import STREAK_PERIOD
from whats_new.sections.tachyon import streak
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


BORDER = "━┃┏┓┗┛"
TYPING_WIDTH = len("┏" + " " * 4 + "Typing" + " " * 4 + "┓")
"""How many of a "Typing" card's border cells are on its top row, and on its bottom one."""


@pytest.mark.parametrize("is_live", [True, False], ids=["live", "a thumbnail"])
async def test_a_title_cards_border_turns(is_live: bool) -> None:
    card = title_card("Typing", is_live=is_live)

    assert await card_colors(card, TURN_PERIOD / 8, BORDER) != await card_colors(card, TURN_PERIOD / 4, BORDER)


async def test_a_title_card_mounted_late_starts_its_turn_from_the_start() -> None:
    by = TURN_PERIOD / 4

    @component
    def late() -> Div:
        tick = use_clock(FRAME_INTERVAL)
        return Div(style=row | full, children=(title_card("Typing", is_live=True),) if tick.since_start >= by else ())

    assert await card_colors(late(), by, BORDER) == await card_colors(
        title_card("Typing", is_live=True), timedelta(), BORDER
    )


def near(color: str, expected: Color) -> bool:
    """Whether `color`, as an ANSI truecolor escape spells it, is `expected`, give or take a little per channel."""
    return all(abs(int(channel) - other) <= 8 for channel, other in zip(color.split(";"), expected, strict=True))


@pytest.mark.parametrize(
    ("by", "top", "bottom"),
    [(timedelta(), PYTHON_BLUE, PYTHON_YELLOW), (TURN_PERIOD / 2, PYTHON_YELLOW, PYTHON_BLUE)],
    ids=["at the start", "half a turn on"],
)
async def test_a_title_cards_border_turns_blue_and_yellow_around_it(by: timedelta, top: Color, bottom: Color) -> None:
    colors = await card_colors(title_card("Typing", is_live=True), by, BORDER)

    assert near(colors[TYPING_WIDTH // 2], top)
    assert near(colors[-TYPING_WIDTH // 2], bottom)


@pytest.mark.parametrize(("is_live", "is_shining"), [(True, True), (False, False)], ids=["live", "a thumbnail"])
async def test_a_shine_crosses_the_title_only_while_live(is_live: bool, is_shining: bool) -> None:
    title = await card_colors(title_card("Typing", is_live=is_live), SHINE_PERIOD * SHINE_SWEEP / 2, "Typing")

    assert any(color != rgb(PYTHON_YELLOW) for color in title) == is_shining


def brightness(color: str) -> int:
    """How bright `color`, as an ANSI truecolor escape spells it, is, by the sum of its channels."""
    return sum(int(channel) for channel in color.split(";"))


async def test_the_tachyon_streaks_trail_fades_away_from_the_particle() -> None:
    # A third of the way through the loop, the particle is halfway across, with its whole trail behind it.
    trail = await card_colors(streak(True), STREAK_PERIOD / 3, "━─·")

    brightnesses = [brightness(color) for color in trail]
    assert brightnesses == sorted(brightnesses)
    assert brightnesses[0] < brightnesses[-1]


def typing_thumbnail(host: Host, is_selected: bool) -> Component:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "Typing")
    return thumbnail(SLIDES, index, is_selected, lambda index: (), host, "github-dark")


THUMBNAIL_BORDER = "╭╮╰╯─│"


async def test_the_selected_thumbnails_border_turns(host: Host) -> None:
    earlier = await card_colors(typing_thumbnail(host, is_selected=True), TURN_PERIOD / 8, THUMBNAIL_BORDER)
    later = await card_colors(typing_thumbnail(host, is_selected=True), TURN_PERIOD / 4, THUMBNAIL_BORDER)

    assert earlier != later


async def test_the_other_thumbnails_borders_stay_slate(host: Host) -> None:
    colors = await card_colors(typing_thumbnail(host, is_selected=False), TURN_PERIOD / 8, THUMBNAIL_BORDER)

    assert set(colors) == {rgb(slate_600)}
