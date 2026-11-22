"""Tracing-status audit of every benchmark readout / driven cell. Read-only; writes only into this folder.

The cell sets are exactly the ones fit/audit_stimuli.py prints before "ALL SETS RESOLVE" (setup.cmd ->
scripts/setup.py -> fit/audit_stimuli.py data). That script runs at import time and exits, so its SETS
dict is rebuilt here from the same source lines (AST-extracted, not retyped).

Usage (from the repo root): .venv\\Scripts\\python.exe explore\\status\\status_audit.py
"""
import ast
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from flycns.protocols import LOOM_TUNING  # noqa: E402,F401
from flycns.graph import ELECTRICAL_SYNAPSES, GUSTATORY_MN9_DRIVING, PEPTIDE_MODULATION, afferents_by_subclass  # noqa: E402,F401

RATIO_FLAG = 3.0
n = pd.read_parquet(ROOT / "data" / "neurons.parquet")
e = pd.read_parquet(ROOT / "data" / "edges.parquet", columns=["post", "weight"])
types = set(n["type"].dropna())

# --- SETS from fit/audit_stimuli.py, evaluated in its own namespace ------------------------------------
src = (ROOT / "fit" / "audit_stimuli.py").read_text(encoding="utf-8")
node = next(s for s in ast.parse(src).body if isinstance(s, ast.Assign) and getattr(s.targets[0], "id", "") == "SETS")
SETS = eval(compile(ast.Expression(node.value), "audit_stimuli.SETS", "eval"),
            {"LOOM_TUNING": LOOM_TUNING, "afferents_by_subclass": afferents_by_subclass, "n": n, "types": types,
             "GUSTATORY_MN9_DRIVING": GUSTATORY_MN9_DRIVING, "PEPTIDE_MODULATION": PEPTIDE_MODULATION,
             "ELECTRICAL_SYNAPSES": ELECTRICAL_SYNAPSES, "os": os, "sorted": sorted, "list": list})
type_sets = {}
for name, members in SETS.items():
    for t in dict.fromkeys(members):
        if t and not str(t).endswith("*") and t in types:
            type_sets.setdefault(t, []).append(name)

# --- 1. status table -----------------------------------------------------------------------------------
status_all = n["status"].fillna("<missing>").value_counts()
status_all.rename_axis("status").reset_index(name="cells").to_csv(OUT / "status_table.csv", index=False)

# --- 2. per-cell table ---------------------------------------------------------------------------------
edge_in = e.groupby("post")["weight"].sum()
c = n[n["type"].isin(type_sets)].copy()
c["status"] = c["status"].fillna("<missing>")
suffix = c["instance"].fillna("").str.extract(r"_(L|R)$")[0]
c["side"] = c["somaSide"].where(c["somaSide"].isin(["L", "R"]), suffix).fillna("none")
c["input_post"] = c["post"].astype(int)
c["input_edges_ge5"] = c["bodyId"].map(edge_in).fillna(0).astype(int)
c["sets"] = c["type"].map(lambda t: "; ".join(type_sets[t]))
cells = c[["bodyId", "type", "instance", "side", "status", "input_post", "input_edges_ge5", "superclass", "sets"]] \
    .sort_values(["type", "side", "bodyId"])
cells.to_csv(OUT / "cells.csv", index=False)


def ratio(a, b):
    lo, hi = min(a, b), max(a, b)
    return float("inf") if lo == 0 and hi > 0 else (hi / lo if lo else np.nan)


# --- 3. bilateral pairs ---------------------------------------------------------------------------------
pairs, types_lr = [], []
for t, g in cells.groupby("type"):
    L, R = g[g["side"] == "L"], g[g["side"] == "R"]
    if len(L) == 1 and len(R) == 1:  # a true one-to-one pair
        l, r = L.iloc[0], R.iloc[0]
        rr = l["input_post"] / r["input_post"] if r["input_post"] else float("inf")
        pairs.append({"type": t, "L_bodyId": int(l["bodyId"]), "R_bodyId": int(r["bodyId"]),
                      "L_status": l["status"], "R_status": r["status"],
                      "L_input": int(l["input_post"]), "R_input": int(r["input_post"]),
                      "L_over_R": rr, "max_over_min": ratio(l["input_post"], r["input_post"]),
                      "L_input_ge5": int(l["input_edges_ge5"]), "R_input_ge5": int(r["input_edges_ge5"]),
                      "max_over_min_ge5": ratio(l["input_edges_ge5"], r["input_edges_ge5"]),
                      "sets": l["sets"]})
    if len(L) and len(R):  # side-level comparison for every type present on both sides
        lm, rm = L["input_post"].mean(), R["input_post"].mean()
        types_lr.append({"type": t, "n_L": len(L), "n_R": len(R), "n_other_side": int(len(g) - len(L) - len(R)),
                         "mean_input_L": lm, "mean_input_R": rm, "L_over_R": lm / rm if rm else float("inf"),
                         "max_over_min": ratio(lm, rm),
                         "non_traced": int((g["status"] != "Traced").sum()), "sets": g["sets"].iloc[0]})
