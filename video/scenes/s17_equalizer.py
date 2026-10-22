import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl import dsp
from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *

OSR = 32
SYM = {1: "+", 0: "0", -1: "−"}


class Equalizer(APLScene):
    def construct(self):
        self.tag = corner_tag("07 · Two directions, one pair", color=VIOLET)
        self.add(self.tag)

        jm = JourneyMap()
        with self.voice("{map}With its own echo removed, the receiver is left with the far end's signal — weak, smeared, and with a closed eye. Time to open it.") as v:
            self.play(FadeIn(jm), run_time=0.8)
            self.play(*jm.focus("rx"), run_time=0.8)
        self.clear(run_time=0.5)
        self.chapter(8, "Inside the receiver", "Equalizer, decisions, and a recovered clock", color=BLUE)

        # ------------------------------------------------------------ the receive chain
        names = [("AGC amplifier", None), ("ADC", None), ("Echo\ncanceller", None), ("Feed-forward\nequalizer", "FFE"),
                 ("Slicer", None), ("Descrambler\n+ decoder", None)]
        blocks = VGroup()
        for nm, sub in names:
            box = RoundedRectangle(width=1.6, height=0.95, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=BLUE, stroke_width=2)
            t = T(nm, size=16, color=TEXT, weight=BOLD)
            if t.width > 1.45:
                t.scale_to_fit_width(1.45)
            blocks.add(VGroup(box, t.move_to(box)))
        blocks.arrange(RIGHT, buff=0.3).move_to([0.3, 0.9, 0])
        arrs = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.03, stroke_width=2.5, color=MUTED, tip_length=0.12) for a, b in zip(blocks[:-1], blocks[1:])])
        line_in = twisted_pair([blocks[0].get_left() + LEFT * 1.1, blocks[0].get_left() + LEFT * 0.05], VIOLET, amp=0.05, pitch=0.25)
        bits_out = Arrow(blocks[-1].get_right(), blocks[-1].get_right() + RIGHT * 0.6, buff=0.03, stroke_width=2.5, color=GOOD, tip_length=0.12)
        bits_l = T("bits", size=16, color=GOOD, weight=BOLD).next_to(bits_out, UP, buff=0.05)
        x_mid = (blocks[3].get_right()[0] + blocks[4].get_left()[0]) / 2
        y_row = blocks[3].get_y()
        dfe = RoundedRectangle(width=1.7, height=0.8, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=BLUE, stroke_width=2)
        dfe_t = T("Decision\nfeedback (DFE)", size=15, color=TEXT, weight=BOLD).move_to(dfe)
        dfe_g = VGroup(dfe, dfe_t).move_to([x_mid - 0.35, -0.75, 0])
        summer = VGroup(Circle(0.14, stroke_color=BLUE, stroke_width=2, fill_color=PANEL, fill_opacity=1),
                        T("+", size=16, color=BLUE, weight=BOLD)).move_to([x_mid, y_row, 0])
        fb_path = VGroup(
            Line(blocks[4].get_bottom(), [blocks[4].get_x(), -0.75, 0]),
            Arrow([blocks[4].get_x(), -0.75, 0], dfe_g.get_right(), buff=0.02, stroke_width=2.2, tip_length=0.1),
            Arrow([x_mid, dfe_g.get_top()[1], 0], summer.get_bottom(), buff=0.02, stroke_width=2.2, tip_length=0.1),
        ).set_color(BLUE)
        clk = RoundedRectangle(width=2.0, height=0.7, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=GOOD, stroke_width=2)
        clk_t = T("Clock recovery", size=16, color=TEXT, weight=BOLD).move_to(clk)
        clk_g = VGroup(clk, clk_t).move_to([blocks[2].get_x(), -1.95, 0])
        xs_c = blocks[4].get_right()[0] - 0.25
        clk_path = VGroup(
            Line([xs_c, blocks[4].get_bottom()[1], 0], [xs_c, -1.95, 0]), Arrow([xs_c, -1.95, 0], clk_g.get_right(), buff=0.02, stroke_width=2.2, tip_length=0.1),
            Line(clk_g.get_left(), [blocks[1].get_x(), -1.95, 0]), Arrow([blocks[1].get_x(), -1.95, 0], blocks[1].get_bottom(), buff=0.02, stroke_width=2.2, tip_length=0.1),
        ).set_color(GOOD)
        clk_l = T("when to sample", size=14, color=GOOD).next_to(clk_path[3], LEFT, buff=0.1)
        digital = DashedVMobject(RoundedRectangle(width=blocks[-1].get_right()[0] - blocks[2].get_left()[0] + 0.35, height=4.0, corner_radius=0.2,
                                                  stroke_color=DIM, stroke_width=1.6), num_dashes=70)
        digital.move_to([(blocks[2].get_left()[0] + blocks[-1].get_right()[0]) / 2, -0.4, 0])
        dig_l = T("all digital", size=16, color=MUTED).next_to(digital, UP, buff=0.08).align_to(digital, RIGHT)
        with self.voice(
            "{chain}Here's the whole receive path. An amplifier with automatic gain control, and an analog-to-digital "
            "converter. {dig}Then, all in the digital domain: the echo canceller, the equalizer, the decision, and finally "
            "the descrambler and the 4B3T decoder. {loops}Two feedback loops complete the picture: decision feedback, which "
            "we'll meet in a moment, and clock recovery, which decides when to sample."
        ) as v:
            self.play(Create(line_in), LaggedStart(*[FadeIn(b, shift=RIGHT * 0.1) for b in blocks[:2]], lag_ratio=0.3), GrowArrow(arrs[0]), run_time=1.2)
            v.wait_until("dig")
            self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.1) for b in blocks[2:]], lag_ratio=0.25),
                      LaggedStart(*[GrowArrow(a) for a in arrs[1:]], lag_ratio=0.25), GrowArrow(bits_out), FadeIn(bits_l), run_time=2.0)
            self.play(Create(digital), FadeIn(dig_l), run_time=0.8)
            v.wait_until("loops")
            self.play(FadeIn(dfe_g), FadeIn(summer), Create(fb_path), run_time=1.0)
            self.play(FadeIn(clk_g), Create(clk_path), FadeIn(clk_l), run_time=1.0)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ cursors
        p = dsp.symbol_response(OSR)
        kpk = int(np.argmax(p))
        ph = kpk % OSR
        h = p / p[kpk]
        ax = Axes(x_range=[-2, 14, 1], y_range=[-0.15, 1.1, 0.5], x_length=11.5, y_length=3.6,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0, -0.2, 0])
        t0 = kpk / OSR
        ts = np.arange(len(h)) / OSR - t0
        keep = (ts >= -2) & (ts <= 14)
        curve = VMobject().set_points_as_corners([ax.c2p(t, v) for t, v in zip(ts[keep], h[keep])]).set_stroke(VIOLET, 3)
        samp = []
        for k in range(-1, 14):
            i = kpk + k * OSR
            if 0 <= i < len(h):
                samp.append((k, h[i]))
        stm = VGroup()
        for k, v_ in samp:
            col = APL if k == 0 else (PINK if k < 0 else HAZARD)
            stm.add(VGroup(Line(ax.c2p(k, 0), ax.c2p(k, v_), stroke_color=col, stroke_width=3.5), Dot(ax.c2p(k, v_), radius=0.06, color=col)))
        labs = VGroup(
            TeX(r"h_0", size=30, color=APL).next_to(ax.c2p(0, 1.0), UP, buff=0.12),
            T("main cursor", size=17, color=APL, weight=BOLD).next_to(ax.c2p(0, 1.0), RIGHT, buff=0.3),
            T("pre-cursor", size=16, color=PINK).next_to(ax.c2p(-1, samp[0][1]), UP, buff=0.4),
            T("post-cursors: the tail", size=17, color=HAZARD, weight=BOLD).next_to(ax.c2p(6, 0.35), UP, buff=0.1),
        )
        grid = VGroup(*[DashedLine(ax.c2p(k, -0.12), ax.c2p(k, 1.05), dash_length=0.05, stroke_color=DIM, stroke_width=1).set_opacity(0.6) for k in range(-2, 15)])
        xl = T("symbol periods →", size=16, color=MUTED).next_to(ax, DOWN, buff=0.15).align_to(ax, RIGHT)
        with self.voice(
            "{resp}Look again at one symbol's response after the cable, but now sampled once per symbol, the way the "
            "receiver sees it. {cursor}One sample is the largest: the main cursor. Before it sits a small pre-cursor; after "
            "it, a long series of post-cursors: the tail. {leak}Every one of those samples lands in some other symbol's decision."
        ) as v:
            self.play(Create(ax), FadeIn(grid), FadeIn(xl), run_time=0.7)
            self.play(Create(curve), run_time=1.4)
            v.wait_until("cursor")
            self.play(LaggedStart(*[GrowFromPoint(s, s[0].get_start()) for s in stm], lag_ratio=0.08), run_time=1.6)
            self.play(FadeIn(labs[0]), FadeIn(labs[1]), run_time=0.5)
            self.play(FadeIn(labs[2]), FadeIn(labs[3]), run_time=0.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ FFE in the frequency domain
        fx = Axes(x_range=[0, 5, 1], y_range=[-45, 30, 15], x_length=8.6, y_length=4.4,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-1.3, -0.35, 0])
        fxt = tick_labels(fx, [0, 1, 2, 3, 3.75, 5], "x", texts=["0", "1", "2", "3", "3.75", "5 MHz"], size=15)
        fyt = tick_labels(fx, [-30, -15, 0, 15, 30], "y", texts=["−30", "−15", "0 dB", "+15", "+30"], size=15)
        zero = DashedLine(fx.c2p(0, 0), fx.c2p(5, 0), dash_length=0.06, stroke_color=DIM, stroke_width=1.5)
        cab = fx.plot(lambda f: -float(dsp.il_db(f)), x_range=[0, 5, 0.02], color=HAZARD, stroke_width=3.5)
        eqc = fx.plot(lambda f: min(float(dsp.il_db(f)), float(dsp.il_db(3.75))) - 0.0, x_range=[0, 5, 0.02], color=BLUE, stroke_width=3.5)
        tot = fx.plot(lambda f: min(0.0, float(dsp.il_db(3.75)) - float(dsp.il_db(f))), x_range=[0, 5, 0.02], color=GOOD, stroke_width=4)
        l_cab = T("cable", size=18, color=HAZARD, weight=BOLD).next_to(fx.c2p(4.4, -float(dsp.il_db(4.4))), DOWN, buff=0.12)
        l_eq = T("equalizer", size=18, color=BLUE, weight=BOLD).next_to(fx.c2p(1.6, float(dsp.il_db(1.6))), UP, buff=0.12)
        l_tot = T("together: flat", size=18, color=GOOD, weight=BOLD).next_to(fx.c2p(1.4, 0), DOWN, buff=0.15)
        noise_before = fx.get_area(fx.plot(lambda f: -38, x_range=[0, 3.75, 0.05]), x_range=[0, 3.75], bounded_graph=fx.plot(lambda f: -45, x_range=[0, 3.75, 0.05]),
                                   color=MUTED, opacity=0.35)
        noise_after = fx.get_area(fx.plot(lambda f: -38 + min(float(dsp.il_db(f)), float(dsp.il_db(3.75))), x_range=[0, 3.75, 0.05]), x_range=[0, 3.75],
                                  bounded_graph=fx.plot(lambda f: -45, x_range=[0, 3.75, 0.05]), color=DANGER, opacity=0.35)
        nl = T("noise", size=16, color=MUTED).next_to(fx.c2p(0.3, -41), RIGHT, buff=0.05)
        nl2 = T("noise, boosted", size=17, color=DANGER, weight=BOLD).next_to(fx.c2p(3.0, -15), RIGHT, buff=0.15)
        ffe_eq = TeX(r"y_n = \sum_k c_k\, r_{n-k}", size=40, color=BLUE).move_to([4.6, 2.2, 0])
        with self.voice(
            "{ffe}A feed-forward equalizer is another FIR filter, this time on the received samples. {inv}Its weights "
            "approximate the inverse of the cable: it boosts the high frequencies that the cable stripped away, so that the "
            "two together are flat again. {noise}The catch: boosting high frequencies also boosts the noise up there."
        ) as v:
            self.play(Create(fx), FadeIn(fxt), FadeIn(fyt), FadeIn(zero), Write(ffe_eq), run_time=1.0)
            v.wait_until("inv")
            self.play(Create(cab), FadeIn(l_cab), run_time=1.0)
            self.play(Create(eqc), FadeIn(l_eq), run_time=1.0)
            self.play(Create(tot), FadeIn(l_tot), run_time=1.0)
            v.wait_until("noise")
            self.play(FadeIn(noise_before), FadeIn(nl), run_time=0.6)
            self.play(ReplacementTransform(noise_before, noise_after), FadeIn(nl2), run_time=1.4)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ DFE: subtract the tails you already know
        cur = [h[kpk + j * OSR] for j in range(0, 13)]
        hist = [1, 1, 0, 1, 1, -1, 1, 1, 0, 1, 1, 1]            # decided symbols a_{n-1} ... a_{n-12}
        a_now = 0
        contrib = [a_now * cur[0]] + [hist[j - 1] * cur[j] for j in range(1, 13)]
        wx = Axes(x_range=[-0.5, 14.5, 1], y_range=[-1.0, 3.6, 1], x_length=10.6, y_length=4.3,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0.2, -0.55, 0])
        cum = np.concatenate([[0], np.cumsum(contrib)])
        segs = VGroup()
        for j in range(13):
            y0_, y1_ = cum[j], cum[j + 1]
            col = APL if j == 0 else HAZARD
            hgt = abs(wx.c2p(0, y1_)[1] - wx.c2p(0, y0_)[1])
            r_ = Rectangle(width=0.55, height=max(hgt, 0.04), fill_color=col, fill_opacity=0.85, stroke_width=0)
            r_.move_to([wx.c2p(j, 0)[0], (wx.c2p(0, y0_)[1] + wx.c2p(0, y1_)[1]) / 2, 0])
            segs.add(r_)
        conn = VGroup(*[DashedLine([wx.c2p(j, 0)[0] + 0.28, wx.c2p(0, cum[j + 1])[1], 0], [wx.c2p(j + 1, 0)[0] - 0.28, wx.c2p(0, cum[j + 1])[1], 0],
                                   dash_length=0.04, stroke_color=DIM, stroke_width=1.2) for j in range(12)])
        tot_bar = Rectangle(width=0.7, height=abs(wx.c2p(0, cum[-1])[1] - wx.c2p(0, 0)[1]), fill_color=WHITE_SOFT, fill_opacity=0.9, stroke_width=0)
        tot_bar.move_to([wx.c2p(14, 0)[0], (wx.c2p(0, 0)[1] + wx.c2p(0, cum[-1])[1]) / 2, 0])
        tot_l = TeX(r"r_n", size=30, color=WHITE_SOFT).next_to(tot_bar, UP, buff=0.1)
        base = Line(wx.c2p(-0.5, 0), wx.c2p(14.5, 0), stroke_color=DIM, stroke_width=2)
        xl2 = VGroup(TeX(r"a_n h_0", size=22, color=APL).next_to(wx.c2p(0, -0.05), DOWN, buff=0.15),
                     T("tails of earlier symbols", size=16, color=HAZARD).next_to(wx.c2p(6.5, -0.05), DOWN, buff=0.2))
        thr = VGroup(*[DashedLine(wx.c2p(13.4, y_), wx.c2p(14.6, y_), dash_length=0.05, stroke_color=TEXT, stroke_width=1.5) for y_ in (0.5, -0.5)])
        thr_l = T("thresholds", size=13, color=MUTED).next_to(thr, RIGHT, buff=0.06)
        wrong = T("raw decision: +1  ✗", size=19, color=DANGER, weight=BOLD).move_to([4.6, 2.8, 0])
        hist_row = VGroup(*[M(SYM[s], size=22, color=HAZARD, weight=BOLD) for s in hist[:8]]).arrange(LEFT, buff=0.32)
        hist_box = VGroup(T("already decided:", size=17, color=MUTED), hist_row, T("…", size=22, color=MUTED)).arrange(RIGHT, buff=0.25)
        hist_box.move_to([-2.6, 2.8, 0])
        dfe_eq = TeX(r"y_n", r"=", r"\sum_k c_k\, r_{n-k}", r"-", r"\sum_{j\ge1} b_j\, \hat a_{n-j}", size=40).move_to([0, -3.3, 0])
        dfe_eq[2].set_color(BLUE)
        dfe_eq[4].set_color(HAZARD)
        right = T("after subtraction: 0  ✓", size=19, color=GOOD, weight=BOLD).move_to([4.6, 2.8, 0])
        with self.voice(
            "{dfe}So the long tail is handled differently. {stack}Look at what one received sample is made of: a little of the "
            "current symbol, plus the tails of all the symbols before it. Here, the tails add up to far more than the symbol "
            "itself — so a raw decision would be wrong. {known}But the receiver has already decided those earlier symbols, "
            "so it knows their tails exactly. {sub}The decision-feedback equalizer simply subtracts them. What's left is the "
            "current symbol. {eq}In one line: y-n is the filtered sample, minus the sum of b-j times the previous decisions. "
            "{clean}No noise gets amplified, because past decisions are clean numbers. {risk}The price: a wrong decision "
            "subtracts the wrong tail, so one error can drag a few more along with it."
        ) as v:
            self.play(Create(wx), Create(base), run_time=0.5)
            v.wait_until("stack")
            self.play(GrowFromEdge(segs[0], DOWN), FadeIn(xl2[0]), run_time=0.5)
            self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(s, DOWN), Create(c)) for s, c in zip(segs[1:], conn)], lag_ratio=0.25), FadeIn(xl2[1]), run_time=3.0)
            self.play(GrowFromEdge(tot_bar, DOWN), FadeIn(tot_l), FadeIn(thr), FadeIn(thr_l), run_time=0.8)
            self.play(FadeIn(wrong, shift=DOWN * 0.1), run_time=0.5)
            v.wait_until("known")
            self.play(FadeIn(hist_box, shift=DOWN * 0.1), run_time=0.8)
            v.wait_until("sub")
            new_tot = Rectangle(width=0.7, height=0.04, fill_color=WHITE_SOFT, fill_opacity=0.9, stroke_width=0).move_to(wx.c2p(14, 0))
            self.play(*[s.animate.set_opacity(0.12) for s in segs[1:]], conn.animate.set_opacity(0.15), Transform(tot_bar, new_tot),
                      tot_l.animate.next_to(new_tot, UP, buff=0.1), FadeOut(wrong), run_time=1.6)
            self.play(FadeIn(right, shift=DOWN * 0.1), run_time=0.5)
            v.wait_until("eq")
            self.play(Write(dfe_eq), run_time=1.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ Lucky, and the eye opens
        luck = name_card("Robert Lucky", "1965 · Bell Labs", "adaptive equalizers for data over phone lines", BLUE).to_corner(UR, buff=0.4).shift(DOWN * 0.1)
        a, raw, (y1, d1), (y2, d2), ph = dsp.equalised_eyes(OSR)
        start = OSR * 300
        tr0 = dsp.eye(raw, OSR, start + ph - OSR, 140)
        tr1 = dsp.eye(y1, OSR, start + ph - OSR, 140)
        tr2 = dsp.eye(y2, OSR, start + ph - OSR, 140)
        centers = [np.array([-4.5, -0.75, 0]), np.array([0, -0.75, 0]), np.array([4.5, -0.75, 0])]
        titles = ["after 1 km", "+ short FFE", "+ DFE"]
        cols = [HAZARD, BLUE, GOOD]
        eyes = VGroup()
        for tr, c_, tt, col in zip((tr0, tr1, tr2), centers, titles, cols):
            box = panel(4.0, 3.2).move_to(c_)
            e = eye_mob(tr, c_, width=3.6, height=2.6, color=col, opacity=0.2, stroke=1.3, clip=1.45, scale=1.0)
            lab = T(tt, size=20, color=col, weight=BOLD).next_to(box, UP, buff=0.12)
            eyes.add(VGroup(box, e, lab))
        lms = T("adapting continuously, with the same LMS rule", size=18, color=MUTED).move_to([0, -2.85, 0])
        with self.voice(
            "{lucky}Adaptive equalizers like these were pioneered by Robert Lucky at Bell Labs in 1965, to push data through "
            "telephone lines. {lms}Like the echo canceller, they adapt continuously, with the same least-mean-squares rule. "
            "{open}Watch the eye open."
        ) as v:
            self.play(FadeIn(luck, shift=LEFT * 0.2), run_time=0.7)
            self.play(FadeIn(eyes[0][0]), FadeIn(eyes[0][2]), LaggedStart(*[Create(m) for m in eyes[0][1]], lag_ratio=0.01), run_time=1.6)
            v.wait_until("lms")
            self.play(FadeIn(lms), run_time=0.6)
            v.wait_until("open")
            self.play(FadeIn(eyes[1][0]), FadeIn(eyes[1][2]), LaggedStart(*[Create(m) for m in eyes[1][1]], lag_ratio=0.01), run_time=1.6)
            self.play(FadeIn(eyes[2][0]), FadeIn(eyes[2][2]), LaggedStart(*[Create(m) for m in eyes[2][1]], lag_ratio=0.01), run_time=1.6)
        self.wait(0.8)
        self.clear(run_time=0.7)
