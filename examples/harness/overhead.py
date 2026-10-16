"""
Runs an example plainly, under the tracing profiler and under the sampling profiler, and draws a bar per way
of the time the example reports for itself, the best of a few runs: EXAMPLE.

The example times itself, so the bars are the overhead the profiler puts on the program it profiles,
not the profiler's own start-up or its report.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]
RUNS = 3
COLORS = ("\x1b[38;2;75;139;190m", "\x1b[38;2;248;113;113m", "\x1b[38;2;134;239;172m")
RESET = "\x1b[0m"

name = sys.argv[1]
shown = Path(name).name
WAYS = {
    f"python {shown}": [],
    f"python -m profiling.tracing {shown}": ["-m", "profiling.tracing", "-o", "/dev/null"],
    f"python -m profiling.sampling run {shown}": ["-m", "profiling.sampling", "run", "-o", "/dev/null"],
}

results = {}
for label, flags in WAYS.items():
    times = []
    for _ in range(RUNS):
        output = subprocess.run([sys.executable, *flags, EXAMPLES / name], capture_output=True, text=True, check=True)
        times.append(float(re.search(r"took ([\d.]+) s", output.stdout).group(1)))
    results[label] = min(times)
    print(f"{label}: {results[label]:.2f} s", flush=True)

print()
slowest = max(results.values())
bar_width = max(8, shutil.get_terminal_size().columns - 18)
for (label, seconds), color in zip(results.items(), COLORS):
    print(label)
    print(f"  {color}{'█' * max(1, round(bar_width * seconds / slowest))}{RESET} {seconds:.2f} s")
