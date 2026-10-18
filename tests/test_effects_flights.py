"""
The effects that move characters about one by one, each on what sets it apart: gravity's falls and landings,
the sort's rows in order, the vortex's spirals, and the swap's hops and decays.
Every effect's first and last frames are checked for all of them together, in `test_crossing`.
"""

import random
from itertools import pairwise
from math import hypot

import pytest
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Grid
from whats_new.components.crossing import rows_of
from whats_new.components.easing import bounce
from whats_new.components.easing import linear
from whats_new.components.effects.characters import drawn_over
from whats_new.components.effects.characters import emptied
from whats_new.components.effects.characters import moves
from whats_new.components.effects.gravity import Drop
from whats_new.components.effects.gravity import Landing
from whats_new.components.effects.gravity import drops
from whats_new.components.effects.gravity import gravity
from whats_new.components.effects.gravity import landings
from whats_new.components.effects.sort import sort
from whats_new.components.effects.sort import sorted_row
from whats_new.components.effects.sort import sorting
from whats_new.components.effects.sort import unsorting
from whats_new.components.effects.swap import Decay
from whats_new.components.effects.swap import Hop
from whats_new.components.effects.swap import nearest_pairs
from whats_new.components.effects.swap import shaded
from whats_new.components.effects.swap import swap
from whats_new.components.effects.vortex import SPIRAL
from whats_new.components.effects.vortex import Spiral
from whats_new.components.effects.vortex import spirals
from whats_new.components.swipe import Direction

RED = CellStyle(foreground=Color.from_name("red"), background=Color.from_name("black"))
BLUE = CellStyle(foreground=Color.from_name("blue"), background=Color.from_name("white"), bold=True)

Q = StyledGrapheme(grapheme="q", style=RED)


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


def text(picture: Grid) -> tuple[str, ...]:
    """What `picture` shows, row by row, without its styles."""
    return tuple("".join(glyph.grapheme for glyph in row) for row in rows_of(picture))


def test_a_falling_character_drops_farther_each_moment() -> None:
    drop = Drop(x=3, y=2, glyph=Q, release=0.1, pull=100.0)

    rows = [drop.at(t)[1] for t in (0.1, 0.2, 0.3, 0.4)]

    assert [later - earlier for earlier, later in pairwise(rows)] == [1, 3, 5]


def test_a_falling_character_keeps_its_column() -> None:
    drop = Drop(x=3, y=2, glyph=Q, release=0.1, pull=40.0)

    assert {drop.at(t)[0] for t in (0.0, 0.3, 0.6)} == {3}


def test_the_lowest_row_of_the_leaving_slide_lets_go_first() -> None:
    falls = drops(grid("q  ", "   ", " q ", style=RED), 3, random.Random(7), RED.background)

    assert min(falls, key=lambda drop: drop.release).y == 2


def test_the_lowest_row_of_the_arriving_slide_lands_first() -> None:
    falls = landings(grid("q  ", "   ", " q ", style=BLUE), 3, random.Random(7), BLUE.background)

    assert min(falls, key=lambda landing: landing.land).y == 2


def test_an_arriving_character_is_above_its_row_partway_through_its_fall() -> None:
    landing = Landing(x=4, y=9, glyph=Q, start=0.2, land=0.8)

    assert landing.at(0.5, linear)[1] < 9


def test_a_bouncing_curve_bounces_a_landing_character_back_up_off_its_row() -> None:
    landing = Landing(x=4, y=10, glyph=Q, start=0.0, land=1.0)

    touching, bounced = landing.at(0.45, bounce)[1], landing.at(0.6, bounce)[1]

    assert (touching, bounced < touching) == (10, True)


@pytest.mark.parametrize(
    ("direction", "expected"),
    [(Direction.NEXT, ("   abc",)), (Direction.PREVIOUS, ("cba   ",))],
    ids=["next, packed right", "previous, packed left"],
)
def test_just_before_halfway_each_leaving_row_is_sorted(direction: Direction, expected: tuple[str, ...]) -> None:
    frames = sort(grid("b a c ", style=RED), grid("      ", style=BLUE), direction, linear)

    assert text(frames(0.4999)) == expected


def test_at_halfway_each_arriving_row_is_sorted() -> None:
    frames = sort(grid("      ", style=RED), grid("z y x ", style=BLUE), Direction.NEXT, linear)

    assert text(frames(0.5)) == ("   xyz",)


def test_the_smallest_character_of_a_row_sorts_first() -> None:
    slides = sorting(grid("cab", style=RED), Direction.NEXT, RED.background)

    assert [slide.glyph.grapheme for slide in sorted(slides, key=lambda slide: slide.begin)] == ["a", "b", "c"]


def test_the_largest_character_of_a_row_unsorts_first() -> None:
    slides = unsorting(grid("cab", style=BLUE), Direction.NEXT, BLUE.background)

    assert [slide.glyph.grapheme for slide in sorted(slides, key=lambda slide: slide.begin)] == ["c", "b", "a"]


def test_a_two_cell_wide_character_takes_two_cells_of_a_sorted_row() -> None:
    row = grid("b😭a ", style=RED)[0]

    assert [(x, to) for x, to, _ in sorted_row(row, Direction.NEXT, RED.background)] == [(3, 1), (0, 2), (1, 3)]


def spiral(direction: Direction) -> Spiral:
    """The one character of a stage 41 by 11, on its middle row 18 columns right of center, spiralling in."""
    stage = grid(*[" " * 41] * 5, " " * 38 + "q  ", *[" " * 41] * 5, style=RED)
    (only,) = spirals(stage, direction, is_inward=True, start=0.0, seed=5, backdrop=RED.background)
    return only


