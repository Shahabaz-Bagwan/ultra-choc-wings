#!/usr/bin/env python3
"""Close the few connections Freerouting reports as done but KiCad sees open.

Freerouting reads some custom-shaped pads (the flippable XIAO footprint) and a
few rotated parts differently from KiCad, so after importing its session a
handful of nets can still be split into islands. This finds those islands
with KiCad's own geometry and joins each one to the rest of its net with the
shortest clean path: a straight track on one layer, or two tracks and a via.

    python3 scripts/finish_routes.py pcb/ultra-choc-wings.kicad_pcb
"""
import itertools
import sys

import pcbnew

MM = pcbnew.FromMM
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
CLEARANCE = MM(0.2)
TRACK = MM(0.25)
VIA_D, VIA_DRILL = MM(0.6), MM(0.3)
HOLE_CLEARANCE = MM(0.25)
EDGE = MM(0.4)
# Grid paths step diagonally between cell centres; keep a little extra room.
SLACK = MM(0.03)


def islands(board, code):
    items = [p for p in board.GetPads() if p.GetNetCode() == code]
    items += [t for t in board.GetTracks() if t.GetNetCode() == code]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    boxes = [it.GetBoundingBox() for it in items]
    for i, j in itertools.combinations(range(len(items)), 2):
        if not boxes[i].Intersects(boxes[j]):
            continue
        for layer in LAYERS:
            if items[i].IsOnLayer(layer) and items[j].IsOnLayer(layer) and \
                    items[i].GetEffectiveShape(layer).Collide(items[j].GetEffectiveShape(layer), 0):
                parent[find(i)] = find(j)
                break
    groups = {}
    for i, item in enumerate(items):
        groups.setdefault(find(i), []).append(item)
    return sorted(groups.values(), key=len, reverse=True)


def anchors(group):
    """(point, layer) pairs a new track may start from."""
    out = []
    for item in group:
        for layer in LAYERS:
            if not item.IsOnLayer(layer):
                continue
            if item.Type() == pcbnew.PCB_TRACE_T:
                out += [(item.GetStart(), layer), (item.GetEnd(), layer)]
            else:
                out.append((item.GetPosition(), layer))
    return out


