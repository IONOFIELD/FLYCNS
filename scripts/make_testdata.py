"""Tiny synthetic graph with the GF circuit types so the pipeline can be smoke-tested without MaleCNS."""
import numpy as np, pandas as pd
rng = np.random.default_rng(0)
rows, bid = [], 1000
def add(t, n, sc, side_alt=True, gen=None):
    global bid
    g = gen or rng
    for k in range(n):
        rows.append(dict(bodyId=bid, type=t, superclass=sc, somaSide=("L","R")[k%2] if side_alt else "L",
                         consensusNt="acetylcholine", x=g.normal(), y=g.normal(), z=g.normal()))
        bid += 1
for t in ["LC4","LPLC2","LC6","LC16","LC26","LPLC1","LC9","LC17","LC12"]: add(t, 20, "visual_projection")
add("DNp01", 2, "descending_neuron"); add("TTMn", 2, "vnc_motor"); add("PSI", 2, "vnc_intrinsic")
add("JO-A1", 20, "cb_sensory"); add("JO-B1_a", 20, "cb_sensory")   # JO-B1_a: a declared electrical partner of GF
add("Gr64f_sugar_GRN", 20, "cb_sensory"); add("Gr66a_bitter_GRN", 10, "cb_sensory")
add("GNG001", 4, "cb_intrinsic"); add("Bract", 4, "descending_neuron"); add("MN9", 2, "cb_motor")
add("JO-FV", 10, "cb_sensory"); add("aPhM2a", 5, "cb_sensory"); add("BM_Taste", 10, "cb_sensory")
add("pC1_1b", 2, "cb_intrinsic"); add("LC10a", 6, "visual_projection"); add("pC1_14a", 2, "cb_intrinsic"); add("pC1_13a", 2, "cb_intrinsic"); add("pC1_14b", 2, "cb_intrinsic"); add("pC1_15a", 2, "cb_intrinsic"); add("pC1_15b", 2, "cb_intrinsic"); add("pC1_15c", 2, "cb_intrinsic"); add("pC1_16a", 2, "cb_intrinsic"); add("pMP2", 2, "descending_neuron"); add("DNp13", 2, "descending_neuron"); add("pIP10", 2, "descending_neuron"); add("LB3a", 4, "cb_sensory"); add("LB1b", 3, "cb_sensory"); add("LB1c", 3, "cb_sensory"); add("LB1d", 3, "cb_sensory"); add("LB2a", 2, "cb_sensory"); add("LB2b", 2, "cb_sensory"); add("LB2c", 2, "cb_sensory"); add("MN6", 2, "cb_motor"); add("MN11D", 2, "cb_motor"); add("MN11V", 2, "cb_motor"); add("LB3b", 6, "cb_sensory"); add("LB3c", 6, "cb_sensory"); add("LB1a", 6, "cb_sensory"); add("LC11", 10, "visual_projection"); add("LC15", 10, "visual_projection"); add("LC18", 10, "visual_projection"); add("LC21", 10, "visual_projection"); add("L3", 20, "ol_intrinsic"); add("L5", 20, "ol_intrinsic"); add("DNg02_a", 3, "descending_neuron"); add("DNg02_b", 3, "descending_neuron"); add("SNpp16", 30, "vnc_sensory"); add("SNpp07", 20, "vnc_sensory"); add("DLMn c-f", 8, "vnc_motor"); add("b1 MN", 2, "vnc_motor"); add("IN19B043", 20, "vnc_intrinsic"); add("Pm3", 6, "ol_intrinsic"); add("Mi1", 20, "ol_intrinsic"); add("Tm2", 10, "ol_intrinsic")
add("filler", 300, "cb_intrinsic")
# types the chains below use; their own generator keeps every other random draw unchanged
_g2 = np.random.default_rng(1)
add("L1", 20, "ol_intrinsic", gen=_g2); add("L2", 20, "ol_intrinsic", gen=_g2); add("Fdg", 2, "cb_intrinsic", gen=_g2)
# Realism the real data has and the toy lacked (audit 2026-10-11, gap 11); a third generator, so every
# draw above is unchanged: the second JON->GF electrical partner, with fewer cells than JO-B1_a as in
# MaleCNS (6 vs 13), so the per-side compound calibration sees unequal populations.
_g3 = np.random.default_rng(2)
add("JO-B1_c", 6, "cb_sensory", gen=_g3)
n = pd.DataFrame(rows)
# Every transmitter label the model must handle, as the connectome spells them (mixed case) and
# missing, on the filler population: ACh, GABA and glutamate are signed; histamine is inhibitory;
# the amines are modulatory (unsigned); a missing label is unknown. Their outputs are dropped.
NT_LABELS = ["Acetylcholine", "GABA", "Glutamate", "histamine", "Dopamine", "octopamine", "Serotonin", None]
_fill = n.index[n.type == "filler"]
n.loc[_fill, "consensusNt"] = [NT_LABELS[i % len(NT_LABELS)] for i in range(len(_fill))]
n["subclass"] = None
n.loc[n.type.str.startswith("JO-A")|n.type.str.startswith("JO-B"), "subclass"] = "auditory"
n.loc[n.type=="JO-FV", "subclass"] = "wind_gravity"
n.loc[n.type.isin(["SNpp16","SNpp07"]), "subclass"] = "campaniform sensilla"
n["entryNerve"] = None
n.loc[n.type=="SNpp16", "entryNerve"] = "ADMN"; n.loc[n.type=="SNpp07", "entryNerve"] = "DMetaN"
n.loc[n.type.str.match(r"^LB[1-4]"), "subclass"] = "labellar bristle"; n.loc[n.type=="aPhM2a", "subclass"] = "pharyngeal sensillum"; n.loc[n.type=="Gr64f_sugar_GRN", "subclass"] = "taste peg"
n.loc[n.type.str.startswith("JO-") | n.type.str.contains("GRN"), "somaSide"] = None
n["instance"] = n.type + "_" + n.somaSide.fillna(pd.Series(["L","R"]*(len(n)//2+1))[:len(n)].set_axis(n.index))
n.loc[n.type.str.startswith("JO-"), "instance"] = None
e = []
gf = n[n.type=="DNp01"].bodyId.values
for b in n[n.type.isin(["LC4","LPLC2","LC6"])].bodyId: 
    for g in gf: e.append(dict(pre=b, post=g, weight=int(rng.integers(60,120)), nt="acetylcholine"))
def chain(pre_t, post_t, w, contra=False):
    for a in n[n.type==pre_t].itertuples():
        for b in n[n.type==post_t].itertuples():
            if contra and a.somaSide == b.somaSide: continue
            e.append(dict(pre=a.bodyId, post=b.bodyId, weight=w, nt="acetylcholine"))
chain("pC1_1b","DNp13",40); chain("LC10a","pC1_1b",30); chain("pC1_14a","pMP2",60); chain("pC1_13a","pMP2",30); chain("pC1_15a","DNp13",30); chain("LB2a","MN11D",20); chain("LB3a","GNG001",20); chain("GNG001","MN6",40); chain("LB3b","GNG001",40); chain("LB3c","GNG001",40); chain("L3","Mi1",30); chain("L5","Mi1",30); chain("LC11","DNp01",5); chain("DNg02_a","DLMn c-f",30); chain("DNg02_b","DLMn c-f",30); chain("SNpp16","IN19B043",40); chain("SNpp07","IN19B043",30); chain("IN19B043","DLMn c-f",25); chain("SNpp16","b1 MN",60); chain("L1","Mi1",30); chain("Pm3","Mi1",20); chain("L2","Pm3",30); chain("Gr64f_sugar_GRN", "GNG001", 120); chain("aPhM2a", "GNG001", 150); chain("BM_Taste", "GNG001", 60); chain("GNG001", "MN9", 400, contra=True); chain("Bract", "MN9", 400)
for a in n[n.type=="Gr66a_bitter_GRN"].bodyId:
    for b in n[n.type=="Fdg"].bodyId: e.append(dict(pre=a, post=b, weight=40, nt="gaba"))
for a in n[n.type=="JO-B1_a"].bodyId[:5]:
    for g in gf: e.append(dict(pre=a, post=g, weight=100, nt="acetylcholine"))
for a in n[n.type=="JO-B1_c"].bodyId[:2]:
    for g in gf: e.append(dict(pre=a, post=g, weight=30, nt="acetylcholine"))
_nt = n.set_index("bodyId")["consensusNt"]
_fill_ids = set(n.bodyId[n.type == "filler"])
for i in range(3000):
    a, b = rng.choice(n.bodyId.values, 2, replace=False)
    w, t = int(rng.integers(5,10)), rng.choice(["acetylcholine","gaba"])
    if a in _fill_ids:                          # the fetch labels every edge with its sender's transmitter
        t = _nt[a].lower() if isinstance(_nt[a], str) else None
    e.append(dict(pre=a, post=b, weight=w, nt=t))
e = pd.DataFrame(e)
# the fetch also writes a legacy `sign` column the model must ignore (scripts/fetch_malecns.py)
e["sign"] = e["nt"].map({"acetylcholine": 1, "gaba": -1, "glutamate": -1})
# SEZ membership by anatomy, as fit/roi_membership.py writes it, so the anatomical SEZ path runs on the
# toy (without it every SEZ-dependent step silently took the name-prefix fallback)
sez = set(n.bodyId[n.type.isin(["GNG001", "Bract", "MN9", "Fdg"])]) | \
      set(_g3.choice(n.bodyId[n.type == "filler"].values, 30, replace=False))
roi = pd.DataFrame(dict(bodyId=n.bodyId.values))
roi["sez_frac"] = [0.9 if b in sez else float(_g3.uniform(0, 0.4)) for b in roi.bodyId]
roi["dominant_roi"] = np.where(roi.sez_frac > 0.5, "GNG", "SMP(R)")
roi["dominant_frac"] = np.maximum(roi.sez_frac, 1 - roi.sez_frac)
roi["n_syn"] = 100
import os
os.makedirs("testdata", exist_ok=True)   # git does not keep empty folders, so a fresh clone has none
e.to_parquet("testdata/edges.parquet", index=False); n.to_parquet("testdata/neurons.parquet", index=False)
roi[["bodyId", "dominant_roi", "dominant_frac", "sez_frac", "n_syn"]].to_parquet("testdata/roi_membership.parquet", index=False)
# the per-synapse transmitter table the targeted sign flip reads (fit/synapse_nt.py writes the real one):
# one row per connection, nt_agree the fraction of T-bars agreeing with the sender's label
nt = e[["pre", "post"]].drop_duplicates().reset_index(drop=True)
nt["nt_agree"] = _g3.random(len(nt))
nt.to_parquet("testdata/edges_nt.parquet", index=False)
print(len(n), "neurons", len(e), "edges", f"({e.nt.isna().sum()} unlabelled)", len(sez), "SEZ by anatomy")
