"""
The effects that move a slide about as a solid thing (`curl`, `cube`, `shatter` and `melt`), each on small pictures:
what makes each one look the way it does, partway through. Where they start and end is tested for every effect
in `test_crossing`.
"""

import re
from math import pi

import pytest
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Grid
from whats_new.components.effects.cube import Face
from whats_new.components.effects.cube import cube
from whats_new.components.effects.curl import curl
from whats_new.components.effects.melt import drips
from whats_new.components.effects.melt import melt
from whats_new.components.effects.shading import BLACK
from whats_new.components.effects.shading import SHADES
from whats_new.components.effects.shading import shaded
from whats_new.components.effects.shatter import CRACKING
from whats_new.components.effects.shatter import shards
from whats_new.components.effects.shatter import shatter
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


def filled(character: str, width: int, height: int, style: CellStyle) -> Grid:
    """A `width` by `height` picture of nothing but `character`."""
    return grid(*(character * width for _ in range(height)), style=style)


def at(frame: Grid, x: int, y: int) -> StyledGrapheme:
    """The glyph in cell `x`, `y` of `frame`, which mustn't be a continuation."""
    glyph = frame[y][x]
    if glyph is None:
        raise ValueError(f"cell {x}, {y} is a continuation")
    return glyph


def text(row: tuple[StyledGrapheme | None, ...]) -> str:
    """The graphemes along `row`, a continuation cell as nothing."""
    return "".join(glyph.grapheme for glyph in row if glyph is not None)


def brightness(color: object) -> int:
    """How bright an RGB color is, all its channels together."""
    if not isinstance(color, Color):
        raise TypeError(f"expected an RGB color, not {color!r}")
    return color.red + color.green + color.blue


LETTERS = grid("abcdefghijklmnopqrst", style=RED)
CAPITALS = grid("ABCDEFGHIJKLMNOPQRST", style=BLUE)


@pytest.mark.parametrize(
    ("direction", "peeled", "flat"),
    [(Direction.NEXT, (19, 5), (0, 0)), (Direction.PREVIOUS, (0, 5), (19, 0))],
    ids=["next, from the bottom right", "previous, from the bottom left"],
)
def test_a_curl_peels_from_the_bottom_corner_the_arriving_slide_comes_from(
    direction: Direction, peeled: tuple[int, int], flat: tuple[int, int]
) -> None:
    frame = curl(filled("L", 20, 6, RED), filled("A", 20, 6, BLUE), direction)(0.3)

    assert (at(frame, *peeled).grapheme, at(frame, *flat).grapheme) == ("A", "L")


@pytest.mark.parametrize(
    ("direction", "expected"),
    [(Direction.NEXT, "abcdefghijtsrqpPQRST"), (Direction.PREVIOUS, "ABCDEedcbaklmnopqrst")],
    ids=["next", "previous"],
)
def test_the_back_of_a_curling_page_shows_the_peeled_cells_mirrored_across_the_fold(
    direction: Direction, expected: str
) -> None:
    (row,) = curl(LETTERS, CAPITALS, direction)(0.37)

    assert text(row) == expected


def test_the_back_of_a_curling_page_is_paler_than_its_front() -> None:
    frame = curl(LETTERS, CAPITALS, Direction.NEXT)(0.37)
    back = at(frame, text(frame[0]).index("t"), 0)

    assert brightness(back.style.background) > brightness(RED.background)


def test_a_curling_page_casts_a_shadow_on_the_arriving_slide_beside_the_fold() -> None:
    frame = curl(LETTERS, CAPITALS, Direction.NEXT)(0.37)
    beside = at(frame, text(frame[0]).index("P"), 0)

    assert brightness(beside.style.background) < brightness(BLUE.background)


