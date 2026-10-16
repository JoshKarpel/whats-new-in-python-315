"""Editing examples on a slide: which lines an editor shows, how it draws its cursor, and where its runs find the edit."""

import asyncio
from pathlib import Path

import pytest
from counterweight.app import app
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Chunk
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame
from counterweight.styles import CellStyle

from whats_new.checkpoint import Checkpoint
from whats_new.components.code import CURSOR
from whats_new.components.code import compiles
from whats_new.components.code import excerpt
from whats_new.components.code import with_cursor
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.runs import EXAMPLES
from whats_new.runs import copy_examples
from whats_new.runs import rehomed
from whats_new.size import PRESENTING

SOURCE = "import sys\n\ndef shown():\n    pass\n\n\ndef hidden():\n    pass"
BOLD = CellStyle(bold=True)


def test_excerpt_shows_from_start_to_before_stop_without_trailing_blank_lines() -> None:
    assert excerpt("x.py", SOURCE, "def shown", "def hidden").shown(SOURCE) == "def shown():\n    pass"


def test_excerpt_replaced_keeps_the_hidden_lines() -> None:
    lines = excerpt("x.py", SOURCE, "def shown", "def hidden")

    edited = lines.replaced(SOURCE, "def shown():\n    return 1\n\nshown()")

    assert edited == "import sys\n\ndef shown():\n    return 1\n\nshown()\n\n\ndef hidden():\n    pass"
    assert lines.shown(edited) == "def shown():\n    return 1\n\nshown()"


def test_excerpt_raises_for_a_start_no_line_has() -> None:
    with pytest.raises(ValueError, match="'class Gone'"):
        excerpt("x.py", SOURCE, "class Gone", None)


@pytest.mark.parametrize(
    ("cursor", "at_cursor", "expected"),
    [
        (1, "b", (Chunk(content="a"), Chunk(content="b", style=BOLD | CURSOR), Chunk(content="\ncd", style=BOLD))),
        (
            2,
            " ",
            (
                Chunk(content="a"),
                Chunk(content="b", style=BOLD),
                Chunk(content=" ", style=CURSOR),
                Chunk(content="\ncd", style=BOLD),
            ),
        ),
        (5, " ", (Chunk(content="a"), Chunk(content="b\ncd", style=BOLD), Chunk(content=" ", style=CURSOR))),
    ],
    ids=["on a character", "at the end of a line", "at the end of the text"],
)
def test_with_cursor_draws_the_cursor_cell(cursor: int, at_cursor: str, expected: tuple[Chunk, ...]) -> None:
    chunks = (Chunk(content="a"), Chunk(content="b\ncd", style=BOLD))

    assert with_cursor(chunks, cursor, at_cursor) == expected


@pytest.mark.parametrize(("source", "expected"), [("print(1)", True), ("print(", False), ("lazy import json", True)])
def test_compiles_judges_by_the_decks_own_grammar(source: str, expected: bool) -> None:
    assert compiles(source) is expected


def test_rehomed_points_paths_into_examples_at_the_copy(tmp_path: Path) -> None:
    argv = ("/usr/bin/python3.15", str(EXAMPLES / "harness" / "checkers.py"), "typing/disjoint.py", "--strict")

    assert rehomed(argv, tmp_path) == (
        "/usr/bin/python3.15",
        str(tmp_path / "harness" / "checkers.py"),
        "typing/disjoint.py",
        "--strict",
    )


def test_copy_examples_writes_edits_over_their_copies(tmp_path: Path) -> None:
    copy_examples(tmp_path, {"small/counter_xor.py": "print('edited')"})

    assert (tmp_path / "small" / "counter_xor.py").read_text() == "print('edited')\n"
    assert (tmp_path / "small" / "unpack.py").read_text() == (EXAMPLES / "small" / "unpack.py").read_text()


async def test_a_run_executes_the_edited_example(host: Host) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "frozendict: the mutable default, fixed")
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.25)

    def typed(text: str) -> tuple[KeyPressed, ...]:
        return tuple(KeyPressed(key=Key.Enter if character == "\n" else character) for character in text)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key=Key.Tab),
        *typed('\nprint("edited on stage")'),
        KeyPressed(key=Key.Tab),
        KeyPressed(key="1"),
        *(Screenshot(handler=settle) for _ in range(20)),
        Screenshot(handler=frames.append),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert "│edited on stage" in frames[0].text(ansi=False)


FIRST_EDITED = "json = NoneQ"
SECOND_EDITED = 'print(f"{"csv" in sys.modules=}")Q'


@pytest.mark.parametrize(
    ("keys", "edited_line"),
    [
        ((Key.Tab,), FIRST_EDITED),
        ((Key.Tab, Key.Tab), SECOND_EDITED),
        ((Key.Tab, Key.Tab, Key.Tab), None),
        ((Key.Tab, Key.Tab, Key.Tab, Key.Tab), FIRST_EDITED),
        ((Key.BackTab,), SECOND_EDITED),
    ],
    ids=[
        "Tab enters the first editor",
        "Tab moves on to the next",
        "Tab from the last goes back to the run pane",
        "Tab wraps around to the first",
        "Shift+Tab goes the other way",
    ],
)
async def test_tab_cycles_through_the_editors_and_the_run_pane(
    host: Host, keys: tuple[str, ...], edited_line: str | None
) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "Lazy imports: gotchas")
    frames: list[Frame] = []

    await app(
        root(SLIDES, host, Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            *(KeyPressed(key=key) for key in keys),
            KeyPressed(key="Q"),
            Screenshot(handler=frames.append),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )

    text = frames[0].text(ansi=False)
    if edited_line is None:
        # The run pane doesn't type.
        assert "Q" not in text
    else:
        # An editor's cursor starts at the end of its text, so the Q lands at the end of its last line.
        assert text.count("Q") == 1
        assert edited_line in text
