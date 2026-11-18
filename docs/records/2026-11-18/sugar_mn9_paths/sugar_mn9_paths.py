"""Sugar (LB3b + LB3c) -> MN9 path analysis on the pinned data. Exploratory, read-only; writes only into this folder.

Graph: flycns.graph.load_graph("data") at the default floor (signed edges; unsigned dropped, amines dropped).
Mirror: fit/gen6_phaseA.py:mirror_mn9 applied to those edges (MN9_R's input replaced by the mirror of MN9_L's).

Definitions
  hop h of cell v (per target)  = length of the shortest directed path v -> target (target = hop 0)
  ds(v)                         = length of the shortest directed path from any sugar cell to v (sugar cell = 0)
  on a sugar path (hop h)       = ds(v) + h <= 4
  layer-h input                 = signed synapses on edges from hop-h cells into hop-(h-1) cells
  normalised weight of an edge  = synapses / the receiving cell's total signed input (sum over its in-edges)
  path score                    = product of the normalised weights along the path
Top paths: exact best-first search over simple paths of 1..4 edges that start at a sugar cell and end at the target.
Every factor is <= 1, so a partial path's score bounds all its extensions; a completed path popped from the heap
is therefore at least as good as anything not yet found.

Usage (from the repo root): .venv\\Scripts\\python.exe explore\\sugar_mn9_paths\\sugar_mn9_paths.py
"""
import hashlib
import heapq
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from flycns.graph import load_graph  # noqa: E402

# Loaded under a module name other than "gen6_phaseA": the file then sets REG = None and neither registers nor runs
# its clean-tree guard (fit/gen6_phaseA.py, module level), so importing it for mirror_mn9 writes nothing.
spec = importlib.util.spec_from_file_location("gen6_phaseA_readonly", ROOT / "fit" / "gen6_phaseA.py")
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)

MAXH = 4
TOPK = 10
SOURCE_TYPES = ["LB3b", "LB3c"]
TARGETS = {"MN9_L": 10331, "MN9_R": 16949}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


neurons, edges = load_graph("data")
meta = neurons.set_index("bodyId")
L, R = pa.mn9_cells(neurons)
assert (L, R) == (TARGETS["MN9_L"], TARGETS["MN9_R"]), (L, R)
sources = sorted(int(b) for b in meta.index[meta["type"].isin(SOURCE_TYPES)])
side = pa.side_of(neurons)


def label(b):
    inst = meta["instance"].get(b)
    return inst if isinstance(inst, str) else f"{meta['type'].get(b)}"


class G:
    def __init__(self, e):
        e = e[e["weight"] > 0]
        e = e.groupby(["pre", "post"], as_index=False).agg(weight=("weight", "sum"), sign=("sign", "first"))
        ids = np.union1d(e["pre"].to_numpy(), e["post"].to_numpy())
        self.ids = ids
        self.idx = {int(b): i for i, b in enumerate(ids)}
        pi = np.searchsorted(ids, e["pre"].to_numpy())
        qi = np.searchsorted(ids, e["post"].to_numpy())
        w = e["weight"].to_numpy(float)
        s = e["sign"].to_numpy(float)
        n = len(ids)
        self.n = n
        self.total_in = np.bincount(qi, weights=w, minlength=n)
        self.pi, self.qi, self.w, self.s = pi, qi, w, s
        self.nw = w / self.total_in[qi]
        # CSC by post: predecessors of each node
        order = np.lexsort((pi, qi))
        self.in_ptr = np.searchsorted(qi[order], np.arange(n + 1))
        self.in_pre, self.in_w, self.in_s, self.in_nw = pi[order], w[order], s[order], self.nw[order]
        self.A = sp.csr_matrix((np.ones(len(pi), dtype=np.int8), (pi, qi)), shape=(n, n))
        self.AT = self.A.T.tocsr()

    def bfs(self, starts, M, maxd):
        d = np.full(self.n, -1, dtype=np.int64)
        st = [self.idx[b] for b in starts if b in self.idx]
        d[st] = 0
        front = np.zeros(self.n, dtype=bool)
        front[st] = True
        for k in range(1, maxd + 1):
            nxt = (M.T @ front.astype(np.int8)) > 0 if False else np.asarray(M[front].sum(axis=0)).ravel() > 0
            nxt &= d < 0
            d[nxt] = k
            front = nxt
            if not front.any():
                break
        return d


