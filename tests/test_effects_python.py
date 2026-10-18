"""
The transition effects drawn from the talk's own subjects: the garbage collection, the free
threads racing, and the ripples. Each test pins what makes its effect itself, on small pictures;
that every effect starts and ends on its pictures is `test_crossing`'s.
"""

from math import hypot

import pytest
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import rows_of
from whats_new.components.effects.garbage import COOLING
from whats_new.components.effects.garbage import DUST
from whats_new.components.effects.garbage import LINE
from whats_new.components.effects.garbage import REACHABLE
from whats_new.components.effects.garbage import garbage
from whats_new.components.effects.ripples import landings
from whats_new.components.effects.ripples import ripples
from whats_new.components.effects.ripples import rippling
from whats_new.components.effects.threads import Paint
from whats_new.components.effects.threads import doubled
from whats_new.components.effects.threads import schedule
from whats_new.components.effects.threads import threads
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
    return grid(*(character * width,) * height, style=style)


def text(frame: Grid) -> list[str]:
    """`frame`'s rows as a canvas draws them, characters only."""
    return ["".join(glyph.grapheme for glyph in row) for row in rows_of(frame)]


def first_shown(frames: Frames, x: int, character: str) -> float:
    """How far through `frames` the top row's cell at `x` first shows `character`, to the nearest hundredth."""
    return next(step / 100 for step in range(101) if text(frames(step / 100))[0][x] == character)


def test_the_mark_phase_shows_arriving_characters_in_green_over_the_leaving_slide() -> None:
    frames = garbage(grid("abcd", style=RED), grid(" x  ", style=BLUE), Direction.NEXT)

    (row,) = frames(0.3)

    assert [(glyph.grapheme, glyph.style.foreground) for glyph in row if glyph is not None] == [
        ("a", RED.foreground),
        ("x", REACHABLE),
        ("c", RED.foreground),
        ("d", RED.foreground),
    ]


def test_the_mark_phase_reaches_characters_farther_from_their_root_later() -> None:
    frames = garbage(grid("abcde", style=RED), grid("pqrs ", style=BLUE), Direction.NEXT)

    p, q, r, s = (first_shown(frames, x, character) for x, character in enumerate("pqrs"))

    assert (p < q, q == r, r < s) == (True, True, True)


@pytest.mark.parametrize("direction", Direction)
def test_the_sweep_line_carries_its_label_on_the_middle_row(direction: Direction) -> None:
    frames = garbage(filled("x", 20, 3, RED), filled(" ", 20, 3, BLUE), direction)

    assert "<GC>" in text(frames(0.7))[1]


@pytest.mark.parametrize(("direction", "behind"), [(Direction.NEXT, 1), (Direction.PREVIOUS, -1)])
def test_an_unreachable_character_crumbles_to_dust_just_behind_the_sweep(direction: Direction, behind: int) -> None:
    frames = garbage(filled("x", 20, 3, RED), filled(" ", 20, 3, BLUE), direction)

    top = text(frames(0.7))[0]
    line = top.index(LINE)

    assert (top[line + behind], top[line - behind]) == (DUST[0], "x")


@pytest.mark.parametrize("direction", Direction)
def test_well_behind_the_sweep_the_arriving_slide_shows_as_itself(direction: Direction) -> None:
    arriving = grid("abcdefghijklmnopqrst", "ABCDEFGHIJKLMNOPQRST", style=BLUE)
    frame = garbage(filled("x", 20, 2, RED), arriving, direction)(0.7)
    line = text(frame)[0].index(LINE)
    settled = slice(line + COOLING + 1, None) if direction is Direction.NEXT else slice(None, line - COOLING)

    assert [row[settled] for row in frame] == [row[settled] for row in arriving] != [(), ()]


def test_every_row_is_last_painted_properly() -> None:
    jobs = schedule(grid(*(f"row {y}" for y in range(20)), style=BLUE))

    last = {job.row: job.paint for job in sorted(jobs, key=lambda job: job.start)}

    assert last == dict.fromkeys(range(20), Paint.ARRIVING)


def test_the_queue_hands_a_row_out_twice() -> None:
    jobs = schedule(grid(*(f"row {y}" for y in range(20)), style=BLUE))

    assert any(job.paint is Paint.DOUBLED for job in jobs)


def test_doubling_a_row_repeats_each_glyph_from_its_first_character() -> None:
    assert text((doubled(grid("  ab cd", style=RED)[0]),)) == ["  aabb "]


def test_a_duplicated_row_shows_doubled_until_it_is_painted_again() -> None:
    arriving = grid(*(f"row {y} of twenty" for y in range(20)), style=BLUE)
    jobs = schedule(arriving)
    duplicate = next(job for job in jobs if job.paint is Paint.DOUBLED)
    on_row = [job for job in jobs if job.row == duplicate.row]
    fix = max(on_row, key=lambda job: job.start)
    settled = max(job.end for job in on_row if job is not fix)
    frames = threads(filled("-", 16, 20, RED), arriving, Direction.NEXT)

    shown = text(frames((settled + fix.start) / 2))[duplicate.row]

    assert shown == text((doubled(arriving[duplicate.row]),))[0]


def test_every_thread_shows_its_tag_while_it_paints() -> None:
    frames = threads(filled("-", 30, 20, RED), filled("=", 30, 20, BLUE), Direction.NEXT)

    shown = "".join(text(frames(0.05)))

    assert [f"T{thread}" in shown for thread in range(1, 5)] == [True] * 4


def test_a_ripple_pushes_characters_out_of_place_behind_the_front() -> None:
    columns = "".join(str(x % 10) for x in range(60))
    frames = rippling(filled(" ", 60, 15, RED), grid(*(columns,) * 15, style=BLUE), ((45.0, 7.5),))

    pushed = [
        (x, y)
        for y, row in enumerate(text(frames(0.4)))
        for x, shown in enumerate(row)
        if shown not in (" ", columns[x])
    ]

    assert pushed != []


def test_ripples_open_separate_circles_with_the_leaving_slide_between_them() -> None:
    drops = landings(100, 28)
    frame = text(ripples(filled("a", 100, 28, RED), filled("b", 100, 28, BLUE), Direction.NEXT)(0.1))

    at_drops = {frame[int(y)][int(x)] for x, y in drops}
    between = {frame[int((y + v) / 2)][int((x + u) / 2)] for x, y in drops for u, v in drops if (x, y) != (u, v)}

    assert (len(drops) >= 3, at_drops, between) == (True, {"b"}, {"a"})


def test_ripples_land_apart() -> None:
    drops = landings(100, 28)

    closest = min(hypot(x - u, (y - v) * CELL_ASPECT) for x, y in drops for u, v in drops if (x, y) != (u, v))

    assert closest > 10
