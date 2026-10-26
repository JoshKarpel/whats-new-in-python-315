"""
A slide's content with the state its examples share: their edits, which its runs execute,
and the keys that move between the editors and the run pane.
"""

from collections.abc import Callable

from counterweight.components import component
from counterweight.elements import Div
from counterweight.focus import FocusHandle
from counterweight.handlers import tab_focus
from counterweight.hooks import use_state
from counterweight.styles.utilities import *

from whats_new.components.code import read_example
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import SlideProps

NO_EDITS: frozendict[str, str] = frozendict()


@component
def slide_body(slide: Slide, step: int, is_live: bool, host: Host, code_theme: str, slide_focus: FocusHandle) -> Div:
    """
    `slide`'s content at `step`, holding its edits until it unmounts, so `r` or leaving the slide undoes them.

    Tab moves focus through the slide's editors, then its run pane, which comes after them in every layout,
    and wraps back to the first editor; Shift+Tab goes the other way. Neither an editor nor the run pane claims Tab.
    """
    edits, set_edits = use_state(NO_EDITS)

    def edit(name: str, change: Callable[[str], str]) -> str:
        return set_edits(lambda current: current | {name: change(current.get(name, read_example(name)))})[name]

    props = SlideProps(
        step=step,
        is_live=is_live,
        host=host,
        code_theme=code_theme,
        runs=slide.runs,
        edits=edits,
        edit=edit,
        slide_focus=slide_focus,
    )
    return Div(style=col | fill(1) | justify_children_center, on_input=tab_focus, children=(slide.content(props),))
