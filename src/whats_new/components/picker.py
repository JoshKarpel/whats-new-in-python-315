"""
The pickers keys open: the function keys' F4 code theme, F6 slide transition, F7 grid transition and F8 speed, and the Tachyon
stage's workload and profiler mode. Each is an autocomplete field over its parent's top right corner, as in counterweight's autocomplete
cookbook. Typing narrows the list of options, Down and Up move the highlight, Enter or Tab chooses the highlighted
option, and Escape closes it unchanged. Either way, focus goes back to the slide.

A picker's options can come in sections, each under a bar naming it. A bar is chosen as an option is, by its title,
so whatever the picker sets decides what choosing it means, such as F7's one of that section at random.
"""

import glob
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from fnmatch import fnmatchcase
from functools import partial

from counterweight.components import component
from counterweight.controls import AnyControl
from counterweight.controls import FocusOn
from counterweight.controls import ScrollIntoView
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.events import response_controls
from counterweight.focus import ElementHandle
from counterweight.focus import FocusHandle
from counterweight.handlers import first
from counterweight.handlers import focus_receiver_on_press
from counterweight.handlers import on_click
from counterweight.handlers import scroll_on_wheel
from counterweight.headless import use_text_input
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles import Color
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.look import dim
from whats_new.components.look import highlight

SHOWN_OPTIONS = 10
"""How many options the list shows at once; it scrolls the rest."""
WIDTH = 28
"""The narrowest a picker is; one with longer options or descriptions widens to fit them on one line each."""
PICKER_BACKGROUND = Color.from_hex("#0f172a")
"""Opaque, so the slide under the picker doesn't show through it."""
CURSOR = (text_color("slate", 900) | text_bg("sky", 300)).text_style
CURRENT = highlight


def matches(text: str, options: tuple[str, ...]) -> tuple[str, ...]:
    """
    The options the typed letters appear in, in order, with anything between them, so `nd` matches `nord-darker`;
    every option while nothing is typed. The one the text names exactly comes first, and the rest keep their order.
    Letters are escaped, so a typed `[` matches itself.
    """
    pattern = f"*{'*'.join(glob.escape(letter) for letter in text.lower())}*"
    found = tuple(option for option in options if fnmatchcase(option.lower(), pattern))
    # The option named exactly first, so typing a whole name and Enter chooses it, whatever else it spells.
    return tuple(sorted(found, key=lambda option: option.lower() != text.lower()))


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    highlighted: int
    """The highlighted option's place among the matches, reset to the first whenever the text changes."""

    def edited(self, text: str) -> Completion:
        return self if text == self.text else Completion(text=text, highlighted=0)


@dataclass(frozen=True, slots=True)
class Option:
    """One thing a picker offers: typing matches its `name`, and its `description`, if any, shows under it."""

    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class Section:
    """
    A run of a picker's options, under a bar naming it with its `title` and saying what choosing the bar does
    (`about`), or under nothing, without a title. The bar is chosen as an option is, by its title.
    """

    title: str | None
    options: tuple[Option, ...]
    about: str = ""

    @property
    def bar(self) -> str:
        """The bar's text, before the rule that runs it on to the picker's edge."""
        return f"── {self.title} ─ {self.about} " if self.about else f"── {self.title} "


@dataclass(frozen=True, slots=True)
class Choice:
    """
    What a picker offers, in `sections`, and how it's labeled: `label` heads it, and `key` names the key that opens it.
    """

    label: str
    sections: tuple[Section, ...]
    key: str

    @classmethod
    def listing(cls, label: str, options: tuple[Option, ...], key: str) -> Choice:
        """A picker offering `options` in one run, under no bar."""
        return cls(label=label, sections=(Section(title=None, options=options),), key=key)

    @property
    def options(self) -> tuple[Option, ...]:
        return tuple(option for section in self.sections for option in section.options)

    @property
    def bars(self) -> frozendict[str, Section]:
        """The titled sections, by the title choosing their bar chooses."""
        return frozendict({section.title: section for section in self.sections if section.title is not None})

    @property
    def names(self) -> tuple[str, ...]:
        """Everything the picker can choose, in the order it lists them: each bar's title ahead of its options."""
        return tuple(
            name
            for section in self.sections
            for name in (
                *(() if section.title is None else (section.title,)),
                *(option.name for option in section.options),
            )
        )

    @property
    def is_described(self) -> bool:
        return any(option.description for option in self.options)

    @property
    def inner_width(self) -> int:
        """Wide enough for the label, each bar, and each option and description on a line of its own."""
        lines = (
            self.label,
            HINT,
            *(f"▸{section.bar}──" for section in self.bars.values()),
            *(f"▸ {option.name}" for option in self.options),
            *(f"  {option.description}" for option in self.options),
        )
        return max(WIDTH - 4, max(len(line) for line in lines))

    @property
    def width(self) -> int:
        """`inner_width`, and the border and padding around it."""
        return 4 + self.inner_width


