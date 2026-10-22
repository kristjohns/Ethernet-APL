"""Building blocks for the physical-layer deep dive: journey map, name cards, scopes, ladders, eyes."""

from __future__ import annotations

import numpy as np
from manim import *  # noqa: F401,F403

from .style import (
    APL, BG, BLUE, DIM, GOOD, HAZARD, MUTED, PANEL, PANEL_EDGE, PINK, POWER, TEXT, VIOLET, WHITE_SOFT,
    H, M, T, TeX, glow, panel,
)
from .widgets import capacitor, inductor, resistor, twisted_pair


def dimmed(mob, a):
    """A copy of ``mob`` faded to opacity ``a`` without filling open strokes (set_opacity would fill them)."""
    t = mob.copy()
    for m in t.family_members_with_points():
        if m.get_fill_opacity() > 0:
            m.set_fill(opacity=a * m.get_fill_opacity() if a < 1 else 1.0)
        m.set_stroke(opacity=a)
    return t


def dim_to(mob, a):
    return Transform(mob, dimmed(mob, a))


# ---------------------------------------------------------------- the journey of a bit
class JourneyMap(VGroup):
    """Transmitter stack (left, top to bottom) -> 1 km pair -> receiver stack (right, bottom to top).

    ``groups`` maps a chapter key ("tx", "wire", "duplex", "rx") to the mobjects it covers.
    """

    TX = [("Ethernet MAC", "bits in"), ("Scrambler", None), ("4B3T coder", None), ("PAM-3 DAC + filter", None), ("Hybrid", None)]
    RX = [("Hybrid", None), ("Echo canceller", None), ("Equalizer", "FFE + DFE"), ("Clock recovery + slicer", None),
          ("Decoder + descrambler", "bits out")]

    def __init__(self, x=4.55, top=2.25, step=0.98, w=2.75, h=0.64, **kw):
        super().__init__(**kw)
        self.tx, self.rx = VGroup(), VGroup()
        for i, (name, sub) in enumerate(self.TX):
            self.tx.add(self._block(name, sub, w, h).move_to([-x, top - i * step, 0]))
        for i, (name, sub) in enumerate(self.RX):
            self.rx.add(self._block(name, sub, w, h).move_to([x, top - (len(self.RX) - 1 - i) * step, 0]))
        self.arrows = VGroup()
        for a, b in zip(self.tx[:-1], self.tx[1:]):
            self.arrows.add(Arrow(a.get_bottom(), b.get_top(), buff=0.04, stroke_width=2.5, color=MUTED,
                                  max_tip_length_to_length_ratio=0.35, tip_length=0.14))
        for a, b in zip(self.rx[:-1], self.rx[1:]):
            self.arrows.add(Arrow(a.get_top(), b.get_bottom(), buff=0.04, stroke_width=2.5, color=MUTED,
                                  max_tip_length_to_length_ratio=0.35, tip_length=0.14))
        y = self.tx[-1].get_y()
        self.cable = twisted_pair([self.tx[-1].get_right() + RIGHT * 0.05, self.rx[0].get_left() + LEFT * 0.05],
                                  APL, amp=0.07, pitch=0.42, width=3.2)
        self.cable_lbl = T("1 km of twisted pair", size=19, color=MUTED).next_to(self.cable, UP, buff=0.22)
        self.badges = VGroup()
        for txt, mob, side in (("06", VGroup(*self.tx[1:4]), LEFT), ("05", self.cable, DOWN),
                               ("07", VGroup(self.tx[-1], self.rx[:2]), DOWN), ("08", VGroup(*self.rx[2:]), RIGHT)):
            b = T(txt, size=18, color=APL, weight=BOLD)
            self.badges.add(b)
        self.badges[0].next_to(VGroup(*self.tx[1:4]), LEFT, buff=0.18)
        self.badges[1].next_to(self.cable, DOWN, buff=0.22)
        self.badges[2].next_to(self.rx[0], DOWN, buff=0.15).shift(LEFT * 0.0)
        self.badges[3].next_to(VGroup(*self.rx[2:]), RIGHT, buff=0.18)
        self.add(self.arrows, self.cable, self.cable_lbl, self.tx, self.rx, self.badges)
        self.groups = {
            "tx": [*self.tx[1:4], self.badges[0], self.arrows[0], self.arrows[1], self.arrows[2]],
            "wire": [self.cable, self.cable_lbl, self.badges[1]],
            "duplex": [self.tx[-1], self.rx[0], self.rx[1], self.badges[2], self.arrows[4]],
            "rx": [*self.rx[2:], self.badges[3], self.arrows[5], self.arrows[6], self.arrows[7]],
        }

    @staticmethod
    def _block(name, sub, w, h):
        box = RoundedRectangle(width=w, height=h, corner_radius=0.12, fill_color=PANEL, fill_opacity=1,
                               stroke_color=APL, stroke_width=2)
        t = T(name, size=19, color=TEXT, weight=BOLD)
        if t.width > w * 0.9:
            t.scale_to_fit_width(w * 0.9)
        if sub:
            s = T(sub, size=14, color=MUTED)
            VGroup(t, s).arrange(DOWN, buff=0.05).move_to(box)
            g = VGroup(box, t, s)
        else:
            t.move_to(box)
            g = VGroup(box, t)
        g.box = box
        return g

    def focus(self, key, dim=0.22):
        """Animations that dim everything except the mobjects of ``key``."""
        keep = set(self.groups[key])
        return [dim_to(m, dim) for m in [*self.tx, *self.rx, self.cable, self.cable_lbl, *self.badges, *self.arrows] if m not in keep]


