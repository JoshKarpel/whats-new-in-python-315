"""
Runs mypy on one example, under a header, with only the lines that carry its verdict.

    checkers.py BIN EXAMPLE [MYPY_FLAG...]

BIN is the deck's environment's scripts directory, which holds mypy. It runs with no project configuration,
as on a file outside any project, for Python 3.15.
"""

import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]
BOLD, RESET = "\x1b[1m", "\x1b[0m"

bin_directory, name, *mypy_flags = Path(sys.argv[1]), *sys.argv[2:]
path = EXAMPLES / name

argv = [bin_directory / "mypy", "--config-file=", "--no-incremental", "--python-version=3.15", "--no-error-summary", *mypy_flags, path]
result = subprocess.run(argv, capture_output=True, text=True, cwd=path.parent)
lines = [line.replace(f"{path}", path.name) for line in (result.stdout + result.stderr).splitlines()]
verdict = [line.strip() for line in lines if f"{path.name}:" in line and "undefined-reveal" not in line]
print(f"{BOLD}mypy{RESET} (exit {result.returncode})")
for line in verdict or ["no issues"]:
    print("  " + line)
