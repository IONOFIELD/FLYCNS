"""MaleCNS vs FlyWire v783: synapses per cell on identically named cell types. Exploratory, read-only.

Inputs
  MaleCNS: data/neurons.parquet, data/edges.parquet (already only pairs of >= 5 synapses; every transmitter counts)
  FlyWire: <dl>/Supplemental_file1_neuron_annotations.tsv (flyconnectome/flywire_annotations, cell_type column)
           <dl>/proofread_connections_783.feather (Zenodo 10676866), summed over neuropils per (pre, post), then >= 5
Method
  matched type   = a MaleCNS `type` string equal to a FlyWire `cell_type` string, with >= 1 cell in each
  input per cell = sum of synapses on the type's incoming pairs (>= 5) / number of cells of the type (zeros included)
  output per cell likewise on outgoing pairs; partners of any type (typed or not) count
  ratio          = MaleCNS / FlyWire, per type; summarised as median and IQR per group (types with both sides > 0)
  groups         : ORN = type starts ORN_; AL PN = ALPN list; AL LN = ALLN list; Kenyon cell = Kenyon_Cell list
                   (data/gen6_phaseA_celltypes.json); rest = every other matched type
  AL->AL         : pairs whose pre and post types are both matched AL types (ORN, AL PN, AL LN); synapses / cells
  sensitivity    : MaleCNS also counted without partners whose superclass starts with "vnc" (FlyWire is brain only)

Usage (repo root): .venv\\Scripts\\python.exe -I explore\\density\\density_check.py explore\\density\\downloads_20261118
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DL = Path(sys.argv[1]).resolve()
FLOOR = 5

ct = json.load(open(ROOT / "data" / "gen6_phaseA_celltypes.json", encoding="utf-8"))["classes"]
ALPN, ALLN, KC = set(ct["ALPN"]), set(ct["ALLN"]), set(ct["Kenyon_Cell"])


def group(t):
    if t.startswith("ORN_"):
        return "ORN"
    if t in ALPN:
        return "AL PN"
    if t in ALLN:
        return "AL LN"
    if t in KC:
        return "Kenyon cell"
    return "rest of brain"


# ---- MaleCNS ----
mn = pd.read_parquet(ROOT / "data" / "neurons.parquet", columns=["bodyId", "type", "superclass"])
me = pd.read_parquet(ROOT / "data" / "edges.parquet", columns=["pre", "post", "weight"])
assert int(me["weight"].min()) >= FLOOR
m_type = mn.set_index("bodyId")["type"]
vnc = set(mn.loc[mn["superclass"].fillna("").str.startswith("vnc"), "bodyId"])

# ---- FlyWire ----
fa = pd.read_csv(DL / "Supplemental_file1_neuron_annotations.tsv", sep="\t", dtype=str,
                 usecols=["root_id", "cell_type", "super_class"])
fa["root_id"] = fa["root_id"].astype("int64")
fc = pd.read_feather(DL / "proofread_connections_783.feather", columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"])
fe = fc.groupby(["pre_pt_root_id", "post_pt_root_id"], as_index=False)["syn_count"].sum()
fe.columns = ["pre", "post", "weight"]
fw_pairs_all, fw_syn_all = len(fe), int(fe["weight"].sum())
fe = fe[fe["weight"] >= FLOOR]
f_type = fa.set_index("root_id")["cell_type"]


def per_type(neur_type, edges, drop_partners=frozenset()):
    """{type: (n_cells, in_per_cell, out_per_cell)} over typed cells."""
    typed = neur_type.dropna()
    typed = typed[typed != ""]
    e_in = edges if not drop_partners else edges[~edges["pre"].isin(drop_partners)]
    e_out = edges if not drop_partners else edges[~edges["post"].isin(drop_partners)]
    ins = e_in.groupby("post")["weight"].sum().reindex(typed.index, fill_value=0)
    outs = e_out.groupby("pre")["weight"].sum().reindex(typed.index, fill_value=0)
    df = pd.DataFrame({"type": typed.values, "in": ins.values, "out": outs.values})
    return df.groupby("type").agg(n=("in", "size"), inp=("in", "mean"), out=("out", "mean"))


M = per_type(m_type, me)
Mb = per_type(m_type, me, vnc)
F = per_type(f_type, fe)
common = sorted(set(M.index) & set(F.index))
T = pd.DataFrame({"type": common})
T["group"] = T["type"].map(group)
for tag, src in (("mcns", M), ("mcns_novnc", Mb), ("fw", F)):
    T[f"n_{tag}"] = T["type"].map(src["n"])
    T[f"in_{tag}"] = T["type"].map(src["inp"])
    T[f"out_{tag}"] = T["type"].map(src["out"])
for io in ("in", "out"):
    T[f"ratio_{io}"] = np.where(T[f"{io}_fw"] > 0, T[f"{io}_mcns"] / T[f"{io}_fw"].replace(0, np.nan), np.nan)
    T[f"ratio_{io}_novnc"] = np.where(T[f"{io}_fw"] > 0, T[f"{io}_mcns_novnc"] / T[f"{io}_fw"].replace(0, np.nan), np.nan)
T.to_csv(OUT / "by_type.csv", index=False)

GROUPS = ["ORN", "AL PN", "AL LN", "Kenyon cell", "rest of brain"]


def summ(x):
    x = x.replace([np.inf, -np.inf], np.nan).dropna()
    x = x[x > 0]
    if not len(x):
        return {"n_types": 0}
    q = np.percentile(x, [25, 50, 75])
    return {"n_types": int(len(x)), "median": float(q[1]), "q25": float(q[0]), "q75": float(q[2])}


groups = {}
for gname in GROUPS + ["all matched"]:
    sub = T if gname == "all matched" else T[T["group"] == gname]
    groups[gname] = {"n_types": int(len(sub)), "cells_mcns": int(sub["n_mcns"].sum()), "cells_fw": int(sub["n_fw"].sum()),
                     **{k: summ(sub[k]) for k in ("ratio_in", "ratio_out", "ratio_in_novnc", "ratio_out_novnc")}}
# AL non-ORN combined vs rest, for the "is the AL denser than the rest" question
al = T[T["group"].isin(["ORN", "AL PN", "AL LN"])]
groups["AL (ORN+PN+LN)"] = {"n_types": int(len(al)),
                            **{k: summ(al[k]) for k in ("ratio_in", "ratio_out", "ratio_in_novnc", "ratio_out_novnc")}}

# ---- AL -> AL among matched AL types ----
al_types = set(al["type"])
al_group = dict(zip(al["type"], al["group"]))


def al_al(neur_type, edges):
    pt, qt = edges["pre"].map(neur_type), edges["post"].map(neur_type)
    sel = pt.isin(al_types) & qt.isin(al_types)
    cells = int(neur_type.isin(al_types).sum())
    syn = float(edges.loc[sel, "weight"].sum())
    by = (edges.loc[sel].assign(g_pre=pt[sel].map(al_group), g_post=qt[sel].map(al_group))
          .groupby(["g_pre", "g_post"])["weight"].sum())
    cells_g = neur_type[neur_type.isin(al_types)].map(al_group).value_counts()
    return {"cells": cells, "pairs": int(sel.sum()), "synapses": syn, "synapses_per_cell": syn / cells if cells else None,
            "cells_by_group": {k: int(v) for k, v in cells_g.items()},
            "by_group_pair": {f"{a}->{b}": {"synapses": float(v), "per_post_cell": float(v) / int(cells_g.get(b, 1))}
                              for (a, b), v in by.items()}}


ALAL = {"MaleCNS": al_al(m_type, me), "FlyWire": al_al(f_type, fe)}
ALAL["ratio_synapses_per_cell"] = ALAL["MaleCNS"]["synapses_per_cell"] / ALAL["FlyWire"]["synapses_per_cell"]

# whole-dataset context
whole = {"MaleCNS": {"cells": int(len(mn)), "pairs_ge5": int(len(me)), "synapses_ge5": int(me["weight"].sum()),
                     "brain_cells_nonvnc": int(len(mn) - len(vnc))},
         "FlyWire": {"annotated_cells": int(len(fa)), "pairs_all": fw_pairs_all, "synapses_all": fw_syn_all,
                     "pairs_ge5": int(len(fe)), "synapses_ge5": int(fe["weight"].sum())}}
# AL (and each group) vs rest of brain: two-sided Mann-Whitney U on the per-type ratios
from scipy.stats import mannwhitneyu  # noqa: E402
rest = T[T["group"] == "rest of brain"]
tests = {}
for gname, sub in [("AL (ORN+PN+LN)", al)] + [(g, T[T["group"] == g]) for g in GROUPS[:4]]:
    for io in ("ratio_in", "ratio_out"):
        a, b = sub[io].dropna(), rest[io].dropna()
        a, b = a[a > 0], b[b > 0]
        tests[f"{gname} vs rest, {io}"] = {"median_group": float(a.median()), "median_rest": float(b.median()),
                                           "p_mannwhitney": float(mannwhitneyu(a, b).pvalue)}
res = {"floor": FLOOR, "matched_types": len(common), "mcns_types": int(len(M)), "fw_types": int(len(F)),
       "groups": groups, "AL_to_AL": ALAL, "group_vs_rest_tests": tests, "whole": whole}
json.dump(res, open(OUT / "results.json", "w", encoding="utf-8"), indent=1)

S = ["# MaleCNS vs FlyWire v783: synapses per cell on identically named types", "",
     f"Pairs with >= {FLOOR} synapses in both datasets (FlyWire summed over neuropils per pair first). "
     f"Matched types: {len(common):,} (MaleCNS typed {len(M):,}, FlyWire typed {len(F):,}). Ratio = MaleCNS / FlyWire per type.", "",
     "| group | types | cells MCNS / FW | input ratio median [IQR] | output ratio median [IQR] | input, no VNC partners | output, no VNC partners |",
     "|---|---|---|---|---|---|---|"]


def fmt(d):
    return f"{d['median']:.2f} [{d['q25']:.2f}–{d['q75']:.2f}] (n={d['n_types']})" if d.get("n_types") else "–"


for gname in GROUPS + ["AL (ORN+PN+LN)", "all matched"]:
    gg = groups[gname]
    cells = f"{gg.get('cells_mcns', ''):,} / {gg.get('cells_fw', ''):,}" if "cells_mcns" in gg else "–"
    S.append(f"| {gname} | {gg['n_types']} | {cells} | {fmt(gg['ratio_in'])} | {fmt(gg['ratio_out'])} | "
             f"{fmt(gg['ratio_in_novnc'])} | {fmt(gg['ratio_out_novnc'])} |")
S += ["", "## Group vs rest of brain (two-sided Mann–Whitney U on per-type ratios)", "",
      "| comparison | median group | median rest | p |", "|---|---|---|---|"]
S += [f"| {k} | {v['median_group']:.2f} | {v['median_rest']:.2f} | {v['p_mannwhitney']:.1e} |" for k, v in tests.items()]
S += ["", "## AL → AL among matched AL types", "",
      "| | AL cells | pairs | synapses | synapses per cell |", "|---|---|---|---|---|"]
for k in ("MaleCNS", "FlyWire"):
    a = ALAL[k]
    S.append(f"| {k} | {a['cells']:,} | {a['pairs']:,} | {a['synapses']:,.0f} | {a['synapses_per_cell']:.0f} |")
S += [f"", f"Ratio of AL→AL synapses per cell: {ALAL['ratio_synapses_per_cell']:.2f}.", "",
      "| pre → post | MaleCNS syn per post cell | FlyWire syn per post cell |", "|---|---|---|"]
for k in sorted(set(ALAL["MaleCNS"]["by_group_pair"]) | set(ALAL["FlyWire"]["by_group_pair"])):
    a = ALAL["MaleCNS"]["by_group_pair"].get(k, {}).get("per_post_cell", 0)
    b = ALAL["FlyWire"]["by_group_pair"].get(k, {}).get("per_post_cell", 0)
    S.append(f"| {k} | {a:,.0f} | {b:,.0f} |")
S += ["", "## Whole datasets", "", "```", json.dumps(whole, indent=1), "```"]
(OUT / "summary.md").write_text("\n".join(S) + "\n", encoding="utf-8")
print("\n".join(S))
for gname in GROUPS:
    print(gname, sorted(T.loc[T["group"] == gname, "type"])[:12])
