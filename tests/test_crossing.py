"""
The transitions F6 offers that are drawn from pictures: each effect's frames on small pictures, the morph's flights,
the arriving slide's picture against what the live slide draws, and a crossing played in the deck.
"""

import random
from collections.abc import Callable
from collections.abc import Sequence
from datetime import timedelta

import pytest
from counterweight.app import app
from counterweight.components import Component
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import StyledGrapheme
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.focus import FocusHandle
from counterweight.geometry import Region
from counterweight.keys import Key
from counterweight.output import Frame
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.checkpoint import Checkpoint
from whats_new.components.crossing import Grid
from whats_new.components.crossing import photograph
from whats_new.components.crossing import picture_of
from whats_new.components.crossing import rows_of
from whats_new.components.effects.characters import beyond
from whats_new.components.effects.masks import Thresholds
from whats_new.components.effects.masks import across
from whats_new.components.effects.masks import circular
from whats_new.components.effects.masks import scattered
from whats_new.components.effects.masks import slatted
from whats_new.components.effects.masks import wipe
from whats_new.components.effects.morph import Flight
from whats_new.components.effects.morph import flights
from whats_new.components.swipe import Direction
from whats_new.components.transitions import OFF
from whats_new.components.transitions import RANDOM
from whats_new.components.transitions import TRANSITIONS
from whats_new.components.transitions import Choose
from whats_new.components.transitions import Crossed
from whats_new.components.transitions import Transition
from whats_new.components.transitions import transition_for
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.presenter import slide_view
from whats_new.size import PRESENTING

FOOTER_ROWS = 2
STAGE = Region(left=0, top=0, right=PRESENTING.columns, bottom=PRESENTING.rows - FOOTER_ROWS)

BLACK, WHITE = Color.from_name("black"), Color.from_name("white")
RED = CellStyle(foreground=Color.from_name("red"), background=BLACK)
BLUE = CellStyle(foreground=Color.from_name("blue"), background=WHITE, bold=True)


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


LEAVING = grid("abc de😭", "  fgh   ", "ab    ab", style=RED)
ARRIVING = grid("  edcba ", "😭 xyz  ", "zz   ba ", style=BLUE)
CROSSINGS = {name: transition for name, transition in TRANSITIONS.items() if isinstance(transition, Crossed)}


@pytest.mark.parametrize("direction", Direction)
@pytest.mark.parametrize("transition", CROSSINGS.values(), ids=CROSSINGS.keys())
def test_a_crossing_starts_on_the_leaving_picture(transition: Crossed, direction: Direction) -> None:
    frames = transition.effect(LEAVING, ARRIVING, direction)

    assert frames(0.0) == LEAVING


@pytest.mark.parametrize("direction", Direction)
@pytest.mark.parametrize("transition", CROSSINGS.values(), ids=CROSSINGS.keys())
def test_a_crossing_ends_on_the_arriving_picture(transition: Crossed, direction: Direction) -> None:
    frames = transition.effect(LEAVING, ARRIVING, direction)

    assert frames(1.0) == ARRIVING


@pytest.mark.parametrize("direction", Direction)
@pytest.mark.parametrize("thresholds", [scattered, across, circular, slatted])
def test_every_cell_uncovers_partway_through(
    thresholds: Callable[[int, int, Direction], Thresholds], direction: Direction
) -> None:
    every = [at for row in thresholds(37, 11, direction) for at in row]

    assert (len(every), min(every) >= 0.0, max(every) < 1.0) == (37 * 11, True, True)


@pytest.mark.parametrize(
    ("direction", "expected"),
    [(Direction.NEXT, ("abc cba ", "  fgyz  ")), (Direction.PREVIOUS, ("  edde  ", "😭 xh   "))],
    ids=["next, from the right", "previous, from the left"],
)
def test_a_wipe_halfway_shows_the_arriving_slide_on_the_side_it_comes_from(
    direction: Direction, expected: tuple[str, ...]
) -> None:
    leaving, arriving = grid("abc de  ", "  fgh   ", style=RED), grid("  edcba ", "😭 xyz  ", style=BLUE)

    halfway = wipe(leaving, arriving, direction)(0.5)

    assert tuple("".join(glyph.grapheme for glyph in row) for row in rows_of(halfway)) == expected


