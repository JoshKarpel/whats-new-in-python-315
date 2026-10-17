"""
How the examples are laid out for the screen, which no formatter checks, since ruff skips `examples/`
and its formatter can't be told to put fewer than two blank lines between top-level definitions.
"""

from pathlib import Path

import pytest

from whats_new.runs import ROOT

EXAMPLES = sorted((ROOT / "examples").rglob("*.py"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[str(path.relative_to(ROOT / "examples")) for path in EXAMPLES])
def test_example_has_no_double_blank_lines(path: Path) -> None:
    """A slide has about 30 rows, so a second blank line between definitions takes one from the run box beneath."""
    assert "\n\n\n" not in path.read_text()
