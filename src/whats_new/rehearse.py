"""
The pre-talk check: everything about the presenting setup a script can confirm, then a checklist for the rest,
which happens in the presenting browser over zellij web. Meant for the day before, so problems surface then.
"""

import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

from whats_new.host import FlamegraphSite
from whats_new.runs import Interpreters

MANUAL = (
    "every deck key arrives through the browser and zellij's locked mode (Ctrl+G), Escape and Enter included",
    "F1 and F2 reach the deck; F2 is green at the presenting zoom",
    "clicking a thumbnail in the slide grid (d) reaches the deck",
    "the flamegraph URL on the Tachyon slide opens from a click",
    "PEP links open from a click",
    "the grapheme slide's n̈ draws as one cell, and its naive reversal puts the umlaut on the a",
    "the Tachyon pane redraws smoothly enough over the venue network",
)


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    run: Callable[[], str]


def interpreters() -> str:
    resolved = Interpreters.resolve()
    return ", ".join(f"{interpreter.value}" for interpreter in resolved.paths)


def flamegraph_site() -> str:
    return FlamegraphSite.resolve(os.environ).url("deck-flamegraph.html")


def profiler_attaches() -> str:
    """Tachyon dumps a child's stack, as the Tachyon stage's profiler attaches to the deck."""
    target = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        dump = subprocess.run(
            [sys.executable, "-m", "profiling.sampling", "dump", str(target.pid)],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    finally:
        target.kill()
        target.wait()
    if f"Stack dump for PID {target.pid}" not in dump.stdout:
        raise RuntimeError(f"the dump isn't the target's stack:\n{dump.stdout}")
    return "dumped a running process's stack"


def perf_works() -> str:
    result = subprocess.run(
        ["perf", "record", "-q", "-o", "/dev/null", "--", "true"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return "perf record ran"


def numpy_imports() -> str:
    import numpy

    return f"numpy {numpy.__version__}"


CHECKS = (
    Check("interpreters resolve", interpreters),
    Check("flamegraph URL resolves", flamegraph_site),
    Check("Tachyon attaches", profiler_attaches),
    Check("perf works", perf_works),
    Check("numpy imports", numpy_imports),
)


def rehearse() -> int:
    """Runs every check, prints the manual checklist, and returns the number of checks that failed."""
    failures = 0
    for check in CHECKS:
        try:
            print(f"ok    {check.name}: {check.run()}")
        except Exception as error:  # noqa: BLE001 (a failed check is reported, and the rest still run)
            failures += 1
            print(f"FAIL  {check.name}: {error!r}")
    print("\nThen, from the presenting browser, over zellij web:")
    for item in MANUAL:
        print(f"  [ ] {item}")
    return failures
