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

from whats_new.components.frame import footer
from whats_new.export import EXPORT_CLOCK
from whats_new.size import PRESENTING


async def rule_colors(index: int, total: int) -> list[AnyColor]:
    """The color of each cell of the footer's rule, left to right, on slide `index` of `total`."""
    frames: list[Frame] = []
    columns, rows = PRESENTING.dimensions
    await app(
        footer(index, total, show_clock=False, show_size=False, columns=columns, rows=rows, timezone=UTC),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(Screenshot(handler=frames.append), Quit()),
        clock=EXPORT_CLOCK,
    )
    paint = frames[0].paint
    rule = next(y for y in range(rows) if (cell := paint.get(Position(0, y))) is not None and cell.grapheme == "─")
    return [cell.style.foreground for x in range(columns) if (cell := paint.get(Position(x, rule))) is not None]


@pytest.mark.parametrize(("index", "filled"), [(0, 25), (1, 50), (2, 75)], ids=["first", "second", "third"])
async def test_the_rule_fills_as_far_across_as_the_slide_is_through_the_deck(index: int, filled: int) -> None:
    colors = await rule_colors(index, 4)

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
    early, late = await rule_colors(0, 4), await rule_colors(2, 4)

    assert all(near(a, b) for a, b in zip(early[:25], late[:25], strict=True))
