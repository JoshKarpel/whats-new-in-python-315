"""
The footer's rule is a progress bar through the deck: filled from the left as far across as the slide is through it,
revealing one ramp of colors in place, and slate past the fill.
"""

from datetime import UTC

import pytest
from counterweight import app
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.geometry import Position
from counterweight.paint import Frame
from counterweight.styles import AnyColor
from counterweight.styles import Color
from counterweight.styles.utilities import slate_600

from whats_new.components.frame import TALK_TITLE
from whats_new.components.frame import footer
from whats_new.components.look import GHOST
from whats_new.export import EXPORT_CLOCK
from whats_new.size import PRESENTING


async def drawn(passed: int, total: int, is_ghost: bool = False) -> Frame:
    """The footer `passed` slides of `total` through the talk, on a ghost or not."""
    frames: list[Frame] = []
    columns, rows = PRESENTING.dimensions
    await app(
        footer(passed, total, is_ghost, show_clock=False, show_size=False, columns=columns, rows=rows, timezone=UTC),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(Screenshot(handler=frames.append), Quit()),
        clock=EXPORT_CLOCK,
    )
    return frames[0]


async def rule_colors(passed: int, total: int, is_ghost: bool = False) -> list[AnyColor]:
    """The color of each cell of the footer's rule, left to right, `passed` slides of `total` through the talk."""
    columns, rows = PRESENTING.dimensions
    paint = (await drawn(passed, total, is_ghost)).paint
    rule = next(y for y in range(rows) if (cell := paint.get(Position(0, y))) is not None and cell.grapheme == "─")
    return [cell.style.foreground for x in range(columns) if (cell := paint.get(Position(x, rule))) is not None]


@pytest.mark.parametrize(
    ("passed", "filled"), [(1, 25), (2, 50), (3, 75), (4, 100)], ids=["first", "second", "third", "last"]
)
async def test_the_rule_fills_as_far_across_as_the_slide_is_through_the_deck(passed: int, filled: int) -> None:
    colors = await rule_colors(passed, 4)

    assert [color != slate_600 for color in colors] == [True] * filled + [False] * (len(colors) - filled)


def near(color: AnyColor, other: AnyColor) -> bool:
    """
    Whether two colors are the same give or take a few steps per channel: between blue and yellow, Oklch passes
    outside sRGB, so the fill's end color is clipped, which bends the colors just before it a little.
    """
    if not (isinstance(color, Color) and isinstance(other, Color)):
        return color == other
    return all(abs(a - b) <= 5 for a, b in zip(color, other, strict=True))


async def test_the_fill_reveals_the_same_colors_wherever_it_ends() -> None:
    early, late = await rule_colors(1, 4), await rule_colors(3, 4)

    assert all(near(a, b) for a, b in zip(early[:25], late[:25], strict=True))


def number_of(frame: Frame) -> str:
    """What the footer shows at the right of its line, where a slide's number goes."""
    line = next(line for line in frame.text(ansi=False).splitlines() if TALK_TITLE in line)
    return line.split()[-1]


async def test_a_slide_that_isnt_a_ghost_shows_its_number_in_the_talk() -> None:
    assert number_of(await drawn(3, 7)) == "7"


async def test_a_ghost_shows_a_ghost_in_place_of_a_number() -> None:
    frame = await drawn(3, 7, is_ghost=True)

    assert number_of(frame) == GHOST
    assert "/" not in frame.text(ansi=False)


async def test_a_ghost_fills_the_rule_as_far_as_the_slide_before_it() -> None:
    assert await rule_colors(2, 4, is_ghost=True) == await rule_colors(2, 4)


async def test_the_rule_is_empty_when_every_slide_is_a_ghost() -> None:
    assert all(color == slate_600 for color in await rule_colors(0, 0, is_ghost=True))
