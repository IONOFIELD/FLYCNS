"""Exploratory, read-only: synapses per cell, MaleCNS (data/) vs FlyWire v783, on cell types with the same name.
Goes into no score. Run from the repo root:  .venv\\Scripts\\python.exe -I explore\\density\\density.py
Reads explore/density/downloads/ (see sources.json); writes explore/density/{by_type.csv, results.json}."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "explore" / "density"
DL = OUT / "downloads"
FLOOR = 5
GROUPS = ["ORN", "AL PN", "AL LN", "Kenyon cell", "LH", "other brain"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def per_type(cells, pairs):
    """cells: bodyId -> type. pairs: pre, post, w (pair totals at/above the floor).
    Per type: cells, mean input and output synapses per cell (all partners, typed or not)."""
    tin = pairs.groupby("post")["w"].sum()
    tout = pairs.groupby("pre")["w"].sum()
    d = pd.DataFrame(dict(type=cells))
    d["in"] = tin.reindex(d.index).fillna(0).to_numpy()
    d["out"] = tout.reindex(d.index).fillna(0).to_numpy()
    g = d.groupby("type")
    return pd.DataFrame(dict(cells=g.size(), in_per_cell=g["in"].mean(), out_per_cell=g["out"].mean()))


def al_loop(cells, pairs, pn, ln):
    """Synapses between cells of the matched AL PN and AL LN types, per cell of those types."""
    cls = cells.map(lambda t: "PN" if t in pn else ("LN" if t in ln else None)).dropna()
    p = pairs[pairs["pre"].isin(cls.index) & pairs["post"].isin(cls.index)]
    a, b = p["pre"].map(cls), p["post"].map(cls)
    n = dict(PN=int((cls == "PN").sum()), LN=int((cls == "LN").sum()))
    out = dict(cells=n, total_synapses=float(p["w"].sum()), per_cell=float(p["w"].sum() / max(1, len(cls))))
    for s in ("PN", "LN"):
        for r in ("PN", "LN"):
            w = float(p.loc[(a == s) & (b == r), "w"].sum())
            out[f"{s}->{r}"] = dict(synapses=w, per_sender_cell=w / max(1, n[s]), per_cell=w / max(1, len(cls)))
    return out


def q(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return dict(n=0)
    return dict(n=int(len(x)), median=float(np.median(x)), q25=float(np.percentile(x, 25)),
                q75=float(np.percentile(x, 75)))


def main():
    # ---------------------------------------------------------------- MaleCNS (pinned data; every edge, any transmitter)
    n = pd.read_parquet(ROOT / "data" / "neurons.parquet")
    e = pd.read_parquet(ROOT / "data" / "edges.parquet", columns=["pre", "post", "weight"])
    assert int(e["weight"].min()) == FLOOR and not e.duplicated(["pre", "post"]).any()
    m_pairs = e.rename(columns={"weight": "w"})
    m_cells = n.dropna(subset=["type"]).set_index("bodyId")["type"].astype(str)

    # ---------------------------------------------------------------- FlyWire v783 (proofread neurons only)
    ann = pd.read_csv(DL / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False,
                      usecols=["root_id", "super_class", "cell_type"])
    ids = np.load(DL / "proofread_root_ids_783.npy")
    con = pd.read_feather(DL / "proofread_connections_783.feather",
                          columns=["pre_pt_root_id", "post_pt_root_id", "neuropil", "syn_count"])
    con = con.rename(columns={"pre_pt_root_id": "pre", "post_pt_root_id": "post", "syn_count": "w"})
    f_all = con.groupby(["pre", "post"], as_index=False)["w"].sum()          # per pair, over neuropils
    f_pairs = f_all[f_all["w"] >= FLOOR]
    al = con[con["neuropil"].isin(["AL_L", "AL_R"])].merge(f_pairs[["pre", "post"]], on=["pre", "post"])
    al = al.groupby(["pre", "post"], as_index=False)["w"].sum()             # the AL part of floor-passing pairs
    f_cells = ann[ann["root_id"].isin(ids)].dropna(subset=["cell_type"]).set_index("root_id")["cell_type"].astype(str)

    # ---------------------------------------------------------------- matching and groups
    ct = json.loads((ROOT / "data" / "gen6_phaseA_celltypes.json").read_text(encoding="utf-8"))["classes"]
    pn, ln, kc = set(ct["ALPN"]), set(ct["ALLN"]), set(ct["Kenyon_Cell"])

    def group(t):
        if t.startswith("ORN_"):
            return "ORN"
        if t in pn:
            return "AL PN"
        if t in ln:
            return "AL LN"
        if t in kc:
            return "Kenyon cell"
        if t.startswith("LH"):
            return "LH"
        return "other brain"

    M, F = per_type(m_cells, m_pairs), per_type(f_cells, f_pairs)
    shared = sorted(set(M.index) & set(F.index))
    T = M.loc[shared].add_prefix("malecns_").join(F.loc[shared].add_prefix("flywire_"))
    T["group"] = [group(t) for t in T.index]
    T["cell_ratio"] = T["malecns_cells"] / T["flywire_cells"]
    for k in ("in", "out"):
        f = T[f"flywire_{k}_per_cell"].replace(0, np.nan)
        T[f"ratio_{k}"] = T[f"malecns_{k}_per_cell"] / f
    T["count_consistent"] = T["cell_ratio"].between(2 / 3, 3 / 2)
    T.index.name = "type"

    def summarise(d):
        r = dict(types=int(len(d)))
        for k in ("in", "out"):
            r[f"ratio_{k}"] = q(d[f"ratio_{k}"])
            r[f"pooled_ratio_{k}"] = float((d[f"malecns_{k}_per_cell"] * d["malecns_cells"]).sum()
                                           / (d[f"flywire_{k}_per_cell"] * d["flywire_cells"]).sum()
                                           * d["flywire_cells"].sum() / d["malecns_cells"].sum())
            r[f"flywire_zero_{k}"] = int((d[f"flywire_{k}_per_cell"] == 0).sum())
        r["cell_ratio"] = q(d["cell_ratio"])
        return r

    res = dict(floor=FLOOR, matched_types=len(shared),
               malecns_types=int(M.shape[0]), flywire_types=int(F.shape[0]),
               all=summarise(T), all_count_consistent=summarise(T[T["count_consistent"]]),
               by_group={g: summarise(T[T["group"] == g]) for g in GROUPS},
               by_group_count_consistent={g: summarise(T[(T["group"] == g) & T["count_consistent"]]) for g in GROUPS},
               al_types_listed=dict(ALPN=len(pn), ALLN=len(ln), Kenyon_Cell=len(kc)),
               al_types_matched=dict(ALPN=int(T.index.isin(pn).sum()), ALLN=int(T.index.isin(ln).sum()),
                                     Kenyon_Cell=int(T.index.isin(kc).sum())),
               al_types_unmatched=dict(ALPN=sorted(pn - set(shared)), ALLN=sorted(ln - set(shared)),
                                       Kenyon_Cell=sorted(kc - set(shared))))
    mpn, mln = pn & set(shared), ln & set(shared)
    res["al_loop"] = dict(malecns=al_loop(m_cells, m_pairs, mpn, mln),
                          flywire=al_loop(f_cells, f_pairs, mpn, mln),
                          flywire_in_AL_neuropil_only=al_loop(f_cells, al, mpn, mln))
    res["al_loop"]["ratio_per_cell"] = res["al_loop"]["malecns"]["per_cell"] / res["al_loop"]["flywire"]["per_cell"]
    res["totals"] = dict(malecns_pairs=int(len(m_pairs)), malecns_synapses=float(m_pairs["w"].sum()),
                         flywire_pairs_all=int(len(f_all)), flywire_pairs_floor=int(len(f_pairs)),
                         flywire_synapses_floor=float(f_pairs["w"].sum()),
                         flywire_synapses_all=float(f_all["w"].sum()),
                         malecns_typed_cells=int(len(m_cells)), flywire_typed_cells=int(len(f_cells)))
    res["data"] = dict(malecns_edges_sha256=sha256(ROOT / "data" / "edges.parquet"),
                       malecns_neurons_sha256=sha256(ROOT / "data" / "neurons.parquet"),
                       celltypes_sha256=sha256(ROOT / "data" / "gen6_phaseA_celltypes.json"))
    T.round(4).to_csv(OUT / "by_type.csv", lineterminator="\n")
    (OUT / "results.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("al_types_unmatched",)}, indent=1))


if __name__ == "__main__":
    main()
