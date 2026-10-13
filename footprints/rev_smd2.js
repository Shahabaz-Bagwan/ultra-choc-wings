/*
 * Reversible two-terminal SMD footprint (resistor, capacitor, LED, diode).
 *
 * The copper on B is the mirror image of the copper on F: pad 1 sits at -x on
 * F and at +x on B. Seen from whichever side the part is soldered on, pad 1 is
 * always on the left, so one PCB works for both halves and a footprint can be
 * flipped in KiCad without changing any copper (that is how the bottom-side
 * JLCPCB placement file for the right half is produced, see jlcpcb/).
 *
 * For polarised parts (LED, diode) pad 1 is the cathode and gets a bar on the
 * silkscreen of both sides.
 */
const PACKAGES = {
  // [pad x, pad w, pad h, courtyard half w, courtyard half h, body half w, body half h]
  "0603": [0.825, 0.8, 0.95, 1.48, 0.73, 0.8, 0.4],
  LED0603: [0.7875, 0.875, 0.95, 1.48, 0.73, 0.8, 0.4],
  "0805": [0.95, 1.0, 1.45, 1.7, 0.98, 1.0, 0.625],
  SOD323: [1.05, 0.6, 0.45, 1.6, 0.7, 0.85, 0.65],
  SOD123: [1.65, 0.9, 1.2, 2.35, 1.15, 1.4, 0.9],
};

module.exports = {
  params: {
    designator: "R",
    package: { type: "string", value: "0603" },
    polarized: false,
    value: { type: "string", value: "" },
    pad1: undefined,
    pad2: undefined,
  },
  body: (p) => {
    const [px, pw, ph, cx, cy, bx, by] = PACKAGES[p.package];
    const side = (l, mirror) => {
      const s = mirror ? -1 : 1;
      const silk = [];
      if (p.polarized) {
        const x = s * -(px + pw / 2 + 0.25);
        silk.push(
          `(fp_line (start ${x} ${-ph / 2 - 0.1}) (end ${x} ${ph / 2 + 0.1}) (layer ${l}.SilkS) (width 0.15))`
        );
      }
      return `
      ${silk.join("\n")}
      (fp_line (start ${-cx} ${-cy}) (end ${cx} ${-cy}) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start ${cx} ${-cy}) (end ${cx} ${cy}) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start ${cx} ${cy}) (end ${-cx} ${cy}) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start ${-cx} ${cy}) (end ${-cx} ${-cy}) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start ${-bx} ${-by}) (end ${bx} ${-by}) (layer ${l}.Fab) (width 0.1))
      (fp_line (start ${bx} ${-by}) (end ${bx} ${by}) (layer ${l}.Fab) (width 0.1))
      (fp_line (start ${bx} ${by}) (end ${-bx} ${by}) (layer ${l}.Fab) (width 0.1))
      (fp_line (start ${-bx} ${by}) (end ${-bx} ${-by}) (layer ${l}.Fab) (width 0.1))
      (pad 1 smd roundrect (at ${s * -px} 0 ${p.rot}) (size ${pw} ${ph}) (layers ${l}.Cu ${l}.Paste ${l}.Mask) (roundrect_rratio 0.25) ${p.pad1.str})
      (pad 2 smd roundrect (at ${s * px} 0 ${p.rot}) (size ${pw} ${ph}) (layers ${l}.Cu ${l}.Paste ${l}.Mask) (roundrect_rratio 0.25) ${p.pad2.str})`;
    };
    return `
    (module "ucw:REV_${p.package}" (layer F.Cu) (tedit 0)
      ${p.at}
      (attr smd)
      (fp_text reference "${p.ref}" (at 0 ${-cy - 0.7}) (layer F.SilkS) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      (fp_text value "${p.value}" (at 0 ${cy + 0.7}) (layer F.Fab) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      ${side("F", false)}
      ${side("B", true)}
    )
    `;
  },
};
