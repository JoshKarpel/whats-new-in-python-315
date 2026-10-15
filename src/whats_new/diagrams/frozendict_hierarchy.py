"""
Why neither `dict` nor `frozendict` subclasses the other, as `set` and `frozenset` don't:
the hierarchy, then the tempting edge crossed out, then the reverse edge crossed out, then the consequence.
"""

from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node

STEPS = 4


def frozendict_hierarchy(step: int) -> Div:
    parts: list[Text | Div] = [
        node("Mapping", 15, 0),
        ink("┌───────┴────────┐", 9, 3),
        ink("│                │", 9, 4),
        node("dict", 5, 5),
        node("frozendict", 20, 5, style=HIGHLIGHT_NODE),
        node("Set", 62, 0),
        ink("┌──────┴───────┐", 56, 3),
        ink("│              │", 56, 4),
        node("set", 53, 5),
        node("frozenset", 66, 5),
        ink("neither subclasses the other", 54, 9, NOTE),
    ]
    if step >= 1:
        parts += [
            ink("◀━✗━━", 14, 5, CROSSED),
            ink("✗ frozendict(dict)?", 1, 9, CROSSED),
            ink("  it has fewer methods", 1, 10, EDGE),
        ]
    if step >= 2:
        parts += [
            ink("━━✗━▶", 14, 7, CROSSED),
            ink("✗ dict(frozendict)?", 25, 9, CROSSED),
            ink("  a dict breaks", 25, 10, EDGE),
            ink("  never-changes and", 25, 11, EDGE),
            ink("  is-hashable (Liskov)", 25, 12, EDGE),
        ]
    if step >= 3:
        parts.append(
            ink(
                (
                    Chunk(content="so accept ", style=NOTE),
                    Chunk(content="Mapping", style=HIGHLIGHT),
                    Chunk(content=", not dict", style=NOTE),
                ),
                10,
                14,
            )
        )
    return area(86, 15, *parts)