def test_a_split_wide_grapheme_draws_as_a_space() -> None:
    (wide, continuation), other = grid("😭", style=BLUE)[0], StyledGrapheme(grapheme="x", style=RED)

    assert rows_of(((wide, other), (other, continuation))) == (
        (StyledGrapheme(grapheme=" ", style=BLUE), other),
        (other, StyledGrapheme(grapheme=" ")),
    )


def test_a_character_on_both_slides_flies_from_one_place_to_the_other() -> None:
    paths = flights(grid("q   ", style=RED), grid("   q", style=RED), Direction.NEXT, BLACK)

    assert [(path.start, path.end) for path in paths] == [((0, 0), (3, 0))]


def test_a_character_only_the_leaving_slide_has_flies_off_beyond_the_edges() -> None:
    (path,) = flights(
        grid("    ", " q  ", "    ", style=RED), grid("    ", "    ", "    ", style=RED), Direction.NEXT, BLACK
    )
    x, y = path.end

    assert (path.start, x < 0 or x >= 4 or y < 0 or y >= 3) == ((1, 1), True)


@pytest.mark.parametrize("point", [(0.0, 0.0), (99.0, 27.0), (50.0, 14.0), (3.0, 20.0)])
def test_beyond_is_off_the_stage(point: tuple[float, float]) -> None:
    x, y = beyond(point, 100, 28, Direction.NEXT)

    assert x < 0 or x >= 100 or y < 0 or y >= 28


def test_a_flight_changes_from_the_leaving_character_to_the_arriving_one_halfway() -> None:
    old, new = StyledGrapheme(grapheme="q", style=RED), StyledGrapheme(grapheme="q", style=BLUE)
    flight = Flight(start=(0, 0), end=(10, 4), leaving=old, arriving=new, delay=0.0)

    assert (flight.at(0.3), flight.at(0.4)) == ((3, 1, old), (7, 3, new))


ARRIVED_FOR = timedelta(milliseconds=1700)
"""How long a slide has been mounted when it's compared with its picture: partway through a title card's turn."""


async def test_the_arriving_slide_draws_its_picture(host: Host) -> None:
    """
    Every slide, mounted for as long as a crossing plays over it, draws the picture the crossing ends on,
    colors included, or the canvas would jump as it goes.
    """
    frames: list[Frame] = []
    await app(
        # Without a transition, so each screenshot is of the live slide.
        root_at(host, 0),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            *(
                step
                for _ in SLIDES
                for step in (AdvanceClock(by=ARRIVED_FOR), Screenshot(handler=frames.append), KeyPressed(key=Key.Right))
            ),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )

    pictures = [
        await photograph(
            slide_view(slide, 0, True, host, Checkpoint(slide=0).code_theme, FocusHandle()),
            STAGE.width,
            STAGE.height,
            after=ARRIVED_FOR,
        )
        for slide in SLIDES
    ]
    mismatched = [
        slide.title
        for slide, frame, picture in zip(SLIDES, frames, pictures, strict=True)
        if picture_of(frame.paint, STAGE) != picture
    ]
    assert mismatched == []


def root_at(host: Host, index: int, transition: str = "off", choose: Choose = random.choice) -> Component:
    return root(
        SLIDES,
        host,
        Checkpoint(slide=index, transition=transition),
        lambda checkpoint: None,
        choose=choose,
    )


EDITED = next(index for index, slide in enumerate(SLIDES) if slide.title == "frozendict: the mutable default, fixed")
DISSOLVE = CROSSINGS["dissolve"].duration


async def dissolving(
    host: Host, steps: Sequence[AnyEvent | AnyControl], transition: str = "dissolve", choose: Choose = random.choice
) -> None:
    await app(
        root_at(host, EDITED, transition, choose),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(*steps, Quit()),
        clock=EXPORT_CLOCK,
    )


def slide_rows(frame: Frame) -> list[str]:
    return frame.text(ansi=False).splitlines()[:-FOOTER_ROWS]


