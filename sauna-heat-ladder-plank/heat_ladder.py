#!/usr/bin/env python3
"""Heat ladder wall plank for a laser cutter: a tall plank with a °F / °C scale and four reference marks.

It is a picture of temperatures, not a thermometer. Run:  python3 heat_ladder.py   (writes svg/, dxf/ and img/)
License: CC BY 4.0 - DIVELUX, https://diveluxsaunahat.com
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from manifold3d import JoinType  # noqa: E402
from dvx_laser import circle, export, poly, preview, rect, rounded, text  # noqa: E402

# ---------------- parameters ----------------
TITLE = "HEAT LADDER"
MARKS = [                 # °F, label under the mark
    (212, "WATER BOILS (SEA LEVEL)"),
    (190, "HOT SAUNA"),
    (160, "MILD SAUNA"),
    (105, "HOT BATH"),
]
FOOTNOTE = "illustrative, not a measurement"
T_LOW, T_HIGH = 95, 220   # °F range of the scale
SIZES = {"S": (80.0, 320.0), "L": (110.0, 450.0)}   # plank width x height, mm
CORNER = 0.08             # corner radius, share of the width
BORDER_INSET = 0.05       # scored border, share of the width
HOLE_D = 5.0              # one hanging hole at the top, mm (0 = none)
MARGIN = 5.0
# --------------------------------------------


def f_to_c(f):
    return (f - 32) * 5 / 9


def bell_hat(width, height, flare=0.07, n=48):
    r0 = width / 2 / (1 + flare)
    half = []
    for i in range(n + 1):
        t = i / n
        r = r0 * (1 - (1 - t) ** 2.4) ** 0.5 + r0 * flare * t ** 8
        half.append((r, height * (1 - t)))
    return poly(half + [(-x, y) for x, y in half[-1:0:-1]])


def right(cs, x):
    b = cs.bounds()
    return cs.translate((x - b[2], 0))


def left(cs, x):
    b = cs.bounds()
    return cs.translate((x - b[0], 0))


def plank(w, h):
    k = w / 110.0                                       # everything scales with the width
    plate = rounded(rect(-w / 2, 0, w / 2, h), CORNER * w)
    cut = plate
    if HOLE_D > 0:
        cut -= circle(HOLE_D / 2, 0, h - 0.09 * w)
    score = plate.offset(-BORDER_INSET * w, JoinType.Round).simplify(0.005)
    # title and a small hat mark
    tc = 7.0 * k
    ty = h - 0.09 * w - HOLE_D - 6 * k - tc
    eng = text(TITLE, tc, tracking=0.12 * tc, max_width=w * 0.8).translate((0, ty))
    eng += bell_hat(6 * k, 6.5 * k).translate((0, ty - 11 * k))
    # scale: centre bar, °F ticks on the left, °C ticks on the right
    y0, y1 = 0.10 * w + 14 * k, ty - 16 * k
    def y_of(f):
        return y0 + (f - T_LOW) / (T_HIGH - T_LOW) * (y1 - y0)
    bar = 1.0 * k
    scale = rect(-bar / 2, y0 - 2 * k, bar / 2, y1 + 2 * k)
    for f in range(T_LOW + (10 - T_LOW % 10) % 10, T_HIGH + 1, 10):
        L = 6 * k if f % 50 else 9 * k
        scale += rect(-bar / 2 - L, y_of(f) - 0.25 * k, -bar / 2, y_of(f) + 0.25 * k)
    c_lo, c_hi = int(f_to_c(T_LOW)) + 1, int(f_to_c(T_HIGH))
    for c in range(c_lo, c_hi + 1):
        if c % 5:
            continue
        L = 6 * k if c % 10 else 9 * k
        f = c * 9 / 5 + 32
        scale += rect(bar / 2, y_of(f) - 0.25 * k, bar / 2 + L, y_of(f) + 0.25 * k)
    # the four marks: long tick, °F on the left, °C on the right, label below
    nc = 5.2 * k
    lc = 2.8 * k
    for f, label in MARKS:
        y = y_of(f)
        eng += rounded(rect(-28 * k, y - 0.7 * k, 28 * k, y + 0.7 * k), 0.69 * k)       # long tick
        nums = (right(text(f"{f}\u00b0F", nc), -3 * k) + left(text(f"{round(f_to_c(f))}\u00b0C", nc), 3 * k)).translate((0, y + 2.2 * k))
        lab = text(label, lc, tracking=0.08 * lc, max_width=w * 0.8).translate((0, y - 2.6 * k - lc))
        for part in (nums, lab):                        # the scale breaks around the numbers and the label
            bb = part.bounds()
            scale -= rect(bb[0] - 1.5 * k, bb[1] - 1.2 * k, bb[2] + 1.5 * k, bb[3] + 1.2 * k)
        eng += nums + lab
    eng += scale
    fc = 2.6 * k
    eng += text(FOOTNOTE, fc, max_width=w * 0.78).translate((0, 0.10 * w + 2 * k))
    shift = (w / 2 + MARGIN, MARGIN)
    return w + 2 * MARGIN, h + 2 * MARGIN, {"CUT": cut.translate(shift), "SCORE": score.translate(shift), "ENGRAVE": eng.translate(shift)}


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    for tag, (w, h) in SIZES.items():
        sw, sh, layers = plank(w, h)
        name = f"heat-ladder-plank-{tag}-{w:g}x{h:g}mm"
        export(HERE, name, sw, sh, layers, title=f"Heat ladder plank {w:g} x {h:g} mm")
        preview(os.path.join(HERE, "img", name + ".png"), sw, sh, layers, scale=2400 / sh)
    # both sizes side by side, to scale
    from PIL import Image, ImageDraw, ImageFont
    a = Image.open(os.path.join(HERE, "img", "heat-ladder-plank-S-80x320mm.png"))
    b = Image.open(os.path.join(HERE, "img", "heat-ladder-plank-L-110x450mm.png"))
    h = 1300
    a = a.resize((int(a.width * h * 330 / 460 / a.height), int(h * 330 / 460)), Image.LANCZOS)
    b = b.resize((int(b.width * h / b.height), h), Image.LANCZOS)
    im = Image.new("RGB", (a.width + b.width + 90, h + 90), (246, 243, 238))
    im.paste(b, (30, 30))
    im.paste(a, (60 + b.width, 30 + h - a.height))
    font = ImageFont.truetype(os.path.join(HERE, "..", "..", "_fonts", "BricolageGrotesque-Bold.ttf"), 24)
    dr = ImageDraw.Draw(im)
    dr.text((40, h + 40), "L: 110 x 450 mm", fill=(61, 51, 44), font=font)
    dr.text((70 + b.width, h + 40), "S: 80 x 320 mm", fill=(61, 51, 44), font=font)
    im.save(os.path.join(HERE, "img", "heat-ladder-plank-sizes.png"), optimize=True)
