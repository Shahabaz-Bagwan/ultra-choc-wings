/*
 * Ergogen footprint for CPG1316S01D02 reversible connector
 * Converted from KiCad footprint CPG1316S01D02_reversible_mikefives
 */
module.exports = {
  params: {
    designator: "SW",
    side: "F",
    from: undefined,
    to: undefined,
  },
  body: (p) => `
    (module "CPG1316S01D02_reversible" (layer ${p.side}.Cu) (tedit 20240108)
      ${p.at}

      (fp_text reference "${p.ref}" (at 0 0.5) (layer F.SilkS)
        (effects (font (size 1 1) (thickness 0.1))))

      (fp_text value "CPG1316S01D02_reversible" (at 0 9) (layer Cmts.User) hide
        (effects (font (size 1 1) (thickness 0.15))))

      (fp_line (start -8 -8) (end 8 -8) (layer F.SilkS) (width 0.1))
      (fp_line (start 8 -8) (end 8 8) (layer F.SilkS) (width 0.1))
      (fp_line (start 8 8) (end -8 8) (layer F.SilkS) (width 0.1))
      (fp_line (start -8 8) (end -8 -8) (layer F.SilkS) (width 0.1))

      (fp_line (start -8 -8) (end 8 -8) (layer B.SilkS) (width 0.1))
      (fp_line (start 8 -8) (end 8 8) (layer B.SilkS) (width 0.1))
      (fp_line (start 8 8) (end -8 8) (layer B.SilkS) (width 0.1))
      (fp_line (start -8 8) (end -8 -8) (layer B.SilkS) (width 0.1))

      (fp_line (start -6.75 -6.5) (end 6.75 -6.5) (layer F.Fab) (width 0.1))
      (fp_line (start 6.75 -6.5) (end 6.75 6.5) (layer F.Fab) (width 0.1))
      (fp_line (start 6.75 6.5) (end -6.75 6.5) (layer F.Fab) (width 0.1))
      (fp_line (start -6.75 6.5) (end -6.75 -6.5) (layer F.Fab) (width 0.1))

      (fp_line (start -6.75 -6.5) (end 6.75 -6.5) (layer B.Fab) (width 0.1))
      (fp_line (start 6.75 -6.5) (end 6.75 6.5) (layer B.Fab) (width 0.1))
      (fp_line (start 6.75 6.5) (end -6.75 6.5) (layer B.Fab) (width 0.1))
      (fp_line (start -6.75 6.5) (end -6.75 -6.5) (layer B.Fab) (width 0.1))

      (fp_circle (center -5.8 -2.75) (end -5.2 -2.75) (layer Edge.Cuts) (width 0.1))
      (fp_circle (center -5.8 2.75) (end -5.3 2.75) (layer Edge.Cuts) (width 0.1))
      (fp_circle (center 5.8 -2.75) (end 6.4 -2.75) (layer Edge.Cuts) (width 0.1))
      (fp_circle (center 5.8 2.75) (end 6.3 2.75) (layer Edge.Cuts) (width 0.1))

      (pad 1 smd roundrect (at -1.55 2.65 ${p.rot}) (size 3.25 2) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.125) ${p.from.str})
      (pad 1 smd roundrect (at -1.55 2.65 ${p.rot}) (size 2 2) (layers B.Cu B.Paste B.Mask) (roundrect_rratio 0.125) ${p.from.str})

      (pad 2 smd roundrect (at 1.55 2.65 ${p.rot}) (size 2 2) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.125) ${p.to.str})
      (pad 2 smd roundrect (at 1.55 2.65 ${p.rot}) (size 3.25 2) (layers B.Cu B.Paste B.Mask) (roundrect_rratio 0.125) ${p.to.str})

      (pad 3 smd roundrect (at -6.05 5.875 ${p.rot}) (size 1.4 1.75) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at -6.05 5.875 ${p.rot}) (size 1.4 1.75) (layers B.Cu B.Paste B.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at 6.05 5.875 ${p.rot}) (size 1.4 1.75) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at 6.05 5.875 ${p.rot}) (size 1.4 1.75) (layers B.Cu B.Paste B.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at -6.05 -5.875 ${p.rot}) (size 1.4 1.75) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at -6.05 -5.875 ${p.rot}) (size 1.4 1.75) (layers B.Cu B.Paste B.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at 6.05 -5.875 ${p.rot}) (size 1.4 1.75) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.1785714286))
      (pad 3 smd roundrect (at 6.05 -5.875 ${p.rot}) (size 1.4 1.75) (layers B.Cu B.Paste B.Mask) (roundrect_rratio 0.1785714286))
    )
  `,
};
