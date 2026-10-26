"""
F6's swipe: where the two slides sit, which moves swipe,
and the swipe itself, drawn on the export's frozen clock and stopped halfway; and the grid shrinking open.
"""

import random
from collections.abc import Sequence

import pytest
from counterweight import app
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.paint import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.components.grid import Toward
from whats_new.components.grid import Zoom
from whats_new.components.grid import shares
from whats_new.components.swipe import SWIPE
from whats_new.components.swipe import Direction
from whats_new.components.swipe import offsets
from whats_new.components.transitions import GRID_TRANSITIONS
from whats_new.components.transitions import OFF
from whats_new.components.transitions import RANDOM
from whats_new.components.transitions import ChooseGrid
from whats_new.components.transitions import GridTransition
from whats_new.components.transitions import grid_transition_for
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import InGrid
from whats_new.presenter import InSectionList
from whats_new.presenter import Position
from whats_new.presenter import root
from whats_new.presenter import swipe_direction
from whats_new.presenter import zoom_toward
from whats_new.size import PRESENTING

FOOTER_ROWS = 2
"""The footer's rule and its line, which stay put while the slides above them swipe."""
HALF = PRESENTING.columns // 2


@pytest.mark.parametrize(
    ("direction", "progress", "expected"),
    [
        (Direction.NEXT, 0.0, (0, 90)),
        (Direction.NEXT, 0.5, (-45, 45)),
        (Direction.NEXT, 1.0, (-90, 0)),
        (Direction.PREVIOUS, 0.0, (0, -90)),
        (Direction.PREVIOUS, 0.5, (45, -45)),
        (Direction.PREVIOUS, 1.0, (90, 0)),
    ],
    ids=[
        "next, start",
        "next, half",
        "next, end",
        "previous, start",
        "previous, half",
        "previous, end",
    ],
)
def test_offsets_place_the_slides_a_width_apart(
    direction: Direction, progress: float, expected: tuple[int, int]
) -> None:
    assert offsets(direction, progress, 90) == expected


LAST = len(SLIDES) - 1


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (Position(index=3), Position(index=4), Direction.NEXT),
        (Position(index=3), Position(index=2), Direction.PREVIOUS),
        (Position(index=3), Position(index=8), Direction.NEXT),
        (Position(index=3, step=0), Position(index=3, step=1), None),
        (Position(index=3), Position(index=3, generation=1), None),
        (Position(index=3), Position(index=3, browsing=InGrid(3)), None),
        (Position(index=3, browsing=InGrid(7)), Position(index=7), None),
        (Position(index=3), Position(index=3, browsing=InSectionList(1)), None),
        (Position(index=3, browsing=InSectionList(1)), Position(index=3), None),
    ],
    ids=[
        "next",
        "previous",
        "a section on",
        "a reveal step",
        "r",
        "opening the grid",
        "jumping from the grid",
        "opening the sections list",
        "closing the sections list",
    ],
)
def test_swipe_direction(before: Position, after: Position, expected: Direction | None) -> None:
    assert swipe_direction(before, after) is expected


def slide_rows(frame: Frame) -> list[str]:
    return frame.text(ansi=False).splitlines()[:-FOOTER_ROWS]


async def drive(
    host: Host,
    index: int,
    steps: Sequence[AnyEvent | AnyControl],
    grid_transition: str = "zoom",
    speed: str = "1x",
    choose_grid: ChooseGrid = random.choice,
) -> None:
    """
    Starts the deck on slide `index` swiping at `speed`, the grid on `grid_transition`, `random` picking the grid's
    with `choose_grid`, then drives it through `steps`.
    """
    await app(
        root(
            SLIDES,
            host,
            Checkpoint(slide=index, transition="swipe", speed=speed, grid_transition=grid_transition),
            lambda checkpoint: None,
            choose_grid=choose_grid,
        ),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(*steps, Quit()),
        clock=EXPORT_CLOCK,
    )


EDITED = next(index for index, slide in enumerate(SLIDES) if slide.title == "frozendict: the mutable default, fixed")


async def test_halfway_through_a_swipe_each_slide_shows_half_of_itself(host: Host) -> None:
    before: list[Frame] = []
    halfway: list[Frame] = []
    after: list[Frame] = []
    await drive(
        host,
        EDITED,
        (
            # An edit, which only shows halfway if the slide being left kept its state rather than remounting.
            KeyPressed(key=Key.Tab),
            KeyPressed(key="Q"),
            KeyPressed(key=Key.Tab),
            Screenshot(handler=before.append),
            KeyPressed(key=Key.Left),
            AdvanceClock(by=SWIPE / 2),
            Screenshot(handler=halfway.append),
            AdvanceClock(by=SWIPE),
            Screenshot(handler=after.append),
        ),
    )

    # Going back, the slide being left travels right, so its left half shows on the right, and the arriving
    # slide's right half on the left.
    expected = [
        arriving[HALF:] + leaving[:HALF]
        for leaving, arriving in zip(slide_rows(before[0]), slide_rows(after[0]), strict=True)
    ]
    assert 'print(f"{DEFAULTS=}")Q' in before[0].text(ansi=False)
    assert slide_rows(halfway[0]) == expected


