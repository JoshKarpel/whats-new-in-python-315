"""A live Python 3.15 REPL embedded in a slide, started by a key, for the new REPL's colors and completions."""

from counterweight.components import component
from counterweight.controls import FocusOn
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.focus import FocusHandle
from counterweight.hooks import use_focus
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles.utilities import *
from counterweight.widgets import terminal

from whats_new.components.look import dim
from whats_new.runs import Interpreter
from whats_new.slides import SlideProps


@component
def repl_pane(props: SlideProps) -> Div:
    """
    `s` starts `python3.15` in a pane and hands it the keyboard; Ctrl+B takes the keyboard back,
    and `s` again (from the deck) starts a fresh one. Leaving the slide hangs it up.
    """
    focus = use_focus(auto_focus=props.is_live, is_focusable=props.is_live)
    pane, _ = use_state(FocusHandle)
    session, set_session = use_state(0)

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key="s"):
                set_session(lambda n: n + 1)
                return (FocusOn(pane),)
            case _:
                return None

    def take_back(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key=Key.ControlB):
                return (FocusOn(focus.handle),)
            case _:
                return None

    interpreter = str(props.host.interpreters.paths[Interpreter.PY315])
    child = (
        terminal(
            (interpreter,),
            style=fill(1),
            intercept=take_back,
            handle=pane,
            in_focus_order=False,
            env=frozendict(PYTHONSTARTUP=""),
        ).with_key(f"repl-{session}")
        if session
        else Text(
            content="s starts a Python 3.15 REPL here; Ctrl+B takes the keyboard back",
            style=dim | border | border_lightrounded | border_color("slate", 600) | fill(1) | text_justify_center,
        )
    )
    return Div(style=col | fill(1), on_input=on_input, children=(child,))
