"""Scene props shared between consecutive scenes (so cuts are seamless)."""

from __future__ import annotations

import numpy as np
from manim import *  # noqa: F401,F403

from .style import *  # noqa: F401,F403
from .widgets import device


def brick_wall(width=1.0, height=3.6, rows=12, color="#2B3554", accent=None):
    bricks = VGroup()
    bh = height / rows
    bw = width / 2
    for r in range(rows):
        x = -width / 2 - (r % 2) * bw / 2
        while x < width / 2 - 1e-6:
            x0, x1 = max(x, -width / 2), min(x + bw, width / 2)
            if x1 - x0 > 0.06:
                b = Rectangle(width=x1 - x0 - 0.035, height=bh - 0.035, stroke_width=0)
                b.set_fill(interpolate_color(ManimColor(color), ManimColor("#3A4670"), np.random.rand() * 0.35), 1)
                b.move_to([(x0 + x1) / 2, -height / 2 + bh * (r + 0.5), 0])
                bricks.add(b)
            x += bw
    if accent:
        cap = Rectangle(width=width, height=0.06, fill_color=accent, fill_opacity=1, stroke_width=0)
        cap.next_to(bricks, UP, buff=0.02)
        bricks.add(cap)
    return bricks



def four_walls_layout():
    """Control-room Ethernet on the left, hazardous field on the right, four walls between."""
    np.random.seed(11)
    sw = device("Ethernet", "router", BLUE, width=1.9, height=1.5, label_size=22, sub="control room").move_to(LEFT * 5.75 + DOWN * 0.2)
    field_zone = RoundedRectangle(width=2.5, height=4.6, corner_radius=0.2, fill_color=HAZARD, fill_opacity=0.06,
                                  stroke_color=HAZARD, stroke_width=1.5).move_to(RIGHT * 5.75 + DOWN * 0.2)
    fz_hatch = hatch(field_zone, HAZARD, spacing=0.3, opacity=0.18)
    fdevs = VGroup(*[device(n, ic, APL, width=1.45, height=1.05, label_size=17) for n, ic in
                     [("PT", "gauge"), ("TT", "temperature"), ("LT", "ripple")]]).arrange(DOWN, buff=0.28).move_to(field_zone)
    fz_lbl = T("field · hazardous area", size=18, color=HAZARD).next_to(field_zone, UP, buff=0.12)
    walls = VGroup()
    wall_lbls = VGroup()
    specs = [("Distance", "100 m per link", "ruler-measure", BLUE),
             ("Wires", "2–4 pairs", "plug", APL),
             ("Power", "no local supply", "bolt", POWER),
             ("Explosion", "limit the energy", "flame", HAZARD)]
    for i, (name, sub, ic, c) in enumerate(specs):
        x = -3.0 + i * 2.0
        wl = brick_wall(1.05, 3.4, rows=11, accent=c).move_to([x, -0.35, 0])
        walls.add(wl)
        ico = icon(ic, c, 0.5).next_to(wl, UP, buff=0.2)
        nm = T(name, size=24, color=TEXT, weight=BOLD).next_to(wl, DOWN, buff=0.22)
        sb = T(sub, size=15, color=MUTED).next_to(nm, DOWN, buff=0.08)
        wall_lbls.add(VGroup(ico, nm, sb))

    return sw, field_zone, fz_hatch, fz_lbl, fdevs, walls, wall_lbls


# ---------------------------------------------------------------- rate vs. length chart (log-log)
CAN_POINTS = [(40, 1e6), (100, 500e3), (250, 250e3), (500, 125e3), (1000, 50e3), (5000, 10e3)]


def rate_length_chart(x_length=8.6, y_length=4.7):
    """Axes in log10 units: x = log10(length / m), y = log10(rate / bit/s)."""
    ax = Axes(x_range=[1, 4, 1], y_range=[4, 7.4, 1], x_length=x_length, y_length=y_length,
              axis_config={"stroke_color": DIM, "stroke_width": 2, "include_tip": False, "include_ticks": False})
    grid = VGroup()
    for dec in range(1, 4):
        for k in range(1, 10):
            x = dec + np.log10(k)
            if x <= 4:
                grid.add(Line(ax.c2p(x, 4), ax.c2p(x, 7.4), stroke_color=GRID, stroke_width=1.5 if k == 1 else 0.8,
                              stroke_opacity=0.9 if k == 1 else 0.5))
    for dec in range(4, 8):
        for k in range(1, 10):
            y = dec + np.log10(k)
            if y <= 7.4:
                grid.add(Line(ax.c2p(1, y), ax.c2p(4, y), stroke_color=GRID, stroke_width=1.5 if k == 1 else 0.8,
                              stroke_opacity=0.9 if k == 1 else 0.5))
    xl = VGroup(*[T(t, size=18, color=MUTED).next_to(ax.c2p(x, 4), DOWN, buff=0.15)
                  for x, t in [(1, "10 m"), (2, "100 m"), (3, "1 km"), (4, "10 km")]])
    yl = VGroup(*[T(t, size=18, color=MUTED).next_to(ax.c2p(1, y), LEFT, buff=0.15)
                  for y, t in [(4, "10 kbit/s"), (5, "100 kbit/s"), (6, "1 Mbit/s"), (7, "10 Mbit/s")]])
    xt = T("cable length", size=20, color=TEXT).next_to(xl, DOWN, buff=0.15)
    yt = T("bit rate", size=20, color=TEXT).next_to(ax.c2p(1, 7.4), UP, buff=0.15).shift(LEFT * 0.4)
    return ax, VGroup(grid, xl, yl, xt, yt)


def can_curve(ax, color=CAN):
    pts = VGroup(*[Dot(ax.c2p(np.log10(L), np.log10(R)), radius=0.075, color=color) for L, R in CAN_POINTS])
    k = np.log10(5e7)  # R * L = 50 Mbit/s * m
    line = VMobject().set_points_as_corners([ax.c2p(1, 6), ax.c2p(k - 6, 6), ax.c2p(k - 4, 4)])
    line.set_stroke(color, 4)
    return line, pts
