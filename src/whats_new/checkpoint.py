"""
What the deck remembers across a restart (live reload, or a crash on stage): the slide it's on, the code theme F4
picked, the transition F6 and its speed F8 picked, the grid's transition F7 picked, and the slides `g` made ghosts
or not.
The deck writes it whenever any of them changes, and reads it once, at startup.
"""

import json
from dataclasses import dataclass

from whats_new.components.code import CODE_THEME
from whats_new.components.code import CODE_THEMES
from whats_new.components.transitions import GRID_OFFERED
from whats_new.components.transitions import OFF
from whats_new.components.transitions import OFFERED
from whats_new.components.transitions import SPEED
from whats_new.components.transitions import SPEEDS


@dataclass(frozen=True, slots=True)
class Checkpoint:
    slide: int
    """The slide's index, which the deck clamps to its length."""
    code_theme: str = CODE_THEME
    transition: str = OFF
    speed: str = SPEED
    grid_transition: str = OFF
    ghost_overrides: frozendict[str, bool] = frozendict()
    """Whether each slide `g` toggled is a ghost, by its title, where that differs from the slide's own `is_ghost`."""

    @classmethod
    def parse(cls, text: str) -> Checkpoint:
        """
        The checkpoint `text` holds, as `serialized` writes it.
        Text that isn't one starts from the first slide, and a theme, transition, speed or grid transition the pickers don't offer
        (or a checkpoint from before there was one to pick) starts from the default, as do ghost overrides that
        aren't titles to booleans:
        losing a checkpoint costs a few key presses, and a deck relaunched on stage mustn't refuse to start.
        """
        try:
            fields = json.loads(text)
        except ValueError:
            return cls(slide=0)
        match fields:
            case {"slide": int(slide), "code_theme": str(theme), **rest}:
                transition = rest.get("transition")
                speed = rest.get("speed")
                grid_transition = rest.get("grid_transition")
                ghost_overrides = rest.get("ghost_overrides")
                return cls(
                    slide=slide,
                    code_theme=theme if theme in CODE_THEMES else CODE_THEME,
                    transition=transition if transition in OFFERED else OFF,
                    speed=speed if speed in SPEEDS else SPEED,
                    grid_transition=grid_transition if grid_transition in GRID_OFFERED else OFF,
                    ghost_overrides=parse_ghost_overrides(ghost_overrides),
                )
            case _:
                return cls(slide=0)

    def serialized(self) -> str:
        return json.dumps(
            {
                "slide": self.slide,
                "code_theme": self.code_theme,
                "transition": self.transition,
                "speed": self.speed,
                "grid_transition": self.grid_transition,
                "ghost_overrides": dict(self.ghost_overrides),
            }
        )


def parse_ghost_overrides(value: object) -> frozendict[str, bool]:
    """The ghost overrides `value` holds, if it's an object of titles to booleans, or none if it isn't."""
    match value:
        case dict() if all(isinstance(title, str) and isinstance(is_ghost, bool) for title, is_ghost in value.items()):
            return frozendict(value)
        case _:
            return frozendict()
