"""
The size the deck is presented at, in cells.

Everything drawn for one width (diagrams, the slide grid, the Tachyon stage) and everything that renders headless
(the export and the smoke test) reads it from here, so changing it is one edit.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Size:
    """A terminal size in cells: the width is an exact target, the height a floor."""

    columns: int
    rows: int

    def fits_width(self, columns: int) -> bool:
        """Whether a terminal `columns` wide is exactly the presenting width, which every diagram is drawn for."""
        return columns == self.columns

    def fits_height(self, rows: int) -> bool:
        """Whether a terminal `rows` tall has at least the presenting height; extra rows are slack."""
        return rows >= self.rows

    @property
    def dimensions(self) -> tuple[int, int]:
        """`(columns, rows)`, as `counterweight.app.app` takes them."""
        return (self.columns, self.rows)


PRESENTING = Size(columns=90, rows=30)
"""
The reference talk's size, presented from the same 3:2 laptop, whose screen gives about three columns per row.
Confirm it in zellij web on the presenting laptop before drawing diagrams.
"""
