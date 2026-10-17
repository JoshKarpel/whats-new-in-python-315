"""
What the deck remembers across a restart (live reload, or a crash on stage): the slide it's on, the code theme F4
picked, and the transition F3 picked. The deck writes it whenever any of them changes, and reads it once, at startup.
"""

import json
from dataclasses import dataclass

from whats_new.components.code import CODE_THEME
from whats_new.components.code import CODE_THEMES
from whats_new.components.swipe import OFF
from whats_new.components.swipe import TRANSITIONS


@dataclass(frozen=True, slots=True)
class Checkpoint:
    slide: int
    """The slide's index, which the deck clamps to its length."""
    code_theme: str = CODE_THEME
    transition: str = OFF

    @classmethod
    def parse(cls, text: str) -> Checkpoint:
        """
        The checkpoint `text` holds, as `serialized` writes it.
        Text that isn't one starts from the first slide, and a theme or transition the pickers don't offer
        (or a checkpoint from before there was a transition to pick) starts from the default:
        losing a checkpoint costs a few key presses, and a deck relaunched on stage mustn't refuse to start.
        """
        try:
            fields = json.loads(text)
        except ValueError:
            return cls(slide=0)
        match fields:
            case {"slide": int(slide), "code_theme": str(theme), **rest}:
                transition = rest.get("transition")
                return cls(
                    slide=slide,
                    code_theme=theme if theme in CODE_THEMES else CODE_THEME,
                    transition=transition if transition in TRANSITIONS else OFF,
                )
            case _:
                return cls(slide=0)

    def serialized(self) -> str:
        return json.dumps({"slide": self.slide, "code_theme": self.code_theme, "transition": self.transition})
