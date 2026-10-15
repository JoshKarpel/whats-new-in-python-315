"""
What a slide is: a title, the component that draws it, how many reveal steps it has, and the PEPs it cites.

Sections build tuples of these; the deck concatenates them, and the presenter, the grid and the export all walk them.
"""

from collections.abc import Callable
from dataclasses import dataclass

from counterweight.components import Component

from whats_new.host import Host
from whats_new.runs import Run


@dataclass(frozen=True, slots=True)
class SlideProps:
    """What a slide's content component is drawn with."""

    step: int
    """Which reveal step is showing, from 0 to the slide's `steps - 1`."""

    is_live: bool
    """
    Whether this is the slide being presented, rather than a thumbnail in the grid.
    Only a live slide takes focus and so receives its own keys: a thumbnail never runs anything.
    """

    host: Host

    runs: tuple[Run, ...]
    """The slide's runs, which its run pane binds to the number keys."""


@dataclass(frozen=True, slots=True)
class Slide:
    title: str
    content: Callable[[SlideProps], Component]
    peps: tuple[int, ...] = ()
    """The PEPs the slide cites, which the slide frame links beneath it."""
    steps: int = 1
    """How many reveal steps the slide has; Space moves to the next one."""
    runs: tuple[Run, ...] = ()
    """
    What the slide runs, bound to `1` through `9` in order.
    Declared on the slide rather than inside its content, so the example check can find and run every one.
    """
    has_heading: bool = True
    """Whether the frame draws the title above the content; title cards carry their own."""

    def __post_init__(self) -> None:
        if self.steps < 1:
            raise ValueError(f"slide {self.title!r} needs at least one step, not {self.steps}")


def pep_url(number: int) -> str:
    return f"https://peps.python.org/pep-{number:04d}/"
