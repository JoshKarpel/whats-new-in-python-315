"""
What a slide is: a title, the component that draws it, how many reveal steps it has, the PEPs it cites,
what it runs, and what the recording does on it.

Sections build tuples of these; the deck concatenates them, and the presenter, the grid and the export all walk them.
"""

from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from counterweight.autopilot import AutopilotStep
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


class TitleCard(Enum):
    """A slide that carries its own title, so the frame draws no heading over it, and what it opens."""

    SECTION = "section"
    """Opens a section of the deck, which the slide grid shows as a grid of its own."""
    SUBSECTION = "subsection"
    """Opens a topic within the section it's in, such as Tachyon within Performance."""


def no_tour(step: int) -> Iterable[AutopilotStep]:
    """The tour of a slide that shows everything through its reveal steps and runs."""
    return ()


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
    title_card: TitleCard | None = None
    """What kind of title card the slide is, or `None` for a slide the frame draws a heading over."""
    tour: Callable[[int], Iterable[AutopilotStep]] = no_tour
    """
    What the recording does on each reveal step, by the step, beyond showing it and running the slide's runs:
    the keys a presenter would press on a stage the run pane doesn't drive, such as the REPL's.
    """

    def __post_init__(self) -> None:
        if self.steps < 1:
            raise ValueError(f"slide {self.title!r} needs at least one step, not {self.steps}")


def sections(slides: tuple[Slide, ...]) -> tuple[range, ...]:
    """
    The indexes of each section of `slides`: a run of slides starting at each section's title card
    (or the first slide).
    """
    starts = [index for index, slide in enumerate(slides) if index == 0 or slide.title_card is TitleCard.SECTION]
    return tuple(range(start, stop) for start, stop in zip(starts, (*starts[1:], len(slides)), strict=True))


def next_section(index: int, slides: tuple[Slide, ...]) -> int:
    """The first slide of the section after the one `index` is in, or the deck's last slide from the last section."""
    return next((section.start for section in sections(slides) if section.start > index), len(slides) - 1)


def previous_section(index: int, slides: tuple[Slide, ...]) -> int:
    """
    The first slide of the section `index` is in, or of the section before it from a section's first slide,
    as a media player's "previous" restarts the track before it skips back.
    """
    return max((section.start for section in sections(slides) if section.start < index), default=0)


def pep_url(number: int) -> str:
    return f"https://peps.python.org/pep-{number:04d}/"
