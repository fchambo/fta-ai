#!/usr/bin/env python3
"""Build a park's real map from OpenStreetMap (developer tool, not shipped in the skills).

    python3 tools/osm_park.py mk                 # downloads the park's area from the OSM API
    python3 tools/osm_park.py mk --osm mk.osm    # or uses a file you exported yourself

Reads the "osm" block of travel-agent/skills/park-itinerary/scripts/parks/<park>.json:

    "osm": {
      "bbox": [south, west, north, east],      # area to download
      "boundary_way": 297428432,               # the park's tourism=theme_park way (or "boundary_relation")
      "entrance": [lat, lon],                  # turnstiles
      "landmark": [lat, lon] or "OSM name",    # e.g. the castle, for the map
      "names": {"meet-mickey": "Town Square Theater"},   # OSM name when it differs from ours
      "points": {"happily-ever-after": [lat, lon]},      # places with no OSM feature (parades, fireworks)
      "walk_grid": 8                           # optional: walk the open space on an 8 m grid when walkways aren't mapped
    }

Writes scripts/parks/osm/<park>.json: the park outline, water, green areas, plazas, buildings,
attraction footprints, the walkway network (for routes and walking times) and where each
attraction is reached from the walkways. Map data © OpenStreetMap contributors, ODbL 1.0.
"""
import argparse
import heapq
import json
import math
import os
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARKS = os.path.join(ROOT, "travel-agent", "skills", "park-itinerary", "scripts", "parks")
OSM_API = "https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}"
USER_AGENT = "fta-ai park map builder"

WALKABLE = {"footway", "pedestrian", "path", "steps", "living_street", "corridor", "service", "unclassified"}
NO_ACCESS = {"private", "no", "destination", "delivery"}
GREEN = {("landuse", "grass"), ("landuse", "forest"), ("leisure", "garden"), ("leisure", "park"),
         ("natural", "wood"), ("natural", "scrub"), ("landuse", "meadow"), ("natural", "grassland")}


