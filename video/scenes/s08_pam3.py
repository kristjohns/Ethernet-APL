import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *

# ---------------------------------------------------------------- an illustrative DC-balanced 4B3T code
# 27 ternary triplets: 7 with zero disparity, plus mirrored pairs with disparity ±1 and ±2.
_ZERO = [(1, 0, -1), (1, -1, 0), (0, 1, -1), (0, -1, 1), (-1, 1, 0), (-1, 0, 1), (0, 0, 0)]
_PLUS1 = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)]
_PLUS2 = [(1, 1, 0), (1, 0, 1), (0, 1, 1)]
TABLE = {}
for nib in range(16):
    if nib < 7:
        TABLE[nib] = (_ZERO[nib], _ZERO[nib])
    elif nib < 13:
        p = _PLUS1[nib - 7]
        TABLE[nib] = (p, tuple(-x for x in p))
    else:
        p = _PLUS2[nib - 13]
        TABLE[nib] = (p, tuple(-x for x in p))


def encode(bits):
    rds, out = 0, []
    for i in range(0, len(bits), 4):
        nib = int("".join(map(str, bits[i:i + 4])), 2)
        pos, neg = TABLE[nib]
        code = pos if rds <= 0 else neg
        rds += sum(code)
        out.append(code)
    return out


def sym_str(c):
    return " ".join({1: "+", 0: "0", -1: "−"}[x] for x in c)


