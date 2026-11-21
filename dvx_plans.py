"""Woodworking plan pages for the DIVELUX sauna projects: parts as boxes, orthographic views with dimensions,
an isometric picture, a cut list and the assembly steps, laid out as Letter-size HTML pages (then printed to PDF
with render_plans.js).

Model units are inches (US lumber); every dimension is printed in inches and millimeters.
Needs:  pip install manifold3d numpy pillow
License: CC BY 4.0 - DIVELUX, https://diveluxsaunahat.com
"""
import html
import math
import os
import sys
from fractions import Fraction

from manifold3d import Manifold

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "3d"))
from render import render  # noqa: E402  (the small numpy renderer of the 3D-print set)
from dvx_cad import to_trimesh  # noqa: E402

MM = 25.4
WOOD = [(226, 190, 146), (214, 170, 120), (200, 156, 108), (236, 206, 166)]


# ---------------- numbers ----------------
def inch(v, denom=16):
    """3.75 -> '3-3/4', 0.75 -> '3/4', 14 -> '14' (nearest 1/16 in)."""
    neg = v < 0
    v = abs(v)
    f = Fraction(round(v * denom), denom)
    whole, rest = divmod(f.numerator, f.denominator)
    if rest == 0:
        s = f"{whole}"
    elif whole == 0:
        s = f"{Fraction(rest, f.denominator)}"
    else:
        s = f"{whole}-{Fraction(rest, f.denominator)}"
    return ("-" if neg else "") + s


def both(v):
    """'14 in (356 mm)'."""
    return f"{inch(v)} in ({round(v * MM)} mm)"


# ---------------- parts ----------------
def along_x(profile_yz, x0, x1):
    """Extrude a 2D profile drawn as (y, z) along the x axis from x0 to x1 (a board seen from its side)."""
    return profile_yz.extrude(x1 - x0).rotate((90, 0, 0)).rotate((0, 0, 90)).translate((x0, 0, 0))


def board_on_slope(size, angle_deg, y0, z0, x0=0.0):
    """A board (x, y, z size) tilted up by angle_deg about the x axis, its lower front bottom edge at (x0, y0, z0)."""
    return Manifold.cube(size).rotate((angle_deg, 0, 0)).translate((x0, y0, z0))
class Part:
    """A rectangular board: size (x, y, z) in inches, placed by a transform function on a Manifold."""

    def __init__(self, name, size, place=None, shape=None, color=0, group=""):
        self.name, self.size, self.color, self.group = name, size, color, group
        base = shape if shape is not None else Manifold.cube(size)
        self.solid = place(base) if place else base


def assembly(parts):
    return [(p.solid, WOOD[p.color % len(WOOD)]) for p in parts]


def iso_png(parts, path, az=35, el=24, size=(1200, 900), extra=()):
    """Isometric-style picture of the assembly (inches scaled to mm so edges and shading look right)."""
    items = [(to_trimesh(m.scale((MM, MM, MM))), c) for m, c in assembly(parts)]
    items += [(to_trimesh(m.scale((MM, MM, MM))), c) for m, c in extra]
    render(items, az=az, el=el, size=size, margin=0.06).save(path, optimize=True)


# ---------------- orthographic views ----------------
def _project(m, view):
    if view == "front":                              # seen from the front (-y): x right, z up
        r = m.rotate((-90, 0, 0))                    # (x, y, z) -> (x, z, -y)
        depth_sign = 1
    elif view == "side":                             # seen from the right (+x): y right, z up
        r = m.rotate((0, 0, -90)).rotate((-90, 0, 0))   # (x, y, z) -> (y, z, x)
        depth_sign = 1
    elif view == "top":
        r = m
        depth_sign = -1
    else:
        raise ValueError(view)
    cs = r.project()
    bb = r.bounding_box()
    depth = (bb[2] + bb[5]) / 2 * depth_sign            # z of the rotated part: larger = nearer for front/side
    return cs, depth


