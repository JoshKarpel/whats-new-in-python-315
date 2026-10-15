"""
One source, four threads, three ways, revealed one at a time:
a bare generator (three threads die), `serialize_iterator` (each item to exactly one thread),
and `concurrent_tee` (each item to every thread). The last two are the ones people mix up.
"""

from counterweight.elements import Div
from counterweight.elements import Text

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node

STEPS = 3
PANEL = 29

PANELS = (
    ("rows()", ("✓ all", "✗ died", "✗ died", "✗ died"), ("ValueError: generator", "already executing")),
    ("serialize_iterator", ("0 4 …", "1 5 …", "2 6 …", "3 7 …"), ("each item to exactly", "one thread")),
    ("concurrent_tee", ("0 1 2 …", "0 1 2 …", "0 1 2 …", "0 1 2 …"), ("each item to every", "thread")),
)


def panel(index: int, title: str, takes: tuple[str, ...], caption: tuple[str, ...]) -> list[Text | Div]:
    x = index * PANEL
    parts: list[Text | Div] = [
        node(title, x + (PANEL - len(title) - 4) // 2, 0),
        ink("┌──────┬──┴───┬──────┐", x + 3, 3),
        ink("T1     T2     T3     T4", x + 3, 4, NOTE),
    ]
    for thread, take in enumerate(takes):
        style = CROSSED if take.startswith("✗") else HIGHLIGHT if take.startswith("✓") else EDGE
        for line, word in enumerate(take.split(" ")):
            parts.append(ink(word, x + 3 + thread * 7, 5 + line, style))
    for line, text in enumerate(caption):
        parts.append(ink(text, x, 9 + line, CROSSED if index == 0 else NOTE))
    return parts


def fan_out(step: int) -> Div:
    parts = [part for index in range(step + 1) for part in panel(index, *PANELS[index])]
    return area(PANEL * 3, 11, *parts)
