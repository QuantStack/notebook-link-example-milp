"""A small ipycanvas widget to build and solve facility-location instances.

Toggle between dropping **customers** and candidate **facility locations**,
then "Solve" opens a subset of the facilities and serves every customer from
the open facilities at minimum total (fixed + serving) cost.
"""

import math
from collections.abc import Callable

import ipycanvas
import ipywidgets

# Modern, flat palette tuned for a light background.
_EDGE_STROKE = "#1f2937"  # gray-800, dark grey assignment links
_PLACEHOLDER = "#cbd5e1"  # slate-300
_BORDER = "#e2e8f0"       # slate-200
_NODE_SIZE = 22           # emoji font size (before scaling)
# Demand points, drawn in a fixed cyclic order: people of every skin tone (no
# yellow), assorted professionals, and a few families.
_CUSTOMER_EMOJIS = [
    "🧑🏻", "👩🏼", "👨🏽", "🧑🏾", "👩🏿",
    "👩🏽‍⚕️", "👨🏾‍🏫", "👩🏻‍🌾", "👨🏿‍🍳", "👩🏼‍🔧",
    "👵🏼", "👴🏾", "🧒🏻", "👶🏽", "🧓🏿",
    "👨🏽‍🏭", "👩🏾‍💻", "👨🏻‍🚀", "👩🏿‍🚒", "🧑🏼‍🎨",
    "👨🏻", "🧑🏼", "👩🏽", "👨🏾", "🧑🏿",
    "👮🏽", "👷🏾", "💂🏻", "🕵🏿", "👩🏼‍✈️",
]
_FACILITY = "🏭"           # an open (built) facility
_CANDIDATE = "🏗️"          # a candidate facility that is not built

# Default instance parameters (per click), in canvas-buffer units.
_DEMAND = 1.0             # every customer asks for one unit
_FIXED_COST_RATIO = 0.35  # fixed cost of opening a facility, as a fraction of
                          # the canvas diagonal (trades off against distance)

Solver = Callable[
    [
        list[int],                    # I: customers
        list[int],                    # J: facilities
        dict[int, float],             # d: demand
        dict[int, float],             # M: capacity
        dict[int, float],             # f: fixed cost
        dict[tuple[int, int], float],  # c: serving cost
    ],
    tuple[float, list[int], list[tuple[int, int]]],
]


def flp_widget(solver: Solver, width: int = 640, height: int = 420, scale: int = 2):
    """Return an interactive facility-location widget to display in a cell.

    Use the toggle to pick what a click drops (a customer or a candidate
    facility), then "Solve" runs ``solver(I, J, d, M, f, c)`` and draws the
    open facilities together with the customer-to-facility assignment, "Reset"
    clears the canvas. The canvas is rendered at ``scale`` times its displayed
    size to stay crisp on high-DPI screens; clicks arrive in that buffer space.
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
    customers: list[tuple[float, float]] = []
    facilities: list[tuple[float, float]] = []

    def draw_points(open_facilities: set[int] | None = None) -> None:
        canvas.font = f"{_NODE_SIZE * scale}px sans-serif"
        canvas.text_align = "center"
        canvas.text_baseline = "middle"
        for i, (x, y) in enumerate(customers):
            canvas.fill_text(_CUSTOMER_EMOJIS[i % len(_CUSTOMER_EMOJIS)], x, y)
        for j, (x, y) in enumerate(facilities):
            # Before solving (open_facilities is None) every facility is still a
            # construction site; afterwards, the open ones become built plants.
            built = open_facilities is not None and j in open_facilities
            canvas.fill_text(_FACILITY if built else _CANDIDATE, x, y)

    def redraw() -> None:
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            if not customers and not facilities:
                canvas.fill_style = _PLACEHOLDER
                canvas.font = f"{14 * scale}px sans-serif"
                canvas.text_align = "center"
                canvas.text_baseline = "middle"
                canvas.fill_text("Click to add a node", canvas.width / 2, canvas.height / 2)
            else:
                draw_points()

    def on_click(x: float, y: float) -> None:
        (customers if mode.value == "customer" else facilities).append((x, y))
        redraw()

    def on_solve(_button: ipywidgets.Button) -> None:
        if not customers or not facilities:  # need both sides to assign
            return
        I = list(range(len(customers)))
        J = list(range(len(facilities)))
        d = {i: _DEMAND for i in I}
        # Uncapacitated demo: any facility could serve everyone, so the trade-off
        # is purely fixed cost vs. serving distance.
        M = {j: _DEMAND * len(I) for j in J}
        fixed = _FIXED_COST_RATIO * math.hypot(canvas.width, canvas.height)
        f = {j: fixed for j in J}
        c = {
            (i, j): math.dist(customers[i], facilities[j])
            for i in I
            for j in J
        }
        _obj, open_facilities, assignments = solver(I, J, d, M, f, c)
        open_set = set(open_facilities)
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            canvas.stroke_style = _EDGE_STROKE
            canvas.line_width = 2 * scale
            canvas.begin_path()
            for i, j in assignments:
                canvas.move_to(*customers[i])
                canvas.line_to(*facilities[j])
            canvas.stroke()
            draw_points(open_set)  # nodes on top of the links

    def on_reset(_button: ipywidgets.Button) -> None:
        customers.clear()
        facilities.clear()
        redraw()

    canvas.on_mouse_down(on_click)
    mode = ipywidgets.ToggleButtons(
        options=[(f"{_CUSTOMER_EMOJIS[0]} Customer", "customer"), (f"{_FACILITY} Location", "facility")],
        value="customer",
    )
    solve_button = ipywidgets.Button(description="Solve", icon="play", button_style="primary")
    reset_button = ipywidgets.Button(description="Reset", icon="redo")
    solve_button.on_click(on_solve)
    reset_button.on_click(on_reset)

    redraw()
    return ipywidgets.VBox([mode, ipywidgets.HBox([solve_button, reset_button]), canvas])
