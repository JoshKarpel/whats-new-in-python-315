"""Slide layouts that recur: code beside its runs, code above them, prose beside a picture."""

from counterweight.components import Component
from counterweight.elements import AnyElement
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.run_pane import run_pane
from whats_new.slides import SlideProps


def code_beside_runs(props: SlideProps, *code: Component | AnyElement) -> Div:
    """
    Code on the left at its natural width, and the slide's runs stacked in the space on the right.
    Prose under the code wraps to the code's width rather than widening the column.
    """
    return Div(
        style=row | fill(1) | gap(1),
        children=(
            # min_width(0) lets the column shrink below its prose's longest line, so the prose wraps.
            Div(style=col | gap(1) | min_width(0), children=code),
            run_pane(props, vertical=True, style=min_width(RUNS_MIN_WIDTH)),
        ),
    )


RUNS_MIN_WIDTH = 30


def code_above_runs(props: SlideProps, *code: Component | AnyElement) -> Div:
    """Code across the top, and the slide's runs side by side beneath it."""
    return Div(style=col | fill(1) | gap(1), children=(*code, run_pane(props)))


def stack(*children: Component | AnyElement) -> Div:
    """Children top to bottom, a blank line apart."""
    return Div(style=col | fill(1) | gap(1), children=children)


def notes_beside_code_above_runs(
    props: SlideProps, code: Component | AnyElement, *notes: Component | AnyElement
) -> Div:
    """Code with notes beside it across the top, and the slide's runs side by side beneath, at full width."""
    return Div(
        style=col | fill(1) | gap(1),
        children=(
            Div(style=row | gap(2) | shrink(0), children=(code, Div(style=col | gap(1) | fill(1), children=notes))),
            run_pane(props),
        ),
    )
