import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl import dsp
from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *

SYM = {1: "+", 0: "0", -1: "−"}


class EchoCanceller(APLScene):
    def construct(self):
        self.tag = corner_tag("07 · Two directions, one pair", color=VIOLET)
        self.add(self.tag)
        g, iters, W, res_db = dsp.lms_history()
        n_taps = len(g)

        # ------------------------------------------------------------ the echo path
        ax = Axes(x_range=[0, n_taps, 10], y_range=[-0.25, 0.4, 0.1], x_length=11.0, y_length=3.2,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0.2, -0.2, 0])
        us = [0, 22.5, 45, 67.5, 75]
        xt = tick_labels(ax, [0, 15, 30, 45, 60, 75], "x", texts=["0", "2 µs", "4 µs", "6 µs", "8 µs", "10 µs"], size=15)
        st = VGroup()
        for k, v in enumerate(g):
            if abs(v) < 1e-4:
                continue
            col = VIOLET if k < 8 else PINK
            st.add(VGroup(Line(ax.c2p(k, 0), ax.c2p(k, v), stroke_color=col, stroke_width=3), Dot(ax.c2p(k, v), radius=0.045, color=col)))
        notes = VGroup(
            T("leakage through the hybrid", size=16, color=VIOLET).next_to(ax.c2p(4, 0.33), RIGHT, buff=0.3),
            T("connector, 300 m", size=15, color=PINK).next_to(ax.c2p(22.5, 0.06), UP, buff=0.12),
            T("splice, 700 m", size=15, color=PINK).next_to(ax.c2p(53, -0.04), DOWN, buff=0.12),
            T("far end, 1 km", size=15, color=PINK).next_to(ax.c2p(75.5, 0.03), UP, buff=0.12),
        )
        rt = BraceBetweenPoints(ax.c2p(0, -0.27), ax.c2p(75, -0.27), DOWN, color=MUTED)
        rt_l = T("round trip through 1 km: 10 µs = 75 symbols", size=17, color=MUTED).next_to(rt, DOWN, buff=0.08)
        title = T("echo impulse response", size=20, color=TEXT, weight=BOLD).next_to(ax, UP, buff=0.3).align_to(ax, LEFT)
        with self.voice(
            "{dig}The rest of the job is done digitally, by the echo canceller. {know}Its secret weapon: the transceiver "
            "knows exactly which symbols it has sent. {path}The echo it receives is those symbols, convolved with the echo "
            "path's impulse response: first the leakage through the hybrid, then the small reflections from connectors and "
            "splices, arriving later — up to a full round trip, ten microseconds for a kilometer of cable."
        ) as v:
            v.wait_until("path")
            self.play(Create(ax), FadeIn(xt), FadeIn(title), run_time=0.8)
            self.play(LaggedStart(*[GrowFromPoint(s, s[0].get_start()) for s in st[:8]], lag_ratio=0.1), FadeIn(notes[0]), run_time=1.2)
            self.play(LaggedStart(*[GrowFromPoint(s, s[0].get_start()) for s in st[8:]], lag_ratio=0.2), FadeIn(notes[1:]), run_time=1.6)
            self.play(GrowFromCenter(rt), FadeIn(rt_l), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the transversal filter
        n_show = 8
        bw, gap = 1.0, 0.45
        y_dl = 1.6
        x_first = -5.2
        rng = np.random.default_rng(4)
        tx_syms = rng.integers(-1, 2, 60)
        shift = ValueTracker(0)
        boxes = VGroup()
        for i in range(n_show):
            x = x_first + i * (bw + gap)
            boxes.add(RoundedRectangle(width=bw, height=0.7, corner_radius=0.1, fill_color=PANEL, fill_opacity=1, stroke_color=APL, stroke_width=2).move_to([x, y_dl, 0]))
        dl_arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.02, stroke_width=2.2, color=MUTED, tip_length=0.1) for a, b in zip(boxes[:-1], boxes[1:])])
        dots_mid = T("…", size=30, color=MUTED).move_to([x_first + (n_show - 0.5) * (bw + gap) - 0.1, y_dl, 0])
        in_arrow = Arrow(boxes[0].get_left() + LEFT * 0.9, boxes[0].get_left(), buff=0.02, stroke_width=2.5, color=APL, tip_length=0.12)
        in_lbl = VGroup(T("symbols", size=15, color=APL), T("we sent", size=15, color=APL)).arrange(DOWN, buff=0.02).next_to(in_arrow, UP, buff=0.08)

        def syms():
            k = int(shift.get_value())
            g_ = VGroup()
            for i in range(n_show):
                val = int(tx_syms[(k - i) % len(tx_syms)])
                g_.add(M(SYM[val], size=28, color=APL if val else MUTED, weight=BOLD).move_to(boxes[i]))
            return g_

        sm = always_redraw(syms)
        wts = VGroup()
        for i in range(n_show):
            wv = g[i]
            c = TeX(r"h_{%d}" % i, size=26, color=VIOLET).next_to(boxes[i], DOWN, buff=0.55)
            wts.add(c)
        drops = VGroup(*[Arrow(b.get_bottom(), w.get_top(), buff=0.05, stroke_width=2, color=MUTED, tip_length=0.1) for b, w in zip(boxes, wts)])
        sigma = Circle(0.32, stroke_color=TEXT, stroke_width=2.5).move_to([0.0, -1.2, 0])
        sig_t = TeX(r"\Sigma", size=34, color=TEXT).move_to(sigma)
        to_sum = VGroup(*[Line(w.get_bottom() + DOWN * 0.05, sigma.get_center() + (w.get_bottom() - sigma.get_center()) * 0.0
                               + normalize(w.get_bottom() - sigma.get_center()) * 0.34, stroke_color=DIM, stroke_width=1.6) for w in wts])
        est = Arrow(sigma.get_right(), [4.0, -1.2, 0], buff=0.02, stroke_width=2.5, color=VIOLET, tip_length=0.12)
        est_l = TeX(r"\hat{e}_n", size=30, color=VIOLET).next_to(est, UP, buff=0.05)
        sub = Circle(0.28, stroke_color=TEXT, stroke_width=2.5).move_to([4.35, -1.2, 0])
        sub_t = T("−", size=28, color=TEXT, weight=BOLD).move_to(sub)
        r_in = Arrow([4.35, -2.3, 0], sub.get_bottom(), buff=0.02, stroke_width=2.5, color=TEXT, tip_length=0.12)
        r_lbl = VGroup(TeX(r"r_n", size=30, color=TEXT), T("received", size=15, color=MUTED)).arrange(RIGHT, buff=0.12).next_to(r_in, DOWN, buff=0.05)
        e_out = Arrow(sub.get_right(), [6.3, -1.2, 0], buff=0.02, stroke_width=2.5, color=GOOD, tip_length=0.12)
        e_lbl = VGroup(TeX(r"e_n", size=30, color=GOOD), T("to the equalizer", size=15, color=MUTED)).arrange(DOWN, buff=0.04).next_to(e_out, UP, buff=0.05).shift(RIGHT * 0.2)
        eqs = VGroup(TeX(r"\hat{e}_n = \sum_k h_k\, a_{n-k}", size=36, color=VIOLET), TeX(r"e_n = r_n - \hat{e}_n", size=36, color=GOOD)).arrange(RIGHT, buff=1.2)
        eqs.move_to([-1.3, -2.85, 0])
        free = VGroup(
            VGroup(M("+", size=26, color=APL, weight=BOLD), T("→ add h", size=18, color=TEXT)).arrange(RIGHT, buff=0.12),
            VGroup(M("0", size=26, color=MUTED, weight=BOLD), T("→ skip", size=18, color=TEXT)).arrange(RIGHT, buff=0.12),
            VGroup(M("−", size=26, color=APL, weight=BOLD), T("→ subtract h", size=18, color=TEXT)).arrange(RIGHT, buff=0.12),
        ).arrange(RIGHT, buff=0.6).move_to([-1.3, -2.85, 0])
        free_t = T("no multipliers needed", size=18, color=GOOD, weight=BOLD).next_to(free, UP, buff=0.15)
        shift.add_updater(lambda m, dt: m.increment_value(dt * 1.6))
        with self.voice(
            "{fir}So the canceller is a finite-impulse-response filter: a delay line that holds the most recently sent "
            "symbols — enough of them to span the whole round trip. {weights}Each one is multiplied by a weight, and "
            "everything is summed. {est}That sum is an estimate of the echo, and it's subtracted from the received signal. "
            "{free}And because the symbols are only plus one, zero or minus one, those multiplications come for free: add "
            "the weight, skip it, or subtract it."
        ) as v:
            self.add(shift)
            self.play(LaggedStart(*[FadeIn(b) for b in boxes], lag_ratio=0.08), LaggedStart(*[GrowArrow(a) for a in dl_arrows], lag_ratio=0.08),
                      GrowArrow(in_arrow), FadeIn(in_lbl), run_time=1.4)
            self.add(sm)
            v.wait_until("weights")
            self.play(LaggedStart(*[GrowArrow(d) for d in drops], lag_ratio=0.06), LaggedStart(*[FadeIn(w) for w in wts], lag_ratio=0.06), run_time=1.2)
            self.play(Create(to_sum), FadeIn(sigma), FadeIn(sig_t), run_time=0.9)
            v.wait_until("est")
            self.play(GrowArrow(est), FadeIn(est_l), FadeIn(sub), FadeIn(sub_t), GrowArrow(r_in), FadeIn(r_lbl), run_time=1.0)
            self.play(GrowArrow(e_out), FadeIn(e_lbl), Write(eqs), run_time=1.4)
            v.wait_until("free")
            self.play(FadeOut(eqs), FadeIn(free, shift=UP * 0.1), FadeIn(free_t), run_time=0.8)
        shift.clear_updaters()
        self.remove(sm, shift)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ LMS: the weights learn the echo path
        wid = name_card("Bernard Widrow & Ted Hoff", "1960 · Stanford", "the least-mean-squares algorithm", GOOD).to_corner(UR, buff=0.4).shift(DOWN * 0.1)
        rule = TeX(r"h_k", r"\;\leftarrow\;", r"h_k", r"+", r"\mu", r"\, e_n", r"\, a_{n-k}", size=48).move_to([-2.3, 2.55, 0])
        rule[4].set_color(POWER)
        rule[5].set_color(GOOD)
        rule[6].set_color(APL)
        bx = Axes(x_range=[0, n_taps, 10], y_range=[-0.2, 0.36, 0.1], x_length=7.6, y_length=3.0,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-2.6, -0.45, 0])
        true_pts = VGroup(*[Dot(bx.c2p(k, v), radius=0.035, color=PINK) for k, v in enumerate(g) if abs(v) > 1e-4])
        snap = ValueTracker(0.0)

        def bars():
            s = snap.get_value()
            i = int(np.floor(s))
            j = min(i + 1, len(W) - 1)
            f = s - i
            w = (1 - f) * W[i] + f * W[j]
            grp = VGroup()
            for k, v in enumerate(w):
                if abs(v) < 0.003:
                    continue
                grp.add(Line(bx.c2p(k, 0), bx.c2p(k, v), stroke_color=VIOLET, stroke_width=3.2))
            return grp

        br = always_redraw(bars)
        b_title = T("canceller weights", size=18, color=VIOLET, weight=BOLD).next_to(bx, UP, buff=0.15).align_to(bx, LEFT)
        t_lbl = VGroup(Dot(radius=0.05, color=PINK), T("true echo path", size=16, color=PINK)).arrange(RIGHT, buff=0.1).next_to(b_title, RIGHT, buff=0.5)
        cx = Axes(x_range=[0, 4.8, 1], y_range=[-55, 0, 10], x_length=4.6, y_length=3.0,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([4.3, -0.45, 0])
        cxt = tick_labels(cx, [0, 2, 4], "x", texts=["1", "100", "10 000"], size=14)
        cyt = tick_labels(cx, [0, -20, -40], "y", texts=["0 dB", "−20", "−40"], size=14)
        c_title = T("residual echo vs. symbols", size=18, color=GOOD, weight=BOLD).next_to(cx, UP, buff=0.15)
        lx = np.log10(np.maximum(iters, 1))

        def curve():
            s = snap.get_value()
            i = int(np.floor(s))
            pts = [cx.c2p(min(lx[k], 4.8), max(res_db[k], -55)) for k in range(0, i + 1)]
            if len(pts) < 2:
                pts = pts + pts
            return VMobject().set_points_as_corners(pts).set_stroke(GOOD, 3)

        cv = always_redraw(curve)

        def meter():
            s = snap.get_value()
            i = int(np.floor(s))
            return T(f"{res_db[i]:.0f} dB", size=30, color=GOOD, weight=BOLD).next_to(cx.c2p(4.8, 0), DOWN, buff=0.1).shift(LEFT * 0.6)

        mt = always_redraw(meter)
        target = DashedLine(cx.c2p(0, -50), cx.c2p(4.8, -50), dash_length=0.06, stroke_color=GOOD, stroke_width=1.5)
        target_l = T("target ≈ −50 dB", size=14, color=GOOD).next_to(cx.c2p(0.1, -50), UP, buff=0.06).align_to(cx, LEFT)
        mit = T("cousin of the MIT rule in adaptive control", size=17, color=MUTED).move_to([-2.6, -2.55, 0])
        with self.voice(
            "{lms}How does it find the weights? It watches the error — whatever is left after the subtraction — and after "
            "every symbol, it nudges every weight a little: {rule}weight k changes by mu, times the error, times the symbol "
            "that sat at tap k. {grad}That's the least-mean-squares algorithm, published by Bernard Widrow and Ted Hoff at "
            "Stanford in 1960. It is gradient descent on the squared error, one tiny step per symbol. {mit}If you know the "
            "MIT rule from adaptive control, you've met its close cousin. {watch}Watch the weights take on the shape of the "
            "echo path, while the residual echo melts away. {track}And because it never stops adapting, the canceller "
            "follows the cable as it warms up in the sun and cools down at night."
        ) as v:
            v.wait_until("rule")
            self.play(Write(rule), run_time=1.6)
            v.wait_until("grad")
            self.play(FadeIn(wid, shift=LEFT * 0.2), run_time=0.7)
            v.wait_until("mit")
            self.play(FadeIn(mit), run_time=0.6)
            v.wait_until("watch")
            self.play(Create(bx), FadeIn(b_title), FadeIn(true_pts), FadeIn(t_lbl), Create(cx), FadeIn(cxt), FadeIn(cyt), FadeIn(c_title),
                      FadeIn(target), FadeIn(target_l), run_time=1.0)
            self.add(br, cv, mt)
            self.play(snap.animate.set_value(len(W) - 1), run_time=v.until("track", 6.0) + 0.5, rate_func=linear)
            v.wait_until("track")
            sun = icon("sun", POWER, 0.45).next_to(bx, DOWN, buff=0.15).shift(LEFT * 1.2)
            moon = icon("moon", BLUE, 0.4).next_to(bx, DOWN, buff=0.15).shift(RIGHT * 1.2)
            self.play(FadeOut(mit), FadeIn(sun), FadeIn(moon), run_time=0.6)
            self.play(Indicate(br, color=VIOLET, scale_factor=1.03), run_time=1.2)
        self.remove(br, cv, mt)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ why the scramblers must differ
        exp = TeX(r"\mathrm{E}\big[e_n\, a_{n-k}\big]", r"=", r"(g_k - h_k)\,\mathrm{E}[a^2]", r"+", r"\mathrm{E}\big[\,\text{far end}\cdot a_{n-k}\big]", size=40)
        exp[2].set_color(VIOLET)
        exp[4].set_color(PINK)
        exp.move_to([0, 1.2, 0])
        zero = TeX(r"= 0", size=40, color=GOOD).next_to(exp[4], DOWN, buff=0.35)
        cross_l = Line(exp[4].get_corner(DL), exp[4].get_corner(UR), stroke_color=GOOD, stroke_width=4)
        expl = VGroup(T("independent scramblers in each direction", size=22, color=GOOD, weight=BOLD),
                      T("→ the canceller can only learn its own echo", size=20, color=TEXT)).arrange(DOWN, buff=0.12).move_to([0, -1.4, 0])
        with self.voice(
            "{why}Now the scrambler detail pays off. The canceller learns by correlating the error with its own symbols. "
            "{corr}If the far end's symbols were correlated with ours, that second term wouldn't vanish, and the canceller "
            "would start cancelling part of the far-end signal too. {indep}With different scramblers in each direction, the "
            "two streams are statistically independent. The only thing the canceller can learn is its own echo."
        ) as v:
            self.play(Write(exp), run_time=2.2)
            v.wait_until("indep")
            self.play(Create(cross_l), FadeIn(zero, shift=UP * 0.1), run_time=0.8)
            self.play(FadeIn(expl, shift=UP * 0.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ a family tree
        tl = timeline([(1960, "LMS algorithm", GOOD), (1967, "echo cancellers\nfor satellite calls", VIOLET, "1960s"), (1986, "ISDN lines:\n4B3T, echo-cancelled", VIOLET, "1980s"),
                       (1999, "1000BASE-T:\n4 echo-cancelled pairs", APL), (2015, "100BASE-T1:\none pair, cars", APL), (2019, "10BASE-T1L:\none pair, 1 km", APL)],
                      x0=-5.5, x1=5.5, y=-0.1, size=18, even=True)
        with self.voice(
            "{history}Adaptive echo cancellers were developed at Bell Labs in the 1960s for satellite telephone calls, where "
            "the trip up to a geostationary satellite and back makes echoes return more than half a second late. {isdn}Two "
            "decades later, they put full-duplex digital data onto ordinary telephone pairs, in ISDN. {gig}In 1999, gigabit "
            "Ethernet ran four echo-cancelled pairs at once; {t1}in 2015, a single pair for cars. {apl}APL's transceivers are "
            "their direct descendants."
        ) as v:
            self.play(Create(tl[0]), run_time=0.8)
            self.play(FadeIn(tl[1][0], shift=UP * 0.1), FadeIn(tl[1][1], shift=UP * 0.1), run_time=1.0)
            v.wait_until("isdn")
            self.play(FadeIn(tl[1][2], shift=UP * 0.1), run_time=0.8)
            v.wait_until("gig")
            self.play(FadeIn(tl[1][3], shift=UP * 0.1), run_time=0.8)
            v.wait_until("t1")
            self.play(FadeIn(tl[1][4], shift=UP * 0.1), run_time=0.8)
            v.wait_until("apl")
            self.play(FadeIn(tl[1][5], shift=UP * 0.1), run_time=0.8)
            self.play(Indicate(tl[1][5], color=APL, scale_factor=1.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the deepest difference
        left = panel(6.4, 4.6).move_to([-3.45, -0.1, 0])
        right = panel(6.4, 4.6).move_to([3.45, -0.1, 0])
        lt = VGroup(T("CAN", size=30, color=CAN, weight=BOLD), T("nonlinear medium", size=22, color=TEXT)).arrange(DOWN, buff=0.08)
        lt.next_to(left.get_top(), DOWN, buff=0.25)
        rtt = VGroup(T("Ethernet-APL", size=30, color=APL, weight=BOLD), T("linear medium + signal processing", size=22, color=TEXT)).arrange(DOWN, buff=0.08)
        rtt.next_to(right.get_top(), DOWN, buff=0.25)
        tlg = VGroup()
        x = -6.2
        for nm, w in [("A", 1.2), ("B", 0.9), ("C", 0.7), ("A", 1.0), ("B", 1.1)]:
            col = {"A": CAN, "B": "#D97706", "C": "#92400E"}[nm]
            r = Rectangle(width=w, height=0.55, fill_color=col, fill_opacity=0.85, stroke_color=BG, stroke_width=2).move_to([x + w / 2, -0.5, 0])
            tlg.add(VGroup(r, T(nm, size=20, color=BG, weight=BOLD).move_to(r)))
            x += w
        tl_lbl = T("one talker at a time; dominant wins", size=19, color=MUTED).next_to(tlg, DOWN, buff=0.3)
        rule_l = T("0 · 1 = 0", size=40, color=CAN, weight=BOLD).next_to(tlg, UP, buff=0.55)
        lanes = VGroup()
        for i, (nm, col) in enumerate([("A → B", APL), ("B → A", VIOLET)]):
            r = Rectangle(width=4.9, height=0.42, fill_color=col, fill_opacity=0.75, stroke_width=0).move_to([3.7, -0.25 - 0.55 * i, 0])
            lanes.add(VGroup(r, T(nm, size=17, color=BG, weight=BOLD).move_to(r)))
        ln_lbl = T("both talk at once, all the time", size=19, color=MUTED).next_to(lanes, DOWN, buff=0.3)
        rule_r = TeX(r"v_A + v_B", size=54, color=APL).move_to([rule_l.get_x() + 6.9, rule_l.get_y(), 0])
        with self.voice(
            "{deep}And so we arrive at the deepest difference between the two physical layers. {canside}CAN uses a nonlinear "
            "medium, where dominant beats recessive, so that nodes can take turns. {aplside}APL uses a linear medium plus "
            "signal processing, so that both ends can talk at once."
        ) as v:
            self.play(FadeIn(left), FadeIn(right), run_time=0.6)
            v.wait_until("canside")
            self.play(FadeIn(lt, shift=DOWN * 0.1), FadeIn(rule_l), run_time=0.7)
            self.play(LaggedStart(*[GrowFromEdge(s, LEFT) for s in tlg], lag_ratio=0.5), FadeIn(tl_lbl), run_time=2.0)
            v.wait_until("aplside")
            self.play(FadeIn(rtt, shift=DOWN * 0.1), FadeIn(rule_r), run_time=0.7)
            self.play(*[GrowFromEdge(l, LEFT) for l in lanes], FadeIn(ln_lbl), run_time=1.5)
        self.wait(0.6)
        self.clear(run_time=0.7)
