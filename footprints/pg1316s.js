/*
 * Ergogen footprint for Kailh PG1316S low-profile switch
 * Cleaned to be valid KiCad 6/7 syntax (no bad comments).
 */

module.exports = {
  params: {
    designator: "SW",
    side: "F",
    from: undefined,
    to: undefined,
  },
  body: (p) => `
    (module "PG1316S" (layer ${p.side}.Cu) (tedit 5B30729B)

      ${p.at}

      (fp_text reference "${p.ref}" (at 0 -10) (layer ${p.side}.SilkS)
        (effects (font (size 1 1) (thickness 0.15))))
      (fp_text value "PG1316S" (at 0 10) (layer ${p.side}.Fab)
        (effects (font (size 1 1) (thickness 0.15))))

      (fp_line (start -8 -8) (end 8 -8) (layer ${p.side}.SilkS) (width 0.12))
      (fp_line (start 8 -8) (end 8 8) (layer ${p.side}.SilkS) (width 0.12))
      (fp_line (start 8 8) (end -8 8) (layer ${p.side}.SilkS) (width 0.12))
      (fp_line (start -8 8) (end -8 -8) (layer ${p.side}.SilkS) (width 0.12))

      (fp_line (start -7 -7) (end 7 -7) (layer ${p.side}.SilkS) (width 0.08))
      (fp_line (start 7 -7) (end 7 7) (layer ${p.side}.SilkS) (width 0.08))
      (fp_line (start 7 7) (end -7 7) (layer ${p.side}.SilkS) (width 0.08))
      (fp_line (start -7 7) (end -7 -7) (layer ${p.side}.SilkS) (width 0.08))

      (pad "" np_thru_hole circle (at -5 5 ${p.rot}) (size 1 1) (drill 1) (layers *.Cu *.Mask))
      (pad "" np_thru_hole circle (at 5 5 ${p.rot}) (size 1 1) (drill 1) (layers *.Cu *.Mask))

      (pad 1 smd rect (at -3 0 ${p.rot}) (size 1.5 1) (layers F.Cu F.Paste F.Mask) ${p.from.str})
      (pad 2 smd rect (at 3 0 ${p.rot}) (size 1.5 1) (layers F.Cu F.Paste F.Mask) ${p.to.str})

      (pad 3 smd rect (at -7 -7 ${p.rot}) (size 2 1) (layers F.Cu F.Paste F.Mask))
      (pad 3 smd rect (at 7 -7 ${p.rot}) (size 2 1) (layers F.Cu F.Paste F.Mask))
      (pad 3 smd rect (at 7 7 ${p.rot}) (size 2 1) (layers F.Cu F.Paste F.Mask))
      (pad 3 smd rect (at -7 7 ${p.rot}) (size 2 1) (layers F.Cu F.Paste F.Mask))
    )
  `,
};
