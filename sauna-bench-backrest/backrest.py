#!/usr/bin/env python3
"""Sauna bench backrest: a freestanding, slatted back support that stands on the bench with its back to the wall.
Woodworking plan (HTML -> PDF).

Run:  python3 backrest.py           (writes plan.html and img/)
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
from dvx_laser import poly  # noqa: E402

# ---------------- parameters (inches) ----------------
WIDTH = 20.0          # slat length = overall width
BASE_L = 10.0         # base rails, front to back (the back end goes against the wall)
STILE_L = 26.0        # stile length along its slope
LEAN = 12.0           # stiles lean back this much from vertical, degrees
FOOT_Y = 1.0          # front of the stile foot, from the front of the base
T = 0.75              # board thickness
W3 = 2.5              # 1x3 width
W2 = 1.5              # 1x2 width
SLATS = 7
GAP = 0.5
SLAT_START = 4.75     # first slat, measured along the stile from its foot
BRACE_AT = 13.0       # the brace meets the stile this far up it
# -----------------------------------------------------
NAME = "sauna-bench-backrest-plan"
A = math.radians(LEAN)
U = (math.sin(A), math.cos(A))                         # up the stile (y back, z up)
N = (math.cos(A), -math.sin(A))                        # across the stile, toward its back face


def stile_profile():
    p0 = (FOOT_Y, 0.0)
    p1 = (FOOT_Y + W3 / math.cos(A), 0.0)
    p3 = (p0[0] + STILE_L * U[0], p0[1] + STILE_L * U[1])
    p2 = (p3[0] + W3 * N[0], p3[1] + W3 * N[1])
    return poly([p0, p1, p2, p3])


def on_front(d):
    """Point on the front face of the stile, d inches up from the foot."""
    return FOOT_Y + d * U[0], d * U[1]


def brace_line():
    a = (BASE_L - 1.25, W3)                            # rear, on top of the base rail (over the spacer)
    f = on_front(BRACE_AT)
    b = (f[0] + W3 * N[0] * 0.5, f[1] + W3 * N[1] * 0.5)   # middle of the stile
    return a, b


def brace_profile():
    (ay, az), (by, bz) = brace_line()
    L = math.hypot(by - ay, bz - az)
    dy, dz = (by - ay) / L, (bz - az) / L
    ny, nz = -dz, dy
    h = W2 / 2
    pts = [(ay - ny * h - dy * 1.2, az - nz * h - dz * 1.2), (by - ny * h + dy * 2, bz - nz * h + dz * 2),
           (by + ny * h + dy * 2, bz + nz * h + dz * 2), (ay + ny * h - dy * 1.2, az + nz * h - dz * 1.2)]
    prof = poly(pts)
    # keep it behind the front face of the stile and above the bench
    f0, f1 = on_front(0), on_front(STILE_L + 5)
    behind = poly([f0, f1, (f1[0] + 40, f1[1]), (f0[0] + 40, -0.01)])
    return (prof ^ behind) ^ poly([(-50, 0), (50, 0), (50, 60), (-50, 60)])


def parts():
    """x = across, y = front to back (wall behind, at y = BASE_L), z = up."""
    out = []
    for side in (0, 1):
        def X(x0, x1):
            return (x0, x1) if side == 0 else (WIDTH - x1, WIDTH - x0)
        out.append(Part("A base rail", (T, BASE_L, W3), shape=dp.along_x(poly([(0, 0), (BASE_L, 0), (BASE_L, W3), (0, W3)]), *X(0, T)), color=1))
        out.append(Part("B stile", (T, W3, STILE_L), shape=dp.along_x(stile_profile(), *X(T, 2 * T)), color=2))
        out.append(Part("C brace", (T, W2, 14), shape=dp.along_x(brace_profile(), *X(2 * T, 3 * T)), color=0))
        sp = poly([(BASE_L - W3, 0), (BASE_L, 0), (BASE_L, W3), (BASE_L - W3, W3)])
        out.append(Part("D spacer", (T, W3, W3), shape=dp.along_x(sp, *X(T, 2 * T)), color=0))
    deg = -LEAN
    for i in range(SLATS):
        d = SLAT_START + i * (W3 + GAP)
        f = on_front(d)
        # the slat lies on the front face of the stiles: thickness toward the front (-N), width up the stile
        sl = Manifold.cube((WIDTH, T, W3)).translate((0, -T, 0)).rotate((deg, 0, 0)).translate((0, f[0], f[1]))
        out.append(Part("E slat", (WIDTH, T, W3), shape=sl, color=3))
    return out


def brace_len():
    (ay, az), (by, bz) = brace_line()
    return math.hypot(by - ay, bz - az) + 3.2


def build_html():
    P = parts()
    side = View([p for p in P if not p.name.startswith("E")] + [p for p in P if p.name.startswith("E")], "side", "Side view (back to the wall on the right)")
    side.dim_h(0, BASE_L, -3.6)
    top_z = STILE_L * math.cos(A) + W3 * math.sin(A) * 0
    side.dim_v(0, STILE_L * math.cos(A), BASE_L + 1.0, f"{both(STILE_L * math.cos(A))} high")
    side.note(on_front(20)[0] - 0.4, on_front(20)[1], -3.0, 27.0, f"leans back {LEAN:g}°")
    side.note(BASE_L - 3.5, 6.2, BASE_L + 1.0, 30.0, "brace")
    front = View(P, "front", "Front view")
    front.dim_h(0, WIDTH, STILE_L * math.cos(A) + 1.6)
    front.dim_v(0, W3, -1.0, f"{inch(W3)} in")
    first = on_front(SLAT_START)[1]
    front.dim_v(0, first, WIDTH + 1.0, f"{both(first)}")
    dp.iso_png(P, os.path.join(HERE, "img", "backrest-iso.png"), az=36, el=24, size=(1100, 1000),
               extra=[(Manifold.cube((WIDTH + 14, 22, 0.75)).translate((-7, -10, -0.76)), (236, 222, 196)),
                      (Manifold.cube((WIDTH + 14, 0.5, 34)).translate((-7, BASE_L, -0.76)), (236, 230, 220))])
    cut = dp.cut_table([
        ("A", 2, "Base rail", "1x3 (3/4 &times; 2-1/2 in, 19 &times; 64 mm)", BASE_L, "stands on edge on the bench"),
        ("B", 2, "Stile", "1x3", STILE_L, f"foot cut at {LEAN:g}\u00b0 so it stands flat"),
        ("C", 2, "Brace", "1x2 (3/4 &times; 1-1/2 in, 19 &times; 38 mm)", brace_len(), "cut ends to fit, see side view"),
        ("D", 2, "Spacer", "1x3 offcut", W3, "between brace and base rail"),
        ("E", SLATS, "Slat", "1x3", WIDTH, "all edges rounded"),
    ])
    hw = dp.ul([
        f"{2 * SLATS} stainless wood screws, #8 &times; 1-1/4 in (4 &times; 32 mm): from the back of the stiles into the slats",
        "12 stainless wood screws, #8 &times; 1-1/4 in: the frame joints, driven from the inner faces",
        "No glue, no metal on the front",
    ])
    p1 = f"""<div class="grid"><div class="col">