class Obstacles:
    def __init__(self, board, code):
        self.shapes = {layer: [] for layer in LAYERS}
        self.holes = []
        for pad in board.GetPads():
            for layer in LAYERS:
                if pad.IsOnLayer(layer) and pad.GetNetCode() != code:
                    self.shapes[layer].append(pad.GetEffectiveShape(layer))
            if pad.HasHole():
                self.holes.append(pad.GetEffectiveHoleShape())
        for t in board.GetTracks():
            if t.GetNetCode() == code:
                continue
            for layer in LAYERS:
                if t.IsOnLayer(layer):
                    self.shapes[layer].append(t.GetEffectiveShape(layer))
            if t.Type() == pcbnew.PCB_VIA_T:
                self.holes.append(t.GetEffectiveHoleShape())
        outline = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(outline)
        self.outline = outline
        chain = outline.Outline(0)
        self.edges = [chain.CSegment(i) for i in range(chain.SegmentCount())]

    def near_edge(self, seg, dist):
        return any(e.Distance(seg) < dist for e in self.edges)

    def segment_ok(self, a, b, layer):
        seg = pcbnew.SHAPE_SEGMENT(a, b, TRACK)
        for p in (a, b):
            if not self.outline.Contains(p):
                return False
        if self.near_edge(pcbnew.SEG(a, b), TRACK // 2 + EDGE):
            return False
        return not any(s.Collide(seg, CLEARANCE) for s in self.shapes[layer]) and \
            not any(h.Collide(seg, HOLE_CLEARANCE) for h in self.holes)

    def via_ok(self, p):
        circle = pcbnew.SHAPE_CIRCLE(p, VIA_D // 2)
        if not self.outline.Contains(p) or self.near_edge(pcbnew.SEG(p, p), VIA_D // 2 + EDGE):
            return False
        return not any(s.Collide(circle, CLEARANCE) for layer in LAYERS for s in self.shapes[layer]) and \
            not any(h.Collide(circle, HOLE_CLEARANCE) for h in self.holes)


def length(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def best_path(obs, src, dst):
    """Shortest straight track, or two tracks joined by one via."""
    best = None
    for (a, la), (b, lb) in itertools.product(src, dst):
        if la == lb and obs.segment_ok(a, b, la):
            cost = length(a, b)
            if best is None or cost < best[0]:
                best = (cost, [(a, b, la)], [])
    if best:
        return best
    pairs = [(x, y) for x, y in itertools.product(src, dst) if x[1] != y[1]]
    pairs = sorted(pairs, key=lambda ab: length(ab[0][0], ab[1][0]))[:12]
    step = MM(0.25)
    for (a, la), (b, lb) in pairs:
        if length(a, b) > MM(15):
            break
        x0, x1 = sorted((a.x, b.x))
        y0, y1 = sorted((a.y, b.y))
        for x in range(x0 - MM(2), x1 + MM(2), step):
            for y in range(y0 - MM(2), y1 + MM(2), step):
                v = pcbnew.VECTOR2I(x, y)
                cost = length(a, v) + length(v, b) + MM(1)
                if best and cost >= best[0]:
                    continue
                if obs.via_ok(v) and obs.segment_ok(a, v, la) and obs.segment_ok(v, b, lb):
                    best = (cost, [(a, v, la), (v, b, lb)], [v])
        if best:
            return best
    return best


def maze_route(obs, src, dst, grid=MM(0.2), margin=MM(5), via_cost=40):
    """A* on a two-layer raster of the board from any src anchor to any dst anchor.

    Obstacles are rasterised once: a cell is blocked for a track (or a via)
    when a track (or via) centred there would break clearance to another net.
    """
    import heapq

    pts = [p for p, _ in src + dst]
    x0 = min(min(p.x for p in pts), obs.outline.BBox().GetX()) - margin
    y0 = min(min(p.y for p in pts), obs.outline.BBox().GetY()) - margin
    x1 = max(max(p.x for p in pts), obs.outline.BBox().GetRight()) + margin
    y1 = max(max(p.y for p in pts), obs.outline.BBox().GetBottom()) + margin
    nx, ny = (x1 - x0) // grid + 1, (y1 - y0) // grid + 1
    li = {LAYERS[0]: 0, LAYERS[1]: 1}

    def pos(i, j):
        return pcbnew.VECTOR2I(x0 + i * grid, y0 + j * grid)

    def cell(p):
        return round((p.x - x0) / grid), round((p.y - y0) / grid)

    def mark(grid_, shape, radius, dist):
        box = shape.BBox()
        pad = radius + dist + grid
        i0, j0 = cell(pcbnew.VECTOR2I(box.GetX() - pad, box.GetY() - pad))
        i1, j1 = cell(pcbnew.VECTOR2I(box.GetRight() + pad, box.GetBottom() + pad))
        for i in range(max(i0, 0), min(i1, nx - 1) + 1):
            for j in range(max(j0, 0), min(j1, ny - 1) + 1):
                k = j * nx + i
                if not grid_[k] and shape.Collide(pcbnew.SHAPE_CIRCLE(pos(i, j), radius), dist):
                    grid_[k] = 1

    def mark_edges(grid_, dist):
        for e in obs.edges:
            i0, j0 = cell(pcbnew.VECTOR2I(min(e.A.x, e.B.x) - dist - grid, min(e.A.y, e.B.y) - dist - grid))
            i1, j1 = cell(pcbnew.VECTOR2I(max(e.A.x, e.B.x) + dist + grid, max(e.A.y, e.B.y) + dist + grid))
            for i in range(max(i0, 0), min(i1, nx - 1) + 1):
                for j in range(max(j0, 0), min(j1, ny - 1) + 1):
                    if e.Distance(pos(i, j)) < dist:
                        grid_[j * nx + i] = 1

    outside = bytearray(nx * ny)
    for i in range(nx):
        for j in range(ny):
            if not obs.outline.Contains(pos(i, j)):
                outside[j * nx + i] = 1
    track = []
    for layer in LAYERS:
        g = bytearray(outside)
        mark_edges(g, TRACK // 2 + EDGE)
        for s in obs.shapes[layer]:
            mark(g, s, TRACK // 2, CLEARANCE + SLACK)
        for h in obs.holes:
            mark(g, h, TRACK // 2, HOLE_CLEARANCE + SLACK)
        track.append(g)
    via = bytearray(outside)
    mark_edges(via, VIA_D // 2 + EDGE)
    for s in obs.shapes[LAYERS[0]] + obs.shapes[LAYERS[1]]:
        mark(via, s, VIA_D // 2, CLEARANCE + SLACK)
    for h in obs.holes:
        mark(via, h, VIA_D // 2, HOLE_CLEARANCE + SLACK)

    goals = {}
    for p, l in dst:
        goals[cell(p) + (li[l],)] = p
    heap, came, cost = [], {}, {}
    for p, l in src:
        k = cell(p) + (li[l],)
        cost[k] = 0
        came[k] = ("start", p)
        heapq.heappush(heap, (0, k))
    gx = [k[0] for k in goals]
    gy = [k[1] for k in goals]

    def h(k):
        return min(max(abs(k[0] - a), abs(k[1] - b)) for a, b in zip(gx, gy))

    # Cells next to the anchors sit inside this net's own pads, so they are
    # free even when the raster says otherwise.
    own = set()
    for p, l in src + dst:
        ci, cj = cell(p)
        for di in range(-3, 4):
            for dj in range(-3, 4):
                own.add((ci + di, cj + dj, li[l]))

    steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    end = None
    while heap:
        c0, k = heapq.heappop(heap)
        if k in goals:
            end = k
            break
        i, j, l = k
        if c0 - h(k) > cost[k] + 1e-9:
            continue
        nbrs = [((i + di, j + dj, l), c) for di, dj, c in steps]
        if not via[j * nx + i]:
            nbrs.append(((i, j, 1 - l), via_cost))
        for n, c in nbrs:
            if not (0 <= n[0] < nx and 0 <= n[1] < ny):
                continue
            if n not in goals and n not in own and track[n[2]][n[1] * nx + n[0]]:
                continue
            nc = cost[k] + c
            if nc < cost.get(n, 1e18):
                cost[n] = nc
                came[n] = k
                heapq.heappush(heap, (nc + h(n), n))
    if end is None:
        return None
    path = [end]
    while not isinstance(came[path[-1]], tuple) or came[path[-1]][0] != "start":
        path.append(came[path[-1]])
    start_point = came[path[-1]][1]
    path.reverse()
    points = [(start_point, LAYERS[path[0][2]])] + [(pos(i, j), LAYERS[l]) for i, j, l in path[1:-1]] + [(goals[end], LAYERS[end[2]])]
    return None, None, points


def simplify(points):
    """Drop collinear points from a list of (VECTOR2I, layer)."""
    res = [points[0]]
    for k in range(1, len(points) - 1):
        (a, la), (b, lb), (c, lc) = res[-1], points[k], points[k + 1]
        if la == lb == lc and (b.x - a.x) * (c.y - b.y) == (b.y - a.y) * (c.x - b.x):
            continue
        res.append(points[k])
    res.append(points[-1])
    return res


def nudge_edge_vias(board, obs, limit=MM(0.2)):
    """Move vias that sit a hair too close to the board edge straight inwards."""
    need = VIA_D // 2 + MM(0.3) + MM(0.01)
    for via in [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]:
        p = via.GetPosition()
        edge = min(obs.edges, key=lambda e: e.Distance(p))
        dist = edge.Distance(p)
        if dist >= need or need - dist > limit:
            continue
        near = edge.NearestPoint(p)
        dx, dy = p.x - near.x, p.y - near.y
        norm = (dx * dx + dy * dy) ** 0.5 or 1
        move = need - dist
        q = pcbnew.VECTOR2I(int(p.x + dx / norm * move), int(p.y + dy / norm * move))
        for t in board.GetTracks():
            if t.GetNetCode() != via.GetNetCode() or t.Type() != pcbnew.PCB_TRACE_T:
                continue
            if t.GetStart() == p:
                t.SetStart(q)
            if t.GetEnd() == p:
                t.SetEnd(q)
        via.SetPosition(q)
        print(f"moved {via.GetNetname()} via {pcbnew.ToMM(move):.3f} mm away from the edge")


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    failed = []
    for net in board.GetNetsByName().values():
        code = net.GetNetCode()
        # GND is joined by the copper pours added afterwards.
        if code <= 0 or net.GetNetname() == "GND":
            continue
        groups = islands(board, code)
        while len(groups) > 1:
            obs = Obstacles(board, code)
            main_group, other = groups[0], groups[1]
            path = best_path(obs, anchors(other), anchors(main_group))
            if path:
                _, segs, vias = path
            else:
                routed = maze_route(obs, anchors(other), anchors(main_group))
                if not routed:
                    failed.append(net.GetNetname())
                    break
                points = simplify(routed[2])
                segs, vias = [], []
                for (a, la), (b, lb) in zip(points, points[1:]):
                    if la != lb:
                        vias.append(a)
                    elif a != b:
                        segs.append((a, b, la))
            for a, b, layer in segs:
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a)
                t.SetEnd(b)
                t.SetWidth(TRACK)
                t.SetLayer(layer)
                t.SetNet(net)
                board.Add(t)
            for v in vias:
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(v)
                via.SetWidth(VIA_D)
                via.SetDrill(VIA_DRILL)
                via.SetNet(net)
                board.Add(via)
            print(f"{net.GetNetname()}: joined island with {len(segs)} track(s), {len(vias)} via(s)")
            groups = islands(board, code)
    nudge_edge_vias(board, Obstacles(board, 0))
    board.Save(sys.argv[1])
    if failed:
        sys.exit("could not join " + ", ".join(failed) + "; route by hand in KiCad")


if __name__ == "__main__":
    main()