class View:
    """One orthographic view of the parts, drawn into an SVG box, plus dimension lines in model inches."""

    def __init__(self, parts, view, title):
        self.view, self.title = view, title
        self.shapes = []
        for p in parts:
            cs, depth = _project(p.solid, view)
            self.shapes.append((depth, cs, WOOD[p.color % len(WOOD)]))
        self.shapes.sort(key=lambda t: -t[0] if view == "top" else t[0])
        xs, ys = [], []
        for _, cs, _c in self.shapes:
            b = cs.bounds()
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
        self.bounds = (min(xs), min(ys), max(xs), max(ys))
        self.dims = []
        self.notes = []

    def dim_h(self, x0, x1, y, text=None, off=0.0):
        """Horizontal dimension between x0 and x1, drawn at height y (model inches)."""
        self.dims.append(("h", x0, x1, y, text or both(abs(x1 - x0))))
        return self

    def dim_v(self, y0, y1, x, text=None):
        self.dims.append(("v", y0, y1, x, text or both(abs(y1 - y0))))
        return self

    def note(self, x, y, tx, ty, text):
        """A leader from (x, y) to a label at (tx, ty), model inches."""
        self.notes.append((x, y, tx, ty, text))
        return self

    def svg(self, width_px, height_px, pad=46):
        x0, y0, x1, y1 = self.bounds
        for kind, a, b, c, _t in self.dims:
            if kind == "h":
                x0, x1, y0, y1 = min(x0, a, b), max(x1, a, b), min(y0, c), max(y1, c)
            else:
                y0, y1, x0, x1 = min(y0, a, b), max(y1, a, b), min(x0, c), max(x1, c)
        for x, y, tx, ty, _t in self.notes:
            x0, x1, y0, y1 = min(x0, x, tx), max(x1, x, tx), min(y0, y, ty), max(y1, y, ty)
        k = min((width_px - 2 * pad) / max(x1 - x0, 1e-6), (height_px - 2 * pad - 18) / max(y1 - y0, 1e-6))
        ox = pad + ((width_px - 2 * pad) - (x1 - x0) * k) / 2 - x0 * k
        oy = pad + 18 + ((height_px - 2 * pad - 18) - (y1 - y0) * k) / 2 + y1 * k

        def P(x, y):
            return ox + x * k, oy - y * k

        out = [f'<svg viewBox="0 0 {width_px} {height_px}" width="{width_px}" height="{height_px}" xmlns="http://www.w3.org/2000/svg">',
               f'<text x="6" y="16" class="vt">{html.escape(self.title)}</text>']
        for _d, cs, col in self.shapes:
            for poly in cs.to_polygons():
                pts = " ".join(f"{P(x, y)[0]:.1f},{P(x, y)[1]:.1f}" for x, y in poly)
                out.append(f'<polygon points="{pts}" fill="rgb{col}" stroke="#1b1512" stroke-width="1.1" stroke-linejoin="round"/>')
        for kind, a, b, c, t in self.dims:
            if kind == "h":
                (ax, ay), (bx, by) = P(a, c), P(b, c)
                out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="dl" marker-start="url(#a)" marker-end="url(#a)"/>')
                out.append(f'<line x1="{ax:.1f}" y1="{ay - 7:.1f}" x2="{ax:.1f}" y2="{ay + 7:.1f}" class="dt"/><line x1="{bx:.1f}" y1="{by - 7:.1f}" x2="{bx:.1f}" y2="{by + 7:.1f}" class="dt"/>')
                out.append(f'<text x="{(ax + bx) / 2:.1f}" y="{ay - 5:.1f}" class="dx" text-anchor="middle">{html.escape(t)}</text>')
            else:
                (ax, ay), (bx, by) = P(c, a), P(c, b)
                out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="dl" marker-start="url(#a)" marker-end="url(#a)"/>')
                out.append(f'<line x1="{ax - 7:.1f}" y1="{ay:.1f}" x2="{ax + 7:.1f}" y2="{ay:.1f}" class="dt"/><line x1="{bx - 7:.1f}" y1="{by:.1f}" x2="{bx + 7:.1f}" y2="{by:.1f}" class="dt"/>')
                cx = (self.bounds[0] + self.bounds[2]) / 2
                mx, my = (ax + 14 if c > cx else ax - 6), (ay + by) / 2
                out.append(f'<text x="{mx:.1f}" y="{my:.1f}" class="dx" text-anchor="middle" transform="rotate(-90 {mx:.1f} {my:.1f})">{html.escape(t)}</text>')
        for x, y, tx, ty, t in self.notes:
            (ax, ay), (bx, by) = P(x, y), P(tx, ty)
            out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="ld"/><circle cx="{ax:.1f}" cy="{ay:.1f}" r="2.2" fill="#1b1512"/>')
            anchor = "start" if tx >= x else "end"
            out.append(f'<text x="{bx + (4 if anchor == "start" else -4):.1f}" y="{by + 4:.1f}" class="nt" text-anchor="{anchor}">{html.escape(t)}</text>')
        out.append('<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                   '<path d="M0,1 L10,5 L0,9" fill="none" stroke="#1b1512" stroke-width="1.4"/></marker></defs>')
        out.append("</svg>")
        return "\n".join(out)


# ---------------- pages ----------------
CSS = """
@font-face{font-family:'Bricolage';src:url('../../_fonts/BricolageGrotesque-Bold.ttf');font-weight:700}
@font-face{font-family:'Inter';src:url('../../_fonts/Inter-Regular.ttf');font-weight:400}
@font-face{font-family:'Inter';src:url('../../_fonts/Inter-SemiBold.ttf');font-weight:600}
@page{size:11in 8.5in;margin:0}
*{box-sizing:border-box}
body{margin:0;background:#f6f3ee;color:#1b1512;font:400 10.2px/1.42 Inter,Arial,sans-serif}
.page{width:11in;height:8.5in;padding:.42in .5in .38in;position:relative;page-break-after:always;overflow:hidden;background:#fbf9f5}
.page:last-child{page-break-after:auto}
header{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1.5px solid #1b1512;padding-bottom:6px;margin-bottom:10px}
h1,h2{font-family:Bricolage,Arial,sans-serif;font-weight:700;margin:0;letter-spacing:-.01em}
h1{font-size:23px}
h2{font-size:13.5px;margin:0 0 4px}
.sub{font-size:10.5px;color:#5a4e45}
.tag{font:600 9.5px Inter;color:#5a4e45;text-align:right}
.tag b{display:inline-block;width:8px;height:8px;border-radius:2px;background:#f0762e;margin-right:5px;vertical-align:0}
.grid{display:grid;grid-template-columns:7.05in 2.85in;gap:.1in}
.col{display:flex;flex-direction:column;gap:8px}
.box{background:#fff;border:1px solid #d9d0c4;border-radius:6px;padding:7px 9px}
.box.pic{padding:0;overflow:hidden}
.box.pic img{display:block;width:100%;height:100%;object-fit:cover}
.views{display:grid;gap:.1in}
table{border-collapse:collapse;width:100%;font-size:9.4px}
th,td{text-align:left;padding:2.5px 4px;border-bottom:1px solid #e6dfd5;vertical-align:top}
th{font:600 9px Inter;color:#5a4e45;text-transform:uppercase;letter-spacing:.03em}
td.n{text-align:center;width:22px}
ol,ul{margin:0;padding-left:15px}
li{margin:0 0 3px}
.warn{border-left:3px solid #f0762e}
.foot{position:absolute;left:.5in;right:.5in;bottom:.18in;display:flex;justify-content:space-between;font-size:8.6px;color:#5a4e45}
svg .vt{font:600 11px Inter;fill:#5a4e45;text-transform:uppercase;letter-spacing:.04em}
svg .dx{font:600 10.5px Inter;fill:#1b1512}
svg .nt{font:400 10px Inter;fill:#1b1512}
svg .dl{stroke:#1b1512;stroke-width:.9}
svg .dt{stroke:#1b1512;stroke-width:.8}
svg .ld{stroke:#1b1512;stroke-width:.7}
"""


def page(title, sub, body, n, total, project_id):
    return f"""<section class="page">
<header><div><h1>{html.escape(title)}</h1><div class="sub">{sub}</div></div>
<div class="tag"><b></b>DIVELUX free sauna plans &middot; {project_id}<br>Sheet {n} of {total} &middot; inches (millimeters)</div></header>
{body}
<div class="foot"><span>Made by DIVELUX, makers of handmade wool sauna hats &middot; diveluxsaunahat.com &middot; more free tools: diveluxsaunahat.com/pages/sauna-tools</span><span>CC BY 4.0 &middot; Build at your own risk.</span></div>
</section>"""


def document(title, pages):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body>
{''.join(pages)}
</body></html>"""


def cut_table(rows):
    """rows: (mark, qty, part, stock, length_in, note)."""
    out = ['<table><tr><th>#</th><th>Qty</th><th>Part</th><th>Size</th></tr>']
    for mark, qty, name, stock, length, note in rows:
        size = f"{stock} &times; {both(length)}"
        out.append(f'<tr><td class="n"><b>{mark}</b></td><td class="n">{qty}</td><td>{html.escape(name)}'
                   f'{"<br><span class=sub>" + html.escape(note) + "</span>" if note else ""}</td><td>{size}</td></tr>')
    out.append("</table>")
    return "\n".join(out)


def li(items):
    return "<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"


def ul(items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


SAFETY = [
    "Build at your own risk. These are hobby plans, not engineered drawings, and nobody has checked them for your bench, your wall or your sauna.",
    "Check that nothing can burn or pinch: no metal on a surface skin can touch, no sharp edges, no gaps that can trap a finger.",
    "Round over or sand every edge you can touch. Leave wood for the hot room unfinished: no varnish, paint or stain.",
    "Hot room or not: screws and other metal get hot in a sauna. Keep every head below the surface or on the hidden side.",
]

WOODS = ("Use a wood that is sold for sauna interiors where you live, such as aspen, alder or western red cedar. "
         "Choose clear boards without loose knots or resin pockets.")


def finalize_pdf(path, title, subject, keywords):
    """Set the PDF metadata (title, author, subject, keywords). Needs pypdf."""
    import pypdf
    r = pypdf.PdfReader(path)
    w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.add_metadata({"/Title": title, "/Author": "DIVELUX", "/Subject": subject, "/Keywords": keywords,
                    "/Creator": "DIVELUX free sauna plans (diveluxsaunahat.com)"})
    with open(path, "wb") as f:
        w.write(f)
