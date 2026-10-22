import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scipy.special import jv

from apl import dsp
from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *

RHO, MU0, R_WIRE = 1.72e-8, 4e-7 * np.pi, 0.51e-3


def skin_depth(f):
    return np.sqrt(2 * RHO / (2 * np.pi * f * MU0))


def current_density(r_frac, f):
    """|J(r)| / |J(surface)| in a round copper wire (exact Bessel solution)."""
    if f <= 0:
        return np.ones_like(r_frac)
    k = (1 - 1j) / skin_depth(f)
    return np.abs(jv(0, k * R_WIRE * r_frac)) / np.abs(jv(0, k * R_WIRE))


def r_ratio(f):
    if f <= 0:
        return 1.0
    k = (1 - 1j) / skin_depth(f)
    return float(((k * R_WIRE / 2) * jv(0, k * R_WIRE) / jv(1, k * R_WIRE)).real)


class Losses(APLScene):
    def construct(self):
        self.tag = corner_tag("05 · The wire is a waveguide")
        self.add(self.tag)

        # ------------------------------------------------------------ R and G, and exponential decay
        sl = rlgc_slice(width=4.6, height=1.45, lsize=22).move_to([0, 1.7, 0])
        heat = glow(sl.r[0].copy().set_stroke(HAZARD, 3), HAZARD, layers=7, max_width=22, max_opacity=0.45)
        heat_g = glow(sl.g[0].copy().set_stroke(HAZARD, 3), HAZARD, layers=7, max_width=22, max_opacity=0.45)
        lr = T("copper heats up", size=17, color=HAZARD).next_to(sl, LEFT, buff=0.4).shift(UP * 0.55)
        lg = T("insulation absorbs a little", size=17, color=HAZARD).next_to(sl, RIGHT, buff=0.4)
        x0, x1, yw = -5.8, 5.8, -1.35
        alpha = 0.32
        phase = ValueTracker(0.0)

        def decaying():
            xs = np.linspace(x0, x1, 500)
            env = np.exp(-alpha * (xs - x0))
            v = env * np.sin(2.2 * (xs - x0) - phase.get_value())
            return VMobject().set_points_as_corners(np.stack([xs, yw + 0.95 * v, 0 * xs], 1)).set_stroke(APL, 3.2)

        wave = always_redraw(decaying)
        envs = VGroup(*[always_redraw(lambda s=s: ParametricFunction(
            lambda u: np.array([u, yw + s * 0.95 * np.exp(-alpha * (u - x0)), 0]), t_range=[x0, x1], color=MUTED,
            stroke_width=1.6).set_stroke(opacity=0.8)) for s in (1, -1)])
        decay_eq = TeX(r"V(x) = V_0\, e^{-\alpha x}", r",\qquad", r"\alpha \approx \frac{R'}{2Z_0} + \frac{G' Z_0}{2}", size=40).move_to([0, -3.05, 0])
        decay_eq[2].set_color(HAZARD)
        with self.voice(
            "{loss}So far, our waves have travelled without loss. Real cables lose energy in two ways. {r}Current flowing "
            "through the copper heats it: that's the series resistance, R. {g}And the insulation absorbs a little energy "
            "from the alternating electric field between the wires: that's the shunt conductance, G. {alpha}On a low-loss "
            "line, every meter takes away the same fraction of the wave, so the amplitude decays exponentially — "
            "{eq}e to the minus alpha x, with alpha about R over two Z-naught, plus G times Z-naught over two."
        ) as v:
            self.play(FadeIn(sl), run_time=0.8)
            v.wait_until("r")
            self.play(FadeIn(heat), FadeIn(lr), run_time=0.8)
            v.wait_until("g")
            self.play(FadeIn(heat_g), FadeIn(lg), run_time=0.8)
            v.wait_until("alpha")
            self.add(wave)
            self.play(FadeIn(wave), FadeIn(envs), phase.animate.set_value(6), run_time=2.5, rate_func=linear)
            v.wait_until("eq")
            self.play(Write(decay_eq), phase.animate.set_value(14), run_time=3.0, rate_func=linear)
            self.play(phase.animate.set_value(18), run_time=v.until_end(0.5), rate_func=linear)
        self.remove(wave, *envs)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the soil analogy
        gx0, gx1, g_top, g_bot = -6.3, -0.9, 1.9, -2.7
        ground_rect = Rectangle(width=gx1 - gx0, height=g_top - g_bot, stroke_width=0).move_to([(gx0 + gx1) / 2, (g_top + g_bot) / 2, 0])
        ground_rect.set_fill(color=["#3B2A1E", "#1A130E"], opacity=1)
        ground_rect.set_sheen_direction(DOWN)
        grass = Line([gx0, g_top, 0], [gx1, g_top, 0], stroke_color=GOOD, stroke_width=5)
        sun = icon("sun", POWER, 0.55).move_to([gx0 + 0.55, g_top + 0.6, 0])
        moon = icon("moon", BLUE, 0.45).move_to([gx1 - 0.55, g_top + 0.6, 0])
        day = ValueTracker(0.0)
        depth_scale = (g_top - g_bot) / 1.0       # 1 m of soil across the panel
        dd = 0.117                                  # daily damping depth [m]
        xmid, amp = (gx0 + gx1) / 2, 2.0

        def soil_curve():
            zs = np.linspace(0, 1.0, 200)
            th = 2 * np.pi * day.get_value()
            T = np.exp(-zs / dd) * np.cos(th - zs / dd)
            pts = np.stack([xmid + amp * T, g_top - zs * depth_scale, 0 * zs], 1)
            return VMobject().set_points_as_corners(pts).set_stroke(HAZARD, 3.5)

        soil = always_redraw(soil_curve)
        zs = np.linspace(0, 1.0, 200)
        env_l = VMobject().set_points_as_corners(np.stack([xmid - amp * np.exp(-zs / dd), g_top - zs * depth_scale, 0 * zs], 1))
        env_r = VMobject().set_points_as_corners(np.stack([xmid + amp * np.exp(-zs / dd), g_top - zs * depth_scale, 0 * zs], 1))
        envg = VGroup(env_l, env_r).set_stroke(MUTED, 1.5, opacity=0.8)
        axis_z = DashedLine([xmid, g_top, 0], [xmid, g_bot, 0], dash_length=0.06, stroke_color=DIM, stroke_width=1.5)
        zl = VGroup(*[T(t, size=14, color=MUTED).move_to([gx1 - 0.45, g_top - z * depth_scale, 0]) for t, z in (("0", 0), ("30 cm", 0.3), ("1 m", 1.0))])
        soil_lbl = T("daily temperature swing in soil", size=18, color=HAZARD, weight=BOLD).next_to(ground_rect, DOWN, buff=0.15)

        # the wire cross-section
        wc = np.array([3.3, 0.2, 0])
        rad = 1.5
        n_ring = 70
        freq = ValueTracker(0.0)
        cold, hot = ManimColor("#101A30"), ManimColor(APL)

        def rings():
            f = freq.get_value()
            g = VGroup()
            edges = np.linspace(0, 1, n_ring + 1)
            mids = 0.5 * (edges[:-1] + edges[1:])
            dens = current_density(mids, f)
            dens = dens / dens.max()
            for i in range(n_ring - 1, -1, -1):
                col = interpolate_color(cold, hot, float(dens[i]) ** 0.75)
                g.add(Circle(radius=rad * edges[i + 1], fill_color=col, fill_opacity=1, stroke_width=0).move_to(wc))
            g.add(Circle(radius=rad, stroke_color=COPPER_EDGE, stroke_width=2.5).move_to(wc))
            if f > 2e4:
                dfrac = min(1.0, skin_depth(f) / R_WIRE)
                g.add(DashedVMobject(Circle(radius=rad * (1 - dfrac), stroke_color=WHITE_SOFT, stroke_width=2).move_to(wc), num_dashes=40))
            return g

        COPPER_EDGE = "#C98A55"
        wire = always_redraw(rings)

        def readout():
            f = freq.get_value()
            if f <= 0:
                fs = "DC"
            elif f < 1e6:
                fs = f"{f / 1e3:.0f} kHz"
            else:
                fs = f"{f / 1e6:.2f} MHz"
            d = skin_depth(f) * 1e6 if f > 0 else np.inf
            ds = "—" if not np.isfinite(d) else (f"{d:.0f} µm" if d < 1000 else f"{d / 1000:.1f} mm")
            g = VGroup(
                VGroup(T("f =", size=20, color=MUTED), T(fs, size=20, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.12),
                VGroup(T("δ =", size=20, color=MUTED), T(ds, size=20, color=WHITE_SOFT, weight=BOLD)).arrange(RIGHT, buff=0.12),
                VGroup(T("R / R_DC =", size=20, color=MUTED), T(f"{r_ratio(f):.1f}", size=20, color=HAZARD, weight=BOLD)).arrange(RIGHT, buff=0.12),
            ).arrange(RIGHT, buff=0.45)
            g.move_to([wc[0], wc[1] - rad - 0.95, 0])
            return g

        ro = always_redraw(readout)
        wlab = T("18 AWG copper, 1.02 mm", size=18, color="#C98A55", weight=BOLD).next_to(wc + DOWN * rad, DOWN, buff=0.15)
        delta_eq = TeX(r"\delta = \sqrt{\frac{2\rho}{\omega\mu}}", size=44, color=WHITE_SOFT).move_to([3.3, 2.75, 0])
        with self.voice(
            "{skin}But R is not the DC resistance. At high frequencies, the current crowds towards the surface of the "
            "conductor: the skin effect. {soil}You know the same phenomenon from the ground beneath your feet. The daily "
            "temperature swing at the surface fades within a few tens of centimeters of soil; only the slow seasonal swing "
            "reaches meters deep. Fast changes only penetrate a thin layer. {math}For the current in a wire, it's the same "
            "diffusion equation, and the penetration depth is delta equals the square root of two rho over omega mu. "
            "{num}For copper at 3.75 megahertz, delta is just thirty-four micrometers. {wire}An 18-gauge conductor is a "
            "millimeter thick, so most of the copper sits idle: the resistance is almost eight times its DC value, and it "
            "keeps growing with the square root of frequency."
        ) as v:
            self.add(wire, ro)
            self.play(FadeIn(wire), FadeIn(ro), FadeIn(wlab), run_time=0.8)
            self.play(freq.animate.set_value(3.75e6), run_time=v.until("soil", 2.5), rate_func=lambda a: a ** 3)
            self.play(FadeIn(ground_rect), Create(grass), FadeIn(sun), FadeIn(moon), FadeIn(axis_z), FadeIn(zl), run_time=0.8)
            self.add(soil)
            self.play(FadeIn(envg), FadeIn(soil_lbl), day.animate.set_value(1.5), run_time=4.0, rate_func=linear)
            v.wait_until("math")
            self.play(Write(delta_eq), day.animate.set_value(2.5), run_time=2.0, rate_func=linear)
            self.play(day.animate.set_value(3.2), run_time=1.4, rate_func=linear)
            v.wait_until("num")
            freq.set_value(0)
            self.play(freq.animate.set_value(1e5), run_time=1.3, rate_func=smooth)
            self.play(freq.animate.set_value(1e6), run_time=1.3, rate_func=smooth)
            self.play(freq.animate.set_value(3.75e6), day.animate.set_value(4.5), run_time=1.3, rate_func=smooth)
            v.wait_until("wire")
            self.play(Indicate(ro, color=HAZARD, scale_factor=1.05), day.animate.set_value(6.0), run_time=v.until_end(1.0), rate_func=linear)
        self.remove(wire, ro, soil)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the loss curve
        ax = Axes(x_range=[0, 10, 1], y_range=[0, 50, 10], x_length=8.2, y_length=4.6,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-1.5, -0.1, 0])
        xt = tick_labels(ax, [0, 2.5, 3.75, 5, 7.5, 10], "x", texts=["0", "2.5", "3.75", "5", "7.5", "10 MHz"], size=16)
        yt = tick_labels(ax, [0, 10, 20, 30, 40, 50], "y", texts=["0", "10", "20", "30", "40", "50 dB"], size=16)
        c_sk = ax.plot(lambda f: dsp.K_SKIN * np.sqrt(f), x_range=[0, 10, 0.02], color=HAZARD, stroke_width=2.5)
        c_sk = DashedVMobject(c_sk, num_dashes=60)
        c_di = DashedVMobject(ax.plot(lambda f: dsp.K_DIEL * f, x_range=[0, 10, 0.02], color=PINK, stroke_width=2.5), num_dashes=60)
        c_all = ax.plot(lambda f: float(dsp.il_db(f)), x_range=[0, 10, 0.02], color=TEXT, stroke_width=4)
        l_sk = T("skin effect  ∝ √f", size=17, color=HAZARD).next_to(ax.c2p(7.2, dsp.K_SKIN * np.sqrt(7.2)), DOWN, buff=0.25)
        l_di = T("dielectric  ∝ f", size=17, color=PINK).next_to(ax.c2p(8.5, dsp.K_DIEL * 8.5), UP, buff=0.12)
        l_all = T("1 km of cable", size=19, color=TEXT, weight=BOLD).next_to(ax.c2p(8.3, float(dsp.il_db(8.3))), UP, buff=0.12).shift(LEFT * 0.4)
        eq_il = TeX(r"\mathrm{IL}(f) \approx k_1\sqrt{f} + k_2\, f", size=40).move_to([4.6, 2.3, 0])
        mark = Dot(ax.c2p(3.75, 25.6), radius=0.09, color=APL)
        vline = DashedLine(ax.c2p(3.75, 0), ax.c2p(3.75, 25.6), dash_length=0.06, stroke_color=APL, stroke_width=2)
        hline = DashedLine(ax.c2p(0, 25.6), ax.c2p(3.75, 25.6), dash_length=0.06, stroke_color=APL, stroke_width=2)
        ml = T("25.6 dB", size=22, color=APL, weight=BOLD).next_to(mark, LEFT, buff=0.2).shift(UP * 0.28)
        fac = VGroup(T("amplitude ÷ 19", size=26, color=APL, weight=BOLD), T("at the Nyquist frequency, 3.75 MHz", size=17, color=MUTED)
                     ).arrange(DOWN, buff=0.06).move_to([4.6, 0.6, 0])
        lp = VGroup(icon("filter", TEXT, 0.5), T("a low-pass filter, 1 km long", size=20, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.2).move_to([4.6, -1.0, 0])
        with self.voice(
            "{curve}Add the dielectric losses, which grow in proportion to frequency, and you get the classic cable-loss "
            "curve: a square-root term plus a linear term. {budget}The standard allows up to about 25.6 dB of loss at 3.75 "
            "megahertz, over a one-kilometer link. In amplitude, that's a factor of nineteen. {lp}And the loss keeps "
            "climbing with frequency. Low frequencies get through; high frequencies are stripped away. The cable is a "
            "low-pass filter, one kilometer long."
        ) as v:
            self.play(Create(ax), FadeIn(xt), FadeIn(yt), run_time=0.8)
            self.play(Create(c_sk), FadeIn(l_sk), run_time=1.0)
            self.play(Create(c_di), FadeIn(l_di), run_time=0.8)
            self.play(Create(c_all), FadeIn(l_all), Write(eq_il), run_time=1.4)
            v.wait_until("budget")
            self.play(Create(vline), Create(hline), FadeIn(mark, scale=0.5), FadeIn(ml), run_time=1.0)
            self.play(FadeIn(fac, shift=UP * 0.1), run_time=0.8)
            v.wait_until("lp")
            self.play(FadeIn(lp, shift=UP * 0.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ one symbol in, a smear out
        osr = 32
        p = dsp.symbol_response(osr)
        kpk = int(np.argmax(p))
        sc_in = scope(4.6, 2.3, "into the cable: one symbol (133 ns)", APL).move_to([-3.55, 1.45, 0])
        sc_out = scope(4.6, 2.3, "after 1 km (×5, delay removed)", VIOLET).move_to([3.55, 1.45, 0])
        t_axis = np.arange(-2 * osr, 26 * osr) / osr
        x_in = np.where((t_axis >= 0) & (t_axis < 1), 1.0, 0.0)
        p_full = np.concatenate([np.zeros(2 * osr), p[: 26 * osr]])
        tr_in = trace_in(sc_in.box, t_axis, x_in, APL, 3, y_range=(-0.15, 1.15))
        tr_out = trace_in(sc_out.box, t_axis, 5 * p_full, VIOLET, 3, y_range=(-0.15, 1.15))
        tail_b = BraceBetweenPoints(sc_out.box.get_bottom() + LEFT * 1.4 + UP * 0.05, sc_out.box.get_bottom() + RIGHT * 2.2 + UP * 0.05, DOWN, color=MUTED)
        tail_l = T("a tail lasting dozens of symbols", size=16, color=MUTED).next_to(tail_b, DOWN, buff=0.06)

        # superposition of a few symbols
        syms = [1, -1, 0, 1, 1, -1]
        sup_ax0, sup_ax1, sup_y = -5.6, 5.6, -2.05
        span_sym = 14
        ts = np.arange(0, span_sym * osr) / osr
        resp_lines = VGroup()
        total = np.zeros_like(ts)
        cols = [APL, VIOLET, PINK, GOOD, POWER, BLUE]
        for k, a in enumerate(syms):
            sh = np.zeros_like(ts)
            seg = p[: len(ts) - k * osr]
            sh[k * osr:] = a * seg
            total += sh
            xs = sup_ax0 + (sup_ax1 - sup_ax0) * ts / span_sym
            resp_lines.add(VMobject().set_points_as_corners(np.stack([xs, sup_y + 4.5 * sh, 0 * xs], 1)).set_stroke(cols[k], 2, opacity=0.75))
        xs = sup_ax0 + (sup_ax1 - sup_ax0) * ts / span_sym
        sum_line = VMobject().set_points_as_corners(np.stack([xs, sup_y + 4.5 * total, 0 * xs], 1)).set_stroke(WHITE_SOFT, 4)
        base = Line([sup_ax0, sup_y, 0], [sup_ax1, sup_y, 0], stroke_color=DIM, stroke_width=1.5)
        sym_lbls = VGroup(*[T({1: "+1", 0: "0", -1: "−1"}[a], size=16, color=cols[k], weight=BOLD)
                            .move_to([sup_ax0 + (sup_ax1 - sup_ax0) * (k + kpk / osr) / span_sym, sup_y + 1.15, 0]) for k, a in enumerate(syms)])
        conv = TeX(r"r(t) = \sum_k a_k\, p(t - kT)", size=40).move_to([0, -3.35, 0])
        with self.voice(
            "{one}Now send a single, crisp symbol into a kilometer of this cable. {out}What comes out is lower, rounder "
            "and later — and it drags a long tail behind it that lasts for dozens of symbol periods. {stream}Send a stream "
            "of symbols, and every symbol's tail spills into the decisions about its neighbors. That's intersymbol "
            "interference. {conv}Mathematically, the received signal is a convolution: each symbol's response, shifted by "
            "one symbol period and scaled by the symbol's value, all added up."
        ) as v:
            self.play(FadeIn(sc_in), FadeIn(sc_out), run_time=0.6)
            self.play(Create(tr_in), run_time=0.8)
            v.wait_until("out")
            self.play(Create(tr_out), run_time=2.0)
            self.play(GrowFromCenter(tail_b), FadeIn(tail_l), run_time=0.7)
            v.wait_until("stream")
            self.play(Create(base), run_time=0.4)
            self.play(LaggedStart(*[AnimationGroup(Create(l), FadeIn(s)) for l, s in zip(resp_lines, sym_lbls)], lag_ratio=0.35), run_time=3.0)
            v.wait_until("conv")
            self.play(Create(sum_line), run_time=1.6)
            self.play(Write(conv), run_time=1.4)
        self.clear(run_time=0.6)

        # the eye closes
        a = dsp.rng_symbols(3000, seed=4)
        r = dsp.received(a, p, osr)
        r = r / (np.max(np.abs(r[osr * 80:])) + 1e-9)
        ideal = np.repeat(a, osr)
        start = osr * 120
        tr_ideal = dsp.eye(ideal * 0.95, osr, start + osr // 2, 60)
        tr_raw = dsp.eye(r, osr, start + kpk % osr + osr // 2 - osr, 160)
        e1_box = panel(5.2, 3.4).move_to([-3.3, -0.25, 0])
        e2_box = panel(5.2, 3.4).move_to([3.3, -0.25, 0])
        e1 = eye_mob(tr_ideal, e1_box.get_center(), width=4.6, height=2.6, color=APL, opacity=0.5, stroke=2, clip=1.1, scale=1.25)
        e2 = eye_mob(tr_raw, e2_box.get_center(), width=4.6, height=2.6, color=HAZARD, opacity=0.2, stroke=1.4, clip=1.3, scale=1.25)
        t1 = T("sent: three clean levels", size=20, color=APL, weight=BOLD).next_to(e1_box, UP, buff=0.15)
        t2 = T("received after 1 km: the eye is closed", size=20, color=HAZARD, weight=BOLD).next_to(e2_box, UP, buff=0.15)
        lv = VGroup(*[T(s, size=18, color=APL, weight=BOLD).next_to(e1_box.get_left() + UP * 1.25 * y, RIGHT, buff=0.1)
                      for s, y in (("+1", 0.95), ("0", 0), ("−1", -0.95))])
        with self.voice(
            "{eye}Overlay every symbol period of the received waveform, and you get an eye diagram. {closed}Sent, it shows "
            "three clean levels. After a kilometer of cable, the eye is closed: from the raw voltage alone, plus, zero and "
            "minus can no longer be told apart. {later}Prying that eye open again is the receiver's job. We'll get there."
        ) as v:
            self.play(FadeIn(e1_box), FadeIn(t1), run_time=0.5)
            self.play(LaggedStart(*[Create(m) for m in e1], lag_ratio=0.02), FadeIn(lv), run_time=1.6)
            v.wait_until("closed")
            self.play(FadeIn(e2_box), FadeIn(t2), run_time=0.5)
            self.play(LaggedStart(*[Create(m) for m in e2], lag_ratio=0.01), run_time=3.0)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ twisting vs. interference
        bfield = VGroup()
        for x in np.arange(-6.6, 6.8, 0.55):
            for y in np.arange(-2.6, 2.4, 0.55):
                bfield.add(Dot([x, y, 0], radius=0.03, color=BLUE).set_opacity(0.55))
        b_lbl = VGroup(icon("engine", BLUE, 0.5), T("motor cable nearby: changing magnetic field", size=18, color=BLUE)).arrange(RIGHT, buff=0.2)
        b_lbl.move_to([0, 2.95, 0])
        fy0, fy1 = 1.45, 0.75
        fx0, fx1 = -5.2, 5.2
        flat = VGroup(Line([fx0, fy0, 0], [fx1, fy0, 0]), Line([fx0, fy1, 0], [fx1, fy1, 0]), Line([fx1, fy0, 0], [fx1, fy1, 0])).set_stroke(TEXT, 3)
        flat_fill = Rectangle(width=fx1 - fx0, height=fy0 - fy1, fill_color=DANGER, fill_opacity=0.2, stroke_width=0).move_to([0, (fy0 + fy1) / 2, 0])
        emf = CurvedArrow([fx0 + 0.6, fy1 + 0.12, 0], [fx0 + 0.6, fy0 - 0.12, 0], angle=-PI / 1.2, color=DANGER, stroke_width=4, tip_length=0.15)
        flat_lbl = T("side by side: one big loop → large induced voltage", size=18, color=DANGER, weight=BOLD).next_to(flat, LEFT, buff=0).next_to(flat, DOWN, buff=0.15)
        ty = -1.35
        xs = np.linspace(fx0, fx1, 600)
        n_half = 10
        wa = VMobject().set_points_as_corners(np.stack([xs, ty + 0.38 * np.sin(np.pi * n_half * (xs - fx0) / (fx1 - fx0)), 0 * xs], 1)).set_stroke(TEXT, 3)
        wb = VMobject().set_points_as_corners(np.stack([xs, ty - 0.38 * np.sin(np.pi * n_half * (xs - fx0) / (fx1 - fx0)), 0 * xs], 1)).set_stroke(MUTED, 3)
        loops = VGroup()
        signs = VGroup()
        seg = (fx1 - fx0) / n_half
        for i in range(n_half):
            cx = fx0 + seg * (i + 0.5)
            col = GOOD if i % 2 == 0 else DANGER
            us = np.linspace(fx0 + seg * i, fx0 + seg * (i + 1), 40)
            top = ty + 0.38 * np.abs(np.sin(np.pi * n_half * (us - fx0) / (fx1 - fx0)))
            bot = ty - 0.38 * np.abs(np.sin(np.pi * n_half * (us - fx0) / (fx1 - fx0)))
            poly = Polygon(*[[u, t, 0] for u, t in zip(us, top)], *[[u, b, 0] for u, b in zip(us[::-1], bot[::-1])],
                           fill_color=col, fill_opacity=0.28, stroke_width=0)
            loops.add(poly)
            signs.add(T("+" if i % 2 == 0 else "−", size=22, color=col, weight=BOLD).move_to([cx, ty, 0]))
        tw_lbl = T("twisted: small loops of alternating sign → contributions cancel", size=18, color=GOOD, weight=BOLD).next_to(wb, DOWN, buff=0.35)
        far = TeX(r"\mathcal{E} = -\frac{d\Phi}{dt}", r",\qquad", r"\Phi_{\text{twisted}} = \sum_k (\pm B A_k) \approx 0", size=36).move_to([0, -3.3, 0])
        far[2].set_color(GOOD)
        with self.voice(
            "{noise}One more enemy comes from outside: interference. A motor cable nearby produces a changing magnetic "
            "field. {flat}If our two wires ran side by side, they would form one long loop, and by Faraday's law that "
            "changing field would induce a voltage around it. {twist}Twist the wires, and the loop becomes a chain of small "
            "loops with alternating orientation. The voltages induced in neighbouring loops cancel. {cm}Whatever is left "
            "appears equally on both wires — common mode — and the differential receiver ignores it, just like CAN's. "
            "{shield}And the shield around the pair takes care of electric fields."
        ) as v:
            self.play(LaggedStart(*[FadeIn(d) for d in bfield], lag_ratio=0.002), FadeIn(b_lbl), run_time=1.2)
            self.play(bfield.animate.set_opacity(0.95), rate_func=there_and_back, run_time=1.0)
            v.wait_until("flat")
            self.play(Create(flat), FadeIn(flat_fill), run_time=1.0)
            self.play(Create(emf), FadeIn(flat_lbl), run_time=0.9)
            v.wait_until("twist")
            self.play(Create(wa), Create(wb), run_time=1.4)
            self.play(FadeIn(loops), LaggedStart(*[FadeIn(s, scale=0.5) for s in signs], lag_ratio=0.1), run_time=1.6)
            self.play(FadeIn(tw_lbl), Write(far), run_time=1.4)
            v.wait_until("cm")
            self.play(Indicate(signs, color=TEXT, scale_factor=1.2), run_time=1.0)
        self.wait(0.4)
        self.clear(run_time=0.7)
