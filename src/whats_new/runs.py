"""
What a slide runs when a number key is pressed, as values, and the interpreters those runs name.

A slide declares its runs; `run_pane` runs them and the example check runs every one and asserts its outcome,
so what's on screen and what's tested are the same declaration.
"""

import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
BIN = Path(sys.executable).parent
"""The deck's own environment's scripts directory, which holds the type checkers from the `checkers` group."""


class Interpreter(Enum):
    """
    An interpreter the demos need, by the request `uv python find` resolves it from.
    Every request names its build variant: with a GIL build and a free-threaded build of one version both installed,
    a bare `3.15` can resolve to either.
    """

    PY315 = "3.15+gil"
    PY315T = "3.15+freethreaded"
    PY314 = "3.14+gil"
    PY314T = "3.14+freethreaded"
    PY3144 = "3.14.4+gil"
    """The last 3.14 with the incremental garbage collector, which 3.14.5 reverted."""
    PY313 = "3.13+gil"

    @property
    def install_request(self) -> str:
        """The request `uv python install` takes, which rejects `+gil` (a GIL build is its default) where `find` needs it."""
        return self.value.removesuffix("+gil")


@dataclass(frozen=True, slots=True)
class MissingInterpreter(Exception):
    """An interpreter the deck needs isn't installed, which is a startup error rather than a dead key on stage."""

    interpreter: Interpreter
    detail: str

    def __str__(self) -> str:
        return (
            f"no interpreter for {self.interpreter.value!r} ({self.detail.strip()}); "
            f"run `just setup` to install the interpreters"
        )


@dataclass(frozen=True, slots=True)
class Interpreters:
    """The path of every interpreter in `Interpreter`, resolved once at startup."""

    paths: Mapping[Interpreter, Path]

    @classmethod
    def resolve(cls) -> Interpreters:
        """
        Resolves every interpreter with `uv python find`.

        Raises:
            MissingInterpreter: For the first interpreter that isn't installed.
        """
        return cls(paths=frozendict({interpreter: find(interpreter) for interpreter in Interpreter}))

    def argv(self, run: Run) -> tuple[str, ...]:
        """`run`'s argv with each interpreter replaced by its path."""
        return tuple(str(self.paths[part]) if isinstance(part, Interpreter) else part for part in run.argv)


def find(interpreter: Interpreter) -> Path:
    """The path `uv python find` resolves `interpreter` to, without considering virtual environments."""
    result = subprocess.run(
        ["uv", "python", "find", "--no-project", "--system", interpreter.value],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise MissingInterpreter(interpreter=interpreter, detail=result.stderr)
    return Path(result.stdout.strip())


@dataclass(frozen=True, slots=True)
class Expect:
    """
    What a run is expected to do, which the example check asserts:
    its exit status, and a substring of its combined output.
    """

    status: int
    output: str


class Capability(Enum):
    """Something a run needs from the machine beyond the interpreters, which a default container may not allow."""

    PERF = "perf"
    """Sampling with `perf_event_open`, which Docker's default seccomp profile blocks."""


@dataclass(frozen=True, slots=True)
class Run:
    """
    One program a slide runs, bound to a number key by its position in the slide's runs.

    `argv` names interpreters symbolically, so slides can be declared before the interpreters are resolved.
    """

    label: str
    argv: tuple[str | Interpreter, ...]
    expect: Expect
    env: Mapping[str, str] = field(default_factory=frozendict)
    needs: frozenset[Capability] = frozenset()


def example(name: str) -> str:
    """The absolute path of the example file `name`, as an argv element, since runs don't set a working directory."""
    path = EXAMPLES / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return str(path)


def tool(name: str) -> str:
    """The path of a script installed in the deck's own environment, such as `mypy`."""
    return str(BIN / name)


def python(interpreter: Interpreter, name: str, *, label: str | None = None, expect: Expect) -> Run:
    """A run of the example `name` on `interpreter`, labeled by the interpreter's version unless `label` is given."""
    return Run(
        label=label or interpreter.install_request,
        argv=(interpreter, example(name)),
        expect=expect,
    )


def on_both(name: str, *, new: Expect, old: Expect) -> tuple[Run, Run]:
    """The example `name` on 3.15 (`1`) and on 3.14 (`2`), where it usually fails, which shows what's new."""
    return (python(Interpreter.PY315, name, expect=new), python(Interpreter.PY314, name, expect=old))


def harness(name: str, *arguments: str | Interpreter, label: str, expect: Expect) -> Run:
    """
    A run of the harness script `name`, a program that drives a demo rather than being shown,
    on the deck's own 3.15 (any interpreters it drives are in `arguments`).
    """
    return Run(label=label, argv=(Interpreter.PY315, example(f"harness/{name}"), *arguments), expect=expect)


def checkers(name: str, *mypy_flags: str, label: str = "mypy, pyright, ty", expect: Expect) -> Run:
    """mypy, pyright and ty on the example `name`, one after another, as the deck's own environment pins them."""
    return harness("checkers.py", str(BIN), name, *mypy_flags, label=label, expect=expect)


if __name__ == "__main__":
    # The interpreters to install, for `just setup` and the Dockerfile, which install them before the deck can run.
    print(*(interpreter.install_request for interpreter in Interpreter))