async def test_returning_mid_swipe_mounts_the_slide_afresh(host: Host) -> None:
    before: list[Frame] = []
    after: list[Frame] = []
    await drive(
        host,
        EDITED,
        (
            # Arriving here by a move first, so the slide is on a mounting navigation made, as it will be again.
            KeyPressed(key=Key.Right),
            AdvanceClock(by=SWIPE),
            KeyPressed(key=Key.Left),
            AdvanceClock(by=SWIPE),
            Screenshot(handler=before.append),
            KeyPressed(key=Key.Tab),
            KeyPressed(key="Q"),
            KeyPressed(key=Key.Tab),
            KeyPressed(key=Key.Right),
            AdvanceClock(by=SWIPE / 3),
            # The edited slide is still leaving as it's returned to: it has to mount afresh, not continue that copy.
            KeyPressed(key=Key.Left),
            AdvanceClock(by=SWIPE),
            Screenshot(handler=after.append),
        ),
    )

    assert slide_rows(after[0]) == slide_rows(before[0])


async def test_the_arriving_slide_takes_the_keys_while_the_swipe_plays(host: Host) -> None:
    frames: list[Frame] = []
    await drive(
        host,
        EDITED - 1,
        (
            KeyPressed(key=Key.Right),
            AdvanceClock(by=SWIPE / 3),
            # Reaches the arriving slide's editor only if focus moved to it as the swipe began.
            KeyPressed(key=Key.Tab),
            KeyPressed(key="Q"),
            AdvanceClock(by=SWIPE),
            Screenshot(handler=frames.append),
        ),
    )

    assert 'print(f"{DEFAULTS=}")Q' in frames[0].text(ansi=False)


@pytest.mark.parametrize(
    ("selected", "openness", "expected"),
    [
        (1, 0.0, (0.0, 1.0, 0.0)),
        (2, 0.0, (0.0, 0.0, 1.0)),
        (0, 0.5, (2 / 3, 1 / 6, 1 / 6)),
        (2, 1.0, (1 / 3, 1 / 3, 1 / 3)),
    ],
    ids=["closed", "closed, last track", "half open", "open"],
)
def test_shares_shrink_the_selected_track_into_place(
    selected: int, openness: float, expected: tuple[float, ...]
) -> None:
    assert shares(selected, 3, openness) == pytest.approx(expected)


@pytest.mark.parametrize(("toward", "expected"), [(Toward.GRID, 0.0625), (Toward.SLIDE, 0.9375)])
def test_zooming_in_runs_the_opening_backwards(toward: Toward, expected: float) -> None:
    assert Zoom(toward=toward, duration=SWIPE).openness(0.25) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (Position(index=3), Position(index=3, browsing=InGrid(3)), Toward.GRID),
        (Position(index=3, browsing=InGrid(7)), Position(index=7), Toward.SLIDE),
        (Position(index=3, browsing=InGrid(7)), Position(index=3), Toward.SLIDE),
        (Position(index=3, browsing=InGrid(3)), Position(index=3, browsing=InGrid(4)), None),
        (Position(index=3), Position(index=4), None),
        (Position(index=3, browsing=InSectionList(2)), Position(index=3, browsing=InGrid(7)), Toward.GRID),
        (Position(index=3, browsing=InGrid(7)), Position(index=3, browsing=InSectionList(2)), None),
        (Position(index=3), Position(index=3, browsing=InSectionList(1)), None),
        (Position(index=3, browsing=InSectionList(1)), Position(index=3), None),
    ],
    ids=[
        "opening the grid",
        "jumping from the grid",
        "Escape",
        "moving the selection",
        "moving on a slide",
        "opening the grid from the sections list",
        "opening the sections list from the grid",
        "opening the sections list",
        "closing the sections list",
    ],
)
def test_zoom_toward(before: Position, after: Position, expected: Toward | None) -> None:
    assert zoom_toward(before, after) is expected


def test_random_picks_one_of_the_grid_transitions() -> None:
    offered: list[tuple[GridTransition, ...]] = []

    def choose(options: tuple[GridTransition, ...]) -> GridTransition:
        offered.append(options)
        return options[-1]

    assert (grid_transition_for(RANDOM, choose), offered) == (
        tuple(GRID_TRANSITIONS.values())[-1],
        [tuple(GRID_TRANSITIONS.values())],
    )


