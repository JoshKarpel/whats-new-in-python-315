"""
The effects that work cell by cell, each on what sets it apart: the rain's columns and settling characters,
decay's shades and ripple, and the departure board's locking columns.
Every effect's first and last frames are checked for all of them together, in `test_crossing`.
"""

import random
import re
from statistics import mean

import pytest
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Effect
from whats_new.components.crossing import Grid
from whats_new.components.easing import linear
from whats_new.components.effects.decay import DUST_COLOR
from whats_new.components.effects.decay import decay
from whats_new.components.effects.decay import rippling
from whats_new.components.effects.rain import drops
from whats_new.components.effects.rain import rain
from whats_new.components.effects.slots import BLANK_FACE
from whats_new.components.effects.slots import slots
from whats_new.components.effects.slots import spinning_faces
from whats_new.components.swipe import Direction

RED = CellStyle(foreground=Color.from_name("red"), background=Color.from_name("black"))
BLUE = CellStyle(foreground=Color.from_name("blue"), background=Color.from_name("white"), bold=True)


def grid(*rows: str, style: CellStyle) -> Grid:
    """A picture of `rows`, each grapheme in `style`, with the `None` after each two-cell-wide one."""
    return tuple(
        tuple(
            cell
            for character in row
            for cell in (
                (StyledGrapheme(grapheme=character, style=style), None)
                if StyledGrapheme(grapheme=character).width == 2
                else (StyledGrapheme(grapheme=character, style=style),)
            )
        )
        for row in rows
    )


def every_frame(leaving: Grid, arriving: Grid, effect: Effect, direction: Direction = Direction.NEXT) -> list[Grid]:
    """`effect`'s frames from `leaving` to `arriving`, at a thousandth of the way apart, on a linear curve."""
    frames = effect(leaving, arriving, direction, linear)
    return [frames(step / 1000) for step in range(1001)]


def kinds(row: tuple[StyledGrapheme | None, ...], leaving: Grid, arriving: Grid, y: int) -> str:
    """Each cell of row `y` of a frame as `L` if it's the leaving picture's, `A` the arriving one's, or `-` neither."""
    return "".join(
        "A" if glyph == arriving[y][x] else "L" if glyph == leaving[y][x] else "-" for x, glyph in enumerate(row)
    )


@pytest.mark.parametrize("effect", [rain, decay, slots])
def test_the_same_progress_always_draws_the_same_frame(effect: Effect) -> None:
    leaving = grid("abc de😭", "  fgh   ", "ab    ab", style=RED)
    arriving = grid("  edcba ", "😭 xyz  ", "zz   ba ", style=BLUE)
    first, second = effect(leaving, arriving, Direction.NEXT, linear), effect(leaving, arriving, Direction.NEXT, linear)

    drawn = [first(t) for t in (0.61, 0.37, 0.52)]

    assert [second(t) for t in (0.61, 0.37, 0.52)] == drawn


def test_rain_leaves_the_arriving_slide_above_each_drop_and_the_leaving_one_below() -> None:
    leaving, arriving = grid(*"q" * 30, style=RED), grid(*"z" * 30, style=BLUE)

    columns = [
        "".join(kinds(row, leaving, arriving, y) for y, row in enumerate(frame))
        for frame in every_frame(leaving, arriving, rain)
    ]

    assert [column for column in columns if not re.fullmatch("A*-*L*", column)] == []


def test_rain_tints_an_arriving_character_as_it_comes_through_the_trail() -> None:
    leaving, arriving = grid(*"q" * 30, style=RED), grid(*"z" * 30, style=BLUE)

    tints = {
        glyph.style.foreground
        for frame in every_frame(leaving, arriving, rain)
        for (glyph,) in frame
        if glyph is not None and glyph.grapheme == "z"
    }

    assert len(tints - {BLUE.foreground}) > 1


@pytest.mark.parametrize(
    ("direction", "near", "far"),
    [(Direction.NEXT, slice(80, 100), slice(0, 20)), (Direction.PREVIOUS, slice(0, 20), slice(80, 100))],
    ids=["next, from the right", "previous, from the left"],
)
def test_rain_tends_to_start_on_the_side_the_arriving_slide_comes_from(
    direction: Direction, near: slice, far: slice
) -> None:
    columns = drops(100, direction, random.Random(27))

    assert mean(drop.delay for drop in columns[near]) < mean(drop.delay for drop in columns[far])


