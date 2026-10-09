#!/usr/bin/env python3
"""Write JLCPCB BOM and placement (CPL) files for both halves.

    python3 scripts/jlcpcb.py pcb/ultra-choc-wings.kicad_pcb jlcpcb/

Both halves use the same gerbers. Every SMD part sits on the switch side:
  - left half:  switch side is F, JLCPCB assembles the TOP side
  - right half: the board is flipped, switch side is B, JLCPCB assembles BOTTOM

The reversible footprints mirror their B copper, so flipping a footprint in
KiCad does not move any copper. This script flips the assembled parts in a
copy of the board, checks that the copper really is unchanged, and lets KiCad
write the bottom-side placement file from that copy.
"""
import csv
import os
import subprocess
import sys
import tempfile

import pcbnew

# value -> (description, footprint, LCSC part). Check stock before ordering.
PARTS = {
    "1N4148W": ("Switching diode 1N4148W", "SOD-123", "C81598"),
    "1N4148WS": ("Switching diode 1N4148WS", "SOD-323", "C2128"),
    "B5819W": ("Schottky diode 40V 1A B5819W", "SOD-123", "C8598"),
    "LED_red_0603": ("LED red 0603", "0603", "C2286"),
    "1k": ("Resistor 1k 1% 0603", "0603", "C21190"),
    "100k": ("Resistor 100k 1% 0603", "0603", "C25803"),
    "22uF": ("Capacitor 22uF 25V X5R 0805", "0805", "C45783"),
    "AO3400A": ("N-MOSFET AO3400A", "SOT-23", "C20917"),
    "SPDT": ("Slide switch SPDT (C128955 land pattern)", "SMD", "C128955"),
}
# Reference prefixes JLCPCB places. Switches (SW), the XIAO and the coin cell
# holder (BT) are hand-soldered.
ASSEMBLED = ("D", "L", "R", "C", "Q", "T")


def assembled(board):
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        prefix = ref.rstrip("0123456789")
        if prefix in ASSEMBLED and not ref.startswith("SW"):
            yield fp


def value_of(fp):
    return fp.GetValue() or ("SPDT" if fp.GetReference().startswith("T") else "")


def copper(fp):
    out = set()
    for pad in fp.Pads():
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if pad.IsOnLayer(layer):
                pos = pad.GetPosition()
                out.add((layer, round(pos.x / 1000), round(pos.y / 1000), pad.GetNetname()))
    return out


def write_bom(board, path):
    groups = {}
    for fp in assembled(board):
        groups.setdefault(value_of(fp), []).append(fp.GetReference())
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for value, refs in sorted(groups.items()):
            desc, footprint, lcsc = PARTS[value]
            w.writerow([desc, ",".join(sorted(refs, key=lambda r: (r.rstrip("0123456789"), int(r.lstrip("BCDLQRTSW") or 0)))), footprint, lcsc])


def write_cpl(pcb_path, side, path):
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "pos.csv")
        subprocess.run(
            ["kicad-cli", "pcb", "export", "pos", pcb_path, "--side", side,
             "--format", "csv", "--units", "mm", "--output", raw],
            check=True, capture_output=True,
        )
        rows = list(csv.DictReader(open(raw)))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            if r["Ref"].rstrip("0123456789") not in ASSEMBLED or r["Ref"].startswith("SW"):
                continue
            layer = "Top" if r["Side"] == "top" else "Bottom"
            w.writerow([r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm', layer, f'{float(r["Rot"]):.1f}'])


def main():
    pcb_path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    board = pcbnew.LoadBoard(pcb_path)
    write_bom(board, os.path.join(out, "bom.csv"))
    write_cpl(pcb_path, "front", os.path.join(out, "cpl-left-top.csv"))

    # Right half: flip every assembled part to B and prove the copper is identical.
    for fp in assembled(board):
        before = copper(fp)
        angle = fp.GetOrientationDegrees()
        fp.Flip(fp.GetPosition(), True)
        # Mirroring in board space also mirrors the rotation; find the
        # orientation that puts the (mirror-symmetric) copper back in place.
        for candidate in (angle, -angle, 180 - angle, 180 + angle):
            fp.SetOrientationDegrees(candidate)
            if copper(fp) == before:
                break
        else:
            sys.exit(f"{fp.GetReference()}: copper changes when flipped, footprint is not reversible")
    with tempfile.TemporaryDirectory() as tmp:
        flipped = os.path.join(tmp, "flipped.kicad_pcb")
        board.Save(flipped)
        write_cpl(flipped, "back", os.path.join(out, "cpl-right-bottom.csv"))
    print(f"BOM and CPL files written to {out}")


if __name__ == "__main__":
    main()
