import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *

rng = np.random.default_rng(42)
SEQ_A = rng.integers(-1, 2, 400)
SEQ_B = rng.integers(-1, 2, 400)


def pam(levels, tau):
    """Smooth PAM-3 waveform (raised-cosine edges) evaluated at symbol time tau (array)."""
    tau = np.asarray(tau, dtype=float)
    k = np.floor(tau).astype(int)
    frac = tau - k
    n = len(levels)
    a = levels[k % n]
    b = levels[(k + 1) % n]
    w = np.where(frac < 0.62, 0.0, 0.5 - 0.5 * np.cos(np.pi * (frac - 0.62) / 0.38))
    return a + (b - a) * w


class FullDuplex(APLScene):
    def construct(self):
        self.tag = corner_tag("04 · Inside Ethernet-APL")
        self.add(self.tag)

        # ------------------------------------------------------------ the link
        xa, xb = -4.6, 4.6
        y_wire, y_ab, y_ba = 1.55, 2.65, 0.45
        phy_a = device("PHY A", "cpu", APL, width=1.6, height=1.3, label_size=20).move_to([xa - 1.25, y_wire, 0])
        phy_b = device("PHY B", "cpu", VIOLET, width=1.6, height=1.3, label_size=20).move_to([xb + 1.25, y_wire, 0])
        pair = VGroup(Line([xa, y_wire + 0.05, 0], [xb, y_wire + 0.05, 0]), Line([xa, y_wire - 0.05, 0], [xb, y_wire - 0.05, 0]))
        pair.set_stroke(DIM, 3)
        lbl_ab = T("A → B", size=18, color=APL, weight=BOLD).move_to([xa + 0.2, y_ab + 0.5, 0])
        lbl_ba = T("B → A", size=18, color=VIOLET, weight=BOLD).move_to([xb - 0.2, y_ba - 0.5, 0])
        lbl_w = T("on the wire: the sum", size=18, color=TEXT, weight=BOLD).move_to([0, y_wire + 0.62, 0])

        clock = ValueTracker(0.0)
        clock.add_updater(lambda m, dt: m.increment_value(dt))
        rate = 2.6         # symbols per second (slowed down a few million times)
        flight = 10.0      # symbols in flight along the cable
        far = 0.28         # far-end amplitude after the cable (drawn larger than the real ~0.06)
        us = np.linspace(0, 1, 420)
        xs = xa + (xb - xa) * us
        amp = 0.32
        show_sum = ValueTracker(0.0)

        def lane(seq, y, col, direction):
            def f():
                t = clock.get_value() * rate
                if direction > 0:
                    v = pam(seq, t - us * flight)
                else:
                    v = pam(seq, t - (1 - us) * flight)
                return VMobject().set_points_as_corners(np.stack([xs, y + amp * v, np.zeros_like(xs)], 1)).set_stroke(col, 3)
            return always_redraw(f)

        def wire():
            t = clock.get_value() * rate
            va = pam(SEQ_A, t - us * flight) * far ** us
            vb = pam(SEQ_B, t - (1 - us) * flight) * far ** (1 - us)
            k = show_sum.get_value()
            pts = np.stack([xs, y_wire + 0.42 * amp * 2.0 * (va + vb) * k, np.zeros_like(xs)], 1)
            return VMobject().set_points_as_corners(pts).set_stroke(WHITE_SOFT, 3.2, opacity=0.25 + 0.75 * k)

        lane_ab = lane(SEQ_A, y_ab, APL, +1)
        lane_ba = lane(SEQ_B, y_ba, VIOLET, -1)
        wire_m = always_redraw(wire)
        self.add(clock)

        with self.voice(
            "{wait}Wait — both directions at the same time, on one pair? {can}In CAN, two transmitters driving the bus "
            "at once is exactly the conflict that arbitration resolves. {apl}In APL, it's the normal state."
        ) as v:
            self.play(FadeIn(phy_a, shift=RIGHT * 0.2), FadeIn(phy_b, shift=LEFT * 0.2), Create(pair), run_time=1.0)
            self.play(FadeIn(lane_ab), FadeIn(lbl_ab), run_time=0.8)
            self.play(FadeIn(lane_ba), FadeIn(lbl_ba), run_time=0.8)
            v.wait_until("apl")
            fd = pill("full duplex: both ends transmit all the time", APL, size=20).move_to([0, -0.35, 0])
            self.play(FadeIn(fd, shift=UP * 0.1), run_time=0.6)

        with self.voice(
            "{add}Both ends transmit continuously, and on the wire the two signals simply add up. "
            "{buried}So each receiver sees the far-end signal — weakened by up to about 25 dB after a kilometer of "
            "cable — buried under its own, much stronger transmission."
        ) as v:
            self.add(wire_m)
            self.play(show_sum.animate.set_value(1.0), FadeIn(lbl_w), pair.animate.set_stroke(opacity=0.35), run_time=1.5)
            v.wait_until("buried")
            near = VGroup(T("near A:", size=17, color=MUTED), T("own signal, big", size=17, color=APL),
                          T("+", size=17, color=MUTED), T("far end, −25 dB", size=17, color=VIOLET)).arrange(RIGHT, buff=0.12)
            near.move_to([-2.2, -0.35, 0])
            self.play(FadeOut(fd), FadeIn(near, shift=UP * 0.1), run_time=0.8)
            foot = T("(far-end amplitude drawn ×5 for visibility; real ratio ≈ 1 : 18)", size=14, color=DIM).next_to(near, DOWN, buff=0.12)
            self.play(FadeIn(foot), run_time=0.5)

        # ------------------------------------------------------------ the echo canceller, live
        n_sym = 26
        px0, px1 = -4.3, 5.9
        taus = np.linspace(0, n_sym, 520)
        pxs = px0 + (px1 - px0) * taus / n_sym
        refl = 0.22
        echo = pam(SEQ_A, taus + 3) + refl * pam(SEQ_A, taus + 3 - 2.4)
        farv = far * pam(SEQ_B, taus + 11)
        recv = echo + farv
        w1, w2 = ValueTracker(0.0), ValueTracker(0.0)
        rows_y = [-0.85, -2.0, -3.15]
        ramp = 0.3

        def row_curve(vals, y, col, width=3):
            return VMobject().set_points_as_corners(np.stack([pxs, y + ramp * vals, np.zeros_like(pxs)], 1)).set_stroke(col, width)

        def est():
            e = w1.get_value() * pam(SEQ_A, taus + 3) + w2.get_value() * refl * pam(SEQ_A, taus + 3 - 2.4)
            return row_curve(e, rows_y[1], APL)

        def resid():
            e = w1.get_value() * pam(SEQ_A, taus + 3) + w2.get_value() * refl * pam(SEQ_A, taus + 3 - 2.4)
            return row_curve(recv - e, rows_y[2], VIOLET, 3.2)

        r_recv = row_curve(recv, rows_y[0], WHITE_SOFT)
        r_est = always_redraw(est)
        r_res = always_redraw(resid)
        names = VGroup(
            T("received at A", size=18, color=TEXT, weight=BOLD),
            T("echo estimate", size=18, color=APL, weight=BOLD),
            T("difference", size=18, color=VIOLET, weight=BOLD),
        )
        for nm, y in zip(names, rows_y):
            nm.next_to([px0 - 0.25, y, 0], LEFT, buff=0)
        ops = VGroup(T("−", size=48, color=TEXT, weight=BOLD).move_to([px0 - 1.0, (rows_y[0] + rows_y[1]) / 2, 0]),
                     T("=", size=48, color=TEXT, weight=BOLD).move_to([px0 - 1.0, (rows_y[1] + rows_y[2]) / 2, 0]))
        ops.set_x(-6.75)
        err = always_redraw(lambda: T(
            f"residual echo: {20 * np.log10(max(1e-3, abs(1 - w1.get_value()) + refl * abs(1 - w2.get_value()) + 1e-3)):.0f} dB",
            size=18, color=GOOD if w1.get_value() > 0.97 else MUTED).move_to([4.6, rows_y[1] + 0.62, 0]))

        with self.voice(
            "{knows}The trick is that every transceiver knows exactly what it just sent. {filter}An adaptive digital "
            "filter — the echo canceller — learns how its own signal appears at its input, including reflections, "
            "and subtracts that copy. {remains}What remains is the far end. {nc}It's the same principle as "
            "noise-cancelling headphones."
        ) as v:
            self.play(FadeOut(VGroup(near, foot)), run_time=0.4)
            self.play(FadeIn(names[0]), Create(r_recv), run_time=1.2)
            v.wait_until("filter")
            self.add(r_est, r_res)
            self.play(FadeIn(names[1]), FadeIn(names[2]), FadeIn(ops), FadeIn(err), run_time=0.6)
            lms = T("adapting…", size=18, color=APL).next_to(names[1], DOWN, buff=0.08)
            self.play(FadeIn(lms), run_time=0.3)
            self.play(w1.animate.set_value(0.75), run_time=1.6, rate_func=smooth)
            self.play(w1.animate.set_value(1.0), w2.animate.set_value(0.7), run_time=1.6, rate_func=smooth)
            self.play(w2.animate.set_value(1.0), run_time=1.2, rate_func=smooth)
            self.play(FadeOut(lms), run_time=0.3)
            v.wait_until("remains")
            box = SurroundingRectangle(r_res, color=VIOLET, buff=0.12, corner_radius=0.1)
            far_lbl = T("= B's data, recovered", size=18, color=VIOLET, weight=BOLD).next_to(box, UP, buff=0.05).align_to(box, RIGHT)
            self.play(Create(box), FadeIn(far_lbl), run_time=0.8)
            v.wait_until("nc")
            hp = VGroup(icon("headphones", TEXT, 0.55), T("same idea", size=18, color=MUTED)).arrange(RIGHT, buff=0.15)
            hp.move_to([-5.4, -0.25, 0])
            self.play(FadeIn(hp, shift=UP * 0.1), run_time=0.6)

        for m in (lane_ab, lane_ba, wire_m):
            m.clear_updaters()
        clock.clear_updaters()
        self.clear(run_time=0.7)

        # ------------------------------------------------------------ nonlinear vs linear medium
        left = panel(6.4, 4.6).move_to([-3.45, -0.1, 0])
        right = panel(6.4, 4.6).move_to([3.45, -0.1, 0])
        lt = VGroup(T("CAN", size=30, color=CAN, weight=BOLD), T("nonlinear medium", size=22, color=TEXT)).arrange(DOWN, buff=0.08)
        lt.next_to(left.get_top(), DOWN, buff=0.25)
        rt = VGroup(T("Ethernet-APL", size=30, color=APL, weight=BOLD), T("linear medium + DSP", size=22, color=TEXT)).arrange(DOWN, buff=0.08)
        rt.next_to(right.get_top(), DOWN, buff=0.25)
        # CAN: turn taking timeline
        tl = VGroup()
        slots = [("A", 1.2), ("B", 0.9), ("C", 0.7), ("A", 1.0), ("B", 1.1)]
        x = -6.2
        for nm, w in slots:
            col = {"A": CAN, "B": "#D97706", "C": "#92400E"}[nm]
            r = Rectangle(width=w, height=0.55, fill_color=col, fill_opacity=0.85, stroke_color=BG, stroke_width=2).move_to([x + w / 2, -0.5, 0])
            tl.add(VGroup(r, T(nm, size=20, color=BG, weight=BOLD).move_to(r)))
            x += w
        tl_lbl = T("one talker at a time, dominant wins", size=19, color=MUTED).next_to(tl, DOWN, buff=0.3)
        rule_l = T("0 · 1 = 0", size=40, color=CAN, weight=BOLD).next_to(tl, UP, buff=0.55)
        # APL: two simultaneous lanes
        lanes = VGroup()
        for i, (nm, col) in enumerate([("A → B", APL), ("B → A", VIOLET)]):
            r = Rectangle(width=4.9, height=0.42, fill_color=col, fill_opacity=0.75, stroke_width=0).move_to([3.7, -0.25 - 0.55 * i, 0])
            lanes.add(VGroup(r, T(nm, size=17, color=BG, weight=BOLD).move_to(r)))
        ln_lbl = T("both talk at once, all the time", size=19, color=MUTED).next_to(lanes, DOWN, buff=0.3)
        rule_r = TeX(r"v_A + v_B", size=54, color=APL).move_to([rule_l.get_x() + 6.9, rule_l.get_y(), 0])
        with self.voice(
            "{deep}So here is the deepest difference between the two physical layers. {canside}CAN uses a nonlinear "
            "medium, where dominant beats recessive, so that nodes can take turns. {aplside}APL uses a linear medium "
            "plus signal processing, so that both ends can talk at once."
        ) as v:
            self.play(FadeIn(left), FadeIn(right), run_time=0.6)
            v.wait_until("canside")
            self.play(FadeIn(lt, shift=DOWN * 0.1), FadeIn(rule_l), run_time=0.7)
            self.play(LaggedStart(*[GrowFromEdge(s, LEFT) for s in tl], lag_ratio=0.5), FadeIn(tl_lbl), run_time=2.0)
            v.wait_until("aplside")
            self.play(FadeIn(rt, shift=DOWN * 0.1), FadeIn(rule_r), run_time=0.7)
            self.play(*[GrowFromEdge(l, LEFT) for l in lanes], FadeIn(ln_lbl), run_time=1.5)
        self.wait(0.6)
        self.clear(run_time=0.7)
