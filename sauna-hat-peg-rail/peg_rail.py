#!/usr/bin/env python3
"""Peg rail for sauna hats and towels: woodworking plan (HTML -> PDF) and a drilling template (SVG + DXF).

Run:  python3 peg_rail.py           (writes plan.html, img/, svg/ and dxf/)
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
from dvx_laser import circle, export, poly, preview, rect, text  # noqa: E402

# ---------------- parameters (inches) ----------------
LENGTH = 36.0         # rail length
PEGS = 4              # number of pegs
SPACING = 9.0         # peg spacing (a felt hat is about 8 in wide)
RAIL_H = 3.5          # 1x4 board: 3/4 x 3-1/2 in actual
RAIL_T = 0.75
PEG_D = 0.75          # hardwood dowel
PEG_L = 4.0           # dowel length (it goes right through the rail)
PEG_ANGLE = 10.0      # pegs tilt up, degrees
PEG_Z = 1.5           # peg center above the bottom edge
SCREW_X = [10.0, 26.0]   # screw positions from the left end: 16 in apart, for studs 16 in on center
SCREW_Z = 2.625       # screw height above the bottom edge
# -----------------------------------------------------
NAME = "sauna-hat-peg-rail-plan"
PEG_X = [(LENGTH - (PEGS - 1) * SPACING) / 2 + i * SPACING for i in range(PEGS)]


def parts():
    """x = along the rail, y = out from the wall (front face at y = 0, wall at y = RAIL_T), z = up."""
    out = [Part("A rail", (LENGTH, RAIL_T, RAIL_H), color=3)]
    for i, x in enumerate(PEG_X):
        dowel = Manifold.cylinder(PEG_L, PEG_D / 2, PEG_D / 2, 48)          # along +z from 0
        # the dowel points out of the front face (-y), tilted up, its back end flush with the back of the rail
        place = (lambda m, x=x: m.rotate((90, 0, 0)).rotate((-PEG_ANGLE, 0, 0)).translate((x, RAIL_T, PEG_Z)))
        flush = Manifold.cube((10, 10, 10)).translate((-5, RAIL_T - 10, -5))           # sanded flush at the back
        out.append(Part(f"B peg {i + 1}", (PEG_D, PEG_L, PEG_D), place=lambda m, p=place, f=flush, x=x: p(m) ^ f.translate((x, 0, PEG_Z)),
                        shape=dowel, color=0))
    for x in SCREW_X:
        plug = Manifold.cylinder(0.08, 0.1875, 0.1875, 32).rotate((90, 0, 0)).translate((x, 0.04, SCREW_Z))
        out.append(Part("plug", (0.375, 0.08, 0.375), shape=plug, color=0))
    return out


def hats():
    """Two felt hats hanging from the pegs by their loops (picture only)."""
    sys.path.insert(0, os.path.join(HERE, "..", "..", "3d"))
    from dvx_text import bell_hat
    from dvx_cad import rect as r3
    w, h = 200 / MM, 190 / MM                          # stand-in hat, inches
    sil = bell_hat(w, h)
    shell = ((sil - sil.offset(-4.5 / MM)) ^ r3(0, 0.01, 20, 20)).revolve(96)
    out = []
    for x, col in ((PEG_X[0], (150, 150, 146)), (PEG_X[2], (176, 112, 82))):
        tip_y = -(PEG_L - RAIL_T) * 0.8
        out.append((shell.translate((x, tip_y + w / 2 * 0.2 - w / 2, PEG_Z - h - 0.6)), col))
        loop = Manifold.cylinder(0.12, 0.45, 0.45, 32) - Manifold.cylinder(0.3, 0.33, 0.33, 32).translate((0, 0, -0.1))
        out.append((loop.rotate((0, 90, 0)).translate((x - 0.06, tip_y, PEG_Z - 0.35)), (60, 58, 62)))
    return out


def template(half=False):
    """Drilling template in mm: the front face of the rail, peg holes, screw pilot holes, centerline marks."""
    L, H = LENGTH * MM, RAIL_H * MM
    if half:
        L = L / 2
    cut = rect(0, 0, L, H)
    eng = None
    for x in PEG_X + SCREW_X:
        xm = x * MM
        if xm > L + 0.01:
            continue
        is_peg = x in PEG_X
        z = (PEG_Z if is_peg else SCREW_Z) * MM
        r = PEG_D * MM / 2 if is_peg else 1.5
        cut -= circle(r, xm, z)
        cross = rect(xm - 0.15, z - r - 6, xm + 0.15, z - r - 1) + rect(xm - 0.15, z + r + 1, xm + 0.15, z + r + 6)
        eng = cross if eng is None else eng + cross
        lab = text("PEG" if is_peg else "SCREW", 3.5).translate((xm, H - 7.5 if is_peg else 4.5))
        eng += lab
    score = rect(2, PEG_Z * MM - 0.1, L - 2, PEG_Z * MM + 0.1)
    title = "LEFT HALF  -  turn it over for the right half" if half else "PEG RAIL DRILLING TEMPLATE"
    eng += text(title, 3.2, max_width=L * 0.6).translate((L / 2, 4.5 if not half else H - 13))
    eng += text("BOTTOM EDGE", 2.6).translate((32 if half else L / 2 + 120, 1.6))
    # 10 degree drilling wedge, as a separate part below the template
    wl = 150.0
    wedge = poly([(0, 0), (wl, 0), (wl, 6 + wl * math.tan(math.radians(PEG_ANGLE))), (0, 6)]).translate((0, -45))
    cut += wedge
    eng += text("10 DEG WEDGE", 3.5).translate((50, -40))
    m = 5.0
    shift = (m, 45 + m)
    return L + 2 * m, H + 45 + 2 * m, {"CUT": cut.translate(shift), "SCORE": score.translate(shift), "ENGRAVE": eng.translate(shift)}


def build_html():
    P = parts()
    front = View(P, "front", "Front view")
    front.dim_h(0, LENGTH, RAIL_H + 2.6)
    front.dim_h(0, PEG_X[0], -1.3, f"{inch(PEG_X[0])} in ({round(PEG_X[0] * MM)} mm)")
    for a, b in zip(PEG_X[:-1], PEG_X[1:]):
        front.dim_h(a, b, -1.3)
    front.dim_h(0, SCREW_X[0], RAIL_H + 1.2, f"screw at {both(SCREW_X[0])}")
    front.dim_h(SCREW_X[0], SCREW_X[1], RAIL_H + 1.2, f"{both(SCREW_X[1] - SCREW_X[0])} between screws")
    front.dim_v(0, RAIL_H, -1.2)
    front.dim_v(0, PEG_Z, LENGTH + 1.0, f"{inch(PEG_Z)} in ({round(PEG_Z * MM)} mm)")
    side = View([p for p in P if p.name.startswith(("A", "B peg 1"))], "side", "Side view")
    side.dim_v(0, RAIL_H, RAIL_T + 0.7)
    side.dim_h(0, RAIL_T, RAIL_H + 0.6, f"{inch(RAIL_T)} in ({round(RAIL_T * MM)} mm)")
    tip = PEG_L - RAIL_T
    side.note(-tip * math.cos(math.radians(PEG_ANGLE)) * 0.55, PEG_Z + 0.45, -1.4, RAIL_H + 1.7, f"peg tilts up {PEG_ANGLE:g}°")
    side.dim_h(-(PEG_L - RAIL_T) * math.cos(math.radians(PEG_ANGLE)), 0, -0.8, f"{inch(PEG_L - RAIL_T)} in out")
    dp.iso_png(P, os.path.join(HERE, "img", "peg-rail-iso.png"), az=24, el=22, size=(1300, 960),
               extra=[(Manifold.cube((LENGTH + 6, 0.4, 14)).translate((-3, RAIL_T, -10.5)), (236, 230, 220))] + hats())
    cut = dp.cut_table([
        ("A", 1, "Rail", "1x4 (3/4 &times; 3-1/2 in, 19 &times; 89 mm)", LENGTH, "front edges rounded 1/8 in"),
        ("B", PEGS, "Peg", f"hardwood dowel, {inch(PEG_D)} in (19 mm)", PEG_L, "tip chamfered"),
    ])
    hw = dp.ul([
        "2 wood screws, #10 &times; 2-1/2 in (5 &times; 65 mm), into studs; or anchors that suit your wall",
        "2 wood plugs, 3/8 in (10 mm), to hide the screw heads",
        "Wood glue for the pegs (this rail lives outside the hot room)",
    ])
    tools = dp.ul([
        "Saw, square, tape measure, sandpaper",
        "Drill, 3/4 in (19 mm) Forstner or spade bit, 3/8 in (10 mm) bit for the counterbores, 1/8 in pilot bit",
        "Drill press or the 10&deg; wedge from the template; a scrap board under the rail against tear-out",
    ])
    p1 = f"""<div class="grid"><div class="col">
