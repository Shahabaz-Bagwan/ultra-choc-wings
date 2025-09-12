// Ergogen footprint for SOD-523 and 0603 LEDs with polarity mark and courtyard, reversible PCB
module.exports = {
  params: {
    designator: "D",
    from: undefined,
    to: undefined,
    variant: { type: "string", value: "0603" }, // '0603' or 'SOD523'
  },
  body: (p) => {
    const { designator, from, to, variant } = p;

    // Defaults per variant
    let pad_length, pad_width, pad_spacing, body_w, body_h;

    if (variant === "SOD523") {
      pad_length = 2.0;
      pad_width = 0.6;
      pad_spacing = 0.8;
      body_w = 2.2;
      body_h = 1.4;
    } else {
      // 0603 default
      pad_length = 1.0;
      pad_width = 0.5;
      pad_spacing = 0.5;
      body_w = 1.8;
      body_h = 0.9;
    }

    const x_offset = pad_spacing / 2 + pad_length / 2;
    const courtyard_margin = 0.25;

    return `
(module LED_${variant}_REV (layer F.Cu) (tedit 0)
  ${p.at}
  (fp_text reference ${designator} (at 0 -1.4) (layer F.SilkS))
  (fp_text value LED (at 0 1.4) (layer F.Fab))

  ${"" /*Pads (duplicated on front and back for reversible design)*/}
  (pad 1 smd rect (at ${-x_offset} 0) (size ${pad_length} ${pad_width}) (layers F.Cu F.Paste F.Mask B.Cu B.Paste B.Mask) ${p.from.str})
  (pad 2 smd rect (at ${x_offset} 0) (size ${pad_length} ${pad_width}) (layers F.Cu F.Paste F.Mask B.Cu B.Paste B.Mask) ${p.to.str})

  ${"" /* Silkscreen polarity mark (cathode line on pad 2 side)*/}
  (fp_line (start ${x_offset + pad_length / 2} -0.7) (end ${x_offset + pad_length / 2} 0.7)
    (layer F.SilkS) (width 0.12))
  (fp_line (start ${x_offset + pad_length / 2} -0.7) (end ${x_offset + pad_length / 2} 0.7)
    (layer B.SilkS) (width 0.12))

  ${"" /* Courtyard outline*/}
  (fp_line (start ${-body_w / 2 - courtyard_margin} ${-body_h / 2 - courtyard_margin}) (end ${body_w / 2 + courtyard_margin} ${-body_h / 2 - courtyard_margin}) (layer F.CrtYd) (width 0.05))
  (fp_line (start ${body_w / 2 + courtyard_margin} ${-body_h / 2 - courtyard_margin}) (end ${body_w / 2 + courtyard_margin} ${body_h / 2 + courtyard_margin}) (layer F.CrtYd) (width 0.05))
  (fp_line (start ${body_w / 2 + courtyard_margin} ${body_h / 2 + courtyard_margin}) (end ${-body_w / 2 - courtyard_margin} ${body_h / 2 + courtyard_margin}) (layer F.CrtYd) (width 0.05))
  (fp_line (start ${-body_w / 2 - courtyard_margin} ${body_h / 2 + courtyard_margin}) (end ${-body_w / 2 - courtyard_margin} ${-body_h / 2 - courtyard_margin}) (layer F.CrtYd) (width 0.05))

  (fp_line (start ${-body_w / 2 - courtyard_margin} ${-body_h / 2 - courtyard_margin}) (end ${body_w / 2 + courtyard_margin} ${-body_h / 2 - courtyard_margin}) (layer B.CrtYd) (width 0.05))
  (fp_line (start ${body_w / 2 + courtyard_margin} ${-body_h / 2 - courtyard_margin}) (end ${body_w / 2 + courtyard_margin} ${body_h / 2 + courtyard_margin}) (layer B.CrtYd) (width 0.05))
  (fp_line (start ${body_w / 2 + courtyard_margin} ${body_h / 2 + courtyard_margin}) (end ${-body_w / 2 - courtyard_margin} ${body_h / 2 + courtyard_margin}) (layer B.CrtYd) (width 0.05))
  (fp_line (start ${-body_w / 2 - courtyard_margin} ${body_h / 2 + courtyard_margin}) (end ${-body_w / 2 - courtyard_margin} ${-body_h / 2 - courtyard_margin}) (layer B.CrtYd) (width 0.05))
)
`;
  },
};
