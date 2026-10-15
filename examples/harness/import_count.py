"""Counts the modules each example imports when run with --version, from -X importtime: INTERPRETER EXAMPLE..."""

import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]

interpreter, *names = sys.argv[1:]
for name in names:
    result = subprocess.run(
        [interpreter, "-X", "importtime", EXAMPLES / name, "--version"], capture_output=True, text=True, check=True
    )
    # The first line is the header.
    count = sum(1 for line in result.stderr.splitlines() if line.startswith("import time:")) - 1
    print(f"{Path(name).name}: {count} imports")
