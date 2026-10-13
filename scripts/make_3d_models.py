#!/usr/bin/env python3
"""Give every part on the board a 3D model, so KiCad's 3D viewer shows it.

    python3 scripts/make_3d_models.py pcb/ultra-choc-wings.kicad_pcb [--preview docs/board-3d.png [--read old.kicad_pcb]]

The footprints come from Ergogen without any 3D model, so the 3D viewer shows
a bare board. This writes simple STEP models (boxes and cylinders sized from
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
import glob
import math
import os
import shutil
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


# --- STEP -------------------------------------------------------------------


def prism(prim):
    """(polygon ccw, z0, z1) of a primitive; boxes and cylinders are prisms."""
    kind = prim[0]
    if kind == "box":
        _, _, cx, cy, cz, sx, sy, sz = prim
        poly = [(cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2), (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)]
        return poly, cz - sz / 2, cz + sz / 2
    _, _, cx, cy, z0, r, h = prim
    n = 32
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)], z0, z0 + h


def write_step(path, name, prims):
    """Write the primitives as a coloured STEP (AP214) file, one B-rep solid each.

    KiCad's 3D viewer and its STEP export load these through OpenCASCADE."""
    ents = []

    def add(text):
        ents.append(text)
        return f"#{len(ents)}"

    def num(v):
        return f"{v:.6f}"

    def pt(x, y, z):
        return add(f"CARTESIAN_POINT('',({num(x)},{num(y)},{num(z)}))")

    def d(x, y, z):
        return add(f"DIRECTION('',({num(x)},{num(y)},{num(z)}))")

    def frame(o, z, x):
        return add(f"AXIS2_PLACEMENT_3D('',{pt(*o)},{d(*z)},{d(*x)})")

    app = add("APPLICATION_CONTEXT('automotive design')")
    add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,{app})")
    mech = add(f"MECHANICAL_CONTEXT('none',{app},'mechanical')")
    prod = add(f"PRODUCT('{name}','{name}','',({mech}))")
    add(f"PRODUCT_RELATED_PRODUCT_CATEGORY('part','',({prod}))")
    form = add(f"PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('','',{prod},.NOT_KNOWN.)")
    pdc = add(f"PRODUCT_DEFINITION_CONTEXT('part definition',{app},'design')")
    pdef = add(f"PRODUCT_DEFINITION('design','',{form},{pdc})")
    pshape = add(f"PRODUCT_DEFINITION_SHAPE('','',{pdef})")
    ln = add("(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.))")
    an = add("(NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.))")
    sa = add("(NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT())")
    unc = add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-05),{ln},'distance_accuracy_value','')")
    ctx = add(f"(GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(({unc})) "
              f"GLOBAL_UNIT_ASSIGNED_CONTEXT(({ln},{an},{sa})) REPRESENTATION_CONTEXT('{name}','3D'))")
    origin = frame((0, 0, 0), (0, 0, 1), (1, 0, 0))
    solids, styled = [], []
    for prim in prims:
        poly, z0, z1 = prism(prim)
        n = len(poly)
        vb = [add(f"VERTEX_POINT('',{pt(x, y, z0)})") for x, y in poly]
        vt = [add(f"VERTEX_POINT('',{pt(x, y, z1)})") for x, y in poly]

        def edge(a, b, pa, pb):
            dx, dy, dz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            line = add(f"LINE('',{pt(*pa)},{add(f'VECTOR(\'\',{d(dx / length, dy / length, dz / length)},{num(length)})')})")
            return add(f"EDGE_CURVE('',{a},{b},{line},.T.)")

        eb = [edge(vb[i], vb[(i + 1) % n], (*poly[i], z0), (*poly[(i + 1) % n], z0)) for i in range(n)]
        et = [edge(vt[i], vt[(i + 1) % n], (*poly[i], z1), (*poly[(i + 1) % n], z1)) for i in range(n)]
        es = [edge(vb[i], vt[i], (*poly[i], z0), (*poly[i], z1)) for i in range(n)]

        def face(edges, plane):
            loop = add(f"EDGE_LOOP('',({','.join(add(f'ORIENTED_EDGE(\'\',*,*,{e},{o})') for e, o in edges)}))")
            bound = add(f"FACE_OUTER_BOUND('',{loop},.T.)")
            return add(f"ADVANCED_FACE('',({bound}),{plane},.T.)")

        faces = [face([(eb[i], ".F.") for i in reversed(range(n))], add(f"PLANE('',{frame((*poly[0], z0), (0, 0, -1), (1, 0, 0))})")),
                 face([(et[i], ".T.") for i in range(n)], add(f"PLANE('',{frame((*poly[0], z1), (0, 0, 1), (1, 0, 0))})"))]
        for i in range(n):
            j = (i + 1) % n
            dx, dy = poly[j][0] - poly[i][0], poly[j][1] - poly[i][1]
            length = math.hypot(dx, dy)
            plane = add(f"PLANE('',{frame((*poly[i], z0), (dy / length, -dx / length, 0), (dx / length, dy / length, 0))})")
            faces.append(face([(eb[i], ".T."), (es[j], ".T."), (et[i], ".F."), (es[i], ".F.")], plane))
        shell = add(f"CLOSED_SHELL('',({','.join(faces)}))")
        solid = add(f"MANIFOLD_SOLID_BREP('{name}',{shell})")
        solids.append(solid)
        r, g, b = prim[1]
        col = add(f"COLOUR_RGB('',{num(r)},{num(g)},{num(b)})")
        style = add(f"PRESENTATION_STYLE_ASSIGNMENT((SURFACE_STYLE_USAGE(.BOTH.,SURFACE_SIDE_STYLE('',"
                    f"(SURFACE_STYLE_FILL_AREA(FILL_AREA_STYLE('',(FILL_AREA_STYLE_COLOUR('',{col}))))))))))")
        styled.append(add(f"STYLED_ITEM('color',({style}),{solid})"))
    rep = add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('',({origin},{','.join(solids)}),{ctx})")
    add(f"SHAPE_DEFINITION_REPRESENTATION({pshape},{rep})")
    add(f"MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({','.join(styled)}),{ctx})")
    with open(path, "w") as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Ultra Choc Wings part model'),'2;1');\n"
                f"FILE_NAME('{name}.step','2026-10-13T00:00:00',('generated'),(''),'make_3d_models.py','','');\n"
                "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n")
        for i, e in enumerate(ents, 1):
            f.write(f"#{i}={e};\n")
        f.write("ENDSEC;\nEND-ISO-10303-21;\n")