def shown_at(path: Spiral, t: float) -> tuple[int, int]:
    """Which cell `path`'s character is in `t` of the way through the transition, which it must be showing at."""
    place = path.at(t, linear)
    if place is None:
        raise AssertionError(f"the character isn't showing at {t}")
    return place[0], place[1]


def test_a_spiralling_character_gets_closer_to_the_center() -> None:
    inward = spiral(Direction.NEXT)
    x, y = shown_at(inward, inward.begin + SPIRAL / 2)

    assert hypot(x + 0.5 - inward.center[0], (y + 0.5 - inward.center[1]) * CELL_ASPECT) < inward.radius * 0.75


@pytest.mark.parametrize(
    ("direction", "expected"),
    [(Direction.NEXT, 9), (Direction.PREVIOUS, 1)],
    ids=["next, clockwise, so down from the right", "previous, anticlockwise, so up from the right"],
)
def test_a_spiral_turns_clockwise_moving_forward(direction: Direction, expected: int) -> None:
    inward = spiral(direction)

    assert shown_at(inward, inward.begin + SPIRAL / 2)[1] == expected


def test_a_leaving_character_is_gone_once_it_reaches_the_center() -> None:
    inward = spiral(Direction.NEXT)

    assert inward.at(inward.begin + SPIRAL, linear) is None


def test_an_arriving_character_starts_out_from_the_center() -> None:
    outward = Spiral(center=(20.5, 5.5), radius=18.0, angle=0.0, glyph=Q, begin=0.5, twist=-1.6, is_inward=False)

    assert shown_at(outward, 0.5001) == (20, 5)


def test_the_closest_pair_of_characters_is_matched_first() -> None:
    assert nearest_pairs([(0, 0), (10, 0)], [(9, 0), (1, 0)]) == [(0, 1), (1, 0)]


def test_characters_too_far_apart_are_not_matched() -> None:
    assert nearest_pairs([(0, 0)], [(60, 0)]) == []


def test_a_character_in_the_same_place_on_both_slides_stays_put() -> None:
    frames = swap(grid("q   ", "  ab", style=RED), grid("q   ", "x   ", style=BLUE), Direction.NEXT, linear)

    assert {text(frames(step / 20))[0][0] for step in range(21)} == {"q"}


def test_a_hop_arcs_above_its_row() -> None:
    hop = Hop(start=(2, 5), end=(18, 5), leaving=Q, arriving=Q, begin=0.0, lift=2.0)

    assert hop.at(0.2, linear)[1] < 5


@pytest.mark.parametrize(
    ("is_leaving", "expected"),
    [(True, ["q", "▓", "▒", "░", None]), (False, [None, "░", "▒", "▓", "q"])],
    ids=["leaving decays", "arriving condenses"],
)
def test_a_character_only_one_slide_has_changes_through_the_shades(
    is_leaving: bool, expected: list[str | None]
) -> None:
    decay = Decay(x=1, y=2, glyph=Q, shades=shaded(Q), begin=0.1, is_leaving=is_leaving)

    shown = [None if (place := decay.at(t)) is None else place[2].grapheme for t in (0.11, 0.17, 0.22, 0.27, 0.31)]

    assert shown == expected


BACKDROP = RED.background
SHADE = CellStyle(foreground=Color.from_name("red"), background=Color.from_name("navy"))
"""A code box's shading: on a background other than the backdrop."""


@pytest.mark.parametrize(
    ("glyph", "expected"),
    [
        (StyledGrapheme(grapheme="q", style=RED), True),
        (StyledGrapheme(grapheme=" ", style=SHADE), True),
        (StyledGrapheme(grapheme=" ", style=RED), False),
    ],
    ids=["a character", "a shaded space", "a space on the backdrop"],
)
def test_what_moves_is_a_character_or_a_shaded_cell(glyph: StyledGrapheme, expected: bool) -> None:
    assert moves(glyph, BACKDROP) is expected


def test_emptied_leaves_the_backdrop_where_shading_was() -> None:
    picture = (tuple(StyledGrapheme(grapheme=" ", style=style) for style in (SHADE, RED)),)

    assert emptied(picture, BACKDROP) == (
        (StyledGrapheme(grapheme=" ", style=CellStyle(background=BACKDROP)), picture[0][1]),
    )


def test_a_shaded_cell_keeps_its_own_color_where_it_lands() -> None:
    shading = StyledGrapheme(grapheme=" ", style=SHADE)
    behind = ((StyledGrapheme(grapheme=" ", style=CellStyle(background=BACKDROP)),),)

    assert drawn_over(behind, [(0, 0, shading)], BACKDROP) == ((shading,),)


def test_a_character_on_the_backdrop_takes_the_color_of_the_shading_it_crosses() -> None:
    behind = ((StyledGrapheme(grapheme=" ", style=CellStyle(background=BACKDROP)),),)
    shading, letter = StyledGrapheme(grapheme=" ", style=SHADE), StyledGrapheme(grapheme="q", style=RED)

    ((drawn,),) = drawn_over(behind, [(0, 0, shading), (0, 0, letter)], BACKDROP)

    assert drawn == StyledGrapheme(grapheme="q", style=RED | CellStyle(background=SHADE.background))


def test_gravity_drops_a_code_boxs_shading_with_its_text() -> None:
    boxed = (
        tuple(StyledGrapheme(grapheme=character, style=SHADE) for character in " q  "),
        *grid("    ", "    ", "    ", "    ", "    ", style=RED),
    )
    blank = grid(*["    "] * 6, style=RED)

    falling = gravity(boxed, blank, Direction.NEXT, linear)(0.25)

    assert all(cell is not None and cell.style.background == BACKDROP for cell in falling[0])
    assert any(cell is not None and cell.style.background == SHADE.background for row in falling[1:] for cell in row)
