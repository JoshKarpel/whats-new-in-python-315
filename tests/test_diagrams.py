"""
The hand-placed drawings: diagrams, which don't wrap, so on stage the slide clips
whatever of them is wider than it. Each diagram is drawn on a screen much wider than the slide, where nothing clips it,
and measured.
"""

from collections.abc import Callable
from functools import partial
from itertools import pairwise

import pytest
from counterweight import app
from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.paint import Frame
from counterweight.styles.utilities import *

from whats_new.diagrams import collector
from whats_new.diagrams import fan_out
from whats_new.diagrams import frozendict_hierarchy
from whats_new.diagrams import jit
from whats_new.diagrams import low_level
from whats_new.diagrams import profilers
from whats_new.diagrams import task_group
from whats_new.diagrams.draw import fork
from whats_new.diagrams.graphemes import band_code_points
from whats_new.diagrams.graphemes import layers
from whats_new.diagrams.site_startup import site_startup
from whats_new.diagrams.take_bytes import take_bytes_memory
from whats_new.export import EXPORT_CLOCK
from whats_new.size import PRESENTING

WIDE = 200
SLIDE_WIDTH = PRESENTING.columns - 2
"""The slide's padding takes a column each side."""

# Animated drawings are drawn as a thumbnail draws them, at the end of each step's animation, the widest they get.
DRAWINGS: dict[str, Callable[[], Component | Text | Div]] = {
    **{
        f"frozendict hierarchy {s}": partial(frozendict_hierarchy.frozendict_hierarchy, s)
        for s in range(frozendict_hierarchy.STEPS)
    },
    **{f"task group {s}": partial(task_group.task_group, s, False) for s in range(task_group.STEPS)},
    **{
        f"fan out {shown} {s}": partial(fan_out.fan_out, shown, s, False)
        for shown in (fan_out.BROKEN, fan_out.SHARED)
        for s in range(fan_out.steps(shown))
    },
    **{
        f"frame pointers {s}": partial(low_level.frame_pointer_chain, s, False)
        for s in range(low_level.FRAME_POINTER_STEPS)
    },
    "jit pipeline": low_level.jit_pipeline,
    **{f"gc cycles {s}": partial(collector.cycle_collection, s, False) for s in range(collector.CYCLE_STEPS)},
    **{f"gc generations {s}": partial(collector.generations, s, False) for s in range(collector.GENERATION_STEPS)},
    **{f"gc schedules {s}": partial(collector.schedules, s, False) for s in range(collector.SCHEDULE_STEPS)},
    **{f"gc timeline {s}": partial(collector.timeline, s, False) for s in range(collector.TIMELINE_STEPS)},
    **{f"gc waiting {s}": partial(collector.waiting, s, False) for s in range(collector.WAITING_STEPS)},
    **{f"jit designs {s}": partial(jit.designs, s, False) for s in range(jit.DESIGN_STEPS)},
    **{f"jit request {s}": partial(jit.request, s, False) for s in range(jit.REQUEST_STEPS)},
    "three experiments": jit.experiments,
    **{
        f"tracing vs sampling {s}": partial(profilers.tracing_vs_sampling, s, False)
        for s in range(profilers.SAMPLING_STEPS)
    },
    "text layers": layers,
    "architectures": profilers.architectures,
    "the loop": partial(profilers.the_loop, 4_194_304),
    "site startup": site_startup,
    "graphemes": band_code_points,
    "take bytes": take_bytes_memory,
}


async def drawn(drawing: Component | Text | Div) -> str:
    """`drawing` as text, alone on a screen `WIDE` columns wide."""

    @component
    def alone() -> Div:
        return Div(style=row | full, children=(drawing,))

    frames: list[Frame] = []
    await app(
        alone(),
        headless=True,
        dimensions=(WIDE, PRESENTING.rows),
        autopilot=(Screenshot(handler=frames.append), Quit()),
        clock=EXPORT_CLOCK,
    )
    return frames[0].text(ansi=False)


async def drawn_width(drawing: Component | Text | Div) -> int:
    """How many columns `drawing` covers, from its leftmost drawn cell to its rightmost, on a screen `WIDE` columns wide."""
    lines = [line.rstrip() for line in (await drawn(drawing)).split("\n") if line.strip()]
    return max(len(line) for line in lines) - min(len(line) - len(line.lstrip()) for line in lines)


@pytest.mark.parametrize("name", DRAWINGS)
async def test_drawing_fits_the_slide(name: str) -> None:
    assert await drawn_width(DRAWINGS[name]()) <= SLIDE_WIDTH


@pytest.mark.parametrize(
    ("parent", "children", "expected"),
    [
        (4, (0, 8), ("┌───┴───┐", "│       │")),
        (4, (0, 4, 8), ("┌───┼───┐", "│   │   │")),
        (3, (0, 5, 9), ("┌──┴─┬───┐", "│    │   │")),
    ],
    ids=["two children", "a child under the parent", "the parent between children"],
)
def test_fork_rises_at_the_parent_and_drops_at_each_child(
    parent: int, children: tuple[int, ...], expected: tuple[str, str]
) -> None:
    bar, stems = fork(parent, children, 0)

    assert (text_of(bar), text_of(stems)) == expected


async def test_text_layers_show_the_accent_a_reader_sees() -> None:
    """The "what you see" row draws "é" as its one code point, which zellij keeps, where it drops a combining mark."""
    seen = next(line for line in (await drawn(layers())).split("\n") if "what you see" in line)

    assert "\N{LATIN SMALL LETTER E WITH ACUTE}" in seen


def text_of(ink: Text) -> str:
    return "".join(chunk if isinstance(chunk, str) else chunk.content for chunk in ink.content)


@pytest.mark.parametrize("thread", range(fan_out.THREADS))
def test_fan_out_items_move_one_cell_at_a_time(thread: int) -> None:
    """An item in flight steps to a neighboring cell on each move, so it glides along the lines rather than jumping."""
    route = fan_out.route(thread)

    assert all(abs(x - nx) + abs(y - ny) == 1 for (x, y), (nx, ny) in pairwise(route))
    assert route[-1] == (fan_out.DROPS[thread], fan_out.LABELS - 1)


@pytest.mark.parametrize("fraction", [step / 200 for step in range(200)])
def test_concurrent_tee_copies_land_on_every_thread_at_once(fraction: float) -> None:
    landed = {fan_out.flight(thread, fraction) is None for thread in range(fan_out.THREADS)}

    assert len(landed) == 1


@pytest.mark.parametrize("fraction", [step / 200 for step in range(200)])
def test_concurrent_tee_copies_cross_the_stem_as_one(fraction: float) -> None:
    stem = set(fan_out.route(0)[: fan_out.SHARED_CELLS])
    cells = {fan_out.flight(thread, fraction) for thread in range(fan_out.THREADS)}

    assert cells.isdisjoint(stem) or len(cells) == 1


def test_a_collection_moves_only_survivors_up() -> None:
    """Right after a collection frees its garbage, the next generation gains exactly the live objects it scanned."""
    snapshots = collector.SNAPSHOTS
    moves = [index for index, snapshot in enumerate(snapshots) if "move up" in snapshot.status]

    assert moves
    for index in moves:
        freeing, moved = snapshots[index - 1], snapshots[index]
        assert moved.collecting is not None
        target = moved.collecting + 1
        survivors = tuple(
            cell for cells in freeing.generations[:target] for cell in cells if cell is collector.Cell.LIVE
        )
        assert moved.generations[target] == freeing.generations[target] + survivors
