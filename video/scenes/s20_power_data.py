import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *


def path_through(points):
    return VMobject().set_points_as_corners([np.array([p[0], p[1], 0]) for p in points])


class PowerData(APLScene):
    def construct(self):
        self.tag = corner_tag("08 · Inside the receiver", color=BLUE)
        self.add(self.tag)
        self.chapter(9, "Power on the same pair", "Inductors, capacitors, and I²R", color=POWER)

        # ------------------------------------------------------------ spectrum: DC vs data
        ax = Axes(x_range=[3, 8, 1], y_range=[0, 1.1, 0.5], x_length=8.2, y_length=3.4,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([1.2, 0.0, 0])
        xl = tick_labels(ax, [3, 4, 5, 6, 7, 8], "x", texts=["1 kHz", "10 kHz", "100 kHz", "1 MHz", "10 MHz", "100 MHz"], size=17)
        f_lbl = T("frequency (log scale)", size=18, color=MUTED).next_to(xl, DOWN, buff=0.15).align_to(ax, RIGHT)
        dc_axis = Line(ax.c2p(3, 0) + LEFT * 1.9, ax.c2p(3, 0) + LEFT * 0.45, stroke_color=DIM, stroke_width=2)
        brk = VGroup(Line(UP * 0.12 + LEFT * 0.06, DOWN * 0.12 + RIGHT * 0.06), Line(UP * 0.12 + RIGHT * 0.06, DOWN * 0.12 + RIGHT * 0.18)).set_stroke(DIM, 2)
        brk.move_to(ax.c2p(3, 0) + LEFT * 0.25)
        dc_x = dc_axis.get_center()[0]
        dc_bar = Rectangle(width=0.32, height=3.2, fill_color=POWER, fill_opacity=0.9, stroke_width=0).move_to([dc_x, ax.c2p(3, 0)[1] + 1.6, 0])
        dc_lbl = VGroup(T("power", size=22, color=POWER, weight=BOLD), T("DC · 0 Hz", size=18, color=POWER)).arrange(DOWN, buff=0.05).next_to(dc_bar, UP, buff=0.12)
        dc_tick = T("0 Hz", size=17, color=MUTED).next_to(dc_axis.get_center(), DOWN, buff=0.18)

        def data_psd(lf):
            f = 10 ** lf
            return float(np.sinc(f / 7.5e6) ** 2 * (1 - np.exp(-(f / 1.5e5) ** 2)))

        psd = ax.plot(data_psd, x_range=[3.2, 7.95, 0.01], color=APL, stroke_width=3.5)
        area = ax.get_area(psd, x_range=[3.2, 7.95], color=APL, opacity=0.25)
        data_lbl = VGroup(T("data", size=22, color=APL, weight=BOLD), T("≈ 100 kHz … a few MHz", size=18, color=APL)).arrange(DOWN, buff=0.05)
        data_lbl.move_to(ax.c2p(6.0, 1.3))
        nodc = T("DC-free code: no data energy at 0 Hz", size=19, color=GOOD).move_to(ax.c2p(4.4, 0.62))

        with self.voice(
            "{pwr}Power travels on the same two wires, and the trick is frequency, again. {dc}Power is direct current, at "
            "zero hertz. {data}The data lives between roughly a hundred kilohertz and a few megahertz — {free}and, thanks "
            "to the DC-free code, it contains no DC of its own."
        ) as v:
            self.play(Create(ax), FadeIn(xl), FadeIn(f_lbl), Create(dc_axis), FadeIn(brk), FadeIn(dc_tick), run_time=1.0)
            v.wait_until("dc")
            self.play(GrowFromEdge(dc_bar, DOWN), FadeIn(dc_lbl, shift=DOWN * 0.1), run_time=0.9)
            v.wait_until("data")
            self.play(Create(psd), FadeIn(area), FadeIn(data_lbl), run_time=1.4)
            v.wait_until("free")
            self.play(FadeIn(nodc, shift=UP * 0.1), run_time=0.7)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the coupling network
        yt, yb = 0.15, -0.6
        phy_a = device("PHY", "cpu", APL, width=1.4, height=1.6, label_size=18).move_to([-6.2, (yt + yb) / 2, 0])
        phy_b = device("PHY", "cpu", VIOLET, width=1.4, height=1.6, label_size=18).move_to([6.2, (yt + yb) / 2, 0])
        caps = VGroup()
        for x in (-4.75, 4.75):
            for y in (yt, yb):
                caps.add(capacitor(0.7, APL, 2.6).move_to([x, y, 0]))
        wires = VGroup(
            Line(phy_a.get_right()[0] * RIGHT + yt * UP, [-5.1, yt, 0]), Line(phy_a.get_right()[0] * RIGHT + yb * UP, [-5.1, yb, 0]),
            Line([-4.4, yt, 0], [4.4, yt, 0]), Line([-4.4, yb, 0], [4.4, yb, 0]),
            Line([5.1, yt, 0], [phy_b.get_left()[0], yt, 0]), Line([5.1, yb, 0], [phy_b.get_left()[0], yb, 0]),
        ).set_stroke(TEXT, 2.6)
        # power supply and load above, inductors down to the conductors
        pse = VGroup(dc_source(0.34, POWER), T("46 V", size=20, color=POWER, weight=BOLD))
        pse[0].move_to([-3.2, 2.55, 0])
        pse[1].next_to(pse[0], LEFT, buff=0.12).shift(UP * 0.38)
        pse_lbl = T("power switch supply", size=17, color=MUTED).next_to(pse[0], UP, buff=0.14).shift(RIGHT * 0.7)
        load = VGroup(RoundedRectangle(width=2.4, height=0.75, corner_radius=0.12, fill_color=PANEL, fill_opacity=1, stroke_color=POWER, stroke_width=2.2),
                      T("DC/DC → electronics", size=15, color=POWER)).move_to([3.2, 2.6, 0])
        load[1].move_to(load[0])
        load_lbl = T("field device", size=17, color=MUTED).next_to(load, UP, buff=0.12)
        ind = VGroup()
        xs_l = [(-3.75, yt), (-2.65, yb), (2.65, yt), (3.75, yb)]
        for x, y in xs_l:
            top = 2.0
            ind.add(VGroup(Line([x, top, 0], [x, 1.55, 0]), inductor(0.95, POWER, 2.6).rotate(PI / 2).move_to([x, 1.08, 0]),
                           Line([x, 0.6, 0], [x, y, 0])).set_stroke(POWER, 2.6))
        pse_wires = VGroup(
            path_through([(-3.75, 2.0), (-3.75, 2.55), (pse[0].get_left()[0], 2.55)]),
            path_through([(-2.65, 2.0), (-2.65, 2.55), (pse[0].get_right()[0], 2.55)]),
            path_through([(2.65, 2.0), (2.65, load[0].get_bottom()[1])]),
            path_through([(3.75, 2.0), (3.75, load[0].get_bottom()[1])]),
        ).set_stroke(POWER, 2.6)
        dots = VGroup(*[Dot([x, y, 0], radius=0.07, color=POWER) for x, y in xs_l])
        pair_lbl = T("one twisted pair", size=19, color=MUTED).move_to([0, yb - 0.45, 0])
        l_note = VGroup(T("inductors", size=20, color=POWER, weight=BOLD), T("pass DC · block data", size=17, color=TEXT)).arrange(DOWN, buff=0.04)
        l_note.move_to([0, 1.55, 0])
        c_note = VGroup(T("capacitors", size=20, color=APL, weight=BOLD), T("pass data · block DC", size=17, color=TEXT)).arrange(DOWN, buff=0.04)
        c_note.move_to([-4.75, yb - 0.95, 0])
        c_note2 = c_note.copy().move_to([4.75, yb - 0.95, 0])

        lb = load[0].get_bottom()[1]
        p_loop = path_through([(pse[0].get_right()[0], 2.55), (-2.65, 2.55), (-2.65, yb), (3.75, yb), (3.75, lb)])
        p_loop2 = path_through([(2.65, lb), (2.65, yt), (-3.75, yt), (-3.75, 2.55), (pse[0].get_left()[0], 2.55)])
        d_path = Line([phy_a.get_right()[0], yt, 0], [phy_b.get_left()[0], yt, 0])

        with self.voice(
            "{coupling}So at each end of the cable, inductors pass the direct current to and from the power supply, but "
            "block the fast data, {caps}while capacitors pass the data to the transceiver, but block the DC. "
            "{mech}A mechanical engineer would recognize it immediately: a static load with a vibration riding on top, "
            "separated by a low-pass and a high-pass filter."
        ) as v:
            self.play(FadeIn(phy_a), FadeIn(phy_b), Create(wires), FadeIn(pair_lbl), run_time=1.0)
            self.play(FadeIn(pse), FadeIn(pse_lbl), FadeIn(load), FadeIn(load_lbl), run_time=0.6)
            self.play(LaggedStart(*[Create(i) for i in ind], lag_ratio=0.15), Create(pse_wires), FadeIn(dots), run_time=1.2)
            pf1 = flow_along(p_loop2, n=9, color=POWER, speed=0.12, radius=0.05, reverse=True)
            pf2 = flow_along(p_loop, n=9, color=POWER, speed=0.12, radius=0.05, reverse=True)
            self.add(pf1, pf2)
            self.play(FadeIn(l_note, shift=DOWN * 0.1), run_time=0.6)
            v.wait_until("caps")
            self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in caps], lag_ratio=0.1), run_time=0.8)
            df1 = flow_along(d_path, n=6, color=APL, speed=0.3, radius=0.05)
            df2 = flow_along(Line([phy_a.get_right()[0], yb, 0], [phy_b.get_left()[0], yb, 0]), n=6, color=VIOLET, speed=0.3, radius=0.05, reverse=True)
            self.add(df1, df2)
            self.play(FadeIn(c_note, shift=UP * 0.1), FadeIn(c_note2, shift=UP * 0.1), run_time=0.6)
            v.wait_until("mech")
            # mechanical analogy strip
            strip = panel(12.6, 1.35).move_to([0, -2.85, 0])
            xs = np.linspace(-5.9, -2.6, 120)
            sig = VMobject().set_points_smoothly([np.array([x, -2.85 + 0.12 + 0.25 * np.sin(9 * x), 0]) for x in xs]).set_stroke(TEXT, 2.5)
            base = DashedLine([-5.9, -2.85 + 0.12, 0], [-2.6, -2.85 + 0.12, 0], dash_length=0.06, stroke_color=POWER, stroke_width=1.5)
            s_lbl = T("load + vibration", size=16, color=TEXT).move_to([-4.25, -3.35, 0])
            arr1 = Arrow([-2.4, -2.75, 0], [-1.0, -2.45, 0], buff=0.05, stroke_width=3, stroke_color=MUTED, max_tip_length_to_length_ratio=0.15)
            arr2 = Arrow([-2.4, -2.95, 0], [-1.0, -3.25, 0], buff=0.05, stroke_width=3, stroke_color=MUTED, max_tip_length_to_length_ratio=0.15)
            lp = VGroup(T("low-pass (L):", size=17, color=POWER, weight=BOLD),
                        Line(LEFT * 1.1, RIGHT * 1.1, stroke_color=POWER, stroke_width=3), T("static load", size=16, color=POWER)).arrange(RIGHT, buff=0.2)
            lp.move_to([1.85, -2.45, 0])
            hp_wave = VMobject().set_points_smoothly([np.array([x, 0.22 * np.sin(9 * x), 0]) for x in np.linspace(-1.1, 1.1, 60)]).set_stroke(APL, 2.5)
            hp = VGroup(T("high-pass (C):", size=17, color=APL, weight=BOLD), hp_wave, T("vibration", size=16, color=APL)).arrange(RIGHT, buff=0.2)
            hp.move_to([1.85, -3.25, 0])
            self.play(FadeOut(c_note), FadeOut(c_note2), FadeIn(strip), Create(sig), Create(base), FadeIn(s_lbl), run_time=1.0)
            self.play(GrowArrow(arr1), GrowArrow(arr2), FadeIn(lp, shift=RIGHT * 0.1), FadeIn(hp, shift=RIGHT * 0.1), run_time=1.0)

        # numbers: the two filters at DC and at the Nyquist frequency
        self.play(FadeOut(VGroup(strip, sig, base, s_lbl, arr1, arr2, lp, hp)), run_time=0.5)
        zl = VGroup(TeX(r"|Z_L| = \omega L", size=34, color=POWER),
                    TeX(r"= 2\pi \cdot 3.75\,\mathrm{MHz} \cdot 220\,\mu\mathrm{H} \approx 5.2\ \mathrm{k\Omega}", size=30, color=TEXT)).arrange(RIGHT, buff=0.2)
        zc = VGroup(TeX(r"|Z_C| = \frac{1}{\omega C}", size=34, color=APL),
                    TeX(r"= \frac{1}{2\pi \cdot 3.75\,\mathrm{MHz} \cdot 220\,\mathrm{nF}} \approx 0.2\ \Omega", size=30, color=TEXT)).arrange(RIGHT, buff=0.2)
        nums = VGroup(zl, zc).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([0, -2.75, 0])
        nb = BackgroundRectangle(nums, color=BG, fill_opacity=0.92, buff=0.2)
        dc_note = T("at DC: exactly the other way round", size=18, color=MUTED).next_to(nums, RIGHT, buff=0.4)
        with self.voice(
            "{num}Some numbers make it concrete. In a typical design, at 3.75 megahertz, a 220-microhenry inductor has an "
            "impedance of about five kilohms — fifty times the line's hundred ohms, so it barely loads the signal. "
            "{cap}A 220-nanofarad capacitor, at the same frequency, is just a fifth of an ohm. {dc}At DC, it's exactly the "
            "other way round."
        ) as v:
            self.play(FadeIn(nb), Write(zl), run_time=1.6)
            v.wait_until("cap")
            self.play(Write(zc), run_time=1.6)
            v.wait_until("dc")
            dc_note.next_to(nums, UP, buff=0.15).align_to(nums, RIGHT)
            self.play(FadeIn(dc_note), run_time=0.6)

        for m in (pf1, pf2, df1, df2):
            m.clear_updaters()
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ why the trunk uses up to 50 V: I^2 R
        f1 = TeX(r"P_{\text{loss}} = I^2 R_{\text{loop}}", r"= \left(\frac{P}{V}\right)^{2} R_{\text{loop}}", size=40).move_to([-3.1, 2.3, 0])
        f1[1].set_color(POWER)
        bars = VGroup()
        for i, (v_, loss, col) in enumerate(((24, 4, DANGER), (48, 1, GOOD))):
            y = 0.85 - i * 0.95
            r = Rectangle(width=0.9 * loss, height=0.55, fill_color=col, fill_opacity=0.85, stroke_width=0).move_to([-4.7, y, 0], aligned_edge=LEFT)
            lab = T(f"{v_} V", size=22, color=TEXT, weight=BOLD).next_to([-4.7, y, 0], LEFT, buff=0.25)
            val = T("loss × 4" if loss == 4 else "loss × 1", size=19, color=col, weight=BOLD).next_to(r, RIGHT, buff=0.15)
            bars.add(VGroup(r, lab, val))
        same_p = T("same power delivered", size=17, color=MUTED).next_to(bars, DOWN, buff=0.25).align_to(bars, LEFT)
        pax = Axes(x_range=[0, 1, 0.25], y_range=[0, 1.15, 0.25], x_length=5.6, y_length=3.6,
                   axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([3.6, -0.3, 0])
        parab = pax.plot(lambda x: 4 * x * (1 - x), x_range=[0, 1, 0.01], color=POWER, stroke_width=4)
        peak = Dot(pax.c2p(0.5, 1.0), radius=0.08, color=POWER)
        pk_l = TeX(r"P_{\max} = \frac{V^2}{4R_{\text{loop}}}", size=34, color=POWER).next_to(peak, UP, buff=0.2)
        eff = T("only at 50 % efficiency", size=17, color=MUTED).next_to(pax.c2p(0.5, 0.0), UP, buff=0.25)
        dl = DashedLine(pax.c2p(0.5, 0), pax.c2p(0.5, 1.0), dash_length=0.06, stroke_color=POWER, stroke_width=1.5)
        x_l = T("current I", size=17, color=MUTED).next_to(pax, DOWN, buff=0.12).align_to(pax, RIGHT)
        y_l = TeX(r"P_{\text{load}} = V I - I^2 R_{\text{loop}}", size=28, color=TEXT).next_to(pax, UP, buff=0.75).align_to(pax, LEFT)
        with self.voice(
            "{why}Why does the trunk run at up to fifty volts? Because the cable's resistance burns I squared R. "
            "{half}Deliver the same power at twice the voltage, and the current halves — so the loss drops to a quarter. "
            "{ceil}And there's a hard ceiling. With a source voltage V and a loop resistance R, the most power that can ever "
            "reach the far end is V squared over four R — and only at fifty percent efficiency. {copper}So a long, powerful "
            "trunk needs both: voltage, and copper."
        ) as v:
            self.play(Write(f1), run_time=1.6)
            v.wait_until("half")
            for b_ in bars:
                self.play(GrowFromEdge(b_[0], LEFT), FadeIn(b_[1]), FadeIn(b_[2]), run_time=0.7)
            self.play(FadeIn(same_p), run_time=0.4)
            v.wait_until("ceil")
            self.play(Create(pax), FadeIn(x_l), FadeIn(y_l), run_time=0.7)
            self.play(Create(parab), run_time=1.2)
            self.play(Create(dl), FadeIn(peak, scale=0.5), Write(pk_l), FadeIn(eff), run_time=1.2)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ how much power
        rows = [("4–20 mA instrument", 0.04, GOOD, "≈ 40 mW"),
                ("APL spur, class A", 0.54, APL, "≈ 0.54 W"),
                ("APL spur, class C", 1.1, APL, "≈ 1.1 W")]
        scale = 5.6 / 1.2
        x0 = -2.6
        bars = VGroup()
        for i, (nm, pw, col, txt) in enumerate(rows):
            y = 1.2 - i * 1.15
            b = Rectangle(width=max(0.03, pw * scale), height=0.62, fill_color=col, fill_opacity=0.8, stroke_width=0)
            b.move_to([x0, y, 0], aligned_edge=LEFT)
            lab = T(nm, size=22, color=TEXT, weight=BOLD).next_to([x0, y, 0], LEFT, buff=0.3)
            val = T(txt, size=22, color=col, weight=BOLD).next_to(b, RIGHT, buff=0.2)
            bars.add(VGroup(b, lab, val))
        base = Line([x0, 1.75, 0], [x0, -1.6, 0], stroke_color=DIM, stroke_width=2)
        mult = VGroup(T("× 13", size=24, color=APL, weight=BOLD).next_to(bars[1][2], RIGHT, buff=0.35),
                      T("× 27", size=24, color=APL, weight=BOLD).next_to(bars[2][2], RIGHT, buff=0.35))
        trunk_card = panel(5.2, 1.5).move_to([2.2, -2.75, 0])
        tc = VGroup(icon("bolt", POWER, 0.6), VGroup(T("Trunk: up to 92 W", size=28, color=POWER, weight=BOLD),
                                                    T("at the power switch (class 4, max 50 V)", size=17, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)).arrange(RIGHT, buff=0.3)
        tc.move_to(trunk_card)
        how = T("How much power?", size=40, color=TEXT, weight=BOLD).move_to(UP * 2.75)
        with self.voice(
            "{how}How much power? {trunk}An APL power switch can feed a trunk with up to about ninety-two watts at the "
            "source. {spur}An instrument on an intrinsically safe spur gets roughly half a watt to one watt, depending on "
            "its power class. {cmp}That sounds modest — but it's more than ten times the forty milliwatts or so that a "
            "four-to-twenty milliamp instrument has to live on."
        ) as v:
            self.play(FadeIn(how, shift=DOWN * 0.1), run_time=0.6)
            v.wait_until("trunk")
            self.play(FadeIn(trunk_card), FadeIn(tc, shift=UP * 0.1), run_time=0.8)
            v.wait_until("spur")
            self.play(Create(base), run_time=0.3)
            for i in (1, 2):
                self.play(GrowFromEdge(bars[i][0], LEFT), FadeIn(bars[i][1]), FadeIn(bars[i][2]), run_time=0.7)
            v.wait_until("cmp")
            self.play(GrowFromEdge(bars[0][0], LEFT), FadeIn(bars[0][1]), FadeIn(bars[0][2]), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(m, shift=LEFT * 0.1) for m in mult], lag_ratio=0.4), run_time=1.0)
        self.wait(0.6)
        self.clear(run_time=0.7)
