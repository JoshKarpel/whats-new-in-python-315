"""
Code on screen, read from the example files the runs execute, so display and execution can't drift.

An example is also an editor, on a slide with runs: Tab moves into it, and the slide's runs execute the edited text.
"""

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from functools import lru_cache

from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import AnyControl
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.handlers import first
from counterweight.headless import use_text_area
from counterweight.highlighting import code_block
from counterweight.highlighting import code_style
from counterweight.highlighting import highlight
from counterweight.keys import Key
from counterweight.styles import CellStyle
from counterweight.styles import Style
from counterweight.styles.utilities import *
from counterweight.widgets import TextFieldStyles
from pygments.styles import get_all_styles
from pygments.styles import get_style_by_name

from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import code_border
from whats_new.components.look import dim
from whats_new.runs import EXAMPLES
from whats_new.slides import SlideProps

CODE_THEME = "github-dark"
"""The Pygments style code is highlighted in until F4 picks another."""


def has_dark_background(theme: str) -> bool:
    """
    Whether the Pygments style `theme` has a dark background, by its relative luminance (as WCAG defines it).
    Pygments' styles split cleanly: the dark ones are at most 0.05, the light ones at least 0.8.
    """
    hex_color = get_style_by_name(theme).background_color.lstrip("#")
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2] < 0.5


CODE_THEMES = tuple(sorted(theme for theme in get_all_styles() if has_dark_background(theme)))
"""The Pygments styles F4's picker offers: the dark ones, since the deck is dark."""

CURSOR = TextFieldStyles().cursor

EDITING_BORDER = Style(border_style=CellStyle(foreground=PYTHON_YELLOW))
INVALID_BORDER = border_color("red", 400)

UNWRAPPED = 10_000
"""
The row width the editor wraps at, wider than any line, so the code never wraps:
the box grows to its longest line instead, as it does for code that isn't being edited.
"""


@cache
def read_example(name: str) -> str:
    """The text of the example file `name`, without its trailing newline, which would show as a blank last line."""
    return (EXAMPLES / name).read_text().rstrip("\n")


@dataclass(frozen=True, slots=True)
class Excerpt:
    """
    The lines of the example `name` a slide shows: all but `hidden_above` lines at its top and `hidden_below` at its end.
    The counts hold while the shown lines are edited, since the hidden lines can't be.
    """

    name: str
    hidden_above: int
    hidden_below: int

    def shown(self, source: str) -> str:
        lines = source.split("\n")
        return "\n".join(lines[self.hidden_above : len(lines) - self.hidden_below])

    def replaced(self, source: str, shown: str) -> str:
        """`source` with its shown lines replaced by `shown`."""
        lines = source.split("\n")
        return "\n".join((*lines[: self.hidden_above], shown, *lines[len(lines) - self.hidden_below :]))


def excerpt(name: str, source: str, start: str | None, stop: str | None) -> Excerpt:
    """
    The lines of `source` from the first that starts with `start`, up to (not including) the first after it that
    starts with `stop`, without the blank lines that would end it, for an example whose imports or harness aren't the
    point.

    Raises:
        ValueError: If no line starts with `start` or `stop`, so an edit to the example can't silently show
            the wrong part of it.
    """
    lines = source.split("\n")
    first_shown = 0 if start is None else first_line(lines, start, 0, name)
    end = len(lines) if stop is None else first_line(lines, stop, first_shown + 1, name)
    while end > first_shown + 1 and not lines[end - 1]:
        end -= 1
    return Excerpt(name=name, hidden_above=first_shown, hidden_below=len(lines) - end)


def first_line(lines: list[str], prefix: str, after: int, name: str) -> int:
    """The index of the first line from `after` on that starts with `prefix`."""
    for index in range(after, len(lines)):
        if lines[index].startswith(prefix):
            return index
    raise ValueError(f"no line in {name} starts with {prefix!r}")


def code_example(
    props: SlideProps, name: str, style: Style = default, start: str | None = None, stop: str | None = None
) -> Component:
    """
    The example file `name`, highlighted, in the deck's code border, from the line that starts with `start`
    to the one before the line that starts with `stop` (see `excerpt`), as the slide has edited it.
    """
    source = read_example(name)
    return code_editor(
        excerpt(name, source, start, stop),
        props.edits.get(name, source),
        props.edit,
        props.leave_editor,
        # Editing a slide with nothing to run would change nothing, and it would have no run pane to Tab back to.
        props.is_live and bool(props.runs),
        props.code_theme,
        style,
    )