<div class="views" style="grid-template-columns:3.35in 3.6in">
<div class="box">{side.svg(310, 300)}</div><div class="box">{front.svg(334, 300)}</div></div>
<div class="views" style="grid-template-columns:3.35in 3.6in">
<div class="box pic"><img src="img/backrest-iso.png" alt="Backrest on a bench"></div>
<div class="box"><h2>How it stands</h2><p style="margin:0">Each side is a triangle: a base rail on the bench, a stile leaning back {LEAN:g}&deg;, and a brace from the stile down to the back of the base rail. The back ends of the base rails go against the wall, so the wall takes your weight when you lean back; the triangle keeps the angle. The stiles do not touch the wall.</p>
<p style="margin:6px 0 0">Your bench must be at least {both(BASE_L + 10)} deep: {both(BASE_L)} for the base and room to sit in front of it.</p></div></div>
</div><div class="col">
<div class="box"><h2>Cut list</h2>{cut}</div>
<div class="box"><h2>Hardware</h2>{hw}</div>
</div></div>"""
    steps = dp.li([
        f"Cut all parts. Round over every edge you can touch, the slats on all four long edges, and sand.",
        f"Cut the foot of each stile at {LEAN:g}&deg; from square, so it stands flat on the bench while leaning back.",
        f"Lay out one side flat, outside face down: base rail, then the stile on top of it with the front of its foot {both(FOOT_Y)} from the front of the base, "
        f"leaning back {LEAN:g}&deg;. Screw the stile to the base rail with two screws from the stile side.",
        "Put the spacer on the base rail at the back end. Lay the brace from the top of the spacer to the stile; mark both ends, cut them so the brace "
        "stays behind the front face of the stile and above the bench. Screw the brace to the stile (two screws) and through the spacer into the base rail (two screws).",
        "Build the second side as a mirror image. The screw heads go on the inner faces, the outer faces stay clean.",
        f"Stand both sides up, {both(WIDTH)} apart outside to outside. Screw the top slat on first, {both(SLAT_START + (SLATS - 1) * (W3 + GAP))} up the stile, "
        f"then the bottom one, then the rest with {inch(GAP)} in ({round(GAP * MM)} mm) gaps. Drive the screws from the back of the stiles into the slats.",
        "Check the diagonal: the frame should not rack. Check every surface by hand. Leave it unfinished.",
    ])
    p2 = f"""<div class="grid"><div class="col">
<div class="box"><h2>Assembly</h2>{steps}</div>
<div class="box"><h2>Wood</h2><p style="margin:0">{dp.WOODS} The stiles and the brace carry the load: pick straight grain for them.</p></div>
</div><div class="col">
<div class="box warn"><h2>Safety</h2>{dp.ul(dp.SAFETY + ["Always set it with the base rails against the wall. Away from a wall it tips backward when you lean on it.", "Do not stand on it or use it as a step."])}</div>
</div></div>"""
    pages = [dp.page("Sauna bench backrest", f"Freestanding &middot; {both(WIDTH)} wide &middot; leans back {LEAN:g}&deg; &middot; back to the wall", p1, 1, 2, "P028"),
             dp.page("Backrest: assembly", "Two triangle frames and seven slats, screws hidden at the back", p2, 2, 2, "P028")]
    with open(os.path.join(HERE, "plan.html"), "w") as f:
        f.write(dp.document("Sauna bench backrest - DIVELUX plan", pages))
    with open(os.path.join(HERE, "plan.name"), "w") as f:
        f.write(NAME)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    build_html()
    P = parts()
    stile_top = max(p.solid.bounding_box()[4] for p in P if p.name.startswith("B"))
    over = sum((a.solid ^ b.solid).volume() for i, a in enumerate(P) for b in P[i + 1:])
    print(f"height {STILE_L * math.cos(A):.2f} in, stile top reaches y = {stile_top:.2f} in (wall at {BASE_L}), "
          f"brace {brace_len():.2f} in, overlap between parts {over:.4f} in3")
