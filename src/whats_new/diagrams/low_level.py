"""
Diagrams for the performance section below Python: the frame pointer chain (and what one extension built
without it does to it), the JIT's pipeline, and the garbage collector's timeline across releases.
"""

from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import default

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node

FRAME_POINTER_STEPS = 2

# Newest first, as a profiler reads them: each frame's saved rbp names its caller's frame.
STACK = (
    ("fib", "py::"),
    ("callback", "py::"),
    ("call_many", "churn.so"),
    ("outer_python_frame", "py::"),
    ("main", "python"),
    ("_start", "libc"),
)
EXTENSION = 2


def frame_pointer_chain(step: int) -> Div:
    """
    The stack as a linked list, each frame's saved rbp pointing at its caller's;
    then the extension built without frame pointers, whose rbp holds data, cuts off everything after it.
    """
    is_broken = step >= 1
    parts: list[Text | Div] = [ink("a sample's stack, newest first", 0, 0, NOTE)]
    for row, (frame, owner) in enumerate(STACK):
        y = 1 + row * 2
        is_lost = is_broken and row > EXTENSION
        box = CellStyle(foreground=EDGE.foreground) if is_lost else HIGHLIGHT if row == 0 else NOTE
        parts.append(ink(f"│ {frame:<20} {owner:>9} │", 0, y, box))
        if row == len(STACK) - 1:
            continue
        if is_broken and row == EXTENSION:
            parts.append(ink("saved rbp ──▶ ✗ data, not a frame: the walk stops here", 35, y, CROSSED))
        elif is_lost:
            parts.append(ink("unreachable", 35, y, EDGE))
        else:
            parts.append(ink(f"saved rbp ──▶ {STACK[row + 1][0]}", 35, y, EDGE))
    caption = (
        (
            Chunk(content="one extension without frame pointers, and ", style=NOTE),
            Chunk(content="its callers vanish", style=CROSSED),
        )
        if is_broken
        else (Chunk(content="perf and eBPF walk this list: cheap, and no DWARF tables needed", style=NOTE),)
    )
    parts.append(ink(caption, 0, 13))
    return area(86, 14, *parts)


def jit_pipeline() -> Div:
    stages = (
        ("bytecode", False),
        ("specialized", False),
        ("trace", True),
        ("micro-ops", True),
        ("machine code", False),
    )
    parts: list[Text | Div] = []
    x = 0
    for index, (name, changed) in enumerate(stages):
        parts.append(node(name, x, 0, style=HIGHLIGHT_NODE if changed else default))
        x += len(name) + 4
        if index < len(stages) - 1:
            parts.append(ink("─▶", x, 1))
            x += 3
    parts += [
        ink("new in 3.15: a tracing frontend, register allocation,", 0, 4, HIGHLIGHT),
        ink("more constant propagation and refcount elimination", 0, 5, HIGHLIGHT),
        ink("and it tells GDB and backtrace() how to unwind through JIT frames", 0, 7, NOTE),
    ]
    return area(86, 8, *parts)


RELEASES = (
    ("3.13", "rolled back", "generational"),
    ("3.14.0", "ships it", "incremental"),
    ("3.14.4", "growth reports", "incremental"),
    ("3.14.5", "reverted", "generational"),
    ("3.15", "a PEP to return", "generational"),
)


def gc_timeline() -> Div:
    parts: list[Text | Div] = [ink("─" * 84 + "▶", 0, 1)]
    for index, (release, event, collector) in enumerate(RELEASES):
        x = index * 17
        style = CROSSED if collector == "incremental" else NOTE
        parts += [
            ink("┬", x + 2, 1),
            ink(release, x, 0, HIGHLIGHT),
            ink(event, x, 2, EDGE),
            ink(collector, x, 3, style),
        ]
    return area(86, 4, *parts)
