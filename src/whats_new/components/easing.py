"""
The curves transitions follow, each mapping how far through its time a motion is, from 0 to 1, to how far along it
has got: 0 at the start and 1 at the end, never past either.

Each transition picks its own, by what its progress stands for. Something moving whole (a slide, a cube's face,
a page, a mask's edge, a character's flight) eases in and out. Something that happens at a steady rate (typing,
a sweep, a spreading wave) doesn't ease at all, since its pace is part of what it shows, and nor does an effect
that models its own physics, such as a fall, which a curve would only distort. A curve that went past the end and
came back would run any of those backwards.
"""


def linear(t: float) -> float:
    """No easing at all, for an effect that takes its curve as a value but happens at a steady rate."""
    return t


def ease_in(t: float) -> float:
    """Starts at rest and speeds up to the end, as something drawn in."""
    return t**3


def ease_out(t: float) -> float:
    """Fast off the mark, slowing into place, as something thrown and caught."""
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    """Gathers speed, then slows into place: the smoothest, and the least noticeable."""
    return 4 * t**3 if t < 0.5 else 1 - (2 - 2 * t) ** 3 / 2
