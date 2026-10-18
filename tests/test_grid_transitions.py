"""
The grid's transitions drawn from pictures (F7): where the thumbnails are in a picture of the grid, each grid effect's
frames on small pictures, and each played in the deck, opening the grid and closing it again.
"""

import random
from collections.abc import Sequence

import pytest
from counterweight.app import app
from counterweight.controls import AdvanceClock
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import StyledGrapheme
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.events import MouseDown
from counterweight.events import MouseUp
from counterweight.geometry import Position as Point
from counterweight.geometry import Region
from counterweight.keys import Key
from counterweight.output import Frame
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.checkpoint import Checkpoint
from whats_new.components.crossing import Grid
from whats_new.components.crossing import Tiles
from whats_new.components.crossing import photograph
from whats_new.components.effects.cards import blank
from whats_new.components.effects.cards import cut
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.deal import SHRUNK
from whats_new.components.effects.deal import deal
from whats_new.components.effects.expose import offstage
from whats_new.components.effects.flip import flip
from whats_new.components.effects.fold import Axis
from whats_new.components.effects.scale import scale
from whats_new.components.effects.slice import bands
from whats_new.components.effects.slice import sliced
from whats_new.components.effects.unpack import PACKED
from whats_new.components.effects.unpack import unpack
from whats_new.components.grid import Toward
from whats_new.components.grid import grid
from whats_new.components.grid import tiles
from whats_new.components.swipe import Direction
from whats_new.components.transitions import GRID_GROUPS
from whats_new.components.transitions import GRID_TRANSITIONS
from whats_new.components.transitions import OFF
from whats_new.components.transitions import Crossed
from whats_new.components.transitions import GridTransition
from whats_new.components.transitions import Group
from whats_new.components.transitions import Tiled
from whats_new.components.transitions import grid_transition_for
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import grid_frames
from whats_new.presenter import root
from whats_new.size import PRESENTING
from whats_new.slides import sections

FOOTER_ROWS = 2
STAGE_WIDTH, STAGE_HEIGHT = PRESENTING.columns, PRESENTING.rows - FOOTER_ROWS

DECK_SECTIONS = sections(SLIDES)
FULL = next(section for section in DECK_SECTIONS if len(section) >= 9)
"""A section with a full window of thumbnails, so the selections below have neighbours on every side."""
MIDDLE = FULL.start + 4
"""The thumbnail in the middle of a full window."""
CORNER = FULL.start
SHORT = next(section for section in DECK_SECTIONS if len(section) < 3).start
"""The first slide of a section with fewer thumbnails than a row holds."""

DRAWN = {name: transition for name, transition in GRID_TRANSITIONS.items() if isinstance(transition, Tiled | Crossed)}


def picture(width: int, height: int, seed: int, style: CellStyle) -> Grid:
    """A `width` by `height` picture of letters chosen at random by `seed`, each in `style`."""
    chance = random.Random(seed)
    return tuple(
        tuple(StyledGrapheme(grapheme=chance.choice("abcdefgh "), style=style) for _ in range(width))
        for _ in range(height)
    )


SMALL_WIDTH, SMALL_HEIGHT = 40, 13
SLIDE = picture(SMALL_WIDTH, SMALL_HEIGHT, 1, CellStyle(foreground=Color.from_name("red")))
OPENED = picture(SMALL_WIDTH, SMALL_HEIGHT, 2, CellStyle(foreground=Color.from_name("blue"), bold=True))


def small_tiles(selected: int) -> Tiles:
    return tiles(SMALL_WIDTH, SMALL_HEIGHT, selected, SLIDES)


def grapheme_at(picture: Grid, x: int, y: int) -> str:
    glyph = picture[y][x]
    return "" if glyph is None else glyph.grapheme


SELECTIONS = {"middle": MIDDLE, "corner": CORNER, "short section": SHORT}


@pytest.mark.parametrize("selected", SELECTIONS.values(), ids=SELECTIONS.keys())
@pytest.mark.parametrize("size", [(STAGE_WIDTH, STAGE_HEIGHT), (STAGE_WIDTH + 1, STAGE_HEIGHT + 1), (80, 24)])
async def test_tiles_are_where_the_grid_draws_its_thumbnails(host: Host, selected: int, size: tuple[int, int]) -> None:
    width, height = size
    drawn = await photograph(grid(SLIDES, selected, lambda index: None, host, "dracula", None), width, height)
    where = tiles(width, height, selected, SLIDES)

    corners = [
        (grapheme_at(drawn, region.left, region.top), grapheme_at(drawn, region.right - 1, region.bottom - 1))
        for region in where.thumbnails
    ]
    assert corners == [("╭", "╯")] * len(where.thumbnails)
    assert grapheme_at(drawn, where.chosen.left + 1, where.chosen.top + 1) == str(selected + 1)[0]


