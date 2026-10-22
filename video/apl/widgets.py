"""Reusable mobjects: devices, cables, circuit symbols, waveforms, packets."""

from __future__ import annotations

import numpy as np
from manim import *  # noqa: F401,F403

from .style import (
    APL, BG, CAN, DIM, FONT_DISPLAY, GOOD, MUTED, PANEL, PANEL_EDGE, POWER, TEXT, VIOLET,
    H, T, M, glow, icon,
)


# ---------------------------------------------------------------- boxes
def device(label, icon_name=None, color=APL, width=1.7, height=1.25, label_size=20,
           sub=None, sub_color=MUTED, icon_scale=0.42, fill=PANEL):
    box = RoundedRectangle(width=width, height=height, corner_radius=0.14,
                           fill_color=fill, fill_opacity=1, stroke_color=color, stroke_width=2.4)
    parts = [box]
    if not label:
        if icon_name:
            parts.append(icon(icon_name, color=color, height=height * icon_scale).move_to(box))
        g = VGroup(*parts)
        g.box = box
        return g
    txt = T(label, size=label_size, color=TEXT, weight=BOLD)
    if txt.width > width * 0.88:
        txt.scale_to_fit_width(width * 0.88)
    if icon_name:
        ic = icon(icon_name, color=color, height=height * icon_scale)
        stack = VGroup(ic, txt).arrange(DOWN, buff=0.1)
        if sub:
            s = T(sub, size=label_size * 0.72, color=sub_color)
            stack = VGroup(ic, txt, s).arrange(DOWN, buff=0.07)
        stack.move_to(box)
        parts += list(stack)
    else:
        if sub:
            s = T(sub, size=label_size * 0.72, color=sub_color)
            stack = VGroup(txt, s).arrange(DOWN, buff=0.07).move_to(box)
            parts += list(stack)
        else:
            parts.append(txt.move_to(box))
    g = VGroup(*parts)
    g.box = box
    return g


def chip(text, color=APL, size=22, width=None, height=0.5, fill_opacity=0.12):
    t = T(text, size=size, color=color, weight=BOLD)
    w = width or t.width + 0.4
    r = RoundedRectangle(width=w, height=height, corner_radius=0.1, fill_color=color,
                         fill_opacity=fill_opacity, stroke_color=color, stroke_width=1.6)
    t.move_to(r)
    return VGroup(r, t)


# ---------------------------------------------------------------- cables
def _resample(path: VMobject, n: int):
    pts = np.array([path.point_from_proportion(a) for a in np.linspace(0, 1, n)])
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    normal = np.stack([-tang[:, 1], tang[:, 0], np.zeros(len(tang))], axis=1)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    return pts, normal, s


def twisted_pair(path, color_a=APL, color_b=None, amp=0.055, pitch=0.32, width=3.0, n=None):
    """Two conductors twisting around ``path`` (a 2D projection of a twisted pair)."""
    if isinstance(path, (list, tuple, np.ndarray)) and len(path) == 2 and not isinstance(path, VMobject):
        path = Line(path[0], path[1])
    color_b = color_b or interpolate_color(ManimColor(color_a), ManimColor(BG), 0.45)
    length = path.get_arc_length() if hasattr(path, "get_arc_length") else 5
    n = n or max(60, int(length / pitch * 14))
    pts, nrm, s = _resample(path, n)
    ph = 2 * np.pi * s / pitch
    a = VMobject().set_points_smoothly(pts + nrm * (amp * np.sin(ph))[:, None])
    b = VMobject().set_points_smoothly(pts - nrm * (amp * np.sin(ph))[:, None])
    a.set_stroke(color_a, width)
    b.set_stroke(color_b, width)
    g = VGroup(b, a)
    g.spine = path
    return g


