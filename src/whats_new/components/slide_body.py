"""
A slide's content with the state its examples share: their edits, which its runs execute,
and the keys that move between the editors and the run pane.
"""

from collections.abc import Callable

from counterweight.components import component
from counterweight.controls import FocusNext
from counterweight.elements import Div
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.focus import FocusHandle
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles.utilities import *

from whats_new.components.code import read_example
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import SlideProps

NO_EDITS: frozendict[str, str] = frozendict()


@component
def slide_body(slide: Slide, step: int, is_live: bool, host: Host) -> Div:
    """
    `slide`'s content at `step`, holding its edits until it unmounts, so `r` or leaving the slide undoes them.

    `e` or Ctrl+X moves into the slide's first editor, from the run pane, which claims neither,
    and Tab, which an editor doesn't claim, moves on to the next one, as unclaimed Tab does anywhere.
    An editor claims Ctrl+X to leave; Escape, which it doesn't claim, leaves too, outside a browser that keeps it.
    """
    edits, set_edits = use_state(NO_EDITS)
    runs_focus, _ = use_state(FocusHandle)

    def edit(name: str, change: Callable[[str], str]) -> None:
        set_edits(lambda current: current | {name: change(current.get(name, read_example(name)))})

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key="e" | Key.ControlX):
                return FocusNext(within=receiver.subtree)
            case KeyPressed(key=Key.Escape):
                return props.leave_editor
            case _:
                return None

    props = SlideProps(
        step=step,
        is_live=is_live,
        host=host,
        runs=slide.runs,
        edits=edits,
        edit=edit,
        runs_focus=runs_focus,
    )
    return Div(style=col | fill(1) | justify_children_center, on_input=on_input, children=(slide.content(props),))