async def test_halfway_through_a_dissolve_each_cell_shows_one_slide_or_the_other(host: Host) -> None:
    before: list[Frame] = []
    starting: list[Frame] = []
    halfway: list[Frame] = []
    after: list[Frame] = []
    await dissolving(
        host,
        (
            # An edit, which shows as it starts only if the leaving picture is of the screen as it was left.
            KeyPressed(key=Key.Tab),
            KeyPressed(key="Q"),
            KeyPressed(key=Key.Tab),
            Screenshot(handler=before.append),
            KeyPressed(key=Key.Left),
            Screenshot(handler=starting.append),
            AdvanceClock(by=DISSOLVE / 2),
            Screenshot(handler=halfway.append),
            AdvanceClock(by=DISSOLVE),
            Screenshot(handler=after.append),
        ),
    )

    left, mixed, arrived = picture_of(before[0].paint, STAGE), picture_of(halfway[0].paint, STAGE), after[0].paint
    shows_either = [
        cell in (old, new)
        for old_row, mixed_row, new_row in zip(left, mixed, picture_of(arrived, STAGE), strict=True)
        for old, cell, new in zip(old_row, mixed_row, new_row, strict=True)
    ]
    assert slide_rows(starting[0]) == slide_rows(before[0])
    assert all(shows_either)
    assert mixed not in (left, picture_of(arrived, STAGE))


async def test_the_arriving_slide_takes_the_keys_while_a_dissolve_plays(host: Host) -> None:
    frames: list[Frame] = []
    await dissolving(
        host,
        (
            KeyPressed(key=Key.Right),
            KeyPressed(key=Key.Left),
            AdvanceClock(by=DISSOLVE / 3),
            # Reaches the arriving slide's editor only if focus moved to it as the dissolve began.
            KeyPressed(key=Key.Tab),
            KeyPressed(key="Q"),
            AdvanceClock(by=DISSOLVE),
            Screenshot(handler=frames.append),
        ),
    )

    assert 'print(f"{DEFAULTS=}")Q' in frames[0].text(ansi=False)


def test_random_plays_whichever_transition_it_chooses_from_all_of_them() -> None:
    offered: list[tuple[Transition, ...]] = []

    def choose(options: tuple[Transition, ...]) -> Transition:
        offered.append(options)
        return TRANSITIONS["iris"]

    assert (transition_for(RANDOM, choose), offered) == (TRANSITIONS["iris"], [tuple(TRANSITIONS.values())])


@pytest.mark.parametrize(("name", "expected"), [("wipe", TRANSITIONS["wipe"]), (OFF, None)])
def test_a_named_transition_plays_itself_without_choosing(name: str, expected: Transition | None) -> None:
    def choose(options: tuple[Transition, ...]) -> Transition:
        raise AssertionError("only random chooses")

    assert transition_for(name, choose) is expected


async def test_random_chooses_afresh_for_every_move(host: Host) -> None:
    chosen = iter((CROSSINGS["dissolve"], CROSSINGS["wipe"]))
    picks: list[Transition] = []

    def choose(options: tuple[Transition, ...]) -> Transition:
        picks.append(next(chosen))
        return picks[-1]

    at_random: list[Frame] = []
    dissolved: list[Frame] = []
    halfway = (KeyPressed(key=Key.Left), AdvanceClock(by=DISSOLVE / 2))
    await dissolving(
        host,
        (*halfway, Screenshot(handler=at_random.append), AdvanceClock(by=DISSOLVE), KeyPressed(key=Key.Right)),
        transition=RANDOM,
        choose=choose,
    )
    await dissolving(host, (*halfway, Screenshot(handler=dissolved.append)))

    assert picks == [CROSSINGS["dissolve"], CROSSINGS["wipe"]]
    assert slide_rows(at_random[0]) == slide_rows(dissolved[0])


async def arrive(host: Host, transition: str, steps: Sequence[AnyEvent | AnyControl]) -> list[Frame]:
    """What moving on from `EDITED` with `transition` picked draws, a screenshot after each of `steps`."""
    frames: list[Frame] = []
    await app(
        root_at(host, EDITED, transition),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            KeyPressed(key=Key.Right),
            *(step for each in steps for step in (each, Screenshot(handler=frames.append))),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )
    return frames


@pytest.mark.parametrize("name", CROSSINGS.keys())
async def test_every_crossing_plays_in_the_deck_and_lands_on_the_slide_as_without_a_transition(
    host: Host, name: str
) -> None:
    halfway, ended = await arrive(
        host, name, (AdvanceClock(by=CROSSINGS[name].duration / 2), AdvanceClock(by=CROSSINGS[name].duration))
    )
    (instant,) = await arrive(host, OFF, (AdvanceClock(by=CROSSINGS[name].duration),))

    assert slide_rows(ended) == slide_rows(instant)
    assert slide_rows(halfway) != slide_rows(instant)
