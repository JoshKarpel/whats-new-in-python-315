"""
The hand-placed drawings: diagrams, which don't wrap, so on stage the slide clips
whatever of them is wider than it. Each diagram is drawn on a screen much wider than the slide, where nothing clips it,
and measured.
"""

from collections.abc import Callable
from functools import partial
from itertools import pairwise

import pytest
from counterweight.app import app
from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.output import Frame
from counterweight.styles.utilities import *

from whats_new.diagrams import fan_out
from whats_new.diagrams import frozendict_hierarchy
from whats_new.diagrams import low_level
from whats_new.diagrams import profilers
from whats_new.diagrams import task_group
from whats_new.diagrams.draw import fork
from whats_new.diagrams.graphemes import LAYER_STEPS
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
    **{f"fan out {s}": partial(fan_out.fan_out, s, False) for s in range(fan_out.STEPS)},
    **{
        f"frame pointers {s}": partial(low_level.frame_pointer_chain, s, False)
        for s in range(low_level.FRAME_POINTER_STEPS)
    },
    "jit pipeline": low_level.jit_pipeline,
    **{f"gc timeline {s}": partial(low_level.gc_timeline, s, False) for s in range(low_level.GC_STEPS)},
    **{
        f"tracing vs sampling {s}": partial(profilers.tracing_vs_sampling, s, False)
        for s in range(profilers.SAMPLING_STEPS)
    },
    **{f"text layers {s}": partial(layers, s) for s in range(LAYER_STEPS)},
    "architectures": profilers.architectures,
    "the loop": partial(profilers.the_loop, 4_194_304),
    "site startup": site_startup,
    "graphemes": band_code_points,
    "take bytes": take_bytes_memory,
}


async def drawn_width(drawing: Component | Text | Div) -> int:
    """How many columns `drawing` covers, from its leftmost drawn cell to its rightmost, on a screen `WIDE` columns wide."""

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
    lines = [line.rstrip() for line in frames[0].text(ansi=False).split("\n") if line.strip()]
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


def text_of(ink: Text) -> str:
    return "".join(chunk if isinstance(chunk, str) else chunk.content for chunk in ink.content)


@pytest.mark.parametrize("thread", range(fan_out.THREADS))
def test_fan_out_items_move_one_cell_at_a_time(thread: int) -> None:
    """An item in flight steps to a neighboring cell on each move, so it glides along the lines rather than jumping."""
    route = fan_out.route(thread)

    assert all(abs(x - nx) + abs(y - ny) == 1 for (x, y), (nx, ny) in pairwise(route))
    assert route[-1] == (fan_out.DROPS[thread], fan_out.LABELS - 1)