# ---------------------------------------------------------------- small cards & panels
def name_card(name, years, line, color=APL, width=None):
    n = T(name, size=26, color=TEXT, weight=BOLD)
    y = T(years, size=18, color=color, weight=BOLD)
    l = T(line, size=17, color=MUTED)
    txt = VGroup(n, y, l).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    w = width or txt.width + 0.5
    box = RoundedRectangle(width=w, height=txt.height + 0.4, corner_radius=0.14, fill_color=PANEL,
                           fill_opacity=0.95, stroke_color=color, stroke_width=1.8)
    bar = Rectangle(width=0.07, height=box.height - 0.24, fill_color=color, fill_opacity=1, stroke_width=0)
    bar.move_to(box.get_left() + RIGHT * 0.16)
    txt.next_to(bar, RIGHT, buff=0.18)
    return VGroup(box, bar, txt)


def scope(width=3.0, height=1.6, title=None, color=APL, grid=True):
    box = panel(width, height, radius=0.12)
    g = VGroup(box)
    if grid:
        for i in range(1, 6):
            x = box.get_left()[0] + width * i / 6
            g.add(Line([x, box.get_bottom()[1] + 0.08, 0], [x, box.get_top()[1] - 0.08, 0], stroke_color=PANEL_EDGE, stroke_width=1))
        for j in range(1, 4):
            y = box.get_bottom()[1] + height * j / 4
            g.add(Line([box.get_left()[0] + 0.08, y, 0], [box.get_right()[0] - 0.08, y, 0], stroke_color=PANEL_EDGE, stroke_width=1))
    if title:
        g.add(T(title, size=16, color=color, weight=BOLD).next_to(box, UP, buff=0.08).align_to(box, LEFT).shift(RIGHT * 0.05))
    g.box = box
    return g


def trace_in(box, xs, ys, color=APL, width=3, x_range=None, y_range=(-1.2, 1.2), pad=0.12):
    """Polyline of (xs, ys) mapped into a scope box."""
    x0, x1 = x_range or (xs[0], xs[-1])
    y0, y1 = y_range
    L, R = box.get_left()[0] + pad, box.get_right()[0] - pad
    B, Tp = box.get_bottom()[1] + pad, box.get_top()[1] - pad
    px = L + (np.asarray(xs) - x0) / (x1 - x0) * (R - L)
    py = B + (np.clip(ys, y0, y1) - y0) / (y1 - y0) * (Tp - B)
    v = VMobject().set_points_as_corners(np.stack([px, py, np.zeros_like(px)], 1))
    return v.set_stroke(color, width)