def analyse(g, tgt_id, ds):
    t = g.idx[tgt_id]
    dh = g.bfs([tgt_id], g.AT, MAXH)            # hops to target (reverse graph)
    res = {"bodyId": tgt_id, "total_signed_input": float(g.total_in[t]),
           "shortest_hops_from_sugar": int(ds[t]) if ds[t] >= 0 else None}
    sugar_ok = (ds >= 0)
    layers = []
    for h in range(1, MAXH + 1):
        at = dh == h
        on = at & sugar_ok & (ds + h <= MAXH)
        sel = (dh[g.pi] == h) & (dh[g.qi] == h - 1)
        sel_on = sel & on[g.pi]
        row = {"hop": h, "cells": int(at.sum()), "cells_on_sugar_path": int(on.sum()),
               "sugar_cells_at_hop": int((at & (ds == 0)).sum())}
        for tag, m in (("all", sel), ("on_sugar_path", sel_on)):
            row[f"exc_{tag}"] = float(g.w[m & (g.s > 0)].sum())
            row[f"inh_{tag}"] = float(g.w[m & (g.s < 0)].sum())
            row[f"edges_{tag}"] = int(m.sum())
        layers.append(row)
    res["layers"] = layers
    # direct input into the target, split by whether the sender is on a sugar path (ds <= 3)
    a, b = g.in_ptr[t], g.in_ptr[t + 1]
    p, w, s = g.in_pre[a:b], g.in_w[a:b], g.in_s[a:b]
    on1 = (ds[p] >= 0) & (ds[p] <= MAXH - 1)
    res["direct_input"] = {"partners": int(b - a), "exc": float(w[s > 0].sum()), "inh": float(w[s < 0].sum()),
                           "from_sugar_path_partners": {"partners": int(on1.sum()), "exc": float(w[on1 & (s > 0)].sum()),
                                                        "inh": float(w[on1 & (s < 0)].sum())},
                           "from_sugar_cells": float(w[ds[p] == 0].sum())}
    res["top_paths"] = top_paths(g, t, ds)
    return res


def top_paths(g, t, ds):
    heap = [(-1.0, 0, (t,), 1.0)]   # (-score, tie, nodes head..target, sign)
    tie, found = 1, []
    popped = 0
    while heap and len(found) < TOPK:
        negsc, _, nodes, sg = heapq.heappop(heap)
        popped += 1
        k = len(nodes) - 1
        head = nodes[0]
        if k >= 1 and ds[head] == 0:
            found.append((-negsc, nodes, sg))
            if len(found) >= TOPK:
                break
        if k >= MAXH:
            continue
        a, b = g.in_ptr[head], g.in_ptr[head + 1]
        rem = MAXH - k - 1                        # hops still allowed before the new head
        for p, nw, s in zip(g.in_pre[a:b], g.in_nw[a:b], g.in_s[a:b]):
            if ds[p] < 0 or ds[p] > rem or p in nodes:
                continue
            heapq.heappush(heap, (negsc * nw, tie, (int(p),) + nodes, sg * s))
            tie += 1
    out = []
    for sc, nodes, sg in found:
        steps = []
        for u, v in zip(nodes[:-1], nodes[1:]):
            a, b = g.in_ptr[v], g.in_ptr[v + 1]
            j = a + int(np.nonzero(g.in_pre[a:b] == u)[0][0])
            steps.append({"pre": label(int(g.ids[u])), "post": label(int(g.ids[v])), "synapses": float(g.in_w[j]),
                          "sign": int(g.in_s[j]), "normalised": float(g.in_nw[j]),
                          "post_total_input": float(g.total_in[v])})
        out.append({"score": sc, "hops": len(nodes) - 1, "net_sign": int(sg),
                    "cells": [label(int(g.ids[x])) for x in nodes], "bodyIds": [int(g.ids[x]) for x in nodes],
                    "steps": steps})
    return {"paths": out, "heap_pops": popped}


