import sys
from math import erfc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *

COPPER = "#C98A55"
LAND = "#151F37"
SEA = "#0C1830"


def coast(x_edge, side, seed, y0=-2.15, y1=2.15):
    """Irregular coastline polygon filling from x_edge to the frame edge on ``side`` (-1 left, +1 right)."""
    rng = np.random.default_rng(seed)
    ys = np.linspace(y1, y0, 40)
    k = rng.normal(0, 1, (4, 2))
    xs = x_edge + sum(0.18 / (i + 1) * (k[i, 0] * np.sin((i + 1) * 1.7 * ys + k[i, 1])) for i in range(4))
    far = 7.4 * side
    pts = [[far, y1, 0]] + [[x, y, 0] for x, y in zip(xs, ys)] + [[far, y0, 0]]
    return Polygon(*pts, fill_color=LAND, fill_opacity=1, stroke_color="#2C3B5E", stroke_width=2)


def kelvin_hump(t, tau):
    """Far-end response of an RC (diffusion) line to a short pulse, peak normalised at t = tau."""
    t = np.maximum(np.asarray(t, dtype=float), 1e-6)
    a = 1.5 * tau                       # t_peak = 2a/3
    v = t ** -1.5 * np.exp(-a / t)
    return v / (tau ** -1.5 * np.exp(-1.5))