@pytest.mark.parametrize(("level", "expected"), [(0, Color(200, 120, 40)), (SHADES // 2, Color(100, 60, 20))])
def test_shading_blends_a_glyphs_colors_toward_another(level: int, expected: Color) -> None:
    glyph = StyledGrapheme(grapheme="q", style=CellStyle(foreground=Color(200, 120, 40)))

    assert shaded(glyph, BLACK, level) == StyledGrapheme(grapheme="q", style=CellStyle(foreground=expected))


@pytest.mark.parametrize(
    ("direction", "expected"), [(Direction.NEXT, "L" * 10 + "A" * 10), (Direction.PREVIOUS, "A" * 10 + "L" * 10)]
)
def test_halfway_round_a_cube_the_shared_edge_is_in_the_middle(direction: Direction, expected: str) -> None:
    frame = cube(filled("L", 20, 7, RED), filled("A", 20, 7, BLUE), direction)(0.5)

    assert text(frame[3]) == expected


def test_a_cube_face_darkens_as_it_turns_away() -> None:
    frame = cube(filled("L", 20, 7, RED), filled("A", 20, 7, BLUE), Direction.NEXT)(0.42)

    assert brightness(at(frame, 0, 3).style.foreground) < brightness(RED.foreground)


def test_a_cube_faces_far_side_is_drawn_shorter_than_its_near_side() -> None:
    frame = cube(filled("L", 20, 7, RED), filled("A", 20, 7, BLUE), Direction.NEXT)(0.5)

    assert (frame[0][0], at(frame, 9, 0).grapheme) == (SPACE, "L")


@pytest.mark.parametrize(("angle", "expected"), [(0.0, True), (pi / 3, True), (pi / 2 - 0.05, False), (pi, False)])
def test_a_cube_face_is_drawn_only_while_the_viewer_is_in_front_of_it(angle: float, expected: bool) -> None:
    assert Face(angle=angle).is_facing is expected


PANE = grid(*(f"{row:x}" * 30 for row in range(9)), style=RED)


def test_every_cell_of_the_leaving_slide_is_in_exactly_one_shard() -> None:
    cells = [(x, y) for shard in shards(PANE, Direction.NEXT) for x, y, _, _ in shard.cells]

    assert sorted(cells) == sorted((x, y) for y in range(9) for x in range(30))


def test_a_two_cell_wide_grapheme_stays_whole_in_one_shard() -> None:
    pictures = grid(*("ab" + "😭" * 14 for _ in range(9)), style=RED)
    owner = {
        (x, y): index for index, shard in enumerate(shards(pictures, Direction.NEXT)) for x, y, _, _ in shard.cells
    }

    assert all(owner[(x, y)] == owner[(x + 1, y)] for y in range(9) for x in range(2, 30, 2))


@pytest.mark.parametrize("direction", Direction)
def test_every_shard_lands_off_the_stage(direction: Direction) -> None:
    pieces = shards(PANE, direction)

    assert all(shard.bounds.is_off(*shard.offset(1.0), 30, 9) for shard in pieces)


def test_shards_nearer_the_middle_set_off_first() -> None:
    pieces = shards(grid(*("x" * 100 for _ in range(28)), style=RED), Direction.NEXT)
    middle = next(shard for shard in pieces if any((x, y) == (50, 14) for x, y, _, _ in shard.cells))
    corner = next(shard for shard in pieces if any((x, y) == (0, 0) for x, y, _, _ in shard.cells))

    assert middle.delay < corner.delay


def test_cracks_show_along_shard_edges_before_the_shards_move() -> None:
    frame = shatter(PANE, filled("A", 30, 9, BLUE), Direction.NEXT)(CRACKING)
    edges = {(x, y) for shard in shards(PANE, Direction.NEXT) for x, y, _, is_edge in shard.cells if is_edge}
    changed = {(x, y) for y, row in enumerate(frame) for x, glyph in enumerate(row) if glyph != PANE[y][x]}

    assert changed == edges != set()


COLUMN = grid(*(f"{row}" * 40 for row in range(10)), style=RED)


def columns_of(frame: Grid) -> list[str]:
    """Each column of `frame`, top to bottom."""
    return ["".join(at(frame, x, y).grapheme for y in range(len(frame))) for x in range(len(frame[0]))]


def test_a_melting_column_shows_the_arriving_slide_above_the_leaving_one() -> None:
    frame = melt(COLUMN, filled("A", 40, 10, BLUE), Direction.NEXT)(0.6)

    assert all(re.fullmatch("A*[0-9]*", column) for column in columns_of(frame))


def is_smeared(column: str) -> bool:
    """Whether `column` is the leaving column's first rows, in order, at least one of them drawn out over several."""
    rows = "".join(dict.fromkeys(column))
    return column == "".join(sorted(column)) and rows == "0123456789"[: len(rows)] and len(rows) < len(column)


def test_a_melting_column_smears_its_cells_down_in_order() -> None:
    frame = melt(COLUMN, filled("A", 40, 10, BLUE), Direction.NEXT)(0.6)
    sagging = [column.lstrip("A") for column in columns_of(frame) if 3 < len(column.lstrip("A")) < 10]

    assert (len(sagging) > 0, [column for column in sagging if not is_smeared(column)]) == (True, [])


@pytest.mark.parametrize(
    ("direction", "first", "last"),
    [(Direction.NEXT, slice(67, 100), slice(0, 33)), (Direction.PREVIOUS, slice(0, 33), slice(67, 100))],
)
def test_a_melt_starts_sooner_on_the_side_the_arriving_slide_comes_from(
    direction: Direction, first: slice, last: slice
) -> None:
    starts = [drip.start for drip in drips(100, direction)]

    assert sum(starts[first]) < sum(starts[last])
