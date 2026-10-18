"""
The snake: a snake races over the stage along a space-filling curve, eating the slide being left, and everything
behind its head is the arriving slide. Apples lie on the curve ahead of it, and each one it eats makes it longer,
as in the game. It's Python blue with a yellow head, naturally.

The curve is a generalized Hilbert curve, which fills a rectangle of any size, not only a power of two, one step
at a time. It runs over blocks two cells wide, about square on screen, so the snake turns corners rather than
stretching. Moving back to the previous slide, it runs the curve from the other end. The head runs on past the
curve's end until the tail has left the stage too, so the last frame is the arriving slide alone.
"""

import random
from collections.abc import Iterator

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.swipe import Direction

BLOCK = 2
"""How many cells wide one step of the curve is: two, so a step is about square on screen."""
LENGTH = 12
"""How many blocks long the snake starts."""
GROWTH = 6
"""How many blocks longer each apple makes it."""
APPLE = Color.from_hex("#E5484D")

BODY = StyledGrapheme(grapheme="█", style=CellStyle(foreground=PYTHON_BLUE))
HEAD = StyledGrapheme(grapheme="█", style=CellStyle(foreground=PYTHON_YELLOW))


def sign(value: int) -> int:
    return (value > 0) - (value < 0)


def generalized_hilbert(width: int, height: int) -> tuple[tuple[int, int], ...]:
    """
    Every cell of a `width` by `height` rectangle, once each, in an order where each cell neighbors the one before
    (diagonally, at most, on some odd sizes). This is Jakub Červený's `gilbert2d`
    (https://github.com/jakubcerveny/gilbert): it splits the rectangle in two along its longer side, or in three,
    and recurses, nudging the splits so every piece's path can join the next.
    """
    if width == 0 or height == 0:
        return ()
    if width >= height:
        return tuple(curve(0, 0, width, 0, 0, height))
    return tuple(curve(0, 0, 0, height, width, 0))


def curve(x: int, y: int, ax: int, ay: int, bx: int, by: int) -> Iterator[tuple[int, int]]:
    """
    The curve through the rectangle from `(x, y)` spanned by the major axis `(ax, ay)` and the minor axis `(bx, by)`,
    starting at its corner and ending at the far end of the major axis.
    """
    width, height = abs(ax + ay), abs(bx + by)
    major_x, major_y, minor_x, minor_y = sign(ax), sign(ay), sign(bx), sign(by)
    if height == 1:
        for step in range(width):
            yield x + major_x * step, y + major_y * step
        return
    if width == 1:
        for step in range(height):
            yield x + minor_x * step, y + minor_y * step
        return
    half_ax, half_ay, half_bx, half_by = ax // 2, ay // 2, bx // 2, by // 2
    if 2 * width > 3 * height:
        # Two halves along the major axis; an odd half would leave the path ending on the wrong side.
        if abs(half_ax + half_ay) % 2 and width > 2:
            half_ax, half_ay = half_ax + major_x, half_ay + major_y
        yield from curve(x, y, half_ax, half_ay, bx, by)
        yield from curve(x + half_ax, y + half_ay, ax - half_ax, ay - half_ay, bx, by)
        return
    if abs(half_bx + half_by) % 2 and height > 2:
        half_bx, half_by = half_bx + minor_x, half_by + minor_y
    yield from curve(x, y, half_bx, half_by, half_ax, half_ay)
    yield from curve(x + half_bx, y + half_by, ax, ay, bx - half_bx, by - half_by)
    yield from curve(
        x + (ax - major_x) + (half_bx - minor_x),
        y + (ay - major_y) + (half_by - minor_y),
        -half_bx,
        -half_by,
        -(ax - half_ax),
        -(ay - half_ay),
    )


def apples(blocks: int) -> tuple[int, ...]:
    """Where along the curve the apples lie: a few, at random, the same every time, clear of both ends."""
    if blocks < 10:
        return ()
    count = min(max(blocks // 150, 3), 12)
    return tuple(sorted(random.Random(315).sample(range(blocks // 10, blocks * 9 // 10), count)))


def length_at(head: int, eaten_at: tuple[int, ...]) -> int:
    """How many blocks long the snake is with its head at `head`: longer by `GROWTH` for each apple behind it."""
    return LENGTH + GROWTH * sum(1 for apple in eaten_at if apple < head)


def snake(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The snake's frames. The eased progress moves its head along the curve and on past the end by its full length,
    so the tail leaves too; a cell shows the arriving slide once the head has passed its block.
    """
    width, height = dimensions(leaving)
    path = generalized_hilbert(-(-width // BLOCK), height)
    if direction is Direction.PREVIOUS:
        path = path[::-1]
    step_of = [[0] * width for _ in range(height)]
    for step, (block_x, y) in enumerate(path):
        for x in range(block_x * BLOCK, min(block_x * BLOCK + BLOCK, width)):
            step_of[y][x] = step
    food = apples(len(path))
    travel = len(path) + length_at(len(path), food)

    def frame(t: float) -> Grid:
        eased = easing(t)
        head = int(eased * travel)
        cells: list[list[StyledGrapheme | None]] = [
            [new if step < head else old for old, new, step in zip(before, after, steps, strict=True)]
            for before, after, steps in zip(leaving, arriving, step_of, strict=True)
        ]
        if eased <= 0:
            return tuple(tuple(row) for row in cells)
        for apple in food:
            if apple < head:
                continue
            block_x, y = path[apple]
            under = leaving[y][block_x * BLOCK]
            if under is not None:
                cells[y][block_x * BLOCK] = StyledGrapheme(
                    grapheme="●", style=under.style | CellStyle(foreground=APPLE)
                )
        tail = max(head - length_at(head, food), 0)
        for step in range(tail, min(head, len(path))):
            block_x, y = path[step]
            glyph = HEAD if step == head - 1 else BODY
            for x in range(block_x * BLOCK, min(block_x * BLOCK + BLOCK, width)):
                cells[y][x] = glyph
        return tuple(tuple(row) for row in cells)

    return frame