@pytest.mark.parametrize("toward", Toward)
@pytest.mark.parametrize("selected", SELECTIONS.values(), ids=SELECTIONS.keys())
@pytest.mark.parametrize("transition", DRAWN.values(), ids=DRAWN.keys())
def test_a_grid_transition_starts_on_what_the_screen_showed(
    transition: Tiled | Crossed, selected: int, toward: Toward
) -> None:
    frames = grid_frames(transition, SLIDE, OPENED, small_tiles(selected), toward)

    assert frames(0.0) == (OPENED if toward is Toward.SLIDE else SLIDE)


@pytest.mark.parametrize("toward", Toward)
@pytest.mark.parametrize("selected", SELECTIONS.values(), ids=SELECTIONS.keys())
@pytest.mark.parametrize("transition", DRAWN.values(), ids=DRAWN.keys())
def test_a_grid_transition_ends_on_what_the_screen_shows_next(
    transition: Tiled | Crossed, selected: int, toward: Toward
) -> None:
    frames = grid_frames(transition, SLIDE, OPENED, small_tiles(selected), toward)

    assert frames(1.0) == (OPENED if toward is Toward.GRID else SLIDE)


@pytest.mark.parametrize("group", GRID_GROUPS, ids=lambda group: group.title)
def test_a_groups_title_picks_one_of_that_group_at_random(group: Group) -> None:
    offered: list[tuple[GridTransition, ...]] = []

    def choose(options: tuple[GridTransition, ...]) -> GridTransition:
        offered.append(options)
        return options[-1]

    assert (grid_transition_for(group.title, choose), offered) == (
        tuple(group.transitions.values())[-1],
        [tuple(group.transitions.values())],
    )


def test_closing_plays_a_grid_effect_backwards() -> None:
    where = small_tiles(MIDDLE)
    opening = grid_frames(DRAWN["deal"], SLIDE, OPENED, where, Toward.GRID)
    closing = grid_frames(DRAWN["deal"], SLIDE, OPENED, where, Toward.SLIDE)

    assert closing(0.3) == opening(0.7)


@pytest.mark.parametrize(("toward", "direction"), [(Toward.GRID, Direction.NEXT), (Toward.SLIDE, Direction.PREVIOUS)])
def test_an_f6_effect_opens_the_grid_as_moving_on_and_closes_it_as_moving_back(
    toward: Toward, direction: Direction
) -> None:
    transition = GRID_TRANSITIONS["wipe"]
    assert isinstance(transition, Crossed)
    leaving, arriving = (SLIDE, OPENED) if toward is Toward.GRID else (OPENED, SLIDE)

    played = grid_frames(transition, SLIDE, OPENED, small_tiles(MIDDLE), toward)

    assert played(0.5) == transition.effect(leaving, arriving, direction)(0.5)


def test_halfway_through_scaling_the_grid_shows_around_the_shrinking_slide() -> None:
    halfway = scale(SLIDE, OPENED, small_tiles(MIDDLE))(0.5)

    assert (halfway[0][0], halfway[-1][-1]) == (OPENED[0][0], OPENED[-1][-1])


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        (Point(1, 5), "left"),
        (Point(30, 5), "right"),
        (Point(15, 0), "top"),
        (Point(15, 10), "bottom"),
    ],
    ids=["near the left", "near the right", "near the top", "near the bottom"],
)
def test_exposé_slides_a_thumbnail_in_from_its_nearest_edge(region: Point, expected: str) -> None:
    start = Region(left=region.x, top=region.y, right=region.x + 8, bottom=region.y + 3)
    away = offstage(start, SMALL_WIDTH, SMALL_HEIGHT)

    edges = {
        "left": away.right <= 0,
        "right": away.left >= SMALL_WIDTH,
        "top": away.bottom <= 0,
        "bottom": away.top >= SMALL_HEIGHT,
    }
    assert [edge for edge, is_past in edges.items() if is_past] == [expected]


def blank_except(frame: Grid, where: Tiles, shown: int) -> list[bool]:
    """For each thumbnail but `shown`, whether nothing has landed in it yet."""
    empty = blank(backdrop_of(SLIDE, OPENED))
    return [
        all(cell == empty for row in cut(frame, region) for cell in row)
        for index, region in enumerate(where.thumbnails)
        if index != shown
    ]


def test_the_deal_starts_once_the_slide_is_in_its_place() -> None:
    where = small_tiles(MIDDLE)

    shrunk = deal(SLIDE, OPENED, where)(SHRUNK)

    assert cut(shrunk, where.chosen) == cut(OPENED, where.chosen)
    assert all(blank_except(shrunk, where, where.selected))


