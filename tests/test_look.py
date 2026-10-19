"""A drop shadow fades from its far corner toward its two ends, where it meets the slide."""

from counterweight.app import app
from counterweight.components import component
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.geometry import Position
from counterweight.output import Frame
from counterweight.styles import Color
from counterweight.styles.utilities import *

from whats_new.components.look import drop_shadow
from whats_new.export import EXPORT_CLOCK
from whats_new.size import PRESENTING


def brightness(color: object) -> int:
    if not isinstance(color, Color):
        raise TypeError(f"a shadow is drawn in RGB colors, not {color!r}")
    return color.red + color.green + color.blue


async def test_a_drop_shadow_fades_toward_its_ends() -> None:
    @component
    def alone() -> Div:
        return Div(
            style=col | full | center_children,
            children=(drop_shadow(Text(content="a card", style=border | pad_x(4) | pad_y(1))),),
        )

    frames: list[Frame] = []
    await app(
        alone(),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(Screenshot(handler=frames.append), Quit()),
        clock=EXPORT_CLOCK,
    )
    columns, rows = PRESENTING.dimensions
    shadow = {
        (x, y): cell.style.foreground
        for y in range(rows)
        for x in range(columns)
        if (cell := frames[0].paint.get(Position(x, y))) is not None and cell.grapheme == "░"
    }
    right, bottom = max(x for x, _ in shadow), max(y for _, y in shadow)
    top_end = shadow[(right, min(y for x, y in shadow if x == right))]
    left_end = shadow[(min(x for x, y in shadow if y == bottom), bottom)]

    assert brightness(shadow[(right, bottom)]) > brightness(top_end)
    assert brightness(shadow[(right, bottom)]) > brightness(left_end)
