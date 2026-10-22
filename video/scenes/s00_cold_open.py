import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *


def radar_transmitter(color=APL):
    housing = RoundedRectangle(width=1.0, height=0.62, corner_radius=0.14, fill_color=PANEL,
                               fill_opacity=1, stroke_color=color, stroke_width=2.4)
    window = RoundedRectangle(width=0.52, height=0.2, corner_radius=0.05, fill_color=color,
                              fill_opacity=0.3, stroke_width=0).move_to(housing).shift(UP * 0.06)
    neck = Rectangle(width=0.3, height=0.18, fill_color=PANEL, fill_opacity=1, stroke_color=color,
                     stroke_width=2).next_to(housing, DOWN, buff=0)
    flange = Rectangle(width=0.95, height=0.1, fill_color="#5B6B8C", fill_opacity=1,
                       stroke_width=0).next_to(neck, DOWN, buff=0)
    horn = Polygon([-0.14, 0, 0], [0.14, 0, 0], [0.38, -0.52, 0], [-0.38, -0.52, 0],
                   fill_color=color, fill_opacity=0.18, stroke_color=color,
                   stroke_width=2).next_to(flange, DOWN, buff=0)
    g = VGroup(neck, housing, window, flange, horn)
    g.horn = horn
    g.flange = flange
    return g


def echo_profile(d):
    return (0.07 + 0.04 * np.sin(3.1 * d) ** 2 + 0.22 * np.exp(-((d - 6.5) / 0.45) ** 2)
            + 0.88 * np.exp(-((d - 20.0) / 0.55) ** 2) + 0.12 * np.exp(-((d - 40 + 20.0) / 3) ** 2) * 0)


