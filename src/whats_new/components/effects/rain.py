"""
Digital rain, as in The Matrix: a drop falls down every column, each at its own speed and moment, with a bright head
and a trail of glyphs fading from green to dark behind it. Below a drop's head the leaving slide still shows;
the trail washes over the cells it has passed, and above it the arriving slide is left in place.

Partway up the trail the arriving slide's own characters come through the rain, green at first, settling into
their own colors by the trail's end, so each column of the arriving slide develops out of its drop.
Each drop falls at a steady speed of its own, so the rain doesn't ease.
"""

import random
from dataclasses import dataclass
from functools import cache

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor
from counterweight.styles.styles import resolve_cell_style
from counterweight.styles.styles import rgb_of

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.swipe import Direction

GLYPHS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$+-*=<>:.!?#&|"
"""What the rain is made of: ASCII only, since anything wider or rarer isn't drawn reliably in every terminal."""
SCREENSHOT_FOREGROUND = Color.from_name("white")
"""The terminal's default text color, as a screenshot draws it."""
HEAD = Color.from_hex("#e8ffe8")
GREEN = Color.from_hex("#22ff55")
DARK_GREEN = Color.from_hex("#0b3d14")
SHADES = 8
"""How many steps the trail fades through, from `GREEN` just behind the head to `DARK_GREEN` at its end."""
SETTLE = 0.4
"""How far up its trail a drop starts letting the arriving slide's characters through."""
FLICKERS = 36
"""How many times the rain glyphs change over the whole transition."""
SHORTEST, LONGEST = 6, 14
"""The range of a trail's length, in rows."""
QUICKEST, SLOWEST = 0.3, 0.55
"""The range of how much of the progress a drop takes to fall from above the top until its trail is gone."""
STAGGER = 0.35
"""
How much of the progress the drops' departures are biased across, from the side the arriving slide comes from,
on top of their random delays, so the rain sweeps over the slide rather than starting everywhere at once.
"""


@dataclass(frozen=True, slots=True)
class Drop:
    """
    One column's drop: it sets off `delay` of the way through the progress, takes `fall` of it to fall from
    just above the stage until its trail, `trail` rows long, has passed the bottom.
    """

    delay: float
    fall: float
    trail: int

    def head(self, progress: float, height: int) -> float:
        """The row the drop's head is on `progress` of the way through: -1 before it sets off, below the stage after."""
        return -1 + (height + self.trail + 1) * between(progress, self.delay, self.delay + self.fall)


def drops(width: int, direction: Direction, chance: random.Random) -> tuple[Drop, ...]:
    """
    Every column's drop, each ending before the progress does, so the last frame is the arriving slide whole.
    Columns nearer the side the arriving slide comes from tend to set off sooner.
    """

    def drop(x: int) -> Drop:
        """Column `x`'s drop, its departure biased by how far the column is from the arriving side."""
        fall = chance.uniform(QUICKEST, SLOWEST)
        trail = chance.randint(SHORTEST, LONGEST)
        order = (width - 1 - x if direction is Direction.NEXT else x) / width
        latest = 0.97 - fall - STAGGER
        return Drop(delay=STAGGER * order + chance.uniform(0, latest), fall=fall, trail=trail)

    return tuple(drop(x) for x in range(width))


def foreground_of(glyph: StyledGrapheme) -> Color:
    """The color `glyph`'s character is drawn in, with anything unset or up to the terminal as a screenshot draws it."""
    return rgb_of(resolve_cell_style(glyph.style).foreground, SCREENSHOT_FOREGROUND)


def shade_of(nearness: float) -> Color:
    """The trail's color `nearness` of the way back from its head (0) to its end (1)."""
    return GREEN.blend(DARK_GREEN, nearness)


@cache
def raindrop(index: int, shade: int, background: AnyColor | UNSET) -> StyledGrapheme:
    """Rain glyph `index` of `GLYPHS` over `background`, `shade` steps back along the trail, or the head at -1."""
    foreground = HEAD if shade < 0 else shade_of(shade / SHADES)
    return StyledGrapheme(
        grapheme=GLYPHS[index],
        style=CellStyle(foreground=foreground, background=background, bold=shade < 0),
    )


@cache
def settling(glyph: StyledGrapheme, shade: int) -> StyledGrapheme:
    """`glyph` coming through the rain, `shade` of `SHADES` steps from the trail's green to its own color."""
    foreground = shade_of(SETTLE).blend(foreground_of(glyph), shade / SHADES)
    return StyledGrapheme(grapheme=glyph.grapheme, style=glyph.style | CellStyle(foreground=foreground))


def rain(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    Digital rain's frames. Each cell is the leaving slide's below its column's drop, the arriving slide's once the
    drop's trail has passed, and in between a rain glyph, or partway up the trail, the arriving character settling.
    """
    width, height = dimensions(leaving)
    chance = random.Random(315)
    columns = drops(width, direction, chance)
    lengths = tuple(drop.trail for drop in columns)
    # Each cell steps through the glyphs from its own start by its own stride, so neighbors don't change in step.
    starts = tuple(tuple(chance.randrange(len(GLYPHS)) for _ in range(width)) for _ in range(height))
    strides = tuple(tuple(chance.randrange(1, len(GLYPHS)) for _ in range(width)) for _ in range(height))

    def trailing(
        arrived: StyledGrapheme | None, behind: float, length: int, start: int, stride: int, flicker: int
    ) -> StyledGrapheme | None:
        """What a cell `behind` rows back from its drop's head (within a trail `length` long) shows."""
        nearness = behind / length
        if nearness >= SETTLE and arrived is not None and arrived.grapheme.strip():
            return settling(arrived, int((nearness - SETTLE) / (1 - SETTLE) * SHADES))
        background = arrived.style.background if arrived is not None else UNSET
        shade = -1 if behind < 1 else int(nearness * SHADES)
        return raindrop((start + flicker * stride) % len(GLYPHS), shade, background)

    def row_at(
        y: int,
        before: tuple[StyledGrapheme | None, ...],
        after: tuple[StyledGrapheme | None, ...],
        heads: list[float],
        flicker: int,
    ) -> tuple[StyledGrapheme | None, ...]:
        """Row `y` of the frame with each column's head at `heads`."""
        return tuple(
            old
            if (behind := head - y) < 0
            else new
            if behind >= length
            else trailing(new, behind, length, start, stride, flicker)
            for old, new, head, length, start, stride in zip(
                before, after, heads, lengths, starts[y], strides[y], strict=True
            )
        )

    def frame(t: float) -> Grid:
        heads = [drop.head(t, height) for drop in columns]
        flicker = int(t * FLICKERS)
        return tuple(
            row_at(y, before, after, heads, flicker)
            for y, (before, after) in enumerate(zip(leaving, arriving, strict=True))
        )

    return frame
