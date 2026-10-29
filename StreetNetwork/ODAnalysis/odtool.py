"""Standalone origin-destination (OD) analysis on a street network.

Routes every origin to one or more destinations over a line network and reports, for each street
segment, how many people's trips cross it, and for each origin, how long its trip takes.

    import odtool
    net = odtool.build_network(streets)                       # lines -> routable graph
    res = odtool.run_od(net, origins, destinations, mode="nearest")
    res.segments      # streets + traffic columns (GeoDataFrame)
    res.origins       # per-origin travel time / distance to the assigned destination(s)
    res.matrix        # long OD travel-time matrix (origin x destination)
    res.summary       # dict: person-km, person-hours, reachable population, ...

Method (same as the PROTECT `od_stochastic_assignment.ipynb`, without the RA2CE graph build):

1. Graph. Every line is an edge between its two end points; lines that share an end point
   coordinate are connected. Parallel lines between the same two points are kept, and in each
   routing pass the cheaper one carries the flow. The network is undirected (one-way streets are
   not modeled).
2. Cost. Travel time from a free-flow speed per road class (`SPEED_MPH`), or distance.
3. Snapping. Each origin and destination is moved to the nearest point on the nearest edge of the
   largest connected part of the network, and that edge is split there.
4. Routing. Dijkstra from each destination gives one shortest-path tree covering every origin.
   Destination choice is `nearest` (all of an origin's trips go to its quickest destination) or
   `gravity` (trips split across destinations in proportion to time ** -beta).
5. Stochastic assignment. The routing is repeated `n_draws` times; in each draw every edge's cost
   is multiplied by an independent lognormal factor (mean 1, sigma `sigma`), and the flows are
   averaged. Near-tied routes share the load; a clearly faster road still wins nearly every draw.
   `n_draws=1, sigma=0` gives one deterministic all-or-nothing assignment.

Traffic measures per segment (all are averages over draws):
    traffic               population routed across the segment
    traffic_egalitarian   number of origins routed across it (each origin counts 1, times its share)
    traffic_prioritarian  population x equity weight
    traffic_sd            draw-to-draw standard deviation of `traffic`
    routed                1 if any trip crossed it in any draw
"""
from __future__ import annotations

from dataclasses import dataclass, field

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import shapely.ops
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra

MPH_TO_MPS = 0.44704

# Free-flow speed by Overture road class (mph). Starting assumptions; calibrate locally.
SPEED_MPH = {
    "motorway": 55, "trunk": 45, "primary": 35, "secondary": 30, "tertiary": 30,
    "unclassified": 25, "residential": 25, "living_street": 10, "service": 10, "unknown": 15,
}
DEFAULT_MPH = 25
GRAVITY_BETA = 2.0
METRIC_CRS = 3310          # California Albers; any metre-based CRS covering the study area works


# --------------------------------------------------------------------------------------------
# network
# --------------------------------------------------------------------------------------------
@dataclass
class Network:
    """Routable graph. `edges` has one row per edge; `street` is the row of the input lines."""
    edges: pd.DataFrame            # u, v, street, length_m, mph, time_s, geometry (metric CRS)
    nodes: np.ndarray              # (n, 2) node coordinates in `crs`
    streets: gpd.GeoDataFrame      # the input lines, unchanged
    crs: object
    main: np.ndarray = field(default=None)   # bool per node: in the largest connected component

    @property
    def n(self):
        return len(self.nodes)


