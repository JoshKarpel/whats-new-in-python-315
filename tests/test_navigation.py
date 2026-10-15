import pytest
from counterweight.keys import Key

from whats_new.presenter import Position
from whats_new.presenter import navigate
from whats_new.slides import Slide


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
        (Position(index=4, step=0), "d", Position(index=4, selected=4)),
        (Position(index=4, selected=4), Key.Down, Position(index=4, selected=6)),
        (Position(index=4, selected=1), Key.Up, Position(index=4, selected=0)),
        (Position(index=4, selected=5), Key.Right, Position(index=4, selected=6)),
        (Position(index=4, selected=5), Key.Enter, Position(index=5)),
        (Position(index=4, step=1, selected=5), Key.Escape, Position(index=4, step=1)),
        (Position(index=4, selected=5), "d", Position(index=4)),
    ],
)
def test_navigate_moves_the_presenter(position: Position, key: str, expected: Position) -> None:
    assert navigate(position, key, SLIDES) == expected


@pytest.mark.parametrize("position", [Position(index=3), Position(index=3, selected=2)])
def test_navigate_leaves_unused_keys_to_the_slide(position: Position) -> None:
    assert navigate(position, "1", SLIDES) is None
