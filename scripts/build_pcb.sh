#!/bin/bash
# Full PCB pipeline: ergogen -> Freerouting -> finish_routes -> GND pours -> DRC -> gerbers + JLCPCB files.
#
# Needs: node (npm install), KiCad with its python module (KiCad 7+; the
# python must be the one pcbnew was built for), java and the Freerouting jar
# (FREEROUTING_JAR, default build/freerouting.jar). On a headless machine run
# it under xvfb-run.
#
# Outputs:
#   output/                       raw ergogen output (unrouted)
#   pcb/ultra-choc-wings.kicad_pcb routed board, open this in KiCad
#   pcb/drc.rpt                   DRC report
#   jlcpcb/gerbers.zip            upload to JLCPCB (same file for both halves)
#   jlcpcb/bom.csv, jlcpcb/cpl-*.csv  assembly files, see jlcpcb/README.md
#   case/board.scad, case/stl/       board data for the cases, printable parts
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=${KICAD_PYTHON:-python3}
JAR=${FREEROUTING_JAR:-build/freerouting.jar}
PASSES=${FREEROUTING_PASSES:-60}
mkdir -p build pcb jlcpcb

npx ergogen . -o output

$PYTHON scripts/kicad_route.py export output/pcbs/main.kicad_pcb build/main.dsn
java -jar "$JAR" -de build/main.dsn -do build/main.ses -mp "$PASSES"
$PYTHON scripts/kicad_route.py import output/pcbs/main.kicad_pcb build/main.ses pcb/ultra-choc-wings.kicad_pcb
# Freerouting misreads a few pads and leaves some nets split, and keeps only
# 0.2 mm from the board edge; join the islands and reroute edge tracks.
$PYTHON scripts/finish_routes.py pcb/ultra-choc-wings.kicad_pcb
$PYTHON scripts/kicad_route.py pour pcb/ultra-choc-wings.kicad_pcb
$PYTHON scripts/kicad_route.py drc pcb/ultra-choc-wings.kicad_pcb pcb/drc.rpt

rm -rf build/gerbers && mkdir -p build/gerbers
kicad-cli pcb export gerbers pcb/ultra-choc-wings.kicad_pcb -o build/gerbers/ \
  --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask
kicad-cli pcb export drill pcb/ultra-choc-wings.kicad_pcb -o build/gerbers/ --excellon-separate-th
(cd build/gerbers && rm -f ../../jlcpcb/gerbers.zip && zip -q ../../jlcpcb/gerbers.zip *)

$PYTHON scripts/jlcpcb.py pcb/ultra-choc-wings.kicad_pcb jlcpcb/

# Cases: board outline, holes and parts from the routed board, then the STLs
$PYTHON scripts/make_case.py pcb/ultra-choc-wings.kicad_pcb case/board.scad
if command -v openscad >/dev/null; then
  scripts/build_case.sh
fi
