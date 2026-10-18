"""
The deck's entry point: `python -m whats_new` presents it, `python -m whats_new export` writes `slides.html`,
`python -m whats_new record` writes `slides.cast`, and `python -m whats_new showcase` writes `transitions.cast`.

Interpreters are resolved here, once, before anything draws, so a missing one fails at launch, not on stage.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from tempfile import gettempdir

from counterweight.app import app

from whats_new import export
from whats_new import recording
from whats_new import showcase
from whats_new.checkpoint import Checkpoint
from whats_new.components.transitions import TRANSITIONS
from whats_new.deck import SLIDES
from whats_new.host import EXPORT_FLAMEGRAPH_SITE
from whats_new.host import EXPORT_PID
from whats_new.host import FlamegraphSite
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.rehearse import rehearse
from whats_new.runs import ROOT
from whats_new.runs import Interpreters
from whats_new.runs import MissingInterpreter
from whats_new.runs import available_capabilities

CHECKPOINT_FILE = Path(gettempdir()) / "whats-new-in-python-315-checkpoint"
"""The deck's checkpoint, so a restart (live reload, or a crash on stage) lands on the same slide, in the same theme."""


def load_checkpoint() -> Checkpoint:
    try:
        return Checkpoint.parse(CHECKPOINT_FILE.read_text())
    except FileNotFoundError:
        return Checkpoint(slide=0)


def save_checkpoint(checkpoint: Checkpoint) -> None:
    CHECKPOINT_FILE.write_text(checkpoint.serialized())


def main() -> None:
    parser = argparse.ArgumentParser(prog="whats_new", description=__doc__)
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("present", help="present the deck (the default)")
    commands.add_parser("rehearse", help="check the presenting setup, then print a checklist for the rest")
    export_parser = commands.add_parser("export", help="write the HTML export")
    export_parser.add_argument(
        "--output", type=Path, help="write the page here instead of the repository's tracked slides.html"
    )
    record_parser = commands.add_parser("record", help="record the deck presented by an autopilot, runs and all")
    record_parser.add_argument(
        "--output", type=Path, default=ROOT / "slides.cast", help="write the recording here instead of slides.cast"
    )
    showcase_parser = commands.add_parser("showcase", help="record every slide transition, one after another")
    showcase_parser.add_argument(
        "--output", type=Path, help="write the recording here instead of the repository's tracked transitions.cast"
    )
    arguments = parser.parse_args()

    if arguments.command == "rehearse":
        sys.exit(rehearse())

    try:
        interpreters = Interpreters.resolve()
    except MissingInterpreter as error:
        sys.exit(str(error))

    with TemporaryDirectory(prefix="whats-new-examples-") as examples_copy:
        match arguments.command:
            case "export":
                host = Host(
                    interpreters=interpreters,
                    flamegraph=EXPORT_FLAMEGRAPH_SITE,
                    pid=EXPORT_PID,
                    examples_copy=Path(examples_copy),
                )
                frames = asyncio.run(export.screenshots(SLIDES, host))
                html = export.page(frames)
                if arguments.output is None:
                    export.write_tracked(ROOT / "slides.html", html)
                else:
                    arguments.output.write_text(html)
            case "record":
                host = Host(
                    interpreters=interpreters,
                    flamegraph=EXPORT_FLAMEGRAPH_SITE,
                    # The real one, since the Tachyon stage's tour attaches the profiler to the deck.
                    pid=os.getpid(),
                    examples_copy=Path(examples_copy),
                )
                asyncio.run(recording.record(SLIDES, host, available_capabilities(), arguments.output))
            case "showcase":
                host = Host(
                    interpreters=interpreters,
                    flamegraph=EXPORT_FLAMEGRAPH_SITE,
                    pid=EXPORT_PID,
                    examples_copy=Path(examples_copy),
                )
                transitions = tuple(TRANSITIONS.items())
                if arguments.output is not None:
                    asyncio.run(showcase.record_showcase(SLIDES, host, transitions, arguments.output))
                    return
                with TemporaryDirectory(prefix="whats-new-showcase-") as scratch:
                    recorded = Path(scratch) / "transitions.cast"
                    asyncio.run(showcase.record_showcase(SLIDES, host, transitions, recorded))
                    export.write_tracked(ROOT / "transitions.cast", recorded.read_text())
            case "present" | None:
                host = Host(
                    interpreters=interpreters,
                    flamegraph=FlamegraphSite.resolve(os.environ),
                    pid=os.getpid(),
                    examples_copy=Path(examples_copy),
                )
                asyncio.run(
                    app(
                        root(SLIDES, host, load_checkpoint(), save_checkpoint),
                        title="What's New in Python 3.15",
                    )
                )
            case unknown:
                parser.error(f"unknown command {unknown!r}")


if __name__ == "__main__":
    main()
