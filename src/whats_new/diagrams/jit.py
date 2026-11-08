"""
The JIT saga's diagrams: the design changes it made on main release by release, the Steering Council's 2026 request
and what followed it, and the JIT beside the incremental garbage collector and free-threading.

The timelines draw themselves on one milestone per reveal step (see `diagrams/timeline.py`).
"""

from counterweight.components import Component
from counterweight.elements import Div
from counterweight.elements import Text

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.timeline import Milestone
from whats_new.diagrams.timeline import timeline_through

SPACING = 20

DESIGNS = (
    Milestone("3.12", "bytecode DSL, uops", "", NOTE),
    Milestone("3.13", "copy-and-patch JIT", "no speedup", CROSSED),
    Milestone("3.14", "more refactoring", "no speedup", CROSSED),
    Milestone("3.15", "trace recording", "4-12% faster", NOTE),
    Milestone("3.16?", "method frontend", "proposed", NOTE),
)
"""
Each release's change to the JIT and the interpreter under it, as PEP 836 lists them, and the speedup it reports:
the "simple implementation of tracing in CPython yielded no speedups initially in 3.13 and 3.14",
and 3.15 is "roughly 4-12% faster geometric mean on the pyperformance benchmark suite".
"""
DESIGN_STEPS = len(DESIGNS)
"""One release per step, the timeline drawing itself on to it."""


def designs_ends_showing(step: int) -> str | None:
    """What changed in the release at `step`, which appears once the axis reaches it."""
    return DESIGNS[step].event


def designs(step: int, is_live: bool) -> Component:
    """The releases up to the one at `step`, with what each changed and how much faster it made the JIT."""
    return timeline_through(DESIGNS, SPACING, step, is_live)


REQUEST = (
    Milestone("Jun 5", "SC: a PEP, or out", "no new JIT work", CROSSED),
    Milestone("Jul 3", "PEP 836 posted", "Standards Track", NOTE),
    Milestone("Sep 21", "SC feedback", '"mostly answers"', NOTE),
    Milestone("Oct 19", "PEP withdrawn", '"bandwidth"', CROSSED),
    Milestone("Dec 2026", "six months up", "out of main?", CROSSED),
)
"""
2026, from the Steering Council's request for a PEP to the end of the six months it gave one to be accepted in.
The notes quote the September feedback ("the PEP mostly answers the questions we asked") and the withdrawal
("we don't feel we have the personal bandwidth to carry the current version forward").
"""
REQUEST_STEPS = len(REQUEST)
"""One event per step, the timeline drawing itself on to it."""


def request_ends_showing(step: int) -> str | None:
    """What happened at `step`, which appears once the axis reaches it."""
    return REQUEST[step].event


def request(step: int, is_live: bool) -> Component:
    """The events up to the one at `step`."""
    return timeline_through(REQUEST, SPACING, step, is_live)


EXPERIMENTS = (
    ("started", "on main", "on main", "a fork: nogil"),
    ("its PEP", "none", "744, Informational", "703, accepted first"),
    ("its flags", "none: on in 3.14.0", "build, and PYTHON_JIT", "build, and PYTHON_GIL"),
    ("cost to others", "memory, in production", "the design kept changing", "agreed in the PEP"),
    ("so far", "reverted in 3.14.5", "paused, PEP withdrawn", "supported since 3.14"),
    ("next", "PEP 848, a draft", "a PEP: none since 836", "phase III: the default"),
)
"""
Three big changes to the interpreter, a row per question: the incremental garbage collector, the JIT, and
free-threading.
- PEP 848 is Mark Shannon's generational incremental collector, a Standards Track draft.
- "the design kept changing" is Pablo Galindo Salgado's account of the JIT's years on main,
  "the design changing underneath everyone".
- Free-threading began as Sam Gross's nogil fork. The Steering Council accepted PEP 703 before it landed, expecting
  every core developer to support the free-threaded build ("it's neither fair nor particularly forward-thinking to
  expect the free-threaded maintainers to do all the work"), and PEP 779 made it supported in 3.14.
  Phase III, the default, is the third of the stages the acceptance laid out.
"""
QUESTION_WIDTH = 16
COLUMN_WIDTH = 27
HEADINGS = ("incremental GC", "the JIT", "free-threading")


def experiments() -> Div:
    """The three side by side under their names, the questions down the left."""
    parts: list[Text | Div] = [
        ink(heading, QUESTION_WIDTH + index * COLUMN_WIDTH, 0, HIGHLIGHT) for index, heading in enumerate(HEADINGS)
    ]
    for row, (question, *answers) in enumerate(EXPERIMENTS, 2):
        parts.append(ink(question, 0, row, EDGE))
        parts += [ink(answer, QUESTION_WIDTH + index * COLUMN_WIDTH, row, NOTE) for index, answer in enumerate(answers)]
    width = QUESTION_WIDTH + (len(HEADINGS) - 1) * COLUMN_WIDTH + max(len(row[-1]) for row in EXPERIMENTS)
    return area(width, len(EXPERIMENTS) + 2, *parts)
