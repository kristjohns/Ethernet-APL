import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apl.base import APLScene
from apl.phy import *
from apl.style import *
from apl.widgets import *


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def bump(x, w):
    return np.exp(-(np.asarray(x) / w) ** 2)


class Waves(APLScene):
    def construct(self):
        self.tag = corner_tag("05 · The wire is a waveguide")
        self.add(self.tag)

        # ------------------------------------------------------------ masses and springs  <->  L and C
        n = 11
        xs_m = np.linspace(-5.9, 5.6, n)
        y_m = 1.75
        y_lt, y_lb = -0.75, -2.35
        clk = ValueTracker(-1.0)
        rate, width, d = 3.4, 1.6, 0.34    # masses per second, edge width [masses], shove distance

        def disp(i):
            return d * smoothstep((clk.get_value() * rate - i) / width + 0.5)

        def vel(i):
            h = 0.02
            t = clk.get_value()
            a = d * smoothstep(((t + h) * rate - i) / width + 0.5)
            b = d * smoothstep(((t - h) * rate - i) / width + 0.5)
            return (a - b) / (2 * h)

        def chain():
            g = VGroup()
            u = [disp(i) for i in range(n)]
            g.add(Line([-6.5, y_m - 0.3, 0], [6.3, y_m - 0.3, 0], stroke_color=DIM, stroke_width=2))
            for i in range(n - 1):
                a = xs_m[i] + u[i] + 0.21
                b = xs_m[i + 1] + u[i + 1] - 0.21
                comp = (u[i] - u[i + 1]) / d
                pts = [[a, y_m, 0]]
                k = 8
                for j in range(k):
                    pts.append([a + (b - a) * (j + 0.5) / k, y_m + (0.12 if j % 2 == 0 else -0.12), 0])
                pts.append([b, y_m, 0])
                col = interpolate_color(ManimColor(MUTED), ManimColor(GOOD), float(np.clip(comp * 2.2, 0, 1)))
                g.add(VMobject().set_points_as_corners(pts).set_stroke(col, 2.6 + 3 * max(0, comp)))
            for i in range(n):
                sp = abs(vel(i)) / (d * rate / width * 1.5)
                col = interpolate_color(ManimColor(PANEL_EDGE), ManimColor(BLUE), float(np.clip(sp, 0, 1)))
                g.add(Square(0.42, fill_color=col, fill_opacity=1, stroke_color=BLUE, stroke_width=2).move_to([xs_m[i] + u[i], y_m, 0]))
            return g

        # LC ladder with the same topology: inductor i <-> mass i, capacitor i <-> spring i
        ladder = VGroup()
        inds, caps = [], []
        for i in range(n):
            ind = inductor(0.62, color=TEXT, loops=3).move_to([xs_m[i], y_lt, 0])
            inds.append(ind)
            ladder.add(ind)
        for i in range(n - 1):
            ladder.add(Line(inds[i].get_right(), inds[i + 1].get_left()))
            xc = (xs_m[i] + xs_m[i + 1]) / 2
            c = capacitor(0.55, color=TEXT).rotate(PI / 2).move_to([xc, (y_lt + y_lb) / 2, 0])
            caps.append(c)
            ladder.add(Line([xc, y_lt, 0], c.get_top()), c, Line(c.get_bottom(), [xc, y_lb, 0]), Dot([xc, y_lt, 0], radius=0.035))
        ladder.add(Line([xs_m[0] - 0.55, y_lt, 0], inds[0].get_left()), Line([xs_m[0] - 0.55, y_lb, 0], [xs_m[-1] + 0.4, y_lb, 0]))
        ladder.set_stroke(TEXT, 2.2)

        def ladder_live():
            g = VGroup()
            u = [disp(i) for i in range(n)]
            for i in range(n - 1):
                comp = max(0.0, (u[i] - u[i + 1]) / d)
                xc = (xs_m[i] + xs_m[i + 1]) / 2 + 0.2
                h = 1.25 * comp
                if h > 0.01:
                    g.add(Rectangle(width=0.1, height=h, fill_color=GOOD, fill_opacity=0.9, stroke_width=0)
                          .move_to([xc, y_lb + h / 2 + 0.05, 0]))
            for i in range(n):
                sp = vel(i) / (d * rate / width * 1.5)
                if sp > 0.05:
                    g.add(Arrow([xs_m[i] - 0.32, y_lt + 0.33, 0], [xs_m[i] - 0.32 + 0.64 * min(1, sp) + 0.05, y_lt + 0.33, 0],
                                buff=0, stroke_width=4, color=BLUE, tip_length=0.12, max_tip_length_to_length_ratio=0.5))
            return g

        ch = always_redraw(chain)
        lv = always_redraw(ladder_live)
        hand = Arrow([-7.0, y_m, 0], [-6.25, y_m, 0], buff=0, stroke_width=6, color=POWER, tip_length=0.2)
        legend = VGroup(
            VGroup(Square(0.22, fill_color=BLUE, fill_opacity=1, stroke_width=0), T("mass", size=17, color=TEXT),
                   T("↔", size=17, color=MUTED), TeX(r"L'\Delta x", size=24, color=BLUE)).arrange(RIGHT, buff=0.12),
            VGroup(T("spring compliance", size=17, color=TEXT), T("↔", size=17, color=MUTED), TeX(r"C'\Delta x", size=24, color=GOOD)).arrange(RIGHT, buff=0.12),
            VGroup(T("force", size=17, color=GOOD), T("↔", size=17, color=MUTED), T("voltage", size=17, color=GOOD)).arrange(RIGHT, buff=0.12),
            VGroup(T("velocity", size=17, color=BLUE), T("↔", size=17, color=MUTED), T("current", size=17, color=BLUE)).arrange(RIGHT, buff=0.12),
        ).arrange(RIGHT, buff=0.6).move_to([0, 0.45, 0])

        with self.voice(
            "{analog}If the wave equation feels abstract, picture a chain of masses joined by springs. {kick}Give the first "
            "mass a shove, and a compression pulse runs down the chain. {map}A transmission line is the very same system. "
            "Inductance plays the role of mass: it resists any change in current, as mass resists any change in velocity. "
            "{cap}Capacitance plays the role of the springs: it stores energy as the voltage builds up. {roles}Voltage is the "
            "force; current is the velocity."
        ) as v:
            self.add(ch)
            self.play(FadeIn(ch), run_time=0.6)
            v.wait_until("kick")
            self.play(GrowArrow(hand), run_time=0.4)
            self.play(clk.animate.set_value(4.0), run_time=3.2, rate_func=linear)
            v.wait_until("map")
            clk.set_value(-1.0)
            self.play(FadeOut(hand), Create(ladder), run_time=1.8)
            self.add(lv)
            self.play(FadeIn(legend[0]), run_time=0.5)
            v.wait_until("cap")
            self.play(FadeIn(legend[1]), run_time=0.5)
            v.wait_until("roles")
            self.play(FadeIn(legend[2]), FadeIn(legend[3]), run_time=0.6)
            self.play(clk.animate.set_value(4.2), run_time=3.4, rate_func=linear)
        self.remove(ch, lv)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ the speed
        c1 = TeX(r"c", r"=", r"\frac{1}{\sqrt{L'C'}}", size=58).move_to([-3.3, 2.0, 0])
        c1[2].set_color(APL)
        c2 = TeX(r"c_{\text{string}}", r"=", r"\sqrt{\frac{T}{\mu}}", size=58).move_to([3.3, 2.0, 0])
        c2[2].set_color(BLUE)
        num = TeX(r"\frac{1}{\sqrt{0.5\,\mu\mathrm{H/m}\times 50\,\mathrm{pF/m}}}", r"=", r"2\times10^{8}\ \mathrm{m/s}", size=44)
        num[2].set_color(APL)
        num.move_to([0, 0.35, 0])
        facts = VGroup(pill("≈ ⅔ of the speed of light", APL, size=22), pill("5 ns per meter", APL, size=22)).arrange(RIGHT, buff=0.5)
        facts.next_to(num, DOWN, buff=0.5)
        with self.voice(
            "{speed}The wave speed follows directly: one over the square root of L C — just as a string's wave speed is the "
            "square root of tension over mass per length. {numbers}For APL's fieldbus cable, about half a microhenry and "
            "fifty picofarads per meter give two hundred thousand kilometers per second: two-thirds of the speed of light, "
            "or five nanoseconds per meter."
        ) as v:
            self.play(Write(c1), run_time=1.1)
            self.play(Write(c2), run_time=1.1)
            v.wait_until("numbers")
            self.play(Write(num), run_time=2.0)
            self.play(LaggedStart(*[FadeIn(f, shift=UP * 0.1) for f in facts], lag_ratio=0.4), run_time=1.0)
        self.clear(run_time=0.6)

        # conveyor belt: 1 km = 5 us = 37.5 symbols in flight, both directions
        x0, x1, yc = -6.0, 6.0, 0.0
        n_vis = 37.5
        seq_a = np.random.default_rng(11).integers(-1, 2, 400)
        seq_b = np.random.default_rng(12).integers(-1, 2, 400)
        belt_t = ValueTracker(0.0)
        cab = twisted_pair([[x0, yc, 0], [x1, yc, 0]], APL, amp=0.06, pitch=0.36, width=3)

        def lane(seq, y, col, sgn):
            def f():
                s = belt_t.get_value()
                us = np.linspace(0, 1, 600)
                pos = us * n_vis
                tau = (s - pos) if sgn > 0 else (s - (n_vis - pos))
                k = np.floor(tau).astype(int)
                fr = tau - k
                a = seq[k % len(seq)]
                b = seq[(k - 1) % len(seq)]
                w = smoothstep((fr - 0.0) / 0.22)
                val = b + (a - b) * w
                pts = np.stack([x0 + (x1 - x0) * us, y + 0.42 * val, 0 * us], 1)
                return VMobject().set_points_as_corners(pts).set_stroke(col, 3)
            return always_redraw(f)

        la = lane(seq_a, yc + 1.45, APL, +1)
        lb = lane(seq_b, yc - 1.45, VIOLET, -1)
        ticks = VGroup()
        for i in range(11):
            x = x0 + (x1 - x0) * i / 10
            ticks.add(Line([x, yc - 0.18, 0], [x, yc + 0.18, 0], stroke_color=DIM, stroke_width=2))
        km = VGroup(T("0", size=16, color=MUTED).next_to([x0, yc - 0.2, 0], DOWN, buff=0.08),
                    T("500 m", size=16, color=MUTED).next_to([0, yc - 0.2, 0], DOWN, buff=0.08),
                    T("1 km", size=16, color=MUTED).next_to([x1, yc - 0.2, 0], DOWN, buff=0.08))
        dir_a = T("A → B", size=18, color=APL, weight=BOLD).next_to([x0, yc + 2.15, 0], RIGHT, buff=0)
        dir_b = T("B → A", size=18, color=VIOLET, weight=BOLD).next_to([x1, yc - 2.15, 0], LEFT, buff=0)
        brace = BraceBetweenPoints([x0, yc + 2.35, 0], [x1, yc + 2.35, 0], UP, color=MUTED)
        btxt = T("1 km  =  5 µs  =  37.5 symbols in flight", size=24, color=TEXT, weight=BOLD).next_to(brace, UP, buff=0.12)
        belt_t.add_updater(lambda m, dt: m.increment_value(dt * 2.4))
        with self.voice(
            "{flight}So a kilometer of cable is five microseconds long. {conv}That's thirty-seven and a half APL symbols in "
            "flight, in each direction, at every moment. {belt}The cable isn't a wire that connects two points instantly. "
            "It's a conveyor belt."
        ) as v:
            self.add(belt_t)
            self.play(Create(cab), FadeIn(ticks), FadeIn(km), run_time=1.0)
            self.add(la)
            self.play(FadeIn(la), FadeIn(dir_a), run_time=0.6)
            v.wait_until("conv")
            self.play(GrowFromCenter(brace), FadeIn(btxt, shift=DOWN * 0.1), run_time=0.9)
            self.add(lb)
            self.play(FadeIn(lb), FadeIn(dir_b), run_time=0.6)
            v.wait_until("belt")
            self.wait(v.until_end(0.5))
        self.wait(1.2)
        belt_t.clear_updaters()
        self.remove(la, lb, belt_t)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ characteristic impedance
        lx0, lx1, ly_t, ly_b = -4.8, 5.6, 1.35, 0.25
        top_w = Line([lx0, ly_t, 0], [lx1, ly_t, 0], stroke_color=TEXT, stroke_width=3)
        bot_w = Line([lx0, ly_b, 0], [lx1, ly_b, 0], stroke_color=TEXT, stroke_width=3)
        src = dc_source(0.3, POWER).move_to([lx0 - 0.75, (ly_t + ly_b) / 2, 0])
        src_w = VGroup(Line(src.get_top(), [src.get_x(), ly_t, 0]), Line([src.get_x(), ly_t, 0], [lx0, ly_t, 0]),
                       Line(src.get_bottom(), [src.get_x(), ly_b, 0]), Line([src.get_x(), ly_b, 0], [lx0, ly_b, 0])).set_stroke(TEXT, 3)
        edge = ValueTracker(lx0)

        def charged():
            xe = edge.get_value()
            g = VGroup()
            if xe > lx0 + 0.02:
                g.add(Rectangle(width=xe - lx0, height=ly_t - ly_b - 0.08, fill_color=POWER, fill_opacity=0.16, stroke_width=0)
                      .move_to([(lx0 + xe) / 2, (ly_t + ly_b) / 2, 0]))
                for x in np.arange(lx0 + 0.25, xe - 0.1, 0.5):
                    g.add(T("+", size=20, color=POWER, weight=BOLD).move_to([x, ly_t - 0.2, 0]))
                    g.add(T("−", size=20, color=BLUE, weight=BOLD).move_to([x, ly_b + 0.2, 0]))
                g.add(Line([xe, ly_t + 0.25, 0], [xe, ly_b - 0.25, 0], stroke_color=POWER, stroke_width=3))
                g.add(Arrow([xe - 1.0, ly_t + 0.22, 0], [xe - 0.1, ly_t + 0.22, 0], buff=0, stroke_width=4, color=BLUE, tip_length=0.14))
            return g

        chg = always_redraw(charged)
        cv = Arrow([lx0 + 1.6, ly_t + 0.7, 0], [lx0 + 1.6 + 1.6, ly_t + 0.7, 0], buff=0, color=APL, stroke_width=3, tip_length=0.14)
        cv_l = T("edge moves at c", size=17, color=APL).next_to(cv, UP, buff=0.05)
        z1 = TeX(r"I", r"=", r"C'\,c\,V", size=44).move_to([-3.6, -1.15, 0])
        z1[2].set_color(GOOD)
        z2 = TeX(r"Z_0", r"=", r"\frac{V}{I}", r"=", r"\frac{1}{C'c}", r"=", r"\sqrt{\frac{L'}{C'}}", size=44).move_to([2.0, -1.15, 0])
        z2[6].set_color(APL)
        z3 = TeX(r"\sqrt{\frac{0.5\,\mu\mathrm{H/m}}{50\,\mathrm{pF/m}}}", r"=", r"100\ \Omega", size=40).move_to([0.6, -2.75, 0])
        z3[2].set_color(APL)
        with self.voice(
            "{z0}A travelling wave carries voltage and current in a fixed ratio: the characteristic impedance, Z-naught. "
            "{derive}Here's why. As the edge advances, every second it charges another c meters of cable capacitance to the "
            "voltage V. That takes a current I equals C c V. {result}So V over I is one over C c, which works out to the "
            "square root of L over C. {hundred}For our cable: a hundred ohms. {ohm}You can't measure it with an ohmmeter. "
            "It's the load a fast edge sees, because the edge only knows about the cable it has already charged."
        ) as v:
            self.play(Create(top_w), Create(bot_w), FadeIn(src), Create(src_w), run_time=1.0)
            v.wait_until("derive")
            self.add(chg)
            self.play(edge.animate.set_value(lx1 - 0.3), FadeIn(cv), FadeIn(cv_l), run_time=v.until("result", 2.5), rate_func=linear)
            self.play(Write(z1), run_time=0.9)
            v.wait_until("result")
            self.play(Write(z2), run_time=2.2)
            v.wait_until("hundred")
            self.play(Write(z3), run_time=1.4)
            self.play(Indicate(z3[2], color=APL), run_time=0.7)
        self.remove(chg)
        self.clear(run_time=0.6)

        # water hammer
        py0, py1 = 0.95, 0.15
        px0, px1 = -5.6, 3.4
        pipe = VGroup(Line([px0, py0, 0], [px1, py0, 0]), Line([px0, py1, 0], [px1, py1, 0])).set_stroke(TEXT, 3)
        tank = Rectangle(width=1.3, height=2.2, fill_color=BLUE, fill_opacity=0.25, stroke_color=TEXT, stroke_width=3).move_to([px0 - 0.65, 0.95, 0])
        valve_open = ValueTracker(1.0)
        front = ValueTracker(px1)

        def valve():
            k = valve_open.get_value()
            gate = Rectangle(width=0.16, height=(py0 - py1) * (1 - k) + 0.02, fill_color=DANGER, fill_opacity=1, stroke_width=0)
            gate.move_to([px1 + 0.08, py0 - gate.height / 2, 0])
            body = VGroup(Polygon([px1, py0 + 0.35, 0], [px1 + 0.16, py0 + 0.35, 0], [px1 + 0.16, py0, 0], [px1, py0, 0],
                                  stroke_color=TEXT, stroke_width=2, fill_color=PANEL, fill_opacity=1), gate)
            return body

        def water():
            g = VGroup()
            xf = front.get_value()
            if xf < px1 - 0.01:
                g.add(Rectangle(width=px1 - xf, height=py0 - py1 - 0.06, fill_color=DANGER, fill_opacity=0.35, stroke_width=0)
                      .move_to([(xf + px1) / 2, (py0 + py1) / 2, 0]))
            ph = (self.t * 1.2) % 0.45
            for x in np.arange(px0 + 0.1 + ph, xf, 0.45):
                g.add(Dot([x, (py0 + py1) / 2, 0], radius=0.045, color=BLUE))
            for x in np.arange(max(xf, px0) + 0.1, px1, 0.45):
                g.add(Dot([x, (py0 + py1) / 2, 0], radius=0.045, color=BLUE).set_opacity(0.5))
            return g

        vm, wm = always_redraw(valve), always_redraw(water)
        jk = TeX(r"\Delta p", r"=", r"\rho\,a", r"\,\Delta v", size=48).move_to([-2.6, -1.35, 0])
        jk[2].set_color(DANGER)
        vz = TeX(r"V", r"=", r"Z_0", r"\,I", size=48).move_to([2.6, -1.35, 0])
        vz[2].set_color(APL)
        eqv = T("↔", size=44, color=MUTED).move_to([0, -1.35, 0])
        jl = T("water hammer (Joukowsky)", size=18, color=DANGER).next_to(jk, DOWN, buff=0.2)
        vl = T("transmission line", size=18, color=APL).next_to(vz, DOWN, buff=0.2)
        with self.voice(
            "{water}If you've ever heard water hammer in a pipe, you've met the same idea. {slam}Slam a valve shut, and the "
            "pressure jumps by rho times a times delta v — Joukowsky's equation — and that pressure wave runs back up the "
            "pipe at the speed of sound. {same}It's exactly V equals Z-naught times I."
        ) as v:
            self.play(Create(pipe), FadeIn(tank), run_time=0.8)
            self.add(wm, vm)
            v.wait_until("slam")
            self.play(valve_open.animate.set_value(0.0), run_time=0.25)
            self.play(front.animate.set_value(px0), run_time=2.4, rate_func=linear)
            self.play(Write(jk), FadeIn(jl), run_time=1.0)
            v.wait_until("same")
            self.play(FadeIn(eqv), Write(vz), FadeIn(vl), run_time=1.0)
        self.remove(wm, vm)
        self.clear(run_time=0.6)

        # ------------------------------------------------------------ reflections
        gam = TeX(r"\Gamma", r"=", r"\frac{Z_L - Z_0}{Z_L + Z_0}", size=50).move_to([0, 2.75, 0])
        gam[0].set_color(PINK)
        L_end, l_start = 4.2, -3.5
        rows = [(1.25, 1.0, "open end", r"\Gamma = +1", "free end of a string"),
                (-0.45, -1.0, "short circuit", r"\Gamma = -1", "string tied to a wall"),
                (-2.15, 0.0, "matched load", r"Z_L = Z_0:\ \Gamma = 0", "a tuned dashpot")]
        lanes = VGroup()
        curves, trackers = [], []
        for y, g, name, gtex, mech in rows:
            ln = Line([l_start, y, 0], [L_end, y, 0], stroke_color=DIM, stroke_width=2.5)
            if g == 1.0:
                term = Circle(0.08, stroke_color=TEXT, stroke_width=2.5).move_to([L_end + 0.08, y, 0])
            elif g == -1.0:
                term = VGroup(Line([L_end, y, 0], [L_end, y - 0.2, 0], stroke_color=TEXT, stroke_width=2.5),
                              ground(TEXT, 2.5, 0.3).move_to([L_end, y - 0.36, 0]))
            else:
                rr = resistor(0.6, color=GOOD).rotate(PI / 2).move_to([L_end, y - 0.42, 0])
                term = VGroup(Line([L_end, y, 0], rr.get_top(), stroke_color=GOOD, stroke_width=2.5), rr,
                              ground(GOOD, 2.5, 0.26).next_to(rr, DOWN, buff=0))
            nm = T(name, size=22, color=TEXT, weight=BOLD).next_to([l_start, y, 0], LEFT, buff=0.3).shift(UP * 0.17)
            gl = TeX(gtex, size=28, color=PINK).next_to(nm, DOWN, buff=0.08).align_to(nm, RIGHT)
            ml = T(mech, size=15, color=MUTED).next_to(term, RIGHT, buff=0.25).shift(UP * 0.1)
            lanes.add(VGroup(ln, term, nm, gl, ml))
            tr = ValueTracker(0.0)
            trackers.append(tr)

            def mk(y=y, g=g, tr=tr):
                def f():
                    xs = np.linspace(l_start, L_end, 400)
                    pos = l_start + 0.4 + tr.get_value() * 4.2
                    vals = bump(xs - pos, 0.38) + g * bump((2 * L_end - xs) - pos, 0.38)
                    return VMobject().set_points_as_corners(np.stack([xs, y + 0.62 * vals, 0 * xs], 1)).set_stroke(APL, 3.5)
                return always_redraw(f)
            curves.append(mk())

        with self.voice(
            "{end}What happens when the wave reaches the end of the line? The mismatch decides. {gamma}The reflection "
            "coefficient is gamma equals Z L minus Z-naught, over Z L plus Z-naught. {open}At an open end, no current can "
            "flow, so the wave reflects with the same sign — like a string with a free end. {short}At a short circuit, the "
            "voltage must be zero, so the wave comes back inverted — like a string tied to a wall. {match}Terminate the line "
            "with a resistor exactly equal to Z-naught, and nothing comes back at all. The resistor swallows the wave as if "
            "the cable went on forever. Mechanically, it's a dashpot tuned to the chain's impedance."
        ) as v:
            self.play(FadeIn(lanes[0][:2]), FadeIn(lanes[1][:2]), FadeIn(lanes[2][:2]), run_time=0.8)
            v.wait_until("gamma")
            self.play(Write(gam), run_time=1.5)
            for i, tag in enumerate(("open", "short", "match")):
                v.wait_until(tag)
                self.add(curves[i])
                self.play(FadeIn(lanes[i][2:]), run_time=0.5)
                self.play(trackers[i].animate.set_value(3.9), run_time=4.2, rate_func=linear)
        for c in curves:
            self.remove(c)
        self.clear(run_time=0.6)

        # CAN vs APL termination, and the small echoes that remain
        bus_y = 1.6
        bus = VGroup(Line([-6.2, bus_y + 0.06, 0], [-0.8, bus_y + 0.06, 0]), Line([-6.2, bus_y - 0.06, 0], [-0.8, bus_y - 0.06, 0])).set_stroke(CAN, 3)
        nodes = VGroup(*[device("", "cpu", CAN, width=0.62, height=0.5).move_to([x, bus_y + 0.75, 0]) for x in (-5.3, -4.0, -2.7, -1.6)])
        drops = VGroup(*[Line([nd.get_x(), nd.get_bottom()[1], 0], [nd.get_x(), bus_y + 0.06, 0], stroke_color=CAN, stroke_width=2.5) for nd in nodes])
        t1 = resistor(0.55, color=CAN).rotate(PI / 2).move_to([-6.2, bus_y - 0.55, 0])
        t2 = resistor(0.55, color=CAN).rotate(PI / 2).move_to([-0.8, bus_y - 0.55, 0])
        tl1 = T("120 Ω", size=16, color=CAN).next_to(t1, LEFT, buff=0.1)
        tl2 = T("120 Ω", size=16, color=CAN).next_to(t2, RIGHT, buff=0.1)
        conn = VGroup(Line([-6.2, bus_y - 0.06, 0], t1.get_top()), Line([-0.8, bus_y - 0.06, 0], t2.get_top())).set_stroke(CAN, 2.5)
        can_lbl = T("CAN: terminators at both ends of the bus", size=19, color=CAN, weight=BOLD).move_to([-3.5, bus_y - 1.35, 0])
        phy_a = device("PHY", None, APL, width=1.3, height=0.95, label_size=18, sub="100 Ω inside").move_to([1.2, bus_y + 0.1, 0])
        phy_b = device("PHY", None, APL, width=1.3, height=0.95, label_size=18, sub="100 Ω inside").move_to([6.0, bus_y + 0.1, 0])
        link = twisted_pair([phy_a.get_right(), phy_b.get_left()], APL, amp=0.05, pitch=0.3)
        apl_lbl = T("APL: each transceiver terminates its own end", size=19, color=APL, weight=BOLD).move_to([3.6, bus_y - 1.35, 0])

        sx0, sx1, sy = -5.6, 5.6, -1.7
        sline = Line([sx0, sy, 0], [sx1, sy, 0], stroke_color=DIM, stroke_width=2.5)
        conns = [(-1.9, 0.12), (2.1, -0.09)]
        cmarks = VGroup(*[Square(0.2, fill_color=PANEL, fill_opacity=1, stroke_color=PINK, stroke_width=2).move_to([x, sy, 0]) for x, _ in conns])
        clab = VGroup(*[T(t, size=15, color=PINK).next_to(m, DOWN, buff=0.12) for t, m in zip(("connector", "splice"), cmarks)])
        st = ValueTracker(0.0)

        def small():
            xs = np.linspace(sx0, sx1, 500)
            s = st.get_value()
            pos = sx0 + 0.3 + s * 5.5
            vals = bump(xs - pos, 0.3) * np.where(xs <= sx1, 1, 0)
            for xc, g in conns:
                vals = vals + 3.0 * g * bump((2 * xc - xs) - pos, 0.3) * (xs < xc)
                vals = vals * 1.0
            return VMobject().set_points_as_corners(np.stack([xs, sy + 0.6 * vals, 0 * xs], 1)).set_stroke(APL, 3.2)

        sm = always_redraw(small)
        note = T("(small echoes drawn ×3 for visibility)", size=14, color=DIM).next_to(sline, DOWN, buff=0.55).align_to(sline, RIGHT)
        with self.voice(
            "{can}That's what CAN's 120-ohm terminators do at both ends of its bus. {apl}In APL, every link has exactly two "
            "ends, and each transceiver terminates its own end with a hundred ohms. {small}Still, no real cable is perfect. "
            "Connectors, splices and manufacturing tolerances each reflect a small echo back towards the sender. "
            "{remember}Remember those echoes — the receiver will have to deal with them."
        ) as v:
            self.play(Create(bus), FadeIn(nodes), Create(drops), run_time=1.0)
            self.play(FadeIn(t1), FadeIn(t2), Create(conn), FadeIn(tl1), FadeIn(tl2), FadeIn(can_lbl), run_time=0.8)
            v.wait_until("apl")
            self.play(FadeIn(phy_a), FadeIn(phy_b), Create(link), FadeIn(apl_lbl), run_time=1.0)
            v.wait_until("small")
            self.play(Create(sline), FadeIn(cmarks), FadeIn(clab), FadeIn(note), run_time=0.8)
            self.add(sm)
            self.play(st.animate.set_value(2.0), run_time=v.until_end(4.0) + 1.0, rate_func=linear)
        self.remove(sm)
        self.clear(run_time=0.7)
