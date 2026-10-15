"""Code on screen, read from the example files the runs execute, so display and execution can't drift."""

from functools import cache

from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.highlighting import code_block
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.look import code_border
from whats_new.components.look import dim
from whats_new.runs import EXAMPLES


@cache
def read_example(name: str) -> str:
    """The text of the example file `name`, without its trailing newline, which would show as a blank last line."""
    return (EXAMPLES / name).read_text().rstrip("\n")


def code_example(name: str, style: Style = default, start: str | None = None, stop: str | None = None) -> Text:
    """
    The example file `name`, highlighted, in the deck's code border,
    for an example whose imports or harness aren't the point, from the first line that starts with `start`,
    and up to (not including) the first line after it that starts with `stop`.

    Raises:
        ValueError: If no line starts with `start` or `stop`, so an edit to the example can't silently show
            the wrong part of it.
    """
    lines = read_example(name).splitlines()
    first = 0 if start is None else first_line(lines, start, 0, name)
    last = len(lines) if stop is None else first_line(lines, stop, first + 1, name)
    return code_snippet("\n".join(lines[first:last]).rstrip("\n"), style)


def first_line(lines: list[str], prefix: str, after: int, name: str) -> int:
    """The index of the first line from `after` on that starts with `prefix`."""
    for index in range(after, len(lines)):
        if lines[index].startswith(prefix):
            return index
    raise ValueError(f"no line in {name} starts with {prefix!r}")


def code_snippet(text: str, style: Style = default, language: str = "python") -> Text:
    """`text` highlighted as `language`, in the deck's code border: for code that isn't run, such as a shell line."""
    return code_block(
        text, language, style=code_border | pad_x(1) | shrink(0) | align_self_start | text_wrap_none | style
    )


def labeled(label: str, block: Text) -> Div:
    """`block` with `label`, such as its file name, above it."""
    return Div(style=col | shrink(0), children=(Text(content=label, style=dim | pad_x(1)), block))
