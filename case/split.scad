// Ultra Choc Wings split / uniboard case.
//
// Two trays, one per half. On their own each is a complete case for one
// half. Pushed together along their straight inner edges they make one
// uniboard at a fixed splay, held rigid by a bridge plate that sits in a
// recess across the seam, flush with the top, with three M2 screws into each
// tray. The plate keeps the two trays from hinging at the seam, so the
// joined board stays flat even when one half is not fully supported (an
// uneven desk, a lap). Unscrew the plate to split it again.
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
part = "assembly"; // [assembly, left, right, bridge]

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
/* [Seam and bridge] */
seam_clr = 0.1;    // gap between the two trays at the seam
bridge_w = 40;     // bridge plate width across the seam (trimmed to the deck)
bridge_t = 2.4;    // bridge plate thickness = recess depth
bridge_clr = 0.2;  // recess clearance around the plate
bridge_margin = 1.6; // deck left between the recess and the PCB pockets
bridge_screw_x = 5; // seam to the bridge screws
bridge_screw_y = [0.2, 0.5, 0.8]; // screw positions along the seam, 0 = front, 1 = back
head_d = 4.2;      // counterbore for the bridge screw heads
head_depth = 1.0;
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

// Bridge plate outline: the deck between the halves, inset from the walls
// and the PCB pockets.
module bridge_shape()
    difference() {
        intersection() {
            offset(r = -wall) outer_shape();
            translate([-bridge_w / 2, y_lo]) square([bridge_w, y_hi - y_lo]);
        }
        offset(r = bridge_margin + bridge_clr) pockets();
    }

bridge_screws = [for (f = bridge_screw_y, sx = [-1, 1]) [sx * bridge_screw_x, y_lo + f * (y_hi - y_lo)]];

module left_tray() {
    difference() {
        intersection() {
            tray();
            translate([-500, -500, -1]) cube([500 - seam_clr / 2, 1000, h + 2]);
        }
        translate([0, 0, h - bridge_t]) linear_extrude(h) offset(delta = bridge_clr) bridge_shape();
        for (p = bridge_screws) translate([p[0], p[1], h - bridge_t - pilot_depth])
            cylinder(d = pilot_d, h = pilot_depth + 0.01);
    }
}

module bridge()
    difference() {
        linear_extrude(bridge_t) bridge_shape();
        for (p = bridge_screws) translate([p[0], p[1], -1]) {
            cylinder(d = 2.4, h = bridge_t + 2);
            translate([0, 0, bridge_t + 1 - head_depth]) cylinder(d = head_d, h = head_depth + 1);
        }
    }

if (part == "left") left_tray();
else if (part == "right") mirror([1, 0, 0]) left_tray();
else if (part == "bridge") bridge();
else {
    color("SteelBlue") left_tray();
    color("LightSteelBlue") mirror([1, 0, 0]) left_tray();
    color("Orange") translate([0, 0, h - bridge_t]) bridge();
}