<div class="box">{front.svg(660, 215)}</div>
<div class="views" style="grid-template-columns:2.3in 4.65in"><div class="box">{side.svg(212, 330)}</div>
<div class="box pic"><img src="img/peg-rail-iso.png" alt="Peg rail on the wall"></div></div>
</div><div class="col">
<div class="box"><h2>Cut list</h2>{cut}</div>
<div class="box"><h2>Hardware</h2>{hw}</div>
<div class="box"><h2>Tools</h2>{tools}</div>
</div></div>"""
    steps = dp.li([
        f"Cut the rail to {both(LENGTH)}. Round over or sand the front edges and both ends.",
        f"Mark the peg holes with the template, or measure: {both(PEG_X[0])} from each end, then every {both(SPACING)}, "
        f"{both(PEG_Z)} up from the bottom edge.",
        f"Drill the {inch(PEG_D)} in holes right through, tilted {PEG_ANGLE:g}&deg; so the pegs point up. On a drill press, "
        "lay the rail face up on the 10&deg; wedge with its top edge on the high side; by hand, use the wedge as a sighting guide. Clamp a scrap board behind to stop tear-out.",
        f"Cut {PEGS} pegs {both(PEG_L)} long and chamfer the front end. Glue them in, flush with the back face. Wipe off the glue.",
        f"Drill the screw holes at {both(SCREW_X[0])} and {both(SCREW_X[1])} from the left end ({both(SCREW_X[1] - SCREW_X[0])} apart, "
        "the usual stud spacing), counterbored 3/8 in wide and 3/8 in deep.",
        "Sand, then oil it or leave it raw. Find the studs, level the rail, screw it on and glue the plugs into the counterbores.",
    ])
    tpl = dp.ul([
        "<b>svg/ and dxf/</b>: the full-length template (914 &times; 89 mm) for a CNC or a large laser, and the left half (457 &times; 89 mm) "
        "for a hobby laser. The layout is symmetric end to end: for the right half, turn the template over (face down), "
        "keep the edge marked BOTTOM EDGE on the bottom edge of the rail and line it up with the right end.",
        "Red = cut: outline, the 19 mm peg holes, 3 mm pilot marks for the screws, and a 10&deg; wedge. Blue = score: the peg centerline. "
        "Black = engrave: labels and centering ticks.",
        "Cut it from 3 mm hardboard or plywood, lay it on the rail flush with the ends and edges, and mark through the holes with an awl.",
    ])
    p2 = f"""<div class="grid"><div class="col">
