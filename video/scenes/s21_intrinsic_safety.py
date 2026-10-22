import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.style import *
from apl.widgets import *

YELLOW_Z2 = "#FDE047"


def puzzle_piece(width, height, tab_side, color, label_lines, tab=True):
    body = RoundedRectangle(width=width, height=height, corner_radius=0.16)
    r = 0.26
    c = Circle(radius=r).move_to(body.get_right() if tab_side == "right" else body.get_left())
    shape = Union(body, c) if tab else Difference(body, c)
    shape.set_fill(color, 0.16).set_stroke(color, 2.6)
    txt = VGroup(*[T(l, size=s, color=col, weight=w) for l, s, col, w in label_lines]).arrange(DOWN, buff=0.08)
    txt.move_to(body)
    return VGroup(shape, txt)


class IntrinsicSafety(APLScene):
    def construct(self):
        self.tag = corner_tag("09 · Power on the same pair", color=POWER)
        self.add(self.tag)
        self.chapter(10, "Intrinsic safety", "Energy too small to ignite", color=HAZARD)

        # ------------------------------------------------------------ fire triangle
        A, B, C = np.array([0, 2.3, 0]), np.array([-2.3, -1.6, 0]), np.array([2.3, -1.6, 0])
        sides = VGroup(Line(B, A), Line(A, C), Line(C, B)).set_stroke(TEXT, 5)
        flame = icon("flame", HAZARD, 1.1).move_to([0, -0.15, 0])
        l_fuel = VGroup(icon("gas-station", TEXT, 0.45), T("fuel", size=26, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.12)
        l_fuel.next_to(sides[0].get_center(), LEFT, buff=0.35)
        l_ox = VGroup(T("oxygen", size=26, color=TEXT, weight=BOLD), icon("wind", TEXT, 0.45)).arrange(RIGHT, buff=0.12)
        l_ox.next_to(sides[1].get_center(), RIGHT, buff=0.35)
        l_ign = VGroup(icon("bolt", POWER, 0.45), T("ignition source", size=26, color=POWER, weight=BOLD)).arrange(RIGHT, buff=0.12)
        l_ign.next_to(sides[2].get_center(), DOWN, buff=0.3)
        tri = VGroup(sides, flame, l_fuel, l_ox, l_ign).shift(LEFT * 0.0 + DOWN * 0.1)
        with self.voice(
            "Now the fourth wall: explosive atmospheres. {tri}An explosion needs three things: fuel, oxygen, and an "
            "ignition source. {cant}In a process plant, you can't always remove the first two."
        ) as v:
            v.wait_until("tri")
            self.play(Create(sides), run_time=1.0)
            self.play(FadeIn(l_fuel), FadeIn(l_ox), FadeIn(l_ign), FadeIn(flame, scale=0.6), run_time=1.0)
            v.wait_until("cant")
            self.play(sides[0].animate.set_stroke(HAZARD, 7), sides[1].animate.set_stroke(HAZARD, 7), run_time=0.6)
            self.play(Wiggle(flame), run_time=0.9)
        self.play(tri.animate.scale(0.5).to_corner(UL, buff=0.7).shift(DOWN * 0.35), run_time=0.8)

        # ------------------------------------------------------------ zones
        tank = RoundedRectangle(width=2.6, height=3.2, corner_radius=0.3, fill_color=PANEL, fill_opacity=1,
                                stroke_color=TEXT, stroke_width=2.5).move_to([-0.9, -1.0, 0])
        vapor = Rectangle(width=2.45, height=1.1, stroke_width=0, fill_color=DANGER, fill_opacity=0.25).move_to(tank.get_top() + DOWN * 0.66)
        vap_h = hatch(vapor, DANGER, spacing=0.14, opacity=0.5)
        liquid = Rectangle(width=2.45, height=1.85, stroke_width=0, fill_color="#0E7490", fill_opacity=0.75).move_to(tank.get_bottom() + UP * 1.03)
        vent = Rectangle(width=0.22, height=0.65, fill_color=PANEL, fill_opacity=1, stroke_color=TEXT, stroke_width=2).next_to(tank, UP, buff=0).shift(RIGHT * 0.6)
        z1 = Circle(radius=1.05, stroke_color=HAZARD, stroke_width=2, fill_color=HAZARD, fill_opacity=0.12).move_to(vent.get_top())
        z2 = RoundedRectangle(width=5.6, height=5.6, corner_radius=1.2, stroke_color=YELLOW_Z2, stroke_width=1.5,
                              fill_color=YELLOW_Z2, fill_opacity=0.05).move_to([-0.9, -0.55, 0])
        zone_art = VGroup(z2, z1, tank, liquid, vapor, vap_h, vent)
        defs = VGroup(
            VGroup(T("Zone 0", size=26, color=DANGER, weight=BOLD), T("continuously or for long periods", size=19, color=TEXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(T("Zone 1", size=26, color=HAZARD, weight=BOLD), T("likely in normal operation", size=19, color=TEXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(T("Zone 2", size=26, color=YELLOW_Z2, weight=BOLD), T("not expected — and only briefly", size=19, color=TEXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([4.55, -0.6, 0])
        zl0 = T("Zone 0", size=18, color=DANGER, weight=BOLD).move_to(vapor)
        zl1 = T("Zone 1", size=18, color=HAZARD, weight=BOLD).next_to(z1, UP, buff=0.05)
        zl2 = T("Zone 2", size=18, color=YELLOW_Z2, weight=BOLD).move_to(z2.get_corner(DL) + UR * 0.55)
        with self.voice(
            "{zones}Areas are classified into zones. {z0}Zone 0: an explosive atmosphere is present continuously or for "
            "long periods — inside a tank, for instance. {z1}Zone 1: likely in normal operation. "
            "{z2}Zone 2: not expected, and only briefly if it happens."
        ) as v:
            self.play(FadeIn(tank), FadeIn(liquid), FadeIn(vent), run_time=0.8)
            v.wait_until("z0")
            self.play(FadeIn(vapor), FadeIn(vap_h), FadeIn(zl0), FadeIn(defs[0], shift=LEFT * 0.1), run_time=0.9)
            v.wait_until("z1")
            self.play(FadeIn(z1), FadeIn(zl1), FadeIn(defs[1], shift=LEFT * 0.1), run_time=0.8)
            v.wait_until("z2")
            self.play(FadeIn(z2), FadeIn(zl2), FadeIn(defs[2], shift=LEFT * 0.1), run_time=0.8)
        self.play(FadeOut(VGroup(zone_art, defs, zl0, zl1, zl2)), run_time=0.6)

        # ------------------------------------------------------------ energy limitation
        cut = Line(sides[2].get_start(), sides[2].get_end(), stroke_color=BG, stroke_width=14)
        x_ign = cross(DANGER, 0.4, 7).move_to(l_ign)
        src = dc_source(0.32, POWER).move_to([-5.4, 0.55, 0])
        src_l = TeX(r"U_o", size=34, color=POWER).next_to(src, LEFT, buff=0.15)
        r_lim = resistor(1.0, TEXT).move_to([-4.0, 1.25, 0])
        r_l = T("current limit", size=16, color=MUTED).next_to(r_lim, UP, buff=0.12)
        y1, y0 = 1.25, -0.15
        cab_c = capacitor(0.7, APL, 2.6).rotate(PI / 2).move_to([-1.6, (y1 + y0) / 2, 0])
        cab_l = inductor(1.0, APL, 2.6).move_to([-0.6, y1, 0])
        cab_lbl = T("cable C and L", size=16, color=APL).next_to(cab_c, LEFT, buff=0.2)
        gap_x = 0.9
        dev = device("device", "gauge", APL, width=1.4, height=1.1, label_size=16).move_to([2.3, (y1 + y0) / 2, 0])
        wires = VGroup(
            Line(src.get_top(), [-5.4, y1, 0]), Line([-5.4, y1, 0], r_lim.get_left()), Line(r_lim.get_right(), [-1.6, y1, 0]),
            Line([-1.6, y1, 0], cab_l.get_left()), Line(cab_l.get_right(), [gap_x - 0.12, y1, 0]),
            Line([gap_x + 0.12, y1, 0], [dev.get_left()[0], y1, 0]),
            Line(src.get_bottom(), [-5.4, y0, 0]), Line([-5.4, y0, 0], [dev.get_left()[0], y0, 0]),
            Line([-1.6, y1, 0], cab_c.get_top()), Line(cab_c.get_bottom(), [-1.6, y0, 0]),
        ).set_stroke(TEXT, 2.4)
        spark = icon("sparkles", POWER, 0.5).move_to([gap_x, y1 + 0.42, 0])
        brk = T("broken wire", size=16, color=POWER).next_to(spark, UP, buff=0.05)
        circuit = VGroup(src, src_l, r_lim, r_l, wires, cab_c, cab_l, cab_lbl, dev)
        eqs = VGroup(TeX(r"E_C = \tfrac{1}{2}\,C\,V^2", size=40, color=TEXT), TeX(r"E_L = \tfrac{1}{2}\,L\,I^2", size=40, color=TEXT)).arrange(RIGHT, buff=0.9)
        eqs.move_to([-1.6, -1.45, 0])
        limits = VGroup(*[pill(t, HAZARD, size=18) for t in ["limit V", "limit I", "limit P", "limit C and L"]]).arrange(RIGHT, buff=0.2)
        limits.move_to([-1.6, -2.55, 0])
        # energy meter
        m_base = np.array([5.75, -2.6, 0])
        m_h = 4.6
        meter = Rectangle(width=0.7, height=m_h, stroke_color=MUTED, stroke_width=2).move_to(m_base + UP * m_h / 2)
        mie_y = m_base[1] + m_h * 0.78
        mie = DashedLine([5.2, mie_y, 0], [6.3, mie_y, 0], dash_length=0.08, stroke_color=DANGER, stroke_width=3)
        mie_l = VGroup(T("ignites hydrogen", size=17, color=DANGER, weight=BOLD), T("≈ 20 µJ", size=17, color=DANGER)).arrange(DOWN, buff=0.04).next_to(mie, LEFT, buff=0.12)
        e_val = ValueTracker(0.0)
        fill = always_redraw(lambda: Rectangle(width=0.62, height=max(0.01, m_h * 0.78 * e_val.get_value()), stroke_width=0,
                                               fill_color=GOOD if e_val.get_value() < 1 else DANGER, fill_opacity=0.85)
                             .move_to(m_base + UP * (m_h * 0.78 * e_val.get_value()) / 2))
        e_l = T("spark energy", size=17, color=GOOD).next_to(meter, DOWN, buff=0.15)
        with self.voice(
            "{is}Intrinsic safety removes the ignition source. {limit}Voltage, current and power are limited — {store}and so "
            "is the energy stored in the circuit's capacitance and inductance, one half C V squared and one half L I "
            "squared — {spark}so that even the spark from a broken wire or a short circuit stays below the minimum "
            "ignition energy of the gas. {h2}For hydrogen, that's only about twenty microjoules."
        ) as v:
            self.play(Create(cut), FadeIn(x_ign, scale=1.5), run_time=0.7)
            self.play(Indicate(x_ign, color=DANGER), run_time=0.6)
            v.wait_until("limit")
            self.play(FadeOut(VGroup(tri, cut, x_ign)), FadeIn(circuit), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in limits], lag_ratio=0.25), run_time=1.0)
            v.wait_until("store")
            self.play(Write(eqs[0]), run_time=0.9)
            self.play(Write(eqs[1]), run_time=0.9)
            v.wait_until("spark")
            self.play(FadeIn(meter), FadeIn(mie), FadeIn(mie_l), FadeIn(e_l), run_time=0.6)
            self.add(fill)
            gap_rect = Rectangle(width=0.24, height=0.3, fill_color=BG, fill_opacity=1, stroke_width=0).move_to([gap_x, y1, 0])
            self.add(gap_rect)
            self.play(FadeIn(spark, scale=1.6), FadeIn(brk), e_val.animate.set_value(0.55), run_time=1.0)
            self.play(Flash(spark.get_center(), color=POWER, flash_radius=0.35, line_length=0.15), run_time=0.6)
            v.wait_until("h2")
            margin = Brace(Line([6.2, m_base[1] + m_h * 0.78 * 0.55, 0], [6.2, mie_y, 0]), RIGHT, buff=0.08, color=GOOD)
            margin_l = T("margin", size=16, color=GOOD).next_to(margin, RIGHT, buff=0.06)
            self.play(GrowFromCenter(margin), FadeIn(margin_l), run_time=0.8)
        self.play(FadeOut(VGroup(circuit, eqs, limits, meter, mie, mie_l, fill, e_l, spark, brk, gap_rect, margin, margin_l)), run_time=0.7)

        # ------------------------------------------------------------ protection levels
        hdr = VGroup(T("level", size=20, color=MUTED), T("stays safe with", size=20, color=MUTED), T("allowed in", size=20, color=MUTED))
        rows_data = [("ia", "2 faults", "Zone 0", DANGER), ("ib", "1 fault", "Zone 1", HAZARD), ("ic", "normal operation", "Zone 2", YELLOW_Z2)]
        table = VGroup()
        col_x = [-3.2, 0.0, 3.4]
        for j, h in enumerate(hdr):
            h.move_to([col_x[j], 1.7, 0])
        for i, (lv, ft, zn, col) in enumerate(rows_data):
            y = 0.8 - i * 0.95
            row = VGroup(T(f"Ex {lv}", size=34, color=col, weight=BOLD).move_to([col_x[0], y, 0]),
                         T(ft, size=26, color=TEXT).move_to([col_x[1], y, 0]),
                         T(zn, size=26, color=col, weight=BOLD).move_to([col_x[2], y, 0]))
            table.add(row)
        rule = Line([-5.0, 1.3, 0], [5.0, 1.3, 0], stroke_color=DIM, stroke_width=1.5)
        with self.voice(
            "{ia}Protection level “i-a” means the circuit stays safe even with two simultaneous faults. "
            "That's what's required to enter Zone 0."
        ) as v:
            self.play(FadeIn(hdr), Create(rule), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in table], lag_ratio=0.25), run_time=1.3)
            hl = SurroundingRectangle(table[0], color=DANGER, buff=0.18, corner_radius=0.12)
            self.play(Create(hl), table[1].animate.set_opacity(0.4), table[2].animate.set_opacity(0.4), run_time=0.8)
        self.play(FadeOut(VGroup(hdr, rule, table, hl)), run_time=0.6)

        # ------------------------------------------------------------ entity concept vs 2-WISE
        left = panel(6.2, 4.6).move_to([-3.45, -0.35, 0])
        lt = VGroup(icon("calculator", MUTED, 0.45), T("classic: entity calculation", size=22, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.15)
        lt.next_to(left.get_top(), DOWN, buff=0.3)
        ineq = VGroup(
            TeX(r"U_o \le U_i", size=34), TeX(r"I_o \le I_i", size=34), TeX(r"P_o \le P_i", size=34),
            TeX(r"C_i + C_{\text{cable}} \le C_o", size=34), TeX(r"L_i + L_{\text{cable}} \le L_o", size=34),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(lt, DOWN, buff=0.35)
        note_l = T("for every loop, every cable", size=17, color=MUTED).next_to(ineq, DOWN, buff=0.25)
        right = panel(6.2, 4.6).move_to([3.45, -0.35, 0])
        rt = VGroup(icon("puzzle", HAZARD, 0.45), T("2-WISE: matching profiles", size=22, color=TEXT, weight=BOLD)).arrange(RIGHT, buff=0.15)
        rt.next_to(right.get_top(), DOWN, buff=0.3)
        p1 = puzzle_piece(2.3, 1.45, "right", APL, [("field switch port", 16, MUTED, NORMAL), ("2-WISE · ia", 20, TEXT, BOLD), ("SPAA", 18, APL, BOLD)], tab=True)
        p2 = puzzle_piece(2.3, 1.45, "left", HAZARD, [("instrument", 16, MUTED, NORMAL), ("2-WISE · ia", 20, TEXT, BOLD), ("SLAA", 18, HAZARD, BOLD)], tab=False)
        p1.move_to([2.05, -0.15, 0])
        p2.move_to([5.3, -0.15, 0])
        spur_note = T("spur cable up to 200 m", size=18, color=MUTED).move_to([3.45, -1.55, 0])
        ok = VGroup(check(GOOD, 0.35, 6), T("labels match → done", size=22, color=GOOD, weight=BOLD)).arrange(RIGHT, buff=0.15).move_to([3.45, -2.2, 0])
        with self.voice(
            "{calc}Traditionally, every intrinsically safe loop needed a calculation: does the source's voltage, current "
            "and power fit the device, and does the cable's capacitance and inductance fit what's left? "
            "{wise}2-WISE replaces that with predefined port profiles. {match}A 2-WISE field-switch port and a 2-WISE "
            "instrument with matching profiles are designed to be safe together, on up to two hundred meters of spur "
            "cable. {done}You compare the labels, and you're done — much like FISCO did for fieldbus."
        ) as v:
            self.play(FadeIn(left), FadeIn(lt), run_time=0.6)
            self.play(LaggedStart(*[Write(i) for i in ineq], lag_ratio=0.35), FadeIn(note_l), run_time=v.until("wise", 2.0))
            self.play(FadeIn(right), FadeIn(rt), run_time=0.6)
            strike = Line(ineq.get_corner(UL) + LEFT * 0.2, ineq.get_corner(DR) + RIGHT * 0.2, stroke_color=DANGER, stroke_width=5)
            self.play(Create(strike), VGroup(ineq, note_l).animate.set_opacity(0.35), run_time=0.7)
            v.wait_until("match")
            self.play(FadeIn(p1, shift=RIGHT * 0.2), FadeIn(p2, shift=LEFT * 0.2), run_time=0.8)
            self.play(p2.animate.next_to(p1, RIGHT, buff=-0.27), run_time=1.0, rate_func=rush_from)
            self.play(FadeIn(spur_note), run_time=0.5)
            v.wait_until("done")
            self.play(FadeIn(ok, shift=UP * 0.1), Flash(VGroup(p1, p2).get_center(), color=GOOD, flash_radius=1.6), run_time=0.9)

        cmp = VGroup(
            VGroup(T("CAN", size=26, color=CAN, weight=BOLD), T("intrinsic safety: engineered case by case", size=21, color=TEXT)).arrange(RIGHT, buff=0.2),
            VGroup(T("APL", size=26, color=APL, weight=BOLD), T("intrinsic safety: designed in from day one (2-WISE)", size=21, color=TEXT)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        bgc = panel(cmp.width + 0.6, cmp.height + 0.5)
        box = VGroup(bgc, cmp.move_to(bgc)).move_to(DOWN * 3.15)
        with self.voice(
            "{can}CAN has no standardized plug-and-play equivalent: intrinsically safe CAN systems exist, but they're "
            "engineered case by case. {apl}For APL, intrinsic safety was a design goal from day one."
        ) as v:
            self.play(VGroup(left, lt, ineq, note_l, strike, right, rt, p1, p2, spur_note, ok).animate.shift(UP * 0.45).scale(0.92), run_time=0.6)
            self.play(FadeIn(bgc), FadeIn(cmp[0], shift=UP * 0.1), run_time=0.7)
            v.wait_until("apl")
            self.play(FadeIn(cmp[1], shift=UP * 0.1), run_time=0.7)
        self.wait(0.6)
        self.clear(run_time=0.7)