HINT = "↑ ↓ · Enter · Esc closes"


@dataclass(frozen=True, slots=True, eq=False)
class PickerHandles:
    """
    A picker's handles, which whatever opens it holds in its `Picking`, so the key that opens it can act on it
    in the frame it opens: its field's focus handle, and the element handle of its highlighted option.
    """

    focus: FocusHandle
    highlighted: ElementHandle

    @classmethod
    def fresh(cls) -> PickerHandles:
        """New handles, naming no element until a picker is given them."""
        return cls(focus=FocusHandle(), highlighted=ElementHandle())


@dataclass(frozen=True, slots=True, eq=False)
class Picking:
    """
    One opening of a picker: what it offers, and handles of its own. A key that opens another picker while one is
    open focuses the new one in the frame the open one unmounts in, so a handle the two shared would still name
    the open one, and focus would leave with it.
    """

    choice: Choice
    handles: PickerHandles = field(default_factory=PickerHandles.fresh)

    @property
    def key(self) -> str:
        return f"picker-{self.choice.key}"

    def opened(self) -> tuple[AnyControl, ...]:
        """
        What the key that opens the picker returns: focus on its field, since `auto_focus` wouldn't take focus from
        the slide, which always has it, and its current option scrolled into view, which can be past the rows
        the list shows. Returned with the state change that opens it, both apply to the frame it opens in.
        """
        return FocusOn(self.handles.focus), ScrollIntoView(self.handles.highlighted, block="nearest")


@component
def picker(
    choice: Choice,
    current: str | None,
    choose: Callable[[str], object],
    close: Callable[[], object],
    leave: AnyControl,
    handles: PickerHandles,
) -> Div:
    """
    Opens with the field empty and `current`, the name of one of `choice`'s options, marked and highlighted,
    or the first option highlighted if there's no `current`. Choosing an option calls `choose` with its name,
    and choosing or Escape calls `close` and does `leave`, which gives focus back to the slide.
    `handles` are a `Picking`'s, and the key that opens it returns that `Picking.opened()`,
    which focuses it and shows its current option.
    """
    names = choice.names
    completion, set_completion = use_state(
        Completion(text="", highlighted=0 if current is None else names.index(current))
    )
    highlighted_match = handles.highlighted

    def edit(edit_text: Callable[[str], str]) -> str:
        return set_completion(lambda c: c.edited(edit_text(c.text))).text

    field = use_text_input(completion.text, edit, handle=handles.focus)
    bars = choice.bars
    # A bar is matched by its own title alone, not its options', so typing an option's name doesn't highlight its bar.
    shown = matches(completion.text, names)
    descriptions = {option.name: option.description for option in choice.options}
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

    def row_of(name: str, style: Style) -> tuple[Chunk, ...]:
        if (section := bars.get(name)) is not None:
            return bar_row(section, style, choice.inner_width, is_current=name == current)
        return option_row(name, descriptions[name] if choice.is_described else None, style, is_current=name == current)

    rows = tuple(
        Text(
            content=row_of(
                name,
                (text_bg("sky", 800) if index == highlighted else default) | (CURRENT if name == current else default),
            ),
            style=text_wrap_none,
            handle=highlighted_match if index == highlighted else None,
            on_input=on_click(partial(chosen, name)),
        )
        for index, name in enumerate(shown)
    )
    return Div(
        style=position_absolute
        | inset_right(1)
        | inset_top(1)
        | z(1)
        | width(choice.width)
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
                style=col | max_height(SHOWN_OPTIONS * (2 if choice.is_described else 1)) | overflow_y_scroll,
                on_input=scroll_on_wheel(1),
                children=rows or (Text(content="nothing matches", style=dim),),
            ),
            Text(content=HINT, style=dim | text_wrap_none),
        ),
    )


def bar_row(section: Section, style: Style, width: int, is_current: bool) -> tuple[Chunk, ...]:
    """
    A section's bar: a rule across the picker `width` cells wide with its title and what choosing it does in it,
    marked if it's the current choice. One line, even in a described picker.
    """
    text = f"{'▸' if is_current else '─'}{section.bar}"
    return (
        Chunk(content=text, style=style | text_bold),
        Chunk(content="─" * (width - len(text)), style=style | dim),
    )


def option_row(name: str, description: str | None, style: Style, is_current: bool) -> tuple[Chunk, ...]:
    """
    An option's row: its name, marked if it's the current one, and, in a described picker, its description under it,
    blank if it has none, so every option takes the same two lines. A chunk ignores its text's style, so each gets it.
    """
    line = Chunk(content=f"{'▸' if is_current else ' '} {name}", style=style)
    if description is None:
        return (line,)
    return (line, Chunk.newline(), Chunk(content=f"  {description}", style=style | dim))
