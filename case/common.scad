// Shared helpers for fold.scad and split.scad.
include <board.scad>

function rot(p, a) = [p[0] * cos(a) - p[1] * sin(a), p[0] * sin(a) + p[1] * cos(a)];

// x of the innermost (thumb side) board point once the half is splayed.
function inner_x(splay) = max([for (p = board) rot(p, -splay)[0]]);
function board_ys(splay) = [for (p = board) rot(p, -splay)[1]];

// Put the left half at its splay with its innermost point at x = -inner.
// The right half is the mirror image (the same PCB, flipped over).
module place_left(splay, inner) translate([-inner - inner_x(splay), 0]) rotate(-splay) children();
module place_right(splay, inner) mirror([1, 0, 0]) place_left(splay, inner) children();

module board_shape() polygon(board);

// One opening per keycap, merged where the ribs between them would be
// thinner than 2 * merge.
module key_openings(w, h, merge)
    offset(r = -merge) offset(delta = merge)
        for (k = keys) translate([k[0], k[1]]) rotate(k[2]) square([w, h], center = true);

module xiao_shape(grow = 1)
    offset(delta = grow) translate([xiao_box[0], xiao_box[1]])
        square([xiao_box[2] - xiao_box[0], xiao_box[3] - xiao_box[1]]);

// XIAO USB-C and the slide switch both stick out of the top edge; one notch
// in the wall clears both.
module top_notch(depth)
    translate([xiao_box[0] - 1, board_top - 2])
        square([power_switch[0] + 5 - (xiao_box[0] - 1), depth + 2]);