def cable(p0, p1, color=APL, width=5, opacity=1.0):
    ln = Line(p0, p1, stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    return ln


# ---------------------------------------------------------------- circuit symbols
def resistor(length=1.0, color=TEXT, width=2.5, zigs=6, amp=0.12, label=None, label_size=22):
    lead = length * 0.18
    body = length - 2 * lead
    pts = [LEFT * length / 2, LEFT * (length / 2 - lead)]
    for i in range(zigs):
        x = -body / 2 + body * (i + 0.5) / zigs
        pts.append(np.array([x, amp if i % 2 == 0 else -amp, 0]))
    pts += [RIGHT * (length / 2 - lead), RIGHT * length / 2]
    z = VMobject().set_points_as_corners(pts).set_stroke(color, width)
    g = VGroup(z)
    if label:
        g.add(T(label, size=label_size, color=color).next_to(z, UP, buff=0.12))
    return g


def capacitor(length=0.8, color=TEXT, width=2.5, plate=0.32, gap=0.11):
    l1 = Line(LEFT * length / 2, LEFT * gap / 2)
    l2 = Line(RIGHT * gap / 2, RIGHT * length / 2)
    p1 = Line(LEFT * gap / 2 + UP * plate / 2, LEFT * gap / 2 + DOWN * plate / 2)
    p2 = Line(RIGHT * gap / 2 + UP * plate / 2, RIGHT * gap / 2 + DOWN * plate / 2)
    g = VGroup(l1, l2, p1, p2).set_stroke(color, width)
    return g


def inductor(length=1.0, color=TEXT, width=2.5, loops=4, r=None):
    lead = length * 0.15
    body = length - 2 * lead
    r = r or body / (2 * loops)
    parts = [Line(LEFT * length / 2, LEFT * body / 2)]
    for i in range(loops):
        cx = -body / 2 + r * (2 * i + 1)
        parts.append(Arc(radius=r, start_angle=PI, angle=-PI, arc_center=[cx, 0, 0]))
    parts.append(Line(RIGHT * body / 2, RIGHT * length / 2))
    return VGroup(*parts).set_stroke(color, width)


def ground(color=TEXT, width=2.5, size=0.3):
    return VGroup(
        Line(UP * size * 0.6, ORIGIN),
        Line(LEFT * size / 2, RIGHT * size / 2),
        Line(LEFT * size / 3 + DOWN * size * 0.18, RIGHT * size / 3 + DOWN * size * 0.18),
        Line(LEFT * size / 6 + DOWN * size * 0.36, RIGHT * size / 6 + DOWN * size * 0.36),
    ).set_stroke(color, width)


def dc_source(radius=0.32, color=POWER, width=2.5, label=None):
    c = Circle(radius=radius).set_stroke(color, width)
    plus = T("+", size=24, color=color).move_to(c.get_center() + UP * radius * 0.42)
    minus = T("−", size=24, color=color).move_to(c.get_center() + DOWN * radius * 0.42)
    g = VGroup(c, plus, minus)
    if label:
        g.add(T(label, size=20, color=color).next_to(c, LEFT, buff=0.12))
    return g


# ---------------------------------------------------------------- waveforms
def polyline(points, color=APL, width=3.0):
    v = VMobject()
    v.set_points_as_corners([np.array([p[0], p[1], 0]) for p in points])
    v.set_stroke(color, width)
    return v


def step_points(levels, t0, dt, y_of=lambda v: v, x_of=lambda t: t, edge=0.0):
    """Corner points for a step waveform; ``edge`` gives finite rise time (fraction of dt)."""
    pts = []
    t = t0
    for i, v in enumerate(levels):
        y = y_of(v)
        if i == 0:
            pts.append((x_of(t), y))
        else:
            pts.append((x_of(t + edge * dt), y))
        pts.append((x_of(t + dt), y))
        t += dt
    return pts


def ternary_waveform(symbols, x0, x1, y_mid, amp, color=APL, width=3, edge=0.12):
    dt = (x1 - x0) / len(symbols)
    pts = step_points(symbols, x0, dt, y_of=lambda v: y_mid + amp * v, edge=edge)
    return polyline(pts, color, width)


# ---------------------------------------------------------------- particles
def packet(color=APL, radius=0.07, glow_layers=4):
    d = Dot(radius=radius, color=color)
    halo = VGroup(*[Dot(radius=radius * (1 + 0.9 * (i + 1)), color=color).set_opacity(0.18 / (i + 1))
                    for i in range(glow_layers)])
    return VGroup(halo, d)


def flow_along(path: VMobject, n=6, color=APL, speed=0.25, radius=0.06, reverse=False, phase=0.0):
    """A train of glowing packets that loops along ``path`` forever (uses an updater)."""
    group = VGroup(*[packet(color, radius) for _ in range(n)])
    tracker = {"t": phase}

    def upd(g, dt):
        tracker["t"] = (tracker["t"] + dt * speed) % 1.0
        for i, p in enumerate(g):
            a = (tracker["t"] + i / n) % 1.0
            if reverse:
                a = 1 - a
            p.move_to(path.point_from_proportion(a))
            fade = min(1.0, 8 * min(a, 1 - a))
            p.set_opacity(fade)
            p[0].set_opacity(0.0)  # halo handled below
            for k, h in enumerate(p[0]):
                h.set_opacity(fade * 0.18 / (k + 1))

    group.add_updater(upd)
    upd(group, 0)
    return group


# ---------------------------------------------------------------- titles
def chapter_title(number, title, subtitle=None, color=APL):
    num = Text(f"{number:02d}", font=FONT_DISPLAY, font_size=150, weight=BOLD, color=color)
    num.set_opacity(0.95)
    ttl = H(title, size=60)
    grp = VGroup(ttl)
    if subtitle:
        sub = T(subtitle, size=30, color=MUTED)
        grp = VGroup(ttl, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    bar = Line(UP * 0.9, DOWN * 0.9, stroke_color=color, stroke_width=6)
    whole = VGroup(num, bar, grp).arrange(RIGHT, buff=0.5)
    return whole


def corner_tag(text, color=APL):
    dot = Dot(radius=0.06, color=color)
    t = T(text, size=20, color=MUTED, weight=MEDIUM)
    g = VGroup(dot, t).arrange(RIGHT, buff=0.15)
    g.to_corner(UL, buff=0.35)
    return g


def lower_third(text, color=APL, size=26):
    t = T(text, size=size, color=TEXT)
    bar = Rectangle(width=0.08, height=t.height + 0.2, fill_color=color, fill_opacity=1, stroke_width=0)
    g = VGroup(bar, t).arrange(RIGHT, buff=0.2)
    return g


def check(color=GOOD, size=0.4, width=6):
    return VMobject().set_points_as_corners(
        [LEFT * size * 0.5 + UP * size * 0.02, LEFT * size * 0.12 + DOWN * size * 0.35, RIGHT * size * 0.55 + UP * size * 0.45]
    ).set_stroke(color, width)


def cross(color="#F43F5E", size=0.36, width=6):
    return VGroup(
        Line(UL * size / 2, DR * size / 2), Line(UR * size / 2, DL * size / 2)
    ).set_stroke(color, width)


# ---------------------------------------------------------------- pseudo-3D twisted pair
class TwistedPair3D(VGroup):
    """A twisted pair rendered with perspective, depth sorting and tube shading.

    Geometry lives in 3D (x along the cable); ``set_view`` re-projects it.
    Each conductor is drawn as short segments with a dark core, a coloured
    body and a specular highlight, all depth-sorted, so the two conductors
    correctly pass in front of / behind each other.  Pulses are beads riding
    on either conductor: list of (wire, x, colour, strength).
    """

    def __init__(self, length=14.0, radius=0.13, pitch=1.3, segments=240,
                 colors=(APL, VIOLET), width=18.0, focal=11.0, **kw):
        super().__init__(**kw)
        self.length, self.radius, self.pitch = length, radius, pitch
        self.n = segments
        self.colors = [ManimColor(c) for c in colors]
        self.base_width = width
        self.focal = focal
        self.spin, self.yaw, self.pitch_angle = 0.0, 0.0, 0.0
        self.offset = np.zeros(3)
        self.pulses = []
        self.fade = 1.0  # master opacity (animate this instead of FadeIn: submobjects re-sort every frame)
        self.segs = []
        for _ in range(2):
            wire = []
            for _ in range(segments):
                body = Line(ORIGIN, RIGHT).set_cap_style(CapStyleType.ROUND)
                hi = Line(ORIGIN, RIGHT).set_cap_style(CapStyleType.ROUND)
                wire.append(VGroup(body, hi))
            self.segs.append(wire)
        self.beads = []
        self.set_view()

    def _xyz(self, wire, x):
        """Vectorised: x may be an array; returns (N, 3)."""
        x = np.atleast_1d(np.asarray(x, dtype=float))
        th = 2 * np.pi * x / self.pitch + self.spin + wire * np.pi
        p0, p1, p2 = x, self.radius * np.cos(th), self.radius * np.sin(th)
        cb, sb = np.cos(self.yaw), np.sin(self.yaw)
        q0, q1, q2 = p0 * cb + p2 * sb, p1, -p0 * sb + p2 * cb
        ca, sa = np.cos(self.pitch_angle), np.sin(self.pitch_angle)
        return np.stack([q0, q1 * ca - q2 * sa, q1 * sa + q2 * ca], axis=1)

    def _proj(self, p):
        p = np.atleast_2d(p)
        k = self.focal / (self.focal - p[:, 2])
        out = np.stack([p[:, 0] * k, p[:, 1] * k, np.zeros(len(p))], axis=1) + self.offset
        return out, k

    def set_view(self, spin=None, yaw=None, pitch=None, pulses=None, offset=None, fade=None):
        if spin is not None:
            self.spin = spin
        if yaw is not None:
            self.yaw = yaw
        if pitch is not None:
            self.pitch_angle = pitch
        if pulses is not None:
            self.pulses = pulses
        if offset is not None:
            self.offset = np.array(offset, dtype=float)
        if fade is not None:
            self.fade = fade
        xs = np.linspace(-self.length / 2, self.length / 2, self.n + 1)
        xm = 0.5 * (xs[:-1] + xs[1:])
        xfade = self.fade * np.clip(1.25 - np.abs(xm) / (self.length / 2), 0, 1) ** 0.7
        dark = np.array(ManimColor("#0A0F1E").to_rgb())
        white = np.ones(3)
        items = []
        thirds = np.array([0, 1 / 3, 2 / 3, 1.0])[:, None]
        for wire in (0, 1):
            pts3 = self._xyz(wire, xs)
            P, K = self._proj(pts3)
            z = 0.5 * (pts3[:-1, 2] + pts3[1:, 2])
            th = 2 * np.pi * xm / self.pitch + self.spin + wire * np.pi
            lit = 0.5 + 0.5 * np.sin(th)
            k = 0.5 * (K[:-1] + K[1:])
            base = np.array(self.colors[wire].to_rgb())
            body_rgb = dark[None, :] + (base - dark)[None, :] * (0.35 + 0.65 * lit)[:, None]
            hi_rgb = base + (white - base) * 0.55
            up = np.array([0, 1, 0]) * 0.0042
            for i in range(self.n):
                a, b = P[i], P[i + 1]
                if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-6:
                    b = b + np.array([1e-4, 0, 0])
                body, hi = self.segs[wire][i]
                w = self.base_width * k[i]
                body.points = a + (b - a) * thirds
                body.stroke_rgbas = np.array([[*body_rgb[i], xfade[i]]])
                body.stroke_width = w
                off = up * w
                hi.points = a + off + (b - a) * thirds
                hi.stroke_rgbas = np.array([[*hi_rgb, xfade[i] * (0.15 + 0.75 * lit[i])]])
                hi.stroke_width = w * 0.22
                items.append((z[i], self.segs[wire][i]))
        while len(self.beads) < len(self.pulses):
            bead = VGroup(*[Dot(radius=1.0) for _ in range(5)])
            self.beads.append(bead)
        for j, bead in enumerate(self.beads):
            if j < len(self.pulses):
                wire, x, col, strength = self.pulses[j]
                p = self._xyz(wire, x)[0]
                cc, kk = self._proj(p)
                c, k = cc[0], kk[0]
                radii = [0.42, 0.30, 0.2, 0.13, 0.075]
                ops = [0.06, 0.1, 0.18, 0.4, 1.0]
                for d, r, o in zip(bead, radii, ops):
                    d.set_stroke(width=0)
                    d.set_fill(interpolate_color(ManimColor(col), ManimColor("#FFFFFF"), 0.5 if o == 1.0 else 0.0),
                               opacity=o * strength * self.fade)
                    d.scale_to_fit_width(2 * r * k)
                    d.move_to(c)
                items.append((p[2] + 0.05, bead))
            else:
                for d in bead:
                    d.set_fill(opacity=0)
        items.sort(key=lambda t: t[0])
        self.submobjects = [m for _, m in items]
        return self


# ---------------------------------------------------------------- axis labels in the house font
def tick_labels(ax, values, axis="x", fmt="{:g}", size=18, color=MUTED, buff=0.18, texts=None):
    """Inter-font tick labels (Manim's default coordinates use LaTeX serif digits)."""
    g = VGroup()
    for i, v in enumerate(values):
        s = texts[i] if texts else fmt.format(v)
        t = T(s, size=size, color=color)
        if axis == "x":
            t.next_to(ax.c2p(v, ax.y_range[0]), DOWN, buff=buff)
        else:
            t.next_to(ax.c2p(ax.x_range[0], v), LEFT, buff=buff)
        g.add(t)
    return g
