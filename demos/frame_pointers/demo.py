"""
Builds churn.c twice, with and without frame pointers, then samples Python calling through each with
`perf record --call-graph fp`, and reports how many samples' stacks unwind all the way to the process entry point.

Run it with the interpreter to test; it builds against that interpreter's headers.
"""

import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRIVER = """
import importlib, sys
module = importlib.import_module(sys.argv[1])

def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

def callback():
    return fib(18)

def outer_python_frame():
    return module.call_many(callback, 400)

outer_python_frame()
"""
BUILDS = {"churn_fp": ("with", "-fno-omit-frame-pointer"), "churn_nofp": ("without", "-fomit-frame-pointer")}


def build(directory: Path, name: str, flag: str) -> None:
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    subprocess.run(
        [
            "cc",
            "-O2",
            "-shared",
            "-fPIC",
            flag,
            f"-I{sysconfig.get_paths()['include']}",
            f'-DNAME="{name}"',
            f"-DMODNAME={name}",
            HERE / "churn.c",
            "-o",
            directory / f"{name}{suffix}",
        ],
        check=True,
    )


def reach(script: str) -> tuple[int, float, float]:
    """How many samples, what fraction unwind to `_start`, and what fraction still see the Python caller."""
    samples = [sample for sample in script.strip().split("\n\n") if sample.strip()]
    reached = sum(1 for sample in samples if "_start" in sample)
    outer = sum(1 for sample in samples if "outer_python_frame" in sample)
    return len(samples), reached / len(samples), outer / len(samples)


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary)
    (directory / "drive.py").write_text(DRIVER)
    for name, (_, flag) in BUILDS.items():
        build(directory, name, flag)
    print("frame pointers  samples  reach _start  see the Python caller")
    for name, (label, _) in BUILDS.items():
        data = directory / f"{name}.data"
        subprocess.run(
            [
                *("perf", "record", "-q", "-F", "999", "--call-graph", "fp", "-o", data, "--"),
                *(sys.executable, "-X", "perf", directory / "drive.py", name),
            ],
            cwd=directory,
            check=True,
            stderr=subprocess.DEVNULL,
        )
        script = subprocess.run(["perf", "script", "-i", data], capture_output=True, text=True, check=True).stdout
        samples, to_start, to_outer = reach(script)
        print(f"{label:>14}  {samples:7}  {to_start:12.1%}  {to_outer:21.1%}")
