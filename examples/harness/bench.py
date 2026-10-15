"""
Times commands with hyperfine and draws a bar per command from its export, so the bars are this run's numbers.

    bench.py [--interpreter NAME PATH]... LABEL=COMMAND...

Each COMMAND may use {NAME} for each interpreter, and {examples} for the examples directory.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1]
COLORS = ("\x1b[38;2;75;139;190m", "\x1b[38;2;255;212;59m", "\x1b[38;2;134;239;172m", "\x1b[38;2;248;113;113m")
RESET = "\x1b[0m"

arguments = sys.argv[1:]
names = {"examples": str(EXAMPLES)}
while arguments[0] == "--interpreter":
    _, name, path, *arguments = arguments
    names[name] = path
labels, commands = zip(*(spec.split("=", 1) for spec in arguments))
commands = tuple(command.format(**names) for command in commands)

with tempfile.NamedTemporaryFile(suffix=".json") as export:
    hyperfine = ["hyperfine", "--shell=none", "--warmup", "3", "--runs", "15", "--style", "none"]
    hyperfine += ["--export-json", export.name]
    for label, command in zip(labels, commands):
        hyperfine += ["--command-name", label, command]
    print("timing with hyperfine...", flush=True)
    # Its warnings (outliers, mostly) would crowd a small pane, so its stderr shows only if it fails.
    timing = subprocess.run(hyperfine, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if timing.returncode != 0:
        sys.exit(timing.stderr)
    results = json.loads(Path(export.name).read_text())["results"]

slowest = max(result["mean"] for result in results)
width = max(len(label) for label in labels)
# As wide as the terminal it's shown in allows, after the label and the numbers.
bar_width = max(8, shutil.get_terminal_size().columns - width - 18)
for index, result in enumerate(results):
    mean, stddev = result["mean"] * 1000, result["stddev"] * 1000
    bar = "█" * max(1, round(bar_width * result["mean"] / slowest))
    color = COLORS[index % len(COLORS)]
    print(f"{result['command']:>{width}} {color}{bar}{RESET} {mean:.0f} ± {stddev:.0f} ms")