def test_a_decaying_cell_steps_down_the_shades_to_dust_and_back_up() -> None:
    leaving, arriving = grid("q", style=RED), grid("z", style=BLUE)

    shown = [frame[0][0].grapheme for frame in every_frame(leaving, arriving, decay) if frame[0][0] is not None]

    assert [grapheme for index, grapheme in enumerate(shown) if index == 0 or shown[index - 1] != grapheme] == list(
        "q▓▒░·░▒▓z"
    )


@pytest.mark.parametrize(
    ("leaving", "ink"),
    [(grid("q", style=RED), Color.from_name("red")), (grid(" ", style=RED), DUST_COLOR)],
    ids=["a character, in its own color", "an empty cell, in dust"],
)
def test_a_cell_decays_in_its_own_color(leaving: Grid, ink: Color) -> None:
    frames = decay(leaving, grid("z", style=BLUE), Direction.NEXT, linear)

    assert frames(0.02) == (
        (StyledGrapheme(grapheme="▓", style=CellStyle(foreground=ink, background=Color.from_name("black"))),),
    )


def test_neighboring_cells_decay_at_nearly_the_same_time() -> None:
    turns = rippling(100, 28, Direction.NEXT)
    chance = random.Random(46)

    neighbors = mean(abs(row[x] - row[x + 1]) for row in turns for x in range(99))
    strangers = mean(
        abs(chance.choice(chance.choice(turns)) - chance.choice(chance.choice(turns))) for _ in range(2800)
    )

    assert neighbors < strangers / 5


@pytest.mark.parametrize(
    ("direction", "first", "last"),
    [(Direction.NEXT, slice(90, 100), slice(0, 10)), (Direction.PREVIOUS, slice(0, 10), slice(90, 100))],
    ids=["next, from the right", "previous, from the left"],
)
def test_decay_ripples_from_the_side_the_arriving_slide_comes_from(
    direction: Direction, first: slice, last: slice
) -> None:
    turns = rippling(100, 28, direction)

    assert mean(turn for row in turns for turn in row[first]) < mean(turn for row in turns for turn in row[last])


@pytest.mark.parametrize(
    ("direction", "pattern"),
    [(Direction.NEXT, "A*-*L*"), (Direction.PREVIOUS, "L*-*A*")],
    ids=["next, left to right", "previous, right to left"],
)
def test_the_departure_board_locks_column_after_column(direction: Direction, pattern: str) -> None:
    leaving, arriving = grid("qqqqqqqqqqqq", style=RED), grid("zzzzzzzzzzzz", style=BLUE)

    rows = [kinds(frame[0], leaving, arriving, 0) for frame in every_frame(leaving, arriving, slots, direction)]

    assert [row for row in rows if not re.fullmatch(pattern, row)] == []


def test_a_cell_the_same_on_both_slides_never_spins() -> None:
    leaving = grid("qmq", style=RED)
    arriving = ((*grid("z", style=BLUE)[0], leaving[0][1], *grid("z", style=BLUE)[0]),)

    assert {frame[0][1] for frame in every_frame(leaving, arriving, slots)} == {leaving[0][1]}


def test_a_spinning_cell_changes_face_as_it_spins() -> None:
    frames = slots(grid("q", style=RED), grid("z", style=BLUE), Direction.NEXT, linear)

    assert len({frames(t) for t in (0.1, 0.15, 0.2, 0.25)}) == 4


@pytest.mark.parametrize(
    ("before", "after", "ink"),
    [
        (StyledGrapheme(grapheme="q", style=RED), StyledGrapheme(grapheme="z", style=BLUE), BLUE.foreground),
        (StyledGrapheme(grapheme="q", style=RED), StyledGrapheme(grapheme=" ", style=BLUE), RED.foreground),
        (StyledGrapheme(grapheme=" ", style=RED), StyledGrapheme(grapheme=" ", style=BLUE), BLANK_FACE),
    ],
    ids=["toward a character", "away from one, to an empty cell", "empty on both"],
)
def test_a_cell_spins_in_the_color_of_the_character_it_turns_to_or_from(
    before: StyledGrapheme, after: StyledGrapheme, ink: object
) -> None:
    assert {face.style.foreground for face in spinning_faces(before, after)} == {ink}
