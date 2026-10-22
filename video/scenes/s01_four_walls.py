import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *
from apl.props import brick_wall, four_walls_layout


def fsk_current(bits, t_bit, i_dc=12.0, amp=0.5, samples_per_bit=120):
    ts, ys = [], []
    phase = 0.0
    t = 0.0
    dt = t_bit / samples_per_bit
    for b in bits:
        f = 1200.0 if b else 2200.0
        for _ in range(samples_per_bit):
            ts.append(t)
            ys.append(i_dc + amp * np.sin(phase))
            phase += 2 * np.pi * f * dt
            t += dt
    ts.append(t)
    ys.append(i_dc + amp * np.sin(phase))
    return np.array(ts), np.array(ys)


class FourWalls(APLScene):
    def construct(self):
        np.random.seed(7)
        self.chapter(1, "The last kilometer", "Why Ethernet stopped at the control room")

        # ------------------------------------------------------------ 4–20 mA loop
        ctrl = RoundedRectangle(width=2.6, height=3.0, corner_radius=0.16, fill_color=PANEL, fill_opacity=1,
                                stroke_color=MUTED, stroke_width=2.2).move_to(LEFT * 4.6 + DOWN * 0.4)
        ctrl_lbl = T("Controller input", size=22, color=MUTED, weight=BOLD).next_to(ctrl, UP, buff=0.15)
        src = dc_source(0.3, POWER).move_to(ctrl.get_center() + UP * 0.6 + LEFT * 0.35)
        src_lbl = T("24 V", size=20, color=POWER).next_to(src, LEFT, buff=0.12)
        res = resistor(1.0, TEXT, label=None).rotate(PI / 2).move_to(ctrl.get_center() + DOWN * 0.55 + LEFT * 0.35)
        res_lbl = T("250 Ω", size=20, color=TEXT).next_to(res, LEFT, buff=0.12)
        tx_dev = device("Transmitter", "gauge", APL, width=2.0, height=1.8, label_size=22).move_to(RIGHT * 4.6 + DOWN * 0.4)

        y_top, y_bot = 0.5, -1.3
        xl, xr = ctrl.get_center()[0] + 0.55, tx_dev.get_left()[0]
        loop_pts = [
            [xl, y_top, 0], [xr, y_top, 0], [xr, y_bot, 0], [xl, y_bot, 0], [xl, y_top, 0],
        ]
        top_wire = Line([xl, y_top, 0], [xr, y_top, 0], stroke_color=TEXT, stroke_width=3.5)
        bot_wire = Line([xr, y_bot, 0], [xl, y_bot, 0], stroke_color=TEXT, stroke_width=3.5)
        inner_link = VGroup(
            Line([xl, y_top, 0], [src.get_center()[0], y_top, 0]),
            Line([src.get_center()[0], y_top, 0], src.get_top()),
            Line(src.get_bottom(), res.get_top()),
            Line(res.get_bottom(), [src.get_center()[0], y_bot, 0]),
            Line([src.get_center()[0], y_bot, 0], [xl, y_bot, 0]),
        ).set_stroke(TEXT, 2.5)
        loop_path = VMobject().set_points_as_corners(
            [[src.get_center()[0], y_top, 0], [xr, y_top, 0], [xr, y_bot, 0], [src.get_center()[0], y_bot, 0], [src.get_center()[0], y_top, 0]])

        current = ValueTracker(12.0)
        def reading_mob():
            val = current.get_value()
            col = GOOD if val > 3.6 else DANGER
            num = Text(f"{val:4.1f}", font=MONO, font_size=56, color=col, weight=BOLD)
            un = T("mA", size=34, color=col)
            return VGroup(num, un).arrange(RIGHT, buff=0.15, aligned_edge=DOWN).move_to(UP * 2.45)

        read_grp = always_redraw(reading_mob)

        bar = Line(LEFT * 2.6, RIGHT * 2.6, stroke_color=DIM, stroke_width=10).move_to(UP * 1.45)
        def x_of(i_ma):
            return bar.get_left()[0] + (i_ma / 24.0) * bar.width
        bar_fill = always_redraw(lambda: Line(bar.get_left(), [x_of(current.get_value()), bar.get_y(), 0],
                                              stroke_color=GOOD if current.get_value() > 3.6 else DANGER, stroke_width=10))
        marks = VGroup()
        for i_ma, lab in [(0, "0"), (4, "4 mA"), (12, "12"), (20, "20 mA")]:
            p = np.array([x_of(i_ma), bar.get_y(), 0])
            marks.add(Line(p + UP * 0.14, p + DOWN * 0.14, stroke_color=MUTED, stroke_width=2))
            marks.add(T(lab, size=17, color=MUTED).next_to(p, DOWN, buff=0.2))
        pv_lbl = always_redraw(lambda: VGroup(
            T("process value", size=20, color=MUTED),
            T(f"{max(0.0, (current.get_value() - 4) / 16 * 100):.0f} %", size=26, color=TEXT, weight=BOLD)
        ).arrange(RIGHT, buff=0.15).move_to(UP * 2.45 + RIGHT * 3.4))

        dots = VGroup(*[packet(GOOD, 0.05, 3) for _ in range(14)])
        flow = {"a": 0.0}

        def run(g, dt):
            flow["a"] = (flow["a"] + dt * 0.012 * current.get_value()) % 1.0
            for i, d in enumerate(g):
                d.move_to(loop_path.point_from_proportion((flow["a"] + i / len(g)) % 1.0))

        dots.add_updater(run)
        run(dots, 0)

        with self.voice(
            "Process instruments have spoken the same basic language for decades. "
            "{loop}The 4–20 mA loop is brilliantly simple: two wires, one analog value, and the same two wires "
            "power the instrument. {live}Four milliamps, not zero, means zero percent — "
            "{brk}so a broken wire is instantly obvious."
        ) as v:
            self.play(FadeIn(ctrl), FadeIn(ctrl_lbl), FadeIn(tx_dev), run_time=0.8)
            self.play(Create(top_wire), Create(bot_wire), Create(inner_link), FadeIn(src), FadeIn(src_lbl),
                      FadeIn(res), FadeIn(res_lbl), run_time=1.2)
            v.wait_until("loop")
            self.add(dots)
            self.play(FadeIn(read_grp), FadeIn(bar), FadeIn(marks), FadeIn(pv_lbl), run_time=0.8)
            self.add(bar_fill)
            self.play(current.animate.set_value(20.0), run_time=1.6, rate_func=smooth)
            self.play(current.animate.set_value(4.0), run_time=1.8, rate_func=smooth)
            v.wait_until("live")
            lz = VGroup(T("live zero", size=22, color=GOOD, weight=BOLD)).next_to(np.array([x_of(4), bar.get_y(), 0]), UP, buff=0.25)
            self.play(FadeIn(lz, shift=DOWN * 0.1), Indicate(marks[3], color=GOOD), run_time=0.8)
            self.play(current.animate.set_value(13.5), run_time=1.0)
            v.wait_until("brk")
            cut_x = 0.6
            gap = Rectangle(width=0.32, height=0.4, fill_color=BG, fill_opacity=1, stroke_width=0).move_to([cut_x, y_top, 0])
            scis = icon("scissors", DANGER, 0.5).next_to(gap, DOWN, buff=0.12)
            dots.clear_updaters()
            self.play(FadeIn(scis, shift=DOWN * 0.2), run_time=0.4)
            self.add(gap)
            self.play(FadeOut(dots), current.animate.set_value(0.0), run_time=0.9)
            alarm = VGroup(icon("alert-triangle", DANGER, 0.45), T("wire break detected", size=26, color=DANGER, weight=BOLD)).arrange(RIGHT, buff=0.15)
            alarm.move_to(DOWN * 0.8 + RIGHT * 0.6)
            self.play(FadeIn(alarm, scale=0.9), Flash(scis.get_center(), color=DANGER), run_time=0.8)

        self.clear(run_time=0.7)

        # ------------------------------------------------------------ HART
        bits = [1, 0, 1, 1, 0, 1]
        t_bit = 1 / 1200
        ts, ys = fsk_current(bits, t_bit)
        T_ms = ts[-1] * 1000
        ax = Axes(x_range=[0, T_ms, 1], y_range=[11, 13, 0.5], x_length=9.4, y_length=3.5,
                  axis_config={"stroke_color": DIM, "stroke_width": 2, "include_tip": False}).shift(DOWN * 0.75 + LEFT * 0.6)
        ax_nums = VGroup(tick_labels(ax, [1, 2, 3, 4, 5], "x", "{:g}"), tick_labels(ax, [11, 11.5, 12, 12.5, 13], "y", "{:.1f}"))
        y_lbl = T("loop current [mA]", size=20, color=MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.6)
        x_lbl = T("time [ms]", size=20, color=MUTED).next_to(ax.x_axis, DOWN, buff=0.45).align_to(ax.x_axis, RIGHT)
        dc = DashedLine(ax.c2p(0, 12), ax.c2p(T_ms, 12), dash_length=0.1, stroke_color=GOOD, stroke_width=2.5)
        dc_lbl = VGroup(T("12 mA", size=22, color=GOOD, weight=BOLD), T("analog value", size=18, color=GOOD)).arrange(DOWN, buff=0.05)
        dc_lbl.next_to(ax.c2p(T_ms, 12), RIGHT, buff=0.3)
        sig = VMobject().set_points_smoothly([ax.c2p(t * 1000, y) for t, y in zip(ts[::3], ys[::3])]).set_stroke(APL, 3.5)
        bit_lbls = VGroup()
        sep = VGroup()
        for i, b in enumerate(bits):
            xm = (i + 0.5) * t_bit * 1000
            c = APL if b else VIOLET
            bit_lbls.add(VGroup(M(str(b), size=34, color=c, weight=BOLD),
                                T("1200 Hz" if b else "2200 Hz", size=16, color=c)).arrange(DOWN, buff=0.06).move_to(ax.c2p(xm, 13.35)))
            if i:
                sep.add(DashedLine(ax.c2p(i * t_bit * 1000, 11), ax.c2p(i * t_bit * 1000, 13), dash_length=0.06,
                                   stroke_color=DIM, stroke_width=1.5))
        title = VGroup(T("HART", size=36, color=TEXT, weight=BOLD), T("Bell 202 FSK riding on the 4–20 mA signal", size=24, color=MUTED)).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        title.to_edge(UP, buff=0.9)

        with self.voice(
            "{hart}In the 1980s, HART added digital communication by superimposing a small tone on that current: "
            "{f1}1,200 hertz for a one, {f2}2,200 hertz for a zero. "
            "{avg}Because the tone averages to zero, the analog value is untouched — "
            "{rate}but the data rate is only 1,200 bits per second."
        ) as v:
            self.play(FadeIn(title, shift=DOWN * 0.1), Create(ax), FadeIn(ax_nums), FadeIn(y_lbl), FadeIn(x_lbl), run_time=1.2)
            self.play(Create(dc), FadeIn(dc_lbl), run_time=0.8)
            v.wait_until("f1")
            self.play(Create(sig), run_time=v.until("avg", 2.0), rate_func=linear)
            self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in bit_lbls], lag_ratio=0.15), FadeIn(sep), run_time=1.0)
            v.wait_until("avg")
            avg_note = T("average = 12 mA, unchanged", size=22, color=GOOD).next_to(ax, DOWN, buff=0.9)
            self.play(Indicate(dc, color=GOOD, scale_factor=1.0), FadeIn(avg_note, shift=UP * 0.1), run_time=1.0)
            v.wait_until("rate")
            rate = pill("1,200 bit/s", GOOD, size=28).next_to(title, RIGHT, buff=0.4)
            self.play(FadeIn(rate, scale=0.8), run_time=0.7)

        self.clear(run_time=0.7)

        # ------------------------------------------------------------ Fieldbus
        trunk = Line(LEFT * 5.6, RIGHT * 5.6, stroke_color=GOOD, stroke_width=5).shift(DOWN * 0.5)
        terms = VGroup(*[resistor(0.7, MUTED).rotate(PI / 2).move_to(trunk.get_end() if k else trunk.get_start()).shift(DOWN * 0.45)
                         for k in range(2)])
        devs = VGroup()
        spurs = VGroup()
        names = [("gauge", "PT"), ("temperature", "TT"), ("droplet", "FT"), ("settings", "Valve"), ("flask", "AT")]
        for i, (ic, nm) in enumerate(names):
            x = -4.4 + i * 2.2
            d = device(nm, ic, GOOD, width=1.25, height=1.1, label_size=18).move_to([x, -2.45, 0])
            devs.add(d)
            spurs.add(Line([x, trunk.get_y(), 0], d.get_top(), stroke_color=GOOD, stroke_width=3))
        # Manchester waveform
        mbits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]
        pts = []
        w0, w1 = -5.4, 5.4
        bw = (w1 - w0) / len(mbits)
        y0, a = 1.25, 0.35
        for i, b in enumerate(mbits):
            x = w0 + i * bw
            first, second = (1, -1) if b else (-1, 1)
            pts += [(x, y0 + a * first), (x + bw / 2, y0 + a * first), (x + bw / 2, y0 + a * second), (x + bw, y0 + a * second)]
        manch = polyline(pts, GOOD, 3)
        fb_title = VGroup(T("Fieldbus", size=36, weight=BOLD), T("FOUNDATION Fieldbus H1 · PROFIBUS PA", size=24, color=MUTED)).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        fb_title.to_edge(UP, buff=0.9)
        with self.voice(
            "{fb}In the 1990s, fieldbuses such as FOUNDATION Fieldbus H1 and PROFIBUS PA went fully digital, "
            "{rate}at 31.25 kilobits per second — {shared}shared by every device on the segment."
        ) as v:
            self.play(FadeIn(fb_title, shift=DOWN * 0.1), Create(trunk), FadeIn(terms), run_time=1.0)
            self.play(LaggedStart(*[AnimationGroup(Create(s), FadeIn(d, shift=UP * 0.2)) for s, d in zip(spurs, devs)], lag_ratio=0.15), run_time=1.4)
            v.wait_until("rate")
            self.play(Create(manch), run_time=1.4, rate_func=linear)
            rate = pill("31.25 kbit/s", GOOD, size=28).next_to(manch, UP, buff=0.25)
            self.play(FadeIn(rate, scale=0.8), run_time=0.5)
            v.wait_until("shared")
            for i in range(len(devs)):
                self.play(devs[i].box.animate.set_fill(GOOD, opacity=0.35), spurs[i].animate.set_stroke(WHITE_SOFT, 5), run_time=0.22)
                self.play(devs[i].box.animate.set_fill(PANEL, opacity=1), spurs[i].animate.set_stroke(GOOD, 3), run_time=0.22)
            share = T("one talker at a time", size=22, color=MUTED).next_to(trunk, UP, buff=0.15).shift(RIGHT * 3.6)
            self.play(FadeIn(share), run_time=0.5)

        self.clear(run_time=0.7)

        # ------------------------------------------------------------ log-scale gap
        lg = Axes(x_range=[2, 9.3, 1], y_range=[0, 4.6, 1], x_length=8.8, y_length=4.6,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": True},
                  y_axis_config={"include_ticks": False, "stroke_opacity": 0}).shift(DOWN * 0.6 + RIGHT * 1.15)
        dec_lbls = VGroup()
        for e, lab in [(3, "1 k"), (4, "10 k"), (5, "100 k"), (6, "1 M"), (7, "10 M"), (8, "100 M"), (9, "1 G")]:
            dec_lbls.add(T(lab, size=18, color=MUTED).next_to(lg.c2p(e, 0), DOWN, buff=0.2))
        unit_lbl = T("bit/s (log scale)", size=18, color=MUTED).next_to(lg.x_axis, DOWN, buff=0.55).align_to(lg.x_axis, RIGHT)
        rows = [("HART", 1.2e3, GOOD), ("Fieldbus", 31.25e3, GOOD), ("Fast Ethernet", 100e6, BLUE), ("Gigabit Ethernet", 1e9, BLUE)]
        bars, labels, vals = VGroup(), VGroup(), VGroup()
        for i, (name, r, c) in enumerate(rows):
            y = 3.9 - i * 1.05
            x1 = np.log10(r)
            b = Rectangle(width=lg.c2p(x1, 0)[0] - lg.c2p(2, 0)[0], height=0.62, fill_color=c, fill_opacity=0.75, stroke_width=0)
            b.move_to(lg.c2p(2, y), aligned_edge=LEFT)
            bars.add(b)
            labels.add(T(name, size=24, color=TEXT, weight=BOLD).next_to(lg.c2p(2, y), LEFT, buff=0.25))
            vtxt = {1.2e3: "1.2 kbit/s", 31.25e3: "31.25 kbit/s", 100e6: "100 Mbit/s", 1e9: "1 Gbit/s"}[r]
            vals.add(T(vtxt, size=22, color=c, weight=BOLD).next_to(b, RIGHT, buff=0.15))
        with self.voice(
            "{eth}Meanwhile, the rest of industry moved to Ethernet, at a hundred megabits per second and more. "
            "{log}On a logarithmic scale, the gap is enormous."
        ) as v:
            self.play(Create(lg), FadeIn(dec_lbls), FadeIn(unit_lbl), FadeIn(labels), run_time=1.0)
            for i in range(4):
                self.play(GrowFromEdge(bars[i], LEFT), FadeIn(vals[i], shift=RIGHT * 0.2), run_time=0.7)
            v.wait_until("log")
            x_a, x_b = bars[0].get_right()[0], bars[2].get_right()[0]
            y_top = bars[0].get_top()[1] + 0.55
            guides = VGroup(DashedLine([x_a, bars[0].get_top()[1], 0], [x_a, y_top, 0], dash_length=0.06, stroke_color=MUTED, stroke_width=1.5),
                            DashedLine([x_b, bars[2].get_top()[1], 0], [x_b, y_top, 0], dash_length=0.06, stroke_color=MUTED, stroke_width=1.5))
            arrow = DoubleArrow([x_a, y_top, 0], [x_b, y_top, 0], buff=0, stroke_color=TEXT, stroke_width=3,
                                tip_length=0.18, max_tip_length_to_length_ratio=0.1)
            gap = T("≈ 83 000 ×", size=32, color=TEXT, weight=BOLD).next_to(arrow, UP, buff=0.12)
            self.play(Create(guides), run_time=0.4)
            self.play(GrowArrow(arrow), FadeIn(gap, scale=0.8), run_time=1.0)

        self.clear(run_time=0.7)

        # ------------------------------------------------------------ four walls
        sw, field_zone, fz_hatch, fz_lbl, fdevs, walls, wall_lbls = four_walls_layout()

        with self.voice(
            "{why}So why didn't plain Ethernet simply run out into the plant? {walls}Four walls stood in the way."
        ) as v:
            self.play(FadeIn(sw, shift=RIGHT * 0.2), FadeIn(field_zone), FadeIn(fz_hatch), FadeIn(fz_lbl),
                      LaggedStart(*[FadeIn(d, shift=LEFT * 0.2) for d in fdevs], lag_ratio=0.15), run_time=1.2)
            probe = packet(APL, 0.09, 4).move_to(sw.get_right())
            self.add(probe)
            self.play(probe.animate.move_to(RIGHT * 4.2 + DOWN * 0.2), run_time=1.0, rate_func=linear)
            self.play(FadeOut(probe), run_time=0.2)
            v.wait_until("walls")

        def raise_wall(i):
            wl = walls[i]
            rows = {}
            for b in wl:
                rows.setdefault(round(b.get_y(), 2), []).append(b)
            ordered = [rows[k] for k in sorted(rows)]
            return AnimationGroup(
                LaggedStart(*[AnimationGroup(*[FadeIn(b, shift=DOWN * 0.25) for b in row]) for row in ordered], lag_ratio=0.12),
                FadeIn(wall_lbls[i], shift=UP * 0.15), run_time=1.3)

        with self.voice(
            "{w1}Distance. Standard 100BASE-TX Ethernet is limited to one hundred meters per link, while field cables "
            "run for hundreds of meters — sometimes a kilometer or more."
        ) as v:
            self.play(raise_wall(0))
        with self.voice(
            "{w2}Wires. Office Ethernet needs two or four pairs; plants are full of installed two-wire cable."
        ) as v:
            self.play(raise_wall(1))
        with self.voice(
            "{w3}Power. A field instrument has no local supply. It must be powered over the same two wires "
            "that carry its signal."
        ) as v:
            self.play(raise_wall(2))
        with self.voice(
            "{w4}And explosion protection. In hazardous areas, the energy in a circuit must be limited, so that not "
            "even a fault can ignite the atmosphere. Ordinary Ethernet was never designed for that."
        ) as v:
            self.play(raise_wall(3))
            probe = packet(APL, 0.09, 4).move_to(sw.get_right())
            self.add(probe)
            self.play(probe.animate.move_to([walls[0].get_left()[0] - 0.12, -0.2, 0]), run_time=0.7, rate_func=rush_into)
            self.play(Flash(probe.get_center(), color=APL, flash_radius=0.4), probe.animate.move_to(sw.get_right() + RIGHT * 0.4),
                      run_time=0.8, rate_func=rush_from)
            self.play(FadeOut(probe), run_time=0.3)
        self.wait(0.5)
