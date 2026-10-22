import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *

SEGS = [("SYNC", 1, "#FDE68A"), ("PROP", 7, CAN), ("PHASE 1", 6, "#D97706"), ("PHASE 2", 2, "#92400E")]


class CANBitTiming(APLScene):
    def construct(self):
        self.tag = corner_tag("03 · Our reference: CAN bus", color=CAN)
        self.add(self.tag)

        # ------------------------------------------------------------ one bit, cut into time quanta
        n_tq = sum(s[1] for s in SEGS)
        x0, x1, y = -5.6, 5.6, 1.2
        tq = (x1 - x0) / n_tq
        cells = VGroup(*[Rectangle(width=tq, height=0.7, stroke_color=BG, stroke_width=2).move_to([x0 + tq * (i + 0.5), y, 0]) for i in range(n_tq)])
        segs = VGroup()
        k = 0
        for name, w, col in SEGS:
            for i in range(k, k + w):
                cells[i].set_fill(col, opacity=0.85)
            r = VGroup(*cells[k:k + w])
            lab = T(name, size=17 if w > 1 else 13, color=TEXT, weight=BOLD).next_to(r, UP, buff=0.12)
            n_lab = T(f"{w} tq", size=14, color=MUTED).next_to(r, DOWN, buff=0.1)
            segs.add(VGroup(r, lab, n_lab))
            k += w
        sp_x = x0 + tq * (1 + 7 + 6)
        sp = VGroup(Arrow([sp_x, y - 1.25, 0], [sp_x, y - 0.42, 0], buff=0, stroke_width=4, color=TEXT, tip_length=0.16),
                    T("sample point · 87.5 %", size=18, color=TEXT, weight=BOLD).next_to([sp_x, y - 1.25, 0], DOWN, buff=0.08))
        brace = BraceBetweenPoints([x0, y + 0.75, 0], [x1, y + 0.75, 0], UP, color=MUTED)
        bl = T("one bit time = 16 time quanta, counted from the node's own crystal", size=18, color=MUTED).next_to(brace, UP, buff=0.1)
        notes = VGroup(T("an edge is expected here", size=15, color="#FDE68A"), T("absorbs the round-trip delay", size=15, color=CAN),
                       T("phase segments: room to re-align", size=15, color="#D97706")).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        notes.move_to([-3.4, -1.25, 0])
        with self.voice(
            "{clockless}One more detail of CAN's physical layer will matter later. There is no clock wire. So how does a "
            "receiver know where one bit ends and the next begins? {tq}Each node divides the bit time into small time quanta, "
            "counted from its own crystal oscillator. {seg}A bit consists of four segments: a synchronization segment, where "
            "an edge is expected; a propagation segment, which absorbs the round-trip delay we just met; and two phase "
            "segments. {sample}The bus is sampled between the two phase segments — typically somewhere between seventy-five "
            "and eighty-seven and a half percent of the bit."
        ) as v:
            v.wait_until("tq")
            self.play(LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.04), GrowFromCenter(brace), FadeIn(bl), run_time=1.6)
            v.wait_until("seg")
            for sg in segs:
                self.play(FadeIn(sg[1], shift=DOWN * 0.1), FadeIn(sg[2]), Indicate(sg[0], scale_factor=1.04, color=WHITE_SOFT), run_time=0.7)
            self.play(FadeIn(notes), run_time=0.6)
            v.wait_until("sample")
            self.play(GrowArrow(sp[0]), FadeIn(sp[1]), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ resynchronisation on edges
        bits = [1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1]
        bw = 0.88
        wx0 = -4.5
        wy = 1.1
        levels = [0 if b else 1 for b in bits]          # dominant (0) drawn high
        pts = []
        drift = [0, 0, 0, 0.18, 0.18, 0.18, 0.18, 0.18, 0.18, 0.18, 0.18, 0.18]
        for i, lv in enumerate(levels):
            xa = wx0 + i * bw + drift[i] * bw
            xb = wx0 + (i + 1) * bw + (drift[i + 1] if i + 1 < len(drift) else drift[-1]) * bw
            yv = wy + (0.45 if lv else -0.45)
            pts += [(xa, yv), (xb, yv)]
        wave = polyline(pts, CAN, 3.5)
        w_lbl = T("bus (dominant up)", size=16, color=CAN).next_to([wx0, wy, 0], LEFT, buff=0.2)
        grid_y = -0.35
        grid = VGroup()
        for i in range(len(bits) + 1):
            grid.add(Line([wx0 + i * bw, grid_y - 0.25, 0], [wx0 + i * bw, grid_y + 0.25, 0], stroke_color=MUTED, stroke_width=2))
        grid_lbl = T("receiver's bit grid", size=16, color=MUTED).next_to([wx0, grid_y, 0], LEFT, buff=0.2)
        sof = VGroup(Arrow([wx0 + bw, grid_y - 1.0, 0], [wx0 + bw, grid_y - 0.32, 0], buff=0, stroke_width=3, color="#FDE68A", tip_length=0.12),
                     T("hard sync on start of frame", size=15, color="#FDE68A").next_to([wx0 + bw, grid_y - 1.0, 0], DOWN, buff=0.06))
        late_x = wx0 + 4 * bw + 0.18 * bw
        late = VGroup(Arrow([late_x, grid_y - 1.0, 0], [late_x, grid_y - 0.32, 0], buff=0, stroke_width=3, color=DANGER, tip_length=0.12),
                      T("edge arrives late", size=15, color=DANGER).next_to([late_x, grid_y - 1.0, 0], DOWN, buff=0.06))
        new_grid = VGroup()
        for i in range(len(bits) + 1):
            shift = 0.18 * bw if i >= 4 else 0
            new_grid.add(Line([wx0 + i * bw + shift, grid_y - 0.25, 0], [wx0 + i * bw + shift, grid_y + 0.25, 0], stroke_color=GOOD, stroke_width=2.5))
        resync = T("phase segment 1 stretched: grid re-aligned", size=16, color=GOOD).next_to(new_grid, UP, buff=0.12).shift(RIGHT * 1.5)
        run = Brace(VGroup(*[Dot([wx0 + i * bw, wy + 0.5, 0]) for i in (4, 9)]), UP, color=CAN)
        run_l = T("5 identical bits → a stuff bit forces an edge", size=16, color=CAN).next_to(run, UP, buff=0.08)
        cmp = VGroup(T("CAN: timing from occasional edges", size=22, color=CAN, weight=BOLD),
                     T("APL will need something far finer", size=20, color=APL)).arrange(DOWN, buff=0.12).move_to([0, -2.85, 0])
        with self.voice(
            "{hard}Every frame begins with a hard synchronization on the very first recessive-to-dominant edge: the start of frame. "
            "{resync}After that, whenever a recessive-to-dominant edge arrives a little early or late, the receiver stretches "
            "phase segment one, or shortens phase segment two, by a few quanta, and realigns. {stuff}And that's the real "
            "reason for bit stuffing: after five identical bits there must be an edge, so the oscillators can never drift "
            "apart for long. {compare}Keep this picture in mind. CAN recovers its timing from occasional edges. APL will need "
            "something far finer."
        ) as v:
            self.play(Create(wave), FadeIn(w_lbl), FadeIn(grid), FadeIn(grid_lbl), run_time=1.4)
            self.play(GrowArrow(sof[0]), FadeIn(sof[1]), run_time=0.7)
            v.wait_until("resync")
            self.play(GrowArrow(late[0]), FadeIn(late[1]), run_time=0.7)
            self.play(Transform(grid, new_grid), FadeIn(resync), run_time=1.2)
            v.wait_until("stuff")
            self.play(GrowFromCenter(run), FadeIn(run_l), run_time=0.8)
            v.wait_until("compare")
            self.play(FadeIn(cmp, shift=UP * 0.1), run_time=0.8)
        self.wait(0.4)
        self.clear(run_time=0.7)
