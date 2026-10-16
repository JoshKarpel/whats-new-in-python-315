"""
What a slide is: a title, the component that draws it, how many reveal steps it has, and the PEPs it cites.

Sections build tuples of these; the deck concatenates them, and the presenter, the grid and the export all walk them.
"""

from collections.abc import Callable
from dataclasses import dataclass

from counterweight.components import Component
from counterweight.controls import AnyControl
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

    code_theme: str
    """The Pygments style the slide's code is highlighted in, which F4 picks."""

    runs: tuple[Run, ...]
    """The slide's runs, which its run pane binds to the number keys."""

    edits: frozendict[str, str]
    """
    The text of each example file edited on the slide so far, by its name under `examples/`,
    which the slide's code shows and its runs execute in place of the file.
    """

    edit: Callable[[str, Callable[[str], str]], None]
    """Edits the example `name`, with a function from its latest text, edited or not, to its new text."""

    slide_focus: FocusHandle
    """
    The focus handle of whatever takes the live slide's own keys: its run pane, or a stage (Tachyon's, the REPL's).
    Leaving an editor or the theme picker focuses it, so those keys work again.
    """

    @property
    def leave_editor(self) -> AnyControl:
        """What leaving an editor does: focus the run pane, so the number keys run again (only a slide with runs edits)."""
        return FocusOn(self.slide_focus)


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
    is_title_card: bool = False
    """
    Whether the slide is a title card, which carries its own title, so the frame draws no heading over it.
    Each title card starts a section of the deck, which the slide grid shows as a grid of its own.
    """

    def __post_init__(self) -> None:
        if self.steps < 1:
            raise ValueError(f"slide {self.title!r} needs at least one step, not {self.steps}")


def sections(slides: tuple[Slide, ...]) -> tuple[range, ...]:
    """The indexes of each section of `slides`: a run of slides starting at each title card (or the first slide)."""
    starts = [index for index, slide in enumerate(slides) if index == 0 or slide.is_title_card]
    return tuple(range(start, stop) for start, stop in zip(starts, (*starts[1:], len(slides)), strict=True))


def pep_url(number: int) -> str:
    return f"https://peps.python.org/pep-{number:04d}/"
