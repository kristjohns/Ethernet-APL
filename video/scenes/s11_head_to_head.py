import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.props import CAN_POINTS, can_curve, rate_length_chart
from apl.style import *
from apl.widgets import *


class HeadToHead(APLScene):
    def construct(self):
        self.chapter(6, "Head to head", "CAN bus vs. Ethernet-APL", color=TEXT)

        # ------------------------------------------------------------ bandwidth per device
        left = panel(6.5, 5.6).move_to([-3.5, -0.3, 0])
        right = panel(6.5, 5.6).move_to([3.5, -0.3, 0])
        lt = T("CAN · 10 nodes", size=26, color=CAN, weight=BOLD).next_to(left.get_top(), DOWN, buff=0.25)
        rt = T("Ethernet-APL · 10 devices", size=26, color=APL, weight=BOLD).next_to(right.get_top(), DOWN, buff=0.25)
        # CAN: bus with 10 nodes
        bus = Line([-6.2, 1.0, 0], [-0.8, 1.0, 0], stroke_color=CAN, stroke_width=5)
        cn = VGroup(*[Square(0.34, fill_color=CAN, fill_opacity=0.25, stroke_color=CAN, stroke_width=2).move_to([-5.9 + 0.57 * i, 1.6, 0]) for i in range(10)])
        cst = VGroup(*[Line(s.get_bottom(), [s.get_x(), 1.0, 0], stroke_color=CAN, stroke_width=2) for s in cn])
        # APL: switch with 10 devices
        swc = np.array([3.5, 0.25, 0])
        sw = RoundedRectangle(width=1.1, height=0.55, corner_radius=0.1, fill_color=APL, fill_opacity=0.25, stroke_color=APL, stroke_width=2).move_to(swc)
        an = VGroup()
        al = VGroup()
        for i in range(10):
            ang = PI * (0.08 + 0.84 * i / 9)
            p = swc + np.array([2.4 * np.cos(ang), 0.95 * np.sin(ang) + 0.55, 0])
            sq = Square(0.34, fill_color=APL, fill_opacity=0.25, stroke_color=APL, stroke_width=2).move_to(p)
            an.add(sq)
            al.add(Line(swc + UP * 0.27, sq.get_bottom(), stroke_color=APL, stroke_width=2))
        # per-device bar chart (linear)
        scale = 5.4 / 10.0
        def bar(x0, y, val, col):
            return Rectangle(width=max(0.035, val * scale), height=0.5, fill_color=col, fill_opacity=0.85, stroke_width=0).move_to([x0, y, 0], aligned_edge=LEFT)
        b_can = bar(-6.2, -1.45, 0.1, CAN)
        b_apl_tx = bar(0.8, -1.2, 10, APL)
        b_apl_rx = bar(0.8, -1.8, 10, VIOLET)
        l_can = VGroup(T("≈ 0.1 Mbit/s per node", size=22, color=CAN, weight=BOLD), T("1 Mbit/s shared, one talker at a time", size=17, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        l_can.next_to(b_can, RIGHT, buff=0.2)
        l_apl = VGroup(T("10 Mbit/s out", size=18, color=BG, weight=BOLD).move_to(b_apl_tx), T("10 Mbit/s in", size=18, color=BG, weight=BOLD).move_to(b_apl_rx))
        l_apl2 = T("per device, simultaneously", size=17, color=MUTED).next_to(b_apl_rx, DOWN, buff=0.15).align_to(b_apl_rx, LEFT)
        ratio = T("≈ 100 × more per device, in each direction", size=24, color=TEXT, weight=BOLD).move_to(DOWN * 3.55)
        with self.voice(
            "Let's put the two side by side. {bw}Bandwidth. On classic CAN, one megabit per second at most — and "
            "that's at forty meters — {share}shared by every node on the bus. With ten nodes, each gets, on average, a "
            "tenth. {apl}On APL, every device has a private ten megabits per second, in each direction."
        ) as v:
            self.play(FadeIn(left), FadeIn(right), FadeIn(lt), FadeIn(rt), run_time=0.7)
            v.wait_until("bw")
            self.play(Create(bus), LaggedStart(*[FadeIn(c) for c in cn], lag_ratio=0.05), Create(cst), run_time=1.0)
            v.wait_until("share")
            self.play(GrowFromEdge(b_can, LEFT), FadeIn(l_can, shift=RIGHT * 0.1), run_time=0.9)
            v.wait_until("apl")
            self.play(FadeIn(sw), LaggedStart(*[AnimationGroup(Create(l), FadeIn(s)) for l, s in zip(al, an)], lag_ratio=0.06), run_time=1.0)
            self.play(GrowFromEdge(b_apl_tx, LEFT), GrowFromEdge(b_apl_rx, LEFT), run_time=1.0)
            self.play(FadeIn(l_apl), FadeIn(l_apl2), run_time=0.5)
            self.play(FadeIn(ratio, shift=UP * 0.1), run_time=0.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ distance
        ax, deco = rate_length_chart()
        VGroup(ax, deco).move_to(LEFT * 0.9 + DOWN * 0.15)
        line, pts = can_curve(ax)
        can_lbl = T("classic CAN", size=20, color=CAN, weight=BOLD).move_to(ax.c2p(2.15, 4.55))
        apl_line = Line(ax.c2p(1, 7), ax.c2p(3, 7), stroke_color=APL, stroke_width=6)
        apl_dash = DashedLine(ax.c2p(3, 7), ax.c2p(np.log10(2000), 7), dash_length=0.1, stroke_color=APL, stroke_width=4)
        apl_glow = glow(apl_line, APL, layers=5, max_width=16, max_opacity=0.3)
        apl_lbl = VGroup(T("10BASE-T1L / APL", size=20, color=APL, weight=BOLD), T("10 Mbit/s to 1 km (≈ 2 km in practice)", size=16, color=APL)).arrange(DOWN, buff=0.04, aligned_edge=LEFT)
        apl_lbl.next_to(ax.c2p(1.05, 7), UP, buff=0.12, aligned_edge=LEFT)
        gap = Polygon(ax.c2p(1.7, 6), ax.c2p(1.7, 7), ax.c2p(3, 7), ax.c2p(3, np.log10(5e4)), stroke_width=0, fill_color=APL, fill_opacity=0.08)
        prod = VGroup(
            VGroup(T("speed × distance", size=20, color=MUTED)),
            VGroup(T("CAN", size=20, color=CAN, weight=BOLD), T("≈ 50 Mbit/s·m", size=20, color=TEXT)).arrange(RIGHT, buff=0.15),
            VGroup(T("APL", size=20, color=APL, weight=BOLD), T("10 000 Mbit/s·m", size=20, color=TEXT)).arrange(RIGHT, buff=0.15),
            T("≈ 200 ×", size=34, color=TEXT, weight=BOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        prod_bg = panel(prod.width + 0.5, prod.height + 0.45)
        prod_box = VGroup(prod_bg, prod.move_to(prod_bg)).move_to([5.1, 0.1, 0])
        with self.voice(
            "{dist}Distance. Back to our chart of bit rate versus cable length. {can}CAN falls along that diagonal: "
            "double the length, halve the speed. {apl}10BASE-T1L stays flat at ten megabits per second, all the way to a "
            "kilometer. {prod}Its speed-distance product is about two hundred times higher."
        ) as v:
            self.play(Create(ax), FadeIn(deco), run_time=0.9)
            v.wait_until("can")
            self.play(FadeIn(pts), Create(line), FadeIn(can_lbl), run_time=1.2)
            v.wait_until("apl")
            self.play(Create(apl_line), FadeIn(apl_glow), run_time=1.3)
            self.play(Create(apl_dash), FadeIn(apl_lbl, shift=UP * 0.1), FadeIn(gap), run_time=0.8)
            v.wait_until("prod")
            self.play(FadeIn(prod_box, shift=LEFT * 0.2), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ frames & addressing
        def fields_bar(spec, y, total_w, x0=-5.6):
            g = VGroup()
            x = x0
            tot = sum(w for _, w, _ in spec)
            for nm, w, col in spec:
                ww = total_w * w / tot
                r = Rectangle(width=ww, height=0.62, fill_color=col, fill_opacity=0.85, stroke_color=BG, stroke_width=1.5).move_to([x + ww / 2, y, 0])
                t = T(nm, size=15, color=BG, weight=BOLD).move_to(r)
                if t.width > ww - 0.08:
                    t.scale_to_fit_width(max(0.05, ww - 0.08))
                g.add(VGroup(r, t))
                x += ww
            return g

        can_spec = [("SOF", 1, MUTED), ("ID · what", 4, CAN), ("ctrl", 1.6, "#FCD34D"), ("data ≤ 8 B", 5, GOOD), ("CRC", 2.2, VIOLET), ("ACK/EOF", 2, MUTED)]
        eth_spec = [("preamble", 2.2, MUTED), ("dest MAC · who", 2.6, APL), ("src MAC · who", 2.6, BLUE), ("type", 1.1, "#93C5FD"),
                    ("payload 46 – 1500 B  ·  IP header: where", 7.5, GOOD), ("FCS", 1.2, VIOLET)]
        cb = fields_bar(can_spec, 1.6, 6.0)
        eb = fields_bar(eth_spec, -0.25, 11.8)
        cl = T("CAN frame", size=22, color=CAN, weight=BOLD).next_to(cb, UP, buff=0.15).align_to(cb, LEFT)
        el = T("Ethernet frame", size=22, color=APL, weight=BOLD).next_to(eb, UP, buff=0.15).align_to(eb, LEFT)
        schem = T("(schematic, not to scale)", size=15, color=DIM).next_to(cl, RIGHT, buff=0.3)
        # payload to scale
        pay_w = 11.8 / 1500
        p_can = Rectangle(width=max(0.04, 8 * pay_w), height=0.42, fill_color=CAN, fill_opacity=0.9, stroke_width=0).move_to([-5.6, -2.05, 0], aligned_edge=LEFT)
        p_eth = Rectangle(width=1500 * pay_w, height=0.42, fill_color=APL, fill_opacity=0.9, stroke_width=0).move_to([-5.6, -2.65, 0], aligned_edge=LEFT)
        p_lbl = T("payload per frame, to scale", size=17, color=MUTED).next_to(p_can, UP, buff=0.15).align_to(p_can, LEFT)
        p_can_l = T("8 bytes", size=17, color=CAN, weight=BOLD).next_to(p_can, RIGHT, buff=0.12)
        p_eth_l = T("1500 bytes", size=17, color=BG, weight=BOLD).move_to(p_eth.get_right() + LEFT * 0.75)
        with self.voice(
            "{frames}Frames. A CAN frame carries up to eight bytes, and names its content. {eth}An Ethernet frame carries "
            "up to fifteen hundred bytes, and names its destination and its source with MAC addresses — {ip}while IP "
            "addresses let it be routed across the whole plant network, or beyond."
        ) as v:
            self.play(FadeIn(cl), FadeIn(schem), LaggedStart(*[FadeIn(f, shift=RIGHT * 0.1) for f in cb], lag_ratio=0.1), run_time=1.0)
            v.wait_until("eth")
            self.play(FadeIn(el), LaggedStart(*[FadeIn(f, shift=RIGHT * 0.1) for f in eb], lag_ratio=0.1), run_time=1.2)
            self.play(FadeIn(p_lbl), GrowFromEdge(p_can, LEFT), FadeIn(p_can_l), run_time=0.6)
            self.play(GrowFromEdge(p_eth, LEFT), FadeIn(p_eth_l), run_time=1.0)
            v.wait_until("ip")
            hl = SurroundingRectangle(eb[4], color=GOOD, buff=0.06, corner_radius=0.06)
            self.play(Create(hl), run_time=0.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ 1 MB transfer
        tx = Axes(x_range=[-1, 4, 1], y_range=[0, 4.4, 1], x_length=8.6, y_length=4.4,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": True},
                  y_axis_config={"include_ticks": False, "stroke_opacity": 0}).move_to([1.1, -0.45, 0])
        tl = tick_labels(tx, [-1, 0, 1, 2, 3, 4], "x", texts=["0.1 s", "1 s", "10 s", "100 s", "1000 s", "10 000 s"], size=16)
        tt = T("time to move 1 MB (log scale)", size=18, color=MUTED).next_to(tl, DOWN, buff=0.15).align_to(tx, RIGHT)
        rows = [("HART", 6667, GOOD, "≈ 1 h 51 min"), ("Fieldbus", 256, GOOD, "≈ 4 min"), ("CAN, 1 Mbit/s", 15, CAN, "≈ 15 s"), ("Ethernet-APL", 0.84, APL, "< 1 s")]
        bars, labs, vals = VGroup(), VGroup(), VGroup()
        for i, (nm, sec, col, txt) in enumerate(rows):
            y = 3.8 - i * 1.0
            w = tx.c2p(np.log10(sec), 0)[0] - tx.c2p(-1, 0)[0]
            b = Rectangle(width=w, height=0.6, fill_color=col, fill_opacity=0.8, stroke_width=0).move_to(tx.c2p(-1, y), aligned_edge=LEFT)
            bars.add(b)
            labs.add(T(nm, size=22, color=TEXT, weight=BOLD).next_to(tx.c2p(-1, y), LEFT, buff=0.25))
            vals.add(T(txt, size=22, color=col, weight=BOLD).next_to(b, RIGHT, buff=0.15))
        title = VGroup(icon("file-download", TEXT, 0.5), T("1 MB: a firmware update, or a diagnostic log", size=26, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.2)
        title.to_edge(UP, buff=0.95)
        with self.voice(
            "{mb}What does that mean in practice? Take one megabyte — say, a firmware update, or a diagnostic log. "
            "{hart}Over HART: almost two hours. {fb}Over a fieldbus: about four minutes. {can}Over CAN at one megabit per "
            "second: around fifteen seconds. {apl}Over Ethernet-APL: less than a second."
        ) as v:
            self.play(FadeIn(title, shift=DOWN * 0.1), Create(tx), FadeIn(tl), FadeIn(tt), FadeIn(labs), run_time=1.0)
            for i, tag in enumerate(["hart", "fb", "can", "apl"]):
                v.wait_until(tag)
                self.play(GrowFromEdge(bars[i], LEFT), FadeIn(vals[i], shift=RIGHT * 0.1), run_time=0.8)
            self.play(Flash(vals[3].get_center(), color=APL, flash_radius=0.6), run_time=0.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ summary table
        rows_t = [
            ("Topology", "shared bus, multidrop", "point-to-point, switched"),
            ("Medium access", "bitwise arbitration", "full duplex, no contention"),
            ("Bit rate", "≤ 1 Mbit/s, shared", "10 Mbit/s per link, each way"),
            ("Reach", "≈ 40 m at 1 Mbit/s", "1000 m trunk · 200 m spur"),
            ("Payload", "0–8 bytes (FD: 64)", "46–1500 bytes"),
            ("Addressing", "message ID = content", "MAC + IP = device"),
            ("Power", "not included", "over the same pair"),
            ("Hazardous areas", "case by case", "intrinsically safe (2-WISE)"),
            ("Higher layers", "CANopen · J1939 · DeviceNet", "PROFINET · EtherNet/IP · HART-IP · OPC UA"),
        ]
        cx = [-4.9, -1.25, 3.55]
        head = VGroup(T("", size=20), T("CAN (classic)", size=24, color=CAN, weight=BOLD), T("Ethernet-APL", size=24, color=APL, weight=BOLD))
        for j, h in enumerate(head):
            h.move_to([cx[j], 2.75, 0])
        trows = VGroup()
        for i, (a, b, c) in enumerate(rows_t):
            y = 2.15 - i * 0.6
            r = VGroup(T(a, size=19, color=MUTED, weight=BOLD).move_to([cx[0], y, 0]),
                       T(b, size=19, color=TEXT).move_to([cx[1], y, 0]),
                       T(c, size=19, color=TEXT).move_to([cx[2], y, 0]))
            if r[2].width > 5.4:
                r[2].scale_to_fit_width(5.4)
            trows.add(r)
        stripes = VGroup(*[Rectangle(width=13.2, height=0.56, fill_color=PANEL, fill_opacity=0.7 if i % 2 == 0 else 0.0, stroke_width=0).move_to([0, 2.15 - i * 0.6, 0]) for i in range(len(rows_t))])
        with self.voice(
            "{pwr}Power, and hazardous areas: CAN leaves both to the system designer. APL delivers power over the data "
            "pair, and it is intrinsically safe by design."
        ) as v:
            self.play(FadeIn(head), FadeIn(stripes), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.08) for r in trows], lag_ratio=0.18), run_time=2.6)
            hl = VGroup(SurroundingRectangle(trows[6], color=POWER, buff=0.06, corner_radius=0.06),
                        SurroundingRectangle(trows[7], color=HAZARD, buff=0.06, corner_radius=0.06))
            self.play(Create(hl), run_time=0.7)
        self.wait(1.5)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ where each one shines
        def column(title, color, icons, words, x):
            pnl = panel(6.2, 5.4).move_to([x, -0.35, 0])
            tt_ = T(title, size=28, color=color, weight=BOLD).next_to(pnl.get_top(), DOWN, buff=0.3)
            ics = VGroup(*[icon(i, color, 0.85) for i in icons]).arrange(RIGHT, buff=0.5).next_to(tt_, DOWN, buff=0.45)
            ws = VGroup(*[T(w, size=22, color=TEXT) for w in words]).arrange(DOWN, buff=0.2).next_to(ics, DOWN, buff=0.5)
            return VGroup(pnl, tt_, ics, ws)

        can_col = column("where CAN shines", CAN, ["car", "tractor", "robot", "truck"],
                         ["cheap: the controller is on the chip", "tiny, efficient frames", "hard, priority-based timing", "short buses in machines"], -3.45)
        apl_col = column("where Ethernet-APL shines", APL, ["building-factory-2", "flask", "gauge", "cloud"],
                         ["kilometer-long cables", "hazardous areas, Zone 0", "power over two wires", "rich data, native IP"], 3.45)
        with self.voice(
            "{simple}So is APL simply better? No. CAN is cheap: a CAN controller is built into countless "
            "microcontrollers, and its frames are tiny and efficient. {rt}Its arbitration gives hard, priority-based "
            "timing on short buses — exactly what vehicles and machines need."
        ) as v:
            self.play(FadeIn(can_col[0]), FadeIn(can_col[1]), LaggedStart(*[FadeIn(i, shift=UP * 0.15) for i in can_col[2]], lag_ratio=0.15), run_time=1.2)
            self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in can_col[3]], lag_ratio=0.3), run_time=v.until_end(1.5) * 0.8)
        with self.voice(
            "{apl}Ethernet-APL solves a different problem: long cables, hazardous areas, power over two wires, and rich "
            "data from every instrument — using the same IP-based networking as the rest of the enterprise."
        ) as v:
            self.play(FadeIn(apl_col[0]), FadeIn(apl_col[1]), LaggedStart(*[FadeIn(i, shift=UP * 0.15) for i in apl_col[2]], lag_ratio=0.15), run_time=1.2)
            self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in apl_col[3]], lag_ratio=0.3), run_time=v.until_end(1.5) * 0.8)
        self.wait(0.8)
        self.clear(run_time=0.7)
