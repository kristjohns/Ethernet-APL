import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *

CAN_L_COL = "#C2410C"  # darker amber/orange for CAN_L


def switch_sym(color=TEXT, length=0.6, width=3):
    a = Dot(radius=0.05, color=color)
    b = Dot(radius=0.05, color=color).shift(DOWN * length)
    lever = Line(a.get_center(), a.get_center() + DOWN * length, stroke_color=color, stroke_width=width)
    lever.rotate(0.55, about_point=a.get_center())
    g = VGroup(a, b, lever)
    g.lever = lever
    g.pivot = a
    return g


def can_bus(x0=-6.2, x1=6.2, y=0.0, gap=0.5, with_terms=True):
    h = Line([x0, y + gap / 2, 0], [x1, y + gap / 2, 0], stroke_color=CAN, stroke_width=4)
    l = Line([x0, y - gap / 2, 0], [x1, y - gap / 2, 0], stroke_color=CAN_L_COL, stroke_width=4)
    g = VGroup(h, l)
    terms = VGroup()
    if with_terms:
        for x in (x0, x1):
            r = resistor(gap, MUTED, width=2.5, amp=0.08).rotate(PI / 2).move_to([x, y, 0])
            lab = T("120 Ω", size=18, color=MUTED).next_to(r, LEFT if x < 0 else RIGHT, buff=0.12)
            terms.add(VGroup(r, lab))
    return g, terms


