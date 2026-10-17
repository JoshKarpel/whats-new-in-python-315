"""
The pickers the function keys open, F3's slide transition and F4's code theme: an autocomplete field over the slide's
top right corner, as in counterweight's autocomplete cookbook. Typing narrows the list of options, Down and Up move
the highlight, Enter or Tab chooses the highlighted option, and Escape or the key that opened it closes it unchanged.
Either way, focus goes back to the slide.
"""

import glob
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace
from fnmatch import fnmatchcase
from functools import partial

from counterweight.components import component
from counterweight.controls import AnyControl
from counterweight.controls import ScrollIntoView
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.events import response_controls
from counterweight.focus import FocusHandle
from counterweight.handlers import first
from counterweight.handlers import focus_receiver_on_press
from counterweight.handlers import on_click
from counterweight.handlers import scroll_on_wheel
from counterweight.headless import use_text_input
from counterweight.hooks import ElementHandle
from counterweight.hooks import use_controls
from counterweight.hooks import use_effect
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import dim

SHOWN_ROWS = 10
"""How many options the list shows at once; it scrolls the rest."""
WIDTH = 28
PICKER_BACKGROUND = Color.from_hex("#0f172a")
"""Opaque, so the slide under the picker doesn't show through it."""
CURSOR = (text_color("slate", 900) | text_bg("sky", 300)).text_style
CURRENT = Style(text_style=CellStyle(foreground=PYTHON_YELLOW, bold=True))


def matches(text: str, options: tuple[str, ...]) -> tuple[str, ...]:
    """
    The options the typed letters appear in, in order, with anything between them, so `nd` matches `nord-darker`;
    every option while nothing is typed. Letters are escaped, so a typed `[` matches itself.
    """
    pattern = f"*{'*'.join(glob.escape(letter) for letter in text.lower())}*"
    return tuple(option for option in options if fnmatchcase(option.lower(), pattern))


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    highlighted: int
    """The highlighted option's place among the matches, reset to the first whenever the text changes."""

    def edited(self, text: str) -> Completion:
        return self if text == self.text else Completion(text=text, highlighted=0)


@dataclass(frozen=True, slots=True)
class Choice:
    """What a picker offers and how it's labeled: `label` heads it, and `key` names the key that closes it."""

    label: str
    options: tuple[str, ...]
    key: str


@component
def picker(
    choice: Choice,
    current: str,
    choose: Callable[[str], None],
    close: Callable[[], None],
    leave: AnyControl,
    handle: FocusHandle,
) -> Div:
    """
    Opens with the field empty and `current`, one of `choice`'s options, highlighted. Choosing an option calls
    `choose` with it, and choosing or Escape calls `close` and does `leave`, which gives focus back to the slide.
    The field's focus handle is `handle`, which the opening key focuses as it opens the picker:
    `auto_focus` wouldn't take focus from the slide, which always has it.
    """
    options = choice.options
    completion, set_completion = use_state(Completion(text="", highlighted=options.index(current)))
    highlighted_match, _ = use_state(ElementHandle)
    send = use_controls()

    # The current option can be past the rows the list shows; an input handler would return this control,
    # but nothing has been pressed yet as the picker opens.
    async def show_current() -> None:
        send(ScrollIntoView(highlighted_match, block="nearest"))

    use_effect(show_current, deps=())

    def edit(edit_text: Callable[[str], str]) -> None:
        set_completion(lambda c: c.edited(edit_text(c.text)))

    field = use_text_input(completion.text, edit, handle=handle)
    shown = matches(completion.text, options)
    highlighted = completion.highlighted

    def chosen(option: str) -> InputResponse:
        choose(option)
        close()
        return leave

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        highlighted_in_view = ScrollIntoView(highlighted_match, block="nearest")
        match event:
            case KeyPressed(key=Key.Down) if shown:
                set_completion(lambda c: replace(c, highlighted=(c.highlighted + 1) % len(shown)))
            case KeyPressed(key=Key.Up) if shown:
                set_completion(lambda c: replace(c, highlighted=(c.highlighted - 1) % len(shown)))
            case KeyPressed(key=Key.Enter | Key.Tab) if shown:
                return chosen(shown[highlighted])
            case KeyPressed(key=Key.Escape):
                close()
                return leave
            case _:
                if (edited := response_controls(field.on_input(event, receiver))) is None:
                    return None
                return (*edited, highlighted_in_view)
        return highlighted_in_view

    rows = tuple(
        Text(
            content=f"{'▸' if option == current else ' '} {option}",
            style=text_wrap_none
            | (text_bg("sky", 800) if index == highlighted else default)
            | (CURRENT if option == current else default),
            handle=highlighted_match if index == highlighted else None,
            on_input=on_click(partial(chosen, option)),
        )
        for index, option in enumerate(shown)
    )
    return Div(
        style=position_absolute
        | inset_right(1)
        | inset_top(1)
        | z(1)
        | width(WIDTH)
        | col
        | border
        | border_lightrounded
        | border_color("amber", 300)
        | pad_x(1)
        | Style(padding_color=PICKER_BACKGROUND, content_color=PICKER_BACKGROUND),
        on_input=first(on_input, focus_receiver_on_press),
        children=(
            Text(content=choice.label, style=dim),
            Div(
                style=row | overflow_x_scroll | stick_to_end_x | text_bg("slate", 700),
                on_input=field.on_press,
                children=(
                    Text(content="> ", style=text_wrap_none),
                    Text(content=field.before_cursor, style=text_wrap_none),
                    Text(
                        content=field.at_cursor,
                        style=text_wrap_none | Style(text_style=CURSOR),
                        handle=field.cursor_cell,
                    ),
                    Text(content=field.after_cursor, style=text_wrap_none),
                ),
            ),
            Div(
                style=col | max_height(SHOWN_ROWS) | overflow_y_scroll,
                on_input=scroll_on_wheel(1),
                children=rows or (Text(content="nothing matches", style=dim),),
            ),
            Text(content=f"↑ ↓ · Enter · {choice.key} closes", style=dim | text_wrap_none),
        ),
    )
