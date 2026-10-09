// Ultra Choc Wings folding case, after the Aronia case
// (https://github.com/kumekay/aronia/tree/main/case).
//
// Each half is a thin frame that wraps the PCB, with a top deck level with
// the keycaps and one opening over the keys, and a flat bottom cover. Three
// M2 x 6 mm screws per half go up through the cover, a printed spacer and the
// PCB into bosses under the deck, so they clamp the whole stack. The two
// halves are joined along their straight inner edges by a double hinge: each
// half turns on its own 2 mm brass rod, and printed links tie the two rods
// together. Open, it is a uniboard at a fixed splay; folded, the halves close
// keys to keys like a book, with a gap sized for the XIAO and the CR2032
// holder that stand above the deck.
//
// Export one part at a time, e.g.
//   openscad -D 'part="left_frame"' -o fold_left_frame.stl fold.scad

include <common.scad>

/* [Part] */
part = "assembly"; // [assembly, folded, left_frame, right_frame, left_cover, right_cover, link]

/* [Layout] */
splay = 10;        // degrees each half is rotated away from the hinge line
/* [Stack-up] */
cover_t = 1.4;     // bottom cover
under_gap = 1.0;   // space under the PCB for switch pegs and solder
pcb_t = 1.6;
key_h = 3.2;       // deck top above the PCB top; about the PG1316S height, so caps sit flush
deck_t = 1.2;      // deck thickness
wall = 2.0;        // side wall thickness
clearance = 0.4;   // gap between PCB edge and frame
/* [Keys] */
key_w = 17;        // opening per keycap, across
key_d = 16;        // opening per keycap, front to back
key_merge = 1.6;   // merge openings closer than 2 * key_merge into one
/* [Parts above the deck] */
xiao_h = 3.6;      // XIAO height above the PCB
coin_h = 4.6;      // CR2032 holder height above the PCB
coin_window = 13.8; // radius of the opening over the CR2032 holder
notch_depth = 10;  // how far the USB-C / switch notch reaches into the wall
/* [Hinge] */
axle_d = 2.0;      // brass rod
axle_clr = 0.2;
links = 2;
link_t = 3;        // link thickness
slot_clr = 0.4;    // clearance around the links
/* [Screws] */
pilot_d = 1.7;     // M2 self-tapping pilot in the deck bosses
boss_d = 4.6;
screw_d = 2.4;     // clearance hole in the cover
head_d = 4.2;      // counterbore for the screw head
head_depth = 0.6;
$fn = 48;

H = cover_t + under_gap + pcb_t + key_h;  // overall thickness of one half
z_pcb = cover_t + under_gap;
z_top = z_pcb + pcb_t;
// Folded, the two decks face each other; leave room for what stands above them.
fold_gap = max(0, 2 * (max(xiao_h, coin_h) - key_h)) + 0.6;
s = (H + fold_gap) / 2;          // the left axle runs along x = -s, z = H / 2
r_link = H / 2 - 0.4;
hinge_band = r_link + slot_clr;  // depth of the link slots behind the axle
inner = s + hinge_band + wall + clearance;  // seam to the PCB
y_lo = min(board_ys(splay)) - wall - clearance;
y_hi = max(board_ys(splay)) + wall + clearance;
link_ys = [for (i = [0 : links - 1])
    y_lo + (y_hi - y_lo) * (links == 1 ? 0.5 : 0.15 + 0.7 * i / (links - 1))];

module left() place_left(splay, inner) children();

// Outline of the opened keyboard, cut at the left half's hinge edge.
module half_outline()
    intersection() {
        offset(r = wall + clearance) hull() { left() board_shape(); place_right(splay, inner) board_shape(); }
        translate([-1000, -1000]) square([1000 - s + H / 2, 2000]);
    }

// Inside of the frame below the PCB, kept clear of the hinge.
module cover_shape()
    offset(r = -wall) intersection() {
        half_outline();
        translate([-1000, -1000]) square([1000 - s - hinge_band, 2000]);
    }