class CANPhysical(APLScene):
    def construct(self):
        self.chapter(3, "Our reference: CAN bus", "A party line on one twisted pair", color=CAN)

        # ------------------------------------------------------------ intro
        badge = VGroup(T("1986", size=54, color=CAN, weight=BOLD), T("Bosch · Controller Area Network", size=24, color=MUTED)).arrange(DOWN, buff=0.1)
        badge.move_to(UP * 1.6)
        tiles = VGroup()
        for ic, nm in [("car", "vehicles"), ("tractor", "tractors"), ("robot", "robots"), ("heartbeat", "medical")]:
            b = panel(2.2, 1.7)
            i = icon(ic, CAN, 0.75).move_to(b.get_center() + UP * 0.2)
            t = T(nm, size=20, color=TEXT).next_to(i, DOWN, buff=0.18)
            tiles.add(VGroup(b, i, t))
        tiles.arrange(RIGHT, buff=0.35).move_to(DOWN * 1.2)
        with self.voice(
            "Before we open up APL, let's set up our reference. {can}CAN, the Controller Area Network, was presented "
            "by Bosch in 1986 to tame the growing tangle of wiring in cars. {apps}Today it's everywhere: vehicles, "
            "tractors, robots, medical devices."
        ) as v:
            v.wait_until("can")
            self.play(FadeIn(badge, shift=DOWN * 0.2), run_time=0.9)
            v.wait_until("apps")
            self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in tiles], lag_ratio=0.3), run_time=1.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the bus
        bus, terms = can_bus(y=-0.6)
        hl = T("CAN_H", size=22, color=CAN, weight=BOLD).next_to(bus[0], UP, buff=0.08).align_to(bus[0], LEFT).shift(RIGHT * 0.5)
        ll = T("CAN_L", size=22, color=CAN_L_COL, weight=BOLD).next_to(bus[1], DOWN, buff=0.08).align_to(bus[1], LEFT).shift(RIGHT * 0.5)
        nodes = VGroup()
        stubs = VGroup()
        for i, nm in enumerate(["Engine", "Brakes", "Gearbox", "Dashboard", "Diagnosis"]):
            x = -4.4 + 2.2 * i
            d = device(nm, "cpu", CAN, width=1.55, height=1.15, label_size=18).move_to([x, 1.55, 0])
            nodes.add(d)
            stubs.add(VGroup(Line([x - 0.12, d.get_bottom()[1], 0], [x - 0.12, bus[0].get_y(), 0]),
                             Line([x + 0.12, d.get_bottom()[1], 0], [x + 0.12, bus[1].get_y(), 0])).set_stroke(CAN, 2.2))
            stubs[-1][1].set_stroke(CAN_L_COL)
        with self.voice(
            "{bus}Physically, CAN is one twisted pair, called CAN high and CAN low, running past every node. "
            "{term}A 120-ohm resistor at each end matches the cable's characteristic impedance, so signals don't reflect."
        ) as v:
            self.play(Create(bus[0]), Create(bus[1]), FadeIn(hl), FadeIn(ll), run_time=1.0)
            self.play(LaggedStart(*[AnimationGroup(FadeIn(n, shift=DOWN * 0.2), Create(s)) for n, s in zip(nodes, stubs)], lag_ratio=0.2), run_time=1.6)
            v.wait_until("term")
            self.play(LaggedStart(*[FadeIn(t, scale=0.8) for t in terms], lag_ratio=0.3), run_time=0.8)
            for _ in range(2):
                pulse = VGroup(packet(CAN, 0.08, 4).move_to(bus[0].get_start()), packet(CAN_L_COL, 0.08, 4).move_to(bus[1].get_start()))
                self.add(pulse)
                self.play(pulse.animate.shift(RIGHT * (bus[0].get_length())), run_time=1.0, rate_func=linear)
                self.play(FadeOut(pulse, scale=0.3), Indicate(terms[1][0], color=CAN, scale_factor=1.15), run_time=0.4)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ transceiver output stage
        vcc = VGroup(Line(LEFT * 0.3, RIGHT * 0.3), T("5 V", size=20, color=POWER)).arrange(UP, buff=0.08).set_color(POWER)
        vcc.move_to([-6.0, 2.55, 0])
        s1 = switch_sym(TEXT).move_to([-6.0, 1.75, 0])
        s2 = switch_sym(TEXT).move_to([-6.0, -1.75, 0])
        gnd = ground(TEXT).move_to([-6.0, -2.75, 0])
        yh, yl = 0.85, -0.85
        xr = -2.7
        wires = VGroup(
            Line(vcc[0].get_center(), s1.pivot.get_center()),
            Line(s1[1].get_center(), [-6.0, yh, 0]),
            Line([-6.0, yl, 0], s2.pivot.get_center()),
            Line(s2[1].get_center(), gnd.get_top()),
        ).set_stroke(TEXT, 2.5)
        h_line = Line([-6.0, yh, 0], [xr, yh, 0], stroke_color=CAN, stroke_width=4)
        l_line = Line([-6.0, yl, 0], [xr, yl, 0], stroke_color=CAN_L_COL, stroke_width=4)
        rt = resistor(abs(yh - yl), MUTED, amp=0.1).rotate(PI / 2).move_to([xr, 0, 0])
        rt_lbl = VGroup(T("bus load", size=17, color=MUTED), T("120 Ω ∥ 120 Ω", size=17, color=MUTED)).arrange(DOWN, buff=0.05).next_to(rt, RIGHT, buff=0.15)
        hlab = T("CAN_H", size=20, color=CAN, weight=BOLD).next_to(h_line.get_start(), UR, buff=0.1).shift(RIGHT * 0.25)
        llab = T("CAN_L", size=20, color=CAN_L_COL, weight=BOLD).next_to(l_line.get_start(), DR, buff=0.1).shift(RIGHT * 0.25)
        stage_title = T("transceiver output stage", size=20, color=MUTED).move_to([-4.4, 3.1, 0])
        vh = ValueTracker(2.5)
        vl = ValueTracker(2.5)
        vh_num = always_redraw(lambda: T(f"{vh.get_value():.1f} V", size=24, color=CAN, weight=BOLD).next_to([xr - 0.25, yh, 0], UL, buff=0.1))
        vl_num = always_redraw(lambda: T(f"{vl.get_value():.1f} V", size=24, color=CAN_L_COL, weight=BOLD).next_to([xr - 0.25, yl, 0], DL, buff=0.1))
        stage = VGroup(vcc, s1, s2, gnd, wires, h_line, l_line, rt, rt_lbl, hlab, llab, stage_title)

        # plots
        bits = [1, 0, 0, 1, 0, 1, 1, 0]  # 1 = recessive, 0 = dominant
        axv = Axes(x_range=[0, 8, 1], y_range=[0, 5, 1], x_length=6.0, y_length=2.6,
                   axis_config={"stroke_color": DIM, "include_tip": False},
                   x_axis_config={"include_ticks": False}).move_to([3.25, 1.1, 0])
        v_lbl = VGroup(tick_labels(axv, [0, 1, 2, 3, 4, 5], "y", "{:g}", size=16),
                       T("volts", size=16, color=MUTED).rotate(PI / 2).next_to(axv.y_axis, LEFT, buff=0.45))
        axd = Axes(x_range=[0, 8, 1], y_range=[-0.5, 3, 1], x_length=6.0, y_length=1.5,
                   axis_config={"stroke_color": DIM, "include_tip": False},
                   x_axis_config={"include_ticks": False}).next_to(axv, DOWN, buff=0.6)
        d_ticks = tick_labels(axd, [0, 2], "y", "{:g} V", size=16)
        d_lbl = T("V_diff = CAN_H − CAN_L", size=18, color=TEXT).next_to(axd, UP, buff=0.04).align_to(axd, LEFT).shift(RIGHT * 0.3)
        noise = ValueTracker(0.0)

        def lvl(t, which):
            i = int(np.clip(np.floor(t), 0, 7))
            frac = t - i
            cur = bits[i]
            prev = bits[i - 1] if i > 0 else 1
            def v_of(b):
                return (2.5 if b else (3.5 if which == "h" else 1.5))
            a, b = v_of(prev), v_of(cur)
            edge = 0.08
            return b if frac > edge else a + (b - a) * frac / edge

        def n_of(t):
            return 0.75 * np.exp(-((t - 4.6) / 1.1) ** 2) * np.sin(2 * np.pi * 2.6 * t) + 0.25 * np.exp(-((t - 4.6) / 1.1) ** 2) * np.sin(2 * np.pi * 7.1 * t)

        ts = np.linspace(0, 7.999, 500)
        progress = ValueTracker(0.0)

        def trace(which, col):
            def f():
                tmax = progress.get_value() * 8
                pts = [axv.c2p(t, lvl(t, which) + noise.get_value() * n_of(t)) for t in ts if t <= tmax]
                if len(pts) < 2:
                    pts = [axv.c2p(0, 2.5), axv.c2p(0.001, 2.5)]
                return VMobject().set_points_as_corners(pts).set_stroke(col, 3.5)
            return always_redraw(f)

        tr_h = trace("h", CAN)
        tr_l = trace("l", CAN_L_COL)

        def diff_trace():
            tmax = progress.get_value() * 8
            pts = [axd.c2p(t, lvl(t, "h") - lvl(t, "l")) for t in ts if t <= tmax]
            if len(pts) < 2:
                pts = [axd.c2p(0, 0), axd.c2p(0.001, 0)]
            return VMobject().set_points_as_corners(pts).set_stroke(TEXT, 3.5)

        tr_d = always_redraw(diff_trace)
        bit_lbls = VGroup()
        for i, b in enumerate(bits):
            c = MUTED if b else CAN
            bit_lbls.add(VGroup(M("1" if b else "0", size=24, color=c, weight=BOLD), T("rec" if b else "dom", size=14, color=c)).arrange(DOWN, buff=0.03).move_to(axv.c2p(i + 0.5, 5.65)))
        th_lines = VGroup(
            DashedLine(axd.c2p(0, 0.5), axd.c2p(8, 0.5), dash_length=0.06, stroke_color=MUTED, stroke_width=1.5),
            DashedLine(axd.c2p(0, 0.9), axd.c2p(8, 0.9), dash_length=0.06, stroke_color=CAN, stroke_width=1.5),
        )
        th_lbls = VGroup(T("0.5 V", size=14, color=MUTED).next_to(th_lines[0], RIGHT, buff=0.08),
                         T("0.9 V", size=14, color=CAN).next_to(th_lines[1], RIGHT, buff=0.08)).shift(UP * 0.0)
        th_lbls[0].shift(DOWN * 0.08)
        th_lbls[1].shift(UP * 0.08)

        # current dots through the closed stage
        loop = VMobject().set_points_as_corners([vcc[0].get_center(), [-6.0, yh, 0], [xr, yh, 0], [xr, yl, 0], [-6.0, yl, 0], gnd.get_top()])
        cur_dots = VGroup(*[packet(POWER, 0.045, 3) for _ in range(9)])
        cflow = {"a": 0.0}

        def cur_upd(g, dt):
            cflow["a"] = (cflow["a"] + dt * 0.35) % 1.0
            for i, d in enumerate(g):
                d.move_to(loop.point_from_proportion((cflow["a"] + i / len(g)) % 1.0))

        cur_dots.add_updater(cur_upd)

        def set_switches(closed):
            ang = -0.55 if closed else 0.55
            return [s1.lever.animate.rotate(ang, about_point=s1.pivot.get_center()),
                    s2.lever.animate.rotate(ang, about_point=s2.pivot.get_center())]

        with self.voice(
            "{states}CAN has two bus states. {rec}In the recessive state, nobody drives the bus: the termination "
            "resistors pull both wires to about two and a half volts, and the difference is zero. "
            "{dom}To send a dominant bit, a transceiver pushes CAN high up to about three and a half volts and pulls "
            "CAN low down to one and a half — a difference of about two volts."
        ) as v:
            self.play(FadeIn(stage_title), Create(wires), FadeIn(vcc), FadeIn(s1), FadeIn(s2), FadeIn(gnd), run_time=1.0)
            self.play(Create(h_line), Create(l_line), FadeIn(rt), FadeIn(rt_lbl), FadeIn(hlab), FadeIn(llab), run_time=0.9)
            v.wait_until("rec")
            self.add(vh_num, vl_num)
            rec_tag = pill("recessive · drivers off", MUTED, size=20).move_to([-4.0, -3.35, 0])
            self.play(FadeIn(rec_tag), run_time=0.5)
            self.play(Create(axv), FadeIn(v_lbl), run_time=0.8)
            self.add(tr_h, tr_l)
            self.play(progress.animate.set_value(1 / 8), run_time=0.8, rate_func=linear)
            v.wait_until("dom")
            dom_tag = pill("dominant · drivers on", CAN, size=20).move_to(rec_tag)
            self.play(*set_switches(True), FadeOut(rec_tag), FadeIn(dom_tag), vh.animate.set_value(3.5), vl.animate.set_value(1.5), run_time=0.7)
            self.add(cur_dots)
            self.play(progress.animate.set_value(3 / 8), run_time=1.2, rate_func=linear)
            self.play(*set_switches(False), vh.animate.set_value(2.5), vl.animate.set_value(2.5),
                      FadeOut(dom_tag), FadeIn(rec_tag), FadeOut(cur_dots), run_time=0.5)
            cur_dots.clear_updaters()
            self.play(progress.animate.set_value(4 / 8), run_time=0.6, rate_func=linear)
            self.play(FadeIn(bit_lbls[:4]), run_time=0.5)

        # ------------------------------------------------------------ differential reception
        dp_body = RoundedRectangle(width=1.8, height=1.2, corner_radius=0.15, fill_color=PANEL, fill_opacity=1, stroke_color=TEXT, stroke_width=2.2)
        dp_head = RoundedRectangle(width=2.15, height=0.55, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=TEXT, stroke_width=2.2).next_to(dp_body, UP, buff=0.12)
        dp_disp = M("Δp = 0.20 bar", size=16, color=GOOD).move_to(dp_head)
        diaphragm = VMobject().set_points_smoothly([dp_body.get_top() + DOWN * 0.15, dp_body.get_center() + RIGHT * 0.06,
                                                    dp_body.get_bottom() + UP * 0.15]).set_stroke(MUTED, 2.5)
        ph = Line(dp_body.get_bottom() + LEFT * 0.45, dp_body.get_bottom() + LEFT * 0.45 + DOWN * 0.7, stroke_color=TEXT, stroke_width=3)
        pl = Line(dp_body.get_bottom() + RIGHT * 0.45, dp_body.get_bottom() + RIGHT * 0.45 + DOWN * 0.7, stroke_color=TEXT, stroke_width=3)
        ph_l = T("H", size=18, color=TEXT, weight=BOLD).next_to(ph, LEFT, buff=0.08)
        pl_l = T("L", size=18, color=TEXT, weight=BOLD).next_to(pl, RIGHT, buff=0.08)
        static = ValueTracker(100.0)
        p_h = always_redraw(lambda: T(f"{static.get_value() + 0.2:.1f} bar", size=18, color=CAN).next_to(ph, DOWN, buff=0.1).shift(LEFT * 0.25))
        p_l = always_redraw(lambda: T(f"{static.get_value():.1f} bar", size=18, color=CAN_L_COL).next_to(pl, DOWN, buff=0.1).shift(RIGHT * 0.25))
        dp = VGroup(dp_body, diaphragm, dp_head, dp_disp, ph, pl, ph_l, pl_l).move_to([-4.3, 0.2, 0])
        dp_title = T("differential-pressure transmitter", size=20, color=MUTED).next_to(dp, UP, buff=0.3)
        dp_note = T("static pressure is rejected", size=20, color=GOOD).move_to([-4.3, -2.65, 0])

        with self.voice(
            "{diff}The receiver looks only at the difference. {dp}It's exactly like a differential-pressure transmitter, "
            "which ignores the static line pressure: {noise}interference that couples equally into both wires simply "
            "cancels out. {apl}APL, as we'll see, uses the very same trick."
        ) as v:
            self.play(Create(axd), FadeIn(d_lbl), FadeIn(d_ticks), run_time=0.7)
            self.add(tr_d)
            self.play(progress.animate.set_value(1.0), FadeIn(bit_lbls[4:]), run_time=2.0, rate_func=linear)
            self.play(FadeIn(th_lines), FadeIn(th_lbls), run_time=0.5)
            v.wait_until("dp")
            self.remove(vh_num, vl_num)
            self.play(FadeOut(stage), FadeOut(rec_tag), run_time=0.5)
            self.play(FadeIn(dp, shift=UP * 0.2), FadeIn(dp_title), run_time=0.8)
            self.add(p_h, p_l)
            v.wait_until("noise")
            self.play(noise.animate.set_value(1.0), static.animate.set_value(160.0), run_time=1.6)
            self.play(FadeIn(dp_note, shift=UP * 0.1), Indicate(tr_d, color=GOOD, scale_factor=1.0), run_time=1.0)
            cm = T("common-mode noise: gone", size=20, color=GOOD).next_to(axd, DOWN, buff=0.25)
            self.play(FadeIn(cm, shift=UP * 0.1), run_time=0.6)
            v.wait_until("apl")
            self.play(noise.animate.set_value(0.0), static.animate.set_value(100.0), run_time=1.2)
        self.wait(0.4)
        self.clear(run_time=0.7)
