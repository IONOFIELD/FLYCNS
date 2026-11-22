"""V7a feasibility on the real MaleCNS data. Read-only; writes only into this folder.

Usage (from the repo root): .venv\\Scripts\\python.exe -I explore\\v7a\\v7a_feasibility.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FLOOR = 5
GLOMS = ["DM4", "DL5", "VM7d", "VM7v", "DM1"]  # VM7 is split into VM7d and VM7v in this dataset

n = pd.read_parquet(ROOT / "data" / "neurons.parquet")
e = pd.read_parquet(ROOT / "data" / "edges.parquet")
ct = json.load(open(ROOT / "data" / "gen6_phaseA_celltypes.json", encoding="utf-8"))
ALPN, ALLN = set(ct["classes"]["ALPN"]), set(ct["classes"]["ALLN"])

n["type"] = n["type"].fillna("")
n["side"] = n["instance"].fillna("").str.extract(r"_(L|R|unknown)$")[0].fillna("none")
typ = n.set_index("bodyId")["type"]
side = n.set_index("bodyId")["side"]
e = e.assign(pre_type=e["pre"].map(typ).fillna(""), post_type=e["post"].map(typ).fillna(""))
e5 = e[e["weight"] >= FLOOR]


def side_counts(types):
    s = n[n["type"].isin(types)]
    out = {}
    for t, g in s.groupby("type"):
        out[t] = {k: int(v) for k, v in g["side"].value_counts().sort_index().items()} | {"total": int(len(g))}
    return out


def edges_from_to(df, pre_types, post_types):
    return df[df["pre_type"].isin(pre_types) & df["post_type"].isin(post_types)]


result = {"floor_synapses": FLOOR, "glomeruli": {}}
rows = []
for gl in GLOMS:
    orn_types = sorted(t for t in n["type"].unique() if t == f"ORN_{gl}" or t.startswith(f"ORN_{gl}_"))
    pn_types = sorted(t for t in n["type"].unique() if t.startswith(gl) and not t.startswith(f"{gl}_ORN"))
    pn_in_alpn = {t: (t in ALPN) for t in pn_types}
    pn_cells = n[n["type"].isin(pn_types)][["bodyId", "type", "instance", "side", "post"]]

    m = edges_from_to(e5, orn_types, pn_types)
    per_pn = (m.assign(orn_side=m["pre"].map(side))
                .pivot_table(index="post", columns="orn_side", values="weight", aggfunc="sum", fill_value=0))
    per_pn_rows = []
    for _, c in pn_cells.sort_values(["type", "instance"]).iterrows():
        r = per_pn.loc[c["bodyId"]] if c["bodyId"] in per_pn.index else pd.Series(dtype=int)
        tot = int(r.sum()) if len(r) else 0
        per_pn_rows.append({"bodyId": int(c["bodyId"]), "type": c["type"], "instance": c["instance"],
                            "orn_syn": tot, "from_orn_L": int(r.get("L", 0)), "from_orn_R": int(r.get("R", 0)),
                            "from_orn_unknown": int(r.get("unknown", 0)),
                            "n_orn_partners": int(m[m["post"] == c["bodyId"]]["pre"].nunique()),
                            "total_post": int(c["post"]),
                            "orn_share_of_input": (tot / c["post"]) if c["post"] else None})
    any_pn = edges_from_to(e5, orn_types, ALPN)
    ln = edges_from_to(e5, orn_types, ALLN)
    ln_by_type = ln.groupby("post_type")["weight"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    n_pn = len(pn_cells)
    g = {
        "orn_types": side_counts(orn_types),
        "pn_types": side_counts(pn_types),
        "pn_type_in_ALPN_list": pn_in_alpn,
        "orn_to_pn": {"edges": int(len(m)), "synapses": int(m["weight"].sum()), "n_pn_cells": n_pn,
                      "synapses_per_pn": (float(m["weight"].sum()) / n_pn) if n_pn else None,
                      "per_pn": per_pn_rows},
        "orn_to_any_ALPN": {"edges": int(len(any_pn)), "synapses": int(any_pn["weight"].sum()),
                            "by_post_type_top10": {k: int(v) for k, v in any_pn.groupby("post_type")["weight"].sum()
                                                   .sort_values(ascending=False).head(10).items()}},
        "orn_to_ln": {"edges": int(len(ln)), "synapses": int(ln["weight"].sum()),
                      "n_ln_cells": int(ln["post"].nunique()),
                      "by_ln_type": {k: {"synapses": int(r["sum"]), "edges": int(r["count"])}
                                     for k, r in ln_by_type.iterrows()}},
    }
    result["glomeruli"][gl] = g
    for t, c in g["orn_types"].items():
        rows.append({"glomerulus": gl, "role": "ORN", "type": t, **c})
    for t, c in g["pn_types"].items():
        rows.append({"glomerulus": gl, "role": "PN", "type": t, **c})

# VM7 combined (d + v)
vm = [result["glomeruli"][k] for k in ("VM7d", "VM7v")]
syn = sum(x["orn_to_pn"]["synapses"] for x in vm)
npn = sum(x["orn_to_pn"]["n_pn_cells"] for x in vm)
result["VM7_combined_matched"] = {"orn_to_pn_synapses": syn, "n_pn_cells": npn, "synapses_per_pn": syn / npn,
                                  "orn_to_ln_synapses": sum(x["orn_to_ln"]["synapses"] for x in vm),
                                  "note": "sum of VM7d ORN->VM7d PN and VM7v ORN->VM7v PN; cross d<->v not included"}
cross = edges_from_to(e5, ["ORN_VM7d"], ["VM7v_adPN"])["weight"].sum(), edges_from_to(e5, ["ORN_VM7v"], ["VM7d_adPN"])["weight"].sum()
result["VM7_combined_matched"]["cross_d_to_v_pn"] = int(cross[0])
result["VM7_combined_matched"]["cross_v_to_d_pn"] = int(cross[1])

# STD-in scope
orn = n[n["type"].str.startswith("ORN_")]
hrn = n[n["type"].str.startswith("HRN_")]
targets = ALPN | ALLN
std = {"n_ORN_cells": int(len(orn)), "n_ORN_types": int(orn["type"].nunique()), "n_HRN_cells_excluded": int(len(hrn)),
       "ORN_side": {k: int(v) for k, v in orn["side"].value_counts().items()}}
for lab, df in (("all_edges", e), (f"edges_ge{FLOOR}", e5)):
    s = df[df["pre"].isin(orn["bodyId"]) & df["post_type"].isin(targets)]
    std[lab] = {"edges": int(len(s)), "synapses": int(s["weight"].sum()),
                "onto_ALPN": {"edges": int(s["post_type"].isin(ALPN).sum()),
                              "synapses": int(s[s["post_type"].isin(ALPN)]["weight"].sum())},
                "onto_ALLN": {"edges": int(s["post_type"].isin(ALLN).sum()),
                              "synapses": int(s[s["post_type"].isin(ALLN)]["weight"].sum())},
                "n_ORN_cells_with_edge": int(s["pre"].nunique()), "n_target_cells": int(s["post"].nunique())}
result["STD_in_scope"] = std

json.dump(result, open(OUT / "v7a.json", "w", encoding="utf-8"), indent=1)
pd.DataFrame(rows).to_csv(OUT / "cell_counts.csv", index=False)
pd.DataFrame([{"glomerulus": gl, **r} for gl, g in result["glomeruli"].items() for r in g["orn_to_pn"]["per_pn"]]) \
    .to_csv(OUT / "per_pn.csv", index=False)

# summary
L = [f"# V7a feasibility (MaleCNS, data\\neurons.parquet + data\\edges.parquet)", "",
     f"Synapse counts use edges with weight >= {FLOOR}. Side = instance suffix (_L/_R/_unknown); ORNs have no somaSide.",
     f"edges.parquet is already floored: min weight {int(e['weight'].min())}, so 'all_edges' and 'edges_ge5' below coincide.",
     "ORN→PN = ORN_<glom> onto PN types named <glom>…; ORN→LN = ORN_<glom> onto ALLN types (data\\gen6_phaseA_celltypes.json).", "",
     "| Glomerulus | ORN types (L/R/unk) | PN types (L/R) | ORN→PN syn | PN cells | syn/PN | ORN→LN syn | LN cells |",
     "|---|---|---|---|---|---|---|---|"]
for gl, g in result["glomeruli"].items():
    ot = "; ".join(f"{t} {c.get('L',0)}/{c.get('R',0)}/{c.get('unknown',0)}" for t, c in g["orn_types"].items())
    pt = "; ".join(f"{t} {c.get('L',0)}/{c.get('R',0)}" for t, c in g["pn_types"].items())
    p, l = g["orn_to_pn"], g["orn_to_ln"]
    L.append(f"| {gl} | {ot} | {pt} | {p['synapses']:,} | {p['n_pn_cells']} | {p['synapses_per_pn']:.0f} | {l['synapses']:,} | {l['n_ln_cells']} |")
L += ["", "## Per PN cell (ORN input from its own glomerulus)", "",
      "| Glom | Instance | bodyId | ORN syn | from ORN L / R / unk | ORN partners | total input | ORN share |", "|---|---|---|---|---|---|---|---|"]
for gl, g in result["glomeruli"].items():
    for r in g["orn_to_pn"]["per_pn"]:
        L.append(f"| {gl} | {r['instance']} | {r['bodyId']} | {r['orn_syn']:,} | {r['from_orn_L']} / {r['from_orn_R']} / {r['from_orn_unknown']} | "
                 f"{r['n_orn_partners']} | {r['total_post']:,} | {r['orn_share_of_input']:.2f} |")
L += ["", "## STD-in scope", "", "```", json.dumps(std, indent=1), "```"]
(OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
print(json.dumps(result["VM7_combined_matched"]))
for gl, g in result["glomeruli"].items():
    print(gl, "any ALPN:", g["orn_to_any_ALPN"]["synapses"], g["orn_to_any_ALPN"]["by_post_type_top10"])
    print(gl, "LN types:", list(g["orn_to_ln"]["by_ln_type"].items())[:6])
