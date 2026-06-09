"""Helpers for displaying Sudoku grids in Jupyter."""


class SudokuGrid:
    """A Sudoku grid that renders as a pretty HTML table in Jupyter."""

    def __init__(self, grid: list[int | None] | None, given: list[int | None] | None = None):
        # A None grid means the puzzle is infeasible; fall back to the clues.
        self.infeasible = grid is None
        if grid is None:
            grid = given if given is not None else [None] * (9 * 9)
        assert len(grid) == 9 * 9
        self.grid = grid
        # Cells present in `given` are styled as clues (the original puzzle).
        self.given = given

    def _repr_html_(self) -> str:
        cells = []
        for i in range(9):
            for j in range(9):
                value = self.grid[j + 9 * i]
                is_clue = self.given is not None and self.given[j + 9 * i] is not None

                style = [
                    "width:25px",
                    "height:25px",
                    "text-align:center",
                    "font-size:16px",
                    "font-family:sans-serif",
                    "border:1px solid #bbb",
                ]
                # Thick borders to separate the nine 3x3 boxes.
                if i % 3 == 0:
                    style.append("border-top:2px solid #333")
                if j % 3 == 0:
                    style.append("border-left:2px solid #333")
                if i == 8:
                    style.append("border-bottom:2px solid #333")
                if j == 8:
                    style.append("border-right:2px solid #333")
                if is_clue:
                    style.append("font-weight:bold")
                    style.append("color:#000")
                else:
                    style.append("color:#1565c0")

                text = "" if value is None else str(value)
                cells.append(f'<td style="{";".join(style)}">{text}</td>')

        rows = "".join(
            "<tr>" + "".join(cells[i * 9:(i + 1) * 9]) + "</tr>" for i in range(9)
        )
        table = f'<table style="border-collapse:collapse">{rows}</table>'

        if not self.infeasible:
            return f'<div style="margin:8px 0">{table}</div>'

        # Overlay a red diagonal "Unfeasible" banner across the grid.
        overlay = (
            '<div style="position:absolute;inset:0;display:flex;'
            'align-items:center;justify-content:center;pointer-events:none">'
            '<span style="color:red;font-weight:bold;font-size:32px;'
            'font-family:sans-serif;letter-spacing:2px;'
            'transform:rotate(-30deg)">UNFEASIBLE</span></div>'
        )
        return (
            '<div style="position:relative;display:inline-block;margin:8px 0">'
            f'{table}{overlay}</div>'
        )

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {"text/html": self._repr_html_()}


def print_sudoku(grid: list[int | None], given: list[int | None] | None = None) -> SudokuGrid:
    """Return a pretty Sudoku grid that renders as HTML in Jupyter.

    Pass `given` (the initial puzzle) to highlight the original clues.
    """
    return SudokuGrid(grid, given)


class SudokuInput:
    """An editable 9x9 grid of single-digit inputs, styled like SudokuGrid."""

    def __init__(self, grid: list[int | None] | None = None):
        import ipywidgets as widgets

        if grid is None:
            grid = [None] * (9 * 9)
        assert len(grid) == 9 * 9

        self.cells = []
        for i in range(9):
            for j in range(9):
                value = grid[j + 9 * i]
                # Thick borders to separate the nine 3x3 boxes.
                layout = widgets.Layout(
                    width="42px",
                    height="42px",
                    padding="0",
                    margin="0",
                    border_top="2px solid #333" if i % 3 == 0 else "1px solid #bbb",
                    border_left="2px solid #333" if j % 3 == 0 else "1px solid #bbb",
                    border_bottom="2px solid #333" if i == 8 else "1px solid #bbb",
                    border_right="2px solid #333" if j == 8 else "1px solid #bbb",
                )
                cell = widgets.Text(
                    value="" if value is None else str(value),
                    layout=layout,
                )
                cell.add_class("sudoku-cell")
                cell.observe(self._sanitize, names="value")
                self.cells.append(cell)

        self.widget = widgets.GridBox(
            self.cells,
            layout=widgets.Layout(
                grid_template_columns="repeat(9, 42px)",
                grid_template_rows="repeat(9, 42px)",
                grid_gap="0",
                margin="8px 0",
                width="max-content",
                overflow="hidden",
            ),
        )

    # Strip the default ipywidgets input chrome so cells match SudokuGrid.
    _CSS = """
    <style>
    .sudoku-cell, .sudoku-cell .widget-input { height:100% !important; }
    .sudoku-cell input {
        height:100% !important;
        width:100% !important;
        min-height:0 !important;
        padding:0 !important;
        margin:0 !important;
        border:none !important;
        border-radius:0 !important;
        box-shadow:none !important;
        text-align:center;
        font-size:24px;
        font-family:sans-serif;
        background:transparent;
        color:#1565c0;
        box-sizing:border-box;
    }
    </style>
    """

    @staticmethod
    def _sanitize(change):
        # Keep only the last typed digit in 1-9.
        cell = change["owner"]
        kept = "".join(c for c in change["new"] if c in "123456789")
        kept = kept[-1:] if kept else ""
        if kept != change["new"]:
            cell.value = kept

    @property
    def value(self) -> list[int | None]:
        """The grid as a flat list of 81 ints (None for empty cells)."""
        return [int(c.value) if c.value else None for c in self.cells]

    def _ipython_display_(self):
        from IPython.display import HTML, display

        display(HTML(self._CSS))
        display(self.widget)


def input_sudoku(grid: list[int | None] | None = None) -> SudokuInput:
    """Return an editable Sudoku grid widget; read its `.value` for the input."""
    return SudokuInput(grid)
