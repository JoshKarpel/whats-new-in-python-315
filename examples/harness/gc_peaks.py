"""Runs the GC churn example on each interpreter and draws its peak memory as a bar: INTERPRETER..."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[1] / "gc" / "gc_churn.py"
INCREMENTAL, GENERATIONAL = "\x1b[38;2;248;113;113m", "\x1b[38;2;75;139;190m"
RESET = "\x1b[0m"

results = []
for interpreter in sys.argv[1:]:
    line = subprocess.run([interpreter, EXAMPLE], capture_output=True, text=True, check=True).stdout.strip()
    version, peak, threshold = re.match(r"\s*(\S+): peak (\d+) MiB, threshold (.*)", line).groups()
    results.append((version, int(peak), threshold))
    print(f"{version:>7}: {peak:>4} MiB, gc.get_threshold() = {threshold}", flush=True)

print()
largest = max(peak for _, peak, _ in results)
bar_width = max(8, shutil.get_terminal_size().columns - 26)
for version, peak, threshold in results:
    color = INCREMENTAL if threshold.endswith(" 0)") else GENERATIONAL
    print(f"{version:>7} {color}{'█' * max(1, round(bar_width * peak / largest))}{RESET} {peak} MiB")
