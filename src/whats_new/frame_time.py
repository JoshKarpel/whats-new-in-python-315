"""
How long the deck's last frame took to render, which F3 shows in the footer.

counterweight doesn't report it, so the deck measures it through two things it hands `app`: the clock, which the
render loop reads as it starts each render (and again after, before it waits), and the output stream, which it writes
each frame to as one synchronized update and then flushes. A frame's time is from the latest clock read to that flush:
the components it ran, layout, paint, and the write to the terminal, but not the effects that run after.
"""

import io
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from time import perf_counter
from typing import BinaryIO
from typing import TextIO

from counterweight.clock import Instant
from counterweight.clock import system_clock
from counterweight.output import SYNCHRONIZED_OUTPUT_ON


@dataclass(slots=True, eq=False)
class FrameTimer:
    """
    A place, written by the render loop through `clock` and the stream from `timed_output`,
    and read by the footer, which shows the previous frame's time as it draws the next.
    """

    last: timedelta | None = None
    """The last frame's time, or `None` before the first frame is flushed."""
    render_started: float = 0.0
    is_frame_written: bool = False

    def clock(self) -> Instant:
        """The system clock, for `app`, noting when each render starts."""
        self.render_started = perf_counter()
        return system_clock()

    def wrote(self, text: str) -> None:
        if text.startswith(SYNCHRONIZED_OUTPUT_ON):
            self.is_frame_written = True

    def flushed(self) -> None:
        # Only a frame's flush, not a title's or a bell's, which come before the render's clock read.
        if self.is_frame_written:
            self.last = timedelta(seconds=perf_counter() - self.render_started)
            self.is_frame_written = False


class TimedOutput(io.TextIOWrapper):
    """A text stream over a terminal's byte stream that tells `timer` what's written to it and when it's flushed."""

    def __init__(self, buffer: BinaryIO, encoding: str, timer: FrameTimer) -> None:
        super().__init__(buffer, encoding=encoding)
        self.timer = timer

    def write(self, text: str) -> int:
        self.timer.wrote(text)
        return super().write(text)

    def flush(self) -> None:
        super().flush()
        self.timer.flushed()


@contextmanager
def timed_output(stream: TextIO, timer: FrameTimer) -> Iterator[TextIO]:
    """
    `stream`'s bytes as a `TimedOutput`, detached on exit,
    since a text stream closes its byte stream when it's collected, and this one is `stream`'s too.
    """
    stream.flush()
    output = TimedOutput(stream.buffer, stream.encoding, timer)
    try:
        yield output
    finally:
        output.flush()
        output.detach()
