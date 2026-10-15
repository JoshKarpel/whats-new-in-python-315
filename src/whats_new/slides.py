"""
What a slide is: a title, the component that draws it, how many reveal steps it has, and the PEPs it cites.

Sections build tuples of these; the deck concatenates them, and the presenter, the grid and the export all walk them.
"""

from collections.abc import Callable
from dataclasses import dataclass

from counterweight.components import Component
from counterweight.controls import AnyControl
from counterweight.controls import ClearFocus
from counterweight.controls import FocusOn
from counterweight.focus import FocusHandle

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

    edits: frozendict[str, str]
    """
    The text of each example file edited on the slide so far, by its name under `examples/`,
    which the slide's code shows and its runs execute in place of the file.
    """

    edit: Callable[[str, Callable[[str], str]], None]
    """Edits the example `name`, with a function from its latest text, edited or not, to its new text."""

    runs_focus: FocusHandle
    """The run pane's focus handle, which leaving an editor focuses, so the number keys run again."""

    @property
    def leave_editor(self) -> AnyControl:
        """What leaving an editor does: focus the run pane, or clear focus, giving the keys to the deck, on a slide with no runs."""
        return FocusOn(self.runs_focus) if self.runs else ClearFocus()


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