pairs = pd.DataFrame(pairs)
types_lr = pd.DataFrame(types_lr)
pairs["flag_ratio"] = pairs["max_over_min"] > RATIO_FLAG
pairs["flag_status"] = (pairs["L_status"] != "Traced") | (pairs["R_status"] != "Traced")
pairs["flagged"] = pairs["flag_ratio"] | pairs["flag_status"]
pairs.sort_values("max_over_min", ascending=False).to_csv(OUT / "pairs.csv", index=False)
types_lr["flag_ratio"] = types_lr["max_over_min"] > RATIO_FLAG
types_lr.sort_values("max_over_min", ascending=False).to_csv(OUT / "types_by_side.csv", index=False)

# within multi-cell types: cells whose input is > 3x off the median of the same type and side
cells["type_side_median"] = cells.groupby(["type", "side"])["input_post"].transform("median")
cells["n_type_side"] = cells.groupby(["type", "side"])["bodyId"].transform("size")
off = cells[(cells["n_type_side"] >= 3) &
            ((cells["input_post"] > RATIO_FLAG * cells["type_side_median"]) |
             (cells["input_post"] < cells["type_side_median"] / RATIO_FLAG))]
off.to_csv(OUT / "within_type_outliers.csv", index=False)
nontraced = cells[cells["status"] != "Traced"]
nontraced.to_csv(OUT / "non_traced_cells.csv", index=False)

# --- summary --------------------------------------------------------------------------------------------
flag = pairs[pairs["flagged"]].sort_values("max_over_min", ascending=False)
res = {"status_all_cells": status_all.to_dict(),
       "n_sets": len(SETS), "n_types": len(type_sets), "n_cells": int(len(cells)),
       "status_benchmark_cells": cells["status"].value_counts().to_dict(),
       "n_one_to_one_pairs": int(len(pairs)), "n_pairs_flagged": int(len(flag)),
       "n_pairs_flag_ratio": int(pairs["flag_ratio"].sum()), "n_pairs_flag_status": int(pairs["flag_status"].sum()),
       "n_types_both_sides": int(len(types_lr)), "n_types_side_mean_ratio_gt3": int(types_lr["flag_ratio"].sum()),
       "n_non_traced_cells": int(len(nontraced)), "n_within_type_outliers": int(len(off)),
       "MN9": pairs[pairs["type"] == "MN9"].to_dict("records")}
json.dump(res, open(OUT / "status_audit.json", "w", encoding="utf-8"), indent=1, default=str)

L = ["# Tracing-status audit", "",
     "Total input = `post` column of data\\neurons.parquet (all postsynaptic sites); `ge5` = summed weight of incoming",
     "edges in data\\edges.parquet (connections of >= 5 synapses). Pair = a type with exactly one L and one R cell (side",
     "from somaSide, else instance suffix). Flag: max/min input > 3, or either cell's status not `Traced`.", "",
     "## Status, all cells", "", "| status | cells |", "|---|---|"]
L += [f"| {k} | {v:,} |" for k, v in status_all.items()]
L += ["", f"## Benchmark cells: {len(SETS)} sets, {len(type_sets)} types, {len(cells):,} cells", "", "| status | cells |", "|---|---|"]
L += [f"| {k} | {v:,} |" for k, v in cells["status"].value_counts().items()]
L += ["", f"## Flagged one-to-one pairs ({len(flag)} of {len(pairs)})", "",
      "| type | L bodyId | R bodyId | L status | R status | L input | R input | max/min | ge5 L | ge5 R | ge5 max/min | sets |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for _, p in flag.iterrows():
    L.append(f"| {p['type']} | {p['L_bodyId']} | {p['R_bodyId']} | {p['L_status']} | {p['R_status']} | {p['L_input']:,} | "
             f"{p['R_input']:,} | {p['max_over_min']:.2f} | {p['L_input_ge5']:,} | {p['R_input_ge5']:,} | "
             f"{p['max_over_min_ge5']:.2f} | {p['sets']} |")
tl = types_lr[types_lr["flag_ratio"] & ((types_lr["n_L"] > 1) | (types_lr["n_R"] > 1))]
L += ["", f"## Multi-cell types with side-mean input ratio > 3 ({len(tl)})", "",
      "| type | n L | n R | mean L | mean R | max/min | non-Traced |", "|---|---|---|---|---|---|---|"]
for _, t in tl.sort_values("max_over_min", ascending=False).iterrows():
    L.append(f"| {t['type']} | {t['n_L']} | {t['n_R']} | {t['mean_input_L']:.0f} | {t['mean_input_R']:.0f} | {t['max_over_min']:.2f} | {t['non_traced']} |")
L += ["", f"## Non-Traced benchmark cells ({len(nontraced)}), by type and status", "", "| type | status | cells |", "|---|---|---|"]
for (t, s), k in nontraced.groupby(["type", "status"]).size().sort_values(ascending=False).items():
    L.append(f"| {t} | {s} | {k} |")
L += ["", f"Within-type outliers (cell input > 3x off its type+side median, groups of >= 3): {len(off)} cells, "
      "see within_type_outliers.csv.", "",
      "Files: status_table.csv, cells.csv (every benchmark cell), pairs.csv, types_by_side.csv, non_traced_cells.csv, "
      "within_type_outliers.csv, status_audit.json."]
(OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
