import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.props import CAN_POINTS, can_curve, rate_length_chart
from apl.style import *
from apl.widgets import *

CAN_L_COL = "#C2410C"
T_NODE = 150e-9   # transceiver + controller delay, one way, per node [s]
V_NS = 5e-9       # cable delay [s/m]
SP = 0.75         # sample point


class CANLength(APLScene):
    def construct(self):
        self.tag = corner_tag("03 · Our reference: CAN bus", color=CAN)
        self.add(self.tag)

        # ------------------------------------------------------------ geometry
        xa, xb, yb = -5.2, 5.2, 1.55
        bus = VGroup(Line([xa, yb + 0.12, 0], [xb, yb + 0.12, 0], stroke_color=CAN, stroke_width=4),
                     Line([xa, yb - 0.12, 0], [xb, yb - 0.12, 0], stroke_color=CAN_L_COL, stroke_width=4))
        na = device("Node A", "cpu", CAN, width=1.5, height=1.1, label_size=18).move_to([xa - 0.2, yb + 1.15, 0])
        nb = device("Node B", "cpu", CAN, width=1.5, height=1.1, label_size=18).move_to([xb + 0.2, yb + 1.15, 0])
        sa = Line(na.get_bottom(), [na.get_x(), yb + 0.12, 0], stroke_color=CAN, stroke_width=2.5)
        sb = Line(nb.get_bottom(), [nb.get_x(), yb + 0.12, 0], stroke_color=CAN, stroke_width=2.5)
        length = ValueTracker(40)
        dim = always_redraw(lambda: VGroup(
            DoubleArrow([xa, yb - 0.55, 0], [xb, yb - 0.55, 0], buff=0, stroke_color=MUTED, stroke_width=2, tip_length=0.15),
            T(f"L = {length.get_value():.0f} m", size=24, color=TEXT, weight=BOLD).move_to([0, yb - 0.85, 0])))

        # bit-time bar
        bx0, bx1, by = -5.2, 5.2, -1.65
        bit_rate = ValueTracker(1e6)
        bar = Rectangle(width=bx1 - bx0, height=0.55, stroke_color=CAN, stroke_width=2, fill_color=CAN, fill_opacity=0.08)
        bar.move_to([(bx0 + bx1) / 2, by, 0])
        sp_x = bx0 + SP * (bx1 - bx0)
        sp_line = DashedLine([sp_x, by - 0.55, 0], [sp_x, by + 0.55, 0], dash_length=0.07, stroke_color=TEXT, stroke_width=2)
        sp_lbl = T("sample point", size=18, color=TEXT).next_to(sp_line, UP, buff=0.08)
        bar_lbl = always_redraw(lambda: T(f"one bit at {bit_rate.get_value() / 1e3:.0f} kbit/s = {1e6 / bit_rate.get_value():.0f} µs"
                                          if bit_rate.get_value() < 1e6 - 1 else "one bit at 1 Mbit/s = 1 µs",
                                          size=22, color=CAN, weight=BOLD).next_to(bar, DOWN, buff=0.25))

        def rt_time():
            return 2 * (length.get_value() * V_NS + T_NODE)

        def rt_frac():
            return rt_time() * bit_rate.get_value()

        playhead = ValueTracker(0.0)  # fraction of the round trip completed

        def head_mob():
            f = playhead.get_value() * rt_frac()
            x = bx0 + min(f, 1.18) * (bx1 - bx0)
            ok = rt_frac() <= SP
            col = GOOD if ok else DANGER
            fill = Rectangle(width=max(1e-3, x - bx0), height=0.55, stroke_width=0, fill_color=col, fill_opacity=0.45)
            fill.move_to([bx0 + (x - bx0) / 2, by, 0])
            return fill

        head = always_redraw(head_mob)

        def pulse_pos():
            p = playhead.get_value()
            if p <= 0.5:
                x = xa + (xb - xa) * (p / 0.5)
            else:
                x = xb - (xb - xa) * ((p - 0.5) / 0.5)
            return np.array([x, yb, 0])

        pulse = always_redraw(lambda: packet(CAN, 0.1, 4).move_to(pulse_pos()))

        def result_mob():
            ok = rt_frac() <= SP
            ns = rt_time() * 1e9
            txt = f"round trip ≈ {ns:,.0f} ns"
            g = VGroup(T(txt, size=22, color=TEXT), (check(GOOD, 0.32, 5) if ok else cross(DANGER, 0.3, 5)))
            g.arrange(RIGHT, buff=0.2).move_to([-2.4, by + 0.95, 0])
            return g

        with self.voice(
            "{price}But arbitration has a price, and it is paid in meters. {see}For the wired-AND to work, a dominant "
            "bit from the far end of the bus must reach every node — and the transmitter must read back the result — "
            "before the bit is sampled."
        ) as v:
            self.play(FadeIn(na), FadeIn(nb), Create(bus), Create(sa), Create(sb), FadeIn(dim), run_time=1.2)
            v.wait_until("see")
            self.play(FadeIn(bar), Create(sp_line), FadeIn(sp_lbl), FadeIn(bar_lbl), run_time=1.0)
            self.add(head, pulse)
            self.play(playhead.animate.set_value(1.0), run_time=3.0, rate_func=linear)
            res = always_redraw(result_mob)
            self.play(FadeIn(res), run_time=0.5)

        with self.voice(
            "{speed}Signals travel about five nanoseconds per meter. {fit}So the round trip to the far end and back, plus "
            "the transceiver delays, has to fit inside a fraction of one bit. {mbit}At one megabit per second, a bit "
            "lasts just one microsecond, which limits the bus to about forty meters."
        ) as v:
            speed_tag = pill("≈ 5 ns per meter", CAN, size=22).move_to([0, yb + 1.15, 0])
            self.play(FadeIn(speed_tag), run_time=0.6)
            v.wait_until("fit")
            self.play(playhead.animate.set_value(0.0), run_time=0.3)
            self.play(length.animate.set_value(200), run_time=1.5)
            self.play(playhead.animate.set_value(1.0), run_time=2.5, rate_func=linear)
            v.wait_until("mbit")
            self.play(playhead.animate.set_value(0.0), run_time=0.3)
            self.play(length.animate.set_value(40), run_time=1.0)
            self.play(playhead.animate.set_value(1.0), run_time=1.5, rate_func=linear)

        with self.voice(
            "{slow}Want two hundred meters? Then slow down, so that every bit lasts long enough."
        ) as v:
            self.play(playhead.animate.set_value(0.0), run_time=0.3)
            self.play(length.animate.set_value(200), run_time=1.0)
            self.play(bit_rate.animate.set_value(250e3), run_time=1.5)
            self.play(playhead.animate.set_value(1.0), run_time=2.0, rate_func=linear)

        self.clear(run_time=0.6)

        # ------------------------------------------------------------ log-log chart
        ax, deco = rate_length_chart()
        chart = VGroup(ax, deco).move_to(LEFT * 1.0 + DOWN * 0.2)
        line, pts = can_curve(ax)
        lbls = VGroup()
        for (L, R), d in zip(CAN_POINTS, pts):
            txt = f"{R / 1e3:.0f} kbit/s · {L:g} m" if R < 1e6 else "1 Mbit/s · 40 m"
            lbls.add(T(txt, size=15, color=CAN).next_to(d, DL if R >= 1e6 else UR, buff=0.08))
        legend = VGroup(Line(LEFT * 0.3, RIGHT * 0.3, stroke_color=CAN, stroke_width=4), T("classic CAN (typical max.)", size=18, color=CAN))
        legend.arrange(RIGHT, buff=0.15).next_to(ax, UP, buff=0.25).align_to(ax, RIGHT)
        with self.voice(
            "{chart}Plot the usual limits on logarithmic axes. {k5}Five hundred meters? 125 kilobits per second. "
            "{k1}A kilometer? About fifty. {const}Bit rate times length is roughly constant: CAN trades speed for distance."
        ) as v:
            self.play(Create(ax), FadeIn(deco), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in pts], lag_ratio=0.15), FadeIn(legend), run_time=1.0)
            self.play(FadeIn(lbls[0]), run_time=0.4)
            v.wait_until("k5")
            self.play(Flash(pts[3], color=CAN), FadeIn(lbls[3]), run_time=0.7)
            v.wait_until("k1")
            self.play(Flash(pts[4], color=CAN), FadeIn(lbls[4]), run_time=0.7)
            v.wait_until("const")
            self.play(Create(line), FadeIn(lbls[1]), FadeIn(lbls[2]), FadeIn(lbls[5]), run_time=1.3)
            formula = VGroup(T("bit rate × length", size=26, color=CAN, weight=BOLD), T("≈ 50 Mbit/s · m", size=26, color=CAN, weight=BOLD)).arrange(DOWN, buff=0.08)
            formula.move_to(ax.c2p(3.25, 6.55))
            self.play(FadeIn(formula, shift=UP * 0.1), run_time=0.7)

        # CAN FD note
        fd_arrow = Arrow(ax.c2p(np.log10(40), 6.0), ax.c2p(np.log10(40), 6.72), buff=0.05, stroke_color=PINK, stroke_width=4,
                         max_tip_length_to_length_ratio=0.25)
        fd_lbl = VGroup(T("CAN FD data phase", size=18, color=PINK, weight=BOLD), T("2 – 8 Mbit/s", size=16, color=PINK)).arrange(DOWN, buff=0.04)
        fd_lbl.next_to(fd_arrow, UP, buff=0.08)
        # mini frame: arbitration slow, data fast
        mf = VGroup()
        widths = [(1.6, CAN, "arbitration"), (1.35, PINK, "data, fast"), (0.6, CAN, "ACK")]
        x = 0
        for w, c, nm in widths:
            r = Rectangle(width=w, height=0.38, fill_color=c, fill_opacity=0.75, stroke_width=0).move_to([x + w / 2, 0, 0])
            mf.add(VGroup(r, T(nm, size=14, color=BG, weight=BOLD).move_to(r)))
            x += w
        mf_lbl = T("CAN FD frame", size=16, color=MUTED).next_to(mf, LEFT, buff=0.15)
        mini = VGroup(mf_lbl, mf).to_corner(DR, buff=0.55).shift(UP * 0.1)
        with self.voice(
            "{fd}That's also why CAN FD only accelerates the data phase. Once arbitration is over and a single node is "
            "talking, the round-trip constraint disappears."
        ) as v:
            self.play(GrowArrow(fd_arrow), FadeIn(fd_lbl, shift=RIGHT * 0.1), run_time=0.9)
            self.play(FadeIn(mini, shift=UP * 0.1), run_time=0.8)
        self.wait(0.5)
        self.clear(run_time=0.7)