@component
def code_editor(
    excerpt: Excerpt,
    source: str,
    edit: Callable[[str, Callable[[str], str]], None],
    leave: AnyControl,
    is_editable: bool,
    theme: str,
    style: Style,
) -> Div:
    """
    The shown lines of `source`, the example's text, which typing edits while the editor is focused,
    with a yellow border while it is, and a red one whenever the whole file, hidden lines included, isn't valid Python.
    Escape does `leave`. Tab isn't an edit, so it bubbles out, to move focus on to the next editor or the run pane;
    it's the way out that works in a browser, which keeps Escape for itself.
    """
    shown = excerpt.shown(source)

    def set_shown(change: Callable[[str], str]) -> None:
        edit(excerpt.name, lambda latest: excerpt.replaced(latest, change(excerpt.shown(latest))))

    field = use_text_area(shown, set_shown, width=UNWRAPPED, enter_inserts_newline=True, is_focusable=is_editable)

    def on_leave(event: InputEvent, receiver: Receiver) -> InputResponse:
        if receiver.is_focused and isinstance(event, KeyPressed) and event.key == Key.Escape:
            return leave
        return None

    is_focused = field.focus.is_focused
    chunks = highlight(shown, "python", theme)
    border = INVALID_BORDER if not compiles(source) else EDITING_BORDER if is_focused else default
    return Div(
        style=code_style(theme) | code_border | pad_x(1) | shrink(0) | style | border,
        on_input=first(on_leave, field.on_input, field.on_press),
        children=(
            Text(
                content=with_cursor(chunks, field.cursor, field.at_cursor) if is_focused else chunks,
                style=code_style(theme) | text_wrap_none,
            ),
        ),
    )


def with_cursor(chunks: tuple[Chunk, ...], cursor: int, at_cursor: str) -> tuple[Chunk, ...]:
    """
    `chunks` with the cursor drawn on the `at_cursor` cluster `cursor` code points in,
    or on a space inserted there when the cursor is at the end of a line or of the text, which has no cell to draw it on.
    """
    text = "".join(chunk.content for chunk in chunks)
    if not text.startswith(at_cursor, cursor):
        return (*clipped(chunks, 0, cursor), Chunk(content=" ", style=CURSOR), *clipped(chunks, cursor, len(text)))
    end = cursor + len(at_cursor)
    return (*clipped(chunks, 0, cursor), *clipped(chunks, cursor, end, CURSOR), *clipped(chunks, end, len(text)))


def clipped(chunks: tuple[Chunk, ...], start: int, stop: int, over: CellStyle = CellStyle()) -> tuple[Chunk, ...]:
    """The parts of `chunks` from code point `start` to `stop` of their joined text, with `over` merged over each."""
    parts: list[Chunk] = []
    offset = 0
    for chunk in chunks:
        low, high = max(start, offset), min(stop, offset + len(chunk.content))
        if low < high:
            parts.append(Chunk(content=chunk.content[low - offset : high - offset], style=chunk.style | over))
        offset += len(chunk.content)
    return tuple(parts)


@lru_cache(maxsize=2**6)
def compiles(source: str) -> bool:
    """
    Whether `source` is valid Python to the deck's own 3.15, which the editor checks on every keystroke.
    Cached, since a slide re-renders its editors for an edit to any of them.
    """
    # A SyntaxWarning (an invalid escape, say) would print over the deck.
    with warnings.catch_warnings(action="ignore"):
        try:
            compile(source, "<example>", "exec", dont_inherit=True)
        except SyntaxError:
            return False
    return True


def code_snippet(props: SlideProps, text: str, style: Style = default, language: str = "python") -> Text:
    """`text` highlighted as `language`, in the deck's code border: for code that isn't run, such as a shell line."""
    return code_block(
        text, language, props.code_theme, style=code_border | pad_x(1) | shrink(0) | text_wrap_none | style
    )


def labeled(label: str, block: Text | Component) -> Div:
    """`block` with `label`, such as its file name, above it."""
    return Div(style=col | shrink(0), children=(Text(content=label, style=dim | pad_x(1)), block))
