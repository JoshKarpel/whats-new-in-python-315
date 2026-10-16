"""
Animations, driven by the app's clock through `use_clock`, so the export's frozen clock holds them still
and its `AdvanceClock` moves them on deterministically.

Two kinds, which start differently:
- An explanatory animation plays once and holds its last frame. It starts when its component mounts, so a slide
  starts one from a key by keying the component on the reveal step: Space remounts it, which plays it.
- A decorative one loops for as long as its slide is the live one, from arrival.

Neither runs off the live slide: a thumbnail shows an explanatory animation's last frame and a decorative one's
first, and ticks no clock for either, since nine thumbnails animating at once would cost frame time for nothing.
The one exception is a title card's pulsing border (see `title_card`), which pulses in the slide grid too,
counted from the app's start rather than arrival, so every card in view pulses in step.
"""

from dataclasses import dataclass
from datetime import timedelta

from counterweight.hooks import Ref
from counterweight.hooks import use_clock
from counterweight.hooks import use_ref

FRAME = timedelta(milliseconds=50)
"""How often a playing animation draws: 20 frames a second, smooth enough for cells, and cheap on 2 vCPUs."""
IDLE = timedelta(hours=1)
"""The clock interval of an animation that isn't playing, which never comes due while a slide is up."""


@dataclass(slots=True)
class Played:
    """Whether an animation has reached its end, which it remembers so it stops ticking the clock."""

    is_done: bool = False


def use_progress(duration: timedelta, is_playing: bool) -> float:
    """
    How far through an animation `duration` long the calling component is: 0 when it mounts, rising to 1,
    where it holds. Not playing, it's 1 at once.
    """
    played: Ref[Played] = use_ref(Played)
    is_ticking = is_playing and not played.current.is_done
    tick = use_clock(FRAME if is_ticking else IDLE)
    if not is_playing:
        return 1.0
    progress = min(tick.since_mount / duration, 1.0)
    if progress >= 1.0:
        played.current.is_done = True
    return progress


def use_loop(period: timedelta, is_playing: bool) -> float:
    """Where in a loop `period` long the calling component is, from 0 up to (not including) 1; 0 while not playing."""
    tick = use_clock(FRAME if is_playing else IDLE)
    if not is_playing:
        return 0.0
    return (tick.since_mount % period) / period


def use_synced_loop(period: timedelta) -> float:
    """
    Where in a loop `period` long the app is, from 0 up to (not including) 1: counted from the app's start
    rather than the calling component's mount, so every component looping on `period` is in step with the rest.
    """
    tick = use_clock(FRAME)
    return (tick.since_start % period) / period


def between(progress: float, start: float, stop: float) -> float:
    """How far `progress` is through the part of an animation from `start` to `stop`: 0 before it, 1 after it."""
    return min(max((progress - start) / (stop - start), 0.0), 1.0)