<div class="box"><h2>Assembly</h2>{steps}</div>
<div class="box"><h2>Drilling template</h2>{tpl}</div>
<div class="box pic"><img src="img/{NAME}-template.png" alt="Drilling template"></div>
</div><div class="col">
<div class="box"><h2>Wood</h2><p style="margin:0">{dp.WOODS} For this rail any straight, dry board works; it hangs in the changing room, not in the hot room.</p></div>
<div class="box"><h2>For hats</h2><p style="margin:0">Hang a felt sauna hat by its loop. A hat pulled over a thin peg can take a dent; nine inches between pegs leaves room for hats side by side.</p></div>
<div class="box warn"><h2>Safety</h2>{dp.ul(dp.SAFETY[:2] + ["Fix the rail into studs or into anchors rated for the load. Glue and plaster alone will not hold it."])}</div>
</div></div>"""
    pages = [dp.page("Peg rail for sauna hats and towels", f"{PEGS} pegs &middot; {both(LENGTH)} long &middot; for the changing room", p1, 1, 2, "P026"),
             dp.page("Peg rail: assembly and template", "Drill, glue, hang", p2, 2, 2, "P026")]
    with open(os.path.join(HERE, "plan.html"), "w") as f:
        f.write(dp.document("Peg rail for sauna hats - DIVELUX plan", pages))
    with open(os.path.join(HERE, "plan.name"), "w") as f:
        f.write(NAME)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    for half in (False, True):
        sw, sh, layers = template(half)
        name = "peg-rail-template-left-half" if half else "peg-rail-template-full"
        export(HERE, name, sw, sh, layers, title=f"Peg rail drilling template ({'left half' if half else 'full length'})")
        preview(os.path.join(HERE, "img", name + ".png"), sw, sh, layers, scale=2200 / sw)
    import shutil
    shutil.copy(os.path.join(HERE, "img", "peg-rail-template-full.png"), os.path.join(HERE, "img", f"{NAME}-template.png"))
    build_html()
    print("peg x (in):", [inch(x) for x in PEG_X], " screws:", [inch(x) for x in SCREW_X])
