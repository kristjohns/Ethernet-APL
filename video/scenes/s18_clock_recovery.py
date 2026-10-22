import sys
from math import erfc, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl import dsp
from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *

OSR = 32


class ClockRecovery(APLScene):
    def construct(self):
        self.tag = corner_tag("08 · Inside the receiver", color=BLUE)
        self.add(self.tag)

        # ------------------------------------------------------------ the slicer
        rng = np.random.default_rng(12)
        n = 110
        syms = rng.integers(-1, 2, n)
        sigma = 0.14
        vals = syms + sigma * rng.standard_normal(n)
        ax = Axes(x_range=[0, n, 10], y_range=[-1.7, 1.7, 0.5], x_length=6.0, y_length=5.0,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-3.1, -0.35, 0])
        thr = VGroup(*[DashedLine(ax.c2p(0, y), ax.c2p(n, y), dash_length=0.07, stroke_color=TEXT, stroke_width=2) for y in (0.5, -0.5)])
        thr_l = VGroup(T("thresholds", size=15, color=TEXT).next_to(ax.c2p(2, 0.5), UP, buff=0.06).align_to(ax, LEFT).shift(RIGHT * 0.1))
        lev_l = VGroup(*[T(s, size=20, color=c, weight=BOLD).next_to(ax.c2p(0, y), LEFT, buff=0.15)
                         for s, y, c in (("+1", 1, APL), ("0", 0, VIOLET), ("−1", -1, PINK))])
        cols = {1: APL, 0: VIOLET, -1: PINK}
        dots = VGroup()
        for i, (s_, v_) in enumerate(zip(syms, vals)):
            dec = 1 if v_ > 0.5 else (-1 if v_ < -0.5 else 0)
            dots.add(Dot(ax.c2p(i + 0.5, v_), radius=0.045, color=cols[dec]))
        xl = T("successive samples →", size=16, color=MUTED).next_to(ax, DOWN, buff=0.12)
        with self.voice(
            "{slicer}After the equalizer, the decision itself is beautifully simple: a slicer with two thresholds, halfway "
            "between the levels. {rules}Above the upper threshold: plus one. Below the lower one: minus one. In between: zero."
        ) as v:
            self.play(Create(ax), FadeIn(xl), FadeIn(lev_l), run_time=0.7)
            self.play(Create(thr), FadeIn(thr_l), run_time=0.8)
            v.wait_until("rules")
            self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.03), run_time=3.2)

        # Gaussians on the right, rotated: density grows to the right
        gx0 = 0.6
        gscale = 1.4
        ys = np.linspace(-1.7, 1.7, 400)

        def gauss(mu):
            return np.exp(-(ys - mu) ** 2 / (2 * sigma ** 2))

        curves = VGroup()
        tails = VGroup()
        for mu, c in ((1, APL), (0, VIOLET), (-1, PINK)):
            dens = gauss(mu)
            pts = [np.array([gx0 + gscale * d, ax.c2p(0, y)[1], 0]) for d, y in zip(dens, ys)]
            curves.add(VMobject().set_points_as_corners(pts).set_stroke(c, 3))
            for lo, hi in ((0.5, 1.7), (-1.7, -0.5), (-0.5, 0.5)):
                inside = (mu >= lo) and (mu <= hi)
                if inside:
                    continue
                m = (ys >= lo) & (ys <= hi)
                if not np.any(m):
                    continue
                yy, dd = ys[m], dens[m]
                if dd.max() < 1e-3:
                    continue
                poly = [np.array([gx0, ax.c2p(0, yy[0])[1], 0])] + [np.array([gx0 + gscale * d, ax.c2p(0, y)[1], 0]) for d, y in zip(dd, yy)] + \
                       [np.array([gx0, ax.c2p(0, yy[-1])[1], 0])]
                tails.add(Polygon(*poly, fill_color=DANGER, fill_opacity=0.9, stroke_width=0))
        g_axis = Line([gx0, ax.c2p(0, -1.7)[1], 0], [gx0, ax.c2p(0, 1.7)[1], 0], stroke_color=DIM, stroke_width=2)
        g_thr = VGroup(*[DashedLine([gx0, ax.c2p(0, y)[1], 0], [gx0 + gscale + 0.2, ax.c2p(0, y)[1], 0], dash_length=0.07, stroke_color=TEXT, stroke_width=2) for y in (0.5, -0.5)])
        tails_lbl = T("errors: the tails beyond a threshold", size=16, color=DANGER, weight=BOLD).next_to(g_axis, DOWN, buff=0.12).shift(RIGHT * 0.8)
        ser = TeX(r"P_{\text{error}} \approx \tfrac{4}{3}\, Q\!\left(\frac{d}{2\sigma}\right)", size=36).move_to([4.75, 1.9, 0])
        qdef = TeX(r"Q(x) = \frac{1}{\sqrt{2\pi}}\int_x^{\infty} e^{-u^2/2}\,du", size=30, color=MUTED).next_to(ser, DOWN, buff=0.3)
        six = TeX(r"10^{-9} \;\Rightarrow\; \frac{d}{2\sigma} \approx 6", size=34, color=GOOD).next_to(qdef, DOWN, buff=0.4)
        snr = VGroup(T("levels 12 σ apart", size=20, color=GOOD, weight=BOLD), T("≈ 20 dB SNR at the slicer", size=20, color=GOOD, weight=BOLD)).arrange(DOWN, buff=0.08)
        snr.next_to(six, DOWN, buff=0.3)
        nofec = VGroup(T("no forward error correction:", size=16, color=MUTED), T("the margin is the error correction", size=16, color=TEXT, weight=BOLD)).arrange(DOWN, buff=0.05)
        nofec.next_to(snr, DOWN, buff=0.35)
        with self.voice(
            "{noise}But noise smears each level into a bell curve. {tail}An error happens whenever a sample strays past a "
            "threshold: the area in the tail of the bell curve, given by the Gaussian Q-function. {ber}For an error rate of "
            "one in a billion, each threshold must sit about six standard deviations away from its level — so neighbouring "
            "levels must be twelve sigma apart. That's a signal-to-noise ratio of about 20 dB at the slicer. {margin}That "
            "number is what the whole design is built around. Every dB the cable takes, every trace of residual echo, every "
            "pickup from a nearby motor eats into it. {nofec}And 10BASE-T1L has no forward error correction to fall back on: "
            "the margin is the error correction."
        ) as v:
            self.play(Create(g_axis), FadeIn(g_thr), run_time=0.5)
            self.play(LaggedStart(*[Create(c) for c in curves], lag_ratio=0.2), run_time=1.4)
            v.wait_until("tail")
            self.play(FadeIn(tails), FadeIn(tails_lbl), run_time=0.8)
            self.play(Write(ser), run_time=1.2)
            self.play(FadeIn(qdef), run_time=0.6)
            v.wait_until("ber")
            self.play(Write(six), run_time=1.2)
            self.play(FadeIn(snr, shift=UP * 0.1), run_time=0.8)
            v.wait_until("nofec")
            self.play(FadeIn(nofec, shift=UP * 0.1), run_time=0.7)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ when to sample: a phase-locked loop
        a, raw, (y1, d1), (y2, d2), ph = dsp.equalised_eyes(OSR)
        start = OSR * 400
        tr = dsp.eye(y2, OSR, start + ph - OSR, 120)
        ec = np.array([-3.9, 1.1, 0])
        ebox = panel(5.0, 2.9).move_to(ec)
        eye = eye_mob(tr, ec, width=4.6, height=2.5, color=GOOD, opacity=0.18, stroke=1.2, clip=1.45, scale=0.9)
        err = dsp.timing_loop(n=400, kp=0.08, ki=0.004, offset=0.42, drift=0.0015)
        k_t = ValueTracker(0.0)

        def marker():
            i = int(min(len(err) - 1, k_t.get_value()))
            off = err[i]
            x = ec[0] + off * 2.3 * 0.5 / 0.5 * 0.5
            x = ec[0] + off * 2.3
            col = GOOD if abs(off) < 0.05 else POWER
            return VGroup(Line([x, ec[1] - 1.3, 0], [x, ec[1] + 1.3, 0], stroke_color=col, stroke_width=3.5),
                          Triangle(fill_color=col, fill_opacity=1, stroke_width=0).scale(0.1).rotate(PI).move_to([x, ec[1] + 1.42, 0]))

        mk = always_redraw(marker)
        e_title = T("sampling instant", size=18, color=POWER, weight=BOLD).next_to(ebox, UP, buff=0.12)
        # block diagram of the loop
        bx = VGroup()
        specs = [("timing\ndetector", [0.75, 1.75, 0]), ("PI controller", [3.25, 1.75, 0]), ("NCO", [5.6, 1.75, 0])]
        for nm, pos in specs:
            b = RoundedRectangle(width=1.9, height=0.85, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=GOOD, stroke_width=2).move_to(pos)
            bx.add(VGroup(b, T(nm, size=17, color=TEXT, weight=BOLD).move_to(b)))
        pi_tf = TeX(r"K_p + \frac{K_i}{s}", size=28, color=GOOD).next_to(bx[1], DOWN, buff=0.12)
        nco_tf = TeX(r"\frac{1}{s}", size=28, color=GOOD).next_to(bx[2], DOWN, buff=0.12)
        b_arr = VGroup(Arrow(bx[0].get_right(), bx[1].get_left(), buff=0.03, stroke_width=2.5, color=MUTED, tip_length=0.12),
                       Arrow(bx[1].get_right(), bx[2].get_left(), buff=0.03, stroke_width=2.5, color=MUTED, tip_length=0.12))
        back = VMobject().set_points_as_corners([bx[2].get_top(), bx[2].get_top() + UP * 0.45, bx[0].get_top() + UP * 0.45, bx[0].get_top() + UP * 0.05])
        back.set_stroke(GOOD, 2.5)
        back_l = T("sampling clock", size=15, color=GOOD).next_to(back, UP, buff=0.05)
        cl_tf = TeX(r"H(s) = \frac{K_p s + K_i}{s^2 + K_p s + K_i}", size=34).move_to([3.25, 0.05, 0])
        # phase-error response
        px = Axes(x_range=[0, 300, 50], y_range=[-0.15, 0.45, 0.1], x_length=6.0, y_length=2.2,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([3.3, -2.2, 0])
        p_t = T("phase error (symbol periods)", size=15, color=MUTED).next_to(px, UP, buff=0.08).align_to(px, LEFT)
        p_x = T("time →", size=14, color=MUTED).next_to(px, DOWN, buff=0.08).align_to(px, RIGHT)
        zero_l = DashedLine(px.c2p(0, 0), px.c2p(300, 0), dash_length=0.05, stroke_color=DIM, stroke_width=1.2)

        def perr():
            i = int(min(299, k_t.get_value()))
            pts = [px.c2p(j, err[j]) for j in range(0, i + 1)]
            if len(pts) < 2:
                pts = pts + pts
            return VMobject().set_points_as_corners(pts).set_stroke(POWER, 3)

        pe = always_redraw(perr)
        with self.voice(
            "{clock}One question remains: when exactly to sample? {noclk}There's no clock wire, and the two ends run on "
            "separate crystal oscillators, a few millionths apart. {pll}So the receiver recovers the clock from the signal "
            "itself, with a phase-locked loop. A timing detector compares samples with decisions, and estimates whether the "
            "receiver is sampling early or late. {pi}That error drives a proportional-integral controller, which steers a "
            "numerically controlled oscillator — the receiver's sense of time. {ctrl}You know this loop from control theory. "
            "The oscillator integrates frequency into phase; the integral term removes the steady frequency offset between "
            "the crystals; the proportional term keeps the loop stable and well damped. {lock}Within a few thousand symbols, "
            "the sampling instant settles in the middle of the eye, and stays there."
        ) as v:
            self.play(FadeIn(ebox), FadeIn(e_title), LaggedStart(*[Create(m) for m in eye], lag_ratio=0.01), run_time=1.6)
            self.add(mk)
            v.wait_until("pll")
            self.play(FadeIn(bx[0]), run_time=0.6)
            v.wait_until("pi")
            self.play(FadeIn(bx[1]), FadeIn(bx[2]), GrowArrow(b_arr[0]), GrowArrow(b_arr[1]), FadeIn(pi_tf), FadeIn(nco_tf), run_time=1.0)
            self.play(Create(back), FadeIn(back_l), run_time=0.8)
            v.wait_until("ctrl")
            self.play(Write(cl_tf), run_time=1.6)
            v.wait_until("lock")
            self.play(Create(px), FadeIn(p_t), FadeIn(p_x), FadeIn(zero_l), run_time=0.6)
            self.add(pe)
            self.play(k_t.animate.set_value(299), run_time=v.until_end(3.0) + 0.6, rate_func=linear)
        self.remove(mk, pe)

        can_cmp = VGroup(
            VGroup(T("CAN", size=22, color=CAN, weight=BOLD), T("nudges its bit timing on occasional edges, by whole time quanta", size=18, color=TEXT)).arrange(RIGHT, buff=0.3),
            VGroup(T("APL", size=22, color=APL, weight=BOLD), T("tracks the phase continuously, to a small fraction of a symbol", size=18, color=TEXT)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.6, 0])
        bg = BackgroundRectangle(can_cmp, color=BG, fill_opacity=0.95, buff=0.25)
        with self.voice(
            "{can}Compare that with CAN, which nudges its bit timing on occasional edges, by whole time quanta. APL's receiver "
            "tracks the phase continuously, to a small fraction of a symbol."
        ) as v:
            self.play(FadeOut(VGroup(px, p_t, p_x, zero_l)), FadeIn(bg), FadeIn(can_cmp[0], shift=UP * 0.1), run_time=0.8)
            self.play(FadeIn(can_cmp[1], shift=UP * 0.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ loop timing: the slave transmits on the master's clock
        m_dev = device("master", "cpu", APL, width=2.0, height=1.4, label_size=20).move_to([-4.6, 0.3, 0])
        s_dev = device("slave", "cpu", VIOLET, width=2.0, height=1.4, label_size=20).move_to([4.6, 0.3, 0])
        xtal = VGroup(Rectangle(width=0.5, height=0.3, stroke_color=POWER, stroke_width=2.5), T("crystal", size=15, color=POWER)).arrange(DOWN, buff=0.06)
        xtal.next_to(m_dev, DOWN, buff=0.3)
        pll_box = VGroup(RoundedRectangle(width=1.1, height=0.5, corner_radius=0.1, stroke_color=GOOD, stroke_width=2.5), T("PLL", size=16, color=GOOD, weight=BOLD))
        pll_box[1].move_to(pll_box[0])
        pll_box.next_to(s_dev, DOWN, buff=0.3)
        go = Arrow([-3.5, 0.75, 0], [3.5, 0.75, 0], buff=0, stroke_width=3, color=APL, tip_length=0.16)
        back2 = Arrow([3.5, -0.15, 0], [-3.5, -0.15, 0], buff=0, stroke_width=3, color=VIOLET, tip_length=0.16)
        go_l = T("data + timing of the master", size=17, color=APL).next_to(go, UP, buff=0.08)
        back_l2 = T("data, sent on the recovered clock", size=17, color=VIOLET).next_to(back2, DOWN, buff=0.08)
        lt_lbl = T("loop timing: both directions tick in lockstep", size=22, color=GOOD, weight=BOLD).move_to([0, -2.4, 0])
        with self.voice(
            "{loop}And there's one more twist. The slave doesn't transmit on its own crystal: it sends using the clock it "
            "recovered from the master. {lockstep}Both directions then tick in lockstep — which is exactly what the echo "
            "canceller needs, because its own echo and the far end's symbols now share the same time grid."
        ) as v:
            self.play(FadeIn(m_dev), FadeIn(s_dev), FadeIn(xtal), run_time=0.8)
            self.play(GrowArrow(go), FadeIn(go_l), run_time=1.0)
            self.play(FadeIn(pll_box), run_time=0.5)
            self.play(GrowArrow(back2), FadeIn(back_l2), run_time=1.0)
            v.wait_until("lockstep")
            self.play(FadeIn(lt_lbl, shift=UP * 0.1), run_time=0.7)
        self.wait(0.4)
        self.clear(run_time=0.7)