# --- linking ----------------------------------------------------------------

def model_line(name, indent):
    i, t = indent, "\t" if "\t" in indent else "  "
    return (f'{i}(model "${{KIPRJMOD}}/ucw.3dshapes/{name}.step"\n{i}{t}(offset (xyz 0 0 0))\n'
            f'{i}{t}(scale (xyz 1 1 1))\n{i}{t}(rotate (xyz 0 0 0))\n{i})')


# The switch uses Kailh's real STEP model (copied from library/leptiosis.pretty
# next to the generated models). The offset places its origin at the footprint
# origin, same as the v1 footprint.
SWITCH_STEP = "PG1316S.step"
SWITCH_STEP_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "leptiosis.pretty", "PG1316S--装配体.STEP")
SWITCH_STEP_OFFSET = (-4.75, -6.25, -10.25)
SWITCH_NAMES = ("CPG1316S01D02_reversible", "CPG1316S01D02_reversible_mikefives")


def step_line(indent):
    i, t = indent, "\t" if "\t" in indent else "  "
    x, y, z = SWITCH_STEP_OFFSET
    return (f'{i}(model "${{KIPRJMOD}}/ucw.3dshapes/{SWITCH_STEP}"\n{i}{t}(offset (xyz {x} {y} {z}))\n'
            f'{i}{t}(scale (xyz 1 1 1))\n{i}{t}(rotate (xyz 0 0 0))\n{i})')


def strip_all_models(block):
    """Remove every (model ...) entry of a footprint block, whatever its path."""
    return re.sub(r'\n[ \t]*\(model "[^"]*"(?:[^()]|\([^()]*(?:\([^()]*\)[^()]*)*\))*\)', "", block)


def strip_models(block):
    """Remove earlier (model "${KIPRJMOD}/ucw.3dshapes/...") entries."""
    return re.sub(r'\n[ \t]*\(model "\$\{KIPRJMOD\}/ucw\.3dshapes/[^"]*"(?:[^()]|\([^()]*(?:\([^()]*\)[^()]*)*\))*\)', "", block)


def add_to_board(path):
    src = open(path).read()
    out, i, n = [], 0, 0
    for m in re.finditer(r'\(footprint "(?:\w+:)?([^"]+)"', src):
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
        if m.group(1) in SWITCH_NAMES:
            block = strip_all_models(block)
            indent = re.search(r"\n([ \t]*)\(", block).group(1)
            block = block[:-1].rstrip() + "\n" + step_line(indent) + "\n" + indent[:-1] + ")"
            n += 1
        elif m.group(1) in MODELS:
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
        if name in SWITCH_NAMES:
            src = strip_all_models(src)
            line = step_line("  ")
        else:
            line = model_line(model, "  ")
        with open(path, "w") as f:
            f.write(src[:-1].rstrip() + "\n" + line + "\n)\n")


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
    shutil.copy(SWITCH_STEP_SRC, os.path.join(shapes, SWITCH_STEP))
    for old in glob.glob(os.path.join(shapes, "*.wrl")):
        os.remove(old)
    for model, prims in MODELS.values():
        if model != "ucw_switch":  # the switch uses Kailh's STEP model
            write_step(os.path.join(shapes, model + ".step"), model, prims)
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
