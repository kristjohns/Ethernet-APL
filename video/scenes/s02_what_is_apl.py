import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.props import four_walls_layout
from apl.style import *
from apl.widgets import *


def spec_card(icon_name, value, sub, color=APL, w=3.75, h=1.75):
    box = panel(w, h)
    ic = icon(icon_name, color, 0.55).move_to(box.get_corner(UL) + RIGHT * 0.55 + DOWN * 0.55)
    val = T(value, size=36, color=TEXT, weight=BOLD)
    sb = T(sub, size=21, color=MUTED)
    txt = VGroup(val, sb).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    max_w = w - 1.35
    if txt.width > max_w:
        txt.scale_to_fit_width(max_w)
    txt.next_to(ic, RIGHT, buff=0.28).shift(DOWN * 0.22)
    accent = Line(box.get_corner(DL) + RIGHT * 0.18, box.get_corner(DR) + LEFT * 0.18, stroke_color=color, stroke_width=3)
    accent.shift(UP * 0.02)
    return VGroup(box, accent, ic, txt)


class WhatIsAPL(APLScene):
    def construct(self):
        sw, field_zone, fz_hatch, fz_lbl, fdevs, walls, wall_lbls = four_walls_layout()
        self.tag = corner_tag("01 · The last kilometer")
        self.add(self.tag, sw, field_zone, fz_hatch, fz_lbl, fdevs, walls, wall_lbls)

        # ------------------------------------------------------------ break the walls
        rng = np.random.default_rng(3)

        def crumble(wall, lbl):
            anims = []
            for b in wall:
                dx = rng.normal(0.6, 0.5)
                dy = rng.uniform(-3.5, -1.5)
                anims.append(b.animate.shift(RIGHT * dx + UP * dy).rotate(rng.uniform(-2.5, 2.5)).set_opacity(0))
            return AnimationGroup(LaggedStart(*anims, lag_ratio=0.004), FadeOut(lbl, shift=DOWN * 0.3), run_time=1.0)

        beam = packet(APL, 0.12, 5).move_to(sw.get_right())
        trail = TracedPath(beam.get_center, stroke_color=APL, stroke_width=6, dissipating_time=0.35, stroke_opacity=[0, 1])
        with self.voice(
            "{apl}Ethernet-APL — the Advanced Physical Layer — was designed to break all four walls. "
            "{phys}The key word is “physical”."
        ) as v:
            self.add(trail, beam)
            xs = [w.get_center()[0] for w in walls]
            for i, x in enumerate(xs):
                self.play(beam.animate.move_to([x - 0.6, -0.2, 0]), run_time=0.35, rate_func=linear)
                self.play(crumble(walls[i], wall_lbls[i]), beam.animate.move_to([x + 0.6, -0.2, 0]), run_time=0.55)
            self.play(beam.animate.move_to(field_zone.get_left() + RIGHT * 0.15), run_time=0.3, rate_func=linear)
            self.play(Flash(beam.get_center(), color=APL, flash_radius=0.5),
                      *[d.box.animate.set_fill(APL, opacity=0.25) for d in fdevs], run_time=0.6)
            self.play(*[d.box.animate.set_fill(PANEL, opacity=1) for d in fdevs], FadeOut(beam), run_time=0.5)
            v.wait_until("phys")
        self.remove(trail)
        self.clear(run_time=0.6)
        self.chapter(2, "One new layer", "Everything above the copper stays the same")

        # ------------------------------------------------------------ the stack
        layer_w, layer_h = 7.0, 0.82
        names = [("L7", "Application"), ("L4", "Transport"), ("L3", "Network"), ("L2", "Data link"), ("L1", "Physical")]
        rects = VGroup(*[RoundedRectangle(width=layer_w, height=layer_h * (1.55 if i == 0 else 1.0), corner_radius=0.12,
                                          fill_color=PANEL, fill_opacity=1, stroke_color=PANEL_EDGE, stroke_width=1.8)
                         for i in range(len(names))]).arrange(DOWN, buff=0.12).move_to(LEFT * 0.35 + DOWN * 0.25)
        layers = VGroup()
        for r, (num, nm) in zip(rects, names):
            lbl = VGroup(T(num, size=18, color=DIM, weight=BOLD), T(nm, size=20, color=MUTED)).arrange(RIGHT, buff=0.15)
            lbl.next_to(r, LEFT, buff=0.25)
            layers.add(VGroup(r, lbl))
        contents = [
            None,
            T("TCP · UDP", size=24, color=TEXT),
            T("IP", size=24, color=TEXT),
            T("Ethernet MAC frames · IEEE 802.3", size=24, color=TEXT),
        ]
        for i in range(1, 4):
            contents[i].move_to(layers[i][0])
        old_phy = VGroup(T("100BASE-TX", size=24, color=BLUE, weight=BOLD),
                         T("4 wires · 100 m · no power · not Ex", size=20, color=MUTED)).arrange(RIGHT, buff=0.3)
        old_box = layers[4][0].copy().set_stroke(BLUE, 2.2)
        old_phy.scale_to_fit_width(min(old_phy.width, layer_w - 0.5)).move_to(old_box)
        new_box = layers[4][0].copy().set_fill(APL, 0.14).set_stroke(APL, 2.6)
        new_phy = VGroup(T("Ethernet-APL", size=26, color=APL, weight=BOLD),
                         T("2 wires · 1000 m · power · intrinsically safe", size=20, color=TEXT)).arrange(RIGHT, buff=0.3)
        new_phy.scale_to_fit_width(min(new_phy.width, layer_w - 0.5)).move_to(new_box)
        new_glow = glow(new_box, APL, layers=5, max_width=16, max_opacity=0.3)

        apps = ["PROFINET", "EtherNet/IP", "HART-IP", "OPC UA", "Modbus TCP"]
        app_chips = VGroup(*[chip(a, APL, size=19, height=0.46) for a in apps])
        web = chip("web server", GOOD, size=19, height=0.46)
        row1 = VGroup(*app_chips[:3]).arrange(RIGHT, buff=0.14)
        row2 = VGroup(*app_chips[3:], web).arrange(RIGHT, buff=0.14)
        VGroup(row1, row2).arrange(DOWN, buff=0.12).move_to(layers[0][0])

        checks = VGroup(*[check(GOOD, 0.3, 5).next_to(layers[i][0], RIGHT, buff=0.25) for i in range(4)])
        unchanged = T("unchanged", size=22, color=GOOD, weight=BOLD).rotate(-PI / 2).next_to(checks, RIGHT, buff=0.12)

        with self.voice(
            "APL replaces only the bottom layer of the network stack: {cu}the copper, the voltages, the power, and the "
            "safety rules. {above}Everything above it is unchanged Ethernet: {mac}the same frames and MAC addresses, "
            "{ip}IP, TCP and UDP, {apps}and the industrial protocols on top — PROFINET, EtherNet/IP, HART-IP, OPC UA, "
            "Modbus TCP — {web}even a web server inside the instrument."
        ) as v:
            self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.15) for l in layers[::-1]], lag_ratio=0.12), run_time=1.0)
            self.play(FadeIn(old_box), FadeIn(old_phy), run_time=0.5)
            v.wait_until("cu")
            self.play(VGroup(old_box, old_phy).animate.shift(LEFT * 9).set_opacity(0), run_time=0.9, rate_func=rush_into)
            new_grp = VGroup(new_glow, new_box, new_phy).shift(RIGHT * 9)
            self.play(new_grp.animate.shift(LEFT * 9), run_time=0.9, rate_func=rush_from)
            v.wait_until("above")
            self.play(LaggedStart(*[Create(c) for c in checks[::-1]], lag_ratio=0.15), FadeIn(unchanged), run_time=0.9)
            v.wait_until("mac")
            self.play(FadeIn(contents[3], shift=UP * 0.1), run_time=0.5)
            v.wait_until("ip")
            self.play(FadeIn(contents[2], shift=UP * 0.1), FadeIn(contents[1], shift=UP * 0.1), run_time=0.6)
            v.wait_until("apps")
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in app_chips], lag_ratio=0.5), run_time=v.until("web", 1.0))
            self.play(FadeIn(web, scale=0.8), run_time=0.5)

        self.clear(run_time=0.6)

        # ------------------------------------------------------------ what APL is made of
        head = H("Ethernet-APL", size=56, color=APL).to_edge(UP, buff=0.95)
        eq = T("=", size=44, color=MUTED).next_to(head, DOWN, buff=0.25)

        def block(title, std, lines, color):
            b = panel(3.9, 2.35, edge=color)
            tt = T(title, size=30, color=color, weight=BOLD)
            ss = T(std, size=18, color=MUTED)
            ls = VGroup(*[T(l, size=19, color=TEXT) for l in lines]).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
            content = VGroup(tt, ss, ls).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
            content.move_to(b)
            return VGroup(b, content)

        b1 = block("10BASE-T1L", "IEEE 802.3cg-2019", ["10 Mbit/s, full duplex", "one twisted pair", "up to 1000 m"], APL)
        b2 = block("Port profiles", "IEC TS 63444", ["power over the pair", "power classes", "cables & lengths"], POWER)
        b3 = block("2-WISE", "IEC TS 60079-47", ["intrinsic safety", "for 2-wire Ethernet", "no IS calculations"], HAZARD)
        row = VGroup(b1, b2, b3).arrange(RIGHT, buff=0.55).next_to(eq, DOWN, buff=0.3)
        plus = VGroup(*[T("+", size=44, color=MUTED).move_to(0.5 * (row[i].get_right() + row[i + 1].get_left())) for i in range(2)])
        orgs_lbl = T("APL project · 2018–2022", size=20, color=MUTED, weight=BOLD)
        orgs = VGroup(*[chip(o, TEXT, size=18, height=0.44, fill_opacity=0.06) for o in
                        ["FieldComm Group", "ODVA", "OPC Foundation", "PROFIBUS & PROFINET Int."]]).arrange(RIGHT, buff=0.18)
        org_grp = VGroup(orgs_lbl, orgs).arrange(DOWN, buff=0.15).next_to(row, DOWN, buff=0.45)

        with self.voice(
            "{base}Its foundation is 10BASE-T1L, part of the IEEE 802.3cg standard from 2019: ten megabits per second, "
            "full duplex, over a single twisted pair, for up to a kilometer. "
            "{proj}On top of that, the APL project — a joint effort of FieldComm Group, ODVA, the OPC Foundation, "
            "and PROFIBUS and PROFINET International — {prof}added what process plants need: port profiles that define "
            "how power is delivered over the same pair, standardized as IEC TS 63444, {wise}and an intrinsic-safety "
            "concept called 2-WISE, published as IEC TS 60079-47."
        ) as v:
            self.play(FadeIn(head, shift=DOWN * 0.15), FadeIn(eq), run_time=0.8)
            v.wait_until("base")
            self.play(FadeIn(b1, shift=UP * 0.2), run_time=0.8)
            v.wait_until("proj")
            self.play(FadeIn(orgs_lbl), LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in orgs], lag_ratio=0.4), run_time=2.4)
            v.wait_until("prof")
            self.play(FadeIn(plus[0]), FadeIn(b2, shift=UP * 0.2), run_time=0.8)
            v.wait_until("wise")
            self.play(FadeIn(plus[1]), FadeIn(b3, shift=UP * 0.2), run_time=0.8)

        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the result
        cards = VGroup(
            spec_card("arrows-exchange", "10 Mbit/s", "full duplex, per link"),
            spec_card("plug", "2 wires", "one twisted pair"),
            spec_card("bolt", "Power + data", "on the same pair", POWER),
            spec_card("ruler-measure", "1000 m", "trunk"),
            spec_card("route-2", "200 m", "spur to the device"),
            spec_card("shield-check", "Zone 0", "intrinsically safe", HAZARD),
        ).arrange_in_grid(rows=2, cols=3, buff=(0.35, 0.35)).move_to(DOWN * 0.15)
        with self.voice(
            "{res}The result: two wires, ten megabits per second in both directions, power and data together, "
            "{len}trunks up to one kilometer, {zone}and intrinsically safe spurs that reach all the way into Zone 0."
        ) as v:
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards[:3]], lag_ratio=0.45), run_time=v.until("len", 1.5))
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards[3:5]], lag_ratio=0.5), run_time=v.until("zone", 1.0))
            self.play(FadeIn(cards[5], shift=UP * 0.2), run_time=0.7)
        self.wait(0.8)
        self.clear(run_time=0.8)
