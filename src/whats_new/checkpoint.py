"""
What the deck remembers across a restart (live reload, or a crash on stage): the slide it's on and the code theme F4
picked. The deck writes it whenever either changes, and reads it once, at startup.
"""

import json
from dataclasses import dataclass

from whats_new.components.code import CODE_THEME
from whats_new.components.code import CODE_THEMES


@dataclass(frozen=True, slots=True)
class Checkpoint:
    slide: int
    """The slide's index, which the deck clamps to its length."""
    code_theme: str = CODE_THEME

    @classmethod
    def parse(cls, text: str) -> Checkpoint:
        """
        The checkpoint `text` holds, as `serialized` writes it.
        Text that isn't one starts from the first slide, and a theme the picker doesn't offer starts from the default:
        losing a checkpoint costs a few key presses, and a deck relaunched on stage mustn't refuse to start.
        """
        try:
            fields = json.loads(text)
        except ValueError:
            return cls(slide=0)
        match fields:
            case {"slide": int(slide), "code_theme": str(theme)}:
                return cls(slide=slide, code_theme=theme if theme in CODE_THEMES else CODE_THEME)
            case _:
                return cls(slide=0)

    def serialized(self) -> str:
        return json.dumps({"slide": self.slide, "code_theme": self.code_theme})
