/*
 * Reversible SPDT slide switch (LCSC C128955 footprint, same geometry as
 * Ergogen's built-in `slider`), with mirrored copper on B so both sides are
 * one footprint. Pad 2 is the common pin.
 */
module.exports = {
  params: {
    designator: "T",
    from: undefined,
    to: undefined,
  },
  body: (p) => {
    const side = (l, s) => `
      (fp_line (start -3.3 -1.35) (end 3.3 -1.35) (layer ${l}.SilkS) (width 0.15))
      (fp_line (start -3.3 -1.35) (end -3.3 1.5) (layer ${l}.SilkS) (width 0.15))
      (fp_line (start -3.3 1.5) (end 3.3 1.5) (layer ${l}.SilkS) (width 0.15))
      (fp_line (start 3.3 1.5) (end 3.3 -1.35) (layer ${l}.SilkS) (width 0.15))
      (fp_line (start -1.95 -3.85) (end 1.95 -3.85) (layer ${l}.Fab) (width 0.1))
      (fp_line (start 1.95 -3.85) (end 1.95 -1.35) (layer ${l}.Fab) (width 0.1))
      (fp_line (start -1.95 -1.35) (end -1.95 -3.85) (layer ${l}.Fab) (width 0.1))
      (fp_line (start -4.4 -4.1) (end 4.4 -4.1) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start 4.4 -4.1) (end 4.4 3) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start 4.4 3) (end -4.4 3) (layer ${l}.CrtYd) (width 0.05))
      (fp_line (start -4.4 3) (end -4.4 -4.1) (layer ${l}.CrtYd) (width 0.05))
      (pad 1 smd rect (at ${s * 2.25} 2.075 ${p.rot}) (size 0.9 1.25) (layers ${l}.Cu ${l}.Paste ${l}.Mask) ${p.from.str})
      (pad 2 smd rect (at ${s * -0.75} 2.075 ${p.rot}) (size 0.9 1.25) (layers ${l}.Cu ${l}.Paste ${l}.Mask) ${p.to.str})
      (pad 3 smd rect (at ${s * -2.25} 2.075 ${p.rot}) (size 0.9 1.25) (layers ${l}.Cu ${l}.Paste ${l}.Mask))
      (pad "" smd rect (at 3.7 -1.1 ${p.rot}) (size 0.9 0.9) (layers ${l}.Cu ${l}.Paste ${l}.Mask))
      (pad "" smd rect (at 3.7 1.1 ${p.rot}) (size 0.9 0.9) (layers ${l}.Cu ${l}.Paste ${l}.Mask))
      (pad "" smd rect (at -3.7 1.1 ${p.rot}) (size 0.9 0.9) (layers ${l}.Cu ${l}.Paste ${l}.Mask))
      (pad "" smd rect (at -3.7 -1.1 ${p.rot}) (size 0.9 0.9) (layers ${l}.Cu ${l}.Paste ${l}.Mask))`;
    return `
    (module "ucw:REV_SPDT_C128955" (layer F.Cu) (tedit 0)
      ${p.at}
      (attr smd)
      (fp_text reference "${p.ref}" (at 0 0) (layer F.SilkS) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      (fp_text value "" (at 0 0) (layer F.Fab) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      (pad "" np_thru_hole circle (at 1.5 0) (size 0.9 0.9) (drill 0.9) (layers *.Cu *.Mask))
      (pad "" np_thru_hole circle (at -1.5 0) (size 0.9 0.9) (drill 0.9) (layers *.Cu *.Mask))
      ${side("F", 1)}
      ${side("B", -1)}
    )
    `;
  },
};
