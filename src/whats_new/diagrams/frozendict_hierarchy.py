"""
Why neither `dict` nor `frozendict` subclasses the other, as `set` and `frozenset` don't, under the ABCs they
register as: `dict` is a `MutableMapping`, `frozendict` only a `Mapping`. The mappings, then the sets beside them,
then the tempting edge crossed out, then the reverse edge crossed out, then the consequence.
The drawing's area is the same size at every step, so revealing a part moves nothing.

The ABCs are drawn in light rounded boxes with italic names, as UML marks abstract classes,
and the classes you instantiate in the heavy boxes every other diagram uses, with a key saying which is which,
alone in the bottom right corner so it doesn't read as part of the argument.
"""

from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.utilities import *

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import centered_node
from whats_new.diagrams.draw import fork
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import middle
from whats_new.diagrams.draw import node

STEPS = 5

ABSTRACT_KEY = CellStyle(foreground=Color.from_hex("#94a3b8"))
CONCRETE_KEY = CellStyle(foreground=Color.from_hex("#cbd5e1"))
"""The key's swatches, in the colors of the boxes they stand for."""
ABSTRACT = border_lightrounded | border_color("slate", 400) | text_italic

# The boxes' left edges. dict sits under MutableMapping, and frozendict straight under Mapping, level with dict,
# which leaves room between the two for the crossed-out arrows.
MUTABLE_MAPPING = 0
FROZENDICT = 22
MUTABLE_SET = 48
FROZENSET = 66
LOWER = 9
"""The row the concrete classes' boxes start on, below their Mutable ABCs."""
WIDTH, HEIGHT = 80, 24
KEY_WIDTH = len("╭─╮ abstract base class")
KEY = (WIDTH - KEY_WIDTH, HEIGHT - 4)
"""The top-left corner of the key, which ends flush with the drawing's bottom right corner."""


def frozendict_hierarchy(step: int) -> Div:
    mutable_mapping, frozendict_ = middle(MUTABLE_MAPPING, "MutableMapping"), middle(FROZENDICT, "frozendict")
    mutable_set, frozenset_ = middle(MUTABLE_SET, "MutableSet"), middle(FROZENSET, "frozenset")
    mapping, set_ = (mutable_mapping + frozendict_) // 2, (mutable_set + frozenset_) // 2
    parts: list[Text | Div] = [
        centered_node("Mapping", mapping, 0, style=ABSTRACT),
        *fork(mapping, (mutable_mapping, frozendict_), 3),
        node("MutableMapping", MUTABLE_MAPPING, 5, style=ABSTRACT),
        ink("│", mutable_mapping, 8),
        centered_node("dict", mutable_mapping, LOWER),
        ink("│\n│\n│\n│", frozendict_, 5),
        node("frozendict", FROZENDICT, LOWER, style=HIGHLIGHT_NODE),
        ink("╭─╮\n╰─╯", KEY[0], KEY[1], ABSTRACT_KEY),
        ink("abstract base class\n(collections.abc)", KEY[0] + 4, KEY[1], NOTE | CellStyle(italic=True)),
        ink("┏━┓\n┗━┛", KEY[0], KEY[1] + 2, CONCRETE_KEY),
        ink("concrete class\n(builtins)", KEY[0] + 4, KEY[1] + 2, NOTE),
    ]
    if step >= 1:
        parts += [
            centered_node("Set", set_, 0, style=ABSTRACT),
            *fork(set_, (mutable_set, frozenset_), 3),
            node("MutableSet", MUTABLE_SET, 5, style=ABSTRACT),
            ink("│", mutable_set, 8),
            centered_node("set", mutable_set, LOWER),
            ink("│\n│\n│\n│", frozenset_, 5),
            node("frozenset", FROZENSET, LOWER),
            ink("neither subclasses the other", MUTABLE_SET, 13, NOTE),
        ]
    if step >= 2:
        parts += [
            ink("◀━✗━━", 15, LOWER, CROSSED),
            ink("✗ frozendict(dict)?", 0, 13, CROSSED),
            ink("  it has fewer methods", 0, 14, EDGE),
        ]
    if step >= 3:
        parts += [
            ink("━━✗━▶", 15, LOWER + 2, CROSSED),
            ink("✗ dict(frozendict)?", 22, 13, CROSSED),
            ink("  a dict breaks", 22, 14, EDGE),
            ink("  never-changes and", 22, 15, EDGE),
            ink("  is-hashable (Liskov)", 22, 16, EDGE),
        ]
    if step >= 4:
        parts.append(
            ink(
                (
                    Chunk(content="so accept ", style=NOTE),
                    Chunk(content="Mapping", style=HIGHLIGHT),
                    Chunk(content=", not dict, unless you mutate it", style=NOTE),
                ),
                10,
                18,
            )
        )
    return area(WIDTH, HEIGHT, *parts)
