import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *

COAX = "#9CA3AF"


class EthernetHistory(APLScene):
    def construct(self):
        self.tag = corner_tag("03 · Our reference: CAN bus", color=CAN)
        self.add(self.tag)
        self.chapter(4, "From coax to one pair", "Ethernet's long road to the field")

        # ------------------------------------------------------------ 1973: a shared coaxial "ether"
        card = name_card("Bob Metcalfe", "1973 · Xerox PARC", "a shared cable, the 'ether'", BLUE).to_corner(UR, buff=0.4).shift(DOWN * 0.1)
        y_bus = 0.2
        coax = VGroup(Line([-6.3, y_bus, 0], [6.3, y_bus, 0], stroke_color=COAX, stroke_width=9),
                      Line([-6.3, y_bus, 0], [6.3, y_bus, 0], stroke_color="#4B5563", stroke_width=3))
        ends = VGroup(*[resistor(0.5, color=COAX).rotate(PI / 2).move_to([x, y_bus - 0.45, 0]) for x in (-6.3, 6.3)])
        xs = [-4.6, -2.3, 0.0, 2.3, 4.6]
        pcs = VGroup(*[device("", "device-desktop", BLUE, width=1.05, height=0.85).move_to([x, y_bus + 1.35, 0]) for x in xs])
        taps = VGroup(*[Line([x, y_bus + 0.92, 0], [x, y_bus + 0.08, 0], stroke_color=COAX, stroke_width=3) for x in xs])
        tap_dots = VGroup(*[Dot([x, y_bus, 0], radius=0.08, color=COAX) for x in xs])
        csma = VGroup(T("listen before talking", size=18, color=TEXT), T("·", size=18, color=MUTED),
                      T("if two talk at once: collision, back off, retry", size=18, color=TEXT)).arrange(RIGHT, buff=0.2).move_to([0, -1.6, 0])
        csma_t = T("carrier sense multiple access with collision detection (CSMA/CD)", size=16, color=MUTED).next_to(csma, DOWN, buff=0.15)
        wa, wb = ValueTracker(0.0), ValueTracker(0.0)

        def fronts():
            g = VGroup()
            ra, rb = wa.get_value(), wb.get_value()
            if ra > 0:
                g.add(Line([max(-6.3, xs[0] - ra), y_bus, 0], [min(6.3, xs[0] + ra), y_bus, 0], stroke_color=BLUE, stroke_width=7))
            if rb > 0:
                g.add(Line([max(-6.3, xs[4] - rb), y_bus, 0], [min(6.3, xs[4] + rb), y_bus, 0], stroke_color=VIOLET, stroke_width=7))
            if ra > 0 and rb > 0 and xs[0] + ra > xs[4] - rb:
                lo, hi = xs[4] - rb, xs[0] + ra
                g.add(Line([lo, y_bus, 0], [hi, y_bus, 0], stroke_color=DANGER, stroke_width=11))
            return g

        fr = always_redraw(fronts)
        boom = VGroup(icon("alert-triangle", DANGER, 0.6), T("collision", size=20, color=DANGER, weight=BOLD)).arrange(RIGHT, buff=0.15).move_to([0, y_bus - 0.75, 0])
        with self.voice(
            "{origin}Ethernet itself started out as a party line, not so different from CAN. {parc}In 1973, at Xerox PARC, "
            "Bob Metcalfe sketched a network in which every computer tapped into one shared coaxial cable: the 'ether'. "
            "{csma}Before sending, a station listened. If two started at the same moment, their signals collided, and both "
            "backed off and tried again later: carrier sense, multiple access, with collision detection."
        ) as v:
            v.wait_until("parc")
            self.play(FadeIn(card, shift=LEFT * 0.2), run_time=0.7)
            self.play(Create(coax), FadeIn(ends), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.15) for p in pcs], lag_ratio=0.12), Create(taps), FadeIn(tap_dots), run_time=1.3)
            v.wait_until("csma")
            self.add(fr)
            self.play(wa.animate.set_value(6.0), wb.animate.set_value(6.0), run_time=2.2, rate_func=linear)
            self.play(FadeIn(boom, scale=0.7), FadeIn(csma), FadeIn(csma_t), run_time=0.8)
        self.remove(fr)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the slot time: the round trip, paid once per frame
        ax0, ax1 = -5.6, 5.6
        ya, yb = 1.7, -1.2
        la = T("station A", size=18, color=BLUE, weight=BOLD).next_to([ax0, ya + 0.35, 0], UP, buff=0.05)
        lb = T("station B, far end", size=18, color=VIOLET, weight=BOLD).next_to([ax1, ya + 0.35, 0], UP, buff=0.05)
        cable_l = Line([ax0, ya, 0], [ax1, ya, 0], stroke_color=COAX, stroke_width=6)
        t_axis = Arrow([ax0, ya - 0.2, 0], [ax0, yb - 0.6, 0], buff=0, stroke_width=2.5, color=DIM, tip_length=0.12)
        t_lbl = T("time ↓", size=16, color=MUTED).next_to(t_axis, LEFT, buff=0.1)
        b_axis = Line([ax1, ya - 0.2, 0], [ax1, yb - 0.6, 0], stroke_color=DIM, stroke_width=2.5)
        go = Arrow([ax0, ya - 0.25, 0], [ax1, ya - 1.45, 0], buff=0, stroke_width=4, color=BLUE, tip_length=0.15)
        back = Arrow([ax1, ya - 1.45, 0], [ax0, yb, 0], buff=0, stroke_width=4, color=DANGER, tip_length=0.15)
        b_starts = T("B starts just before A's signal arrives", size=16, color=VIOLET).next_to([ax1, ya - 1.45, 0], LEFT, buff=0.15)
        frame_bar = Rectangle(width=0.5, height=ya - 0.25 - yb, fill_color=BLUE, fill_opacity=0.35, stroke_color=BLUE, stroke_width=2)
        frame_bar.move_to([ax0 + 0.25, (ya - 0.25 + yb) / 2, 0])
        fb_l = VGroup(T("A must still be sending", size=17, color=BLUE, weight=BOLD), T("when the collision news returns", size=16, color=MUTED)).arrange(DOWN, buff=0.04, aligned_edge=LEFT)
        fb_l.next_to(frame_bar, RIGHT, buff=0.2).shift(DOWN * 0.9)
        rule = TeX(r"t_{\text{frame}} \;\ge\; t_{\text{round trip}}", size=40).move_to([2.2, -2.35, 0])
        nums = VGroup(T("minimum frame: 64 bytes = 512 bits", size=20, color=TEXT, weight=BOLD),
                      T("= 51.2 µs at 10 Mbit/s → networks a few km across", size=18, color=MUTED)).arrange(DOWN, buff=0.08).move_to([2.2, -3.2, 0])
        with self.voice(
            "{rt}And it carried the very same physical constraint as CAN. A sender must still be transmitting when the news "
            "of a collision returns from the far end of the cable. {slot}That's why classic Ethernet frames have a minimum "
            "length of sixty-four bytes: 512 bits, or 51.2 microseconds at ten megabits per second — enough to cover the "
            "round trip of a network a few kilometers across, repeaters included. {can}CAN pays for the round trip in every "
            "single bit; early Ethernet paid for it once per frame."
        ) as v:
            self.play(Create(cable_l), FadeIn(la), FadeIn(lb), GrowArrow(t_axis), FadeIn(t_lbl), Create(b_axis), run_time=1.0)
            self.play(GrowArrow(go), run_time=1.2)
            self.play(FadeIn(b_starts), GrowArrow(back), run_time=1.2)
            self.play(GrowFromEdge(frame_bar, UP), FadeIn(fb_l), run_time=1.0)
            v.wait_until("slot")
            self.play(Write(rule), run_time=1.0)
            self.play(FadeIn(nums, shift=UP * 0.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the escape: switches and full duplex
        sw = device("switch", "router", APL, width=2.0, height=1.15, label_size=19).move_to([0, 0.35, 0])
        angs = np.linspace(PI * 0.15, PI * 0.85, 5)
        nodes = VGroup()
        links = VGroup()
        arrows = VGroup()
        for i, a in enumerate(np.concatenate([angs, angs + PI])):
            p = sw.get_center() + np.array([4.6 * np.cos(a), 1.95 * np.sin(a), 0])
            nd = device("", "device-desktop", APL, width=0.9, height=0.72).move_to(p)
            nodes.add(nd)
            ln = Line(sw.get_center(), p, stroke_color=APL, stroke_width=3)
            ln.put_start_and_end_on(sw.get_center() + (p - sw.get_center()) * 0.28, p - (p - sw.get_center()) * 0.12)
            links.add(ln)
        nocol = VGroup(T("each cable: exactly two devices", size=19, color=TEXT), T("full duplex → collisions impossible", size=19, color=GOOD, weight=BOLD),
                       T("→ no round-trip limit; only the signal quality matters", size=19, color=APL, weight=BOLD)).arrange(DOWN, buff=0.1)
        nocol.move_to([0, -3.15, 0])
        with self.voice(
            "{switch}Then Ethernet escaped. Twisted-pair cabling arrived in 1990, first with hubs, then with switches. Each "
            "cable now connected exactly two devices, and with full duplex, standardized in the late 1990s, collisions became "
            "impossible. {free}With nothing to detect, the round-trip constraint simply vanished. From then on, the length "
            "of a link is limited by one thing only: how well a signal survives the cable."
        ) as v:
            self.play(FadeIn(sw), run_time=0.6)
            self.play(LaggedStart(*[AnimationGroup(Create(l), FadeIn(n)) for l, n in zip(links, nodes)], lag_ratio=0.1), run_time=2.0)
            self.play(FadeIn(nocol[0]), FadeIn(nocol[1]), run_time=0.8)
            v.wait_until("free")
            self.play(FadeIn(nocol[2], shift=UP * 0.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ fifty years of physical layers
        tl = timeline([(1973, "experimental Ethernet,\n2.94 Mbit/s on coax", BLUE), (1983, "IEEE 802.3:\n10 Mbit/s thick coax", BLUE),
                       (1990, "10BASE-T: Manchester,\n2 pairs", PINK), (1995, "100BASE-TX: MLT-3,\n3 levels", VIOLET),
                       (1999, "1000BASE-T: PAM-5,\n4 pairs, echo-cancelled", VIOLET), (2015, "100BASE-T1:\n1 pair, cars", APL),
                       (2019, "10BASE-T1L:\n1 pair, 1 km", APL)], x0=-5.5, x1=5.5, y=-0.2, size=17, even=True)
        goal = VGroup(T("not speed —", size=26, color=MUTED, weight=BOLD), T("distance", size=26, color=APL, weight=BOLD)).arrange(RIGHT, buff=0.2).move_to([3.6, 2.65, 0])
        with self.voice(
            "{phy}That turned Ethernet into a story of ever cleverer physical layers. {t10}Manchester code over two pairs in "
            "1990. {t100}Three-level MLT-3 for a hundred megabits in 1995. {t1000}Five levels, echo cancellation and four "
            "pairs for gigabit Ethernet in 1999. {t1}In 2015, a single pair for cars. {t1l}And in 2019, 10BASE-T1L applied "
            "the whole toolbox to a different goal: not speed, but distance."
        ) as v:
            self.play(Create(tl[0]), FadeIn(tl[1][0]), FadeIn(tl[1][1]), run_time=1.2)
            for i, tag in ((2, "t10"), (3, "t100"), (4, "t1000"), (5, "t1"), (6, "t1l")):
                v.wait_until(tag)
                self.play(FadeIn(tl[1][i], shift=UP * 0.1), run_time=0.6)
            self.play(FadeIn(goal, shift=DOWN * 0.1), Indicate(tl[1][6], color=APL, scale_factor=1.1), run_time=1.0)
        self.wait(0.4)
        self.clear(run_time=0.7)
