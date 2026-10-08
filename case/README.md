# Uniboard case

`ultra_choc_wings_case.stl` is a single printable tray that holds both halves
side by side at a fixed splay, turning the split board into one unit.

* Each half drops into its pocket and rests on a solid floor (all SMD parts are
  on the top side, so the underside of the PCB is flat), which keeps the
  switches from flexing the board.
* Three M2 × 4 mm screws per half go through the PCB's mounting holes and
  self-tap into the floor. Use low-profile (wafer) heads. For heat-set inserts
  set `pilot_d = 3.2` in the .scad file.
* The CR2032 holder is on top and stays reachable.
* A notch in the top wall clears the XIAO's USB-C port and the power switch.
* The deck between the halves is a shallow tray; the dongle fits there for
  travel.

## Changing the layout

Open `ultra_choc_wings_case.scad` in OpenSCAD and change the parameters at the
top (`splay`, `gap`, wall and floor thickness), then export an STL. The board
outline and hole positions are generated from the PCB by
`scripts/make_case.py`; rerun `scripts/build_pcb.sh` after changing
`config.yaml`.

Print flat, floor down, no supports. 0.2 mm layers, 3 walls.