def test_the_unpacked_thumbnails_start_packed_under_the_slide() -> None:
    where = small_tiles(MIDDLE)

    packed = unpack(SLIDE, OPENED, where)(PACKED)

    assert cut(packed, where.chosen) == cut(OPENED, where.chosen)
    assert all(blank_except(packed, where, where.selected))


def test_folded_flat_only_the_kept_panel_shows() -> None:
    folded = Axis(edges=(0, 3, 6, 9), kept=1).folded(1.0)

    assert folded == (None, None, None, (3, 0), (4, 0), (5, 0), None, None, None)


def test_unfolded_every_cell_shows_itself() -> None:
    assert Axis(edges=(0, 3, 6, 9), kept=2).folded(0.0) == tuple((cell, 0) for cell in range(9))


@pytest.mark.parametrize("direction", Direction)
def test_halfway_through_a_flip_the_card_is_edge_on(direction: Direction) -> None:
    halfway = flip(SLIDE, OPENED, direction)(0.5)

    assert {glyph.grapheme for row in halfway for glyph in row if glyph is not None} == {" "}


def test_the_slices_are_the_header_and_each_row_of_thumbnails() -> None:
    where = small_tiles(MIDDLE)

    assert bands(where, SMALL_HEIGHT) == (0, 1, *(region.top for region in where.thumbnails[3::3]), SMALL_HEIGHT)


def test_the_slides_own_slice_moves_first() -> None:
    where = small_tiles(MIDDLE)

    started = sliced(SLIDE, OPENED, where)(0.2)

    moved = [row != slide_row for row, slide_row in zip(started, SLIDE, strict=True)]
    assert moved == [where.chosen.top <= y < where.chosen.bottom for y in range(SMALL_HEIGHT)]


def slide_rows(frame: Frame) -> list[str]:
    return frame.text(ansi=False).splitlines()[:-FOOTER_ROWS]


EDITED = next(index for index, slide in enumerate(SLIDES) if slide.title == "frozendict: the mutable default, fixed")


async def screens(host: Host, grid_transition: str, steps: Sequence[AnyEvent | AnyControl | None]) -> list[Frame]:
    """What `steps` from `EDITED`, with `grid_transition` picked, draw, a screenshot for each `None` among them."""
    frames: list[Frame] = []
    await app(
        root(SLIDES, host, Checkpoint(slide=EDITED, grid_transition=grid_transition), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(*(Screenshot(handler=frames.append) if step is None else step for step in steps), Quit()),
        clock=EXPORT_CLOCK,
    )
    return frames


PLAYED = {name: DRAWN[name] for name in ("scale", "expose", "deal", "unpack", "fold", "flip", "slice")}
"""The grid's own effects, rather than F6's, which the crossing tests play in the deck already."""


@pytest.mark.parametrize("name", [*PLAYED, "dissolve"])
async def test_every_grid_effect_opens_the_grid_in_the_deck_and_lands_on_it(host: Host, name: str) -> None:
    duration = DRAWN[name].duration
    playing = (KeyPressed(key="d"), AdvanceClock(by=duration / 2), None, AdvanceClock(by=duration), None)
    halfway, ended = await screens(host, name, playing)
    (instant,) = await screens(host, OFF, (KeyPressed(key="d"), None))

    assert slide_rows(ended) == slide_rows(instant)
    assert slide_rows(halfway) != slide_rows(instant)


@pytest.mark.parametrize("name", [*PLAYED, "dissolve"])
async def test_every_grid_effect_closes_the_grid_in_the_deck_and_lands_on_the_slide(host: Host, name: str) -> None:
    duration = DRAWN[name].duration
    opened = (KeyPressed(key="d"), AdvanceClock(by=duration), KeyPressed(key=Key.Right), KeyPressed(key=Key.Enter))
    halfway, ended = await screens(
        host, name, (*opened, AdvanceClock(by=duration / 2), None, AdvanceClock(by=duration), None)
    )
    (instant,) = await screens(host, OFF, (*opened, None))

    assert slide_rows(ended) == slide_rows(instant)
    assert slide_rows(halfway) != slide_rows(instant)


async def test_clicking_a_thumbnail_plays_the_grid_transition(host: Host) -> None:
    duration = DRAWN["deal"].duration
    where = tiles(STAGE_WIDTH, STAGE_HEIGHT, EDITED, SLIDES)
    beside = where.thumbnails[where.selected + 1]
    click = Point(beside.left + 2, beside.top + 2)
    clicked = (
        KeyPressed(key="d"),
        AdvanceClock(by=duration),
        MouseDown(absolute=click, button=1),
        MouseUp(absolute=click, button=1),
    )
    (halfway,) = await screens(host, "deal", (*clicked, AdvanceClock(by=duration / 2), None))
    (instant,) = await screens(host, OFF, (*clicked, None))

    assert slide_rows(halfway) != slide_rows(instant)
