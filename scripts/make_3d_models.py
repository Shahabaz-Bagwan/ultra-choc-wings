#!/usr/bin/env python3
"""Give every part on the board a 3D model, so KiCad's 3D viewer shows it.

    python3 scripts/make_3d_models.py pcb/ultra-choc-wings.kicad_pcb [--preview docs/board-3d.png [--read old.kicad_pcb]]

The footprints come from Ergogen without any 3D model, so the 3D viewer shows
a bare board. This writes simple VRML models (boxes and cylinders sized from
the datasheet outlines, not exact CAD) to pcb/ucw.3dshapes/ and adds a
`(model ...)` line to each footprint on the board and in pcb/ucw.pretty/.
All parts sit on the switch side, which is the front (F) for the left half;
KiCad mirrors the models by itself for a footprint on the back.

Everything is edited as text, so it works on a board saved by any KiCad
version. Rerunning replaces the model lines. With --preview it also renders
images of the board with the models, with and without keycaps (needs OpenSCAD
and a board KiCad's python module can open).
"""
import argparse
import math
import os
import re
import subprocess
import sys
import tempfile

# --- parts ------------------------------------------------------------------
# Models are in mm, x right, y up (so y is the footprint's y mirrored), z up
# from the board surface. Each primitive is
#   ("box", color, cx, cy, cz, sx, sy, sz)   centre and size
#   ("cyl", color, cx, cy, z0, radius, h)    base centre, radius, height
BLACK, GRAY, SILVER = (0.08, 0.08, 0.09), (0.2, 0.2, 0.22), (0.78, 0.78, 0.8)
WHITE, RED, TAN = (0.92, 0.92, 0.9), (0.85, 0.12, 0.1), (0.62, 0.45, 0.28)


def box(color, cx, cy, cz, sx, sy, sz):
    return ("box", color, cx, cy, cz, sx, sy, sz)


def cyl(color, cx, cy, z0, r, h):
    return ("cyl", color, cx, cy, z0, r, h)


def chip(body, length, width, height, end, end_len, lead_z=0.0):
    """Two-terminal SMD part: body between two terminations."""
    pieces = [box(body, 0, 0, lead_z + height / 2, length - 2 * end_len, width, height)]
    for s in (-1, 1):
        pieces.append(box(end, s * (length / 2 - end_len / 2), 0, lead_z + height / 2, end_len, width, height))
    return pieces


# Switch: housing 2.2 mm, stem to 3.2 mm (the height the cases assume).
SWITCH = [box(GRAY, 0, 0, 1.1, 13.8, 13.8, 2.2), box(WHITE, 0, 0, 2.7, 4.2, 3.0, 1.0)]
# Pad 1 (cathode) is at -x on the front.
SOD123 = [box(BLACK, 0, 0, 0.55, 2.6, 1.6, 1.1), box(SILVER, -1.0, 0, 0.56, 0.3, 1.62, 1.12),
          box(SILVER, -1.7, 0, 0.15, 0.8, 1.0, 0.3), box(SILVER, 1.7, 0, 0.15, 0.8, 1.0, 0.3)]
SOD323 = chip(BLACK, 1.7, 1.25, 0.9, SILVER, 0.35)
LED0603 = chip(RED, 1.6, 0.8, 0.5, SILVER, 0.3) + [box(BLACK, -0.45, 0, 0.51, 0.12, 0.8, 0.52)]
SOT23 = [box(BLACK, 0, 0, 0.55, 1.3, 2.9, 1.1)] + \
        [box(SILVER, -0.95, y, 0.2, 0.8, 0.5, 0.3) for y in (-0.95, 0.95)] + [box(SILVER, 0.95, 0, 0.2, 0.8, 0.5, 0.3)]
# CR2032 in its holder: base, cell, and the two contact clips at x = +-11.9.
COINCELL = [cyl(BLACK, 0, 0, 0, 11.0, 1.4), cyl(SILVER, 0, 0, 1.4, 10.0, 3.2)] + \
           [box(SILVER, s * 11.9, 0, 1.8, 2.6, 5.56, 3.6) for s in (-1, 1)]
