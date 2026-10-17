"""
Loaded only by the Tachyon stage's profiler, whose environment puts this directory on `PYTHONPATH`,
so the command the stage runs (and the loop diagram shows) stays plain Tachyon.

Tachyon's live TUI marks its top three functions with medal emoji, two cells wide,
and zellij web measures them wrongly (zellij-org/zellij#5718), which knocks the rest of their row,
and anything the deck draws over it, out of line. This draws each medal as `#1` and so on instead:
the same two cells, so Tachyon's layout doesn't move. Delete this directory once zellij measures them.

It wraps `Widget.add_str` in Tachyon's own (pinned) source, so a Tachyon that changes how it draws the medals
quietly brings them back; `tests/test_tachyon.py` draws the row to catch that.
"""

import profiling.sampling.live_collector.widgets as widgets

MEDALS = {"🥇": "#1", "🥈": "#2", "🥉": "#3"}

draw = widgets.Widget.add_str


def add_str(self: widgets.Widget, line: int, col: int, text: str, attr: int = 0) -> None:
    """Tachyon's own `add_str`, with any medal in `text` replaced by its rank."""
    for medal, rank in MEDALS.items():
        text = text.replace(medal, rank)
    draw(self, line, col, text, attr)


widgets.Widget.add_str = add_str
