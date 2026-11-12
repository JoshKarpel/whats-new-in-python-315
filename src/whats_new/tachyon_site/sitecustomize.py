"""
Loaded only by the Tachyon stage's profiler, whose environment puts this directory on `PYTHONPATH`,
so the command the stage runs (and the loop diagram shows) stays plain Tachyon. It fits Tachyon's live TUI to the stage
in two ways, each wrapping a method in Tachyon's own (pinned) source, so a Tachyon that changes that method quietly
undoes the fit; `tests/test_tachyon.py` exercises each to catch that.

Tachyon marks its top three functions with medal emoji, two cells wide,
and zellij web measures them wrongly (zellij-org/zellij#5718), which knocks the rest of their row,
and anything the deck draws over it, out of line. This draws each medal as `#1` and so on instead:
the same two cells, so Tachyon's layout doesn't move. Drop that part once zellij measures them.

Tachyon shortens a path by stripping the stdlib and site-packages from its front, but the deck runs from its source
tree, so the deck's own frames showed as the whole absolute path, cut off at the pane's right edge.
This strips the directory the deck's package is in as well, so they show as `whats_new/workloads.py:42`.
"""

import profiling.sampling.live_collector.collector as collector
import profiling.sampling.live_collector.widgets as widgets
from pathlib import Path

MEDALS = {"🥇": "#1", "🥈": "#2", "🥉": "#3"}
DECK_SOURCE = str(Path(__file__).resolve().parents[2])
"""The directory the `whats_new` package is in: `src/` in a checkout, site-packages in an installed deck."""

draw = widgets.Widget.add_str
common_path_prefixes = collector.LiveStatsCollector._get_common_path_prefixes


def add_str(self: widgets.Widget, line: int, col: int, text: str, attr: int = 0) -> None:
    """Tachyon's own `add_str`, with any medal in `text` replaced by its rank."""
    for medal, rank in MEDALS.items():
        text = text.replace(medal, rank)
    draw(self, line, col, text, attr)


def path_prefixes(self: collector.LiveStatsCollector) -> list[str]:
    """Tachyon's own prefixes to strip, and the deck's source directory, which no prefix of theirs contains."""
    return [DECK_SOURCE, *common_path_prefixes(self)]


widgets.Widget.add_str = add_str
collector.LiveStatsCollector._get_common_path_prefixes = path_prefixes