# Slide switch: body towards +y (footprint -y is the lever side).
SLIDE = [box(GRAY, 0, -0.75, 1.0, 8.4, 4.5, 2.0), box(SILVER, 0, 2.8, 1.2, 1.8, 2.6, 1.2)]
# XIAO nRF52840: module with the USB-C at the -x end of the footprint.
# The footprint spans y -17.78..0, so the model spans y 0..17.78.
XIAO = [box(BLACK, -10.6, 8.89, 0.8, 21.0, 17.78, 1.0), box(SILVER, -17.8, 8.89, 2.9, 7.3, 8.94, 3.26),
        box(SILVER, -8.5, 8.89, 1.9, 7.5, 8.5, 1.2)]

MODELS = {
    "CPG1316S01D02_reversible": ("ucw_switch", SWITCH),
    "REV_SOD123": ("ucw_sod123", SOD123),
    "REV_SOD323": ("ucw_sod323", SOD323),
    "REV_0603": ("ucw_0603", chip(BLACK, 1.6, 0.8, 0.45, SILVER, 0.3)),
    "REV_0805": ("ucw_0805", chip(TAN, 2.0, 1.25, 0.9, SILVER, 0.4)),
    "REV_LED0603": ("ucw_led0603", LED0603),
    "REV_SOT-23": ("ucw_sot23", SOT23),
    "REV_CR2032_BC2003": ("ucw_cr2032", COINCELL),
    "REV_SPDT_C128955": ("ucw_slide", SLIDE),
    "xiao-ble": ("ucw_xiao", XIAO),
}

# Keycap, only for the preview: a low-profile cap on the switch stem.
KEYCAP = (17.0, 16.0, 3.4, 2.0)  # width, depth, bottom z, height


# --- VRML -------------------------------------------------------------------
UNIT = 2.54  # KiCad reads VRML in units of 0.1 inch


def wrl_box(cx, cy, cz, sx, sy, sz):
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return pts, faces


def wrl_cyl(cx, cy, z0, r, h, n=32):
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z) for z in (z0, z0 + h)
           for i in range(n)]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return pts, faces


def write_wrl(path, prims):
    out = ["#VRML V2.0 utf8", "# Ultra Choc Wings part model, generated by scripts/make_3d_models.py",
           "# Units are 0.1 inch, as KiCad expects."]
    for prim in prims:
        kind, color = prim[0], prim[1]
        pts, faces = wrl_box(*prim[2:]) if kind == "box" else wrl_cyl(*prim[2:])
        coords = ", ".join(f"{x / UNIT:.5f} {y / UNIT:.5f} {z / UNIT:.5f}" for x, y, z in pts)
        idx = ", ".join(" ".join(str(i) for i in f) + " -1" for f in faces)
        r, g, b = color
        out.append(f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} "
                   f"specularColor 0.3 0.3 0.3 ambientColor {r * .5:.3f} {g * .5:.3f} {b * .5:.3f} shininess 0.3 }} }}\n"
                   f"  geometry IndexedFaceSet {{ ccw TRUE solid FALSE creaseAngle 0.5 coord Coordinate {{ point [ {coords} ] }}\n"
                   f"    coordIndex [ {idx} ] }} }}")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


# --- linking ----------------------------------------------------------------

def model_line(name, indent):
    i, t = indent, "\t" if "\t" in indent else "  "
    return (f'{i}(model "${{KIPRJMOD}}/ucw.3dshapes/{name}.wrl"\n{i}{t}(offset (xyz 0 0 0))\n'
            f'{i}{t}(scale (xyz 1 1 1))\n{i}{t}(rotate (xyz 0 0 0))\n{i})')


def strip_models(block):
    """Remove earlier (model "${KIPRJMOD}/ucw.3dshapes/...") entries."""
    return re.sub(r'\n[ \t]*\(model "\$\{KIPRJMOD\}/ucw\.3dshapes/[^"]*"(?:[^()]|\([^()]*(?:\([^()]*\)[^()]*)*\))*\)', "", block)


