"""
The curves a slide transition can follow, which F3 picks between.

Each maps how far through the transition's time it is, from 0 to 1, to how far across the slides have moved:
0 at the start and 1 at the end. In between a curve may go past 1 and come back, as `overshoot` and `spring` do,
so whatever places the slides from one mustn't clamp it.
The last three share a form: a cosine for the motion, times a power of the time left, which damps it to rest at 1.
"""

from collections.abc import Callable
from math import cos
from math import pi

type Easing = Callable[[float], float]


def linear(t: float) -> float:
    """Constant speed, which reads as mechanical: the baseline the others are judged against."""
    return t


def ease_out(t: float) -> float:
    """Fast off the mark, slowing into place, as something thrown and caught."""
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    """Gathers speed, then slows into place: the smoothest, and the least noticeable."""
    return 4 * t**3 if t < 0.5 else 1 - (2 - 2 * t) ** 3 / 2


def overshoot(t: float) -> float:
    """Goes about a fifth of the screen too far, once, and settles back."""
    return 1 - cos(1.5 * pi * t) * (1 - t) ** 2


def spring(t: float) -> float:
    """Overshoots by about a quarter, swings a little short, and settles: a damped spring."""
    return 1 - cos(2.5 * pi * t) * (1 - t) ** 3


def bounce(t: float) -> float:
    """Lands at the end and bounces off it, lower each time; never past the end, unlike `spring`."""
    return 1 - abs(cos(2.5 * pi * t)) * (1 - t) ** 2


EASINGS: frozendict[str, Easing] = frozendict(
    {
        "linear": linear,
        "ease-out": ease_out,
        "ease-in-out": ease_in_out,
        "overshoot": overshoot,
        "spring": spring,
        "bounce": bounce,
    }
)
