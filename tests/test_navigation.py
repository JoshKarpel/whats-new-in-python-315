import pytest
from counterweight.keys import Key

from whats_new.presenter import InGrid
from whats_new.presenter import InSectionList
from whats_new.presenter import Position
from whats_new.presenter import navigate
from whats_new.slides import Slide
from whats_new.slides import sections


def blank(props: object) -> object:
    raise AssertionError("navigation never draws a slide")


SLIDES = tuple(Slide(title=f"slide {n}", content=blank, steps=steps) for n, steps in enumerate((1, 3, 1, 2, 1, 1, 1)))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("position", "key", "expected"),
    [
        (Position(index=2, step=0), Key.Right, Position(index=3)),
        (Position(index=6), Key.Right, Position(index=6)),
        (Position(index=2), Key.Left, Position(index=1)),
        (Position(index=0), Key.Left, Position(index=0)),
        (Position(index=1, step=1), Key.Space, Position(index=1, step=2)),
        (Position(index=1, step=2), Key.Space, Position(index=1, step=2)),
        (Position(index=1, step=2, generation=4), "r", Position(index=1, step=0, generation=5)),
        (Position(index=4, step=0), "d", Position(index=4, browsing=InGrid(4))),
        (Position(index=4, browsing=InGrid(4)), Key.Down, Position(index=4, browsing=InGrid(6))),
        (Position(index=4, browsing=InGrid(1)), Key.Up, Position(index=4, browsing=InGrid(0))),
        (Position(index=4, browsing=InGrid(5)), Key.Right, Position(index=4, browsing=InGrid(6))),
        (Position(index=4, browsing=InGrid(5)), Key.Enter, Position(index=5)),
        (Position(index=4, step=1, browsing=InGrid(5)), Key.Escape, Position(index=4, step=1)),
        (Position(index=4, browsing=InGrid(5)), "d", Position(index=5)),
    ],
)
def test_navigate_moves_the_presenter(position: Position, key: str, expected: Position) -> None:
    assert navigate(position, key, SLIDES) == expected


@pytest.mark.parametrize(
    "position", [Position(index=3), Position(index=3, browsing=InGrid(2)), Position(index=3, browsing=InSectionList(0))]
)
def test_navigate_leaves_unused_keys_to_the_slide(position: Position) -> None:
    assert navigate(position, "1", SLIDES) is None


def title_card(n: int) -> Slide:
    return Slide(title=f"section {n}", content=blank, is_title_card=True)  # type: ignore[arg-type]


def plain(n: int) -> Slide:
    return Slide(title=f"slide {n}", content=blank)  # type: ignore[arg-type]


# Sections of 5 (two rows), 2 (one row) and 4 (two rows) slides.
SECTIONED = (title_card(0), *map(plain, range(1, 5)), title_card(5), plain(6), title_card(7), *map(plain, range(8, 11)))


def test_sections_split_at_title_cards() -> None:
    assert sections(SECTIONED) == (range(5), range(5, 7), range(7, 11))


def test_sections_start_at_the_first_slide_without_a_title_card() -> None:
    assert sections((plain(0), title_card(1), plain(2))) == (range(1), range(1, 3))


@pytest.mark.parametrize(
    ("position", "key", "expected"),
    [
        (Position(index=2, step=0), Key.PageDown, Position(index=5)),
        (Position(index=5), Key.PageDown, Position(index=7)),
        (Position(index=8), Key.PageDown, Position(index=10)),
        (Position(index=6, step=1), Key.PageUp, Position(index=5)),
        (Position(index=5), Key.PageUp, Position(index=0)),
        (Position(index=0), Key.PageUp, Position(index=0)),
        (Position(index=0, browsing=InGrid(3)), Key.PageDown, Position(index=0, browsing=InGrid(5))),
        (Position(index=0, browsing=InGrid(7)), Key.PageUp, Position(index=0, browsing=InGrid(5))),
    ],
    ids=[
        "down to the next section's first slide",
        "down from a section's first slide",
        "down from the last section to the last slide",
        "up to the first slide of its own section",
        "up from a section's first slide to the previous section's",
        "up at the first slide",
        "the grid's selection down a section",
        "the grid's selection up a section",
    ],
)
def test_page_keys_move_between_sections(position: Position, key: str, expected: Position) -> None:
    assert navigate(position, key, SECTIONED) == expected


@pytest.mark.parametrize(
    ("selected", "key", "expected"),
    [
        (1, Key.Down, 4),
        (2, Key.Down, 4),
        (4, Key.Down, 6),
        (3, Key.Down, 5),
        (6, Key.Down, 8),
        (5, Key.Up, 3),
        (6, Key.Up, 4),
        (8, Key.Up, 6),
        (9, Key.Down, 10),
        (10, Key.Down, 10),
        (2, Key.Up, 0),
        (4, Key.Right, 5),
        (5, Key.Left, 4),
    ],
    ids=[
        "down a row",
        "down to a shorter row",
        "down into the next section",
        "down into a short next section",
        "down past a one-row section",
        "up into the last row of the previous section",
        "up from a one-row section",
        "up into a one-row section",
        "down into the shorter last row of the last section",
        "down at the last slide",
        "up from the first row",
        "right across a section's end",
        "left across a section's start",
    ],
)
def test_grid_moves_through_sections(selected: int, key: str, expected: int) -> None:
    assert navigate(Position(index=0, browsing=InGrid(selected)), key, SECTIONED) == Position(
        index=0, browsing=InGrid(expected)
    )


@pytest.mark.parametrize(
    ("position", "key", "expected"),
    [
        (Position(index=6, step=1), Key.ControlD, Position(index=6, step=1, browsing=InSectionList(1))),
        (Position(index=2, browsing=InGrid(8)), Key.ControlD, Position(index=2, browsing=InSectionList(2))),
        (Position(index=2, browsing=InSectionList(0)), Key.Down, Position(index=2, browsing=InSectionList(1))),
        (Position(index=2, browsing=InSectionList(2)), Key.Down, Position(index=2, browsing=InSectionList(2))),
        (Position(index=2, browsing=InSectionList(2)), Key.Up, Position(index=2, browsing=InSectionList(1))),
        (Position(index=2, browsing=InSectionList(0)), Key.Up, Position(index=2, browsing=InSectionList(0))),
        (
            Position(index=2, step=1, browsing=InSectionList(2)),
            Key.Enter,
            Position(index=2, step=1, browsing=InGrid(7)),
        ),
        (Position(index=6, step=1, browsing=InSectionList(2)), Key.Escape, Position(index=6, step=1)),
        (Position(index=6, step=1, browsing=InSectionList(2)), Key.ControlD, Position(index=6, step=1)),
    ],
    ids=[
        "opens on the slide's section",
        "opens on the grid's selection's section",
        "down a section",
        "down at the last section",
        "up a section",
        "up at the first section",
        "Enter opens the grid on the section's title card",
        "Escape goes back to the slide",
        "Ctrl+D goes back to the slide",
    ],
)
def test_sections_list(position: Position, key: str, expected: Position) -> None:
    assert navigate(position, key, SECTIONED) == expected