def build_network(streets: gpd.GeoDataFrame, class_col: str | None = "class",
                  speeds: dict | None = None, default_mph: float = DEFAULT_MPH,
                  speed_col: str | None = None, crs=METRIC_CRS, precision: float = 0.01) -> Network:
    """Turn a line layer into a routable graph.

    streets    LineString / MultiLineString layer (any CRS).
    class_col  road-class column used to look up `speeds`; None to use `default_mph` everywhere.
    speed_col  optional column with a speed in mph per line; overrides the class lookup where set.
    crs        metre-based CRS lengths are measured in.
    precision  end points closer than this (metres) are treated as the same node.
    """
    speeds = SPEED_MPH if speeds is None else speeds
    s = streets.reset_index(drop=True)
    g = s.geometry.to_crs(crs).values
    g = shapely.force_2d(g)
    multi = shapely.get_type_id(g) == 5
    if multi.any():                 # MultiLineString: merge parts; anything still multi is split
        g[multi] = shapely.line_merge(g[multi])
    parts, street = shapely.get_parts(g, return_index=True)
    parts = np.asarray(parts)
    keep = (shapely.get_type_id(parts) == 1) & (shapely.length(parts) > 0)
    parts, street = parts[keep], street[keep]

    a = shapely.get_coordinates(shapely.get_point(parts, 0))
    b = shapely.get_coordinates(shapely.get_point(parts, -1))
    key = np.round(np.vstack([a, b]) / precision).astype(np.int64)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    nodes = uniq * precision

    if class_col is not None and class_col in s.columns:
        mph = s[class_col].map(speeds).astype(float).fillna(default_mph).to_numpy()
    else:
        mph = np.full(len(s), float(default_mph))
    if speed_col is not None:
        given = pd.to_numeric(s[speed_col], errors="coerce").to_numpy()
        mph = np.where(np.isfinite(given) & (given > 0), given, mph)

    e = pd.DataFrame({"u": inv[:len(parts)], "v": inv[len(parts):], "street": street,
                      "length_m": shapely.length(parts), "mph": mph[street]})
    e["time_s"] = e.length_m / (e.mph * MPH_TO_MPS)
    e["geometry"] = parts
    net = Network(edges=e, nodes=nodes, streets=s, crs=crs)
    net.main = _main_component(net)
    return net


def _main_component(net: Network) -> np.ndarray:
    e = net.edges
    G = csr_matrix((np.ones(len(e)), (e.u, e.v)), shape=(net.n, net.n))
    _, lab = connected_components(G, directed=False)
    return lab == np.bincount(lab).argmax()


def snap(net: Network, points: gpd.GeoSeries, main_only: bool = True, end_tol: float = 0.5):
    """Snap points onto the network, splitting edges where they land.

    Returns (new_network, node_index_per_point, snap_distance_m). A point within `end_tol` metres of
    an edge's end snaps to that node instead of splitting the edge. With `main_only` points snap
    only to edges in the largest connected component, so every snapped point can reach every other.
    """
    e = net.edges
    pts = np.asarray(points.to_crs(net.crs).values)
    cand = np.flatnonzero(net.main[e.u.to_numpy()]) if main_only else np.arange(len(e))
    tree = shapely.STRtree(e.geometry.to_numpy()[cand])
    (pi, ti), d = tree.query_nearest(pts, return_distance=True, all_matches=False)
    eid = np.full(len(pts), -1)
    dist = np.full(len(pts), np.nan)
    eid[pi], dist[pi] = cand[ti], d
    if (eid < 0).any():
        raise ValueError(f"{(eid < 0).sum()} points have empty geometry")

    geom = e.geometry.to_numpy()
    pos = shapely.line_locate_point(geom[eid], pts)
    L = e.length_m.to_numpy()[eid]
    node = np.full(len(pts), -1)
    at_u, at_v = pos <= end_tol, pos >= L - end_tol
    node[at_u] = e.u.to_numpy()[eid[at_u]]
    node[at_v & ~at_u] = e.v.to_numpy()[eid[at_v & ~at_u]]

    # split each touched edge at the sorted interior positions; one new node per distinct position
    new_nodes, new_edges, drop = [], [], []
    next_id = net.n
    mid = np.flatnonzero(node < 0)
    for k in np.unique(eid[mid]):
        idx = mid[eid[mid] == k]
        ps = np.round(pos[idx], 3)
        cuts = np.unique(ps)
        ids = np.arange(next_id, next_id + len(cuts))
        next_id += len(cuts)
        node[idx] = ids[np.searchsorted(cuts, ps)]
        line, row = geom[k], e.iloc[k]
        new_nodes.append(shapely.get_coordinates(shapely.line_interpolate_point(line, cuts)))
        stops = np.concatenate([[0.0], cuts, [row.length_m]])
        ends = np.concatenate([[row.u], ids, [row.v]])
        for j in range(len(stops) - 1):
            piece = shapely.ops.substring(line, stops[j], stops[j + 1])
            ln = piece.length
            new_edges.append(dict(u=ends[j], v=ends[j + 1], street=row.street, length_m=ln,
                                  mph=row.mph, time_s=ln / (row.mph * MPH_TO_MPS), geometry=piece))
        drop.append(k)

    edges = e.drop(index=drop)
    if new_edges:
        edges = pd.concat([edges, pd.DataFrame(new_edges)], ignore_index=True)
        nodes = np.vstack([net.nodes] + new_nodes)
        main = np.concatenate([net.main, np.ones(next_id - net.n, bool) if main_only
                               else np.zeros(next_id - net.n, bool)])
    else:
        edges, nodes, main = edges.reset_index(drop=True), net.nodes, net.main
    edges["u"], edges["v"] = edges.u.astype(int), edges.v.astype(int)
    out = Network(edges=edges, nodes=nodes, streets=net.streets, crs=net.crs, main=main)
    if not main_only:
        out.main = _main_component(out)
    return out, node, dist


