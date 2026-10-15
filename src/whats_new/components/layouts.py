"""Slide layouts that recur: code above its runs, with or without notes beside it."""

from counterweight.components import Component
from counterweight.elements import AnyElement
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.run_pane import run_pane
from whats_new.slides import SlideProps

CENTERED_COLUMN = col | fill(1) | gap(1) | align_self_stretch | align_children_center | justify_children_center
"""
Children top to bottom, a blank line apart, centered both ways in the slide, as slides are unless that looks wrong.
A run box stretches across it anyway, and takes the height left over, which leaves nothing to center vertically.
"""


def code_above_runs(props: SlideProps, *code: Component | AnyElement) -> Div:
    """Code across the top, and the slide's run box beneath it."""
    return Div(style=CENTERED_COLUMN, children=(*code, run_pane(props)))


def side_by_side(*children: Component | AnyElement) -> Div:
    """`children` in a centered row, such as two examples, which wraps onto more rows if they don't fit across."""
    return Div(
        style=row | flex_wrap | justify_children_center | gap_width(2) | gap_height(1) | shrink(0), children=children
    )


def stack(*children: Component | AnyElement) -> Div:
    """Children top to bottom, a blank line apart, centered."""
    return Div(style=CENTERED_COLUMN, children=children)


def notes_beside_code_above_runs(
    props: SlideProps, code: Component | AnyElement, *notes: Component | AnyElement
) -> Div:
    """
    Code with notes (or a second example) beside it across the top, and the slide's run box beneath,
    at full width: the screen is wider than it is tall, so runs beside the code would squeeze both.
    The notes take their natural width, and wrap down to `NOTES_MIN_WIDTH` when the slide is too narrow for it:
    code wider than that leaves room for belongs in `code_above_runs`, with its notes under it.
    """
    return Div(
        style=CENTERED_COLUMN,
        children=(
            Div(
                # Across the slide, so the notes shrink to fit it rather than overflow, centered while they fit.
                style=row | gap_width(2) | shrink(0) | align_self_stretch | justify_children_center,
                children=(code, Div(style=col | gap(1) | shrink(1) | min_width(NOTES_MIN_WIDTH), children=notes)),
            ),
            run_pane(props),
        ),
    )


NOTES_MIN_WIDTH = 28
"""Narrower than this, a bullet wraps a word or two per line, and an inline code span splits mid-name."""
