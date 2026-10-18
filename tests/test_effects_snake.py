"""The snake effect: its space-filling curve, what the snake has eaten, and how apples grow it."""

from itertools import pairwise

import pytest
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Grid
from whats_new.components.effects.snake import BLOCK
from whats_new.components.effects.snake import BODY
from whats_new.components.effects.snake import GROWTH
from whats_new.components.effects.snake import HEAD
from whats_new.components.effects.snake import LENGTH
from whats_new.components.effects.snake import generalized_hilbert
from whats_new.components.effects.snake import length_at
from whats_new.components.effects.snake import snake
from whats_new.components.swipe import Direction

OLD = StyledGrapheme(grapheme="o", style=CellStyle(foreground=Color.from_name("red")))
NEW = StyledGrapheme(grapheme="n", style=CellStyle(foreground=Color.from_name("green")))


def filled(glyph: StyledGrapheme, width: int, height: int) -> Grid:
    return tuple(tuple(glyph for _ in range(width)) for _ in range(height))


@pytest.mark.parametrize(("width", "height"), [(1, 1), (1, 7), (9, 1), (8, 8), (13, 5), (5, 13), (50, 28), (17, 11)])
def test_the_curve_visits_every_cell_once_each_a_step_from_the_last(width: int, height: int) -> None:
    path = generalized_hilbert(width, height)
    steps = [max(abs(x - before_x), abs(y - before_y)) for (before_x, before_y), (x, y) in pairwise(path)]

    assert sorted(path) == sorted((x, y) for x in range(width) for y in range(height))
    assert all(step == 1 for step in steps)


def test_cells_behind_the_tail_show_the_arriving_slide_and_cells_ahead_of_the_head_the_leaving_one() -> None:
    width, height = 16, 8
    frame = snake(filled(OLD, width, height), filled(NEW, width, height), Direction.NEXT)(0.2)
    path = generalized_hilbert(width // BLOCK, height)
    shown = [frame[y][block_x * BLOCK] for block_x, y in path]
    head = max(index for index, glyph in enumerate(shown) if glyph == HEAD)

    assert set(shown[: head - LENGTH]) == {NEW}
    assert set(shown[head - LENGTH + 1 : head]) == {BODY}
    assert {glyph for glyph in shown[head + 1 :] if glyph is None or glyph.grapheme != "●"} == {OLD}


def test_moving_back_starts_the_snake_from_the_other_end_of_the_curve() -> None:
    width, height = 16, 8
    path = generalized_hilbert(width // BLOCK, height)
    frame = snake(filled(OLD, width, height), filled(NEW, width, height), Direction.PREVIOUS)(0.2)

    first_x, first_y = path[0]
    last_x, last_y = path[-1]
    assert (frame[first_y][first_x * BLOCK], frame[last_y][last_x * BLOCK]) == (OLD, NEW)


@pytest.mark.parametrize(("head", "expected"), [(5, LENGTH), (21, LENGTH + GROWTH), (95, LENGTH + 2 * GROWTH)])
def test_each_apple_behind_the_head_makes_the_snake_longer(head: int, expected: int) -> None:
    assert length_at(head, (20, 40)) == expected
