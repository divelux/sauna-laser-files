"""Small helpers for the DIVELUX laser-cut sauna projects: 2D shapes, text outlines, SVG and DXF writers.

Needs:  pip install manifold3d fonttools numpy        (Pillow only for the preview images)
All dimensions are millimeters. License: CC BY 4.0 - DIVELUX, https://diveluxsaunahat.com

Layers and colors (the usual laser convention):
  CUT      red   (255, 0, 0)  hairline stroke, cut through
  SCORE    blue  (0, 0, 255)  hairline stroke, light vector line
  ENGRAVE  black (0, 0, 0)    filled areas, raster engrave
"""
import math
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, JoinType, set_circular_segments

set_circular_segments(96)

LAYERS = {"CUT": ("#ff0000", 1), "SCORE": ("#0000ff", 5), "ENGRAVE": ("#000000", 7)}   # svg color, DXF color index
_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES = [
    os.environ.get("DVX_FONT", ""),
    os.path.join(_HERE, "..", "_fonts", "BricolageGrotesque-Bold.ttf"),   # the font used for the released files
    os.path.join(_HERE, "fonts", "BricolageGrotesque-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
_cache = {}


# ---------------- shapes ----------------
def poly(points):
    cs = CrossSection([[(float(x), float(y)) for x, y in points]])
    return cs if cs.area() > 0 else CrossSection([[(float(x), float(y)) for x, y in points[::-1]]])


def rect(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def circle(r, x=0.0, y=0.0):
    return CrossSection.circle(r).translate((x, y))


def rounded(cs, r):
    """Round convex corners with radius r."""
    return cs.offset(-r, JoinType.Round).offset(r, JoinType.Round).simplify(0.005)


def filleted(cs, r):
    """Fill concave corners with radius r."""
    return cs.offset(r, JoinType.Round).offset(-r, JoinType.Round).simplify(0.005)


class _FlatPen(BasePen):
    def __init__(self, glyph_set, steps=12):
        super().__init__(glyph_set)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self._flush()
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                             a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _flush(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _closePath = _endPath = _flush


def text(string, cap_height, font=None, tracking=0.0, max_width=None):
    """Outline of a line of text, centered on x = 0, baseline on y = 0. cap_height and tracking in mm."""
    path = next((f for f in ([font] if font else FONT_CANDIDATES) if f and os.path.exists(f)), None)
    if path is None:
        raise FileNotFoundError("No .ttf font found. Set DVX_FONT=/path/to/a/bold/font.ttf")
    if path not in _cache:
        tt = TTFont(path)
        _cache[path] = (tt, tt.getGlyphSet(), tt.getBestCmap())
    tt, glyphs, cmap = _cache[path]
    caps = getattr(tt["OS/2"], "sCapHeight", 0) or 0.7 * tt["head"].unitsPerEm
    k = cap_height / caps
    contours, x = [], 0.0
    for ch in string:
        name = cmap.get(ord(ch))
        if name is None:
            raise ValueError(f"the font has no glyph for {ch!r}")
        pen = _FlatPen(glyphs)
        glyphs[name].draw(pen)
        pen._flush()
        contours += [[(x + px * k, py * k) for px, py in c] for c in pen.contours]
        x += glyphs[name].width * k + tracking
    width = x - tracking
    cs = CrossSection(contours, FillRule.NonZero)
    if max_width and width > max_width:
        cs, width = cs.scale((max_width / width, max_width / width)), max_width
    return cs.translate((-width / 2, 0))


# ---------------- output ----------------
def _contours(cs):
    return [[(float(x), float(y)) for x, y in c] for c in cs.to_polygons()]


def write_svg(path, width, height, layers, title=""):
    """layers: {"CUT": CrossSection, "SCORE": ..., "ENGRAVE": ...}. The drawing spans x 0..width, y 0..height
    (y up, as in the DXF); the SVG is in millimeters, 1 user unit = 1 mm."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
           f'width="{width:g}mm" height="{height:g}mm" viewBox="0 0 {width:g} {height:g}">',
           f'<title>{title}</title>',
           '<desc>DIVELUX, https://diveluxsaunahat.com - CC BY 4.0. Layers: CUT red, SCORE blue, ENGRAVE black. Units: mm.</desc>']
    for name in ("ENGRAVE", "SCORE", "CUT"):                  # cut last, as lasers should run it
        cs = layers.get(name)
        if cs is None or cs.is_empty():
            continue
        color = LAYERS[name][0]
        d = " ".join("M " + " L ".join(f"{x:.3f} {height - y:.3f}" for x, y in c) + " Z" for c in _contours(cs))
        style = (f'fill="{color}" fill-rule="evenodd" stroke="none"' if name == "ENGRAVE"
                 else f'fill="none" stroke="{color}" stroke-width="0.1"')
        out.append(f'<g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}">')
        out.append(f'<path d="{d}" {style}/>')
        out.append('</g>')
    out.append('</svg>')
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def write_dxf(path, layers):
    """Plain ASCII DXF (R12): every contour is a closed POLYLINE on the layer CUT, SCORE or ENGRAVE. Units: mm."""
    g = []

    def add(*pairs):
        for code, value in pairs:
            g.append(f"{code}\n{value}")

    add((0, "SECTION"), (2, "HEADER"), (9, "$ACADVER"), (1, "AC1009"), (9, "$INSUNITS"), (70, 4), (0, "ENDSEC"))
    add((0, "SECTION"), (2, "TABLES"))
    add((0, "TABLE"), (2, "LTYPE"), (70, 1), (0, "LTYPE"), (2, "CONTINUOUS"), (70, 0), (3, "Solid line"), (72, 65), (73, 0), (40, 0.0), (0, "ENDTAB"))
    add((0, "TABLE"), (2, "LAYER"), (70, len(LAYERS)))
    for name, (_, aci) in LAYERS.items():
        add((0, "LAYER"), (2, name), (70, 0), (62, aci), (6, "CONTINUOUS"))
    add((0, "ENDTAB"), (0, "ENDSEC"), (0, "SECTION"), (2, "ENTITIES"))
    for name in LAYERS:
        cs = layers.get(name)
        if cs is None or cs.is_empty():
            continue
        for c in _contours(cs):
            add((0, "POLYLINE"), (8, name), (66, 1), (70, 1))
            for x, y in c:
                add((0, "VERTEX"), (8, name), (10, f"{x:.4f}"), (20, f"{y:.4f}"), (30, "0.0"))
            add((0, "SEQEND"), (8, name))
    add((0, "ENDSEC"), (0, "EOF"))
    with open(path, "w") as f:
        f.write("\n".join(g) + "\n")


def export(folder, name, width, height, layers, title=""):
    """Write <folder>/svg/<name>.svg and <folder>/dxf/<name>.dxf; the drawing spans 0..width, 0..height."""
    for ext in ("svg", "dxf"):
        os.makedirs(os.path.join(folder, ext), exist_ok=True)
    write_svg(os.path.join(folder, "svg", name + ".svg"), width, height, layers, title or name)
    write_dxf(os.path.join(folder, "dxf", name + ".dxf"), layers)
    b = layers["CUT"].bounds()
    print(f"{name:34s} sheet {width:g} x {height:g} mm, cut outline {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} mm, "
          + ", ".join(f"{k} {v.num_contour()} paths" for k, v in layers.items() if v is not None and not v.is_empty()))


def preview(path, width, height, layers, scale=4, wood=(222, 190, 140), burn=(96, 62, 40), bg=(246, 243, 238), pad=10):
    """A simple picture of the cut part: wood where the material stays, dark where it is engraved or scored."""
    from PIL import Image, ImageDraw
    ss = 2
    k = scale * ss
    W, H = int((width + 2 * pad) * k), int((height + 2 * pad) * k)
    im = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(im)

    def pts(c):
        return [((x + pad) * k, (height - y + pad) * k) for x, y in c]

    def area(c):
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(c, c[1:] + c[:1])) / 2

    def fill(cs, on, off):
        cont = sorted(_contours(cs), key=lambda c: -abs(area(c)))
        for c in cont:
            dr.polygon(pts(c), fill=on if area(c) > 0 else off)

    fill(layers["CUT"], wood, bg)
    edge = tuple(int(v * 0.62) for v in wood)
    for c in _contours(layers["CUT"]):
        dr.line(pts(c) + pts(c)[:1], fill=edge, width=max(2, int(0.35 * k)))
    if layers.get("ENGRAVE") is not None and not layers["ENGRAVE"].is_empty():
        fill(layers["ENGRAVE"], burn, wood)
    if layers.get("SCORE") is not None and not layers["SCORE"].is_empty():
        for c in _contours(layers["SCORE"]):
            dr.line(pts(c) + pts(c)[:1], fill=burn, width=max(2, int(0.3 * k)))
    im = im.resize((W // ss, H // ss), Image.LANCZOS)
    im.save(path, optimize=True)
    return im
