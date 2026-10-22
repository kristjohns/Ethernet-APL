import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *


def plant_map():
    """Safe area + hazardous area with power switch, trunk, field switch, spurs and instruments."""
    g = {}
    safe = Rectangle(width=4.45, height=7.0, stroke_width=0, fill_color="#0F1A30", fill_opacity=1).move_to([-4.88, -0.25, 0])
    haz = Rectangle(width=9.75, height=7.0, stroke_width=0, fill_color=HAZARD, fill_opacity=0.05).move_to([2.23, -0.25, 0])
    haz_h = hatch(haz, HAZARD, spacing=0.34, opacity=0.13)
    border = DashedLine([-2.65, 3.25, 0], [-2.65, -3.75, 0], dash_length=0.12, stroke_color=HAZARD, stroke_width=2)
    safe_lbl = T("SAFE AREA · control room", size=17, color=MUTED, weight=BOLD).move_to([-4.88, 2.95, 0])
    haz_lbl = T("HAZARDOUS AREA · Zone 1", size=17, color=HAZARD, weight=BOLD).move_to([0.3, 2.95, 0])
    g["areas"] = VGroup(safe, haz, haz_h, border, safe_lbl, haz_lbl)

    dcs = device("Plant network", "server", BLUE, width=2.3, height=1.15, label_size=18, sub="DCS · PLC · IT").move_to([-4.9, 1.75, 0])
    psw = device("APL power switch", "router", APL, width=2.4, height=1.25, label_size=18).move_to([-4.9, -0.65, 0])
    eth = Line(dcs.get_bottom(), psw.get_top(), stroke_color=BLUE, stroke_width=5)
    g["dcs"], g["psw"], g["eth"] = dcs, psw, eth

    fsw = device("APL field switch", "router", APL, width=2.2, height=1.4, label_size=18).move_to([1.35, -0.65, 0])
    trunk = Line(psw.get_right(), fsw.get_left(), stroke_color=APL, stroke_width=7)
    g["fsw"], g["trunk"] = fsw, trunk
    t_up = T("TRUNK  ≤ 1000 m", size=20, color=APL, weight=BOLD).next_to(trunk, UP, buff=0.22)
    t_dn = VGroup(T("2.4 Vpp · data + power", size=16, color=MUTED), T("up to 92 W", size=16, color=POWER)).arrange(DOWN, buff=0.06)
    t_dn.next_to(trunk, DOWN, buff=0.22)
    t_up.set_x(-1.2)
    t_dn.set_x(-1.2)
    g["t_lbl"] = VGroup(t_up, t_dn)

    specs = [("PT", "gauge"), ("TT", "temperature"), ("FT", "droplet"), ("LT", "ripple"), ("Valve", "settings"), ("AT", "flask")]
    devs = VGroup()
    spurs = VGroup()
    ys = np.linspace(2.35, -3.2, len(specs))
    for (nm, ic), y in zip(specs, ys):
        d = device(nm, ic, APL, width=1.3, height=0.86, label_size=16, icon_scale=0.4).move_to([5.85, y, 0])
        devs.add(d)
        port = fsw.get_right() + UP * (0.45 - 0.9 * (len(spurs) / (len(specs) - 1)))
        sp = VMobject().set_points_as_corners([port, port + RIGHT * 0.55, d.get_left()]).set_stroke(APL, 3.5)
        spurs.add(sp)
    g["devs"], g["spurs"] = devs, spurs
    s_lbl = VGroup(T("SPURS  ≤ 200 m", size=20, color=APL, weight=BOLD),
                   T("1.0 Vpp · intrinsically safe (Ex ia)", size=16, color=MUTED)).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    s_lbl.move_to([3.1, 2.2, 0])
    g["s_lbl"] = s_lbl
    z0 = RoundedRectangle(width=1.75, height=2.25, corner_radius=0.18, stroke_color=DANGER, stroke_width=2,
                          fill_color=DANGER, fill_opacity=0.08).move_to(VGroup(devs[3], devs[5]).get_center())
    z0_h = hatch(z0, DANGER, spacing=0.18, opacity=0.25)
    z0_lbl = T("Zone 0", size=16, color=DANGER, weight=BOLD).next_to(z0, LEFT, buff=0.1).shift(DOWN * 0.55)
    z0_lbl = VGroup(BackgroundRectangle(z0_lbl, color=BG, fill_opacity=0.9, buff=0.05), z0_lbl)
    g["z0"] = VGroup(z0, z0_h, z0_lbl)
    return g