# --------------------------------------------------------------------------------------------
# router (from od_stochastic_assignment.ipynb)
# --------------------------------------------------------------------------------------------
def cheapest_parallel(ui, vi, w):
    """Index of the cheapest edge per undirected node pair (self-loops dropped)."""
    a, b = np.minimum(ui, vi), np.maximum(ui, vi)
    idx = np.flatnonzero(a != b)
    order = idx[np.lexsort((w[idx], b[idx], a[idx]))]
    first = np.ones(len(order), bool)
    first[1:] = (a[order][1:] != a[order][:-1]) | (b[order][1:] != b[order][:-1])
    return order[first]


def push_down_tree(dist, pred, loads):
    """Accumulate node loads toward the tree root; returns the load leaving each node."""
    reach = np.flatnonzero(np.isfinite(dist) & (pred >= 0))
    order = reach[np.argsort(-dist[reach], kind="stable")]
    L = [col.tolist() for col in loads]       # python lists: fast scalar access
    P = pred.tolist()
    L0, L1, L2 = L
    for n in order:
        if L1[n] == 0.0:
            continue
        p = P[n]
        L0[p] += L0[n]; L1[p] += L1[n]; L2[p] += L2[n]
    return np.array(L), order


def _graph(ui, vi, w, n):
    best = cheapest_parallel(ui, vi, w)
    rows = np.concatenate([ui[best], vi[best]])
    cols = np.concatenate([vi[best], ui[best]])
    G = csr_matrix((np.concatenate([w[best], w[best]]), (rows, cols)), shape=(n, n))
    E = csr_matrix((np.concatenate([best, best]) + 1, (rows, cols)), shape=(n, n))  # pair -> edge id+1
    return G, E


