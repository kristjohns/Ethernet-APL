"""Visual language: palette, typography and small styling helpers.

Colour semantics are kept strict across the whole video so the viewer can
read a frame at a glance:
  * CAN bus ............ amber
  * Ethernet-APL ....... cyan
  * power / energy ..... yellow
  * hazard / Ex ........ orange
  * far-end / remote ... violet
"""

from pathlib import Path

from manim import *  # noqa: F401,F403

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

# ---------------------------------------------------------------- palette
BG = "#0A0F1E"
BG_2 = "#0E1528"
PANEL = "#121B31"
PANEL_EDGE = "#24314F"
GRID = "#1A2540"
TEXT = "#E8EEF8"
MUTED = "#8C9AB5"
DIM = "#55627E"

APL = "#22D3EE"
APL_DEEP = "#0891B2"
CAN = "#F5A524"
CAN_DEEP = "#B66A06"
POWER = "#FACC15"
HAZARD = "#FB923C"
DANGER = "#F43F5E"
GOOD = "#34D399"
VIOLET = "#A78BFA"
PINK = "#F472B6"
BLUE = "#60A5FA"
WHITE_SOFT = "#F5F7FB"

FONT = "Inter"
FONT_DISPLAY = "Inter Display"
MONO = "JetBrains Mono"

config.background_color = BG


# ---------------------------------------------------------------- text
def T(text, size=32, color=TEXT, weight=NORMAL, font=FONT, **kw):
    """Body text with the house defaults."""
    return Text(text, font=font, font_size=size, color=color, weight=weight, **kw)


def H(text, size=56, color=TEXT, weight=BOLD, **kw):
    """Display heading."""
    return Text(text, font=FONT_DISPLAY, font_size=size, color=color, weight=weight, **kw)


def M(text, size=28, color=TEXT, weight=NORMAL, **kw):
    """Monospace text (bits, symbols, identifiers)."""
    return Text(text, font=MONO, font_size=size, color=color, weight=weight, **kw)


def TeX(*tex, size=40, color=TEXT, **kw):
    """Sans-serif maths that sits well next to Inter."""
    return MathTex(*tex, font_size=size, color=color, tex_template=SANS_TEX, **kw)


SANS_TEX = TexTemplate()
SANS_TEX.add_to_preamble(r"\usepackage{cmbright}\usepackage{amsmath}\usepackage{siunitx}")


# ---------------------------------------------------------------- shapes
def glow(mob, color=None, layers=6, max_width=18, max_opacity=0.28):
    """Soft neon halo: stacked, widening, fading copies of a stroked mobject."""
    color = color or mob.get_stroke_color()
    halo = VGroup()
    base_w = max(mob.get_stroke_width(), 1)
    for i in range(layers):
        a = (i + 1) / layers
        c = mob.copy().set_fill(opacity=0)
        c.set_stroke(color=color, width=base_w + max_width * a, opacity=max_opacity * (1 - a) ** 1.6 + 0.01)
        halo.add(c)
    return halo


def panel(width, height, color=PANEL, edge=PANEL_EDGE, radius=0.18, opacity=0.92, stroke=1.6):
    return RoundedRectangle(
        width=width, height=height, corner_radius=radius,
        fill_color=color, fill_opacity=opacity, stroke_color=edge, stroke_width=stroke,
    )


def pill(text, color=APL, size=24, text_color=None, pad_x=0.28, pad_y=0.14, fill_opacity=0.16, weight=BOLD):
    label = T(text, size=size, color=text_color or color, weight=weight)
    box = RoundedRectangle(
        width=label.width + 2 * pad_x, height=label.height + 2 * pad_y,
        corner_radius=(label.height + 2 * pad_y) / 2,
        fill_color=color, fill_opacity=fill_opacity, stroke_color=color, stroke_width=1.5,
    )
    label.move_to(box)
    return VGroup(box, label)


def icon(name, color=TEXT, height=0.6, stroke_width=2.4):
    """Tabler outline icon (MIT) recoloured for the dark theme."""
    svg = SVGMobject(str(ASSETS / "icons" / f"{name}.svg"), height=height)
    svg.set_fill(opacity=0)
    svg.set_stroke(color=color, width=stroke_width, opacity=1)
    return svg


def hatch(mob, color=HAZARD, spacing=0.22, angle=PI / 4, width=1.2, opacity=0.35):
    """Diagonal hatching clipped to the bounding box of a rectangle-like mobject."""
    w, h = mob.width, mob.height
    c = mob.get_center()
    lines = VGroup()
    d = np.array([np.cos(angle), np.sin(angle), 0])
    n = np.array([-np.sin(angle), np.cos(angle), 0])
    span = (w + h)
    k = -span
    while k <= span:
        p0 = c + n * k - d * span
        p1 = c + n * k + d * span
        seg = _clip_segment(p0, p1, c[0] - w / 2, c[0] + w / 2, c[1] - h / 2, c[1] + h / 2)
        if seg is not None:
            lines.add(Line(seg[0], seg[1], stroke_color=color, stroke_width=width, stroke_opacity=opacity))
        k += spacing
    return lines


def _clip_segment(p0, p1, xmin, xmax, ymin, ymax):
    """Liang-Barsky clip of a 2D segment against an axis-aligned box."""
    x0, y0, x1, y1 = p0[0], p0[1], p1[0], p1[1]
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xmin), (dx, xmax - x0), (-dy, y0 - ymin), (dy, ymax - y0)):
        if p == 0:
            if q < 0:
                return None
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if t0 > t1:
        return None
    return (np.array([x0 + t0 * dx, y0 + t0 * dy, 0]), np.array([x0 + t1 * dx, y0 + t1 * dy, 0]))


def background_grid(color=GRID, step=0.5, opacity=0.35):
    """Faint engineering-paper grid that fades towards the edges."""
    g = VGroup()
    fw, fh = config.frame_width, config.frame_height
    x = -fw / 2
    while x <= fw / 2 + 1e-6:
        g.add(Line([x, -fh / 2, 0], [x, fh / 2, 0], stroke_width=1, stroke_color=color))
        x += step
    y = -fh / 2
    while y <= fh / 2 + 1e-6:
        g.add(Line([-fw / 2, y, 0], [fw / 2, y, 0], stroke_width=1, stroke_color=color))
        y += step
    for ln in g:
        mid = ln.get_center()
        r = np.hypot(mid[0] / (fw / 2), mid[1] / (fh / 2))
        ln.set_stroke(opacity=opacity * max(0.0, 1 - 0.75 * r))
    return g