def run(e, tag):
    g = G(e)
    ds = g.bfs(sources, g.A, MAXH)
    return {"graph": {"cells_in_graph": int(g.n), "edges": int(len(g.w)), "synapses": float(g.w.sum())},
            **{name: analyse(g, b, ds) for name, b in TARGETS.items()}}


res = {
    "commit": os.popen("git rev-parse HEAD").read().strip(),
    "data_sha256": {f: sha(ROOT / "data" / f) for f in ("neurons.parquet", "edges.parquet")},
    "graph_load": "flycns.graph.load_graph('data') defaults (floor 5, amines dropped, unsigned dropped)",
    "sources": {"types": SOURCE_TYPES, "n": len(sources),
                "by_type": meta.loc[sources, "type"].value_counts().to_dict(),
                "by_side": side.reindex(sources).fillna("none").value_counts().to_dict(),
                "in_graph": int(sum(b in set(edges["pre"]) | set(edges["post"]) for b in sources))},
    "targets": TARGETS,
}
res["observed"] = run(edges, "observed")
em, mlog = pa.mirror_mn9(edges, neurons, L, R)
res["mirror_log"] = {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v) for k, v in mlog.items()}
res["mirrored"] = run(em, "mirrored")
json.dump(res, open(OUT / "paths.json", "w", encoding="utf-8"), indent=1, default=str)

# ---- summary ----
S = ["# Sugar → MN9 paths (exploratory)", "",
     f"Commit `{res['commit']}`. data sha256: neurons `{res['data_sha256']['neurons.parquet'][:12]}…`, "
     f"edges `{res['data_sha256']['edges.parquet'][:12]}…`. Graph: {res['graph_load']}.",
     f"Sources: {res['sources']['n']} cells {res['sources']['by_type']} sides {res['sources']['by_side']}. "
     f"Targets MN9_L {L}, MN9_R {R}. Definitions are in the script's docstring.", ""]
for cond in ("observed", "mirrored"):
    gi = res[cond]["graph"]
    S += [f"## {cond} graph ({gi['cells_in_graph']:,} cells, {gi['edges']:,} edges)", ""]
    for name in TARGETS:
        r = res[cond][name]
        di = r["direct_input"]
        S += [f"### {name} ({r['bodyId']}): total signed input {r['total_signed_input']:,.0f}; shortest hops from sugar "
              f"= {r['shortest_hops_from_sugar']}",
              f"Direct input: {di['partners']} partners, +{di['exc']:,.0f} / −{di['inh']:,.0f}; from partners on a sugar path: "
              f"{di['from_sugar_path_partners']['partners']} partners, +{di['from_sugar_path_partners']['exc']:,.0f} / "
              f"−{di['from_sugar_path_partners']['inh']:,.0f}; straight from sugar cells: {di['from_sugar_cells']:,.0f}.", "",
              "| hop | cells | on sugar path | layer input exc / inh (all) | layer input exc / inh (on sugar path) |",
              "|---|---|---|---|---|"]
        for l in r["layers"]:
            S.append(f"| {l['hop']} | {l['cells']:,} | {l['cells_on_sugar_path']:,} | +{l['exc_all']:,.0f} / −{l['inh_all']:,.0f} | "
                     f"+{l['exc_on_sugar_path']:,.0f} / −{l['inh_on_sugar_path']:,.0f} |")
        S += ["", "| # | score | hops | sign | path (synapses, normalised) |", "|---|---|---|---|---|"]
        for i, p in enumerate(r["top_paths"]["paths"], 1):
            chain = p["steps"][0]["pre"] + "".join(
                f" →({st['synapses']:.0f}, {st['normalised']:.3f}{'' if st['sign'] > 0 else ', inh'}) {st['post']}" for st in p["steps"])
            S.append(f"| {i} | {p['score']:.2e} | {p['hops']} | {'+' if p['net_sign'] > 0 else '−'} | {chain} |")
        S.append("")
S += ["## Mirror log", "", "```", json.dumps(res["mirror_log"], indent=1, default=str), "```"]
(OUT / "summary.md").write_text("\n".join(S) + "\n", encoding="utf-8")
print("\n".join(S))
