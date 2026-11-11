"""
Ghosts in the running deck: `g` in the grid makes the selected slide a ghost or not, which the arrows then skip
and the checkpoint remembers, and the export still shows every one, marked.
How the arrows move around ghosts, as a pure function, is in `test_navigation.py`.
"""

from collections.abc import Sequence
from dataclasses import replace

from counterweight import app
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key

from whats_new import export
from whats_new.checkpoint import Checkpoint
from whats_new.components.grid import thumbnail_number
from whats_new.components.look import GHOST
from whats_new.components.look import GHOST_STAND_IN
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING

# Title cards, which run nothing, so each test takes only the time it takes to render.
DECK = tuple(slide for slide in SLIDES if slide.is_title_card)[:4]

SELECT_SECOND = (KeyPressed(key="d"), KeyPressed(key=Key.Right))
"""From the first slide, open the grid and select the second."""


async def checkpoints(host: Host, steps: Sequence[AnyEvent | AnyControl], start: Checkpoint) -> list[Checkpoint]:
    """Every checkpoint the deck remembers, starting from `start`, as it's driven through `steps`."""
    remembered: list[Checkpoint] = []
    await app(
        root(DECK, host, start, remembered.append),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(*steps, Quit()),
        clock=EXPORT_CLOCK,
    )
    return remembered


async def test_g_in_the_grid_makes_the_selected_slide_a_ghost_that_right_skips(host: Host) -> None:
    steps = (*SELECT_SECOND, KeyPressed(key="g"), KeyPressed(key=Key.Escape), KeyPressed(key=Key.Right))

    last = (await checkpoints(host, steps, Checkpoint(slide=0)))[-1]

    assert (last.slide, last.ghost_overrides) == (2, frozendict({DECK[1].title: True}))


async def test_g_twice_leaves_the_slide_as_it_was(host: Host) -> None:
    steps = (*SELECT_SECOND, *(KeyPressed(key="g"),) * 2, KeyPressed(key=Key.Escape), KeyPressed(key=Key.Right))

    last = (await checkpoints(host, steps, Checkpoint(slide=0)))[-1]

    assert (last.slide, last.ghost_overrides) == (1, frozendict())


async def test_g_on_a_slide_outside_the_grid_does_nothing(host: Host) -> None:
    steps = (KeyPressed(key="g"), KeyPressed(key=Key.Right))

    last = (await checkpoints(host, steps, Checkpoint(slide=0)))[-1]

    assert (last.slide, last.ghost_overrides) == (1, frozendict())


async def test_a_restart_keeps_the_ghosts_g_made(host: Host) -> None:
    start = Checkpoint(slide=0, ghost_overrides=frozendict({DECK[1].title: True}))

    last = (await checkpoints(host, (KeyPressed(key=Key.Right),), start))[-1]

    assert last.slide == 2


WITH_A_GHOST = (DECK[0], replace(DECK[1], is_ghost=True), DECK[2])


async def test_the_export_captions_every_slide_marking_ghosts(host: Host) -> None:
    captions = [caption for caption, _ in await export.screenshots(WITH_A_GHOST, host)]

    assert captions == [f"1. {DECK[0].title}", f"2. {DECK[1].title} {GHOST}", f"3. {DECK[2].title}"]


async def test_the_export_screenshots_the_ghost_itself(host: Host) -> None:
    frames = [frame for _, frame in await export.screenshots(WITH_A_GHOST, host)]

    assert [GHOST in frame.text(ansi=False) for frame in frames] == [False, True, False]


def test_the_grid_marks_a_ghost_without_the_emoji_zellij_web_mismeasures() -> None:
    assert thumbnail_number(1, frozenset({1})) == GHOST_STAND_IN
