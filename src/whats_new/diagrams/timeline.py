"""
A timeline that draws itself on one milestone per reveal step: the axis grows out to the newest milestone, which
appears when the axis reaches it. The sagas (the garbage collector's releases, the JIT's) are told on it.
"""

from dataclasses import dataclass
from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle

from whats_new.components.animation import use_explanation
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink

EXTEND = timedelta(milliseconds=500)
ROWS = 4
"""When, the axis, what happened, and the note."""


@dataclass(frozen=True, slots=True)
class Milestone:
    """One tick on a timeline: when (above the axis), what happened (below it), and a note under that, in its own style."""

    when: str
    event: str
    note: str
    note_style: CellStyle


def width(milestones: tuple[Milestone, ...], spacing: int) -> int:
    """How wide the whole timeline draws: every milestone but the last one `spacing` apart, and the last one's text."""
    last = milestones[-1]
    return spacing * (len(milestones) - 1) + max(len(last.when), len(last.event), len(last.note))


def timeline_through(milestones: tuple[Milestone, ...], spacing: int, step: int, is_live: bool) -> Component:
    """
    The milestones up to the one at `step`, `spacing` columns apart, the axis growing out to the newest,
    which appears when the axis arrives.
    The key remounts the drawing on each step, which plays the axis's growth once.
    """
    return growing_timeline(milestones, spacing, step, is_live).with_key(f"milestone-{step}")


@component
def growing_timeline(milestones: tuple[Milestone, ...], spacing: int, step: int, is_live: bool) -> Div:
    progress = use_explanation(EXTEND, is_live)
    start = 0 if step == 0 else tick_x(step - 1, spacing)
    head = start + round((tick_x(step, spacing) - start) * progress)
    parts: list[Text | Div] = [ink("─" * head + "▶", 0, 1)]
    for index, milestone in enumerate(milestones[: step + 1]):
        if index == step and progress < 1:
            continue
        x = index * spacing
        parts += [
            ink("┬", tick_x(index, spacing), 1),
            ink(milestone.when, x, 0, HIGHLIGHT),
            ink(milestone.event, x, 2, EDGE),
            ink(milestone.note, x, 3, milestone.note_style),
        ]
    return area(width(milestones, spacing), ROWS, *parts)


def tick_x(index: int, spacing: int) -> int:
    """The column of the milestone at `index`'s tick on the axis."""
    return index * spacing + 2
