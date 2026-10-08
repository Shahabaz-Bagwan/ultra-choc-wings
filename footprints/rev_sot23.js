/*
 * Reversible SOT-23 (e.g. AO3400A N-MOSFET: 1 = G, 2 = S, 3 = D).
 * B copper is the mirror image of F copper, same convention as rev_smd2.js.
 */
module.exports = {
  params: {
    designator: "Q",
    value: { type: "string", value: "" },
    pad1: undefined,
    pad2: undefined,
    pad3: undefined,
  },
  body: (p) => {
    const side = (l, s) => `
      (fp_line (start -1.7 -1.75) (end 1.7 -1.75) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start 1.7 -1.75) (end 1.7 1.75) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start 1.7 1.75) (end -1.7 1.75) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start -1.7 1.75) (end -1.7 -1.75) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start ${s * -0.7} -1.52) (end ${s * 0.7} -1.52) (layer ${l}.SilkS) (width 0.12))
      (fp_line (start ${s * -0.7} 1.52) (end ${s * 0.7} 1.52) (layer ${l}.SilkS) (width 0.12))
      (fp_circle (center ${s * -1.6} -1.6) (end ${s * -1.5} -1.6) (layer ${l}.SilkS) (width 0.2))
      (pad 1 smd roundrect (at ${s * -0.9375} -0.95 ${p.rot}) (size 1.475 0.6) (layers ${l}.Cu ${l}.Paste ${l}.Mask) (roundrect_rratio 0.25) ${p.pad1.str})
      (pad 2 smd roundrect (at ${s * -0.9375} 0.95 ${p.rot}) (size 1.475 0.6) (layers ${l}.Cu ${l}.Paste ${l}.Mask) (roundrect_rratio 0.25) ${p.pad2.str})
      (pad 3 smd roundrect (at ${s * 0.9375} 0 ${p.rot}) (size 1.475 0.6) (layers ${l}.Cu ${l}.Paste ${l}.Mask) (roundrect_rratio 0.25) ${p.pad3.str})`;
    return `
    (module "ucw:REV_SOT-23" (layer F.Cu) (tedit 0)
      ${p.at}
      (attr smd)
      (fp_text reference "${p.ref}" (at 0 -2.4) (layer F.SilkS) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      (fp_text value "${p.value}" (at 0 2.4) (layer F.Fab) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      ${side("F", 1)}
      ${side("B", -1)}
    )
    `;
  },
};
