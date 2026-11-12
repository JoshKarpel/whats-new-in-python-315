"""
Profiles an example under one of 3.15's two profilers and prints its table, cut to the rows that fit the run box:
PROFILER EXAMPLE, where PROFILER is `tracing` (cProfile, under its new name) or `sampling` (Tachyon).
"""

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]
ROWS = 2
SAMPLING_STATISTICS = ("Sample rate", "Error rate", "Profile Stats")
FLAGS = {"tracing": ["-s", "tottime"], "sampling": ["run", "-l", str(ROWS), "--no-summary"]}

profiler, name = sys.argv[1:]
flags = FLAGS[profiler]
print(f"$ python -m profiling.{profiler} {' '.join(flags)} {Path(name).name}", flush=True)
# The profiler's stdout is a pipe to here, so it colors only if told to, as it would a terminal.
color = {"FORCE_COLOR": "1"} if sys.stdout.isatty() else {}
result = subprocess.run(
    [sys.executable, "-m", f"profiling.{profiler}", *flags, EXAMPLES / name],
    stdout=subprocess.PIPE,
    text=True,
    env={**os.environ, **color},
    cwd=EXAMPLES / Path(name).parent,
)
if profiler == "sampling":
    # The legend always follows the table, and would push it out of the run box, as would the sampling statistics.
    table, _, _ = result.stdout.partition("Legend:")
    kept = [line for line in table.splitlines() if not any(word in line for word in SAMPLING_STATISTICS)]
    print("\n".join(kept).rstrip().removesuffix("\x1b[1;34m").rstrip())
else:
    # The program's own output, the call count, and the table's header, then its slowest rows.
    lines = [line for line in result.stdout.splitlines() if line.strip() and "Ordered by" not in line]
    header = next(index for index, line in enumerate(lines) if "ncalls" in line)
    print("\n".join(lines[: header + 1 + ROWS]))
sys.exit(result.returncode)
