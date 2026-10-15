"""
Runs every run declared on every slide and checks it does what the slide expects,
so an interpreter or checker bump that changes a demo's outcome fails here rather than on stage.
"""

import os
import subprocess

import pytest

from whats_new.deck import SLIDES
from whats_new.runs import Capability
from whats_new.runs import Interpreters
from whats_new.runs import Run

RUNS = [(slide.title, run) for slide in SLIDES for run in slide.runs]


@pytest.mark.parametrize(("title", "run"), RUNS, ids=[f"{title} [{run.label}]" for title, run in RUNS])
def test_run_does_what_its_slide_expects(
    title: str, run: Run, interpreters: Interpreters, capabilities: frozenset[Capability]
) -> None:
    if missing := run.needs - capabilities:
        pytest.skip(f"this machine doesn't allow {', '.join(sorted(need.value for need in missing))}")
    # Off a terminal, so the output is uncolored: the expectations are about what it says, not how it looks.
    result = subprocess.run(
        interpreters.argv(run),
        env={**os.environ, **run.env},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
        check=False,
    )
    assert run.expect.output in result.stdout, result.stdout
    assert result.returncode == run.expect.status, result.stdout
