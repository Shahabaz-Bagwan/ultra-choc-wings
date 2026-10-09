#!/bin/bash
# Export every printable case part to case/stl/ with OpenSCAD.
# case/board.scad comes from scripts/make_case.py (run by build_pcb.sh).
set -euo pipefail
cd "$(dirname "$0")/../case"
mkdir -p stl
for part in left_frame right_frame left_cover right_cover link; do
  openscad -D "part=\"$part\"" -o "stl/fold_$part.stl" fold.scad
done
for part in left right bridge_back bridge_front; do
  openscad -D "part=\"$part\"" -o "stl/split_$part.stl" split.scad
done
