#!/usr/bin/env python3
"""Sauna bucket stand: a low slatted platform that lifts the water bucket off the floor or the bench.
Woodworking plan (HTML -> PDF) and a full-size runner template (SVG + DXF).

Run:  python3 bucket_stand.py      (writes plan.html, img/, svg/ and dxf/)
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
SLAT_L = 13.0         # slat length = width of the stand
SLATS = 5
SLAT_W = 2.5          # 1x3
GAP = 0.375
RUNNER_H = 3.5        # 1x4 on edge
T = 0.75
INSET = 1.25          # runners sit this far in from the slat ends
FOOT = 2.25           # length of each foot under the runner
RELIEF = 0.5          # the runner is cut away this much between the feet
CLEAT = 0.75
# -----------------------------------------------------
NAME = "sauna-bucket-stand-plan"
DEPTH = SLATS * SLAT_W + (SLATS - 1) * GAP            # front to back = runner length


def runner_profile():
    L, r = DEPTH, RELIEF
    return poly([(0, 0), (FOOT, 0), (FOOT + r, r), (L - FOOT - r, r), (L - FOOT, 0), (L, 0), (L, RUNNER_H), (0, RUNNER_H)])


def parts():
    """x = across (slat length), y = front to back, z = up."""
    out = []
    xs = [INSET, SLAT_L - INSET - T]
    for x in xs:
        out.append(Part("A runner", (T, DEPTH, RUNNER_H), shape=dp.along_x(runner_profile(), x, x + T), color=1))
    for x in (xs[0] + T, xs[1] - CLEAT):
        out.append(Part("B cleat", (CLEAT, DEPTH - 1, CLEAT), shape=Manifold.cube((CLEAT, DEPTH - 1, CLEAT)).translate((x, 0.5, RUNNER_H - CLEAT)), color=2))
    for i in range(SLATS):
        y = i * (SLAT_W + GAP)
        out.append(Part("C slat", (SLAT_L, SLAT_W, T), shape=Manifold.cube((SLAT_L, SLAT_W, T)).translate((0, y, RUNNER_H)), color=3))
    return out


def bucket():
    """A stand-in wooden bucket, 10 in across at the bottom, for the picture."""
    body = Manifold.cylinder(8.0, 5.0, 5.6, 64).translate((SLAT_L / 2, DEPTH / 2, RUNNER_H + T))
    out = [(body, (196, 150, 98))]
    for z in (1.2, 6.6):
        r = 5.0 + 0.6 * z / 8.0 + 0.08
        out.append((Manifold.cylinder(0.5, r, r, 64).translate((SLAT_L / 2, DEPTH / 2, RUNNER_H + T + z)), (90, 90, 92)))
    return out


def template():
    prof = runner_profile().scale((MM, MM))
    lab = text("BUCKET STAND RUNNER  -  cut 2", 4.0).translate((DEPTH * MM / 2, RUNNER_H * MM - 14))
    m = 5.0
    return DEPTH * MM + 2 * m, RUNNER_H * MM + 2 * m, {"CUT": prof.translate((m, m)), "SCORE": None, "ENGRAVE": lab.translate((m, m))}


def build_html():
    P = parts()
    front = View(P, "front", "Front view")
    front.dim_h(0, SLAT_L, RUNNER_H + T + 1.0)
    front.dim_h(INSET, SLAT_L - INSET, -0.9)
    front.dim_v(0, RUNNER_H + T, -0.9)
    side = View(P, "side", "Side view")
    side.dim_h(0, DEPTH, RUNNER_H + T + 1.0)
    side.dim_h(0, FOOT, -0.9, f"foot {inch(FOOT)} in")
    side.dim_v(0, RELIEF, DEPTH + 0.8, f"{inch(RELIEF)} in")
    top = View(P, "top", "Top view")
    top.dim_h(0, SLAT_L, DEPTH + 0.9)
    top.dim_v(0, SLAT_W, -0.8, f"{inch(SLAT_W)} in")
    top.note(SLAT_L * 0.5, SLAT_W + GAP / 2, SLAT_L * 0.62, -1.6, f"{inch(GAP)} in ({round(GAP * MM)} mm) gaps")
    dp.iso_png(P, os.path.join(HERE, "img", "bucket-stand-iso.png"), az=30, el=26, size=(1100, 1000),
               extra=bucket() + [(Manifold.cube((SLAT_L + 16, DEPTH + 14, 0.5)).translate((-8, -7, -0.51)), (222, 214, 200))])
    dp.iso_png(P, os.path.join(HERE, "img", "bucket-stand-empty.png"), az=30, el=26, size=(1100, 1000))
    cut = dp.cut_table([
        ("A", 2, "Runner", "1x4 (3/4 &times; 3-1/2 in, 19 &times; 89 mm)", DEPTH, f"stands on edge; {inch(RELIEF)} in relief between the feet"),
        ("B", 2, "Cleat", "3/4 &times; 3/4 in (19 &times; 19 mm) strip", DEPTH - 1, "inside each runner, flush with its top"),
        ("C", SLATS, "Slat", "1x3 (3/4 &times; 2-1/2 in, 19 &times; 64 mm)", SLAT_L, "all edges rounded"),
    ])
    hw = dp.ul([
        f"{2 * SLATS} stainless wood screws, #8 &times; 1-1/4 in (4 &times; 32 mm): up through the cleats into the slats",
        "6 stainless wood screws, #8 &times; 1-1/4 in: through the cleats into the runners, from the inside",
        "No glue, no metal on top",
    ])
    p1 = f"""<div class="grid"><div class="col">
