#!/usr/bin/env python3
"""Prepare, autoroute and finish the ergogen PCB with KiCad's pcbnew module.

    python3 scripts/kicad_route.py export  output/pcbs/main.kicad_pcb build/main.dsn
    (run Freerouting on build/main.dsn -> build/main.ses)
    python3 scripts/kicad_route.py import  output/pcbs/main.kicad_pcb build/main.ses pcb/ultra-choc-wings.kicad_pcb
    python3 scripts/kicad_route.py pour    pcb/ultra-choc-wings.kicad_pcb
    python3 scripts/kicad_route.py drc     pcb/ultra-choc-wings.kicad_pcb pcb/drc.rpt

`scripts/build_pcb.sh` runs the whole thing.
"""
import sys

import pcbnew

MM = pcbnew.FromMM

# JLCPCB standard 2-layer capabilities are well below these numbers.
TRACK = 0.25
CLEARANCE = 0.2
VIA_D = 0.6
VIA_DRILL = 0.3


def apply_rules(board):
    ds = board.GetDesignSettings()
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetTrackWidth(MM(TRACK))
    nc.SetClearance(MM(CLEARANCE))
    nc.SetViaDiameter(MM(VIA_D))
    nc.SetViaDrill(MM(VIA_DRILL))
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_ViasMinSize = MM(0.5)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.m_HoleClearance = MM(0.25)


def _sexpr(text):
    """Tiny s-expression reader, enough for Specctra session files."""
    import re

    tokens = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    stack = [[]]
    for tok in tokens:
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok.strip('"'))
    return stack[0][0]


def import_ses(board, path):
    """Import wires and vias from a Freerouting .ses file.

    KiCad 8+ can do this through pcbnew.ImportSpecctraSES(board, path); the
    KiCad 7 binding only works inside the GUI, so fall back to a small parser.
    """
    try:
        return pcbnew.ImportSpecctraSES(board, path)
    except TypeError:
        pass
    session = _sexpr(open(path).read())
    routes = next(x for x in session if isinstance(x, list) and x[0] == "routes")
    scale = 1.0
    for item in routes:
        if isinstance(item, list) and item[0] == "resolution":
            scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[item[1]] / float(item[2])
    network = next(x for x in routes if isinstance(x, list) and x[0] == "network_out")

    def pt(x, y):
        return pcbnew.VECTOR2I(MM(float(x) * scale), MM(-float(y) * scale))

    layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    for net in network:
        if not (isinstance(net, list) and net[0] == "net"):
            continue
        netinfo = board.FindNet(net[1])
        for item in net[2:]:
            if item[0] == "wire":
                path = item[1]
                layer, width, coords = path[1], float(path[2]) * scale, path[3:]
                points = [pt(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
                for a, b in zip(points, points[1:]):
                    track = pcbnew.PCB_TRACK(board)
                    track.SetStart(a)
                    track.SetEnd(b)
                    track.SetWidth(MM(width))
                    track.SetLayer(layers[layer])
                    track.SetNet(netinfo)
                    board.Add(track)
            elif item[0] == "via":
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pt(item[2], item[3]))
                via.SetDrill(MM(VIA_DRILL))
                via.SetWidth(MM(VIA_D))
                via.SetNet(netinfo)
                board.Add(via)
    return True


def add_ground_pours(board):
    """Fill both copper layers with GND inside the board outline."""
    gnd = board.FindNet("GND")
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNetCode(gnd.GetNetCode())
        zone.SetLocalClearance(MM(0.3))
        zone.SetMinThickness(MM(0.25))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetIsFilled(False)
        zone.Outline().AddOutline(outline.Outline(0))
        board.Add(zone)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def main():
    mode = sys.argv[1]
    board = pcbnew.LoadBoard(sys.argv[2])
    apply_rules(board)
    if mode == "export":
        if not pcbnew.ExportSpecctraDSN(board, sys.argv[3]):
            sys.exit("DSN export failed")
    elif mode == "import":
        if not import_ses(board, sys.argv[3]):
            sys.exit("SES import failed")
        for track in list(board.GetTracks()):
            if track.GetLength() < MM(0.01) and track.Type() == pcbnew.PCB_TRACE_T:
                board.Remove(track)
        board.Save(sys.argv[4])
    elif mode == "pour":
        for zone in list(board.Zones()):
            board.Remove(zone)
        add_ground_pours(board)
        board.Save(sys.argv[2])
    elif mode == "drc":
        pcbnew.WriteDRCReport(board, sys.argv[3], pcbnew.EDA_UNITS_MILLIMETRES, True)
        print(open(sys.argv[3]).read().split("** End")[0].splitlines()[-3:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
