/*
 * Reversible CR2032 SMD holder (MPD BC-2003 / Q&J CR2032-BS-6-1 land pattern).
 * Pad 1 = + (two side tabs), pad 2 = - (the round contact under the cell).
 * The pattern is symmetric, so it is the same on F and B.
 */
module.exports = {
  params: {
    designator: "BT",
    pos: undefined,
    neg: undefined,
  },
  body: (p) => {
    const side = (l) => `
      (fp_circle (center 0 0) (end 10.3 0) (layer ${l}.Fab) (width 0.1))
      (fp_circle (center 0 0) (end 13.6 0) (layer ${l}.CrtYd) (width 0.05))
      (fp_text user "+" (at -11.9 -4.5) (layer ${l}.SilkS) (effects (font (size 1.5 1.5) (thickness 0.2))${l === "B" ? " (justify mirror)" : ""}))
      (fp_text user "+" (at 11.9 -4.5) (layer ${l}.SilkS) (effects (font (size 1.5 1.5) (thickness 0.2))${l === "B" ? " (justify mirror)" : ""}))
      (pad 1 smd rect (at -11.905 0 ${p.rot}) (size 2.6 5.56) (layers ${l}.Cu ${l}.Paste ${l}.Mask) ${p.pos.str})
      (pad 1 smd rect (at 11.905 0 ${p.rot}) (size 2.6 5.56) (layers ${l}.Cu ${l}.Paste ${l}.Mask) ${p.pos.str})
      (pad 2 smd circle (at 0 0 ${p.rot}) (size 17.8 17.8) (layers ${l}.Cu ${l}.Mask) ${p.neg.str})`;
    return `
    (module "ucw:REV_CR2032_BC2003" (layer F.Cu) (tedit 0)
      ${p.at}
      (attr smd)
      (fp_text reference "${p.ref}" (at 0 7) (layer F.SilkS) hide (effects (font (size 1 1) (thickness 0.15))))
      (fp_text value "CR2032" (at 0 9) (layer F.Fab) hide (effects (font (size 1 1) (thickness 0.15))))
      ${side("F")}
      ${side("B")}
    )
    `;
  },
};
