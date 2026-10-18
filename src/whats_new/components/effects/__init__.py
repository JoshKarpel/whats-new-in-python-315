"""
The transition effects drawn from pictures, one module per effect, each exporting an `Effect` or, for the grid,
a `GridEffect` (see `crossing`), and the pieces several effects share: `masks` for effects that uncover the arriving
slide cell by cell, `characters` for effects that move characters about, `shading` for effects that darken or tint
cells, and `cards` for grid effects that move whole pictures about. `transitions` names each effect for F6 and F7.
"""
