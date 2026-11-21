#!/usr/bin/env python3
"""Sauna rules board for a laser cutter: cut outline, scored border, engraved title and rules, in two sizes.

Run:  python3 rules_board.py                    (writes svg/, dxf/ and img/ next to this file)
      python3 rules_board.py rules.txt          (your own text: first line = title, then up to 8 rules)
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
TITLE = "SAUNA RULES"
RULES = [
    "SHOWER BEFORE YOU GO IN",
    "SIT ON A TOWEL",
    "ASK BEFORE ADDING STEAM",
    "KEEP YOUR VOICE LOW",
    "COOL DOWN, DRINK WATER",
    "LEAVE IF YOU FEEL UNWELL",
]
SIZES = {"M": 300.0, "L": 450.0}   # board width in mm
ASPECT = 0.70             # height = width x ASPECT
CORNER = 0.035            # corner radius, share of the width
BORDER_INSET = 0.025      # scored border, share of the width
TITLE_CAP = 0.060         # title cap height, share of the width
RULE_CAP = 0.030          # rule cap height, share of the width
HOLE_D = 5.0              # two mounting holes, mm (0 = none)
MARGIN = 5.0              # free space around the part on the drawing, mm
# --------------------------------------------


def bell_hat(width, height, flare=0.07, n=48):
    """Bell sauna hat silhouette, brim on y = 0, centered on x = 0 (same shape as the 3D-print set)."""
    r0 = width / 2 / (1 + flare)
    half = []
    for i in range(n + 1):
        t = i / n
        r = r0 * (1 - (1 - t) ** 2.4) ** 0.5 + r0 * flare * t ** 8
        half.append((r, height * (1 - t)))
    return poly(half + [(-x, y) for x, y in half[-1:0:-1]])


def left(cs, x):
    """Move a centered text outline so its left edge is at x."""
    b = cs.bounds()
    return cs.translate((x - b[0], 0))


def board(width, title=TITLE, rules=RULES):
    w, h = width, round(width * ASPECT, 1)
    plate = rounded(rect(-w / 2, -h / 2, w / 2, h / 2), CORNER * w)
    cut = plate
    if HOLE_D > 0:
        for sx in (-1, 1):
            cut -= circle(HOLE_D / 2, sx * (w / 2 - 0.06 * w), h / 2 - 0.06 * w)
    score = plate.offset(-BORDER_INSET * w, JoinType.Round).simplify(0.005)
    inner = w / 2 - BORDER_INSET * w - 0.05 * w
    tc = TITLE_CAP * w
    ty = h / 2 - BORDER_INSET * w - 0.05 * w - tc
    engrave = text(title, tc, tracking=0.14 * tc, max_width=2 * inner - 0.16 * w).translate((0, ty))
    engrave += rect(-0.09 * w, ty - 0.45 * tc, 0.09 * w, ty - 0.45 * tc + 0.006 * w)
    rc = RULE_CAP * w
    top, bottom = ty - 0.9 * tc, -h / 2 + BORDER_INSET * w + 0.05 * w
    step = (top - bottom) / max(len(rules), 1)
    outlines = [text(line, rc, tracking=0.04 * rc, max_width=2 * inner - 2.2 * rc) for line in rules]
    block = 2.0 * rc + max(o.bounds()[2] - o.bounds()[0] for o in outlines)
    x0 = -block / 2                                     # the bullets and the longest line, centered as a block
    for i, (line, o) in enumerate(zip(rules, outlines)):
        y = top - (i + 0.5) * step - rc / 2
        engrave += bell_hat(rc * 1.25, rc * 1.3).translate((x0 + rc * 0.62, y - 0.05 * rc))
        engrave += left(o, x0 + 2.0 * rc).translate((0, y))
    shift = (w / 2 + MARGIN, h / 2 + MARGIN)
    return w + 2 * MARGIN, h + 2 * MARGIN, {"CUT": cut.translate(shift), "SCORE": score.translate(shift), "ENGRAVE": engrave.translate(shift)}


if __name__ == "__main__":
    title, rules, tag = TITLE, RULES, "sauna-rules-board"
    if len(sys.argv) > 1:
        lines = [l.strip() for l in open(sys.argv[1]) if l.strip()]
        title, rules, tag = lines[0], lines[1:9], "rules-board-custom"
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    for size, width in SIZES.items():
        sw, sh, layers = board(width, title, rules)
        name = f"{tag}-{size}-{width:g}mm"
        export(HERE, name, sw, sh, layers, title=f"{title} board {width:g} x {sh - 2 * MARGIN:g} mm")
        preview(os.path.join(HERE, "img", name + ".png"), sw, sh, layers, scale=1200 / sw)
    if tag == "sauna-rules-board":
        # both sizes side by side, to scale
        from PIL import Image, ImageDraw, ImageFont
        ims = [Image.open(os.path.join(HERE, "img", f"{tag}-{t}-{w:g}mm.png")) for t, w in SIZES.items()]
        k = 2.2
        ims = [im.resize((int(w * k), int(im.height * w * k / im.width)), Image.LANCZOS) for im, w in zip(ims, SIZES.values())]
        font = ImageFont.truetype(os.path.join(HERE, "..", "..", "_fonts", "BricolageGrotesque-Bold.ttf"), 26)
        W, H = sum(im.width for im in ims) + 90, max(im.height for im in ims) + 80
        sheet = Image.new("RGB", (W, H), (246, 243, 238))
        dr, x = ImageDraw.Draw(sheet), 30
        for im, (t, w) in zip(ims, SIZES.items()):
            sheet.paste(im, (x, H - 60 - im.height))
            dr.text((x + 14, H - 52), f"{t}: {w:g} x {w * ASPECT:g} mm", fill=(61, 51, 44), font=font)
            x += im.width + 30
        sheet.save(os.path.join(HERE, "img", "sauna-rules-board-sizes.png"), optimize=True)
