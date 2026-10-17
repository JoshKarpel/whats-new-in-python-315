"""
F3's slide transitions: the easing curves, where the two slides sit, which moves swipe,
and the swipe itself, drawn on the export's frozen clock and stopped halfway.
"""

from collections.abc import Sequence

import pytest
from counterweight.app import app
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.components.easing import EASINGS
from whats_new.components.easing import Easing
from whats_new.components.swipe import SWIPE
from whats_new.components.swipe import Direction
from whats_new.components.swipe import offsets
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import Position
from whats_new.presenter import root
from whats_new.presenter import swipe_direction
from whats_new.size import PRESENTING

SAMPLES = [step / 100 for step in range(101)]
FOOTER_ROWS = 2
"""The footer's rule and its line, which stay put while the slides above them swipe."""
HALF = PRESENTING.columns // 2


@pytest.mark.parametrize("easing", EASINGS.values(), ids=EASINGS.keys())
def test_easing_starts_at_rest_and_ends_in_place(easing: Easing) -> None:
    assert (easing(0.0), easing(1.0)) == pytest.approx((0.0, 1.0))


@pytest.mark.parametrize(
    ("name", "goes_past"),
    [
        ("linear", False),
        ("ease-out", False),
        ("ease-in-out", False),
        ("overshoot", True),
        ("spring", True),
        ("bounce", False),
    ],
)
def test_only_overshoot_and_spring_go_past_the_end(name: str, goes_past: bool) -> None:
    assert (max(EASINGS[name](t) for t in SAMPLES) > 1.0 + 1e-9) is goes_past


def test_every_curve_is_offered() -> None:
    assert set(EASINGS) == {"linear", "ease-out", "ease-in-out", "overshoot", "spring", "bounce"}


@pytest.mark.parametrize(
    ("direction", "eased", "expected"),
    [
        (Direction.NEXT, 0.0, (0, 90)),
        (Direction.NEXT, 0.5, (-45, 45)),
        (Direction.NEXT, 1.0, (-90, 0)),
        (Direction.NEXT, 1.2, (-108, -18)),
        (Direction.PREVIOUS, 0.0, (0, -90)),
        (Direction.PREVIOUS, 0.5, (45, -45)),
        (Direction.PREVIOUS, 1.0, (90, 0)),
    ],
    ids=[
        "next, start",
        "next, half",
        "next, end",
        "next, past the end",
        "previous, start",
        "previous, half",
        "previous, end",
    ],
)
def test_offsets_place_the_slides_a_width_apart(direction: Direction, eased: float, expected: tuple[int, int]) -> None:
    assert offsets(direction, eased, 90) == expected


LAST = len(SLIDES) - 1


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (Position(index=3), Position(index=4), Direction.NEXT),
        (Position(index=3), Position(index=2), Direction.PREVIOUS),
        (Position(index=3), Position(index=8), Direction.NEXT),
        (Position(index=3, step=0), Position(index=3, step=1), None),
        (Position(index=3), Position(index=3, generation=1), None),
        (Position(index=3), Position(index=3, selected=3), None),
        (Position(index=3, selected=7), Position(index=7), None),
    ],
    ids=["next", "previous", "a section on", "a reveal step", "r", "opening the grid", "jumping from the grid"],
)
def test_swipe_direction(before: Position, after: Position, expected: Direction | None) -> None:
    assert swipe_direction(before, after) is expected


def slide_rows(frame: Frame) -> list[str]:
    return frame.text(ansi=False).splitlines()[:-FOOTER_ROWS]


async def drive(host: Host, index: int, steps: Sequence[AnyEvent | AnyControl]) -> None:
    """Starts the deck on slide `index` with the linear transition picked, then drives it through `steps`."""
    await app(
        root(SLIDES, host, Checkpoint(slide=index, transition="linear"), lambda checkpoint: None),
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