def add_to_board(path):
    src = open(path).read()
    out, i, n = [], 0, 0
    for m in re.finditer(r'\(footprint "(?:ucw:)?([^"]+)"', src):
        if m.start() < i:
            continue
        depth, j = 0, m.start()
        while True:
            c = src[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            elif c == '"':
                j += 1
                while src[j] != '"':
                    j += 2 if src[j] == "\\" else 1
            j += 1
        block = strip_models(src[m.start():j + 1])
        if m.group(1) in MODELS:
            indent = re.search(r"\n([ \t]*)\(", block).group(1)
            block = block[:-1].rstrip() + "\n" + model_line(MODELS[m.group(1)][0], indent) + "\n" + indent[:-1] + ")"
            n += 1
        out.append(src[i:m.start()])
        out.append(block)
        i = j + 1
    out.append(src[i:])
    with open(path, "w") as f:
        f.write("".join(out))
    return n


def add_to_library(libdir):
    for name, (model, _) in MODELS.items():
        path = os.path.join(libdir, name + ".kicad_mod")
        if not os.path.exists(path):
            continue
        src = strip_models(open(path).read()).rstrip()
        assert src.endswith(")")
        with open(path, "w") as f:
            f.write(src[:-1].rstrip() + "\n" + model_line(model, "  ") + "\n)\n")


# --- preview ----------------------------------------------------------------

def scad_prim(p):
    if p[0] == "box":
        _, c, cx, cy, cz, sx, sy, sz = p
        return f"color([{c[0]},{c[1]},{c[2]}]) translate([{cx},{cy},{cz}]) cube([{sx},{sy},{sz}], center=true);"
    _, c, cx, cy, z0, r, h = p
    return f"color([{c[0]},{c[1]},{c[2]}]) translate([{cx},{cy},{z0}]) cylinder(r={r}, h={h}, $fn=48);"


def render_preview(board_path, png, keycaps=True):
    import pcbnew
    board = pcbnew.LoadBoard(board_path)
    mm = pcbnew.ToMM
    poly = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(poly)
    chain = poly.Outline(0)
    outline = [(round(mm(chain.CPoint(i).x), 3), round(-mm(chain.CPoint(i).y), 3)) for i in range(chain.PointCount())]
    w, d, z0, h = KEYCAP
    lines = ["// generated by scripts/make_3d_models.py --preview"]
    for name, (model, prims) in MODELS.items():
        lines.append(f"module {model}() {{ " + " ".join(scad_prim(p) for p in prims) + " }")
    lines.append(f"module keycap() color([0.93,0.93,0.9]) hull() {{ translate([0,0,{z0}]) linear_extrude(0.01) "
                 f"square([{w},{d}], center=true); translate([0,0,{z0 + h - 0.01}]) linear_extrude(0.01) "
                 f"square([{w - 3},{d - 3}], center=true); }}")
    pcb = ", ".join(f"[{x},{y}]" for x, y in outline)
    lines.append(f"color([0.1,0.42,0.22]) translate([0,0,-1.6]) linear_extrude(1.6) polygon([{pcb}]);")
    for fp in board.GetFootprints():
        name = str(fp.GetFPID().GetUniStringLibItemName()).split(":")[-1]
        if name not in MODELS or fp.GetLayer() != pcbnew.F_Cu:
            continue
        pos = fp.GetPosition()
        lines.append(f"translate([{mm(pos.x):.3f},{-mm(pos.y):.3f},0]) rotate([0,0,{fp.GetOrientationDegrees():.3f}]) "
                     f"{{ {MODELS[name][0]}(); {'keycap();' if keycaps and MODELS[name][0] == 'ucw_switch' else ''} }}")
    with tempfile.TemporaryDirectory() as tmp:
        scad = os.path.join(tmp, "board.scad")
        open(scad, "w").write("\n".join(lines) + "\n")
        subprocess.run(["xvfb-run", "-a", "openscad", "--preview", "--colorscheme=Tomorrow", "--viewall", "--autocenter",
                        "--projection=p", "--camera=0,0,0,50,0,20,0", "--imgsize=1800,1200", "-o", png, scad],
                       check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board", help="board to link the models into")
    ap.add_argument("--preview", metavar="PNG", help="also render the board with the models and keycaps, and PNG-parts.png without keycaps")
    ap.add_argument("--read", metavar="BOARD", help="board for --preview if KiCad's python cannot open `board`")
    args = ap.parse_args()
    outdir = os.path.dirname(os.path.abspath(args.board))
    shapes = os.path.join(outdir, "ucw.3dshapes")
    os.makedirs(shapes, exist_ok=True)
    for model, prims in MODELS.values():
        write_wrl(os.path.join(shapes, model + ".wrl"), prims)
    n = add_to_board(args.board)
    lib = os.path.join(outdir, "ucw.pretty")
    if os.path.isdir(lib):
        add_to_library(lib)
    print(f"wrote {len(MODELS)} models, linked {n} footprints")
    if args.preview:
        parts = args.preview[:-4] + "-parts.png"
        render_preview(args.read or args.board, args.preview)
        render_preview(args.read or args.board, parts, keycaps=False)
        print("wrote", args.preview, parts)


if __name__ == "__main__":
    main()
