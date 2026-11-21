#!/usr/bin/env python3
"""Sauna bench headrest: woodworking plan (HTML -> PDF) and a full-size side template (SVG + DXF).

Run:  python3 headrest.py           (writes plan.html, img/, svg/ and dxf/)
      then the PDF:  flock /tmp/freebies-chromium.lock env NODE_PATH=/opt/carmax/node_modules node ../render_plans.js .
License: CC BY 4.0 - DIVELUX, https://diveluxsaunahat.com
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from manifold3d import Manifold  # noqa: E402
import dvx_plans as dp  # noqa: E402
from dvx_plans import MM, Part, View, both, inch  # noqa: E402
from dvx_laser import export, poly, preview, text  # noqa: E402

# ---------------- parameters (inches) ----------------
LENGTH = 14.0         # along the bench
WIDTH = 12.0          # across the bench = slat length
LOW = 1.0             # side height at the shoulder end
HIGH = 3.5            # side height at the head end (a 1x4 is 3-1/2 in wide)
T = 0.75              # board thickness
SLAT_W = 1.5          # 1x2 slats
SLATS = 7
GAP = 0.375           # gap between slats
INSET = 1.0           # sides sit this far in from the slat ends
CLEAT = 0.75          # 3/4 x 3/4 cleat inside each side, under the slats
# -----------------------------------------------------
NAME = "sauna-bench-headrest-plan"
A = math.atan2(HIGH - LOW, LENGTH)                     # slope of the top
SLOPE_L = math.hypot(LENGTH, HIGH - LOW)
RUN = SLATS * SLAT_W + (SLATS - 1) * GAP
START = (SLOPE_L - RUN) / 2


def side_profile():
    """(y, z) outline of a side, inches: a wedge with the head-end top corner rounded."""
    r = 0.75
    pts = [(0, 0), (LENGTH, 0), (LENGTH, HIGH - r)]
    cx, cz = LENGTH - r, HIGH - r
    for i in range(1, 12):
        t = math.radians(90 * i / 12)
        pts.append((cx + r * math.cos(t), cz + r * math.sin(t)))
    pts += [(0, LOW)]
    return poly(pts)


def parts():
    """x = across the bench, y = along it (shoulder end at y = 0), z = up."""
    out = []
    xs = [INSET, WIDTH - INSET - T]
    for i, x in enumerate(xs):
        out.append(Part("A side", (T, LENGTH, HIGH), shape=dp.along_x(side_profile(), x, x + T), color=1))
    deg = math.degrees(A)
    for x in (xs[0] + T, xs[1] - CLEAT):
        cl = Manifold.cube((CLEAT, SLOPE_L - 1.0, CLEAT)).translate((0, 0.5, -CLEAT)).rotate((deg, 0, 0)).translate((x, 0, LOW))
        out.append(Part("B cleat", (CLEAT, SLOPE_L - 1, CLEAT), shape=cl, color=2))
    for i in range(SLATS):
        s = START + i * (SLAT_W + GAP)
        sl = Manifold.cube((WIDTH, SLAT_W, T)).rotate((deg, 0, 0)).translate((0, s * math.cos(A), LOW + s * math.sin(A)))
        out.append(Part("C slat", (WIDTH, SLAT_W, T), shape=sl, color=3))
    return out


def template():
    """Full-size side template in mm: cut outline, engraved label."""
    prof = side_profile().scale((MM, MM))
    m = 5.0
    lab = text("HEADREST SIDE  -  cut 2", 4.0).translate((LENGTH * MM / 2, 12))
    lab += text("shoulder end", 3.0).translate((22, 4)) + text("head end", 3.0).translate((LENGTH * MM - 20, 4))
    shift = (m, m)
    return LENGTH * MM + 2 * m, HIGH * MM + 2 * m, {"CUT": prof.translate(shift), "SCORE": None, "ENGRAVE": lab.translate(shift)}


def build_html():
    P = parts()
    side = View(P, "side", "Side view")
    side.dim_h(0, LENGTH, -0.9)
    side.dim_v(0, LOW, -0.7)
    side.dim_v(0, HIGH, LENGTH + 0.7)
    s0 = START
    side.note(LENGTH * 0.5, LOW + (HIGH - LOW) * 0.5 + 0.9, LENGTH * 0.25, HIGH + 2.2,
              f"{SLATS} slats, {inch(GAP)} in ({round(GAP * MM)} mm) gaps")
    side.note(LENGTH * 0.75, 0.4, LENGTH * 0.8, -2.0, f"top slopes {math.degrees(A):.0f}°")
    front = View(P, "front", "End view (from the shoulder end)")
    front.dim_h(0, WIDTH, HIGH + 1.5)
    front.dim_h(0, INSET, -0.8, f"{inch(INSET)} in")
    front.dim_h(INSET, WIDTH - INSET, -1.7)
    top = View(P, "top", "Top view")
    top.dim_h(0, WIDTH, LENGTH + 0.8)
    top.dim_v(0, LENGTH, -0.8)
    dp.iso_png(P, os.path.join(HERE, "img", "headrest-iso.png"), az=32, el=24, size=(1300, 860),
               extra=[(Manifold.cube((26, 30, 0.75)).translate((-7, -12, -0.76)), (236, 222, 196))])
    cut = dp.cut_table([
        ("A", 2, "Side", "1x4 (3/4 &times; 3-1/2 in, 19 &times; 89 mm)", LENGTH, f"cut to a wedge: {inch(LOW)} in high at one end, {inch(HIGH)} in at the other"),
        ("B", 2, "Cleat", "3/4 &times; 3/4 in (19 &times; 19 mm) strip", SLOPE_L - 1, "follows the slope, flush with the top of the side"),
        ("C", SLATS, "Slat", "1x2 (3/4 &times; 1-1/2 in, 19 &times; 38 mm)", WIDTH, "all edges rounded"),
    ])
    hw = dp.ul([
        f"{2 * SLATS} stainless wood screws, #8 &times; 1-1/4 in (4 &times; 32 mm): up through the cleats into the slats",
        "6 stainless wood screws, #8 &times; 1-1/4 in: through the cleats into the sides, from the inside",
        "No glue, no nails, no metal on top",
    ])
    p1 = f"""<div class="grid"><div class="col">
