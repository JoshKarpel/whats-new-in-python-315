"""
The deck's entry point: `python -m whats_new` presents it, and `python -m whats_new export` writes `slides.html`.

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
from whats_new.checkpoint import Checkpoint
from whats_new.deck import SLIDES
from whats_new.frame_time import FrameTimer
from whats_new.frame_time import timed_output
from whats_new.host import EXPORT_FLAMEGRAPH_SITE
from whats_new.host import EXPORT_PID
from whats_new.host import FlamegraphSite
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.rehearse import rehearse
from whats_new.runs import ROOT
from whats_new.runs import Interpreters
from whats_new.runs import MissingInterpreter

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
            case "present" | None:
                host = Host(
                    interpreters=interpreters,
                    flamegraph=FlamegraphSite.resolve(os.environ),
                    pid=os.getpid(),
                    examples_copy=Path(examples_copy),
                )
                timer = FrameTimer()
                with timed_output(sys.stdout, timer) as output:
                    asyncio.run(
                        app(
                            root(SLIDES, host, load_checkpoint(), save_checkpoint, last_frame=lambda: timer.last),
                            output_stream=output,
                            clock=timer.clock,
                            title="What's New in Python 3.15",
                        )
                    )
            case unknown:
                parser.error(f"unknown command {unknown!r}")


if __name__ == "__main__":
    main()
