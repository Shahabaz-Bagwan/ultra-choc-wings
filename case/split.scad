// Ultra Choc Wings split / uniboard case.
//
// Two trays, one per half. On their own each is a complete case for one
// half. Joined, they make one uniboard at a fixed splay, held by a single
// printed clip that slides on from the back edge, no screws or tools. The
// clip is an I-beam: a wide base plate under both trays (about half of each
// half's underside), a thin web up through the seam, and a small wedge-shaped
// bridge on top that sits flush in a groove along the seam. The base carries
// both halves from below and the bridge holds them down from the top, so the
// joined board is one rigid piece that doesn't hinge at the seam and doesn't
// need a flat surface under it. A lip at the back of the base stops the clip
// in place and two small bumps click into dimples under the trays. Slide the
// clip off backwards to split the board again.
//
// Each half drops into its pocket and sits flat on the floor (every SMD part
// is on the switch side, so the bottom is bare), held by three M2 screws that
// self-tap into the floor. The CR2032 is reachable from the top; the top-edge
// notch clears the XIAO USB-C and the power switch.
//
// Export one part at a time, e.g.
//   openscad -D 'part="left"' -o split_left.stl split.scad

include <common.scad>

/* [Part] */
part = "assembly"; // [assembly, left, right, clip]

/* [Layout] */
splay = 12;        // degrees each half is rotated away from straight
gap = 18;          // mm between the two PCBs at their closest point
/* [Walls] */
wall = 2.4;        // side wall thickness
floor_t = 3;       // floor under the PCB
clearance = 0.4;   // gap between PCB edge and pocket wall
pcb_t = 1.6;
lip = 1.0;         // wall height above the PCB top surface
/* [Screws] */
pilot_d = 1.7;     // M2 self-tapping pilot (use 3.2 for M2 heat-set inserts)
pilot_depth = 2.6;
/* [Details] */
xiao_relief_depth = 2;
notch_depth = 10;  // how far the top-edge notch reaches into the wall
/* [Clip] */
clip_web = 2.0;    // web thickness = gap between the trays at the seam
clip_wedge = 3.0;  // height of the 45-degree bridge on top; it is this much wider than the web a side
clip_base_t = 2.0; // base plate thickness
clip_base_w = 120; // base plate width across the seam (about half of each tray)
clip_inset = 2;    // base plate inset from the case outline
clip_stop = 3.5;   // back lip height above the base
clip_clr = 0.15;   // clearance around the web and bridge
bump_d = 1.2;      // detent bumps on the base, dimples under the trays
bump_x = 25;       // seam to each bump
bump_f = 0.4;      // bump position along the seam, 0 = front, 1 = back
$fn = 48;

h = floor_t + pcb_t + lip;
y_lo = min(board_ys(splay)) - wall - clearance;
y_hi = max(board_ys(splay)) + wall + clearance;

module both() { place_left(splay, gap / 2) children(); place_right(splay, gap / 2) children(); }

module outer_shape() offset(r = wall + clearance) hull() both() board_shape();

module pockets() both() offset(delta = clearance) board_shape();

module tray() {
    difference() {
        linear_extrude(h) outer_shape();
        // PCB pockets
        translate([0, 0, floor_t]) linear_extrude(h) pockets();
        // XIAO pin relief
        translate([0, 0, floor_t - xiao_relief_depth]) linear_extrude(h)
            both() xiao_shape();
        // USB-C / power switch notch in the top wall
        translate([0, 0, floor_t]) linear_extrude(h) both() top_notch(notch_depth);
        // M2 pilot holes
        both() for (p = holes) translate([p[0], p[1], floor_t - pilot_depth])
            linear_extrude(pilot_depth + 0.01) circle(d = pilot_d);
    }
}

bumps = [for (sx = [-1, 1]) [sx * bump_x, y_lo + bump_f * (y_hi - y_lo)]];

// Web and bridge cross-section in the x-z plane, centred on the seam.
module clip_profile(grow = 0)
    offset(delta = grow) polygon([
        [-clip_web / 2, -1], [clip_web / 2, -1], [clip_web / 2, h - clip_wedge],
        [clip_web / 2 + clip_wedge, h], [-clip_web / 2 - clip_wedge, h], [-clip_web / 2, h - clip_wedge]]);

// That profile run along the whole seam, front to back (y up to `y1`).
module along_seam(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

module clip() {
    // Web and bridge, trimmed to the case outline.
    intersection() {
        along_seam(y_lo - 1, y_hi) clip_profile();
        translate([0, 0, -0.01]) linear_extrude(h + 0.01) outer_shape();
    }
    translate([0, 0, -clip_base_t]) {
        linear_extrude(clip_base_t) intersection() {
            offset(r = -clip_inset) outer_shape();
            translate([-clip_base_w / 2, y_lo]) square([clip_base_w, y_hi - y_lo]);
        }
        // Back lip: butts against the back edge of both trays.
        translate([-clip_base_w / 2, y_hi + clip_clr, 0]) cube([clip_base_w, 2, clip_base_t + clip_stop]);
        translate([-clip_base_w / 2, y_hi - clip_inset - 1, 0]) cube([clip_base_w, clip_inset + 1 + clip_clr + 0.01, clip_base_t]);
    }
    for (p = bumps) translate([p[0], p[1], 0]) sphere(d = bump_d, $fn = 16);
}

module left_tray() {
    difference() {
        intersection() {
            tray();
            translate([-500, -500, -1]) cube([500 - clip_web / 2 - clip_clr, 1000, h + 2]);
        }
        // Groove for the bridge, open at both ends.
        along_seam(y_lo - 5, y_hi + 5) clip_profile(clip_clr);
        translate([0, 0, h - 0.01]) along_seam(y_lo - 5, y_hi + 5)
            translate([-clip_web / 2 - clip_wedge - clip_clr, 0]) square([clip_web + 2 * (clip_wedge + clip_clr), 1]);
        for (p = bumps) translate([p[0], p[1], 0]) sphere(d = bump_d + 2 * clip_clr, $fn = 16);
    }
}

if (part == "left") left_tray();
else if (part == "right") mirror([1, 0, 0]) left_tray();
else if (part == "clip") translate([0, 0, clip_base_t]) clip();
else {
    color("SteelBlue") left_tray();
    color("LightSteelBlue") mirror([1, 0, 0]) left_tray();
    color("Orange") clip();
}
