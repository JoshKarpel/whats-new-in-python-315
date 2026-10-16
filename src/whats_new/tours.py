"""
The steps the recording drives the deck with: holding on a slide while its animations play, typing,
and waiting for the screen to show something.
Slides' tours are built from these, and so is the recording's walk through the whole deck (`recording.py`).
"""

from datetime import timedelta

from counterweight.autopilot import AutopilotStep
from counterweight.autopilot import Wait
from counterweight.autopilot import WaitFor
from counterweight.controls import AdvanceClock
from counterweight.events import KeyPressed
from counterweight.keys import Key

from whats_new.components.animation import FRAME

TYPING = timedelta(milliseconds=90)
"""The pause between keys a tour types, about a fast typist's."""


def hold(duration: timedelta) -> list[AutopilotStep]:
    """
    `duration` passing on the recording's frozen clock, one animation frame at a time,
    so an animation plays out rather than jumping to its end.
    """
    return [AdvanceClock(by=FRAME)] * (duration // FRAME)


def typed(text: str) -> list[AutopilotStep]:
    """
    `text` typed a key at a time, with a newline pressing Enter.
    The pause between keys is real time, not the frozen clock's,
    so a program on a pseudo-terminal echoes each key before the next one arrives.
    """
    return [
        step
        for character in text
        for step in (KeyPressed(key=Key.Enter if character == "\n" else character), Wait(TYPING))
    ]


def showing(text: str, timeout: timedelta = timedelta(seconds=30)) -> WaitFor:
    """Waits until `text` is on screen, such as a program's prompt."""
    return WaitFor(lambda frame: text in frame.text(ansi=False), timeout=timeout)