def assign(P, w, mode, beta=GRAVITY_BETA):
    """One routing pass on edge cost `w`.

    Returns (flows, check): flows is per-edge [traffic, egalitarian, prioritarian]; check holds,
    per destination, trips sent there and trips that arrive at its node. They must be equal.
    """
    ui, vi, n = P["ui"], P["vi"], P["n"]
    G, E = _graph(ui, vi, w, n)
    flows = np.zeros((3, len(ui)))
    o_ix, pop, wt, d_ix = P["o_ix"], P["pop"], P["wt"], P["d_ix"]

    def add_tree(dist, pred, share):
        loads = np.zeros((3, n))
        np.add.at(loads[0], o_ix, share * pop)
        np.add.at(loads[1], o_ix, share)
        np.add.at(loads[2], o_ix, share * pop * wt)
        L, order = push_down_tree(dist, pred, loads)
        ch = order[L[1, order] > 0]
        eid = np.asarray(E[ch, pred[ch]]).ravel() - 1
        flows[:, eid] += L[:, ch]
        return L[0]                     # population load at every node; roots hold what arrived

    if mode == "nearest":
        dist, pred, src = dijkstra(G, indices=d_ix, min_only=True, return_predecessors=True)
        share = np.isfinite(dist[o_ix]).astype(float)
        L0 = add_tree(dist, pred, share)
        # destinations sharing a node are one root; count each node once
        sent = np.array([float((share * pop)[src[o_ix] == d].sum()) for d in d_ix])
        first = ~pd.Series(d_ix).duplicated().to_numpy()
        sent, arrived = np.where(first, sent, 0.0), np.where(first, L0[d_ix], 0.0)
    elif mode == "gravity":
        dists, preds = dijkstra(G, indices=d_ix, return_predecessors=True)
        shares = gravity_shares(dists[:, o_ix], beta)
        sent, arrived = np.zeros(len(d_ix)), np.zeros(len(d_ix))
        for k in range(len(d_ix)):
            L0 = add_tree(dists[k], preds[k], shares[k])
            sent[k] = float((shares[k] * pop).sum())
            arrived[k] = L0[d_ix[k]]
    else:
        raise ValueError(f"mode must be 'nearest' or 'gravity', not {mode!r}")
    return flows, dict(sent=sent, arrived=arrived)


def gravity_shares(t, beta=GRAVITY_BETA):
    """(n_dest, n_origin) cost -> share of each origin's trips going to each destination."""
    t = np.clip(t, 1.0, None)
    inv = np.where(np.isfinite(t), t ** (-beta), 0.0)
    tot = inv.sum(axis=0)
    return np.divide(inv, tot, out=np.zeros_like(inv), where=tot > 0)


# --------------------------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------------------------
@dataclass
class ODResult:
    segments: gpd.GeoDataFrame
    origins: gpd.GeoDataFrame
    destinations: gpd.GeoDataFrame
    matrix: pd.DataFrame
    summary: dict
    edges: gpd.GeoDataFrame        # the snapped routing edges with their flows (for QA)

    def save(self, folder, name):
        """Write <name>_segments.gpkg, _origins.gpkg, _destinations.csv, _od_matrix.csv, _summary.json."""
        import json
        from pathlib import Path
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        self.segments.to_file(folder / f"{name}_segments.gpkg", layer="segments", driver="GPKG")
        self.origins.to_file(folder / f"{name}_origins.gpkg", layer="origins", driver="GPKG")
        self.destinations.drop(columns="geometry").to_csv(folder / f"{name}_destinations.csv", index=False)
        self.matrix.to_csv(folder / f"{name}_od_matrix.csv", index=False)
        (folder / f"{name}_summary.json").write_text(json.dumps(self.summary, indent=2, default=float),
                                                     encoding="utf-8")
        return folder


