# Ordering from JLCPCB

One PCB design is used for both halves. Order it twice: once assembled on the
top side (left half), once assembled on the bottom side (right half). The
gerbers are identical.

| File | Use |
| --- | --- |
| `gerbers.zip` | PCB, 2 layers, 1.6 mm. Same file for both orders. |
| `bom.csv` | Bill of materials (LCSC part numbers). Same file for both orders. |
| `cpl-left-top.csv` | Placement for the **left** half: assemble **Top side**. |
| `cpl-right-bottom.csv` | Placement for the **right** half: assemble **Bottom side**. |

Every SMD part is on the switch side, so each half only needs single-side
assembly. The reversible footprints mirror their copper on the back, which is
why the right half can use the exact same board flipped over;
`scripts/jlcpcb.py` checks that no copper moves when the parts are flipped.

## What JLCPCB assembles

| Ref | Part | LCSC |
| --- | --- | --- |
| D1–D18 | 1N4148WS matrix diodes (SOD-323) | C2128 |
| D19 | B5819W Schottky, reverse protection for the coin cell | C8598 |
| L1–L18 | Red LED 0603 (per key) | C2286 |
| R1–R18 | 1 kΩ 0603 (LED current) | C21190 |
| R19 | 100 kΩ 0603 (MOSFET gate pull-down) | C25803 |
| C1, C2 | 22 µF 0805 (buffer for the coin cell) | C45783 |
| Q1 | AO3400A N-MOSFET (LED switch) | C20917 |
| T1 | SPDT slide switch, power | C128955 |

Check stock and the rotation preview on JLCPCB's site before paying; the
rotations come straight from KiCad and polarised parts (diodes, LEDs, Q1) are
the ones to look at.

## What you solder yourself

* 18 Kailh PG1316S switches per half (SW1–SW18), on the same side as the parts.
* Seeed XIAO nRF52840 per half, plus one more for the dongle (no PCB needed).
  Mount it on the switch side and bridge the `[> ]` jumper pads under it on
  that side.
* CR2032 holder (BT1), MPD BC-2003 or Q&J CR2032-BS-6-1 land pattern. It is
  left out of the BOM because stock of these varies; add it to the order if
  JLCPCB has one.
* A short wire from the RAW pad to the BAT+ pad under the XIAO.

## Regenerating

`scripts/build_pcb.sh` regenerates everything in this folder from
`config.yaml`.
