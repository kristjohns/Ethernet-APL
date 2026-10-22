import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl import dsp
from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *


def xor_gate(r=0.2, color=TEXT):
    c = Circle(r, stroke_color=color, stroke_width=2.5)
    return VGroup(c, Line(c.get_top(), c.get_bottom(), stroke_color=color, stroke_width=2.5),
                  Line(c.get_left(), c.get_right(), stroke_color=color, stroke_width=2.5))


def line_psd(symbols, osr=8, nfft=2048):
    x = np.repeat(np.asarray(symbols, float), osr)
    f, S = dsp.psd(x, dsp.BAUD * osr, nfft)
    return f / 1e6, S


class Scrambler(APLScene):
    def construct(self):
        self.tag = corner_tag("06 · From bits to symbols")
        self.add(self.tag)

        # ------------------------------------------------------------ the problem: real data has patterns
        idle = [x for c in dsp.encode_4b3t([0] * 4 * 300) for x in c]
        rnd_bits = list(np.random.default_rng(5).integers(0, 2, 4 * 3000))
        scr = [x for c in dsp.encode_4b3t(rnd_bits) for x in c]
        f1, S1 = line_psd(idle)
        f2, S2 = line_psd(scr)
        S1 = S1 / S1.max()
        S2 = S2 / S2.max()
        ax = Axes(x_range=[0, 15, 2.5], y_range=[0, 1.05, 0.5], x_length=8.8, y_length=3.0,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([1.0, -1.35, 0])
        xt = tick_labels(ax, [0, 2.5, 5, 7.5, 10, 12.5, 15], "x", texts=["0", "2.5", "5", "7.5", "10", "12.5", "15 MHz"], size=15)
        keep = f1 <= 15

        def spec(f, S, col):
            pts = [ax.c2p(a, min(b, 1.0)) for a, b in zip(f[keep], S[keep])]
            return VMobject().set_points_as_corners(pts).set_stroke(col, 2.6)

        sp1 = spec(f1, S1, DANGER)
        sp2 = spec(f2, S2, APL)
        lines_lbl = T("spectral lines: tones that radiate", size=19, color=DANGER, weight=BOLD).next_to(ax.c2p(2.5, 1.0), RIGHT, buff=0.4)
        data_txt = M("0000 0000 0000 0000 0000 0000 0000 0000", size=24, color=TEXT).move_to([0, 2.35, 0])
        data_lbl = T("an idle link: data = all zeros", size=18, color=MUTED).next_to(data_txt, UP, buff=0.12)
        idle_w = ternary_waveform(idle[:30], -5.4, 5.4, 1.0, 0.35, DANGER, 2.6, edge=0.1)
        with self.voice(
            "{before}One step comes before the coding: scrambling. {problem}Real data is anything but random: long runs of "
            "zeros, idle patterns, repeated headers. {tones}Sent as they are, they turn into periodic signals with strong "
            "spectral lines — tones that radiate and interfere — and long, monotonous stretches that tell the receiver "
            "nothing about timing."
        ) as v:
            v.wait_until("problem")
            self.play(FadeIn(data_lbl), FadeIn(data_txt, shift=DOWN * 0.1), run_time=0.8)
            self.play(Create(idle_w), run_time=1.4, rate_func=linear)
            v.wait_until("tones")
            self.play(Create(ax), FadeIn(xt), run_time=0.6)
            self.play(Create(sp1), run_time=1.4)
            self.play(FadeIn(lines_lbl), run_time=0.6)
        self.play(FadeOut(VGroup(data_lbl, data_txt, idle_w, lines_lbl)), sp1.animate.set_stroke(opacity=0.35),
                  VGroup(ax, xt, sp1).animate.scale(0.5).move_to([4.6, -2.75, 0]), run_time=0.8)

        # ------------------------------------------------------------ the LFSR
        n_cells, cw = 33, 0.31
        rx0 = -4.6
        ry = 0.55
        seq = dsp.lfsr(400)
        step = ValueTracker(33.0)
        cells_frame = VGroup(*[Square(cw, stroke_color=PANEL_EDGE, stroke_width=1.5).move_to([rx0 + cw * (i + 0.5), ry, 0]) for i in range(n_cells)])

        def cells():
            s = step.get_value()
            k = int(np.floor(s))
            fr = s - k
            g = VGroup()
            for i in range(n_cells):
                b = seq[k - 1 - i] if k - 1 - i >= 0 else 0
                x = rx0 + cw * (i + 0.5 + fr)
                if x > rx0 + cw * n_cells:
                    continue
                col = APL if b else "#16223B"
                g.add(Square(cw * 0.78, fill_color=col, fill_opacity=1, stroke_width=0).move_to([x, ry, 0]))
            return g

        live = always_redraw(cells)
        idx = VGroup(*[T(str(i), size=14, color=PINK if i in (13, 33) else MUTED, weight=BOLD if i in (13, 33) else NORMAL)
                       .next_to(cells_frame[i - 1], DOWN, buff=0.08) for i in (1, 13, 33)])
        gy = ry + 1.15
        gate = xor_gate(0.2, PINK).move_to([rx0 - 0.75, gy, 0])
        t13 = cells_frame[12].get_top()
        t33 = cells_frame[32].get_top()
        fb = VGroup(
            Line(t13, [t13[0], gy, 0]), Line([t13[0], gy, 0], gate.get_right()),
            Line(t33, [t33[0], gy + 0.45, 0]), Line([t33[0], gy + 0.45, 0], [gate.get_x(), gy + 0.45, 0]),
            Line([gate.get_x(), gy + 0.45, 0], gate.get_top()), Line(gate.get_bottom(), [gate.get_x(), ry, 0]),
        ).set_stroke(PINK, 2.5)
        fb2 = Arrow([gate.get_x(), ry, 0], cells_frame[0].get_left(), buff=0, stroke_width=2.5, color=PINK, tip_length=0.12)
        reg_lbl = T("33-bit linear-feedback shift register", size=19, color=TEXT, weight=BOLD).next_to(cells_frame, DOWN, buff=0.45)
        poly = TeX(r"s_n = s_{n-13} \oplus s_{n-33}", size=36, color=PINK).move_to([2.6, 2.6, 0])
        # data path
        dgate = xor_gate(0.22, APL).move_to([rx0 - 0.75, ry - 1.55, 0])
        s_down = Arrow([rx0 - 0.75, ry, 0], dgate.get_top(), buff=0.02, stroke_width=2.5, color=PINK, tip_length=0.12)
        x_in = Arrow(dgate.get_left() + LEFT * 0.9, dgate.get_left(), buff=0.02, stroke_width=2.5, color=TEXT, tip_length=0.12)
        x_lbl = TeX(r"x_n", size=30, color=TEXT).next_to(x_in, UP, buff=0.05)
        y_out = Arrow(dgate.get_right(), dgate.get_right() + RIGHT * 1.0, buff=0.02, stroke_width=2.5, color=APL, tip_length=0.12)
        y_lbl = TeX(r"y_n = x_n \oplus s_n", size=30, color=APL).next_to(y_out, RIGHT, buff=0.15)
        rxl = TeX(r"\text{receiver: }\; y_n \oplus s_n = x_n \oplus s_n \oplus s_n = x_n", size=32, color=GOOD).move_to([-1.2, -1.75, 0])
        with self.voice(
            "{lfsr}So the transmitter mixes every bit with a pseudo-random sequence from a linear-feedback shift register: "
            "thirty-three flip-flops in a row, with two taps fed back through an exclusive-or gate. {xor}Each data bit is "
            "exclusive-or'ed with the register's output. {rx}The receiver runs an identical register in step, and applies "
            "the same exclusive-or — which restores the data exactly, because anything exclusive-or'ed twice with the same "
            "bit is unchanged."
        ) as v:
            self.play(FadeIn(cells_frame), FadeIn(reg_lbl), run_time=0.7)
            self.add(live)
            self.play(FadeIn(idx), Create(fb), Create(fb2), FadeIn(gate), run_time=1.2)
            self.play(Write(poly), step.animate.set_value(41), run_time=2.6, rate_func=linear)
            v.wait_until("xor")
            self.play(FadeIn(dgate), GrowArrow(s_down), GrowArrow(x_in), FadeIn(x_lbl), run_time=0.8)
            self.play(GrowArrow(y_out), FadeIn(y_lbl), step.animate.set_value(47), run_time=1.6, rate_func=linear)
            v.wait_until("rx")
            self.play(Write(rxl), step.animate.set_value(55), run_time=2.4, rate_func=linear)
            self.play(step.animate.set_value(55 + 2.5 * v.until_end(0.5)), run_time=v.until_end(0.5), rate_func=linear)

        period = VGroup(TeX(r"2^{33} - 1 = 8\,589\,934\,591\ \text{bits}", size=36, color=TEXT),
                        T("≈ 14 minutes at 10 Mbit/s before the pattern repeats", size=19, color=MUTED)).arrange(DOWN, buff=0.12)
        period.move_to([-2.4, -2.75, 0])
        with self.voice(
            "{period}With this feedback polynomial, the sequence only repeats after two to the thirty-three, minus one bits: "
            "about a quarter of an hour at ten megabits per second. {flat}The result: whatever the data, the line signal "
            "looks like noise — a smooth spectrum with no tones, and plenty of transitions for the receiver's clock."
        ) as v:
            self.play(FadeOut(rxl), FadeIn(period, shift=UP * 0.1), step.animate.set_value(70), run_time=2.0, rate_func=linear)
            v.wait_until("flat")
            sp2.scale(0.5).move_to(sp1)
            sp2.shift(sp1.get_bottom() - sp2.get_bottom() + RIGHT * 0.0)
            self.play(Create(sp2), step.animate.set_value(80), run_time=2.0, rate_func=linear)
            self.play(Indicate(sp2, color=APL, scale_factor=1.05), step.animate.set_value(86), run_time=1.6, rate_func=linear)
        self.remove(live)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ master and slave use mirror-image polynomials
        m_card = VGroup(T("master", size=24, color=APL, weight=BOLD), TeX(r"1 + x^{13} + x^{33}", size=40, color=APL)).arrange(DOWN, buff=0.18)
        s_card = VGroup(T("slave", size=24, color=VIOLET, weight=BOLD), TeX(r"1 + x^{20} + x^{33}", size=40, color=VIOLET)).arrange(DOWN, buff=0.18)
        cards = VGroup(m_card, s_card).arrange(RIGHT, buff=2.4).move_to([0, 1.9, 0])
        sa = dsp.lfsr(60, (13, 33), seed=0x0F0F0F0F1)
        sb = dsp.lfsr(60, (20, 33), seed=0x0F0F0F0F1)
        rowa = VGroup(*[Square(0.17, fill_color=APL if b else "#16223B", fill_opacity=1, stroke_width=0) for b in sa]).arrange(RIGHT, buff=0.03)
        rowb = VGroup(*[Square(0.17, fill_color=VIOLET if b else "#16223B", fill_opacity=1, stroke_width=0) for b in sb]).arrange(RIGHT, buff=0.03)
        rows = VGroup(rowa, rowb).arrange(DOWN, buff=0.3).move_to([0, 0.05, 0])
        corr = TeX(r"\mathrm{E}[\,a_n\, b_m\,] \approx 0", size=40, color=GOOD).move_to([0, -1.5, 0])
        indep = T("the two directions are statistically independent", size=22, color=GOOD, weight=BOLD).next_to(corr, DOWN, buff=0.3)
        with self.voice(
            "{two}And one subtle detail. The two ends of a link use different polynomials: one plus x to the thirteen plus "
            "x to the thirty-three for the master, and its mirror image, with x to the twenty, for the slave. {indep}That "
            "makes the two directions statistically independent. Keep that in mind: the echo canceller will depend on it."
        ) as v:
            self.play(FadeIn(m_card, shift=DOWN * 0.1), run_time=0.7)
            self.play(FadeIn(s_card, shift=DOWN * 0.1), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(s) for s in rowa], lag_ratio=0.02), LaggedStart(*[FadeIn(s) for s in rowb], lag_ratio=0.02), run_time=1.6)
            v.wait_until("indep")
            self.play(Write(corr), run_time=1.0)
            self.play(FadeIn(indep), run_time=0.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the complete transmitter
        names = ["Ethernet MAC", "Scrambler", "4B3T coder", "PAM-3 DAC", "TX filter", "Line driver"]
        blocks = VGroup()
        for nm in names:
            box = RoundedRectangle(width=1.7, height=0.75, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=APL, stroke_width=2)
            t = T(nm, size=18, color=TEXT, weight=BOLD)
            if t.width > 1.55:
                t.scale_to_fit_width(1.55)
            blocks.add(VGroup(box, t.move_to(box)))
        blocks.arrange(RIGHT, buff=0.28).move_to([-0.5, 1.9, 0])
        arrs = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.03, stroke_width=2.5, color=MUTED, tip_length=0.12) for a, b in zip(blocks[:-1], blocks[1:])])
        out = twisted_pair([blocks[-1].get_right() + RIGHT * 0.05, blocks[-1].get_right() + RIGHT * 1.0], APL, amp=0.05, pitch=0.25)
        # snapshots under each block
        snaps = VGroup()
        cx = [b.get_x() for b in blocks]
        y_s = 0.35
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        sbits = [b ^ s for b, s in zip(bits, seq[50:58])]
        snaps.add(M("".join(map(str, bits)), size=17, color=TEXT).move_to([cx[0], y_s, 0]))
        snaps.add(M("".join(map(str, sbits)), size=17, color=APL).move_to([cx[1], y_s, 0]))
        tri = dsp.encode_4b3t(sbits)
        snaps.add(M("  ".join(sym_s for sym_s in ["".join({1: "+", 0: "0", -1: "−"}[x] for x in c) for c in tri]), size=17, color=APL).move_to([cx[2], y_s, 0]))
        flat = [x for c in tri for x in c]
        snaps.add(ternary_waveform(flat, cx[3] - 0.85, cx[3] + 0.85, y_s, 0.3, APL, 2.4, edge=0.02))
        osr = 24
        xr = np.repeat(np.array(flat, float), osr)
        k = np.exp(-np.linspace(-2.5, 2.5, 21) ** 2)
        k /= k.sum()
        sm = np.convolve(xr, k, mode="same")
        xs = np.linspace(cx[4] - 0.85, cx[4] + 0.85, len(sm))
        snaps.add(VMobject().set_points_as_corners(np.stack([xs, y_s + 0.3 * sm, 0 * xs], 1)).set_stroke(APL, 2.4))
        xs2 = np.linspace(cx[5] - 0.85, cx[5] + 0.85, len(sm))
        snaps.add(VMobject().set_points_as_corners(np.stack([xs2, y_s + 0.42 * sm, 0 * xs2], 1)).set_stroke(APL, 3))
        conn = VGroup(*[DashedLine(b.get_bottom(), [b.get_x(), y_s + 0.45, 0], dash_length=0.05, stroke_color=DIM, stroke_width=1.2) for b in blocks])
        rs = resistor(0.9, color=APL, label="100 Ω", label_size=18).move_to([2.5, -1.35, 0])
        drv = VGroup(Triangle(fill_color=PANEL, fill_opacity=1, stroke_color=APL, stroke_width=2.5).scale(0.4).rotate(-PI / 2).move_to([1.15, -1.35, 0]))
        wire_o = twisted_pair([[3.0, -1.35, 0], [6.0, -1.35, 0]], APL, amp=0.05, pitch=0.3)
        lvls = VGroup(
            VGroup(T("trunk", size=19, color=APL, weight=BOLD), T("±1.2 V  (2.4 Vpp)", size=19, color=TEXT)).arrange(RIGHT, buff=0.25),
            VGroup(T("IS spur", size=19, color=HAZARD, weight=BOLD), T("±0.5 V  (1.0 Vpp)", size=19, color=TEXT)).arrange(RIGHT, buff=0.25),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([-3.3, -1.45, 0])
        src_lbl = T("source impedance matched to the cable", size=17, color=MUTED).next_to(rs, DOWN, buff=0.35).shift(RIGHT * 0.6)
        with self.voice(
            "{chain}So here's the complete transmitter. Bits from the Ethernet MAC are scrambled, grouped in fours, and "
            "mapped onto ternary triplets. {dac}A digital-to-analog converter turns each symbol into one of three voltages, "
            "and a filter rounds off the edges to keep emissions low. {drv}Finally, a line driver with a hundred-ohm source "
            "impedance launches the wave into the cable: plus or minus 1.2 volts on a trunk, or plus or minus half a volt on "
            "an intrinsically safe spur."
        ) as v:
            self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.1) for b in blocks[:3]], lag_ratio=0.3),
                      LaggedStart(*[GrowArrow(a) for a in arrs[:2]], lag_ratio=0.3), run_time=1.4)
            self.play(LaggedStart(*[FadeIn(s) for s in snaps[:3]], lag_ratio=0.3), FadeIn(conn[:3]), run_time=1.2)
            v.wait_until("dac")
            self.play(FadeIn(blocks[3]), FadeIn(blocks[4]), GrowArrow(arrs[2]), GrowArrow(arrs[3]), run_time=0.8)
            self.play(Create(snaps[3]), Create(snaps[4]), FadeIn(conn[3:5]), run_time=1.4)
            v.wait_until("drv")
            self.play(FadeIn(blocks[5]), GrowArrow(arrs[4]), Create(out), Create(snaps[5]), FadeIn(conn[5]), run_time=1.0)
            self.play(FadeIn(drv), FadeIn(rs), Create(wire_o), FadeIn(src_lbl), run_time=1.0)
            self.play(FadeIn(lvls[0], shift=RIGHT * 0.1), run_time=0.6)
            self.play(FadeIn(lvls[1], shift=RIGHT * 0.1), run_time=0.6)
        self.wait(0.4)
        self.clear(run_time=0.7)