class ColdOpen(APLScene):
    def construct(self):
        self._chapters.append({"time": 0.0, "title": "Intro"})
        self.wait(0.6)
        # ------------------------------------------------------------ the tank
        tank = RoundedRectangle(width=3.4, height=4.6, corner_radius=0.45, stroke_color="#41507A",
                                stroke_width=3, fill_color="#0C1325", fill_opacity=1)
        tank.move_to(LEFT * 3.6 + DOWN * 0.75)
        top_y = tank.get_top()[1]
        geo = lambda: (tank.get_center()[0], tank.get_bottom()[1] + 0.36 * tank.height, tank.width / 3.4)

        def wave_y(x, cx, level, k):
            u = (x - cx) / k
            return level + k * (0.045 * np.sin(2.6 * u + 2.2 * self.t) + 0.025 * np.sin(5.3 * u - 3.1 * self.t))

        def liquid():
            cx, level, k = geo()
            inner = tank.copy().scale(0.985).set_stroke(width=0)
            xs = np.linspace(cx - 2.2 * k, cx + 2.2 * k, 60)
            wave = [np.array([x, wave_y(x, cx, level, k), 0]) for x in xs[::-1]]
            bottom = level - 5 * k
            poly = VMobject().set_points_as_corners(
                [np.array([cx - 2.2 * k, bottom, 0]), np.array([cx + 2.2 * k, bottom, 0])] + wave
                + [np.array([cx - 2.2 * k, bottom, 0])])
            liq = Intersection(inner, poly, stroke_width=0)
            liq.set_fill(color=["#0E7490", "#082F49"], opacity=1)
            liq.set_sheen_direction(DOWN)
            return liq.set_z_index(2)

        liq = always_redraw(liquid)

        def surface():
            cx, level, k = geo()
            return VMobject().set_points_smoothly(
                [np.array([x, wave_y(x, cx, level, k), 0]) for x in np.linspace(cx - 1.62 * k, cx + 1.62 * k, 40)]
            ).set_stroke(APL, 2.5 * k, opacity=0.9).set_z_index(3)

        surface_glow = always_redraw(surface)

        tx = radar_transmitter().scale(1.15)
        tx.next_to(tank, UP, buff=0)
        tx.shift(UP * (top_y - tx.flange.get_bottom()[1]))

        period, travel = 1.15, 0.6

        def pulses():
            g = VGroup()
            cx, level, k = geo()
            tip = tx.horn.get_bottom()
            dist = tip[1] - level
            for j in range(3):
                tau = (self.t - j * period / 3) % period
                if tau < travel:
                    r = 0.12 * k + (dist - 0.12 * k) * tau / travel
                    a = Arc(radius=r, start_angle=-PI / 2 - 0.42, angle=0.84, arc_center=tip)
                    g.add(a.set_stroke(APL, 3 * k, opacity=0.95 * (1 - 0.55 * tau / travel)))
                elif tau < 2 * travel:
                    q = (tau - travel) / travel
                    mirror = np.array([tip[0], level - dist, 0])
                    r = dist + dist * q
                    a = Arc(radius=r, start_angle=PI / 2 - 0.42 * (1 - 0.5 * q), angle=0.84 * (1 - 0.5 * q), arc_center=mirror)
                    g.add(a.set_stroke(VIOLET, 2.6 * k, opacity=0.85 * (1 - 0.6 * q)))
            return g.set_z_index(3)

        radar = always_redraw(pulses)
        tank_label = T("Radar level transmitter", size=22, color=MUTED).next_to(tx, UP, buff=0.18)

        # ------------------------------------------------------------ what the device knows
        info = panel(5.7, 5.3).move_to(RIGHT * 3.35 + DOWN * 0.35)
        info_title = T("What the instrument knows", size=24, color=MUTED, weight=MEDIUM)
        info_title.next_to(info.get_top(), DOWN, buff=0.28).align_to(info, LEFT).shift(RIGHT * 0.35)

        ax = Axes(x_range=[0, 30, 10], y_range=[0, 1, 1], x_length=4.7, y_length=1.45,
                  axis_config={"stroke_color": DIM, "stroke_width": 2, "include_ticks": False},
                  tips=False).next_to(info_title, DOWN, buff=0.38).align_to(info_title, LEFT)
        curve = ax.plot(echo_profile, x_range=[0.3, 29.7, 0.05], color=APL, stroke_width=2.6)
        area = ax.get_area(curve, x_range=[0.3, 29.7], color=APL, opacity=0.18)
        surf_mark = DashedLine(ax.c2p(20, 0), ax.c2p(20, 1.05), dash_length=0.06, stroke_color=VIOLET, stroke_width=2)
        surf_lbl = T("liquid surface", size=16, color=VIOLET).next_to(surf_mark.get_top(), RIGHT, buff=0.08).shift(DOWN * 0.08)
        ax_lbl = T("echo profile", size=18, color=TEXT).next_to(ax, UP, buff=0.06).align_to(ax, LEFT).shift(RIGHT * 0.15)
        x_lbl = T("distance [m]", size=14, color=MUTED).next_to(ax.x_axis, DOWN, buff=0.08).align_to(ax, RIGHT)
        echo_grp = VGroup(ax, area, curve, surf_mark, surf_lbl, ax_lbl, x_lbl)

        def row(icon_name, label, value, color=TEXT):
            ic = icon(icon_name, color=MUTED, height=0.38)
            lb = T(label, size=21, color=MUTED)
            vl = T(value, size=23, color=color, weight=BOLD)
            g = VGroup(ic, lb).arrange(RIGHT, buff=0.18)
            vl.next_to(g, RIGHT, buff=0.3)
            return VGroup(g, vl)

        r_temp = row("temperature", "Electronics", "41.3 °C")
        r_ant = row("eye", "Antenna", "clean ✓", GOOD)
        spark_ax_pts = [(i / 59, 0.5 + 0.22 * np.sin(i / 6.0) + 0.08 * np.sin(i * 1.7)) for i in range(60)]
        spark = polyline([(0, 0)], APL)
        spark = VMobject().set_points_smoothly([np.array([x * 1.9, y * 0.55, 0]) for x, y in spark_ax_pts]).set_stroke(APL, 2.5)
        r_trend = VGroup(VGroup(icon("chart-line", MUTED, 0.38), T("30-day trend", size=21, color=MUTED)).arrange(RIGHT, buff=0.18))
        spark.next_to(r_trend, RIGHT, buff=0.3)
        r_trend.add(spark)
        rows = VGroup(r_temp, r_ant, r_trend).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        rows.next_to(ax, DOWN, buff=0.45).align_to(ax, LEFT)

        # ------------------------------------------------------------ beat 1
        with self.voice(
            "Somewhere in a chemical plant, a radar level transmitter watches the surface of a liquid, "
            "twenty meters below. {echo}It knows the full echo profile, {temp}its own electronics temperature, "
            "{antenna}the condition of its antenna, {trend}and weeks of trends."
        ) as v:
            self.play(DrawBorderThenFill(tank), run_time=1.2)
            self.play(FadeIn(liq), FadeIn(surface_glow), run_time=0.6)
            self.play(FadeIn(tx, shift=DOWN * 0.3), FadeIn(tank_label), run_time=0.8)
            self.add(radar)
            self.wait(0.4)
            self.play(FadeIn(info), FadeIn(info_title, shift=UP * 0.1), run_time=v.until("echo", 0.6))
            self.play(Create(ax), run_time=0.5)
            self.play(Create(curve), FadeIn(area), FadeIn(ax_lbl), FadeIn(x_lbl), run_time=1.0)
            self.play(Create(surf_mark), FadeIn(surf_lbl), run_time=0.5)
            v.wait_until("temp")
            self.play(FadeIn(r_temp, shift=RIGHT * 0.2), run_time=0.6)
            v.wait_until("antenna")
            self.play(FadeIn(r_ant, shift=RIGHT * 0.2), run_time=0.6)
            v.wait_until("trend")
            self.play(FadeIn(r_trend[0], shift=RIGHT * 0.2), Create(spark), run_time=1.0)

        # ------------------------------------------------------------ beat 2: one number
        readout_box = RoundedRectangle(width=3.1, height=1.05, corner_radius=0.14, fill_color="#071a14",
                                       fill_opacity=1, stroke_color=GOOD, stroke_width=2.4)
        readout = M("12.00 mA", size=40, color=GOOD, weight=BOLD).move_to(readout_box)
        ro = VGroup(readout_box, readout).move_to(RIGHT * 2.2 + UP * 1.2)

        scale_bar = Line(LEFT * 2.2, RIGHT * 2.2, stroke_color=DIM, stroke_width=8)
        scale_bar.next_to(ro, DOWN, buff=0.75)
        fill_bar = Line(scale_bar.get_left(), scale_bar.point_from_proportion(0.5), stroke_color=GOOD, stroke_width=8)
        ticks = VGroup()
        for frac, lab in [(0, "4 mA"), (0.5, "12 mA"), (1, "20 mA")]:
            p = scale_bar.point_from_proportion(frac)
            ticks.add(Line(p + UP * 0.12, p + DOWN * 0.12, stroke_color=MUTED, stroke_width=2))
            ticks.add(T(lab, size=18, color=MUTED).next_to(p, DOWN, buff=0.2))
        pct = VGroup(T("0 %", size=18, color=DIM).next_to(scale_bar.get_left(), UP, buff=0.18),
                     T("50 %", size=18, color=GOOD).next_to(scale_bar.get_center(), UP, buff=0.18),
                     T("100 %", size=18, color=DIM).next_to(scale_bar.get_right(), UP, buff=0.18))
        meter = VGroup(scale_bar, fill_bar, ticks, pct)

        wire_y = tx[1].get_center()[1]
        w_start = tx[1].get_right()
        wire_a = Line(w_start + UP * 0.08, [7.4, wire_y + 0.08, 0], stroke_color=MUTED, stroke_width=3)
        wire_b = Line(w_start + DOWN * 0.08, [7.4, wire_y - 0.08, 0], stroke_color=MUTED, stroke_width=3)

        content = VGroup(echo_grp, rows, info_title)
        with self.voice(
            "{one}And it reports — one number. {ma}A current between four and twenty milliamps, on two wires. "
            "{hart}If you're lucky, a trickle of digital data rides along at 1,200 bits per second — "
            "the speed of an early telephone modem."
        ) as v:
            v.wait_until("one")
            target = tx[1].get_center()
            self.play(
                LaggedStart(*[m.animate.scale(0.05).move_to(target).set_opacity(0) for m in [echo_grp, rows[0], rows[1], rows[2], info_title]],
                            lag_ratio=0.08),
                info.animate.scale(0.05).move_to(target).set_opacity(0),
                run_time=1.3,
            )
            self.remove(info, content)
            self.play(Flash(target, color=GOOD, flash_radius=0.7, line_length=0.3), FadeIn(ro, scale=0.6), run_time=0.8)
            v.wait_until("ma")
            self.play(Create(wire_a), Create(wire_b), run_time=0.9)
            self.play(FadeIn(meter, shift=UP * 0.1), run_time=0.8)
            v.wait_until("hart")
            bits = VGroup(*[packet(GOOD, 0.045, 3) for _ in range(5)])
            path = Line(w_start + UP * 0.08, [7.4, wire_y + 0.08, 0])
            for i, b in enumerate(bits):
                b.move_to(path.point_from_proportion(0))
            hart_lbl = T("HART: 1,200 bit/s", size=22, color=GOOD).next_to(wire_a, UP, buff=0.12).shift(RIGHT * 1.6)
            self.play(FadeIn(hart_lbl, shift=UP * 0.1), run_time=0.6)
            self.add(bits)
            prog = {"t": 0.0}

            def crawl(g, dt):
                prog["t"] += dt
                for i, b in enumerate(g):
                    a = (prog["t"] * 0.03 - i * 0.075)
                    b.move_to(path.point_from_proportion(np.clip(a, 0, 1)))
                    b.set_opacity(1 if 0 < a < 1 else 0)

            bits.add_updater(crawl)
            v.wait_end()

        # ------------------------------------------------------------ beat 3: the office next door
        plant = VGroup(tank, tx, tank_label)
        with self.voice(
            "{office}Meanwhile, a few hundred meters away, the office network moves a billion bits per second — "
            "almost a million times more."
        ) as v:
            bits.clear_updaters()
            self.play(FadeOut(VGroup(meter, ro, hart_lbl, bits, wire_a, wire_b)), run_time=0.6)
            self.play(FadeOut(tank_label), run_time=0.3)
            plant = VGroup(tank, tx)
            self.play(plant.animate.scale(0.6).move_to(LEFT * 5.3 + DOWN * 1.35), run_time=1.0)
            wy = tx[1].get_center()[1]
            ctrl = device("Control room", "device-desktop", MUTED, width=2.0, height=1.35, label_size=20).move_to([-0.9, wy, 0])
            office = device("Office / IT", "building", BLUE, width=2.0, height=1.35, label_size=20).move_to([4.9, wy, 0])
            f_wire = Line(tx[1].get_right() + RIGHT * 0.05, ctrl.get_left(), stroke_color=MUTED, stroke_width=3)
            e_wire = Line(ctrl.get_right(), office.get_left(), stroke_color=BLUE, stroke_width=7)
            e_glow = glow(e_wire, BLUE, layers=5, max_width=14, max_opacity=0.25)
            self.play(FadeIn(ctrl, shift=UP * 0.2), FadeIn(office, shift=UP * 0.2), run_time=0.8)
            self.play(Create(f_wire), Create(e_wire), FadeIn(e_glow), run_time=0.8)
            slow = flow_along(f_wire, n=2, color=GOOD, speed=0.05, radius=0.05)
            fast = flow_along(Line(office.get_left(), ctrl.get_right()), n=26, color=BLUE, speed=1.6, radius=0.045)
            l1 = T("1,200 bit/s", size=24, color=GOOD, weight=BOLD).next_to(f_wire, UP, buff=0.3)
            l2 = T("1,000,000,000 bit/s", size=24, color=BLUE, weight=BOLD).next_to(e_wire, UP, buff=0.3)
            l2b = T("1 Gbit/s Ethernet", size=18, color=MUTED).next_to(e_wire, DOWN, buff=0.3)
            l1b = T("4–20 mA + HART", size=18, color=MUTED).next_to(f_wire, DOWN, buff=0.3).shift(RIGHT * 0.35)
            self.add(slow, fast)
            self.play(FadeIn(l1, shift=UP * 0.1), FadeIn(l2, shift=UP * 0.1), FadeIn(l1b), FadeIn(l2b), run_time=0.7)
            gap = VGroup(T("≈ 830 000 ×", size=44, color=TEXT, weight=BOLD), T("more data", size=22, color=MUTED)).arrange(DOWN, buff=0.12)
            gap.move_to([1.2, wy + 2.1, 0])
            v.wait_end(-0.6)
            self.play(FadeIn(gap, scale=0.8), run_time=0.6)
        self.wait(0.4)

        # ------------------------------------------------------------ title
        slow.clear_updaters()
        fast.clear_updaters()
        self.clear(run_time=0.8)
        tp = TwistedPair3D(length=20, radius=0.13, pitch=1.25, segments=260, colors=(APL, VIOLET), width=20)
        state = {"t": 0.0}
        tp_fade = ValueTracker(0.0)

        def spin(m, dt):
            state["t"] += dt
            t = state["t"]
            pulses = []
            for k in range(4):
                x = ((t * 3.2 + k * 5) % 20) - 10
                pulses.append((0, x, APL, 1.0))
                x2 = 10 - ((t * 3.2 + k * 5 + 2.5) % 20)
                pulses.append((1, x2, VIOLET, 1.0))
            m.set_view(spin=-1.6 * t, yaw=0.62 - 0.02 * t, pitch=0.18, offset=[0.3, -1.45, 0], pulses=pulses,
                       fade=tp_fade.get_value())

        tp.add_updater(spin)
        spin(tp, 0)
        self.add(tp)
        title = H("Ethernet-APL", size=110).move_to(UP * 1.75)
        title_glow = glow(title.copy().set_stroke(APL, 2), APL, layers=7, max_width=26, max_opacity=0.16).set_z_index(-1)
        sub = T("Ethernet, all the way to the field instrument", size=32, color=MUTED).next_to(title, DOWN, buff=0.3)
        with self.voice(
            "This video is about the technology that finally brings Ethernet all the way out to the instrument: "
            "{title}Ethernet-APL."
        ) as v:
            self.play(tp_fade.animate.set_value(1.0), run_time=1.5)
            v.wait_until("title")
            self.play(Write(title), FadeIn(title_glow), run_time=1.3)
            self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.7)

        chips = VGroup(pill("volts", POWER), pill("symbols", APL), pill("joules", HAZARD)).arrange(RIGHT, buff=0.35)
        chips.next_to(sub, DOWN, buff=0.45)
        vs = VGroup(T("compared with", size=28, color=MUTED), T("CAN bus", size=34, color=CAN, weight=BOLD)).arrange(RIGHT, buff=0.22)
        vs.next_to(sub, DOWN, buff=0.45)
        with self.voice(
            "{volts}We'll take it apart down to the volts, the symbols, and the joules. "
            "{can}And as a reference point, we'll use a network that many engineers already know from vehicles "
            "and machines: CAN bus."
        ) as v:
            v.wait_until("volts")
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in chips], lag_ratio=0.35), run_time=1.4)
            v.wait_until("can")
            self.play(FadeOut(chips, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(vs, shift=UP * 0.2), run_time=0.8)
        self.wait(0.6)
        self.play(FadeOut(VGroup(title, title_glow, sub, vs)), tp_fade.animate.set_value(0.0), run_time=1.0)
        tp.clear_updaters()
