"""
Runs an example on each interpreter and draws its timings side by side, a bar per interpreter per timing,
with how much faster the last interpreter is than the first: EXAMPLE INTERPRETER...

The example prints each timing on its own line as `NAME: TIME ms`, and its first line is its Python version.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]
TIMING = re.compile(r"(.+?):\s*([\d.]+) ms")
COLORS = ("\x1b[38;2;248;113;113m", "\x1b[38;2;75;139;190m")
BOLD, RESET = "\x1b[1m", "\x1b[0m"

name, *interpreters = sys.argv[1:]
versions = []
timings: dict[str, list[float]] = {}
for index, interpreter in enumerate(interpreters, 1):
    print(f"running {Path(name).name}, {index} of {len(interpreters)}...", flush=True)
    version, *lines = subprocess.run(
        [interpreter, EXAMPLES / name], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    versions.append(version)
    for line in lines:
        label, milliseconds = TIMING.fullmatch(line).groups()
        timings.setdefault(label, []).append(float(milliseconds))

print()
width = max(len(version) for version in versions)
bar_width = max(8, shutil.get_terminal_size().columns - width - 30)
for label, values in timings.items():
    slowest = max(values)
    print(f"{BOLD}{label}{RESET}: {values[0] / values[-1]:.1f}x faster on {versions[-1]}")
    for version, value, color in zip(versions, values, COLORS * len(versions)):
        print(f"  {version:>{width}} {color}{'█' * max(1, round(bar_width * value / slowest))}{RESET} {value:.1f} ms")