GRID_TOP = 1
"""The grid's first row, under the line naming the section."""
OPEN = (KeyPressed(key="d"), AdvanceClock(by=SWIPE))
JUMP = (*OPEN, KeyPressed(key=Key.Right), KeyPressed(key=Key.Enter))
"""Opens the grid from `EDITED`, then jumps to the slide after it."""


async def screens(
    host: Host,
    steps: Sequence[AnyEvent | AnyControl | None],
    grid_transition: str = "zoom",
    choose_grid: ChooseGrid = random.choice,
) -> list[Frame]:
    """What `steps` from `EDITED` draw, a screenshot for each `None` among them."""
    frames: list[Frame] = []
    await drive(
        host,
        EDITED,
        tuple(Screenshot(handler=frames.append) if step is None else step for step in steps),
        grid_transition=grid_transition,
        choose_grid=choose_grid,
    )
    return frames


async def test_opening_the_grid_starts_with_the_selected_thumbnail_filling_it(host: Host) -> None:
    (frame,) = await screens(host, (KeyPressed(key="d"), None))

    rows = slide_rows(frame)
    assert rows[GRID_TOP] == "╭" + "─" * (PRESENTING.columns - 2) + "╮"
    assert rows[GRID_TOP + 1].startswith(f"│{EDITED + 1} | {SLIDES[EDITED].title}")


async def test_f7_picks_the_grid_zoom(host: Host) -> None:
    picked = (KeyPressed(key=Key.F7), *(KeyPressed(key=character) for character in "zoom"), KeyPressed(key=Key.Enter))
    (zoomed,) = await screens(host, (*picked, KeyPressed(key="d"), None), grid_transition=OFF)
    (instant,) = await screens(host, (KeyPressed(key="d"), None), grid_transition=OFF)

    assert slide_rows(zoomed) != slide_rows(instant)
    assert slide_rows(zoomed)[GRID_TOP + 1].startswith(f"│{EDITED + 1} | {SLIDES[EDITED].title}")


async def test_random_plays_the_grid_transition_it_chooses(host: Host) -> None:
    (randomly,) = await screens(
        host, (KeyPressed(key="d"), None), grid_transition=RANDOM, choose_grid=lambda options: GRID_TRANSITIONS["zoom"]
    )
    (zoomed,) = await screens(host, (KeyPressed(key="d"), None))

    assert slide_rows(randomly) == slide_rows(zoomed)


async def test_the_grid_opens_to_where_it_opens_without_the_zoom(host: Host) -> None:
    (zoomed,) = await screens(host, (*OPEN, None))
    (instant,) = await screens(host, (*OPEN, None), grid_transition=OFF)

    assert slide_rows(zoomed) == slide_rows(instant)


async def test_jumping_from_the_grid_zooms_in_from_the_grid_as_it_was(host: Host) -> None:
    before, after = await screens(host, (*JUMP[:-1], None, JUMP[-1], None))

    assert slide_rows(after) == slide_rows(before)


async def test_jumping_from_the_grid_ends_on_the_slide_as_without_the_zoom(host: Host) -> None:
    (zoomed,) = await screens(host, (*JUMP, AdvanceClock(by=SWIPE), None))
    (instant,) = await screens(host, (*JUMP, None), grid_transition=OFF)

    assert slide_rows(zoomed) == slide_rows(instant)


async def test_the_slide_jumped_to_takes_the_keys_while_the_grid_zooms_in(host: Host) -> None:
    frames: list[Frame] = []
    await drive(
        host,
        EDITED - 1,
        (
            *JUMP,
            AdvanceClock(by=SWIPE / 3),
            # Reaches the editor only if the slide mounted, and took focus, beneath the grid as the zoom began.
            KeyPressed(key=Key.Tab),
            KeyPressed(key="Q"),
            AdvanceClock(by=SWIPE),
            Screenshot(handler=frames.append),
        ),
    )

    assert 'print(f"{DEFAULTS=}")Q' in frames[0].text(ansi=False)


async def test_a_swipe_at_twice_the_speed_ends_in_half_the_time(host: Host) -> None:
    at_half: list[Frame] = []
    ended: list[Frame] = []
    await drive(
        host,
        EDITED,
        (
            KeyPressed(key=Key.Right),
            AdvanceClock(by=SWIPE / 2),
            Screenshot(handler=at_half.append),
            AdvanceClock(by=SWIPE),
            Screenshot(handler=ended.append),
        ),
        speed="2x",
    )

    assert slide_rows(at_half[0]) == slide_rows(ended[0])
