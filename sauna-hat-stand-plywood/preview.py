"""Preview renders for the plywood stand (not needed for cutting). Uses the small renderer from ../../3d."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "3d"))
import stand_laser as sl
from dvx_cad import to_trimesh
from render import render, sheet
from PIL import Image

PLY = (226, 196, 148); PLY2 = (206, 174, 128); BASE = (190, 156, 112)
T = 3.0
d = os.path.join(HERE, "img"); os.makedirs(d, exist_ok=True)
a = sl.rib("A", T).extrude(T).translate((0, 0, -T / 2)).rotate((90, 0, 0)).translate((0, 0, T))
b = sl.rib("B", T).extrude(T).translate((0, 0, -T / 2)).rotate((90, 0, 90)).translate((0, 0, T))
c = sl.base(T).extrude(T)
print("assembled overlap A&B %.2f mm3, A&base %.2f, B&base %.2f (kerf not removed, so tight joints show as a small overlap)"
      % ((a ^ b).volume(), (a ^ c).volume(), (b ^ c).volume()))
at, bt, ct = to_trimesh(a), to_trimesh(b), to_trimesh(c)
render([(at, PLY), (bt, PLY2), (ct, BASE)], az=30, el=22).save(os.path.join(d, "stand-assembled.png"))
a2 = at.copy(); a2.apply_translation((0, 0, 95)); b2 = bt.copy(); b2.apply_translation((0, 0, 35))
render([(a2, PLY), (b2, PLY2), (ct, BASE)], az=30, el=20).save(os.path.join(d, "stand-exploded.png"))
flat = Image.open(os.path.join(d, "hat-stand-3mm-all-parts.png"))
tiles = [(Image.open(os.path.join(d, "stand-assembled.png")), "Assembled: 186 x 186 x 201 mm"),
         (Image.open(os.path.join(d, "stand-exploded.png")), "Three flat parts from 3 or 4 mm plywood")]
sheet(tiles, 2, os.path.join(d, "stand-preview.png"), "Plywood sauna hat drying stand")
# add the cutting layout under the two renders
top = Image.open(os.path.join(d, "stand-preview.png"))
flat = flat.resize((top.width - 48, int(flat.height * (top.width - 48) / flat.width)), Image.LANCZOS)
out = Image.new("RGB", (top.width, top.height + flat.height + 70), (246, 243, 238))
out.paste(top, (0, 0)); out.paste(flat, (24, top.height))
from PIL import ImageDraw, ImageFont
ImageDraw.Draw(out).text((30, top.height + flat.height + 14), "Cutting layout: 534 x 201 mm, or cut the three parts one by one",
                         fill=(61, 51, 44), font=ImageFont.truetype(os.path.join(HERE, "..", "..", "_fonts", "BricolageGrotesque-Bold.ttf"), 24))
out.save(os.path.join(d, "stand-preview.png"), optimize=True)
