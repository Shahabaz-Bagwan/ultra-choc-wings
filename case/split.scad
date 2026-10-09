// Ultra Choc Wings split / uniboard case.
//
// Two trays, one per half. On their own each is a complete case for one
// half. Pushed together along their straight inner edges they make one
// uniboard at a fixed splay, held by two printed dog-bone keys that slide
// into channels in the seam from the front and back edges. Slide the keys
// out to split it again.
//
// Each half drops into its pocket and sits flat on the floor (every SMD part
// is on the switch side, so the bottom is bare), held by three M2 screws that
// self-tap into the floor. The CR2032 is reachable from the top; the top-edge
// notch clears the XIAO USB-C and the power switch. The deck between the
// halves is a shallow tray (the dongle fits there for travel).
//
// Export one part at a time, e.g.
//   openscad -D 'part="left"' -o split_left.stl split.scad

include <common.scad>

/* [Part] */
part = "assembly"; // [assembly, left, right, key]

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
center_tray = true; // hollow the deck between the halves
/* [Seam and keys] */
seam_clr = 0.1;    // gap between the two trays at the seam
spine = 12;        // solid band along the seam that holds the key channels
key_len = 18;      // length of each dog-bone key
key_d = 3.2;       // dog-bone end diameter
key_neck = 1.8;    // dog-bone neck thickness
key_offset = 2.6;  // seam to dog-bone end centre
key_clr = 0.15;    // channel clearance around the key
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
        // Deck between the halves, minus the spine along the seam
        if (center_tray)
            translate([0, 0, floor_t]) linear_extrude(h)
                // offset in, then out: drops slivers too thin to be useful
                offset(r = 3) offset(delta = -3) difference() {
                    offset(r = -wall) outer_shape();
                    offset(r = wall + clearance) both() board_shape();
                    translate([-spine / 2, y_lo - 1]) square([spine, y_hi - y_lo + 2]);
                }
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

// Dog-bone profile in the x-z plane, centred on the seam.
module key_profile(grow) {
    for (sx = [-1, 1]) translate([sx * key_offset, 0]) circle(d = key_d + 2 * grow);
    translate([-key_offset, -key_neck / 2 - grow]) square([2 * key_offset, key_neck + 2 * grow]);
}

// The two channels, entering from the front and back edges.
module key_channels() {
    len = key_len + 0.5;
    for (end = [[y_hi + 1, -1], [y_lo - 1, 1]])
        translate([0, end[0], h / 2]) rotate([-90 * end[1], 0, 0])
            linear_extrude(len + 1) key_profile(key_clr);
}

module left_tray() {
    difference() {
        intersection() {
            tray();
            translate([-500, -500, -1]) cube([500 - seam_clr / 2, 1000, h + 2]);
        }
        key_channels();
    }
}

module key() linear_extrude(key_len) key_profile(0);

if (part == "left") left_tray();
else if (part == "right") mirror([1, 0, 0]) left_tray();
else if (part == "key") key();
else {
    color("SteelBlue") left_tray();
    color("LightSteelBlue") mirror([1, 0, 0]) left_tray();
    color("Orange") for (end = [[y_hi, -1], [y_lo, 1]])
        translate([0, end[0], h / 2]) rotate([-90 * end[1], 0, 0]) key();
}