<div class="views" style="grid-template-columns:4.1in 2.85in">
<div class="box">{side.svg(380, 250)}</div><div class="box">{front.svg(262, 250)}</div></div>
<div class="views" style="grid-template-columns:2.85in 4.1in">
<div class="box">{top.svg(262, 300)}</div><div class="box pic"><img src="img/headrest-iso.png" alt="Headrest on a bench"></div></div>
</div><div class="col">
<div class="box"><h2>Cut list</h2>{cut}</div>
<div class="box"><h2>Hardware</h2>{hw}</div>
<div class="box"><h2>Wood</h2><p style="margin:0">{dp.WOODS}</p></div>
</div></div>"""
    steps = dp.li([
        f"Cut both sides from a 1x4: {both(LENGTH)} long, {both(LOW)} high at the shoulder end, full {both(HIGH)} at the head end. "
        "Trace the full-size template, or mark the two heights and join them with a straight line. Round the top corner at the head end.",
        "Clamp the two sides together and sand them to the same shape.",
        f"Cut two cleats {both(SLOPE_L - 1)} long. Fix each one to the inside face of a side, its top flush with the sloped top edge, "
        "with three screws driven from the cleat into the side.",
        f"Cut {SLATS} slats {both(WIDTH)} long. Round every edge, especially the top ones, and sand smooth.",
        f"Stand the sides {both(WIDTH - 2 * INSET)} apart outside to outside, {both(INSET)} in from each slat end. Lay the slats on top, "
        f"{inch(GAP)} in ({round(GAP * MM)} mm) apart (a 3/8 in spacer helps), starting {both(START)} along the slope from the shoulder end.",
        "Turn it over and fix every slat with two screws driven up through the cleats. The screws stop about 1/4 in below the top surface.",
        "Check every surface with your hand: no splinters, no screw tips, no sharp corners. Leave it unfinished.",
    ])
    p2 = f"""<div class="grid"><div class="col">
<div class="box"><h2>Assembly</h2>{steps}</div>
<div class="box"><h2>Full-size side template</h2>{dp.ul(['<b>svg/ and dxf/</b>: the side outline at 1:1 (356 &times; 89 mm), for a laser, a CNC, or to print at 100% and trace. Red = cut, black = engraved label. Cut 2.'])}</div>
<div class="box pic"><img src="img/headrest-side-template.png" alt="Side template"></div>
</div><div class="col">
<div class="box"><h2>Use</h2><p style="margin:0">Lay it on the bench with the high end under your head. The slope is gentle, about {math.degrees(A):.0f}&deg;. Lift it away to clean the bench and let it dry with the rest of the sauna wood.</p></div>
<div class="box warn"><h2>Safety</h2>{dp.ul(dp.SAFETY)}</div>
</div></div>"""
    pages = [dp.page("Sauna bench headrest", f"{both(LENGTH)} long &middot; {both(WIDTH)} wide &middot; {inch(LOW)} to {inch(HIGH)} in high sides, plus slats", p1, 1, 2, "P027"),
             dp.page("Headrest: assembly", "Hidden stainless screws, no metal on top", p2, 2, 2, "P027")]
    with open(os.path.join(HERE, "plan.html"), "w") as f:
        f.write(dp.document("Sauna bench headrest - DIVELUX plan", pages))
    with open(os.path.join(HERE, "plan.name"), "w") as f:
        f.write(NAME)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    sw, sh, layers = template()
    export(HERE, "headrest-side-template", sw, sh, layers, title="Sauna headrest side, full size")
    preview(os.path.join(HERE, "img", "headrest-side-template.png"), sw, sh, layers, scale=2000 / sw)
    build_html()
    print(f"slope {math.degrees(A):.1f} deg, slat run {inch(RUN)} in of {SLOPE_L:.2f} in, first slat at {inch(START)} in")