class Telegraph(APLScene):
    def construct(self):
        self.tag = corner_tag("04 · From coax to one pair")
        self.add(self.tag)

        # ------------------------------------------------------------ the journey map
        jm = JourneyMap()
        with self.voice(
            "{map}From here on, we'll follow a single bit through the physical layer. {tx}A transmitter turns bits into "
            "voltages. {wire}A kilometer of twisted pair carries them — and mangles them on the way. {rx}And a receiver "
            "turns whatever arrives back into bits. {first}We'll start in the middle, with the wire itself."
        ) as v:
            self.play(FadeIn(jm.tx[0], shift=DOWN * 0.1), run_time=0.6)
            v.wait_until("tx")
            self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in jm.tx[1:]], lag_ratio=0.25),
                      LaggedStart(*[GrowArrow(a) for a in jm.arrows[:4]], lag_ratio=0.25), run_time=1.6)
            v.wait_until("wire")
            self.play(Create(jm.cable), FadeIn(jm.cable_lbl), run_time=1.4)
            v.wait_until("rx")
            self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in jm.rx], lag_ratio=0.25),
                      LaggedStart(*[GrowArrow(a) for a in jm.arrows[4:]], lag_ratio=0.25), run_time=1.6)
            self.play(FadeIn(jm.badges), run_time=0.5)
            v.wait_until("first")
            self.play(*jm.focus("wire"), run_time=0.8)
            self.play(jm.cable.animate.scale(1.08), rate_func=there_and_back, run_time=0.6)
        self.clear(run_time=0.6)

        self.chapter(5, "The wire is a waveguide", "Kelvin, Heaviside, and a kilometer of copper")

        # ------------------------------------------------------------ 1858
        sea = Rectangle(width=14.6, height=4.3, fill_color=SEA, fill_opacity=1, stroke_width=0).move_to([0, 0.0, 0])
        ripples = VGroup()
        rng = np.random.default_rng(7)
        for _ in range(26):
            x, y = rng.uniform(-4.4, 4.4), rng.uniform(-1.9, 1.9)
            ripples.add(ArcBetweenPoints([x - 0.22, y, 0], [x + 0.22, y, 0], angle=-PI / 3, stroke_color="#1E3357", stroke_width=2))
        nf = coast(-5.0, -1, 3)
        ie = coast(5.25, 1, 11)
        p0, p1 = np.array([-5.05, 0.75, 0]), np.array([5.2, 0.55, 0])
        cable_path = CubicBezier(p0, p0 + np.array([2.5, -2.4, 0]), p1 + np.array([-2.5, -2.4, 0]), p1)
        cable_path.set_stroke(COPPER, 4)
        lbl_ie = VGroup(T("Valentia", size=20, color=TEXT, weight=BOLD), T("Ireland", size=16, color=MUTED)).arrange(DOWN, buff=0.04)
        lbl_ie.move_to([6.2, 1.55, 0])
        lbl_nf = VGroup(T("Trinity Bay", size=20, color=TEXT, weight=BOLD), T("Newfoundland", size=16, color=MUTED)).arrange(DOWN, buff=0.04)
        lbl_nf.move_to([-6.15, 1.55, 0])
        year = H("1858", size=54, color=COPPER).move_to([0, 3.05, 0])
        sub = T("the first transatlantic telegraph cable", size=22, color=MUTED).next_to(year, DOWN, buff=0.08)

        sc_tx = scope(2.7, 1.25, "sent (Ireland)", COPPER).move_to([4.55, -3.05, 0])
        sc_rx = scope(2.7, 1.25, "received (Newfoundland)", COPPER).move_to([-4.55, -3.05, 0])
        ts = np.linspace(0, 6, 300)
        tx_tr = trace_in(sc_tx.box, ts, np.where((ts > 0.4) & (ts < 0.75), 1.0, 0.0), COPPER, 3, y_range=(-0.15, 1.15))
        rx_tr = trace_in(sc_rx.box, ts, 0.92 * kelvin_hump(ts - 0.4, 1.6), COPPER, 3, y_range=(-0.15, 1.15))
        sec_lbl = T("time (s) →", size=14, color=DIM).next_to(sc_rx.box, RIGHT, buff=0.12).align_to(sc_rx.box, DOWN)

        bead = packet(COPPER, radius=0.08)
        prog = ValueTracker(0.0)

        def bead_upd(m):
            a = prog.get_value()
            m.move_to(cable_path.point_from_proportion(1 - a))
            spread = 1 + 5 * a
            for k, h in enumerate(m[0]):
                h.set_opacity(0.2 / (k + 1) * (1 - 0.6 * a))
            m[0].stretch_to_fit_width(0.5 * spread)
            m[1].set_opacity(1 - 0.75 * a)

        bead.add_updater(bead_upd)

        with self.voice(
            "{y}In the summer of 1858, the first telegraph cable across the Atlantic went into service, from Ireland to "
            "Newfoundland. {tri}It was a triumph — and a disappointment. {smear}A crisp pulse sent at one end arrived at the "
            "other smeared out over seconds. {queen}Queen Victoria's ninety-eight-word greeting took most of a day to get through."
        ) as v:
            self.play(FadeIn(sea), FadeIn(nf, shift=RIGHT * 0.3), FadeIn(ie, shift=LEFT * 0.3), run_time=1.0)
            self.play(LaggedStart(*[Create(r) for r in ripples], lag_ratio=0.03), FadeIn(year, shift=DOWN * 0.2),
                      FadeIn(sub), run_time=1.2)
            self.play(Create(cable_path), FadeIn(lbl_ie), FadeIn(lbl_nf), run_time=1.8)
            v.wait_until("smear")
            self.play(FadeIn(sc_tx), FadeIn(sc_rx), run_time=0.5)
            self.play(Create(tx_tr), run_time=0.6)
            self.add(bead)
            self.play(prog.animate.set_value(1.0), run_time=2.6, rate_func=linear)
            bead.clear_updaters()
            self.play(Create(rx_tr), FadeIn(sec_lbl), FadeOut(bead), run_time=1.4)
            v.wait_until("queen")
            q = pill("98 words  ≈  16 hours", COPPER, size=22).move_to([0, -1.75, 0])
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.clear(run_time=0.7)

        # ------------------------------------------------------------ Kelvin's RC model
        kel = name_card("William Thomson (Lord Kelvin)", "1855", "On the theory of the electric telegraph", COPPER)
        kel.to_corner(UR, buff=0.4).shift(DOWN * 0.15)
        n_sec = 6
        x_l, x_r, y_t, y_b = -6.0, 3.2, 1.75, 0.45
        dxs = (x_r - x_l) / n_sec
        ladder = VGroup()
        for i in range(n_sec):
            xa = x_l + i * dxs
            r = resistor(dxs * 0.62, color=TEXT, zigs=5, amp=0.1).move_to([xa + dxs * 0.42, y_t, 0])
            ladder.add(Line([xa, y_t, 0], r.get_left()), r, Line(r.get_right(), [xa + dxs, y_t, 0]))
            c = capacitor(0.62, color=TEXT).rotate(PI / 2).move_to([xa + dxs * 0.85, (y_t + y_b) / 2, 0])
            ladder.add(Line([c.get_x(), y_t, 0], c.get_top()), c, Line(c.get_bottom(), [c.get_x(), y_b, 0]),
                       Dot([c.get_x(), y_t, 0], radius=0.04, color=TEXT))
        ladder.add(Line([x_l, y_b, 0], [x_r, y_b, 0]))
        ladder.set_stroke(TEXT, 2.4)
        sea_line = Line([x_l, y_b, 0], [x_r, y_b, 0], stroke_color=BLUE, stroke_width=4)
        lab_r = TeX(r"R'\,\Delta x", size=24, color=HAZARD).next_to(ladder[1], UP, buff=0.12)
        lab_c = TeX(r"C'\,\Delta x", size=24, color=GOOD).next_to(ladder[4], RIGHT, buff=0.1)
        lab_core = T("copper core", size=16, color=MUTED).next_to([x_r, y_t, 0], RIGHT, buff=0.15)
        lab_sea = T("the sea (return)", size=16, color=BLUE).next_to([x_r, y_b, 0], RIGHT, buff=0.15)
        lab_ins = T("gutta-percha insulation = capacitor", size=16, color=GOOD).next_to(ladder, DOWN, buff=0.18).align_to(ladder, LEFT)

        eq_cable = TeX(r"\frac{\partial v}{\partial t}", r"=", r"\frac{1}{R'C'}", r"\,\frac{\partial^2 v}{\partial x^2}", size=46)
        eq_cable[2].set_color(COPPER)
        eq_heat = TeX(r"\frac{\partial T}{\partial t}", r"=", r"\alpha", r"\,\frac{\partial^2 T}{\partial x^2}", size=46)
        eq_heat[2].set_color(HAZARD)
        eq_cable.move_to([-3.3, -1.25, 0])
        eq_heat.move_to([3.3, -1.25, 0])
        cap_c = T("telegraph cable · Kelvin, 1855", size=18, color=COPPER).next_to(eq_cable, DOWN, buff=0.22)
        cap_h = T("heat conduction · Fourier, 1822", size=18, color=HAZARD).next_to(eq_heat, DOWN, buff=0.22)
        same = T("same equation", size=22, color=TEXT, weight=BOLD).move_to([0, -1.25, 0])
        arr_l = Arrow([-0.95, -1.25, 0], [-1.75, -1.25, 0], buff=0, stroke_width=3, color=MUTED, tip_length=0.16)
        arr_r = Arrow([0.95, -1.25, 0], [1.75, -1.25, 0], buff=0, stroke_width=3, color=MUTED, tip_length=0.16)

        with self.voice(
            "{kelvin}A few years earlier, William Thomson — later Lord Kelvin — had worked out why. {model}He modelled the "
            "cable as a resistance and a capacitance per meter. The copper core, its gutta-percha insulation and the sea "
            "around it form one enormous capacitor, and every piece of it must be charged through the resistance of the "
            "copper before it. {heat}What comes out is exactly the equation Fourier had written for heat."
        ) as v:
            self.play(FadeIn(kel, shift=LEFT * 0.2), run_time=0.7)
            v.wait_until("model")
            self.play(Create(ladder), run_time=2.2)
            self.play(FadeIn(lab_r), FadeIn(lab_c), FadeIn(lab_core), Create(sea_line), FadeIn(lab_sea), run_time=0.8)
            self.play(FadeIn(lab_ins), run_time=0.5)
            v.wait_until("heat")
            self.play(Write(eq_cable), FadeIn(cap_c), run_time=1.3)
            self.play(Write(eq_heat), FadeIn(cap_h), run_time=1.3)
            self.play(FadeIn(same), GrowArrow(arr_l), GrowArrow(arr_r), run_time=0.6)
            self.play(Indicate(eq_cable[2], color=COPPER), Indicate(eq_heat[2], color=HAZARD), run_time=0.9)

        # soak-in animation: a step applied at x = 0 creeps along the line like heat along a bar
        self.play(FadeOut(VGroup(ladder, sea_line, lab_r, lab_c, lab_core, lab_sea, lab_ins, same, arr_l, arr_r, cap_c, cap_h)),
                  eq_cable.animate.scale(0.7).move_to([-4.6, 2.45, 0]), eq_heat.animate.scale(0.7).move_to([-1.3, 2.45, 0]),
                  run_time=0.9)
        tt = ValueTracker(0.002)
        bx0, bx1, by = -5.6, 5.6, -1.85
        n_cells = 90
        cells = VGroup(*[Rectangle(width=(bx1 - bx0) / n_cells + 0.004, height=0.42, stroke_width=0)
                         .move_to([bx0 + (i + 0.5) * (bx1 - bx0) / n_cells, by, 0]) for i in range(n_cells)])
        bar_edge = Rectangle(width=bx1 - bx0, height=0.42, stroke_color=DIM, stroke_width=2).move_to([0, by, 0])
        hot = ManimColor(POWER)
        cold = ManimColor("#1A2540")

        def profile(x):
            D = 1.0
            return np.array([erfc(xi / (2 * np.sqrt(D * tt.get_value()))) for xi in np.atleast_1d(x)])

        def paint(m):
            xs = np.linspace(0, 10, n_cells)
            vals = profile(xs)
            for c, val in zip(m, vals):
                c.set_fill(interpolate_color(cold, hot, float(np.clip(val, 0, 1)) ** 0.8), opacity=1)

        cells.add_updater(paint)
        ax = Axes(x_range=[0, 10, 1], y_range=[0, 1.1, 0.5], x_length=bx1 - bx0, y_length=2.4,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0, 0.15, 0])
        curve = always_redraw(lambda: ax.plot(lambda x: float(profile(x)[0]), x_range=[0, 10, 0.05], color=POWER, stroke_width=3.5))
        src = VGroup(dc_source(0.3, POWER), T("key down", size=16, color=POWER)).arrange(DOWN, buff=0.08).next_to(bar_edge, LEFT, buff=0.25)
        y_lab = T("voltage along the cable", size=16, color=POWER).next_to(ax.c2p(0, 1.1), RIGHT, buff=0.15)
        x_lab = T("distance →", size=16, color=MUTED).next_to(bar_edge, DOWN, buff=0.12).align_to(bar_edge, RIGHT)
        with self.voice(
            "{soak}So a voltage step doesn't run down such a cable. {heatbar}It soaks in, the way heat creeps along a metal "
            "bar that's held in a flame at one end: quickly near the source, and ever more slowly further along."
        ) as v:
            self.play(FadeIn(bar_edge), FadeIn(cells), FadeIn(src), Create(ax), FadeIn(y_lab), FadeIn(x_lab), run_time=0.8)
            self.add(curve)
            v.wait_until("heatbar")
            self.play(tt.animate.set_value(30.0), run_time=v.until_end(4.5), rate_func=lambda a: a ** 2)
        cells.clear_updaters()
        self.remove(curve)
        self.clear(keep=[kel], run_time=0.6)

        # ------------------------------------------------------------ law of squares
        ax2 = Axes(x_range=[0, 10, 1], y_range=[0, 1.15, 0.5], x_length=8.6, y_length=3.6,
                   axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-1.6, -0.35, 0])
        c1 = ax2.plot(lambda t: kelvin_hump(t, 1.4), x_range=[0.05, 10, 0.02], color=COPPER, stroke_width=4)
        c2 = ax2.plot(lambda t: kelvin_hump(t, 5.6) / 4, x_range=[0.05, 10, 0.02], color=VIOLET, stroke_width=4)
        l1 = T("length x", size=19, color=COPPER, weight=BOLD).next_to(ax2.c2p(1.4, 1.0), RIGHT, buff=0.2)
        l2 = T("length 2x", size=19, color=VIOLET, weight=BOLD).next_to(ax2.c2p(5.6, 0.25), UP, buff=0.5)
        d1 = DashedLine(ax2.c2p(1.4, 0), ax2.c2p(1.4, 1.0), dash_length=0.06, stroke_color=COPPER, stroke_width=2)
        d2 = DashedLine(ax2.c2p(5.6, 0), ax2.c2p(5.6, 0.25), dash_length=0.06, stroke_color=VIOLET, stroke_width=2)
        tl1 = TeX(r"t_1", size=28, color=COPPER).next_to(ax2.c2p(1.4, 0), DOWN, buff=0.12)
        tl2 = TeX(r"4\,t_1", size=28, color=VIOLET).next_to(ax2.c2p(5.6, 0), DOWN, buff=0.12)
        xl = T("time at the far end →", size=17, color=MUTED).next_to(ax2, DOWN, buff=0.45).align_to(ax2, RIGHT)
        law = TeX(r"t_{\text{peak}}", r"=", r"\frac{R'C'\,x^2}{6}", size=50).move_to([4.6, 0.6, 0])
        law[2].set_color(COPPER)
        law_lbl = T("law of squares", size=22, color=COPPER, weight=BOLD).next_to(law, DOWN, buff=0.3)
        with self.voice(
            "{peak}At the far end, a short pulse shows up as a slow, low hump. Its peak arrives after a time proportional "
            "to R C x squared. {double}Double the length, and the signal takes four times as long, and arrives four times "
            "weaker. That's Kelvin's law of squares."
        ) as v:
            self.play(Create(ax2), FadeIn(xl), run_time=0.7)
            self.play(Create(c1), FadeIn(l1), run_time=1.3)
            self.play(Create(d1), FadeIn(tl1), Write(law), run_time=1.2)
            v.wait_until("double")
            self.play(Create(c2), FadeIn(l2), run_time=1.6)
            self.play(Create(d2), FadeIn(tl2), FadeIn(law_lbl), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ Whitehouse, and 1866
        quote = VGroup(T("“a fiction of the schools”", size=40, color=TEXT, weight=BOLD, slant=ITALIC),
                       T("— Wildman Whitehouse, the cable's chief electrician, on Kelvin's theory", size=20, color=MUTED)
                       ).arrange(DOWN, buff=0.25).move_to(UP * 1.6)
        bolt = icon("bolt", POWER, 1.0).move_to([-1.3, -0.6, 0])
        kv = T("≈ 2,000 V", size=40, color=POWER, weight=BOLD).next_to(bolt, RIGHT, buff=0.3)
        dead = VGroup(T("insulation fails", size=24, color=DANGER, weight=BOLD), T("silent after a few weeks", size=18, color=MUTED)
                      ).arrange(DOWN, buff=0.06).move_to([0, -2.1, 0])
        with self.voice(
            "{white}The cable's chief electrician, Wildman Whitehouse, dismissed the theory as 'a fiction of the schools'. "
            "{volts}He tried to force the signals through with induction coils of around two thousand volts. "
            "{dead}Within weeks the insulation broke down, and the cable fell silent."
        ) as v:
            self.play(FadeIn(quote[0], shift=UP * 0.1), run_time=0.9)
            self.play(FadeIn(quote[1]), run_time=0.6)
            v.wait_until("volts")
            self.play(FadeIn(bolt, scale=0.6), FadeIn(kv, shift=LEFT * 0.1), run_time=0.8)
            self.play(Flash(bolt, color=POWER, line_length=0.3, num_lines=12), run_time=0.6)
            v.wait_until("dead")
            self.play(FadeIn(dead, shift=UP * 0.1), run_time=0.7)
        self.clear(run_time=0.6)

        # mirror galvanometer: a tiny current, a tiny mirror, a long lever of light
        lamp = VGroup(Circle(0.16, fill_color=POWER, fill_opacity=1, stroke_width=0),
                      *[Circle(0.16 * (1 + 0.6 * k), stroke_width=0, fill_color=POWER, fill_opacity=0.12 / k) for k in (1, 2, 3)]
                      ).move_to([-5.2, -1.6, 0])
        mirror_c = np.array([-1.0, 1.2, 0])
        theta = ValueTracker(0.0)
        thread = Line(mirror_c + UP * 0.85, mirror_c + UP * 0.3, stroke_color=MUTED, stroke_width=1.5)
        coil = Ellipse(width=1.15, height=0.6, stroke_color=COPPER, stroke_width=5).move_to(mirror_c)
        scale_y = -1.6
        scale_bar = VGroup(Line([1.2, scale_y, 0], [6.2, scale_y, 0], stroke_color=TEXT, stroke_width=3),
                           *[Line([x, scale_y, 0], [x, scale_y + (0.18 if i % 5 == 0 else 0.1), 0], stroke_color=TEXT, stroke_width=2)
                             for i, x in enumerate(np.linspace(1.2, 6.2, 26))])

        def mirror():
            a = theta.get_value()
            d = np.array([np.cos(a), np.sin(a), 0]) * 0.32
            return Line(mirror_c - d, mirror_c + d, stroke_color=WHITE_SOFT, stroke_width=7)

        def beam():
            a = theta.get_value()
            inc = mirror_c - lamp.get_center()
            inc = inc / np.linalg.norm(inc)
            nrm = np.array([np.cos(a - PI / 2), np.sin(a - PI / 2), 0])
            out = inc - 2 * np.dot(inc, nrm) * nrm
            k = (scale_y - mirror_c[1]) / out[1]
            hit = mirror_c + k * out
            return VGroup(Line(lamp.get_center(), mirror_c, stroke_color=POWER, stroke_width=3, stroke_opacity=0.6),
                          Line(mirror_c, hit, stroke_color=POWER, stroke_width=3, stroke_opacity=0.8),
                          Dot(hit, radius=0.1, color=POWER))

        mir = always_redraw(mirror)
        bm = always_redraw(beam)
        title66 = VGroup(H("1866", size=48, color=GOOD), T("a better cable, read with a very sensitive instrument", size=22, color=MUTED)
                         ).arrange(DOWN, buff=0.08).to_edge(UP, buff=0.55).shift(RIGHT * 1.0)
        gal_lbl = T("Kelvin's mirror galvanometer", size=20, color=TEXT, weight=BOLD).next_to(coil, LEFT, buff=0.35).shift(UP * 0.45)
        cur = T("tiny current → tiny twist → big swing of the light spot", size=18, color=MUTED).move_to([2.0, -2.45, 0])
        with self.voice(
            "{success}The cable of 1866 was far better built, and it worked — read with Kelvin's mirror galvanometer, "
            "which needs only a minute current. {mirror}A tiny current twists a tiny mirror, and a beam of light turns "
            "that twist into a big swing of a spot across a scale."
        ) as v:
            self.play(FadeIn(title66, shift=DOWN * 0.1), run_time=0.8)
            self.play(FadeIn(lamp), Create(thread), Create(coil), FadeIn(mir), FadeIn(scale_bar), FadeIn(gal_lbl), run_time=1.0)
            self.add(bm)
            v.wait_until("mirror")
            self.play(FadeIn(cur), run_time=0.5)
            for a in (0.06, -0.05, 0.08, 0.0):
                self.play(theta.animate.set_value(a), run_time=0.7, rate_func=smooth)
        self.remove(bm, mir)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ Heaviside
        heav = name_card("Oliver Heaviside", "1880s", "self-taught telegraph engineer", BLUE).to_corner(UR, buff=0.4).shift(DOWN * 0.15)
        sl = rlgc_slice(width=4.6, height=1.45).move_to([-3.4, 1.55, 0])
        e1 = TeX(r"\frac{\partial v}{\partial x}", r"=", r"-R'\,i", r"-L'\,\frac{\partial i}{\partial t}", size=40)
        e2 = TeX(r"\frac{\partial i}{\partial x}", r"=", r"-G'\,v", r"-C'\,\frac{\partial v}{\partial t}", size=40)
        e1[2].set_color(HAZARD)
        e1[3].set_color(BLUE)
        e2[2].set_color(HAZARD)
        e2[3].set_color(GOOD)
        eqs = VGroup(e1, e2).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([3.3, 0.5, 0])
        tel_lbl = T("telegrapher's equations", size=20, color=MUTED).next_to(eqs, UP, buff=0.25)
        cond = TeX(r"\omega L' \gg R', \quad \omega C' \gg G'", size=34, color=TEXT).move_to([-3.4, -1.3, 0])
        arrow_c = Arrow(cond.get_right() + RIGHT * 0.15, cond.get_right() + RIGHT * 1.15, buff=0, stroke_width=3, color=MUTED, tip_length=0.16)
        weq = TeX(r"\frac{\partial^2 v}{\partial x^2}", r"=", r"L'C'", r"\,\frac{\partial^2 v}{\partial t^2}", size=44).next_to(arrow_c, RIGHT, buff=0.2)
        weq[2].set_color(APL)
        wave_lbl = T("the wave equation · d'Alembert, 1747", size=18, color=APL).next_to(weq, DOWN, buff=0.2)
        sol = TeX(r"v(x,t) = f(x - c\,t) + g(x + c\,t)", r",\qquad", r"c = \frac{1}{\sqrt{L'C'}}", size=38).move_to([0, -2.95, 0])
        sol[2].set_color(APL)

        with self.voice(
            "{heav}The full picture came from Oliver Heaviside, a self-taught telegraph engineer, in the 1880s. "
            "{l}He added what Kelvin had left out: the inductance — the magnetic inertia of the current — and the leakage "
            "through the insulation. {eqs}His telegrapher's equations describe one short slice of line. "
            "{wave}At low frequencies, resistance wins and you get Kelvin's diffusion. But once omega L is much larger "
            "than R, the equations turn into the wave equation — the same one d'Alembert solved for a vibrating string "
            "in 1747. {sol}Its solutions are shapes that travel, unchanged, in both directions, at a speed of one over the "
            "square root of L C."
        ) as v:
            self.play(FadeIn(heav, shift=LEFT * 0.2), run_time=0.7)
            self.play(Create(sl[0]), run_time=1.6)
            v.wait_until("l")
            self.play(FadeIn(sl.labels[0]), FadeIn(sl.labels[3]), run_time=0.5)
            self.play(Indicate(sl.l, color=BLUE, scale_factor=1.15), FadeIn(sl.labels[1]), run_time=0.9)
            self.play(Indicate(sl.g, color=HAZARD, scale_factor=1.15), FadeIn(sl.labels[2]), run_time=0.9)
            v.wait_until("eqs")
            self.play(FadeIn(tel_lbl), Write(e1), run_time=1.3)
            self.play(Write(e2), run_time=1.3)
            v.wait_until("wave")
            self.play(FadeIn(cond, shift=UP * 0.1), run_time=0.8)
            self.play(GrowArrow(arrow_c), Write(weq), run_time=1.3)
            self.play(FadeIn(wave_lbl), run_time=0.5)
            v.wait_until("sol")
            self.play(Write(sol), run_time=1.8)
        self.clear(run_time=0.6)

        # diffusion vs travelling wave, side by side
        lanes_x0, lanes_x1 = -4.3, 6.3
        y_rc, y_lc = 1.0, -1.6
        tw = ValueTracker(0.0)
        xs = np.linspace(0, 1, 400)
        lane_rc = Line([lanes_x0, y_rc, 0], [lanes_x1, y_rc, 0], stroke_color=DIM, stroke_width=2)
        lane_lc = Line([lanes_x0, y_lc, 0], [lanes_x1, y_lc, 0], stroke_color=DIM, stroke_width=2)

        def rc_curve():
            t = tw.get_value()
            s2 = 0.03 ** 2 + 0.07 * t           # variance grows linearly: diffusion
            v = np.exp(-(xs - 0.03) ** 2 / (2 * s2)) * 0.03 / np.sqrt(s2)
            pts = np.stack([lanes_x0 + (lanes_x1 - lanes_x0) * xs, y_rc + 1.4 * v, 0 * xs], 1)
            return VMobject().set_points_as_corners(pts).set_stroke(COPPER, 4)

        def lc_curve():
            t = tw.get_value()
            v = np.exp(-(xs - 0.03 - 0.9 * t) ** 2 / (2 * 0.03 ** 2))
            pts = np.stack([lanes_x0 + (lanes_x1 - lanes_x0) * xs, y_lc + 1.4 * v, 0 * xs], 1)
            return VMobject().set_points_as_corners(pts).set_stroke(APL, 4)

        rcm, lcm = always_redraw(rc_curve), always_redraw(lc_curve)
        lab_rc = VGroup(T("R C line", size=24, color=COPPER, weight=BOLD), T("diffusion · Kelvin", size=16, color=MUTED)).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        lab_rc.next_to(lane_rc, LEFT, buff=0.25).shift(UP * 0.45)
        lab_lc = VGroup(T("L C line", size=24, color=APL, weight=BOLD), T("waves · Heaviside", size=16, color=MUTED)).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        lab_lc.next_to(lane_lc, LEFT, buff=0.25).shift(UP * 0.45)
        with self.voice(
            "{side}Side by side: in a resistance-capacitance line, a pulse spreads out and sinks away. "
            "{lc}In an inductance-capacitance line, the same pulse simply travels, keeping its shape."
        ) as v:
            self.play(Create(lane_rc), Create(lane_lc), FadeIn(lab_rc), FadeIn(lab_lc), run_time=0.8)
            self.add(rcm, lcm)
            self.play(tw.animate.set_value(1.0), run_time=v.until_end(4.0), rate_func=linear)
        self.remove(rcm, lcm)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ which world does each signal live in?
        axr = Axes(x_range=[1, 7, 1], y_range=[0, 6.6, 1], x_length=10.4, y_length=4.6,
                   axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0.35, -0.35, 0])
        fxl = tick_labels(axr, [1, 2, 3, 4, 5, 6, 7], "x", texts=["10 Hz", "100 Hz", "1 kHz", "10 kHz", "100 kHz", "1 MHz", "10 MHz"], size=16)
        fyl = tick_labels(axr, [1, 3, 5], "y", texts=["0.1 mΩ/m", "10 mΩ/m", "1 Ω/m"], size=15)
        r_dc, l_p = 0.042, 0.5e-6

        def r_of(lf):
            f = 10 ** lf
            return np.log10(r_dc * np.sqrt(1 + f / 6.5e4)) + 5

        def wl_of(lf):
            return np.log10(2 * np.pi * 10 ** lf * l_p) + 5

        cr = axr.plot(r_of, x_range=[1, 7, 0.02], color=HAZARD, stroke_width=4)
        cw = axr.plot(wl_of, x_range=[1, 7, 0.02], color=BLUE, stroke_width=4)
        lr = TeX(r"R'", size=34, color=HAZARD).next_to(axr.c2p(1.3, r_of(1.3)), UP, buff=0.12)
        lw = TeX(r"\omega L'", size=34, color=BLUE).next_to(axr.c2p(6.55, wl_of(6.55)), RIGHT, buff=0.12).shift(DOWN * 0.35)
        f_x = np.log10(r_dc / (2 * np.pi * l_p))
        xdot = Dot(axr.c2p(f_x, r_of(f_x)), radius=0.08, color=TEXT)
        xlbl = T("≈ 13 kHz", size=20, color=TEXT, weight=BOLD).next_to(xdot, DOWN, buff=0.2).shift(RIGHT * 0.35)
        left_zone = Rectangle(width=axr.c2p(f_x, 0)[0] - axr.c2p(1, 0)[0], height=4.6, fill_color=COPPER, fill_opacity=0.07, stroke_width=0)
        left_zone.move_to(axr).align_to(axr, LEFT)
        right_zone = Rectangle(width=axr.c2p(7, 0)[0] - axr.c2p(f_x, 0)[0], height=4.6, fill_color=APL, fill_opacity=0.07, stroke_width=0)
        right_zone.move_to(axr).align_to(axr, RIGHT)
        zl = T("diffusion · Kelvin's world", size=20, color=COPPER, weight=BOLD).move_to([axr.c2p(2.6, 0)[0], axr.get_top()[1] + 0.3, 0])
        zr = T("waves · Heaviside's world", size=20, color=APL, weight=BOLD).move_to([axr.c2p(5.65, 0)[0], axr.get_top()[1] + 0.3, 0])

        def band(f0, f1, col, txt, y):
            a, b = axr.c2p(np.log10(f0), y), axr.c2p(np.log10(f1), y)
            if b[0] - a[0] < 0.12:
                b = a + RIGHT * 0.12
            r = RoundedRectangle(width=b[0] - a[0], height=0.26, corner_radius=0.08, fill_color=col, fill_opacity=0.85, stroke_width=0)
            r.move_to((a + b) / 2)
            t = T(txt, size=16, color=col, weight=BOLD).next_to(r, UP, buff=0.06)
            return VGroup(r, t)

        hart = band(1200, 2200, CAN, "HART", 0.65)
        h1 = band(25e3, 40e3, VIOLET, "fieldbus H1", 0.65)
        aplb = band(1e5, 3.75e6, APL, "Ethernet-APL", 0.65)
        with self.voice(
            "{cross}For APL's fieldbus cable, resistance and inductive reactance are equal at around thirteen kilohertz. "
            "{below}Below that lies Kelvin's world of diffusion. That's where HART's tones live — which is why HART's cable "
            "rules are written as a maximum R C time constant. {above}Above it lies Heaviside's world of waves. "
            "{apl}APL's signals sit between about a hundred kilohertz and a few megahertz: firmly in the world of waves. "
            "{next}So let's look at those waves."
        ) as v:
            self.play(Create(axr), FadeIn(fxl), FadeIn(fyl), run_time=0.8)
            self.play(Create(cr), FadeIn(lr), run_time=1.0)
            self.play(Create(cw), FadeIn(lw), run_time=1.0)
            self.play(FadeIn(xdot, scale=0.5), FadeIn(xlbl), run_time=0.5)
            v.wait_until("below")
            self.play(FadeIn(left_zone), FadeIn(zl), FadeIn(hart, shift=UP * 0.1), run_time=0.9)
            v.wait_until("above")
            self.play(FadeIn(right_zone), FadeIn(zr), FadeIn(h1, shift=UP * 0.1), run_time=0.9)
            v.wait_until("apl")
            self.play(FadeIn(aplb, shift=UP * 0.1), run_time=0.8)
            self.play(Indicate(aplb, color=APL, scale_factor=1.08), run_time=0.8)
        self.wait(0.3)
        self.clear(run_time=0.7)
