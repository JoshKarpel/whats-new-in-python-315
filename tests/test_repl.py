"""The REPL slide's embedded Python 3.15: it starts on `s`, at the slide's width, and evaluates what's typed into it."""

import asyncio

from counterweight import app
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.paint import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING


async def test_the_repl_evaluates_what_is_typed(host: Host) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "Lightning: the REPL")
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.25)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key="s"),
        *(Screenshot(handler=settle) for _ in range(8)),
        *(KeyPressed(key=character) for character in "6*7"),
        KeyPressed(key=Key.Enter),
        *(Screenshot(handler=settle) for _ in range(4)),
        Screenshot(handler=frames.append),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert "│42" in frames[0].text(ansi=False)
