import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *


class LinkUp(APLScene):
    def construct(self):
        self.tag = corner_tag("08 · Inside the receiver", color=BLUE)
        self.add(self.tag)

        # ------------------------------------------------------------ auto-negotiation
        xa, xb = -5.2, 5.2
        pa = device("PHY A", "cpu", APL, width=1.7, height=1.25, label_size=19).move_to([xa, 1.6, 0])
        pb = device("PHY B", "cpu", VIOLET, width=1.7, height=1.25, label_size=19).move_to([xb, 1.6, 0])
        cab = twisted_pair([pa.get_right(), pb.get_left()], DIM, amp=0.05, pitch=0.3)
        plug = T("cable plugged in", size=18, color=MUTED).next_to(cab, UP, buff=0.2)

        def page(text, frm, col, y):
            box = RoundedRectangle(width=2.9, height=0.5, corner_radius=0.1, fill_color=PANEL, fill_opacity=1, stroke_color=col, stroke_width=1.8)
            t = T(text, size=15, color=col, weight=BOLD).move_to(box)
            g = VGroup(box, t)
            x0 = xa + 1.6 if frm == "a" else xb - 1.6
            g.move_to([x0, y, 0])
            return g

        p1 = page("A: I can do 2.4 V and 1.0 V", "a", APL, 0.55)
        p2 = page("B: I can do 2.4 V and 1.0 V", "b", VIOLET, 0.0)
        p3 = page("A: I'd like to be master", "a", APL, -0.55)
        p4 = page("B: fine, I'll be slave", "b", VIOLET, -1.1)
        res = VGroup(pill("2.4 Vpp", APL, size=22), pill("A = master · B = slave", GOOD, size=22)).arrange(RIGHT, buff=0.5).move_to([0, -2.2, 0])
        dme = T("slow, robust pulses (differential Manchester)", size=16, color=MUTED).move_to([0, -2.95, 0])
        with self.voice(
            "{start}All of this has to come alive within moments of plugging in a cable. {an}First, the two ends exchange a "
            "few slow, simple messages: auto-negotiation. {agree}Using a robust low-speed code, they agree on the transmit "
            "amplitude — 2.4 or 1 volt peak to peak — and on which end will be master, and which slave."
        ) as v:
            self.play(FadeIn(pa), FadeIn(pb), run_time=0.6)
            self.play(Create(cab), FadeIn(plug), run_time=0.8)
            v.wait_until("an")
            for p, frm in ((p1, "a"), (p2, "b")):
                tgt = p.get_center() + (RIGHT if frm == "a" else LEFT) * 7.2
                self.play(FadeIn(p, shift=(RIGHT if frm == "a" else LEFT) * 0.3), run_time=0.4)
                self.play(p.animate.move_to(tgt).set_opacity(0.35), run_time=1.0, rate_func=smooth)
            v.wait_until("agree")
            for p, frm in ((p3, "a"), (p4, "b")):
                tgt = p.get_center() + (RIGHT if frm == "a" else LEFT) * 7.2
                self.play(FadeIn(p, shift=(RIGHT if frm == "a" else LEFT) * 0.3), run_time=0.4)
                self.play(p.animate.move_to(tgt).set_opacity(0.35), run_time=1.0, rate_func=smooth)
            self.play(FadeIn(res, shift=UP * 0.1), FadeIn(dme), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ training
        t0, t1 = -4.4, 6.2
        rows_y = {"mtx": 1.65, "srx": 0.75, "stx": -0.55, "mrx": -1.45}
        names = VGroup(
            T("master transmits", size=18, color=APL, weight=BOLD).next_to([t0, rows_y["mtx"], 0], LEFT, buff=0.3),
            T("slave receiver", size=18, color=MUTED).next_to([t0, rows_y["srx"], 0], LEFT, buff=0.3),
            T("slave transmits", size=18, color=VIOLET, weight=BOLD).next_to([t0, rows_y["stx"], 0], LEFT, buff=0.3),
            T("master receiver", size=18, color=MUTED).next_to([t0, rows_y["mrx"], 0], LEFT, buff=0.3),
        )
        axis = Arrow([t0, -2.25, 0], [t1 + 0.3, -2.25, 0], buff=0, stroke_width=2, color=DIM, tip_length=0.12)
        ax_l = T("time →", size=15, color=MUTED).next_to(axis, DOWN, buff=0.08).align_to(axis, RIGHT)
        mtx = Rectangle(width=t1 - t0, height=0.42, fill_color=APL, fill_opacity=0.75, stroke_width=0).move_to([(t0 + t1) / 2, rows_y["mtx"], 0])
        mtx_t = T("scrambled idle symbols", size=15, color=BG, weight=BOLD).move_to(mtx).shift(LEFT * 2.5)
        x_s = 0.6
        stx = Rectangle(width=t1 - x_s, height=0.42, fill_color=VIOLET, fill_opacity=0.75, stroke_width=0).move_to([(x_s + t1) / 2, rows_y["stx"], 0])
        stx_t = T("idle, on the master's clock", size=15, color=BG, weight=BOLD).move_to(stx).shift(LEFT * 0.6)
        silent = DashedLine([t0, rows_y["stx"], 0], [x_s, rows_y["stx"], 0], dash_length=0.08, stroke_color=DIM, stroke_width=2)
        silent_l = T("silent", size=14, color=MUTED).next_to(silent, UP, buff=0.05)

        def checks(items, y, x_start, dx):
            g = VGroup()
            for i, txt in enumerate(items):
                c = VGroup(check(GOOD, 0.22, 4), T(txt, size=14, color=GOOD)).arrange(RIGHT, buff=0.08)
                c.move_to([x_start + i * dx, y, 0], aligned_edge=LEFT)
                g.add(c)
            return g

        s_checks = checks(["clock locked", "equalizer", "descrambler"], rows_y["srx"], -4.2, 1.6)
        m_checks = checks(["clock & equalizer", "descrambler", "echo canceller"], rows_y["mrx"], 0.8, 1.85)
        s_ec = VGroup(check(GOOD, 0.22, 4), T("echo canceller", size=14, color=GOOD)).arrange(RIGHT, buff=0.08).move_to([x_s + 0.2, rows_y["srx"], 0], aligned_edge=LEFT)
        up = VGroup(RoundedRectangle(width=2.6, height=0.75, corner_radius=0.2, fill_color=GOOD, fill_opacity=0.18, stroke_color=GOOD, stroke_width=2.5),
                    T("LINK UP", size=28, color=GOOD, weight=BOLD))
        up[1].move_to(up[0])
        up.move_to([5.0, 2.65, 0])
        with self.voice(
            "{train}Then training begins. The master sends a scrambled stream of idle symbols, while the slave stays silent. "
            "{slock}The slave's receiver locks its clock to the master, trains its equalizer, and synchronizes its "
            "descrambler. {stx}Only then does the slave start transmitting — on the master's clock. {mrx}Now the master "
            "trains its own receiver, and both sides fine-tune their echo cancellers. {up}When both ends report that their "
            "receivers are happy, the link is up, and Ethernet frames can flow."
        ) as v:
            self.play(FadeIn(names), Create(axis), FadeIn(ax_l), run_time=0.8)
            self.play(GrowFromEdge(mtx, LEFT), FadeIn(mtx_t), Create(silent), FadeIn(silent_l), run_time=1.6, rate_func=linear)
            v.wait_until("slock")
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in s_checks], lag_ratio=0.5), run_time=2.0)
            v.wait_until("stx")
            self.play(GrowFromEdge(stx, LEFT), FadeIn(stx_t), run_time=1.2)
            v.wait_until("mrx")
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in m_checks], lag_ratio=0.5), FadeIn(s_ec), run_time=2.2)
            v.wait_until("up")
            self.play(FadeIn(up, scale=0.8), run_time=0.7)
            self.play(Flash(up, color=GOOD, line_length=0.3, num_lines=16, flash_radius=1.5), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the journey of one bit, end to end
        jm = JourneyMap()
        bit = packet(POWER, 0.11)
        self.play(FadeIn(jm), run_time=0.8)
        path_tx = [jm.tx[i].get_center() for i in range(5)]
        cab_a = jm.tx[-1].get_right()
        cab_b = jm.rx[0].get_left()
        path_rx = [jm.rx[i].get_center() for i in range(5)]
        with self.voice(
            "{journey}Let's follow one bit from end to end. {tx}It's scrambled, grouped with three others, and turned into "
            "three ternary symbols. {wire}A voltage step launches a wave into the cable, which carries it at two-thirds of "
            "the speed of light, strips away about ninety-five percent of its amplitude, and smears it across its "
            "neighbors — all while a wave travelling the other way passes straight through it. {rx}At the far end, the "
            "receiver subtracts its own echo, undoes the smearing, picks the right instant to sample, decides plus, zero or "
            "minus, and decodes and descrambles. {done}Five microseconds and a few clever filters later, the bit is back — "
            "with fewer than one error in a billion."
        ) as v:
            self.play(FadeIn(bit.move_to(path_tx[0])), run_time=0.4)
            v.wait_until("tx")
            for i in range(1, 5):
                self.play(bit.animate.move_to(path_tx[i]), Indicate(jm.tx[i], color=APL, scale_factor=1.06), run_time=0.8)
            v.wait_until("wire")
            self.play(bit.animate.move_to(cab_a), run_time=0.4)
            t_lbl = T("5 µs", size=22, color=POWER, weight=BOLD).next_to(jm.cable, DOWN, buff=0.55)
            self.play(MoveAlongPath(bit, Line(cab_a, cab_b)), FadeIn(t_lbl), run_time=v.until("rx", 4.0) * 0.9, rate_func=linear)
            for i in range(0, 5):
                self.play(bit.animate.move_to(path_rx[i]).set_opacity(1.0), Indicate(jm.rx[i], color=BLUE, scale_factor=1.06), run_time=0.9)
            v.wait_until("done")
            done = VGroup(check(GOOD, 0.4, 6), T("bit delivered", size=22, color=GOOD, weight=BOLD)).arrange(RIGHT, buff=0.15).next_to(jm.rx[-1], DOWN, buff=0.15).shift(LEFT * 0.0)
            done.next_to(jm.rx[-1], LEFT, buff=0.4)
            self.play(FadeIn(done, shift=LEFT * 0.1), Flash(bit, color=GOOD, flash_radius=0.4), run_time=0.8)
        self.wait(0.5)
        self.clear(run_time=0.7)
