import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *


def bump(x, w):
    return np.exp(-(np.asarray(x) / w) ** 2)


def pam(levels, tau):
    """Smooth PAM-3 waveform (raised-cosine edges) evaluated at symbol time tau (array)."""
    tau = np.asarray(tau, dtype=float)
    k = np.floor(tau).astype(int)
    frac = tau - k
    n = len(levels)
    a = levels[k % n]
    b = levels[(k + 1) % n]
    w = np.where(frac < 0.62, 0.0, 0.5 - 0.5 * np.cos(np.pi * (frac - 0.62) / 0.38))
    return a + (b - a) * w


def ac_source(r=0.3, color=APL):
    c = Circle(r, stroke_color=color, stroke_width=2.5)
    xs = np.linspace(-0.6 * r, 0.6 * r, 40)
    s = VMobject().set_points_smoothly(np.stack([xs, 0.35 * r * np.sin(xs / r * 5.2), 0 * xs], 1)).set_stroke(color, 2.5)
    return VGroup(c, s.move_to(c))


def amp_tri(color=TEXT, size=0.55, direction=RIGHT):
    t = Triangle(fill_color=PANEL, fill_opacity=1, stroke_color=color, stroke_width=2.5).scale(size / 2)
    ang = {tuple(RIGHT): -PI / 2, tuple(LEFT): PI / 2}[tuple(direction)]
    return t.rotate(ang)


