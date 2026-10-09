// Ultra Choc Wings split / uniboard case.
//
// Two trays, one per half. On their own each is a complete case for one
// half. Pushed together along their straight inner edges they make one
// uniboard at a fixed splay, held rigid by two bridge plates. No screws or
// tools: each plate is a tapered dovetail that slides into a matching groove
// along the seam, one from the back edge and one from the front, and wedges
// tight, flush with the top. Their undercut sides grip both trays, so they
// can't pull apart, lift, or hinge at the seam, and the joined board stays
// flat even when one half is not fully supported (an uneven desk, a lap).
// Pull the plates out by their tabs to split the board again.
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
part = "assembly"; // [assembly, left, right, bridge_back, bridge_front]

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
// Two plates: [edge it enters from (1 = back, -1 = front), length,
// width at that edge, width at its inner end].
bridges = [[1, 70, 22, 12], [-1, 26, 16, 10]];
bridge_t = 2.4;    // plate thickness = groove depth
dovetail = 0.8;    // undercut of each side, bottom vs. top of the plate
bridge_clr = 0.1;  // groove clearance; the taper takes up the rest
tab = 4;           // grip tab sticking out of the case edge
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

// Plate plan at its top face, tapering inward from the edge it enters by.
// `extra` carries the taper on past the edge for the open end of the groove.
module bridge_plan(b, grow = 0, extra = 0) {
    side = b[0]; L = b[1]; edge = side > 0 ? y_hi : y_lo;
    function hw(d) = b[3] / 2 + (b[2] - b[3]) / 2 * d / L; // d: distance from the inner end
    y_in = edge - side * L;
    y_out = edge + side * (tab + extra);
    offset(delta = grow) polygon([[-hw(0), y_in], [hw(0), y_in], [hw(L + tab + extra), y_out], [-hw(L + tab + extra), y_out]]);
}

// Dovetail solid: the bottom face is wider than the top by `dovetail` a side.
module bridge_solid(b, grow = 0, extra = 0)
    hull() {
        linear_extrude(0.01) bridge_plan(b, grow + dovetail, extra);
        translate([0, 0, bridge_t - 0.01]) linear_extrude(0.01) bridge_plan(b, grow, extra);
    }

module left_tray() {
    difference() {
        intersection() {
            tray();
            translate([-500, -500, -1]) cube([500 - seam_clr / 2, 1000, h + 2]);
        }
        // Groove, open at the back edge; taller than the plate so its top
        // stays clear.
        for (b = bridges) {
            translate([0, 0, h - bridge_t]) bridge_solid(b, bridge_clr, 5);
            translate([0, 0, h - 0.01]) linear_extrude(1) bridge_plan(b, bridge_clr, 5);
        }
    }
}

module bridges_in_place() for (b = bridges) bridge_solid(b);

if (part == "left") left_tray();
else if (part == "right") mirror([1, 0, 0]) left_tray();
else if (part == "bridge_back") bridge_solid(bridges[0]);
else if (part == "bridge_front") bridge_solid(bridges[1]);
else {
    color("SteelBlue") left_tray();
    color("LightSteelBlue") mirror([1, 0, 0]) left_tray();
    color("Orange") translate([0, 0, h - bridge_t]) bridges_in_place();
}