def norm(text):
    text = str(text).replace("'", "").replace("’", "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return re.sub(r"^the ", "", text)


def simplify(points, tol):
    """Douglas-Peucker on [(x, y)]."""
    if len(points) < 3:
        return points
    (x0, y0), (x1, y1) = points[0], points[-1]
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1e-9
    best, idx = -1, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = abs(dy * px - dx * py + x1 * y0 - y1 * x0) / length if (dx or dy) else math.dist(points[i], points[0])
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [points[0], points[-1]]
    return simplify(points[: idx + 1], tol)[:-1] + simplify(points[idx:], tol)


def inside(pt, poly):
    x, y, hit = pt[0], pt[1], False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            hit = not hit
    return hit


def rings(ways):
    """Join open member ways of a multipolygon into closed rings."""
    pending = [list(w) for w in ways if len(w) > 1]
    out = []
    while pending:
        ring = pending.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, w in enumerate(pending):
                if w[0] == ring[-1]:
                    ring += w[1:]
                elif w[-1] == ring[-1]:
                    ring += w[::-1][1:]
                elif w[-1] == ring[0]:
                    ring = w[:-1] + ring
                elif w[0] == ring[0]:
                    ring = w[::-1][:-1] + ring
                else:
                    continue
                pending.pop(i)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) > 3:
            out.append(ring)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("park")
    ap.add_argument("--osm", help="OSM XML file (default: download the bbox from the OSM API)")
    ap.add_argument("--list", action="store_true", help="list named features and entrance candidates, then stop")
    args = ap.parse_args()

    park_path = os.path.join(PARKS, f"{args.park}.json")
    park = json.load(open(park_path, encoding="utf-8"))
    cfg = park["osm"]
    s, w, n, e = cfg["bbox"]
    if args.osm:
        xml = open(args.osm, "rb").read()
    else:
        req = urllib.request.Request(OSM_API.format(s=s, w=w, n=n, e=e), headers={"User-Agent": USER_AGENT})
        xml = urllib.request.urlopen(req, timeout=180).read()
    root = ET.fromstring(xml)

    lat0, lon0 = s, w
    kx = math.cos(math.radians((s + n) / 2)) * 111320.0
    ky = 110574.0

    def xy(lat, lon):
        return ((lon - lon0) * kx, (lat - lat0) * ky)

    nodes, node_tags, ways, rels = {}, {}, {}, []
    for el in root:
        tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
        if el.tag == "node":
            nodes[el.get("id")] = xy(float(el.get("lat")), float(el.get("lon")))
            if tags:
                node_tags[el.get("id")] = tags
        elif el.tag == "way":
            ways[el.get("id")] = ([nd.get("ref") for nd in el.findall("nd")], tags)
        elif el.tag == "relation":
            rels.append(([(m.get("type"), m.get("ref"), m.get("role")) for m in el.findall("member")], tags, el.get("id")))

    def coords(refs):
        return [nodes[r] for r in refs if r in nodes]

    # park outline
    if cfg.get("boundary_way"):
        outline = coords(ways[str(cfg["boundary_way"])][0])
    else:
        rel = next(r for r in rels if r[2] == str(cfg["boundary_relation"]))
        outline = max((coords(r) for r in rings([ways[m[1]][0] for m in rel[0] if m[0] == "way" and m[1] in ways])),
                      key=len)
    pad = 25
    minx, miny = min(p[0] for p in outline) - pad, min(p[1] for p in outline) - pad
    maxx, maxy = max(p[0] for p in outline) + pad, max(p[1] for p in outline) + pad

    def shift(pts):
        return [[round(x - minx, 1), round(y - miny, 1)] for x, y in pts]

    def in_park(pts):
        if not pts:
            return False
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        return inside((cx, cy), outline) or any(inside(p, outline) for p in pts[:: max(1, len(pts) // 6)])

    areas = {"water": [], "green": [], "plaza": [], "building": []}
    named_polys = {}  # norm name -> list of polygons (unshifted)
    paths, graph_ways = [], []

    def classify(tags):
        if tags.get("natural") == "water" or "water" in tags or tags.get("waterway") == "riverbank":
            return "water"
        if any((k, tags.get(k)) in GREEN for k in ("landuse", "leisure", "natural")):
            return "green"
        if tags.get("highway") == "pedestrian" and tags.get("area") == "yes" or tags.get("place") == "square":
            return "plaza"
        if "building" in tags:
            return "building"
        return None

    for wid, (refs, tags) in ways.items():
        pts = coords(refs)
        if len(pts) < 2:
            continue
        name = tags.get("name")
        closed = refs[0] == refs[-1] and len(pts) > 3
        kind = classify(tags) if closed else None
        if kind and in_park(pts):
            areas[kind].append(pts)
        if name and closed and "highway" not in tags and in_park(pts):
            for key in {name, tags.get("alt_name"), tags.get("official_name")} - {None}:
                named_polys.setdefault(norm(key), []).append(pts)
        hw = tags.get("highway")
        if hw in WALKABLE and tags.get("access") not in NO_ACCESS and tags.get("area") != "yes" \
                and not (hw == "service" and tags.get("service") in ("driveway", "parking_aisle", "alley")) \
                and in_park(pts):
            graph_ways.append(refs)
            paths.append(pts)
        elif hw == "pedestrian" and tags.get("area") == "yes" and in_park(pts):
            graph_ways.append(refs)  # walk along plaza edges
    for members, tags, _ in rels:
        if tags.get("type") != "multipolygon":
            continue
        kind = classify(tags)
        outer = [ways[m[1]][0] for m in members if m[0] == "way" and m[1] in ways and m[2] in ("outer", "")]
        for ring in rings(outer):
            pts = coords(ring)
            if kind and in_park(pts):
                areas[kind].append(pts)
            if tags.get("name") and in_park(pts):
                for key in {tags["name"], tags.get("alt_name"), tags.get("official_name")} - {None}:
                    named_polys.setdefault(norm(key), []).append(pts)
        if tags.get("highway") == "pedestrian":
            for ring in rings(outer):
                graph_ways.append(ring)

    # walkway graph, largest connected component
    index, gnodes, edges = {}, [], set()
    grid = cfg.get("walk_grid")  # meters; for parks whose walkways aren't mapped: walk the open space instead
    if grid:
        ox, oy = min(p[0] for p in outline), min(p[1] for p in outline)
        nx = int((max(p[0] for p in outline) - ox) / grid) + 1
        ny = int((max(p[1] for p in outline) - oy) / grid) + 1

        def cells_in(poly):
            xs, ys = [p[0] for p in poly], [p[1] for p in poly]
            for i in range(max(0, int((min(xs) - ox) / grid)), min(nx - 1, int((max(xs) - ox) / grid)) + 1):
                for j in range(max(0, int((min(ys) - oy) / grid)), min(ny - 1, int((max(ys) - oy) / grid)) + 1):
                    if inside((ox + (i + .5) * grid, oy + (j + .5) * grid), poly):
                        yield i, j

        free = set(cells_in(outline))
        for poly in areas["building"] + areas["water"]:
            free -= set(cells_in(poly))
        for i, j in sorted(free):
            index[(i, j)] = len(gnodes)
            gnodes.append((ox + (i + .5) * grid, oy + (j + .5) * grid))
        for (i, j), v in index.items():
            for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
                u = index.get((i + di, j + dj))
                if u is not None and (di == 0 or dj == 0 or ((i + di, j) in index and (i, j + dj) in index)):
                    edges.add((min(u, v), max(u, v)))
    for refs in ([] if grid else graph_ways):
        ids = [r for r in refs if r in nodes]
        for a, b in zip(ids, ids[1:]):
            for r in (a, b):
                if r not in index:
                    index[r] = len(gnodes)
                    gnodes.append(nodes[r])
            if a != b:
                edges.add((min(index[a], index[b]), max(index[a], index[b])))
    adj = [[] for _ in gnodes]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen, best = [False] * len(gnodes), []
    for start in range(len(gnodes)):
        if seen[start]:
            continue
        comp, stack = [], [start]
        seen[start] = True
        while stack:
            v = stack.pop()
            comp.append(v)
            for u in adj[v]:
                if not seen[u]:
                    seen[u] = True
                    stack.append(u)
        if len(comp) > len(best):
            best = comp
    keep = sorted(best)
    remap = {old: new for new, old in enumerate(keep)}
    g_nodes = [gnodes[i] for i in keep]
    g_edges = sorted((remap[a], remap[b]) for a, b in edges if a in remap and b in remap)

    def nearest(pt):
        return min(range(len(g_nodes)), key=lambda i: (g_nodes[i][0] - pt[0]) ** 2 + (g_nodes[i][1] - pt[1]) ** 2)

    # where each attraction is reached from the walkways
    point_names = {}
    for nid, tags in node_tags.items():
        if tags.get("name"):
            for key in {tags["name"], tags.get("alt_name"), tags.get("official_name")} - {None}:
                point_names.setdefault(norm(key), nodes[nid])
    if args.list:
        def ll(p):
            return f"{lat0 + p[1] / ky:.6f},{lon0 + p[0] / kx:.6f}"
        print("AREAS:", " | ".join(sorted(named_polys)))
        print("POINTS:", " | ".join(sorted(k for k, v in point_names.items() if inside(v, outline))))
        for nid, tags in node_tags.items():
            text = " ".join(f"{k}={v}" for k, v in tags.items())
            if re.search(r"entrance|turnstile|gate|security|ticket", text, re.I) and inside(nodes[nid], outline):
                print("ENTRANCE?", ll(nodes[nid]), text[:120])
        missing_ids = [a["id"] for a in park["attractions"]
                       if not any(norm(x) in named_polys or norm(x) in point_names for x in [a["name"], a.get("short", "")] if x)]
        print("UNMATCHED:", missing_ids)
        return
    places, polys_for, missing = {}, {}, []
    for a in park["attractions"]:
        if a["id"] in cfg.get("points", {}):
            lat, lon = cfg["points"][a["id"]]
            places[a["id"]] = nearest(xy(lat, lon))
            continue
        wanted = [norm(x) for x in ([cfg.get("names", {}).get(a["id"])] if cfg.get("names", {}).get(a["id"]) else [])
                  + [a["name"], a.get("short", "")] if x]
        polys = next((named_polys[k] for k in wanted if k in named_polys), None)
        if polys:
            best_d, best_i = None, None
            for poly in polys:
                for p in poly[:: max(1, len(poly) // 40)]:
                    i = nearest(p)
                    d = math.dist(p, g_nodes[i])
                    if best_d is None or d < best_d:
                        best_d, best_i = d, i
            places[a["id"]] = best_i
            polys_for[a["id"]] = polys
            continue
        pt = next((point_names[k] for k in wanted if k in point_names), None)
        if pt:
            places[a["id"]] = nearest(pt)
        else:
            missing.append(a["id"])

    attraction_polys = list({id(p): p for polys in polys_for.values() for p in polys}.values())
    landmark = cfg.get("landmark")
    if isinstance(landmark, str):  # a name: the middle of that feature
        poly = max(named_polys.get(norm(landmark), [[]]), key=len)
        landmark = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)) if poly \
            else point_names.get(norm(landmark))
        if landmark is None:
            print(f"Landmark '{cfg['landmark']}' not found in OSM", file=sys.stderr)
    elif landmark:
        landmark = xy(*landmark)
    out = {
        "attribution": "© OpenStreetMap contributors (ODbL 1.0)",
        "extracted": date.today().isoformat(),
        "origin": [lat0, lon0, round(kx, 3), ky, round(minx, 1), round(miny, 1)],
        "size": [round(maxx - minx, 1), round(maxy - miny, 1)],
        "outline": shift(simplify(outline, 2.0)),
        "areas": {k: [shift(simplify(p, 1.5 if k != "building" else 0.8)) for p in v] for k, v in areas.items()},
        "attractions": [shift(simplify(p, 0.8)) for p in attraction_polys],
        "paths": [shift(simplify(p, 1.0)) for p in paths],
        "graph": {"nodes": shift(g_nodes), "edges": [list(e) for e in g_edges]},
        "places": places,
        "entrance": nearest(xy(*cfg["entrance"])),
        "landmark": shift([landmark])[0] if landmark else None,
    }
    dest = os.path.join(PARKS, "osm", f"{park['id']}.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(json.dumps({"file": os.path.relpath(dest, ROOT), "kb": round(os.path.getsize(dest) / 1024),
                      "size_m": out["size"], "graph_nodes": len(g_nodes), "graph_edges": len(g_edges),
                      "areas": {k: len(v) for k, v in out["areas"].items()}, "paths": len(paths),
                      "matched": len(places), "missing": missing}, indent=1))
    if missing:
        print("Add these to osm.names or osm.points in the park file and re-run.", file=sys.stderr)


if __name__ == "__main__":
    main()