def run_od(net: Network, origins: gpd.GeoDataFrame, destinations: gpd.GeoDataFrame,
           mode: str = "nearest", population: str | None = "population", weight: str | None = None,
           cost: str = "time", n_draws: int = 100, sigma: float = 0.25, beta: float = GRAVITY_BETA,
           seed: int = 20261008, origin_id: str | None = None, dest_name: str | None = "name",
           verbose: bool = True) -> ODResult:
    """Route every origin to `destinations` and return segment traffic and per-origin access.

    mode        'nearest' or 'gravity'.
    population  origin column of trips per origin (None = 1 per origin).
    weight      origin column of an equity weight for `traffic_prioritarian` (None = 1).
    cost        'time' (road-class speeds) or 'distance'.
    n_draws, sigma  stochastic assignment; n_draws=1, sigma=0 for a deterministic run.
    """
    import time as _time
    t0 = _time.time()
    log = print if verbose else (lambda *a, **k: None)
    o = origins.reset_index(drop=True)
    d = destinations.reset_index(drop=True)
    pts = pd.concat([o.geometry.to_crs(net.crs), d.geometry.to_crs(net.crs)], ignore_index=True)
    snet, node, snap_m = snap(net, gpd.GeoSeries(pts, crs=net.crs))
    o_ix, d_ix = node[:len(o)], node[len(o):]

    e = snet.edges
    P = dict(ui=e.u.to_numpy(), vi=e.v.to_numpy(), n=snet.n, o_ix=o_ix, d_ix=d_ix,
             pop=(o[population].fillna(0).astype(float).to_numpy() if population else np.ones(len(o))),
             wt=(o[weight].fillna(1.0).astype(float).to_numpy() if weight else np.ones(len(o))))
    base = e["time_s" if cost == "time" else "length_m"].to_numpy(dtype=float)
    log(f"network {snet.n:,} nodes / {len(e):,} edges; {len(o):,} origins, {len(d)} destinations; "
        f"median snap {np.nanmedian(snap_m[:len(o)]):.0f} m")

    # stochastic assignment
    rng = np.random.default_rng(seed)
    s = np.zeros((3, len(e)))
    s2 = np.zeros(len(e))
    arrived = np.zeros(len(d))
    max_gap = 0.0
    for i in range(n_draws):
        noise = np.exp(rng.normal(-sigma ** 2 / 2, sigma, len(base))) if sigma > 0 else 1.0
        f, chk = assign(P, base * noise, mode, beta)
        max_gap = max(max_gap, float(np.abs(chk["sent"] - chk["arrived"]).max()))
        arrived += chk["arrived"]
        s += f
        s2 += f[0] ** 2
    mean = s / n_draws
    sd = np.sqrt(np.maximum(s2 / n_draws - mean[0] ** 2, 0))
    log(f"{n_draws} draw(s) in {_time.time() - t0:.0f} s")

    # edges -> input streets (a split street takes the max over its pieces)
    ef = pd.DataFrame({"street": e.street.to_numpy(), "traffic": mean[0], "traffic_egalitarian": mean[1],
                       "traffic_prioritarian": mean[2], "traffic_sd": sd})
    per = ef.groupby("street").max()
    seg = net.streets.copy()
    seg["mph"] = net.edges.groupby("street")["mph"].first().reindex(seg.index).to_numpy()
    for c in per.columns:
        seg[c] = per[c].reindex(seg.index).fillna(0).to_numpy()
    seg["routed"] = (seg["traffic_egalitarian"] > 0).astype(int)

    # per-origin access on the unperturbed cost: time and distance along the chosen route(s)
    acc = _access(snet, P, base, mode, beta)
    oo = o.copy()
    oo["snap_m"] = snap_m[:len(o)]
    oo["reachable"] = np.isfinite(acc["time_min"]).astype(int)
    if mode == "nearest":
        oo["dest_id"] = np.where(oo.reachable == 1, acc["dest"], -1)
        if dest_name and dest_name in d.columns:
            oo["dest_name"] = pd.Series(d[dest_name].to_numpy()[np.clip(acc["dest"], 0, None)]).where(
                oo.reachable.to_numpy() == 1).to_numpy()
    oo["time_min"] = acc["time_min"]
    oo["dist_km"] = acc["dist_km"]

    dd = d.copy()
    dd["snap_m"] = snap_m[len(o):]
    dd["trips_arriving"] = arrived / n_draws
    mx = acc["matrix"]
    if origin_id:
        mx["origin"] = o[origin_id].to_numpy()[mx["origin"].to_numpy()]
    if dest_name and dest_name in d.columns:
        mx.insert(2, "dest_name", d[dest_name].to_numpy()[mx["dest_id"].to_numpy()])

    pop = P["pop"]
    reach = oo.reachable.to_numpy() == 1
    elen = e.length_m.to_numpy()
    summary = dict(
        mode=mode, cost=cost, n_draws=n_draws, sigma=sigma, beta=beta if mode == "gravity" else None,
        origins=len(o), destinations=len(d),
        population=float(pop.sum()), population_reachable=float(pop[reach].sum()),
        origins_unreachable=int((~reach).sum()),
        person_km=float((mean[0] * elen).sum() / 1000),
        person_hours=float((mean[0] * e.time_s.to_numpy()).sum() / 3600),
        mean_trip_min=float(np.average(oo.time_min[reach], weights=pop[reach])) if pop[reach].sum() else None,
        trip_check_max_gap=max_gap,
        streets_routed=int(seg.routed.sum()),
        seconds=round(_time.time() - t0, 1),
    )
    edges_out = gpd.GeoDataFrame(e.drop(columns="geometry").assign(**ef.drop(columns="street")),
                                 geometry=e.geometry.to_numpy(), crs=net.crs)
    log(f"done in {summary['seconds']} s: {summary['person_km']:,.0f} person-km, "
        f"mean trip {summary['mean_trip_min'] or 0:.1f} min, "
        f"{summary['origins_unreachable']} origins unreachable")
    return ODResult(seg, oo, dd, mx, summary, edges_out)