module along_y(len = 1000) rotate([90, 0, 0]) cylinder(h = len, center = true, r = 1);

module left_frame() {
    difference() {
        union() {
            difference() {
                linear_extrude(H) half_outline();
                // Round the hinge edge into a half cylinder around the axle.
                translate([-s, 0, H / 2]) difference() {
                    translate([0, -1000, -H]) cube([H, 2000, 2 * H]);
                    scale([H / 2, 1, H / 2]) along_y();
                }
                // Room for the cover, the space under the PCB, and the PCB.
                translate([0, 0, -1]) linear_extrude(cover_t + 1) cover_shape();
                translate([0, 0, cover_t - 0.01]) linear_extrude(H - deck_t - cover_t + 0.01)
                    left() offset(delta = clearance) board_shape();
            }
            // Screw bosses from the PCB up to the deck.
            left() for (p = holes) translate([p[0], p[1], z_top]) cylinder(d = boss_d, h = H - z_top - deck_t + 0.01);
        }
        // Deck openings: keys, XIAO, CR2032, and the top-edge notch.
        translate([0, 0, z_top + 0.2]) linear_extrude(H) left() {
            key_openings(key_w, key_d, key_merge);
            xiao_shape();
            translate(coin) circle(r = coin_window);
        }
        translate([0, 0, z_top]) linear_extrude(H) left() top_notch(notch_depth);
        // Axle and link slots.
        translate([-s, 0, H / 2]) scale([(axle_d + axle_clr) / 2, 1, (axle_d + axle_clr) / 2]) along_y();
        for (y = link_ys) translate([-s - hinge_band, y - link_t / 2 - slot_clr, -1])
            cube([H + 1, link_t + 2 * slot_clr, H + 2]);
        // M2 pilots, stopping 0.6 mm under the deck top.
        left() for (p = holes) translate([p[0], p[1], z_top - 0.01]) cylinder(d = pilot_d, h = H - z_top - 0.6);
    }
}

module left_cover() {
    difference() {
        union() {
            linear_extrude(cover_t) offset(delta = -0.2) cover_shape();
            // Spacers that hold the PCB off the cover, trimmed to the PCB pocket.
            intersection() {
                left() for (p = holes) translate([p[0], p[1], cover_t - 0.01]) cylinder(d = boss_d, h = under_gap + 0.01);
                linear_extrude(H) left() board_shape();
            }
        }
        left() for (p = holes) translate([p[0], p[1], 0]) {
            translate([0, 0, -1]) cylinder(d = screw_d, h = H);
            translate([0, 0, -1]) cylinder(d = head_d, h = head_depth + 1);
        }
    }
}

module link()
    difference() {
        hull() for (x = [0, 2 * s]) translate([x, 0]) circle(r = r_link);
        for (x = [0, 2 * s]) translate([x, 0]) circle(d = axle_d + axle_clr);
    }

module left_half() { color("DimGray") left_frame(); color("Gray") left_cover(); }
module links_in_place()
    color("Orange") for (y = link_ys) translate([-s, y + link_t / 2, H / 2]) rotate([90, 0, 0]) linear_extrude(link_t) link();

if (part == "left_frame") left_frame();
else if (part == "right_frame") mirror([1, 0, 0]) left_frame();
else if (part == "left_cover") left_cover();
else if (part == "right_cover") mirror([1, 0, 0]) left_cover();
else if (part == "link") linear_extrude(link_t) link();
else if (part == "folded") {
    // Links stay put; each half turns 90 degrees about its own axle.
    links_in_place();
    translate([-s, 0, H / 2]) rotate([0, 90, 0]) translate([s, 0, -H / 2]) left_half();
    mirror([1, 0, 0]) translate([-s, 0, H / 2]) rotate([0, 90, 0]) translate([s, 0, -H / 2]) left_half();
} else {
    left_half();
    mirror([1, 0, 0]) left_half();
    links_in_place();
}
