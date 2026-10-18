"""
Darkening or tinting cells by steps, for the effects that shade the slides as they move them (`curl`, `cube`,
`shatter`): a few steps, so a smooth shadow needs only a handful of styles per character, each remembered.
"""

from functools import lru_cache

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

SHADES = 8
"""How many steps `shaded` divides a blend into, so a smooth shadow needs only a handful of styles per character."""

GLYPHS_KEPT = 2**15
"""How many shaded glyphs to remember, a few slides' worth, so shading a frame is mostly looking one up."""

BLACK = Color(0, 0, 0)


@lru_cache(maxsize=GLYPHS_KEPT)
def shaded(glyph: StyledGrapheme | None, toward: Color, level: int) -> StyledGrapheme | None:
    """
    `glyph` with its colors blended `level` of `SHADES` of the way to `toward`: darkened toward black, or tinted.
    Level 0 is `glyph` itself, so an effect can shade by a level that falls to 0 and land on the picture exactly.
    A color that isn't an RGB `Color` (a terminal's own default, say) can't be blended, so stays as it is.
    """
    if glyph is None or level == 0:
        return glyph
    style = glyph.style
    return StyledGrapheme(
        grapheme=glyph.grapheme,
        style=style
        | CellStyle(
            foreground=blended(style.foreground, toward, level),
            background=blended(style.background, toward, level),
        ),
    )


def blended[C](color: C, toward: Color, level: int) -> C | Color:
    """`color` `level` of `SHADES` of the way to `toward`, if it's an RGB `Color`; anything else as it is."""
    if not isinstance(color, Color):
        return color
    return color.blend(toward, level / SHADES)
