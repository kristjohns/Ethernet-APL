import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl import dsp
from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *


def sym_str(c):
    return " ".join({1: "+", 0: "0", -1: "−"}[x] for x in c)


class LineCodes(APLScene):
    def construct(self):
        self.tag = corner_tag("06 · From bits to symbols")
        self.add(self.tag)

        # ------------------------------------------------------------ Manchester (10BASE-T)
        bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0]
        x0, x1 = -4.6, 5.6
        bw = (x1 - x0) / len(bits)
        y_b, y_m = 2.3, 1.2
        bit_lbls = VGroup(*[M(str(b), size=26, color=TEXT, weight=BOLD).move_to([x0 + bw * (i + 0.5), y_b, 0]) for i, b in enumerate(bits)])
        man_pts = []
        for i, b in enumerate(bits):
            a, c = (-1, 1) if b else (1, -1)
            xa = x0 + bw * i
            man_pts += [(xa, a), (xa + bw / 2, a), (xa + bw / 2, c), (xa + bw, c)]
        man = polyline([(x, y_m + 0.42 * y) for x, y in man_pts], PINK, 3.5)
        grid = VGroup(*[DashedLine([x0 + bw * i, y_m - 0.6, 0], [x0 + bw * i, y_b + 0.25, 0], dash_length=0.05, stroke_color=DIM, stroke_width=1)
                        for i in range(len(bits) + 1)])
        man_lbl = VGroup(T("Manchester", size=24, color=PINK, weight=BOLD), T("10BASE-T, 1990", size=16, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.05)
        man_lbl.next_to([x0, y_m, 0], LEFT, buff=0.3)
        bit_name = T("bits", size=20, color=MUTED).next_to([x0, y_b, 0], LEFT, buff=0.3)

        # spectra (top) and cable loss (bottom) on a shared frequency axis
        fmax = 20
        axs = Axes(x_range=[0, fmax, 2.5], y_range=[0, 1.05, 0.5], x_length=9.6, y_length=1.9,
                   axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0.6, -0.75, 0])
        axl = Axes(x_range=[0, fmax, 2.5], y_range=[0, 70, 10], x_length=9.6, y_length=1.25,
                   axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0.6, -2.85, 0])
        f_man = lambda f: (np.sinc(f / 20) * np.sin(np.pi * f / 20)) ** 2 / 0.525
        psd_man = axs.plot(lambda f: min(1.0, f_man(f)), x_range=[0.01, fmax, 0.05], color=PINK, stroke_width=3.5)
        area_man = axs.get_area(psd_man, x_range=[0.01, fmax], color=PINK, opacity=0.18)
        loss = axl.plot(lambda f: float(dsp.il_db(f)), x_range=[0, fmax, 0.05], color=HAZARD, stroke_width=3)
        xt = tick_labels(axl, [0, 5, 10, 15, 20], "x", texts=["0", "5", "10", "15", "20 MHz"], size=15)
        s_lbl = T("signal spectrum", size=16, color=MUTED).next_to(axs, LEFT, buff=0.2)
        l_lbl = T("cable loss, 1 km", size=16, color=HAZARD).next_to(axl, LEFT, buff=0.2)
        l_ticks = VGroup(*[T(f"{d} dB", size=13, color=HAZARD).next_to(axl.c2p(fmax, d), RIGHT, buff=0.1) for d in (0, 30, 60)])
        band = Rectangle(width=axs.c2p(10, 0)[0] - axs.c2p(5, 0)[0], height=4.3, fill_color=PINK, fill_opacity=0.08, stroke_width=0)
        band.move_to([(axs.c2p(5, 0)[0] + axs.c2p(10, 0)[0]) / 2, -1.75, 0])
        man_loss = T("30 – 45 dB", size=22, color=PINK, weight=BOLD).next_to(axl.c2p(7.5, 38), RIGHT, buff=0.6)
        with self.voice(
            "{same}Let's turn those knobs for ten megabits per second. {manch}The original twisted-pair Ethernet, 10BASE-T, "
            "used Manchester code: every bit is a transition in the middle of its bit period — up for a one, down for a zero. "
            "It's robust, and it carries its own clock. {cost}But it can need two transitions per bit, so its energy sits "
            "between about five and ten megahertz. {loss}On a kilometer of cable, that costs thirty to forty-five dB. "
            "Far too much."
        ) as v:
            self.play(FadeIn(bit_name), LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in bit_lbls], lag_ratio=0.06), FadeIn(grid), run_time=1.0)
            v.wait_until("manch")
            self.play(FadeIn(man_lbl), Create(man), run_time=2.4, rate_func=linear)
            v.wait_until("cost")
            self.play(Create(axs), FadeIn(s_lbl), run_time=0.6)
            self.play(Create(psd_man), FadeIn(area_man), run_time=1.4)
            v.wait_until("loss")
            self.play(Create(axl), FadeIn(xt), FadeIn(l_lbl), FadeIn(l_ticks), run_time=0.6)
            self.play(Create(loss), run_time=1.0)
            self.play(FadeIn(band), FadeIn(man_loss), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the options at 10 Mbit/s
        rows = [
            ("PAM-2", "2 levels", "10 MBd", 5.0, 1.0, MUTED),
            ("PAM-3", "3 levels", "7.5 MBd", 3.75, 0.5, APL),
            ("PAM-4", "4 levels", "5 MBd", 2.5, 1 / 3, VIOLET),
        ]
        hdr = VGroup(T("code", size=18, color=MUTED), T("symbol rate", size=18, color=MUTED), T("Nyquist", size=18, color=MUTED),
                     T("cable loss at Nyquist", size=18, color=MUTED), T("level spacing", size=18, color=MUTED))
        cols_x = [-5.3, -2.9, -1.2, 1.6, 4.9]
        for h, x in zip(hdr, cols_x):
            h.move_to([x, 2.35, 0])
        table = VGroup()
        rng = np.random.default_rng(3)
        for r, (name, lv, baud, fn, spacing, col) in enumerate(rows):
            y = 1.35 - r * 1.3
            n_lv = int(lv[0])
            syms = rng.integers(0, n_lv, 10)
            levels = -1 + 2 * syms / (n_lv - 1)
            wv = ternary_waveform(levels, -6.45, -4.75, y, 0.32, col, 2.5, edge=0.12)
            nm = VGroup(T(name, size=22, color=col, weight=BOLD), T(lv, size=14, color=MUTED)).arrange(DOWN, buff=0.04).move_to([-4.1, y, 0])
            nm.next_to(wv, RIGHT, buff=0.15)
            br = T(baud, size=22, color=TEXT).move_to([cols_x[1], y, 0])
            ny = T(f"{fn:g} MHz", size=22, color=TEXT).move_to([cols_x[2], y, 0])
            ldb = float(dsp.il_db(fn))
            bar = Rectangle(width=2.6 * ldb / 32, height=0.32, fill_color=HAZARD, fill_opacity=0.85, stroke_width=0)
            bar.move_to([0.35, y, 0], aligned_edge=LEFT)
            bl = T(f"{ldb:.1f} dB", size=19, color=HAZARD, weight=BOLD).next_to(bar, RIGHT, buff=0.12)
            sb = Rectangle(width=1.6 * spacing, height=0.32, fill_color=col, fill_opacity=0.85, stroke_width=0)
            sb.move_to([4.15, y, 0], aligned_edge=LEFT)
            sl = T({1.0: "1", 0.5: "½", 1 / 3: "⅓"}[spacing], size=20, color=col, weight=BOLD).next_to(sb, RIGHT, buff=0.12)
            table.add(VGroup(wv, nm, br, ny, VGroup(bar, bl), VGroup(sb, sl)))
        hl = SurroundingRectangle(table[1], color=APL, buff=0.15, corner_radius=0.12)
        note = T("fewer levels → higher frequency → more loss        more levels → closer spacing → more noise margin needed",
                 size=16, color=MUTED).move_to([0, -2.6, 0])
        with self.voice(
            "{lv}Now compare the options for ten megabits per second, by the frequency they need and the loss at that "
            "frequency. {p2}Two levels at ten megabaud: Nyquist at five megahertz, and thirty dB of loss. {p3}Three levels at "
            "7.5 megabaud: 3.75 megahertz, and 25.6 dB. {p4}Four levels at five megabaud: 2.5 megahertz, about twenty dB — "
            "but now the levels are packed closer together, so every dB saved in the cable is paid for in noise margin. "
            "{choice}10BASE-T1L chose three levels: a compromise between cable loss, emissions and noise margin — combined "
            "with a code that keeps the signal free of DC."
        ) as v:
            self.play(LaggedStart(*[FadeIn(h) for h in hdr], lag_ratio=0.1), run_time=0.8)
            v.wait_until("p2")
            self.play(FadeIn(table[0][:4]), GrowFromEdge(table[0][4][0], LEFT), FadeIn(table[0][4][1]), run_time=1.0)
            self.play(GrowFromEdge(table[0][5][0], LEFT), FadeIn(table[0][5][1]), run_time=0.5)
            v.wait_until("p3")
            self.play(FadeIn(table[1][:4]), GrowFromEdge(table[1][4][0], LEFT), FadeIn(table[1][4][1]), run_time=1.0)
            self.play(GrowFromEdge(table[1][5][0], LEFT), FadeIn(table[1][5][1]), run_time=0.5)
            v.wait_until("p4")
            self.play(FadeIn(table[2][:4]), GrowFromEdge(table[2][4][0], LEFT), FadeIn(table[2][4][1]), run_time=1.0)
            self.play(GrowFromEdge(table[2][5][0], LEFT), FadeIn(table[2][5][1]), run_time=0.5)
            self.play(FadeIn(note), run_time=0.6)
            v.wait_until("choice")
            self.play(Create(hl), dim_to(table[0], 0.3), dim_to(table[2], 0.3), run_time=0.9)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ 4B3T
        rbits = [1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0]
        codes = dsp.encode_4b3t(rbits)
        groups = VGroup(*[M("".join(map(str, rbits[4 * i: 4 * i + 4])), size=34, color=TEXT, weight=BOLD) for i in range(4)])
        groups.arrange(RIGHT, buff=1.15).move_to(UP * 2.35 + RIGHT * 0.4)
        g_lbl = T("4 bits", size=20, color=MUTED).next_to(groups, LEFT, buff=0.5)
        trip = VGroup(*[M(sym_str(c), size=32, color=APL, weight=BOLD) for c in codes])
        for t, gr in zip(trip, groups):
            t.move_to(gr.get_center() + DOWN * 1.3)
        t_lbl = T("3 ternary symbols", size=20, color=MUTED).next_to(trip, LEFT, buff=0.5).align_to(g_lbl, RIGHT)
        arrows = VGroup(*[Arrow(gr.get_bottom(), t.get_top(), buff=0.12, stroke_color=MUTED, stroke_width=3,
                                max_tip_length_to_length_ratio=0.2) for gr, t in zip(groups, trip)])
        flat = [x for c in codes for x in c]
        wv = ternary_waveform(flat, groups.get_left()[0] - 0.2, groups.get_right()[0] + 0.2, -0.6, 0.4, APL, 3.5, edge=0.1)
        sep = VGroup(*[DashedLine([wv.get_left()[0] + (groups.get_width() + 0.4) * k / 4, -1.15, 0],
                                  [wv.get_left()[0] + (groups.get_width() + 0.4) * k / 4, -0.05, 0], dash_length=0.05,
                                  stroke_color=DIM, stroke_width=1.5) for k in range(1, 4)])

        def dot_grid(n, cols, col, used=None):
            dg = VGroup(*[Dot(radius=0.075, color=col) for _ in range(n)]).arrange_in_grid(cols=cols, buff=0.12)
            if used is not None:
                for i, d in enumerate(dg):
                    if i >= used:
                        d.set_color(PINK)
            return dg

        c16 = VGroup(T("2⁴ = 16", size=26, color=TEXT, weight=BOLD), dot_grid(16, 8, TEXT)).arrange(DOWN, buff=0.2)
        c27 = VGroup(T("3³ = 27", size=26, color=APL, weight=BOLD), dot_grid(27, 9, APL, used=16)).arrange(DOWN, buff=0.2)
        counts = VGroup(c16, c27).arrange(RIGHT, buff=1.0, aligned_edge=UP).move_to(DOWN * 2.55 + LEFT * 3.2)
        eq = TeX(r"7.5\,\mathrm{MBd}", r"\times", r"\tfrac{4}{3}\,\tfrac{\text{bit}}{\text{symbol}}", r"=", r"10\ \mathrm{Mbit/s}", size=40)
        eq[0].set_color(APL)
        eq[4].set_color(APL)
        eq.move_to([3.4, -2.55, 0])
        with self.voice(
            "{map}The code is called 4B3T: four bits in, three ternary symbols out. {count}Four bits have sixteen "
            "combinations; three ternary symbols have twenty-seven. {rate}And seven and a half million symbols per second, "
            "times four-thirds of a bit each, is exactly ten megabits per second."
        ) as v:
            self.play(LaggedStart(*[FadeIn(gr, shift=DOWN * 0.1) for gr in groups], lag_ratio=0.2), FadeIn(g_lbl), run_time=1.0)
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2),
                      LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in trip], lag_ratio=0.2), FadeIn(t_lbl), run_time=1.4)
            self.play(Create(wv), FadeIn(sep), run_time=1.4, rate_func=linear)
            v.wait_until("count")
            self.play(FadeIn(c16, shift=UP * 0.1), run_time=0.6)
            self.play(FadeIn(c27, shift=UP * 0.1), run_time=0.6)
            v.wait_until("rate")
            self.play(Write(eq), run_time=2.0)
        self.play(FadeOut(VGroup(counts, eq, sep)), wv.animate.shift(DOWN * 0.15), run_time=0.6)

        # mirror pairs and the running sum
        pair = VGroup(M("1101", size=30, color=TEXT, weight=BOLD), T("→", size=28, color=MUTED),
                      M("+ + 0", size=30, color=APL, weight=BOLD), T("or", size=22, color=MUTED), M("− − 0", size=30, color=VIOLET, weight=BOLD)
                      ).arrange(RIGHT, buff=0.3).move_to([-2.6, -2.2, 0])
        pair_l = T("same data, sums +2 and −2", size=17, color=MUTED).next_to(pair, DOWN, buff=0.15)
        rds_vals = np.cumsum(flat)
        meter_ax = Line(UP * 0.75, DOWN * 0.75, stroke_color=DIM, stroke_width=3).move_to([5.9, -0.75, 0])
        zero_tick = Line(LEFT * 0.18, RIGHT * 0.18, stroke_color=MUTED, stroke_width=2).move_to(meter_ax)
        rds_t = ValueTracker(0)

        def needle():
            k = int(rds_t.get_value())
            val = int(rds_vals[min(k, len(rds_vals) - 1)]) if k > 0 else 0
            y = meter_ax.get_center()[1] + 0.25 * val
            return VGroup(Triangle(fill_color=GOOD, fill_opacity=1, stroke_width=0).scale(0.11).rotate(-PI / 2).move_to([5.62, y, 0]),
                          T(f"{val:+d}", size=18, color=GOOD).move_to([6.35, y, 0]))

        nd = always_redraw(needle)
        m_lbl = T("running sum", size=16, color=MUTED).next_to(meter_ax, UP, buff=0.12)
        isdn = VGroup(icon("device-landline-phone", MUTED, 0.5), T("4B3T on ISDN telephone lines, 1980s", size=18, color=MUTED)).arrange(RIGHT, buff=0.2)
        isdn.move_to([3.0, -2.2, 0])
        with self.voice(
            "{disp}The spare combinations buy something valuable. Many triplets have a non-zero sum, like plus, plus, zero. "
            "So each group of four bits gets two possible codes, mirror images of each other, and the encoder keeps a "
            "running sum of everything it has sent. {choose}When the sum is positive, it picks the version that pulls it "
            "back down, and vice versa. The running sum stays bounded, so the signal's average is zero. {isdn}The idea "
            "isn't new: a 4B3T code carried ISDN over ordinary telephone pairs in the 1980s — also full duplex, with echo "
            "cancellation, over several kilometers."
        ) as v:
            self.play(FadeIn(pair[:3], shift=UP * 0.1), run_time=0.7)
            self.play(FadeIn(pair[3:], shift=UP * 0.1), FadeIn(pair_l), run_time=0.7)
            v.wait_until("choose")
            self.play(FadeIn(meter_ax), FadeIn(zero_tick), FadeIn(m_lbl), run_time=0.4)
            self.add(nd)
            self.play(rds_t.animate.set_value(len(rds_vals)), run_time=3.0, rate_func=linear)
            v.wait_until("isdn")
            self.play(FadeIn(isdn, shift=UP * 0.1), run_time=0.7)
        self.remove(nd)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ baseline wander
        rng = np.random.default_rng(21)
        dbits = list(rng.integers(0, 2, 4 * 12)) + [1, 1, 0, 1] * 28      # random data, then a repetitive pattern
        bal = [x for c in dsp.encode_4b3t(dbits) for x in c]
        unb = []
        for i in range(0, len(dbits) - 3, 4):
            nib = int("".join(str(int(b)) for b in dbits[i:i + 4]), 2)
            unb += list(dsp.TABLE[nib][0])                 # always the "positive" version: no running-sum rule
        osr = 8
        xb = np.repeat(np.array(bal, float), osr)
        xu = np.repeat(np.array(unb, float), osr)
        alpha = 0.99
        yb, yu = dsp.highpass(xb, alpha), dsp.highpass(xu, alpha)
        n = len(xb)
        wx0, wx1 = -4.2, 6.4
        ts = np.linspace(wx0, wx1, n)

        def trace(vals, y0, col, sc=0.42):
            return VMobject().set_points_as_corners(np.stack([ts, y0 + sc * vals, 0 * ts], 1)).set_stroke(col, 2.4)

        hp = VGroup(capacitor(0.7, color=TEXT), resistor(0.8, color=TEXT).rotate(PI / 2))
        hp[0].move_to([-5.6, 2.3, 0])
        hp[1].move_to([-5.0, 1.75, 0])
        hp_w = VGroup(Line([-6.3, 2.3, 0], hp[0].get_left()), Line(hp[0].get_right(), [-4.6, 2.3, 0]),
                      Line([-5.0, 2.3, 0], hp[1].get_top()), Line(hp[1].get_bottom(), [-5.0, 1.2, 0]), Line([-6.3, 1.2, 0], [-4.6, 1.2, 0])).set_stroke(TEXT, 2.4)
        hp_lbl = T("AC coupling = high-pass filter", size=18, color=TEXT, weight=BOLD).next_to(VGroup(hp, hp_w), RIGHT, buff=0.3)
        y_u, y_b2 = 0.15, -2.35
        thr = VGroup()
        for y0 in (y_u, y_b2):
            for t in (0.5, -0.5):
                thr.add(DashedLine([wx0, y0 + 0.42 * t, 0], [wx1, y0 + 0.42 * t, 0], dash_length=0.06, stroke_color=MUTED, stroke_width=1.6))
        tu = trace(yu, y_u, DANGER)
        drift = np.convolve(yu - xu, np.ones(osr * 3) / (osr * 3), mode="same")        # the slowly moving baseline
        base_u = VMobject().set_points_as_corners(np.stack([ts, y_u + 0.42 * drift, 0 * ts], 1)).set_stroke(POWER, 5, opacity=0.8)
        base_l = T("baseline", size=15, color=POWER, weight=BOLD).move_to([wx1 - 0.55, y_u + 0.42 * drift[-1] - 0.75, 0])
        tb = trace(yb, y_b2, GOOD)
        lu = VGroup(T("without DC balance", size=19, color=DANGER, weight=BOLD), T("baseline wanders", size=15, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.04)
        lu.next_to([wx0, y_u, 0], LEFT, buff=0.25)
        lb = VGroup(T("4B3T, balanced", size=19, color=GOOD, weight=BOLD), T("baseline stays put", size=15, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.04)
        lb.next_to([wx0, y_b2, 0], LEFT, buff=0.25)
        # mark wrong decisions on the unbalanced trace
        errs = VGroup()
        idx = np.arange(osr // 2, n, osr)
        for k, i in enumerate(idx):
            s = unb[k]
            yv = yu[i]
            dec = 1 if yv > 0.5 else (-1 if yv < -0.5 else 0)
            if dec != s and k > 8:
                errs.add(Dot([ts[i], y_u + 0.42 * yv, 0], radius=0.05, color=DANGER))
        with self.voice(
            "{why}Why does DC matter so much? {ac}Because the data path is AC-coupled. Capacitors and transformers — and, as "
            "we'll see, the network that lets power share the pair — block DC. {hp}Electrically, that's a high-pass filter. "
            "{wander}Feed it a signal with a DC component, and the output slowly drifts — baseline wander — until the levels "
            "no longer sit where the receiver's thresholds expect them. {bal}With a balanced code, there's nothing to drift. "
            "The baseline stays put."
        ) as v:
            v.wait_until("ac")
            self.play(Create(hp_w), FadeIn(hp), run_time=1.0)
            v.wait_until("hp")
            self.play(FadeIn(hp_lbl), run_time=0.6)
            v.wait_until("wander")
            self.play(FadeIn(thr[:2]), FadeIn(lu), run_time=0.5)
            self.play(Create(tu), run_time=2.6, rate_func=linear)
            self.play(Create(base_u), FadeIn(base_l), run_time=1.2)
            if len(errs):
                self.play(LaggedStart(*[FadeIn(e, scale=0.5) for e in errs], lag_ratio=0.02), run_time=1.0)
            v.wait_until("bal")
            self.play(FadeIn(thr[2:]), FadeIn(lb), run_time=0.5)
            self.play(Create(tb), run_time=2.4, rate_func=linear)
        self.wait(0.4)
        self.clear(run_time=0.7)
