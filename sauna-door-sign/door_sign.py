#!/usr/bin/env python3
""""SAUNA" door sign for a laser cutter - cut outline, scored border, engraved letters, in three sizes.

Run:  python3 door_sign.py            (writes svg/, dxf/ and img/ next to this file)
      python3 door_sign.py BANYA      (your own word)
License: CC BY 4.0 - DIVELUX, https://diveluxsaunahat.com
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from manifold3d import JoinType  # noqa: E402
from dvx_laser import circle, export, preview, rect, rounded, text  # noqa: E402

# ---------------- parameters ----------------
WORD = "SAUNA"
SIZES = {"S": 200.0, "M": 300.0, "L": 400.0}   # sign width in mm
ASPECT = 0.375            # height = width x ASPECT
CORNER = 0.045            # corner radius, as a share of the width
BORDER_INSET = 0.024      # distance of the scored border from the edge, as a share of the width (0 = no border)
CAP = 0.150               # height of the capital letters, as a share of the width
TRACKING = 0.030          # extra space between letters, as a share of the width
TEXT_MAX = 0.70           # the word is scaled down to fit this share of the width
HOLE_D = 5.0              # two mounting holes for screws or a cord (0 = no holes), mm
HOLE_INSET = 0.070        # hole center to the side edge, as a share of the width
MARGIN = 5.0              # free space around the part on the drawing, mm
# --------------------------------------------


def sign(width, word=WORD):
    """Returns (sheet width, sheet height, layers). The drawing's lower left corner is (0, 0)."""
    w, h = width, round(width * ASPECT, 1)
    plate = rounded(rect(-w / 2, -h / 2, w / 2, h / 2), CORNER * w)
    cut = plate
    if HOLE_D > 0:
        for sx in (-1, 1):
            cut -= circle(HOLE_D / 2, sx * (w / 2 - HOLE_INSET * w), 0)
    score = None
    if BORDER_INSET > 0:
        score = plate.offset(-BORDER_INSET * w, JoinType.Round).simplify(0.005)   # its outline is the scored line
    cap = CAP * w
    engrave = text(word, cap, tracking=TRACKING * w, max_width=TEXT_MAX * w).translate((0, -cap / 2))
    shift = (w / 2 + MARGIN, h / 2 + MARGIN)
    layers = {"CUT": cut.translate(shift), "SCORE": score.translate(shift) if score is not None else None,
              "ENGRAVE": engrave.translate(shift)}
    return w + 2 * MARGIN, h + 2 * MARGIN, layers


if __name__ == "__main__":
    word = sys.argv[1] if len(sys.argv) > 1 else WORD
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    for tag, width in SIZES.items():
        sw, sh, layers = sign(width, word)
        name = f"sauna-door-sign-{tag}-{width:g}mm" if word == WORD else f"door-sign-{word.lower()}-{tag}-{width:g}mm"
        export(HERE, name, sw, sh, layers, title=f"{word} door sign {width:g} x {sh - 2 * MARGIN:g} mm")
        preview(os.path.join(HERE, "img", name + ".png"), sw, sh, layers, scale=1200 / sw)
    if word == WORD:
        # the three sizes side by side, to scale
        from PIL import Image, ImageDraw, ImageFont
        ims = [Image.open(os.path.join(HERE, "img", f"sauna-door-sign-{t}-{w:g}mm.png")) for t, w in SIZES.items()]
        ims = [im.resize((int(w * 2.6), int(im.height * w * 2.6 / im.width)), Image.LANCZOS) for im, w in zip(ims, SIZES.values())]
        font = ImageFont.truetype(os.path.join(HERE, "..", "..", "_fonts", "BricolageGrotesque-Bold.ttf"), 26)
        W, H = max(im.width for im in ims) + 60, sum(im.height + 52 for im in ims) + 30
        sheet = Image.new("RGB", (W, H), (246, 243, 238))
        dr, y = ImageDraw.Draw(sheet), 20
        for im, (t, w) in zip(ims, SIZES.items()):
            sheet.paste(im, (30, y))
            dr.text((44, y + im.height + 2), f"{t}: {w:g} x {w * ASPECT:g} mm", fill=(61, 51, 44), font=font)
            y += im.height + 52
        sheet.save(os.path.join(HERE, "img", "sauna-door-sign-sizes.png"), optimize=True)
