"""
A split-flap departure board: every cell that differs between the slides spins through random characters and locks
onto its arriving character, column after column in the direction the slides travel, left to right moving to the next
slide. A cell the same on both slides stays still, as a flap with nothing to change doesn't turn.

Spinning cells are drawn in the colors of the character they're spinning toward (or away from, for one that ends
empty), so each column's text is already its own color as it locks. The columns lock at a
steady clip, as a board's mechanism turns them.
"""

import random
from functools import cache
from math import inf

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.swipe import Direction

FACES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#$%&*+=?@<>"
"""
What a spinning cell flips through: ASCII only, so it draws the same everywhere. Its length is prime, so every stride
through it visits every face before repeating.
"""
BLANK_FACE = Color.from_hex("#64748b")
"""The color a cell empty on both slides spins in: Tailwind's slate 500, there without competing with the text."""
FLIPS = 40
"""How many times a spinning cell changes face over the whole transition."""
STARTING = 0.3
"""How much of the progress the columns set off spinning over, one after another."""
FIRST_LOCK, LAST_LOCK = 0.3, 0.95
"""When, in the progress, the first column and the last lock onto the arriving slide."""
JITTER = 0.04
"""How far a cell's start and lock stray from its column's, so a column doesn't move as one rigid strip."""


@cache
def faces(foreground: AnyColor | UNSET, background: AnyColor | UNSET) -> tuple[StyledGrapheme, ...]:
    """Every face a spinning cell can show, `foreground` on `background`."""
    style = CellStyle(foreground=foreground, background=background)
    return tuple(StyledGrapheme(grapheme=face, style=style) for face in FACES)


def is_visible(glyph: StyledGrapheme | None) -> bool:
    """Whether `glyph` draws a character, rather than nothing, a space, or the second half of one to its left."""
    return glyph is not None and bool(glyph.grapheme.strip())


def spinning_faces(before: StyledGrapheme | None, after: StyledGrapheme | None) -> tuple[StyledGrapheme, ...]:
    """
    The faces one cell spins through: in the color of its arriving character, or of its leaving one if it ends empty,
    on the arriving slide's background.
    """
    shown = after if is_visible(after) else before if is_visible(before) else None
    foreground = BLANK_FACE if shown is None else shown.style.foreground
    return faces(foreground, (after or SPACE).style.background)


def slots(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The departure board's frames. Each cell is its leaving character until the progress reaches its start,
    a spinning face until it reaches its lock, and its arriving character after.
    """
    width, height = dimensions(leaving)
    chance = random.Random(315)

    def order(x: int) -> float:
        """How far along the order the columns lock in column `x` is, from 0 for the first to 1 for the last."""
        along = x / max(width - 1, 1)
        return along if direction is Direction.NEXT else 1 - along

    def start(x: int, before: StyledGrapheme | None, after: StyledGrapheme | None) -> float:
        """When a cell in column `x` starts spinning: never, if it's the same on both slides."""
        if before == after:
            return inf
        return (STARTING - JITTER) * order(x) + chance.uniform(0, JITTER)

    def lock(x: int) -> float:
        """When a cell in column `x` locks onto its arriving character, always before the end."""
        return FIRST_LOCK + (LAST_LOCK - FIRST_LOCK - JITTER) * order(x) + chance.uniform(0, JITTER)

    starts = tuple(
        tuple(start(x, before, after) for x, (before, after) in enumerate(zip(old, new, strict=True)))
        for old, new in zip(leaving, arriving, strict=True)
    )
    locks = tuple(tuple(lock(x) for x in range(width)) for _ in range(height))
    reels = tuple(
        tuple(spinning_faces(before, after) for before, after in zip(old, new, strict=True))
        for old, new in zip(leaving, arriving, strict=True)
    )
    # Each cell flips through the faces from its own offset by its own stride, so neighbors don't flip in step.
    offsets = tuple(tuple(chance.randrange(len(FACES)) for _ in range(width)) for _ in range(height))
    strides = tuple(tuple(chance.randrange(1, len(FACES)) for _ in range(width)) for _ in range(height))

    def frame(t: float) -> Grid:
        flip = int(t * FLIPS)
        return tuple(
            tuple(
                before if t <= begun else after if t >= locked else reel[(offset + flip * stride) % len(FACES)]
                for before, after, begun, locked, reel, offset, stride in zip(*rows, strict=True)
            )
            for rows in zip(leaving, arriving, starts, locks, reels, offsets, strides, strict=True)
        )

    return frame