def _access(snet, P, w, mode, beta):
    """Travel time and route distance from every origin to every destination (no noise)."""
    G, E = _graph(P["ui"], P["vi"], w, snet.n)
    elen = snet.edges.length_m.to_numpy()
    tsec = snet.edges.time_s.to_numpy()
    dists, preds = dijkstra(G, indices=P["d_ix"], return_predecessors=True)
    o_ix = P["o_ix"]
    n_d, n_o = len(P["d_ix"]), len(o_ix)
    T, D = np.full((n_d, n_o), np.inf), np.full((n_d, n_o), np.inf)
    for k in range(n_d):
        dist, pred = dists[k], preds[k]
        # route length and time to the root: walk nodes outward from the root in cost order
        reach = np.flatnonzero(np.isfinite(dist))
        order = reach[np.argsort(dist[reach], kind="stable")]
        has = order[pred[order] >= 0]
        eid = np.asarray(E[has, pred[has]]).ravel() - 1
        step_len = np.zeros(snet.n); step_len[has] = elen[eid]
        step_t = np.zeros(snet.n); step_t[has] = tsec[eid]
        ln, tt = np.full(snet.n, np.inf), np.full(snet.n, np.inf)
        ln[P["d_ix"][k]] = tt[P["d_ix"][k]] = 0.0
        Pl, Ln, Tt, SL, ST = pred.tolist(), ln.tolist(), tt.tolist(), step_len.tolist(), step_t.tolist()
        for nd in has.tolist():
            p = Pl[nd]
            Ln[nd] = Ln[p] + SL[nd]
            Tt[nd] = Tt[p] + ST[nd]
        T[k] = np.asarray(Tt)[o_ix]
        D[k] = np.asarray(Ln)[o_ix]
    cost = dists[:, o_ix]
    if mode == "nearest":
        best = np.argmin(np.where(np.isfinite(cost), cost, np.inf), axis=0)
        cols = np.arange(n_o)
        tmin, dkm = T[best, cols] / 60, D[best, cols] / 1000
    else:
        sh = gravity_shares(cost, beta)
        ok = sh.sum(axis=0) > 0
        tmin = np.where(ok, np.nansum(np.where(sh > 0, T, 0) * sh, axis=0) / 60, np.inf)
        dkm = np.where(ok, np.nansum(np.where(sh > 0, D, 0) * sh, axis=0) / 1000, np.inf)
        best = np.argmax(sh, axis=0)
    mx = pd.DataFrame({"origin": np.tile(np.arange(n_o), n_d), "dest_id": np.repeat(np.arange(n_d), n_o),
                       "time_min": (T / 60).ravel(), "dist_km": (D / 1000).ravel()})
    if mode == "gravity":
        mx["share"] = gravity_shares(cost, beta).ravel()
    mx = mx.replace(np.inf, np.nan)
    return dict(time_min=np.where(np.isfinite(tmin), tmin, np.nan),
                dist_km=np.where(np.isfinite(dkm), dkm, np.nan), dest=best, matrix=mx)