class APLTopology(APLScene):
    def construct(self):
        self.chapter(4, "Inside Ethernet-APL", "One pair · both directions · power included")

        # ------------------------------------------------------------ bus -> point-to-point
        nodes = VGroup(*[device(f"Device {i + 1}", "cpu", CAN, width=1.5, height=1.05, label_size=17) for i in range(5)])
        nodes.arrange(RIGHT, buff=0.55).move_to(UP * 1.7)
        bus = Line(LEFT * 6.2, RIGHT * 6.2, stroke_color=CAN, stroke_width=6).move_to(UP * 0.1)
        stubs = VGroup(*[Line(n.get_bottom(), [n.get_x(), bus.get_y(), 0], stroke_color=CAN, stroke_width=2.5) for n in nodes])
        bus_lbl = T("shared bus", size=20, color=CAN).next_to(bus, DOWN, buff=0.12).align_to(bus, RIGHT)
        sw = device("Switch", "router", APL, width=2.0, height=1.1, label_size=18).move_to(DOWN * 2.3)
        links = VGroup()
        for i, n in enumerate(nodes):
            port = sw.get_top() + RIGHT * (-0.7 + 0.35 * i)
            links.add(Line(n.get_bottom(), port, stroke_color=APL, stroke_width=3.5))
        with self.voice(
            "Now let's look at Ethernet-APL with the same eyes. {topo}First, topology. {nobus}There is no shared bus. "
            "{p2p}Every link connects exactly two ports, point to point, and switches tie the links together."
        ) as v:
            self.play(LaggedStart(*[FadeIn(n, shift=DOWN * 0.2) for n in nodes], lag_ratio=0.1), Create(bus), Create(stubs),
                      FadeIn(bus_lbl), run_time=1.4)
            v.wait_until("nobus")
            cracks = VGroup(*[Line(bus.point_from_proportion(a) + UP * 0.15, bus.point_from_proportion(a) + DOWN * 0.15,
                                   stroke_color=BG, stroke_width=10) for a in np.linspace(0.08, 0.92, 9)])
            self.play(FadeIn(cracks, lag_ratio=0.1), run_time=0.5)
            self.play(FadeOut(VGroup(bus, cracks, stubs, bus_lbl), shift=DOWN * 0.3), *[n.box.animate.set_stroke(APL) for n in nodes],
                      *[n[1].animate.set_stroke(APL) for n in nodes], run_time=0.8)
            v.wait_until("p2p")
            self.play(FadeIn(sw, shift=UP * 0.2), run_time=0.5)
            self.play(LaggedStart(*[Create(l) for l in links], lag_ratio=0.15), run_time=1.0)
            flows = VGroup(*[flow_along(l, n=2, color=APL, speed=0.55, radius=0.05) for l in links],
                           *[flow_along(l, n=2, color=VIOLET, speed=0.55, radius=0.05, reverse=True, phase=0.25) for l in links])
            self.add(flows)
            note = T("every link: exactly two ports", size=22, color=APL, weight=BOLD).next_to(sw, RIGHT, buff=0.5)
            self.play(FadeIn(note, shift=LEFT * 0.1), run_time=0.6)
        for f in flows:
            f.clear_updaters()
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the plant
        g = plant_map()
        with self.voice(
            "{plant}A typical plant uses a trunk-and-spur layout. {ps}In the safe area, an APL power switch connects to "
            "the plant network and feeds a trunk cable up to one kilometer long, {trunk}carrying both data and power, "
            "with a 2.4-volt peak-to-peak signal."
        ) as v:
            self.play(FadeIn(g["areas"]), run_time=1.0)
            v.wait_until("ps")
            self.play(FadeIn(g["dcs"], shift=DOWN * 0.2), run_time=0.5)
            self.play(Create(g["eth"]), FadeIn(g["psw"], shift=UP * 0.2), run_time=0.7)
            self.play(Create(g["trunk"]), FadeIn(g["fsw"]), run_time=1.2)
            v.wait_until("trunk")
            tg = glow(g["trunk"], APL, layers=5, max_width=16, max_opacity=0.25)
            data_r = flow_along(g["trunk"], n=6, color=APL, speed=0.35, radius=0.06)
            data_l = flow_along(g["trunk"], n=6, color=VIOLET, speed=0.35, radius=0.06, reverse=True, phase=0.08)
            pwr = flow_along(Line(g["trunk"].get_start() + DOWN * 0.0, g["trunk"].get_end()), n=10, color=POWER, speed=0.12, radius=0.035)
            eth_f = flow_along(g["eth"], n=3, color=BLUE, speed=0.6, radius=0.05)
            self.add(tg, data_r, data_l, pwr, eth_f)
            self.play(FadeIn(g["t_lbl"], shift=UP * 0.1), run_time=0.8)

        with self.voice(
            "{fs}Out in the hazardous area, a field switch takes that power and distributes it over spurs up to two "
            "hundred meters long. {spur}Each spur serves exactly one instrument, with a lower one-volt signal and "
            "intrinsically safe power."
        ) as v:
            self.play(Indicate(g["fsw"], color=APL, scale_factor=1.06), run_time=0.8)
            self.play(LaggedStart(*[Create(s) for s in g["spurs"]], lag_ratio=0.12),
                      LaggedStart(*[FadeIn(d, shift=LEFT * 0.2) for d in g["devs"]], lag_ratio=0.12), run_time=1.8)
            v.wait_until("spur")
            self.play(FadeIn(g["s_lbl"], shift=UP * 0.1), FadeIn(g["z0"]), run_time=1.0)

        with self.voice(
            "{own}And because every spur is its own link, every instrument gets its own ten megabits per second, in each "
            "direction, all the time. {nothing}Nothing is shared, so there's nothing to arbitrate."
        ) as v:
            sflows = VGroup()
            for s in g["spurs"]:
                sflows.add(flow_along(s, n=2, color=APL, speed=0.5, radius=0.045))
                sflows.add(flow_along(s, n=2, color=VIOLET, speed=0.5, radius=0.045, reverse=True, phase=0.3))
            self.add(sflows)
            rate = pill("10 Mbit/s ⇄ on every spur", APL, size=19).next_to(g["s_lbl"], DOWN, buff=0.25).align_to(g["s_lbl"], LEFT)
            self.play(FadeIn(rate, shift=UP * 0.1), run_time=0.8)
            v.wait_until("nothing")
            callout = VGroup(T("CAN:", size=20, color=CAN, weight=BOLD), T("one medium, shared by all", size=20, color=TEXT)).arrange(RIGHT, buff=0.15)
            callout2 = VGroup(T("APL:", size=20, color=APL, weight=BOLD), T("a private link per device", size=20, color=TEXT)).arrange(RIGHT, buff=0.15)
            box = VGroup(callout, callout2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            bg = panel(box.width + 0.5, box.height + 0.4).move_to(box)
            cbox = VGroup(bg, box).move_to([-0.6, -2.75, 0])
            self.play(FadeIn(cbox, shift=UP * 0.15), run_time=0.8)
        self.wait(0.6)
        for m in [data_r, data_l, pwr, eth_f, *sflows]:
            m.clear_updaters()
        self.clear(run_time=0.8)
