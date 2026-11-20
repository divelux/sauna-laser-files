# Sauna laser-cut files

Free, parametric laser-cutting files for the sauna, from [DIVELUX](https://diveluxsaunahat.com), makers of handmade wool felt sauna hats.

| | Project | Material |
|---|---|---|
| ![SAUNA door sign](sauna-door-sign/img/sauna-door-sign-M-300mm.png) | **[SAUNA door sign](sauna-door-sign/)**: cut outline, scored border, engraved letters. Three sizes: 200 × 75, 300 × 112.5 and 400 × 150 mm. Any word you like with the script. | 3–6 mm plywood or solid wood |
| ![Plywood hat stand](sauna-hat-stand-plywood/img/stand-assembled.png) | **[Plywood sauna hat drying stand](sauna-hat-stand-plywood/)**: two arch ribs that cross slot-in-slot plus a base ring. 186 × 186 × 201 mm assembled. The same outline as the 3D-printed stand; the slots follow your sheet thickness. | 3 or 4 mm plywood |

Each folder has `svg/`, `dxf/`, preview pictures in `img/`, a `LISTING.md` with cutting notes, and the Python source. The shared helper `dvx_laser.py` sits in this folder.

## File conventions

- Units are millimeters, scale 1:1. Every drawing has a 5 mm margin around the parts.
- Layers are set apart by color, the way laser software expects:

| Layer | Color | Meaning |
|---|---|---|
| CUT | red (255, 0, 0), hairline stroke | cut through |
| SCORE | blue (0, 0, 255), hairline stroke | light vector line |
| ENGRAVE | black fill | raster engrave |

- In the SVG files the layers are named groups (they open as layers in Inkscape). In the DXF files they are layers named CUT, SCORE and ENGRAVE, and every shape is a closed polyline, so the files open in LightBurn, LaserGRBL, Inkscape, Fusion and most CAD programs.
- Lettering is converted to outlines. No font is needed to open the files.

## Changing the designs

Install the tools once: `pip install manifold3d fonttools numpy pillow`. Then edit the block of parameters at the top of a source file and run it, for example:

```
python3 sauna-door-sign/door_sign.py BANYA        # the sign with your own word, all three sizes
python3 sauna-hat-stand-plywood/stand_laser.py 3.4 # the stand for sheet that measures 3.4 mm
```

Text needs a bold TrueType font. Set the `DVX_FONT` environment variable to a .ttf file, or let the script pick a system font.

## Before you cut

- Test power and speed on a scrap of the same sheet.
- Run engraving first, then scoring, then cutting.
- Measure your sheet. Plywood sold as 3 mm is often 2.7 to 3.2 mm, and slot joints only work when the drawing matches the sheet.
- Plywood is for the changing room and the outside of the door. Inside a hot room use solid, unfinished wood.

## About the hat

A wool felt sauna hat is worn dry and air-dried after each visit, which is what the drying stand is for. The 3D-printable version of the stand and more sauna accessories are in the companion 3D-print set. More free sauna tools: https://diveluxsaunahat.com/pages/sauna-tools

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit DIVELUX with a link to https://diveluxsaunahat.com.
