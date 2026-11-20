#!/usr/bin/env python3
"""Sauna hat drying stand for a laser cutter - the flat-pack stand from the DIVELUX 3D-print set, drawn for
3 to 4 mm plywood: two arch ribs that cross slot-in-slot, plus a base ring the four feet plug into.

The outline is the same as the printed stand (170 mm wide, 198 mm tall ribs); only the slots follow the
thickness of your sheet.
Run:  python3 stand_laser.py          (writes svg/, dxf/ and img/ for 3.0 and 4.0 mm sheet)
      python3 stand_laser.py 3.4      (your measured sheet thickness, mm)
License: CC BY 4.0 - DIVELUX, https://diveluxsaunahat.com
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from manifold3d import CrossSection, JoinType  # noqa: E402
from dvx_laser import circle, export, poly, preview, rect, rounded, text  # noqa: E402

# ---------------- parameters (mm) ----------------
THICK = 3.0               # measured thickness of your sheet (plywood sold as 3 mm is often 2.7 to 3.2)
KERF = 0.15               # width of material the laser burns away; slots are drawn narrower by this much
FIT = 0.0                 # extra slot width: raise it if the joints are too tight, lower it if loose
HAT_CIRCUMFERENCE = 610   # about 24 in; inner diameter is about 194 mm
WIDTH = 170               # rib width - kept smaller than the hat so the felt hangs loose
HEIGHT = 198              # rib height above the base
LEG_HEIGHT = 50           # straight part of the legs before the dome starts
DOME_POWER = 2.0          # 2 = ellipse, higher = boxier shoulders
BAND = 16                 # width of the arch band
CROWN = 50                # solid depth at the top where the two ribs cross
TAB_W = 12                # foot tab width
BASE_BAND = 34            # base ring width
LABELS = True             # engrave a small A and B on the ribs
GAP = 4.0                 # space between parts on the sheet
MARGIN = 5.0              # free space around the parts on the drawing
# -------------------------------------------------

assert WIDTH <= 0.92 * HAT_CIRCUMFERENCE / math.pi, "rib is too wide for the hat"
LEG_X = WIDTH / 2 - BAND / 2          # center of each leg


def outline(y_bottom=0.0):
    pts = [(WIDTH / 2, y_bottom)]
    n = 120
    for i in range(n + 1):
        t = math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        x = WIDTH / 2 * math.copysign(abs(c) ** (2 / DOME_POWER), c)
        y = LEG_HEIGHT + (HEIGHT - LEG_HEIGHT) * abs(s) ** (2 / DOME_POWER)
        pts.append((x, y))
    pts.append((-WIDTH / 2, y_bottom))
    return poly(pts)


def rib(kind, thick=THICK):
    """kind 'A' has its crown slot open downward, 'B' open upward. The feet end in tabs as long as the sheet is thick."""
    slot = thick - KERF + FIT
    outer = outline()
    inner = outline(-60).offset(-BAND, JoinType.Round) ^ rect(-WIDTH, -40, WIDTH, HEIGHT - CROWN)
    shape = outer - rounded(inner, 10)
    ch = min(0.8, thick / 4)                      # small lead-in on the tabs
    for sx in (-1, 1):
        cx = sx * LEG_X
        shape += poly([(cx - TAB_W / 2, 0.01), (cx - TAB_W / 2, -thick + ch), (cx - TAB_W / 2 + ch, -thick),
                       (cx + TAB_W / 2 - ch, -thick), (cx + TAB_W / 2, -thick + ch), (cx + TAB_W / 2, 0.01)])
    mid = HEIGHT - CROWN / 2
    if kind == "A":
        shape -= rect(-slot / 2, HEIGHT - CROWN - 5, slot / 2, mid + 0.15)
    else:
        shape -= rect(-slot / 2, mid - 0.15, slot / 2, HEIGHT + 5)
    return shape.simplify(0.005)


def base(thick=THICK):
    slot = thick - KERF + FIT
    r_out = WIDTH / 2 + 8
    ring = circle(r_out) - circle(r_out - BASE_BAND)
    for a in range(4):
        ring -= rect(LEG_X - (TAB_W - KERF + FIT + 0.1) / 2, -slot / 2, LEG_X + (TAB_W - KERF + FIT + 0.1) / 2, slot / 2).rotate(90 * a)
    return ring.simplify(0.005)


def label(letter):
    return text(letter, 7.0).translate((-24, HEIGHT - CROWN + 8))       # clear of the crown slot


def layout(parts, thick):
    """parts: list of (cut shape, engrave shape or None). Places them in a row; returns sheet size and layers."""
    cut, eng, x = CrossSection(), CrossSection(), MARGIN
    height = 0.0
    for shape, mark in parts:
        b = shape.bounds()
        shift = (x - b[0], MARGIN - b[1])
        cut += shape.translate(shift)
        if mark is not None:
            eng += mark.translate(shift)
        x += b[2] - b[0] + GAP
        height = max(height, b[3] - b[1])
    return x - GAP + MARGIN, height + 2 * MARGIN, {"CUT": cut, "SCORE": None, "ENGRAVE": eng}


def build(thick):
    tag = f"{thick:g}mm"
    a = (rib("A", thick), label("A") if LABELS else None)
    b = (rib("B", thick), label("B") if LABELS else None)
    c = (base(thick), None)
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    for name, parts in ((f"hat-stand-{tag}-all-parts", [a, b, c]), (f"hat-stand-{tag}-rib-A", [a]),
                        (f"hat-stand-{tag}-rib-B", [b]), (f"hat-stand-{tag}-base-ring", [c])):
        w, h, layers = layout(parts, thick)
        export(HERE, name, round(w, 1), round(h, 1), layers, title=f"Sauna hat drying stand, {tag} sheet")
        if name.endswith("all-parts"):
            preview(os.path.join(HERE, "img", name + ".png"), w, h, layers, scale=1500 / w)


if __name__ == "__main__":
    for t in ([float(v) for v in sys.argv[1:]] or [3.0, 4.0]):
        build(t)