class Hybrid(APLScene):
    def construct(self):
        self.tag = corner_tag("06 · From bits to symbols")
        self.add(self.tag)

        jm = JourneyMap()
        with self.voice("{map}Our symbols are on the wire. But the far end is transmitting too — at the same time, on the same two wires.") as v:
            self.play(FadeIn(jm), run_time=0.8)
            self.play(*jm.focus("duplex"), run_time=0.8)
        self.clear(run_time=0.5)
        self.chapter(7, "Two directions, one pair", "Hybrids, echoes, and adaptive cancellation", color=VIOLET)

        # ------------------------------------------------------------ superposition on a linear line
        x0, x1, y = -5.8, 5.8, 0.6
        base = Line([x0, y, 0], [x1, y, 0], stroke_color=DIM, stroke_width=2)
        tt = ValueTracker(0.0)
        a_end = device("A", None, APL, width=0.8, height=0.8, label_size=24).next_to([x0, y, 0], LEFT, buff=0.1)
        b_end = device("B", None, VIOLET, width=0.8, height=0.8, label_size=24).next_to([x1, y, 0], RIGHT, buff=0.1)
        xs = np.linspace(x0, x1, 500)

        def waves():
            t = tt.get_value()
            pa = bump(xs - (x0 + 0.8 + 5.0 * t), 0.45)
            pb = -0.7 * bump(xs - (x1 - 0.8 - 5.0 * t), 0.6)
            g = VGroup(
                VMobject().set_points_as_corners(np.stack([xs, y + 1.0 * pa + 1.45, 0 * xs], 1)).set_stroke(APL, 3),
                VMobject().set_points_as_corners(np.stack([xs, y + 1.0 * pb - 1.45, 0 * xs], 1)).set_stroke(VIOLET, 3),
                VMobject().set_points_as_corners(np.stack([xs, y + 1.0 * (pa + pb), 0 * xs], 1)).set_stroke(WHITE_SOFT, 4),
            )
            return g

        wv = always_redraw(waves)
        la = T("A → B", size=18, color=APL, weight=BOLD).move_to([x0 + 0.5, y + 2.3, 0])
        lb = T("B → A", size=18, color=VIOLET, weight=BOLD).move_to([x1 - 0.5, y - 2.15, 0])
        ls = T("on the wire: the sum", size=18, color=WHITE_SOFT, weight=BOLD).move_to([0, y + 0.95, 0]).shift(LEFT * 3.6)
        dal = TeX(r"v(x,t) = ", r"v^{+}(x - c\,t)", r"+", r"v^{-}(x + c\,t)", size=42).move_to([0, -2.75, 0])
        dal[1].set_color(APL)
        dal[3].set_color(VIOLET)
        with self.voice(
            "{q}How can that possibly work? {linear}Because the cable is linear. Two waves travelling in opposite directions "
            "simply pass through each other. {sum}The voltage anywhere on the line is just their sum: v-plus of x minus c t, "
            "plus v-minus of x plus c t — d'Alembert's solution again. {can}On a CAN bus, two transmitters at once means a "
            "contest between states, settled by arbitration. On a linear line, it's just addition."
        ) as v:
            self.play(Create(base), FadeIn(a_end), FadeIn(b_end), run_time=0.8)
            v.wait_until("linear")
            self.add(wv)
            self.play(FadeIn(la), FadeIn(lb), FadeIn(ls), tt.animate.set_value(1.15), run_time=4.0, rate_func=linear)
            v.wait_until("sum")
            tt.set_value(0.0)
            self.play(Write(dal), tt.animate.set_value(1.15), run_time=4.0, rate_func=linear)
            v.wait_until("can")
            tt.set_value(0.0)
            self.play(tt.animate.set_value(1.15), run_time=v.until_end(3.0), rate_func=linear)
        self.remove(wv)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the telephone hybrid
        ph_l = icon("phone", TEXT, 0.75).move_to([-6.2, 0.3, 0])
        ph_r = icon("phone", TEXT, 0.75).move_to([6.2, 0.3, 0])
        hy_l = device("hybrid", None, VIOLET, width=1.25, height=1.0, label_size=18).move_to([-3.9, 0.3, 0])
        hy_r = device("hybrid", None, VIOLET, width=1.25, height=1.0, label_size=18).move_to([3.9, 0.3, 0])
        two_l = twisted_pair([ph_l.get_right() + RIGHT * 0.1, hy_l.get_left()], TEXT, amp=0.05, pitch=0.25)
        two_r = twisted_pair([hy_r.get_right(), ph_r.get_left() + LEFT * 0.1], TEXT, amp=0.05, pitch=0.25)
        top_y, bot_y = 0.75, -0.15
        go = VGroup(Line([hy_l.get_right()[0], top_y, 0], [-0.4, top_y, 0]), Line([0.4, top_y, 0], [hy_r.get_left()[0], top_y, 0])).set_stroke(APL, 3)
        ret = VGroup(Line([hy_r.get_left()[0], bot_y, 0], [0.4, bot_y, 0]), Line([-0.4, bot_y, 0], [hy_l.get_right()[0], bot_y, 0])).set_stroke(GOOD, 3)
        amp1 = amp_tri(APL, 0.6, RIGHT).move_to([0, top_y, 0])
        amp2 = amp_tri(GOOD, 0.6, LEFT).move_to([0, bot_y, 0])
        lbl2 = T("2 wires", size=16, color=MUTED).next_to(two_l, DOWN, buff=0.25)
        lbl2r = T("2 wires", size=16, color=MUTED).next_to(two_r, DOWN, buff=0.25)
        lbl4 = T("long distance: 4 wires, with amplifiers", size=17, color=MUTED).move_to([0, 1.35, 0])
        echo = CurvedArrow([hy_r.get_left()[0] + 0.05, top_y - 0.05, 0], [hy_r.get_left()[0] + 0.05, bot_y + 0.05, 0], angle=PI * 0.9,
                           color=DANGER, stroke_width=4, tip_length=0.14).shift(LEFT * 0.35)
        echo_l = VGroup(T("hybrid leaks:", size=17, color=DANGER, weight=BOLD), T("the talker hears an echo", size=17, color=DANGER)).arrange(DOWN, buff=0.04)
        echo_l.move_to([2.2, -1.25, 0])
        pkt = packet(APL, 0.08)
        path_go = VMobject().set_points_as_corners([ph_l.get_right(), [hy_l.get_right()[0], top_y, 0], [hy_r.get_left()[0], top_y, 0]])
        path_back = VMobject().set_points_as_corners([[hy_r.get_left()[0], top_y, 0], [hy_r.get_left()[0] - 0.2, 0.3, 0], [hy_r.get_left()[0], bot_y, 0],
                                                      [hy_l.get_right()[0], bot_y, 0], ph_l.get_right()])
        with self.voice(
            "{phone}Telephones have relied on this for well over a century. Your voice and the caller's voice share one pair "
            "of wires, and a circuit called a hybrid separates them, so that you hear the far end — and only a little of "
            "yourself. {four}Long-distance lines with amplifiers split the two directions onto four wires. {echo}The hybrids "
            "at the ends were never perfectly balanced, so a little of your voice leaked back into the return path — which "
            "is why long-distance calls used to come with an echo."
        ) as v:
            self.play(FadeIn(ph_l), FadeIn(ph_r), run_time=0.6)
            self.play(Create(two_l), Create(two_r), FadeIn(hy_l), FadeIn(hy_r), FadeIn(lbl2), FadeIn(lbl2r), run_time=1.2)
            v.wait_until("four")
            self.play(Create(go), Create(ret), FadeIn(amp1), FadeIn(amp2), FadeIn(lbl4), run_time=1.4)
            v.wait_until("echo")
            self.play(MoveAlongPath(pkt, path_go), run_time=1.6, rate_func=linear)
            self.play(Create(echo), FadeIn(echo_l), pkt.animate.set_color(DANGER), run_time=0.8)
            self.play(MoveAlongPath(pkt, path_back), run_time=2.0, rate_func=linear)
            self.play(FadeOut(pkt), run_time=0.3)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the transceiver's hybrid circuit
        sx, gy, sy = -5.7, -2.3, 1.55
        src = ac_source(0.32, APL).move_to([sx, -1.35, 0])
        node_s = np.array([sx, sy, 0])
        node_j = np.array([sx, -0.2, 0])
        rs = resistor(1.1, color=TEXT).move_to([sx + 1.35, sy, 0])
        node_a = np.array([sx + 2.5, sy, 0])
        rr = resistor(1.1, color=TEXT).move_to([sx + 1.35, -0.2, 0])
        node_b = np.array([sx + 2.5, -0.2, 0])
        zr = resistor(0.9, color=VIOLET).rotate(PI / 2).move_to([node_b[0], -1.25, 0])
        gnd = Line([sx, gy, 0], [node_b[0] + 4.6, gy, 0], stroke_color=TEXT, stroke_width=2.5)
        wires = VGroup(
            Line(src.get_top(), node_s), Line(node_s, rs.get_left()), Line(rs.get_right(), node_a), Line(src.get_bottom(), [sx, gy, 0]),
        ).set_stroke(TEXT, 2.5)
        wires_rep = VGroup(
            Line(node_j, rr.get_left()), Line(rr.get_right(), node_b), Line(node_b, zr.get_top()), Line(zr.get_bottom(), [node_b[0], gy, 0]),
        ).set_stroke(TEXT, 2.5)
        line_start = node_a + RIGHT * 0.05
        cable_c = twisted_pair([line_start, line_start + RIGHT * 4.3], APL, amp=0.06, pitch=0.3)
        far = device("far end", None, VIOLET, width=1.3, height=0.9, label_size=18).next_to(cable_c, RIGHT, buff=0.08)
        lbls = VGroup(
            T("100 Ω", size=17, color=TEXT).next_to(rs, UP, buff=0.12),
            T("100 Ω", size=17, color=TEXT).next_to(rr, UP, buff=0.12),
            T("line model", size=15, color=VIOLET).next_to(zr, RIGHT, buff=0.12),
            T("1 km, Z₀ = 100 Ω", size=16, color=APL).next_to(cable_c, UP, buff=0.15),
            TeX(r"v_{tx}", size=30, color=APL).next_to(src, LEFT, buff=0.15),
            T("A", size=20, color=TEXT, weight=BOLD).next_to(node_a, UP, buff=0.12).shift(RIGHT * 0.15),
            T("B", size=20, color=TEXT, weight=BOLD).next_to(node_b, UP, buff=0.12).shift(RIGHT * 0.15),
            T("replica", size=16, color=VIOLET, weight=BOLD).next_to(rr, DOWN, buff=0.15),
        )
        dots = VGroup(*[Dot(p, radius=0.06, color=TEXT) for p in (node_s, node_a, node_b, node_j)])
        damp = amp_tri(TEXT, 0.95, RIGHT).move_to([-0.6, -0.95, 0])
        plus = T("+", size=22, color=TEXT, weight=BOLD).move_to(damp.get_left() + RIGHT * 0.22 + UP * 0.2)
        minus = T("−", size=22, color=TEXT, weight=BOLD).move_to(damp.get_left() + RIGHT * 0.22 + DOWN * 0.2)
        wire_a = VMobject().set_points_as_corners([[node_a[0] + 0.6, node_a[1], 0], [node_a[0] + 0.6, -0.75, 0], [damp.get_left()[0], -0.75, 0]]).set_stroke(TEXT, 2.2)
        wire_b = VMobject().set_points_as_corners([node_b, [node_b[0] + 0.25, node_b[1], 0], [node_b[0] + 0.25, -1.15, 0], [damp.get_left()[0], -1.15, 0]]).set_stroke(TEXT, 2.2)
        dot_a2 = Dot([node_a[0] + 0.6, node_a[1], 0], radius=0.05, color=TEXT)
        out_arrow = Arrow(damp.get_right(), damp.get_right() + RIGHT * 1.0, buff=0.02, stroke_width=3, color=VIOLET, tip_length=0.14)
        out_lbl = T("to the receiver", size=17, color=VIOLET, weight=BOLD).next_to(out_arrow, RIGHT, buff=0.12)

        # node waveforms
        rng = np.random.default_rng(8)
        own = rng.integers(-1, 2, 60)
        farv = rng.integers(-1, 2, 60)
        taus = np.linspace(0, 14, 300)

        def scope_at(center, title, vals, col):
            sc = scope(2.6, 1.05, title, col).move_to(center)
            tr = trace_in(sc.box, taus, vals, col, 2.4, y_range=(-1.25, 1.25))
            return VGroup(sc, tr)

        va = 0.5 * pam(own, taus) + 0.3 * pam(farv, taus + 3)
        vb = 0.5 * pam(own, taus)
        vo = 0.3 * pam(farv, taus + 3)
        sc_a = scope_at([4.85, 2.75, 0], "A: own half + far end", va, TEXT)
        sc_b = scope_at([4.85, 0.95, 0], "B: own half (replica)", vb, APL)
        sc_o = scope_at([4.85, -0.85, 0], "A − B: far end only", vo * 2.2, VIOLET)
        sc_a.shift(LEFT * 0.0)
        eq1 = TeX(r"v_A = \tfrac{1}{2}v_{tx} + v_{far}", size=32).move_to([-4.5, -3.1, 0])
        eq2 = TeX(r"v_B = \tfrac{1}{2}v_{tx}", size=32, color=APL).move_to([-1.55, -3.1, 0])
        eq3 = TeX(r"v_A - v_B = v_{far}", size=32, color=VIOLET).move_to([1.2, -3.1, 0])
        circuit = VGroup(src, rs, rr, zr, gnd, wires, wires_rep, cable_c, far, lbls, dots)
        circuit_grp = VGroup(circuit, damp, plus, minus, wire_a, wire_b, dot_a2, out_arrow, out_lbl)
        with self.voice(
            "{circuit}Inside an APL transceiver, the hybrid works like this. The transmitter drives the line through a "
            "source resistance equal to the cable's hundred ohms. {half}With the line matched, the voltage at the terminals "
            "is half of the transmitter's voltage — plus whatever arrives from the far end. {replica}A replica network, "
            "built from the same resistor and a model of the line's impedance, produces a copy of just that half. "
            "{sub}Subtract the two, and ideally your own signal vanishes, leaving only the far end."
        ) as v:
            self.play(FadeIn(src), Create(wires), FadeIn(rs), FadeIn(lbls[0]), FadeIn(lbls[4]), FadeIn(dots[0]), run_time=1.2)
            self.play(Create(cable_c), FadeIn(far), FadeIn(lbls[3]), FadeIn(lbls[5]), FadeIn(dots[1]), Create(gnd), run_time=1.0)
            v.wait_until("half")
            self.play(FadeIn(sc_a), Write(eq1), run_time=1.2)
            v.wait_until("replica")
            self.play(FadeIn(rr), FadeIn(zr), Create(wires_rep), FadeIn(lbls[1]), FadeIn(lbls[2]), FadeIn(lbls[6]), FadeIn(lbls[7]), FadeIn(dots[2]), FadeIn(dots[3]), run_time=1.0)
            self.play(FadeIn(sc_b), Write(eq2), run_time=1.0)
            v.wait_until("sub")
            self.play(FadeIn(damp), FadeIn(plus), FadeIn(minus), Create(wire_a), Create(wire_b), FadeIn(dot_a2), run_time=1.0)
            self.play(GrowArrow(out_arrow), FadeIn(out_lbl), FadeIn(sc_o), Write(eq3), run_time=1.2)

        # reality: imperfect replica + reflections
        echo_res = 0.12 * pam(own, taus - 0.4) + 0.06 * pam(own, taus - 3.2)
        sc_r = scope_at([4.85, -2.65, 0], "in reality: far end + leftover echo", (vo + echo_res) * 2.2, DANGER)
        with self.voice(
            "{real}In reality, the cable's impedance isn't exactly a hundred ohms at every frequency, and every connector "
            "and splice reflects a little echo. {part}So the analog hybrid removes a good part of the echo — but nowhere "
            "near enough."
        ) as v:
            self.play(FadeIn(sc_r, shift=UP * 0.1), run_time=1.0)
            v.wait_until("part")
            self.play(Indicate(sc_r, color=DANGER, scale_factor=1.04), run_time=1.0)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the echo budget
        ax = Axes(x_range=[0, 4, 1], y_range=[-60, 0, 10], x_length=7.0, y_length=5.2,
                  axis_config={"stroke_color": DIM, "include_tip": False, "include_ticks": False}).move_to([-1.6, -0.35, 0])
        yt = tick_labels(ax, [0, -10, -20, -30, -40, -50, -60], "y", texts=["0 dB", "−10", "−20", "−30", "−40", "−50", "−60"], size=15)

        def bar(i, db, col, name, sub):
            top = ax.c2p(i + 0.5, 0)
            bot = ax.c2p(i + 0.5, db)
            r = Rectangle(width=1.0, height=top[1] - bot[1], fill_color=col, fill_opacity=0.85, stroke_width=0)
            r.move_to((top + bot) / 2)
            lab = VGroup(T(name, size=17, color=col, weight=BOLD), T(sub, size=14, color=MUTED)).arrange(DOWN, buff=0.04)
            lab.next_to(r, DOWN, buff=0.12)
            return VGroup(r, lab)

        b_own = bar(0, -1.0, APL, "own signal", "2.4 Vpp")
        b_far = bar(1, -25.6, VIOLET, "far end", "≈ 0.13 Vpp")
        b_need = bar(2, -50, GOOD, "echo + noise", "must stay below")
        b_own[0].stretch_to_fit_height(0.12).align_to(ax.c2p(0, 0), UP)
        b_own[1].next_to(b_own[0], DOWN, buff=0.12)
        b_far[0].stretch_to_fit_height(0.12).move_to(ax.c2p(1.5, -25.6))
        b_far[1].next_to(b_far[0], DOWN, buff=0.12)
        b_need[0].stretch_to_fit_height(0.12).move_to(ax.c2p(2.5, -50))
        b_need[1].next_to(b_need[0], DOWN, buff=0.12)
        for b in (b_own, b_far, b_need):
            b[0].stretch_to_fit_width(1.1)
        arr1 = DoubleArrow(ax.c2p(1.05, -1.5), ax.c2p(1.05, -25.0), buff=0, stroke_width=3, color=HAZARD, tip_length=0.14)
        arr1_l = T("cable: 25.6 dB", size=16, color=HAZARD).next_to(arr1, LEFT, buff=0.1)
        arr2 = DoubleArrow(ax.c2p(2.05, -26.2), ax.c2p(2.05, -49.4), buff=0, stroke_width=3, color=GOOD, tip_length=0.14)
        arr2_l = T("≈ 20 dB SNR + margin", size=16, color=GOOD).next_to(arr2, RIGHT, buff=0.1).shift(UP * 0.3)
        total = VGroup(T("≈ 50 dB", size=40, color=TEXT, weight=BOLD), T("of echo suppression needed", size=20, color=MUTED),
                       T("a factor of ≈ 300 in amplitude", size=20, color=MUTED)).arrange(DOWN, buff=0.1).move_to([4.6, 0.4, 0])
        with self.voice(
            "{budget}How much is enough? Our own signal leaves at 2.4 volts peak to peak. {far}The far end's signal arrives up "
            "to 25.6 dB weaker: about an eighth of a volt. {snr}To tell plus, zero and minus apart reliably, the receiver "
            "needs about 20 dB of signal-to-noise ratio, plus some margin. {need}So the leftover echo has to end up around "
            "fifty dB below our own transmission — a factor of about three hundred in amplitude. {analog}Across all cables, "
            "lengths and temperatures, no fixed analog circuit can manage that on its own."
        ) as v:
            self.play(Create(ax), FadeIn(yt), run_time=0.7)
            self.play(FadeIn(b_own), run_time=0.7)
            v.wait_until("far")
            self.play(FadeIn(b_far), GrowFromCenter(arr1), FadeIn(arr1_l), run_time=1.0)
            v.wait_until("snr")
            self.play(FadeIn(b_need), GrowFromCenter(arr2), FadeIn(arr2_l), run_time=1.0)
            v.wait_until("need")
            self.play(FadeIn(total, shift=LEFT * 0.1), run_time=0.9)
        self.wait(0.3)
        self.clear(run_time=0.7)
