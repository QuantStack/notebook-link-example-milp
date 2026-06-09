"""A small ipycanvas widget to build and solve TSP instances interactively.

Click on the canvas to drop nodes, then use the buttons to solve the tour or reset.
"""

import math
from collections.abc import Callable

import ipycanvas
import ipywidgets

# Modern, flat palette tuned for a light background.
_EDGE_STROKE = "#1f2937" # gray-800, dark grey tour
_PLACEHOLDER = "#cbd5e1" # slate-300
_BORDER = "#e2e8f0"      # slate-200
_NODE_SIZE = 22          # emoji font size (before scaling)
_CAR = "🚴🏼"              # drawn at the middle of every edge
_CAR_SIZE = 16

# Each node is drawn as a city/building emoji, picked in a fixed cyclic order.
_NODE_EMOJIS = [
    "🏠", "🏢", "🏰", "⛪", "🗼", "🏟️", "🏭", "🕌", "🏝️", "🏬",
    "🏡", "🏥", "🗽", "🛕", "⛺", "🏯", "🏦", "🌆", "🏪", "🕍",
    "🏖️", "🏛️", "🏨", "⛩️", "🌃", "🏚️", "🏫", "🏗️", "🏩", "🏘️",
]

Solver = Callable[
    [list[int], dict[tuple[int, int], float]],
    tuple[float, list[tuple[int, int]]],
]


def tsp_widget(solver: Solver, width: int = 640, height: int = 420, scale: int = 2):
    """Return an interactive TSP widget to display in a notebook cell.

    Click on the canvas to add nodes; "Solve" runs ``solver(V, c)`` (same
    signature as ``solve_tsp``) and draws the tour, "Reset" clears the canvas.
    The canvas is rendered at ``scale`` times its displayed size to stay crisp
    on high-DPI screens; clicks arrive in that same buffer space.
    """
    canvas = ipycanvas.Canvas(
        width=width * scale,
        height=height * scale,
        layout={
            "width": f"{width}px",
            "height": f"{height}px",
            "border": f"1px solid {_BORDER}",
            "border-radius": "8px",
        },
    )
    points: list[tuple[float, float]] = []

    def draw_nodes() -> None:
        canvas.font = f"{_NODE_SIZE * scale}px sans-serif"
        canvas.text_align = "center"
        canvas.text_baseline = "middle"
        for i, (x, y) in enumerate(points):
            canvas.fill_text(_NODE_EMOJIS[i % len(_NODE_EMOJIS)], x, y)

    def redraw() -> None:
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            if not points:
                canvas.fill_style = _PLACEHOLDER
                canvas.font = f"{14 * scale}px sans-serif"
                canvas.text_align = "center"
                canvas.text_baseline = "middle"
                canvas.fill_text("Click to add node", canvas.width / 2, canvas.height / 2)
            else:
                draw_nodes()

    def on_click(x: float, y: float) -> None:
        points.append((x, y))
        redraw()

    def on_solve(_button: ipywidgets.Button) -> None:
        if len(points) < 2:  # nothing to route yet
            return
        V = list(range(len(points)))
        c = {
            (i, j): math.dist(points[i], points[j])
            for i in V
            for j in V
            if j > i
        }
        _obj, edges = solver(V, c)
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            canvas.stroke_style = _EDGE_STROKE
            canvas.line_width = 2 * scale
            canvas.begin_path()
            for i, j in edges:
                canvas.move_to(*points[i])
                canvas.line_to(*points[j])
            canvas.stroke()
            # A little car driving along one edge, rotated to follow it.
            if edges:
                (x1, y1), (x2, y2) = points[edges[0][0]], points[edges[0][1]]
                angle = math.atan2(y2 - y1, x2 - x1)
                canvas.font = f"{_CAR_SIZE * scale}px sans-serif"
                canvas.text_align = "center"
                canvas.text_baseline = "middle"
                canvas.save()
                canvas.translate((x1 + x2) / 2, (y1 + y2) / 2)
                canvas.rotate(angle)
                if abs(angle) > math.pi / 2:  # keep it upright when the edge points left
                    canvas.scale(1, -1)
                canvas.fill_text(_CAR, 0, 0)
                canvas.restore()
            draw_nodes()  # nodes on top of the edges

    def on_reset(_button: ipywidgets.Button) -> None:
        points.clear()
        redraw()

    canvas.on_mouse_down(on_click)
    solve_button = ipywidgets.Button(description="Solve", icon="play", button_style="primary")
    reset_button = ipywidgets.Button(description="Reset", icon="redo")
    solve_button.on_click(on_solve)
    reset_button.on_click(on_reset)

    redraw()
    return ipywidgets.VBox([ipywidgets.HBox([solve_button, reset_button]), canvas])
