"""
What the deck remembers across a restart (live reload, or a crash on stage): the slide it's on, the code theme F4
picked, the transition F6, its easing curve F7 and its speed F8 picked, and the grid's transition F9 picked.
The deck writes it whenever any of them changes, and reads it once, at startup.
"""

import json
from dataclasses import dataclass

from whats_new.components.code import CODE_THEME
from whats_new.components.code import CODE_THEMES
from whats_new.components.easing import EASING
from whats_new.components.easing import EASINGS
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
    easing: str = EASING
    speed: str = SPEED
    grid_transition: str = OFF

    @classmethod
    def parse(cls, text: str) -> Checkpoint:
        """
        The checkpoint `text` holds, as `serialized` writes it.
        Text that isn't one starts from the first slide, and a theme, transition, curve, speed or grid transition the pickers don't offer
        (or a checkpoint from before there was one to pick) starts from the default:
        losing a checkpoint costs a few key presses, and a deck relaunched on stage mustn't refuse to start.
        """
        try:
            fields = json.loads(text)
        except ValueError:
            return cls(slide=0)
        match fields:
            case {"slide": int(slide), "code_theme": str(theme), **rest}:
                transition = rest.get("transition")
                easing = rest.get("easing")
                speed = rest.get("speed")
                grid_transition = rest.get("grid_transition")
                return cls(
                    slide=slide,
                    code_theme=theme if theme in CODE_THEMES else CODE_THEME,
                    transition=transition if transition in OFFERED else OFF,
                    easing=easing if easing in EASINGS else EASING,
                    speed=speed if speed in SPEEDS else SPEED,
                    grid_transition=grid_transition if grid_transition in GRID_OFFERED else OFF,
                )
            case _:
                return cls(slide=0)

    def serialized(self) -> str:
        return json.dumps(
            {
                "slide": self.slide,
                "code_theme": self.code_theme,
                "transition": self.transition,
                "easing": self.easing,
                "speed": self.speed,
                "grid_transition": self.grid_transition,
            }
        )
