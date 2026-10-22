import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *


class SignallingLimits(APLScene):
    def construct(self):
        self.tag = corner_tag("05 · The wire is a waveguide")
        self.add(self.tag)

        jm = JourneyMap()
        with self.voice(
            "{map}We know what the wire does to a signal. Now, on to the transmitter: how should bits become voltages?"
        ) as v:
            self.play(FadeIn(jm), run_time=0.8)
            self.play(*jm.focus("tx"), run_time=0.8)
        self.clear(run_time=0.5)
        self.chapter(6, "From bits to symbols", "Nyquist, Shannon, and three voltage levels")

        # ------------------------------------------------------------ Nyquist
        nyq = name_card("Harry Nyquist", "1928 · Bell Labs", "Certain topics in telegraph transmission theory", BLUE)
        nyq.to_corner(UR, buff=0.4).shift(DOWN * 0.15)
        ax = Axes(x_range=[-4, 9, 1], y_range=[-1.4, 1.4, 1], x_length=12.0, y_length=3.2,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([0, -0.85, 0])
        one = ax.plot(lambda t: np.sinc(t), x_range=[-4, 9, 0.02], color=APL, stroke_width=4)
        zeros = VGroup(*[Dot(ax.c2p(k, 0), radius=0.06, color=PINK) for k in range(-4, 10) if k != 0])
        zl = T("zero at every other sampling instant", size=18, color=PINK).next_to(ax.c2p(4.5, 0), DOWN, buff=0.35)
        syms = [1, -1, 0, 1, 1, -1, 0, 1]
        cols = [APL, VIOLET, PINK, GOOD, POWER, BLUE, HAZARD, APL]
        pulses = VGroup(*[ax.plot(lambda t, k=k, a=a: a * np.sinc(t - k), x_range=[-4, 9, 0.02], color=cols[k], stroke_width=2).set_stroke(opacity=0.7)
                          for k, a in enumerate(syms)])
        total = ax.plot(lambda t: sum(a * np.sinc(t - k) for k, a in enumerate(syms)), x_range=[-4, 9, 0.02], color=WHITE_SOFT, stroke_width=4.5)
        samples = VGroup(*[VGroup(DashedLine(ax.c2p(k, -1.35), ax.c2p(k, 1.35), dash_length=0.05, stroke_color=DIM, stroke_width=1.5),
                                  Dot(ax.c2p(k, a), radius=0.08, color=cols[k])) for k, a in enumerate(syms)])
        rule = TeX(r"\text{symbol rate} \;\le\; 2B", size=46).move_to([-3.2, 2.05, 0])
        aplr = TeX(r"7.5\ \mathrm{MBd} \;\Rightarrow\; B \ge 3.75\ \mathrm{MHz}", size=40, color=APL).move_to([-3.2, 2.05, 0])
        with self.voice(
            "{q}Given a cable like this, how fast can we signal? Engineers at Bell Labs asked exactly that about telegraph "
            "and telephone lines in the 1920s. {nyq}In 1928, Harry Nyquist showed that a channel with a bandwidth of B hertz "
            "can carry at most two B independent pulses per second. {sinc}The ideal pulse is the sinc function. It rings — "
            "but its ringing passes through zero at exactly every other pulse's sampling instant. {train}Line them up, one "
            "symbol apart, sample at the right moments, and each sample sees only its own pulse. No interference, in a "
            "channel only half as wide as the symbol rate. {apl}For APL, 7.5 million symbols per second need at least 3.75 "
            "megahertz of bandwidth. That's the Nyquist frequency we keep meeting."
        ) as v:
            self.play(FadeIn(nyq, shift=LEFT * 0.2), run_time=0.7)
            v.wait_until("nyq")
            self.play(Write(rule), run_time=1.2)
            v.wait_until("sinc")
            self.play(Create(ax), run_time=0.6)
            self.play(Create(one), run_time=1.4)
            self.play(LaggedStart(*[FadeIn(z, scale=0.5) for z in zeros], lag_ratio=0.08), FadeIn(zl), run_time=1.2)
            v.wait_until("train")
            self.play(FadeOut(zl), FadeOut(zeros), FadeOut(one), run_time=0.4)
            self.play(LaggedStart(*[Create(p) for p in pulses], lag_ratio=0.25), run_time=2.6)
            self.play(Create(total), run_time=1.2)
            self.play(LaggedStart(*[FadeIn(s) for s in samples], lag_ratio=0.12), run_time=1.6)
            v.wait_until("apl")
            self.play(ReplacementTransform(rule, aplr), run_time=1.0)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ Hartley
        hart = name_card("Ralph Hartley", "1928 · Bell Labs", "Transmission of information", BLUE).to_corner(UR, buff=0.4).shift(DOWN * 0.15)
        ladders = VGroup()
        for i, (M, bits) in enumerate(((2, "1 bit"), (3, "1.58 bits"), (4, "2 bits"), (8, "3 bits"))):
            col = APL if M == 3 else TEXT
            levels = VGroup(*[Line(LEFT * 0.55, RIGHT * 0.55, stroke_color=col, stroke_width=4).shift(UP * (-1 + 2 * j / (M - 1)))
                              for j in range(M)])
            frame = Rectangle(width=1.5, height=2.5, stroke_color=PANEL_EDGE, stroke_width=1.5)
            top = TeX(r"M = %d" % M, size=34, color=col)
            bot = T(bits, size=20, color=col, weight=BOLD)
            g = VGroup(frame, levels)
            col_g = VGroup(top, g, bot).arrange(DOWN, buff=0.25)
            ladders.add(col_g)
        ladders.arrange(RIGHT, buff=0.7).move_to([-2.7, -0.45, 0])
        hrule = TeX(r"\text{bits per symbol} = \log_2 M", size=40).move_to([4.3, 0.5, 0])
        hrate = TeX(r"R = 2B\,\log_2 M", size=46, color=BLUE).move_to([4.3, -0.8, 0])
        with self.voice(
            "{hart}The same year, Ralph Hartley, also at Bell Labs, added the second dimension. If each pulse can take one "
            "of M distinguishable levels, it carries log two of M bits. {ex}Two levels: one bit. Four levels: two bits. "
            "Three levels: about one and a half. {rate}So the bit rate is two B times log two M — and apparently there's no "
            "limit, if you just use enough levels."
        ) as v:
            self.play(FadeIn(hart, shift=LEFT * 0.2), run_time=0.7)
            self.play(Write(hrule), run_time=1.1)
            v.wait_until("ex")
            self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.15) for l in ladders], lag_ratio=0.3), run_time=2.2)
            v.wait_until("rate")
            self.play(Write(hrate), run_time=1.2)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ Shannon
        sha = name_card("Claude Shannon", "1948 · Bell Labs", "A mathematical theory of communication", BLUE).to_corner(UR, buff=0.4).shift(DOWN * 0.15)
        cap = TeX(r"C", r"=", r"B", r"\,\log_2\!\left(1 + \frac{S}{N}\right)", size=60).move_to([-2.4, 1.55, 0])
        cap[0].set_color(GOOD)
        sigma = 0.11
        M_t = ValueTracker(2)
        box_c = np.array([-2.6, -1.25, 0])

        def noisy_levels():
            M = int(round(M_t.get_value()))
            g = VGroup(Rectangle(width=4.2, height=3.0, stroke_color=PANEL_EDGE, stroke_width=1.5).move_to(box_c))
            ys = [-1.1 + 2.2 * j / (M - 1) for j in range(M)]
            gap = 2.2 / (M - 1)
            bad = gap < 5 * sigma * 1.1
            for y in ys:
                for k, w in enumerate((3.0, 2.0, 1.0)):
                    g.add(Rectangle(width=3.6, height=2 * w * sigma * 1.1, fill_color=DANGER if bad else APL, fill_opacity=0.12,
                                    stroke_width=0).move_to(box_c + UP * y))
                g.add(Line(box_c + UP * y + LEFT * 1.8, box_c + UP * y + RIGHT * 1.8, stroke_color=WHITE_SOFT, stroke_width=2.5))
            lab = T(f"M = {M}", size=22, color=DANGER if bad else APL, weight=BOLD).next_to(g[0], UP, buff=0.12)
            g.add(lab)
            return g

        nl = always_redraw(noisy_levels)
        noise_lbl = T("same noise, more levels", size=18, color=MUTED).next_to(box_c + DOWN * 1.5, DOWN, buff=0.15)
        knob1 = VGroup(Circle(0.45, stroke_color=APL, stroke_width=3), Line(ORIGIN, UP * 0.38, stroke_color=APL, stroke_width=4),
                       T("symbol rate", size=20, color=APL, weight=BOLD), T("costs bandwidth → cable loss", size=16, color=MUTED))
        knob1[2].next_to(knob1[0], DOWN, buff=0.15)
        knob1[3].next_to(knob1[2], DOWN, buff=0.06)
        knob2 = VGroup(Circle(0.45, stroke_color=VIOLET, stroke_width=3), Line(ORIGIN, UP * 0.38, stroke_color=VIOLET, stroke_width=4).rotate(-0.8, about_point=ORIGIN),
                       T("levels per symbol", size=20, color=VIOLET, weight=BOLD), T("costs signal-to-noise ratio", size=16, color=MUTED))
        knob2[2].next_to(knob2[0], DOWN, buff=0.15)
        knob2[3].next_to(knob2[2], DOWN, buff=0.06)
        knobs = VGroup(knob1, knob2).arrange(RIGHT, buff=1.0).move_to([3.6, -1.35, 0])
        with self.voice(
            "{sh}The catch is noise: levels packed too closely can no longer be told apart. {cap}In 1948, Claude Shannon "
            "settled the question for good. The capacity of a channel is C equals B times log two of one plus the "
            "signal-to-noise ratio. {meaning}Below that rate, error-free communication is possible, with clever enough "
            "coding. Above it, it's impossible. {knobs}So the designer has two knobs. The symbol rate costs bandwidth — and "
            "on our cable, bandwidth means loss. The number of levels costs signal-to-noise ratio. {next}Let's see how "
            "10BASE-T1L sets those two knobs."
        ) as v:
            self.add(nl)
            self.play(FadeIn(nl), FadeIn(noise_lbl), run_time=0.6)
            for M in (3, 4, 6, 8):
                self.play(M_t.animate.set_value(M), run_time=0.6)
                self.wait(0.15)
            v.wait_until("cap")
            self.play(FadeIn(sha, shift=LEFT * 0.2), run_time=0.6)
            self.play(Write(cap), run_time=1.8)
            v.wait_until("meaning")
            self.play(Indicate(cap[0], color=GOOD, scale_factor=1.3), run_time=0.9)
            self.play(M_t.animate.set_value(3), run_time=0.6)
            v.wait_until("knobs")
            self.play(FadeIn(knob1, shift=UP * 0.1), run_time=0.7)
            self.play(knob1[1].animate.rotate(-1.2, about_point=knob1[0].get_center()), run_time=0.7)
            self.play(FadeIn(knob2, shift=UP * 0.1), run_time=0.7)
            self.play(knob2[1].animate.rotate(1.0, about_point=knob2[0].get_center()), run_time=0.7)
        self.remove(nl)
        self.clear(run_time=0.6)
