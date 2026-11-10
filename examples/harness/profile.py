"""
Profiles an example under Tachyon and prints what it prints, up to the legend that always follows the table,
which would otherwise push the table out of the run box: EXAMPLE.
"""

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]
FLAGS = ["-l", "3", "--no-summary"]

name = sys.argv[1]
print(f"$ python -m profiling.sampling run {' '.join(FLAGS)} {Path(name).name}", flush=True)
# Tachyon's stdout is a pipe to here, so it colors only if told to, as it would a terminal.
color = {"FORCE_COLOR": "1"} if sys.stdout.isatty() else {}
result = subprocess.run(
    [sys.executable, "-m", "profiling.sampling", "run", *FLAGS, EXAMPLES / name],
    stdout=subprocess.PIPE,
    text=True,
    env={**os.environ, **color},
)
table, _, _ = result.stdout.partition("Legend:")
print(table.rstrip().removesuffix("\x1b[1;34m").rstrip())
sys.exit(result.returncode)