<div class="views" style="grid-template-columns:3.45in 3.5in">
<div class="box">{front.svg(318, 235)}</div><div class="box">{side.svg(322, 235)}</div></div>
<div class="views" style="grid-template-columns:3.45in 3.5in">
<div class="box">{top.svg(318, 330)}</div><div class="box pic"><img src="img/bucket-stand-iso.png" alt="Bucket on the stand"></div></div>
</div><div class="col">
<div class="box"><h2>Cut list</h2>{cut}</div>
<div class="box"><h2>Hardware</h2>{hw}</div>
<div class="box"><h2>Wood</h2><p style="margin:0">{dp.WOODS}</p></div>
</div></div>"""
    steps = dp.li([
        f"Cut two runners {both(DEPTH)} long from a 1x4. Cut the relief between the feet: {both(RELIEF)} deep, leaving a {both(FOOT)} foot at each end, "
        "with 45&deg; ends (trace the full-size template). The stand then rests on four feet and stays steady on a wet, uneven floor.",
        f"Cut two cleats {both(DEPTH - 1)} long and fix each inside a runner, flush with its top edge, with three screws from the cleat side.",
        f"Cut {SLATS} slats {both(SLAT_L)} long. Round every edge and sand.",
        f"Set the runners {both(SLAT_L - 2 * INSET)} apart outside to outside. Lay the slats across, {inch(GAP)} in ({round(GAP * MM)} mm) apart, "
        f"flush with the runner ends, {both(INSET)} of overhang at each side.",
        "Turn it over and fix each slat with two screws up through each cleat. The screw tips stop about 1/4 in below the top.",
        "Check every edge by hand. Leave it unfinished; let it dry out after each sauna.",
    ])
    p2 = f"""<div class="grid"><div class="col">
<div class="box"><h2>Assembly</h2>{steps}</div>
<div class="box"><h2>Full-size runner template</h2>{dp.ul(['<b>svg/ and dxf/</b>: the runner outline at 1:1 (' + f'{round(DEPTH * MM)} &times; {round(RUNNER_H * MM)}' + ' mm) with its relief cut, for a laser, a CNC, or to print at 100% and trace. Red = cut, black = engraved label. Cut 2.'])}</div>
<div class="box pic"><img src="img/bucket-stand-runner-template.png" alt="Runner template"></div>
</div><div class="col">
<div class="box"><h2>Use</h2><p style="margin:0">Most sauna buckets are 8 to 12 in across; the top is {both(SLAT_L)} by {both(DEPTH)}. The gaps let spilled water run through and the wood dry. Put the stand where nobody steps backward onto it, and not against the heater or its guard.</p></div>
<div class="box warn"><h2>Safety</h2>{dp.ul(dp.SAFETY + ["It is a stand for a bucket, not a step. Do not stand on it."])}</div>
</div></div>"""
    pages = [dp.page("Sauna bucket stand", f"{both(SLAT_L)} &times; {both(DEPTH)} &middot; {both(RUNNER_H + T)} high &middot; slatted, drains and dries", p1, 1, 2, "P029"),
             dp.page("Bucket stand: assembly", "Two runners, two cleats, five slats", p2, 2, 2, "P029")]
    with open(os.path.join(HERE, "plan.html"), "w") as f:
        f.write(dp.document("Sauna bucket stand - DIVELUX plan", pages))
    with open(os.path.join(HERE, "plan.name"), "w") as f:
        f.write(NAME)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    sw, sh, layers = template()
    export(HERE, "bucket-stand-runner-template", sw, sh, layers, title="Sauna bucket stand runner, full size")
    preview(os.path.join(HERE, "img", "bucket-stand-runner-template.png"), sw, sh, layers, scale=2000 / sw)
    build_html()
    P = parts()
    over = sum((a.solid ^ b.solid).volume() for i, a in enumerate(P) for b in P[i + 1:])
    print(f"top {SLAT_L} x {DEPTH} in, height {RUNNER_H + T} in, overlap between parts {over:.4f} in3")
