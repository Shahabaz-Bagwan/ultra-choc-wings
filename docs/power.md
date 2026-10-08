# Power: CR2032 and per-key LEDs

The halves run from a single CR2032 each. That only works because of two choices:

1. **ZMK dongle.** A third XIAO nRF52840 plugged into the computer is the split
   central. Both halves are BLE peripherals, which only talk to the dongle and
   never advertise to hosts, so the radio duty cycle on the coin cell is as
   low as ZMK gets.
2. **LEDs are off unless you ask for them.**

## Power path

```
CR2032 (+) ─ slide switch ─ B5819W Schottky ─ RAW pad ──wire──> XIAO BAT+
                                               └ 2× 22 µF to GND
```

* The Schottky stops the XIAO's Li-ion charger from ever pushing current into
  the coin cell when USB is plugged in. A CR2032 is not rechargeable.
* The 2× 22 µF buffer the radio's transmit peaks; a coin cell has 10–30 Ω of
  internal resistance and sags badly on bursts without them.
* The XIAO's own regulator then feeds the 3V3 rail (about 2.6 V on a fresh
  cell after the diode, which the nRF52840 is happy with down to 1.7 V).
* ZMK's battery percentage assumes a Li-ion cell and would always read 0 %, so
  battery reporting is turned off in the halves' config.

## The LED tradeoff

Each key has a red 0603 LED with a 1 kΩ resistor from 3V3. All 18 cathodes
share one AO3400A MOSFET switched by PWM on D6, with a 100 kΩ pull-down so the
LEDs stay dark while the MCU sleeps or boots. A MOSFET that is off draws
nothing, so the LEDs cost zero when they are off.

Rough numbers (estimated from part data, not measured):

| State | Current per half | CR2032 (≈220 mAh) lasts |
| --- | --- | --- |
| Asleep (ZMK deep sleep) | ~5 µA | years |
| Connected, typing, LEDs off | ~30–60 µA average | several months |
| LEDs on at 10 % (default when toggled) | +~1.5 mA | about 4–6 days of LEDs-on time |
| LEDs on at 100 % | +~15 mA | under a day, with heavy voltage sag |

So the firmware defaults are:

* LEDs **off at boot** (`CONFIG_ZMK_BACKLIGHT_ON_START=n`)
* **10 %** brightness when switched on (`CONFIG_ZMK_BACKLIGHT_BRT_START=10`)
* **off whenever the half goes idle** (`CONFIG_ZMK_BACKLIGHT_AUTO_OFF_IDLE=y`)
* toggle and dim on the ADJUST layer (hold LOWER + RAISE): `BL_TOG`, `BL_DEC`, `BL_INC`

If you want the LEDs on a lot, skip the coin cell: solder a small 3.7 V LiPo
straight to the RAW pad and GND (leave the coin cell holder empty). The XIAO
then charges it over USB.

## LED colour and voltage

Red was picked because its forward voltage (~1.8 V) still leaves headroom on a
2.4–2.6 V rail as the cell drains. Blue or white LEDs (~2.8–3 V) would not light
from a coin cell.

## Not yet verified on hardware

* Light through the PG1316S housing. The LED sits in the component pocket under
  the switch (the area marked on Dwgs.User in the PG1316S footprint). Whether
  enough light makes it through the switch to the keycap needs one test switch
  before ordering a full set of LEDs. If it does not, leave L1–L18 off the
  JLCPCB order; nothing else depends on them.