def eye_traces(n_traces=110, osr=32, closed=True, seed=5):
    """Simulated PAM-3 eye: rectangular symbols -> lossy channel -> (optional) equaliser."""
    rng = np.random.default_rng(seed)
    syms = rng.integers(-1, 2, 600).astype(float)
    x = np.repeat(syms, osr)
    t = np.arange(0, 6 * osr) / osr
    h = np.exp(-t / 0.55) * (1 + 0.0 * t)
    h += 0.35 * np.exp(-t / 2.2)  # long tail (skin effect / dielectric)
    h /= h.sum()
    y = np.convolve(x, h)[: len(x)]
    if not closed:
        # 7-tap symbol-spaced zero-forcing-ish equaliser fitted by least squares
        d = 2
        A = np.stack([np.roll(y, k * osr) for k in range(7)], 1)[osr * 10: -osr * 10]
        target = np.roll(x, d * osr + osr // 2)[osr * 10: -osr * 10]
        w, *_ = np.linalg.lstsq(A, target, rcond=None)
        y = np.stack([np.roll(y, k * osr) for k in range(7)], 1) @ w
    y = y / (np.percentile(np.abs(y[osr * 20:]), 99) + 1e-9)
    traces = []
    start = osr * 30
    for i in range(n_traces):
        a = start + i * osr + (osr // 2 if not closed else osr // 2 + 6)
        traces.append(y[a: a + 2 * osr + 1])
    return traces


class PAM3(APLScene):
    def construct(self):
        self.tag = corner_tag("04 · Inside Ethernet-APL")
        self.add(self.tag)

        # ------------------------------------------------------------ two levels vs three
        def level_lines(y_mid, amp, levels, col, x0=-3.4, x1=5.9):
            g = VGroup()
            for lv in levels:
                g.add(DashedLine([x0, y_mid + amp * lv, 0], [x1, y_mid + amp * lv, 0], dash_length=0.06, stroke_color=DIM, stroke_width=1.2))
            return g

        can_bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]
        y_can, y_pam = 1.55, -1.25
        can_wave = polyline(step_points([0.5 if b else -0.5 for b in can_bits], -3.4, 9.3 / len(can_bits), y_of=lambda v: y_can + 0.9 * v, edge=0.08), CAN, 3.5)
        pam_syms = [1, 0, -1, -1, 0, 1, 1, -1, 0, 1, 0, -1, 1, 1, 0, -1, 0, 0]
        pam_wave = ternary_waveform(pam_syms, -3.4, 5.9, y_pam, 0.75, APL, 3.5, edge=0.1)
        can_lbl = VGroup(T("CAN", size=28, color=CAN, weight=BOLD), T("2 levels · 1 bit per symbol", size=19, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        can_lbl.to_edge(LEFT, buff=0.45).set_y(y_can)
        pam_lbl = VGroup(T("PAM-3", size=28, color=APL, weight=BOLD), T("3 levels", size=19, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        pam_lbl.to_edge(LEFT, buff=0.45).set_y(y_pam)
        lv_can = level_lines(y_can, 0.9, [-0.5, 0.5], CAN)
        lv_pam = level_lines(y_pam, 0.75, [-1, 0, 1], APL)
        pam_marks = VGroup(*[T(s, size=20, color=APL, weight=BOLD).move_to([6.35, y_pam + 0.75 * v, 0]) for s, v in [("+1", 1), ("0", 0), ("−1", -1)]])
        with self.voice(
            "{next}Next: how do you push ten megabits per second through a kilometer of cable originally designed for "
            "slow fieldbus signals? {low}You keep the frequencies low."
        ) as v:
            q = VGroup(T("10 Mbit/s", size=40, color=APL, weight=BOLD), T("through", size=28, color=MUTED),
                       T("1 km of fieldbus cable?", size=40, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.3)
            self.play(FadeIn(q, shift=UP * 0.2), run_time=1.0)
            v.wait_until("low")
            hint = T("keep the frequencies low", size=32, color=APL).next_to(q, DOWN, buff=0.5)
            self.play(FadeIn(hint, shift=UP * 0.1), run_time=0.8)
        self.play(FadeOut(VGroup(q, hint)), run_time=0.5)

        with self.voice(
            "{can}CAN uses two voltage levels: one bit per symbol. {pam}10BASE-T1L uses three: plus, zero, and minus. "
            "This is called PAM-3."
        ) as v:
            self.play(FadeIn(can_lbl), FadeIn(lv_can), Create(can_wave), run_time=1.6)
            v.wait_until("pam")
            self.play(FadeIn(pam_lbl), FadeIn(lv_pam), FadeIn(pam_marks), Create(pam_wave), run_time=1.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ 4B3T
        bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1]
        codes = encode(bits)
        groups = VGroup()
        for i in range(4):
            groups.add(M("".join(map(str, bits[4 * i: 4 * i + 4])), size=34, color=TEXT, weight=BOLD))
        groups.arrange(RIGHT, buff=1.15).move_to(UP * 2.35)
        g_lbl = T("4 data bits", size=20, color=MUTED).next_to(groups, LEFT, buff=0.5)
        trip = VGroup(*[M(sym_str(c), size=32, color=APL, weight=BOLD) for c in codes])
        for t, gr in zip(trip, groups):
            t.move_to(gr.get_center() + DOWN * 1.35)
        t_lbl = T("3 ternary symbols", size=20, color=MUTED).next_to(trip, LEFT, buff=0.5).align_to(g_lbl, RIGHT)
        arrows = VGroup(*[Arrow(gr.get_bottom(), t.get_top(), buff=0.12, stroke_color=MUTED, stroke_width=3,
                                max_tip_length_to_length_ratio=0.2) for gr, t in zip(groups, trip)])
        flat = [x for c in codes for x in c]
        wv = ternary_waveform(flat, groups.get_left()[0] - 0.2, groups.get_right()[0] + 0.2, -0.65, 0.42, APL, 3.5, edge=0.1)
        sep = VGroup(*[DashedLine([wv.get_left()[0] + (groups.get_width() + 0.4) * k / 4, -1.2, 0],
                                  [wv.get_left()[0] + (groups.get_width() + 0.4) * k / 4, -0.1, 0], dash_length=0.05,
                                  stroke_color=DIM, stroke_width=1.5) for k in range(1, 4)])

        # 16 vs 27
        def dot_grid(n, cols, col, used=None):
            dg = VGroup(*[Dot(radius=0.075, color=col) for _ in range(n)]).arrange_in_grid(cols=cols, buff=0.12)
            if used is not None:
                for i, d in enumerate(dg):
                    if i >= used:
                        d.set_color(PINK)
            return dg

        g16 = dot_grid(16, 8, TEXT)
        g27 = dot_grid(27, 9, APL, used=16)
        c16 = VGroup(T("2⁴ = 16", size=26, color=TEXT, weight=BOLD), g16).arrange(DOWN, buff=0.2)
        c27 = VGroup(T("3³ = 27", size=26, color=APL, weight=BOLD), g27).arrange(DOWN, buff=0.2)
        counts = VGroup(c16, c27).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to(DOWN * 2.55 + LEFT * 2.2)
        spare = T("11 spare codes → DC balance", size=20, color=PINK, weight=BOLD).next_to(c27, RIGHT, buff=0.3)

        # running digital sum meter
        rds_vals = np.cumsum(flat)
        meter_ax = Line(UP * 0.6, DOWN * 0.6, stroke_color=DIM, stroke_width=3).move_to([5.9, -0.65, 0])
        zero_tick = Line(LEFT * 0.18, RIGHT * 0.18, stroke_color=MUTED, stroke_width=2).move_to(meter_ax)
        rds_t = ValueTracker(0)

        def needle():
            k = int(rds_t.get_value())
            val = rds_vals[min(k, len(rds_vals) - 1)] if k > 0 else 0
            y = meter_ax.get_center()[1] + 0.2 * val
            return VGroup(Triangle(fill_color=GOOD, fill_opacity=1, stroke_width=0).scale(0.11).rotate(-PI / 2).move_to([5.62, y, 0]),
                          T(f"{val:+d}", size=18, color=GOOD).move_to([6.35, y, 0]))

        nd = always_redraw(needle)
        m_lbl = T("running DC sum", size=16, color=MUTED).next_to(meter_ax, UP, buff=0.12)

        with self.voice(
            "{map}The coder takes four data bits at a time and maps them onto three ternary symbols. "
            "{count}Four bits have sixteen combinations; three ternary symbols have twenty-seven. "
            "{spare}The spare codes let the encoder choose, at every step, the pattern that keeps the average voltage at "
            "zero, so there's no DC drift — which matters, as we'll see in a moment."
        ) as v:
            self.play(LaggedStart(*[FadeIn(gr, shift=DOWN * 0.1) for gr in groups], lag_ratio=0.2), FadeIn(g_lbl), run_time=1.0)
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2),
                      LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in trip], lag_ratio=0.2), FadeIn(t_lbl), run_time=1.4)
            self.play(Create(wv), FadeIn(sep), run_time=1.4, rate_func=linear)
            v.wait_until("count")
            self.play(FadeIn(c16, shift=UP * 0.1), run_time=0.6)
            self.play(FadeIn(c27, shift=UP * 0.1), run_time=0.6)
            v.wait_until("spare")
            self.play(FadeIn(spare, shift=LEFT * 0.1), Indicate(VGroup(*g27[16:]), color=PINK, scale_factor=1.3), run_time=1.0)
            self.play(FadeIn(meter_ax), FadeIn(zero_tick), FadeIn(m_lbl), run_time=0.4)
            self.add(nd)
            self.play(rds_t.animate.set_value(len(rds_vals)), run_time=3.0, rate_func=linear)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the arithmetic
        eq = TeX(r"7.5\,\mathrm{MBd}", r"\times", r"\tfrac{4}{3}\ \tfrac{\text{bit}}{\text{symbol}}", r"=", r"10\ \mathrm{Mbit/s}", size=64)
        eq[0].set_color(APL)
        eq[4].set_color(APL)
        eq.move_to(UP * 0.6)
        sub = VGroup(T("7.5 million symbols per second", size=22, color=MUTED), T("·", size=22, color=MUTED),
                     T("one symbol every 133 ns", size=22, color=MUTED)).arrange(RIGHT, buff=0.2).next_to(eq, DOWN, buff=0.55)
        with self.voice(
            "{rate}Symbols are sent at 7.5 megabaud. Seven and a half million symbols per second, times four-thirds of "
            "a bit per symbol, is exactly ten megabits per second."
        ) as v:
            self.play(Write(eq[0]), run_time=0.8)
            self.play(FadeIn(sub[0]), FadeIn(sub[1]), FadeIn(sub[2]), run_time=0.6)
            self.play(Write(eq[1]), Write(eq[2]), run_time=1.0)
            self.play(Write(eq[3]), Write(eq[4]), run_time=0.9)
            box = SurroundingRectangle(eq[4], color=APL, buff=0.15, corner_radius=0.1)
            self.play(Create(box), run_time=0.5)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ spectrum vs cable loss
        ax = Axes(x_range=[0, 15, 2.5], y_range=[0, 1.05, 0.25], x_length=7.0, y_length=3.9,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-2.75, 0.0, 0])
        xl = tick_labels(ax, [0, 3.75, 7.5, 15], "x", texts=["0", "3.75", "7.5", "15 MHz"])
        y_lbl = T("power density", size=17, color=APL).next_to(ax.c2p(0, 1.05), UP, buff=0.12).align_to(ax, LEFT).shift(LEFT * 0.2)
        psd = ax.plot(lambda f: np.sinc(f / 7.5) ** 2, x_range=[0.02, 15, 0.05], color=APL, stroke_width=3.5)
        area = ax.get_area(psd, x_range=[0.02, 3.75], color=APL, opacity=0.3)
        nyq = DashedLine(ax.c2p(3.75, 0), ax.c2p(3.75, 1.05), dash_length=0.08, stroke_color=TEXT, stroke_width=2)
        nyq_lbl = VGroup(T("Nyquist", size=18, color=TEXT, weight=BOLD), T("3.75 MHz", size=16, color=MUTED)).arrange(DOWN, buff=0.04)
        nyq_lbl.next_to(nyq, UP, buff=0.08).shift(RIGHT * 0.85)
        energy = VGroup(T("≈ 77 %", size=20, color=WHITE_SOFT, weight=BOLD), T("of the power", size=16, color=WHITE_SOFT)).arrange(DOWN, buff=0.04).move_to(ax.c2p(1.55, 0.6))
        # insertion loss on a second scale (0..50 dB, drawn downward-growing curve)
        ax2 = Axes(x_range=[0, 15, 2.5], y_range=[0, 60, 10], x_length=7.0, y_length=3.9,
                   axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to(ax)
        il = ax2.plot(lambda f: 11.5 * np.sqrt(f) + 0.9 * f, x_range=[0.05, 15, 0.05], color=HAZARD, stroke_width=3.5)
        il_ticks = VGroup(*[T(f"{d} dB", size=16, color=HAZARD).next_to(ax2.c2p(15, d), RIGHT, buff=0.12) for d in (0, 20, 40, 60)])
        il_lbl = T("cable loss, 1 km (right scale)", size=18, color=HAZARD, weight=BOLD).next_to(ax2.c2p(15, 60), UP, buff=0.12).shift(LEFT * 1.2)
        r_axis = Line(ax2.c2p(15, 0), ax2.c2p(15, 60), stroke_color=HAZARD, stroke_width=2, stroke_opacity=0.6)
        mark = Dot(ax2.c2p(3.75, 11.5 * np.sqrt(3.75) + 0.9 * 3.75), radius=0.08, color=HAZARD)
        mark_lbl = T("≈ 25 dB", size=20, color=HAZARD, weight=BOLD).next_to(mark, RIGHT, buff=0.12).shift(DOWN * 0.15)

        eye_c = eye_traces(closed=True)
        eye_o = eye_traces(closed=False)

        def eye_group(traces, center, col, title):
            box = panel(3.0, 2.25).move_to(center)
            g = VGroup()
            for tr in traces:
                xs = np.linspace(-1.25, 1.25, len(tr))
                pts = np.stack([xs, 0.75 * np.clip(tr, -1.6, 1.6), np.zeros_like(xs)], 1) + center
                g.add(VMobject().set_points_as_corners(pts).set_stroke(col, 1.2, opacity=0.16))
            ttl = T(title, size=17, color=TEXT, weight=BOLD).next_to(box, UP, buff=0.1)
            return VGroup(box, g, ttl)

        eye1 = eye_group(eye_c, np.array([5.0, 1.15, 0]), HAZARD, "eye after 1 km of cable")
        eye2 = eye_group(eye_o, np.array([5.0, -1.95, 0]), APL, "after the equalizer")
        with self.voice(
            "{scr}Because the data is scrambled first, the spectrum stays smooth, whatever you send. "
            "{nyq}Most of the energy sits below the Nyquist frequency of 3.75 megahertz, {loss}where a kilometer of cable "
            "costs about 25 dB — {eq}a loss the receiver's equalizer can handle."
        ) as v:
            self.play(Create(ax), FadeIn(xl), FadeIn(y_lbl), run_time=0.8)
            self.play(Create(psd), run_time=1.4)
            v.wait_until("nyq")
            self.play(Create(nyq), FadeIn(nyq_lbl), FadeIn(area), FadeIn(energy), run_time=1.0)
            v.wait_until("loss")
            self.play(Create(r_axis), Create(il), FadeIn(il_ticks), FadeIn(il_lbl), run_time=1.2)
            self.play(FadeIn(mark, scale=0.5), FadeIn(mark_lbl), run_time=0.6)
            self.play(FadeIn(eye1), run_time=0.8)
            v.wait_until("eq")
            self.play(FadeIn(eye2), run_time=0.9)
        self.wait(0.6)
        self.clear(run_time=0.7)
