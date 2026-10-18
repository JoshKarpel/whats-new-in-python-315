"""
The text effects' own behavior, on small pictures: the typewriter's keystrokes and cursor,
the crash's squash and report, and the lazy import's regions and proxy labels.
Every effect's first and last frames are checked for all effects together, in `test_crossing`.
"""

import random

import pytest
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Grid
from whats_new.components.crossing import rows_of
from whats_new.components.effects.crash import crash
from whats_new.components.effects.crash import glitched
from whats_new.components.effects.crash import squashed
from whats_new.components.effects.lazy_import import label_of
from whats_new.components.effects.lazy_import import labelled
from whats_new.components.effects.lazy_import import lazy_import
from whats_new.components.effects.lazy_import import regions
from whats_new.components.effects.typewriter import stops_of
from whats_new.components.effects.typewriter import typewriter
from whats_new.components.swipe import Direction

RED = CellStyle(foreground=Color.from_name("red"), background=Color.from_name("black"))
BLUE = CellStyle(foreground=Color.from_name("blue"), background=Color.from_name("white"), bold=True)
GOLD = CellStyle(foreground=Color.from_hex("#ffd43b"), background=Color.from_name("black"))


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
    """What `picture` reads as, row by row, as a canvas draws it."""
    return tuple("".join(glyph.grapheme for glyph in row) for row in rows_of(picture))


def test_a_row_is_typed_a_character_per_keystroke_skipping_blanks_and_never_splitting_a_wide_grapheme() -> None:
    (row,) = grid("  ab 😭 c", style=RED)

    assert stops_of(row) == (2, 3, 4, 7, 9)


def test_partway_through_typing_a_row_the_cursor_is_just_past_the_typed_part() -> None:
    frames = typewriter(grid("    ", style=RED), grid("wxyz", style=BLUE), Direction.NEXT)

    # The erasing takes the first 0.35, with nothing to erase, and the typing the rest: 0.6 of it is 2.4 keystrokes.
    assert text(frames(0.35 + 0.65 * 0.6)) == ("wx█ ",)


def test_backspacing_starts_on_the_bottom_row() -> None:
    frames = typewriter(grid("abcd", "efgh", style=RED), grid("    ", "    ", style=BLUE), Direction.NEXT)

    # The erasing is the first 0.35 of the transition. The bottom row erases over its first 0.6, so 0.24 into it
    # is 1.6 keystrokes, and the top row starts 0.4 into it.
    assert text(frames(0.35 * 0.24)) == ("abcd", "ef█ ")


GLITCHABLE = grid("abcdefghij" * 4, "klmnopqrst" * 4, "uvwxyzabcd" * 4, style=RED)


def test_partway_through_glitching_the_leaving_picture_is_glitched() -> None:
    frames = crash(GLITCHABLE, GLITCHABLE, Direction.NEXT)

    assert frames(0.3) != GLITCHABLE


def test_a_glitched_frame_is_the_same_every_time_its_drawn() -> None:
    first, again = (crash(GLITCHABLE, GLITCHABLE, Direction.NEXT) for _ in range(2))

    assert first(0.3) == again(0.3)


def test_no_glitch_at_all_leaves_the_picture_as_it_is() -> None:
    assert glitched(GLITCHABLE, 0.0, random.Random(9)) is GLITCHABLE


def test_a_squashed_picture_draws_its_rows_closer_together_in_the_middle() -> None:
    picture = grid("aa", "bb", "cc", "dd", style=RED)

    # 0.4 of its full height: the squash is down to a line with 0.3 of it still to go.
    assert text(squashed(picture, 0.3 + 0.7 * 0.4)) == ("  ", "aa", "dd", "  ")


def test_a_squashed_picture_ends_as_a_shrinking_line_across_the_middle() -> None:
    picture = grid("abcdefgh", "ijklmnop", "qrstuvwx", "yzabcdef", style=RED)

    assert text(squashed(picture, 0.15)) == ("        ", "        ", "  ━━━━  ", "        ")


def test_the_crash_report_prints_on_the_dark_screen() -> None:
    picture = grid(" " * 60, " " * 60, " " * 60, style=RED)

    frames = crash(picture, picture, Direction.NEXT)

    assert text(frames(0.7))[1].strip() == "Fatal Python error: Segmentation fault"


def test_words_a_single_blank_apart_are_one_region_and_two_blanks_apart_two() -> None:
    found = regions(grid("ab cd  ef", style=RED))

    assert sorted(sorted(region.cells) for region in found) == [
        [(0, 0), (1, 0), (3, 0), (4, 0)],
        [(7, 0), (8, 0)],
    ]


def test_a_heading_straight_over_a_box_in_other_colors_is_a_region_of_its_own() -> None:
    picture = grid("Title  ", style=GOLD) + grid("┏━━━━━┓", "┗━━━━━┛", style=RED)

    assert len(regions(picture)) == 2


@pytest.mark.parametrize(
    ("words", "expected"),
    [("the Tachyon", "tachyon"), ("x = profiling.sampling", "profiling.sampling"), ("1 3.15", None)],
    ids=["skips short words", "keeps dotted names", "no word long enough"],
)
def test_a_region_is_named_after_its_first_word_fit_to_be_a_module_name(words: str, expected: str | None) -> None:
    (region,) = regions(grid(words, style=RED))

    assert region.name == expected


@pytest.mark.parametrize(
    ("name", "room", "expected"),
    [
        ("defaults", 30, "<lazy_import 'defaults'>"),
        ("profiling.sampling", 26, "<lazy_import 'profiling.'>"),
        ("tachyon", 19, None),
    ],
    ids=["fits", "cut short", "no room"],
)
def test_a_proxys_label_fits_its_name_into_the_room_it_has(name: str, room: int, expected: str | None) -> None:
    assert label_of(name, room) == expected


def test_a_label_inside_a_box_moves_left_to_stay_inside_it() -> None:
    picture = grid("┃         Tachyon       ┃", style=RED)
    found = regions(picture)
    owners = {point: region for region in found for point in region.cells}
    (title,) = (region for region in found if region.name == "tachyon")

    assert labelled(title, owners, 25) == (1, "<lazy_import 'tachyon'>")


def test_before_anything_resolves_a_region_shows_its_label_and_placeholders() -> None:
    blank = grid(" " * 24, " " * 24, style=RED)
    arriving = grid("Title of it" + " " * 13, "with more" + " " * 15, style=BLUE)

    frames = lazy_import(blank, arriving, Direction.NEXT)

    assert text(frames(0.32)) == ("<lazy_import 'title'>   ", "░░░░ ░░░░" + " " * 15)
