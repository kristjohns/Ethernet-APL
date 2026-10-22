import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *

CAN_L_COL = "#C2410C"


def id_bits(v):
    return [int(b) for b in format(v, "011b")]


class CANArbitration(APLScene):
    def construct(self):
        self.tag = corner_tag("03 · Our reference: CAN bus", color=CAN)
        self.add(self.tag)

        # ------------------------------------------------------------ wired-AND
        bus_h = Line(LEFT * 5.8 + UP * 0.25, RIGHT * 3.2 + UP * 0.25, stroke_color=CAN, stroke_width=4)
        bus_l = Line(LEFT * 5.8 + DOWN * 0.25, RIGHT * 3.2 + DOWN * 0.25, stroke_color=CAN_L_COL, stroke_width=4)
        bus = VGroup(bus_h, bus_l).shift(DOWN * 0.3)
        drivers = VGroup()
        states = [1, 1, 1]
        for i, nm in enumerate("ABC"):
            x = -4.5 + 2.6 * i
            box = RoundedRectangle(width=1.7, height=1.5, corner_radius=0.12, fill_color=PANEL, fill_opacity=1,
                                   stroke_color=CAN, stroke_width=2.2).move_to([x, 1.95, 0])
            name = T(f"Node {nm}", size=20, color=TEXT, weight=BOLD).move_to(box.get_top() + DOWN * 0.28)
            stubs = VGroup(Line([x - 0.15, box.get_bottom()[1], 0], [x - 0.15, bus_h.get_y(), 0]),
                           Line([x + 0.15, box.get_bottom()[1], 0], [x + 0.15, bus_l.get_y(), 0])).set_stroke(CAN, 2)
            stubs[1].set_stroke(CAN_L_COL)
            drivers.add(VGroup(box, name, stubs))
        res_box = panel(2.9, 2.2).move_to(RIGHT * 5.0 + DOWN * 0.3)
        res_title = T("bus level", size=20, color=MUTED).next_to(res_box.get_top(), DOWN, buff=0.18)

        def bit_badge(b, size=34):
            col = CAN if b == 0 else MUTED
            word = "dominant" if b == 0 else "recessive"
            return VGroup(M(str(b), size=size, color=col, weight=BOLD), T(word, size=16, color=col)).arrange(DOWN, buff=0.05)

        node_bits = VGroup(*[bit_badge(1, 26).move_to(drivers[i][0].get_center() + DOWN * 0.22) for i in range(3)])
        bus_bit = bit_badge(1, 54).move_to(res_box.get_center() + DOWN * 0.15)
        rule = T("bus = A AND B AND C        (0 = dominant)", size=22, color=TEXT).move_to(DOWN * 2.6)

        def set_state(i, b):
            states[i] = b
            out = min(states)
            anims = [Transform(node_bits[i], bit_badge(b, 26).move_to(node_bits[i])),
                     Transform(bus_bit, bit_badge(out, 54).move_to(bus_bit))]
            col = CAN if out == 0 else DIM
            anims += [bus_h.animate.set_stroke(CAN if out == 0 else "#7C5A1E", 6 if out == 0 else 4),
                      bus_l.animate.set_stroke(CAN_L_COL if out == 0 else "#5C2A10", 6 if out == 0 else 4)]
            anims.append(drivers[i][0].animate.set_fill(CAN if b == 0 else PANEL, opacity=0.35 if b == 0 else 1))
            return anims

        with self.voice(
            "{key}Now the crucial property. {win}Dominant always wins. If even one node drives a dominant zero, the bus "
            "is dominant, no matter how many others send a recessive one. {and}Engineers call this a wired-AND, and "
            "CAN builds its entire access method on it."
        ) as v:
            self.play(FadeIn(bus), LaggedStart(*[FadeIn(d, shift=DOWN * 0.2) for d in drivers], lag_ratio=0.15),
                      FadeIn(res_box), FadeIn(res_title), run_time=1.0)
            self.play(FadeIn(node_bits), FadeIn(bus_bit), *set_state(0, 1), run_time=0.6)
            v.wait_until("win")
            self.play(*set_state(1, 0), run_time=0.6)
            self.wait(0.6)
            self.play(*set_state(0, 0), run_time=0.6)
            self.wait(0.4)
            self.play(*set_state(1, 1), run_time=0.6)
            self.wait(0.4)
            self.play(*set_state(0, 1), run_time=0.6)
            v.wait_until("and")
            self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
            self.play(*set_state(2, 0), run_time=0.6)
            self.wait(0.8)
            self.play(*set_state(2, 1), run_time=0.6)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ arbitration race
        msgs = [("Brake pressure", 0x326), ("Engine speed", 0x329), ("Cabin temperature", 0x340)]
        rows_bits = [[0] + id_bits(v) for _, v in msgs]  # SOF + 11 ID bits
        n_cols = 12
        cell = 0.62
        x0 = -3.55
        y_rows = [1.95, 1.1, 0.25]
        y_bus = -0.85
        head = VGroup()
        for c in range(n_cols):
            lab = "SOF" if c == 0 else f"ID{10 - (c - 1)}"
            head.add(T(lab, size=13, color=DIM).move_to([x0 + c * cell, 2.65, 0]))
        names = VGroup()
        for r, (nm, v_id) in enumerate(msgs):
            names.add(VGroup(T(nm, size=22, color=TEXT, weight=BOLD), M(f"ID 0x{v_id:03X}", size=17, color=MUTED)).arrange(DOWN, aligned_edge=RIGHT, buff=0.05)
                      .next_to([x0 - 0.45, y_rows[r], 0], LEFT, buff=0.0))
        bus_name = T("Bus", size=24, color=CAN, weight=BOLD).next_to([x0 - 0.45, y_bus, 0], LEFT, buff=0.0)
        sep = DashedLine([x0 - 3.7, -0.3, 0], [x0 + (n_cols - 0.5) * cell + 0.2, -0.3, 0], dash_length=0.08, stroke_color=DIM, stroke_width=1.5)

        def cell_mob(b, x, y, state="active"):
            sq = RoundedRectangle(width=cell * 0.86, height=cell * 0.86, corner_radius=0.08, stroke_width=2)
            if state == "lost":
                sq.set_fill(PANEL, 1).set_stroke(DIM, 1.5)
                t = M(str(b), size=22, color=DIM)
            elif b == 0:
                sq.set_fill(CAN, 0.85).set_stroke(CAN, 2)
                t = M("0", size=24, color=BG, weight=BOLD)
            else:
                sq.set_fill(PANEL, 1).set_stroke(MUTED, 2)
                t = M("1", size=24, color=MUTED, weight=BOLD)
            g = VGroup(sq, t.move_to(sq)).move_to([x, y, 0])
            return g

        cursor = RoundedRectangle(width=cell * 1.0, height=(y_rows[0] - y_bus) + cell * 1.05, corner_radius=0.1,
                                  stroke_color=WHITE_SOFT, stroke_width=2, fill_opacity=0.04, fill_color=WHITE_SOFT)
        cursor.move_to([x0, 0.5 * (y_rows[0] + y_bus), 0])

        # bus waveform under the grid
        wf_y0, wf_amp = -2.35, 0.55
        wf_pts = []
        wave_mob = VMobject()

        alive = [True, True, True]
        lost_at = {2: 5, 1: 8}  # row -> column where it loses

        def reveal(c, run_time):
            anims = []
            col_bits = []
            for r in range(3):
                if alive[r]:
                    col_bits.append(rows_bits[r][c])
            busb = min(col_bits)
            for r in range(3):
                x, y = x0 + c * cell, y_rows[r]
                if alive[r]:
                    m = cell_mob(rows_bits[r][c], x, y)
                    anims.append(FadeIn(m, scale=0.6))
                    self.cells[r].append(m)
            bm = cell_mob(busb, x0 + c * cell, y_bus)
            anims.append(FadeIn(bm, scale=0.6))
            self.cells[3].append(bm)
            # waveform segment
            xa, xb = x0 + (c - 0.5) * cell, x0 + (c + 0.5) * cell
            yv = wf_y0 + (wf_amp if busb == 0 else 0)
            seg = Line([xa, yv, 0], [xb, yv, 0], stroke_color=CAN, stroke_width=3.5)
            parts = [seg]
            if self.last_level is not None and self.last_level != yv:
                parts.append(Line([xa, self.last_level, 0], [xa, yv, 0], stroke_color=CAN, stroke_width=3.5))
            self.last_level = yv
            anims.append(Create(VGroup(*parts)))
            self.play(cursor.animate.move_to([x0 + c * cell, cursor.get_y(), 0]), *anims, run_time=run_time)

        self.cells = [[], [], [], []]
        self.last_level = wf_y0
        wf_axis = VGroup(Line([x0 - 0.5 * cell, wf_y0, 0], [x0 + (n_cols + 5) * cell, wf_y0, 0], stroke_color=DIM, stroke_width=1.5),
                         T("dominant", size=14, color=CAN).move_to([x0 - 1.25, wf_y0 + wf_amp, 0]),
                         T("recessive", size=14, color=MUTED).move_to([x0 - 1.25, wf_y0, 0]))

        def lose(r):
            alive[r] = False
            x_last = x0 + lost_at[r] * cell
            flash = SurroundingRectangle(self.cells[r][-1], color=DANGER, buff=0.04, stroke_width=3)
            lbl = VGroup(icon("ear", MUTED, 0.32), T("lost — now listening", size=18, color=DANGER)).arrange(RIGHT, buff=0.1)
            lbl.next_to(self.cells[r][-1], RIGHT, buff=0.35)
            lbl = VGroup(BackgroundRectangle(lbl, color=BG, fill_opacity=0.9, buff=0.06), lbl).set_z_index(6)
            dim_anims = [m.animate.set_opacity(0.35) for m in self.cells[r][:-1]]
            self.play(Create(flash), names[r].animate.set_opacity(0.45), run_time=0.35)
            self.play(FadeOut(flash), FadeIn(lbl, shift=LEFT * 0.2), *dim_anims, run_time=0.45)

        with self.voice(
            "{start}Suppose three nodes start a frame at the same instant. Each one sends its eleven-bit identifier, "
            "bit by bit, while listening to the bus. "
            "{c_lose}At the fifth bit, the cabin-temperature node sends a recessive one, but reads back a dominant zero. "
            "Someone with a more important message is talking, so it stops immediately, and just listens. "
            "{b_lose}Three bits later, the engine-speed node loses the same way. "
            "{win}The brake-pressure message, with the lowest identifier, wins — and its frame continues undamaged. "
            "No collision, no retransmission, no time lost. "
            "{det}This is bitwise arbitration, and it's why CAN is so deterministic: the most important message "
            "always gets through first."
        ) as v:
            self.play(FadeIn(names), FadeIn(bus_name), FadeIn(head), Create(sep), FadeIn(wf_axis), run_time=1.0)
            self.play(FadeIn(cursor), run_time=0.3)
            # columns 0..5 until c_lose
            t_avail = v.until("c_lose", 3.0)
            for c in range(0, 6):
                reveal(c, t_avail / 6)
            lose(2)
            v.wait_until("b_lose")
            for c in range(6, 9):
                reveal(c, 0.45)
            lose(1)
            t_avail = v.until("win", 1.2)
            for c in range(9, 12):
                reveal(c, max(0.3, t_avail / 3))
            win_box = SurroundingRectangle(VGroup(names[0], *self.cells[0]), color=GOOD, buff=0.1, corner_radius=0.1, stroke_width=3)
            win_lbl = VGroup(icon("crown", GOOD, 0.34), T("wins the bus", size=18, color=GOOD, weight=BOLD)).arrange(RIGHT, buff=0.1)
            win_lbl.next_to(self.cells[0][-1], RIGHT, buff=0.3)
            self.play(Create(win_box), FadeIn(win_lbl, shift=LEFT * 0.2), FadeOut(cursor), run_time=0.7)
            # frame continues
            rest = VGroup(*[Rectangle(width=cell * 0.86, height=cell * 0.86, fill_color=GOOD, fill_opacity=0.25 + 0.5 * (k % 2),
                                      stroke_width=0) for k in range(5)]).arrange(RIGHT, buff=cell * 0.14)
            rest.next_to(self.cells[0][-1], RIGHT, buff=cell * 0.14)
            cont = T("… control, data, CRC …", size=16, color=GOOD).next_to(rest, DOWN, buff=0.08)
            self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rest], lag_ratio=0.2), FadeOut(win_lbl), FadeIn(cont), run_time=1.0)
            v.wait_until("det")
            det = T("highest priority = lowest ID  →  guaranteed to win", size=24, color=TEXT).move_to(DOWN * 3.3)
            self.play(FadeIn(det, shift=UP * 0.1), run_time=0.8)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ frame anatomy
        fields = [("SOF", 1, MUTED), ("ID", 11, CAN), ("RTR", 1, "#FCD34D"), ("IDE", 1, "#FDE68A"), ("r0", 1, "#FDE68A"),
                  ("DLC", 4, "#FCD34D"), ("Data", 64, GOOD), ("CRC", 15, VIOLET), ("del", 1, MUTED), ("ACK", 1, BLUE),
                  ("del", 1, MUTED), ("EOF", 7, MUTED), ("IFS", 3, DIM)]
        total = sum(f[1] for f in fields)
        W = 12.6
        ux = W / total
        x = -W / 2
        bar = VGroup()
        for nm, n, col in fields:
            r = Rectangle(width=n * ux, height=0.75, fill_color=col, fill_opacity=0.85 if nm != "IFS" else 0.4, stroke_color=BG, stroke_width=1.2)
            r.move_to([x + n * ux / 2, 0.4, 0])
            r.field = nm
            bar.add(r)
            x += n * ux
        labels = VGroup()
        for r, (nm, n, col) in zip(bar, fields):
            if n >= 7:
                labels.add(T(nm, size=20, color=BG if nm in ("Data",) else BG, weight=BOLD).move_to(r))
        small = VGroup(
            T("SOF", size=15, color=MUTED).next_to(bar[0], UP, buff=0.35),
            T("control", size=15, color="#FCD34D").next_to(VGroup(*bar[2:6]), UP, buff=0.35),
            T("ACK", size=15, color=BLUE).next_to(bar[9], UP, buff=0.35),
            T("IFS", size=15, color=MUTED).next_to(bar[12], UP, buff=0.35),
        )
        ticks = VGroup(*[Line(lbl.get_bottom() + DOWN * 0.03, tgt.get_top(), stroke_color=DIM, stroke_width=1.5)
                         for lbl, tgt in zip(small, [bar[0], VGroup(*bar[2:6]), bar[9], bar[12]])])
        bits_lbl = VGroup()
        for r, (nm, n, col) in zip(bar, fields):
            if n >= 4:
                bits_lbl.add(T(f"{n}", size=15, color=MUTED).next_to(r, DOWN, buff=0.1))
        b_data = Brace(bar[6], DOWN, buff=0.45, color=GOOD)
        t_data = T("payload: 0 – 8 bytes", size=22, color=GOOD, weight=BOLD).next_to(b_data, DOWN, buff=0.1)
        ovh_l = Brace(VGroup(*bar[0:6]), DOWN, buff=0.45, color=CAN)
        ovh_r = Brace(VGroup(*bar[7:13]), DOWN, buff=0.45, color=CAN)
        t_ovh = T("≈ 47 bits of overhead", size=22, color=CAN, weight=BOLD).next_to(VGroup(ovh_l, ovh_r), DOWN, buff=0.55)
        t_ovh.move_to([0, t_ovh.get_y() - 0.55, 0])
        ovh_lines = VGroup(Line(ovh_l.get_bottom(), t_ovh.get_left() + LEFT * 0.1, stroke_color=CAN, stroke_width=1.5),
                           Line(ovh_r.get_bottom(), t_ovh.get_right() + RIGHT * 0.1, stroke_color=CAN, stroke_width=1.5))
        frame_title = VGroup(T("Classic CAN data frame", size=30, weight=BOLD), T("111 bits for 8 data bytes (before stuffing)", size=22, color=MUTED)).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        frame_title.to_edge(UP, buff=0.95)

        with self.voice(
            "{frame}A classic CAN frame carries at most eight bytes of data, {ovh}wrapped in nearly fifty bits of "
            "overhead: the identifier, control bits, a fifteen-bit CRC, an acknowledge slot, and an end-of-frame marker."
        ) as v:
            self.play(FadeIn(frame_title, shift=DOWN * 0.1), run_time=0.6)
            self.play(LaggedStart(*[GrowFromEdge(r, LEFT) for r in bar], lag_ratio=0.08), run_time=1.6)
            self.play(FadeIn(labels), FadeIn(small), Create(ticks), FadeIn(bits_lbl), run_time=0.8)
            v.wait_until("frame")
            self.play(GrowFromCenter(b_data), FadeIn(t_data), run_time=0.8)
            v.wait_until("ovh")
            self.play(GrowFromCenter(ovh_l), GrowFromCenter(ovh_r), Create(ovh_lines), FadeIn(t_ovh), run_time=1.0)

        # bit stuffing
        stuff_bits = [1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0]
        cells = VGroup(*[cell_mob(b, 0, 0) for b in stuff_bits]).arrange(RIGHT, buff=0.06).scale(0.9).move_to(DOWN * 2.85)
        with self.voice(
            "{stuff}After five identical bits, the transmitter inserts one opposite stuff bit, so the receivers never "
            "lose their clock."
        ) as v:
            self.play(FadeOut(VGroup(b_data, t_data, ovh_l, ovh_r, ovh_lines, t_ovh)), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in cells], lag_ratio=0.05), run_time=0.9)
            run1 = SurroundingRectangle(VGroup(*cells[1:6]), color=PINK, buff=0.05, stroke_width=2.5)
            self.play(Create(run1), run_time=0.5)
            # insert stuff bit after index 5
            right_part = VGroup(*cells[6:])
            sb = cell_mob(1, 0, 0).scale(0.9)
            sb[0].set_fill(PINK, 0.9).set_stroke(PINK, 2)
            sb[1].set_color(BG)
            self.play(right_part.animate.shift(RIGHT * (cells[1].width + 0.06)), run_time=0.5)
            sb.next_to(cells[5], RIGHT, buff=0.06)
            sb_lbl = T("stuff bit", size=18, color=PINK, weight=BOLD).next_to(sb, UP, buff=0.12)
            self.play(FadeIn(sb, scale=1.6), FadeIn(sb_lbl, shift=DOWN * 0.1), run_time=0.6)
            run2 = SurroundingRectangle(VGroup(*right_part[3:8]), color=PINK, buff=0.05, stroke_width=2.5)
            sb2 = cell_mob(0, 0, 0).scale(0.9)
            sb2[0].set_fill(PINK, 0.9).set_stroke(PINK, 2)
            sb2[1].set_color(BG)
            self.play(Create(run2), run_time=0.4)
            tail = VGroup(*right_part[8:])
            self.play(tail.animate.shift(RIGHT * (cells[1].width + 0.06)), run_time=0.4)
            sb2.next_to(right_part[7], RIGHT, buff=0.06)
            self.play(FadeIn(sb2, scale=1.6), run_time=0.5)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ content addressing
        bus2 = VGroup(Line(LEFT * 6 + UP * 0.12, RIGHT * 6 + UP * 0.12, stroke_color=CAN, stroke_width=4),
                      Line(LEFT * 6 + DOWN * 0.12, RIGHT * 6 + DOWN * 0.12, stroke_color=CAN_L_COL, stroke_width=4)).shift(DOWN * 0.2)
        rx = [("Engine", -4.5, None), ("Brakes", -1.5, False), ("Dashboard", 1.5, True), ("Gearbox", 4.5, True)]
        rnodes = VGroup()
        for nm, x, _ in rx:
            d = device(nm, "cpu", CAN, width=1.7, height=1.15, label_size=19).move_to([x, 1.55, 0])
            st = Line([x, d.get_bottom()[1], 0], [x, bus2.get_y(), 0], stroke_color=CAN, stroke_width=2)
            rnodes.add(VGroup(d, st))
        frm = VGroup(RoundedRectangle(width=3.3, height=0.6, corner_radius=0.3, fill_color=CAN, fill_opacity=0.9, stroke_width=0),
                     T("ID 0x329 · engine speed", size=19, color=BG, weight=BOLD))
        frm[1].move_to(frm[0])
        frm.move_to([-4.5, -1.05, 0])
        with self.voice(
            "{noaddr}Notice what's missing: there's no destination address. {content}The identifier names the content, "
            "like “engine speed”, {filter}and every node decides for itself whether it cares."
        ) as v:
            self.play(Create(bus2), LaggedStart(*[FadeIn(n, shift=DOWN * 0.2) for n in rnodes], lag_ratio=0.15), run_time=1.2)
            v.wait_until("content")
            self.play(FadeIn(frm, scale=0.8), run_time=0.6)
            self.play(frm.animate.move_to([4.5, -1.05, 0]), run_time=1.6, rate_func=linear)
            v.wait_until("filter")
            marks = VGroup()
            for (nm, x, acc), n in zip(rx, rnodes):
                if acc is None:
                    m = T("sender", size=18, color=MUTED)
                elif acc:
                    m = VGroup(check(GOOD, 0.3, 5), T("uses it", size=18, color=GOOD)).arrange(RIGHT, buff=0.1)
                else:
                    m = VGroup(cross(DANGER, 0.26, 5), T("ignores", size=18, color=DANGER)).arrange(RIGHT, buff=0.1)
                m.next_to(n[0], UP, buff=0.18)
                marks.add(m)
            self.play(LaggedStart(*[FadeIn(m, shift=DOWN * 0.1) for m in marks], lag_ratio=0.25), run_time=1.2)
            note = T("ID = what it is, not who it's for", size=26, color=TEXT, weight=BOLD).move_to(DOWN * 2.6)
            self.play(FadeIn(note, shift=UP * 0.1), run_time=0.7)
        self.wait(0.4)
        self.clear(run_time=0.6)