def eye_mob(traces, center, width=2.6, height=1.7, color=APL, opacity=0.18, stroke=1.3, clip=1.6, scale=None):
    """Overlay of equal-length traces (an eye diagram) centred at ``center``."""
    g = VGroup()
    s = scale if scale is not None else height / (2 * clip)
    for tr in traces:
        xs = np.linspace(-width / 2, width / 2, len(tr))
        pts = np.stack([xs, s * np.clip(tr, -clip, clip), np.zeros_like(xs)], 1) + np.asarray(center)
        g.add(VMobject().set_points_as_corners(pts).set_stroke(color, stroke, opacity=opacity))
    return g


def rlgc_slice(width=4.2, height=1.5, color=TEXT, labels=True, show=("R", "L", "G", "C"), lsize=20):
    """One short slice of a transmission line: series R and L, shunt G and C."""
    top, bot = height / 2, -height / 2
    parts = VGroup()
    x0, x1 = -width / 2, width / 2
    r = resistor(0.9, color=color).move_to([x0 + 0.95, top, 0])
    l = inductor(0.9, color=color, loops=4).move_to([x0 + 2.05, top, 0])
    g = resistor(0.9, color=color).rotate(PI / 2).move_to([x0 + 2.85, 0, 0])
    c = capacitor(0.9, color=color).rotate(PI / 2).move_to([x0 + 3.55, 0, 0])
    wires = VGroup(
        Line([x0, top, 0], r.get_left()), Line(r.get_right(), l.get_left()), Line(l.get_right(), [x1, top, 0]),
        Line([x0, bot, 0], [x1, bot, 0]),
        Line([g.get_x(), top, 0], g.get_top()), Line(g.get_bottom(), [g.get_x(), bot, 0]),
        Line([c.get_x(), top, 0], c.get_top()), Line(c.get_bottom(), [c.get_x(), bot, 0]),
    ).set_stroke(color, 2.5)
    dots = VGroup(*[Dot([x, y, 0], radius=0.045, color=color) for x in (g.get_x(), c.get_x()) for y in (top, bot)])
    parts.add(wires, r, l, g, c, dots)
    lab = VGroup()
    if labels:
        lab.add(TeX(r"R'\,\Delta x", size=lsize, color=HAZARD).next_to(r, UP, buff=0.12))
        lab.add(TeX(r"L'\,\Delta x", size=lsize, color=BLUE).next_to(l, UP, buff=0.12))
        lab.add(TeX(r"G'\,\Delta x", size=lsize, color=HAZARD).next_to(g, LEFT, buff=0.1))
        lab.add(TeX(r"C'\,\Delta x", size=lsize, color=GOOD).next_to(c, RIGHT, buff=0.1))
    grp = VGroup(parts, lab)
    grp.r, grp.l, grp.g, grp.c, grp.labels = r, l, g, c, lab
    return grp


def stems(values, x0, dx, y0, scale, color=APL, radius=0.05, width=3):
    """Stem plot (sampled values)."""
    g = VGroup()
    for i, v in enumerate(values):
        x = x0 + i * dx
        top = [x, y0 + scale * v, 0]
        g.add(VGroup(Line([x, y0, 0], top, stroke_color=color, stroke_width=width), Dot(top, radius=radius, color=color)))
    return g


def timeline(entries, x0=-6.2, x1=6.2, y=0.0, color=MUTED, size=17, up_first=True, even=False):
    """Horizontal timeline; entries = [(year, label, colour[, shown year])] (years set the spacing)."""
    years = [e[0] for e in entries]
    lo, hi = min(years), max(years)
    axis = Line([x0, y, 0], [x1, y, 0], stroke_color=DIM, stroke_width=2.5)
    marks = VGroup()
    for i, e in enumerate(entries):
        yr, lab, col = e[:3]
        shown = e[3] if len(e) > 3 else str(yr)
        if even:
            x = x0 + i / max(1, len(entries) - 1) * (x1 - x0)
        else:
            x = x0 + (yr - lo) / (hi - lo) * (x1 - x0) if hi > lo else (x0 + x1) / 2
        d = Dot([x, y, 0], radius=0.07, color=col)
        up = (i % 2 == 0) == up_first
        yt = T(shown, size=size, color=col, weight=BOLD)
        lt = T(lab, size=size - 2, color=TEXT)
        stack = VGroup(yt, lt).arrange(DOWN, buff=0.05)
        stack.next_to(d, UP if up else DOWN, buff=0.18)
        marks.add(VGroup(d, stack))
    return VGroup(axis, marks)
