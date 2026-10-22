import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *


def bubble(text, color, width=None):
    t = T(text, size=18, color=color, weight=BOLD)
    w = width or t.width + 0.4
    b = RoundedRectangle(width=w, height=0.48, corner_radius=0.2, fill_color=PANEL, fill_opacity=1, stroke_color=color, stroke_width=1.8)
    tail = Polygon([-0.1, 0, 0], [0.1, 0, 0], [0, -0.16, 0], fill_color=PANEL, fill_opacity=1, stroke_color=color, stroke_width=1.8)
    tail.next_to(b, DOWN, buff=-0.02)
    t.move_to(b)
    return VGroup(b, tail, t)


class Outro(APLScene):
    def construct(self):
        self.tag = corner_tag("Summary", color=TEXT)
        self.add(self.tag)
        self._chapters.append({"time": 0.0, "title": "Summary"})

        # ------------------------------------------------------------ party line vs private line
        lp = panel(6.4, 5.6).move_to([-3.45, -0.3, 0])
        rp = panel(6.4, 5.6).move_to([3.45, -0.3, 0])
        lt = VGroup(T("CAN", size=30, color=CAN, weight=BOLD), T("a party line", size=22, color=TEXT)).arrange(DOWN, buff=0.06).next_to(lp.get_top(), DOWN, buff=0.25)
        rt = VGroup(T("Ethernet-APL", size=30, color=APL, weight=BOLD), T("a private line per instrument", size=22, color=TEXT)).arrange(DOWN, buff=0.06).next_to(rp.get_top(), DOWN, buff=0.25)
        bus = Line([-6.2, -1.6, 0], [-0.7, -1.6, 0], stroke_color=CAN, stroke_width=5)
        cn = VGroup(*[device("", "cpu", CAN, width=0.85, height=0.8, icon_scale=0.55) for _ in range(5)]).arrange(RIGHT, buff=0.25).move_to([-3.45, -0.55, 0])
        cs = VGroup(*[Line(n.get_bottom(), [n.get_x(), -1.6, 0], stroke_color=CAN, stroke_width=2) for n in cn])
        crown = icon("crown", CAN, 0.4).next_to(cn[1], UP, buff=0.12)
        talk = bubble("ID 0x0A5", CAN).next_to(crown, UP, buff=0.08)
        waits = VGroup(*[bubble("…", DIM, 0.6).next_to(cn[i], UP, buff=0.15) for i in (0, 2, 3, 4)])
        lnote = T("highest priority wins · speed × distance ≈ const", size=17, color=MUTED).move_to([-3.45, -2.4, 0])
        sw = device("switch", "router", APL, width=1.3, height=0.8, label_size=14, icon_scale=0.45).move_to([3.45, -1.75, 0])
        an = VGroup()
        al = VGroup()
        for i in range(5):
            ang = PI * (0.12 + 0.76 * i / 4)
            p = np.array([3.45 + 2.3 * np.cos(ang), -1.75 + 2.25 * np.sin(ang), 0])
            d = device("", "gauge", APL, width=0.8, height=0.75, icon_scale=0.55).move_to(p)
            an.add(d)
            al.add(Line(sw.get_top(), d.get_bottom(), stroke_color=APL, stroke_width=2.5))
        rnote = T("10 Mbit/s each way · 1 km · power · Zone 0", size=17, color=MUTED).move_to([3.45, -2.6, 0])
        with self.voice(
            "{sum}So, to sum up. {can}CAN is a party line. Everyone shares one pair of wires, the most important voice "
            "always wins, and speed and distance trade off against each other."
        ) as v:
            self.play(FadeIn(lp), FadeIn(lt), run_time=0.6)
            self.play(Create(bus), LaggedStart(*[FadeIn(n) for n in cn], lag_ratio=0.1), Create(cs), run_time=1.0)
            v.wait_until("can")
            self.play(FadeIn(waits, lag_ratio=0.1), run_time=0.6)
            self.play(FadeIn(crown, shift=DOWN * 0.1), FadeIn(talk, shift=UP * 0.1), run_time=0.7)
            self.play(FadeIn(lnote), run_time=0.6)
        with self.voice(
            "{apl}Ethernet-APL is a private line from every instrument: point to point, full duplex, ten megabits per "
            "second up to a kilometer, power and data on the same two wires, and intrinsically safe all the way into Zone 0."
        ) as v:
            self.play(FadeIn(rp), FadeIn(rt), FadeIn(sw), run_time=0.6)
            self.play(LaggedStart(*[AnimationGroup(Create(l), FadeIn(d)) for l, d in zip(al, an)], lag_ratio=0.12), run_time=1.0)
            flows = VGroup(*[flow_along(l, n=2, color=APL, speed=0.6, radius=0.045) for l in al],
                           *[flow_along(l, n=2, color=VIOLET, speed=0.6, radius=0.045, reverse=True, phase=0.25) for l in al])
            self.add(flows)
            self.play(FadeIn(rnote), run_time=0.6)
        for f in flows:
            f.clear_updaters()
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ a century of ideas in one chip
        ideas = [("1880s", "Heaviside", "waves on a line", BLUE), ("1928", "Nyquist", "2B symbols per second", BLUE),
                 ("1948", "Shannon", "capacity and noise", BLUE), ("telephony", "the hybrid", "two directions, one pair", VIOLET),
                 ("1960", "Widrow & Hoff", "adaptive filters", GOOD), ("1965", "Lucky", "adaptive equalizers", GOOD)]
        cards = VGroup()
        for yr, who, what, col in ideas:
            lines = [T(yr, size=18, color=col, weight=BOLD), T(who, size=21, color=TEXT, weight=BOLD), T(what, size=15, color=MUTED)]
            for ln in lines:
                if ln.width > 1.85:
                    ln.scale_to_fit_width(1.85)
            c = VGroup(*lines).arrange(DOWN, buff=0.07)
            box = RoundedRectangle(width=2.08, height=1.35, corner_radius=0.14, fill_color=PANEL, fill_opacity=1, stroke_color=col, stroke_width=1.8)
            c.move_to(box)
            cards.add(VGroup(box, c))
        cards.arrange(RIGHT, buff=0.12).move_to(UP * 1.25)
        chip = VGroup(RoundedRectangle(width=3.2, height=1.4, corner_radius=0.16, fill_color=PANEL, fill_opacity=1, stroke_color=APL, stroke_width=3),
                      VGroup(T("10BASE-T1L PHY", size=24, color=APL, weight=BOLD), T("well under 0.1 W", size=18, color=MUTED)).arrange(DOWN, buff=0.08))
        chip[1].move_to(chip[0])
        chip.move_to(DOWN * 1.75)
        pins = VGroup(*[Line([x, chip[0].get_top()[1], 0], [x, chip[0].get_top()[1] + 0.18, 0], stroke_color=APL, stroke_width=3) for x in np.linspace(-1.3, 1.3, 9)],
                      *[Line([x, chip[0].get_bottom()[1], 0], [x, chip[0].get_bottom()[1] - 0.18, 0], stroke_color=APL, stroke_width=3) for x in np.linspace(-1.3, 1.3, 9)])
        arrows = VGroup(*[Arrow(c.get_bottom(), chip[0].get_top() + UP * 0.2 + RIGHT * (c.get_x() * 0.12), buff=0.08, stroke_width=2, color=DIM, tip_length=0.1) for c in cards])
        with self.voice(
            "{under}And underneath that private line sits more than a century of ideas: {ideas}Heaviside's waves, Nyquist's "
            "and Shannon's limits, the telephone hybrid, Widrow and Hoff's adaptive filters, Lucky's equalizers. {chip}All "
            "of it packed into a transceiver chip that runs on well under a tenth of a watt."
        ) as v:
            v.wait_until("ideas")
            self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.15) for c in cards], lag_ratio=0.3), run_time=v.until("chip", 3.0))
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.08), FadeIn(chip, shift=UP * 0.15), FadeIn(pins), run_time=1.2)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ four walls down + sensor to cloud
        walls = VGroup()
        for ic, txt, col in [("ruler-measure", "1000 m", BLUE), ("plug", "2 wires", APL), ("bolt", "power", POWER), ("flame", "Zone 0", HAZARD)]:
            g = VGroup(icon(ic, col, 0.6), T(txt, size=24, color=TEXT, weight=BOLD), check(GOOD, 0.3, 5)).arrange(RIGHT, buff=0.2)
            walls.add(g)
        walls.arrange(RIGHT, buff=0.7).move_to(UP * 1.9)
        chain_specs = [("gauge", "sensor", APL), ("router", "field switch", APL), ("router", "power switch", APL), ("server", "plant network", BLUE), ("cloud", "cloud", BLUE)]
        chain = VGroup(*[device(n, ic, col, width=1.85, height=1.25, label_size=17) for ic, n, col in chain_specs]).arrange(RIGHT, buff=0.75).move_to(DOWN * 1.0)
        links = VGroup(*[Line(chain[i].get_right(), chain[i + 1].get_left(), stroke_color=APL if i < 2 else BLUE, stroke_width=4) for i in range(4)])
        path = VMobject().set_points_as_corners([chain[0].get_center()] + [c.get_center() for c in chain[1:]])
        with self.voice(
            "{walls}The four walls are down. {lang}After decades of four to twenty milliamps, the process plant can finally "
            "speak the same language as the rest of the network — {cloud}from the sensor, all the way to the cloud."
        ) as v:
            self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in walls], lag_ratio=0.25), run_time=1.6)
            v.wait_until("lang")
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in chain], lag_ratio=0.15), run_time=1.2)
            self.play(LaggedStart(*[Create(l) for l in links], lag_ratio=0.2), run_time=0.8)
            v.wait_until("cloud")
            pk = packet(APL, 0.11, 5).move_to(chain[0].get_center())
            trail = TracedPath(pk.get_center, stroke_color=APL, stroke_width=5, dissipating_time=0.5)
            self.add(trail, pk)
            self.play(MoveAlongPath(pk, path), run_time=2.2, rate_func=smooth)
            self.play(Flash(chain[4].get_center(), color=BLUE, flash_radius=0.9), chain[4].box.animate.set_fill(BLUE, opacity=0.25), run_time=0.7)
            self.remove(trail)
            self.play(FadeOut(pk), run_time=0.3)
        self.wait(0.5)
        self.clear(run_time=0.8)

        # ------------------------------------------------------------ end card
        title = H("Ethernet-APL", size=84, color=APL)
        vs = T("a deep dive — and how it differs from CAN bus", size=30, color=MUTED)
        thanks = T("Thanks for watching.", size=34, color=TEXT, weight=BOLD)
        top = VGroup(title, vs).arrange(DOWN, buff=0.25).move_to(UP * 1.3)
        thanks.next_to(top, DOWN, buff=0.7)
        src = VGroup(
            T("Key references: IEEE 802.3cg-2019 (10BASE-T1L) · IEC TS 60079-47 (2-WISE) · IEC TS 63444 (APL port profiles)", size=16, color=MUTED),
            T("ISO 11898-1/-2 (CAN) · Ethernet-APL Engineering Guideline · CAN in Automation (CiA)", size=16, color=MUTED),
            T("Thomson 1855 · Heaviside 1880s · Nyquist 1928 · Hartley 1928 · Shannon 1948 · Widrow & Hoff 1960 · Lucky 1965", size=16, color=MUTED),
            T("Animation: Manim · Narration: Kokoro neural TTS · Icons: Tabler (MIT)", size=16, color=DIM),
        ).arrange(DOWN, buff=0.12).to_edge(DOWN, buff=0.5)
        with self.voice("Thanks for watching.", pad=2.5) as v:
            self.play(Write(title), FadeIn(vs, shift=UP * 0.1), run_time=1.4)
            self.play(FadeIn(thanks), FadeIn(src), run_time=0.8)
        self.wait(1.0)
        self.play(FadeOut(VGroup(title, vs, thanks, src, self.tag)), run_time=1.2)
