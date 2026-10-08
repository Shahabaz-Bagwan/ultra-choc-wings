/*
 * Plain M2 mounting hole (NPTH, 2.2 mm) for the uniboard case screws.
 * Symmetric, so it is the same whichever way up the PCB is used.
 */
module.exports = {
  params: {
    designator: "H",
  },
  body: (p) => `
    (module "ucw:M2_NPTH" (layer F.Cu) (tedit 0)
      ${p.at}
      (attr virtual)
      (fp_text reference "${p.ref}" (at 0 -2.6) (layer F.SilkS) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      (fp_text value "M2" (at 0 2.6) (layer F.Fab) hide (effects (font (size 0.8 0.8) (thickness 0.12))))
      (fp_circle (center 0 0) (end 2.1 0) (layer F.CrtYd) (width 0.05))
      (fp_circle (center 0 0) (end 2.1 0) (layer B.CrtYd) (width 0.05))
      (pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers *.Cu *.Mask))
    )
  `,
};
