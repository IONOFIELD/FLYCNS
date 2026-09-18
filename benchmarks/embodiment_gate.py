"""
Gate check for a surrogate wingbeat loop (embodiment, version A).

DNp31 is the strongest descending input to the wing motor pool (3,019 excitatory synapses) and
is dominated by chordotonal and campaniform input, which reports self-generated movement. A
disembodied model cannot produce that input, so DNp31 never fires. The proposal is a SURROGATE
loop: no physics, just a wingbeat phase variable driving the proprioceptive afferents, with the
wing motor output feeding back to modulate it.

This script decides whether that is buildable at all. It answers four questions and stops if any
of them fails, because a loop built on unidentifiable afferents would be a guess dressed as a
model:

  0. NOTE (11 Sept 2026): they do not. The 851 campaniform and chordotonal afferents in MaleCNS
     v1.0 enter through ADMN (218), DMetaN (195), MetaLN (193), MesoLN (163), ProLN and ProCN
     (69): abdominal, thoracic and LEG nerves. No haltere nerve and no wing campaniform
     population appears. DNp31's proprioceptive dominance is therefore leg and body load
     sensing, not wingbeat feedback, and a surrogate WINGBEAT loop would drive the wrong
     afferents. The questions below still run, because a leg-load to flight-muscle loop is a
     different and possibly more interesting circuit, but the original premise is withdrawn.

  1. Do the wing and haltere mechanosensors exist as identifiable types in MaleCNS v1.0?
     MaleCNS annotates sensory `subclass`, including "campaniform sensilla" and
     "chordotonal organ"; this splits them by entry nerve, since haltere afferents enter
     through the haltere nerve and wing afferents through the wing nerve.
  2. Do they reach DNp31, and how strongly relative to its other inputs?
  3. Do they reach the wing motor pool directly or through premotor interneurons?
  4. Is DNp31's output positioned to modulate the same muscles whose sensors feed it, which is
     what makes it a loop rather than a chain?

Nothing here is simulated and nothing is written to the model. Output: results/embodiment/gate.json

Run:  python benchmarks/embodiment_gate.py [data_dir]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import load_graph
from flycns.bench import provenance
from flycns.graph import SIGN_MAP

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = Path("results/embodiment")
OUT.mkdir(parents=True, exist_ok=True)
WING_MN = r"^(DLMn|DVMn|b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
PROPRIO_SUBCLASSES = ["campaniform sensilla", "chordotonal organ"]

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna("")
sub = meta["subclass"].fillna("") if "subclass" in meta else pd.Series("", index=meta.index)
nerve = meta["entryNerve"].fillna("") if "entryNerve" in meta else pd.Series("", index=meta.index)
edges["sgn"] = edges["nt"].str.lower().map(SIGN_MAP).fillna(0)
report = dict(gate="embodiment_surrogate_loop", questions={})

# ---------------------------------------------------------------- Q1 identifiable afferents
print("=" * 72)
print("Q1: are the wing and haltere mechanosensors identifiable?")
print("=" * 72)
prop = meta.index[sub.isin(PROPRIO_SUBCLASSES)]
print(f"  proprioceptive afferents (campaniform + chordotonal): {len(prop)}")
if not len(prop):
    raise SystemExit("GATE FAILED: no proprioceptive subclass annotation in this dataset")

grp = (meta.loc[prop].assign(nerve=nerve.loc[prop], sc=sub.loc[prop])
       .groupby(["sc", "nerve"]).size().sort_values(ascending=False))
print("\n  by subclass and entry nerve:")
print(grp.head(14).to_string())
report["questions"]["q1_afferents"] = dict(
    n_total=int(len(prop)),
    by_subclass_nerve={f"{k[0]} | {k[1]}": int(v) for k, v in grp.items()},
    types_by_nerve={n_: sorted(meta.loc[[b for b in prop if nerve.loc[b] == n_], "type"].dropna().unique())[:12]
                    for n_ in sorted({x for x in nerve.loc[prop].unique() if x})})
for n_, types in report["questions"]["q1_afferents"]["types_by_nerve"].items():
    n_cells = int((nerve.loc[prop] == n_).sum())
    print(f"    nerve {n_:<8} {n_cells:>4} cells  {types[:6]}")

# ---------------------------------------------------------------- Q2 do they reach DNp31
print("\n" + "=" * 72)
print("Q2: do the proprioceptors reach DNp31, and how strongly?")
print("=" * 72)
dnp31 = meta.index[meta["type"] == "DNp31"]


def two_hop(src, targets, min_first=20):
    f = edges[edges.pre.isin(src)].groupby("post").weight.sum()
    f = f[f >= min_first]
    s = edges[edges.pre.isin(f.index)].assign(w2=lambda x: x.weight * x.pre.map(f))
    return float(s.groupby("post").w2.sum().reindex(targets).fillna(0).sum())


direct = int(edges[edges.pre.isin(prop) & edges.post.isin(dnp31)].weight.sum())
by_nerve = {}
for n_ in sorted({x for x in nerve.loc[prop].unique() if x}):
    src = [b for b in prop if nerve.loc[b] == n_]
    by_nerve[n_] = dict(n_afferents=len(src), two_hop_to_DNp31=two_hop(src, dnp31),
                        direct_to_DNp31=int(edges[edges.pre.isin(src) & edges.post.isin(dnp31)].weight.sum()))
    print(f"  nerve {n_:<8} {len(src):>4} afferents   two-hop {by_nerve[n_]['two_hop_to_DNp31']:>12,.0f}   "
          f"direct {by_nerve[n_]['direct_to_DNp31']:>5}")
report["questions"]["q2_to_DNp31"] = dict(direct_synapses=direct, by_nerve=by_nerve)
print(f"  direct proprioceptive synapses onto DNp31: {direct}")

# ---------------------------------------------------------------- Q3 do they reach the wing pool
print("\n" + "=" * 72)
print("Q3: do the proprioceptors reach the wing motor pool?")
print("=" * 72)
wing = meta.index[t.str.match(WING_MN)]
direct_mn = edges[edges.pre.isin(prop) & edges.post.isin(wing)]
first = edges[edges.pre.isin(prop)].groupby("post").weight.sum()
first = first[first >= 20]
premotor = edges[edges.pre.isin(first.index) & edges.post.isin(wing)]
prem_types = (premotor.assign(ty=lambda x: x.pre.map(meta["type"]), sw=lambda x: x.weight * x.sgn)
              .groupby("ty").sw.sum().sort_values(ascending=False).head(10))
print(f"  direct onto wing motor neurons: {int(direct_mn.weight.sum()):,} synapses")
print(f"  via first-order relays: {int(premotor.weight.sum()):,} synapses through "
      f"{premotor.pre.nunique()} interneurons")
print("\n  strongest relays onto wing motor neurons (signed):")
print(prem_types.astype(int).to_string())
report["questions"]["q3_to_wing_pool"] = dict(
    direct_synapses=int(direct_mn.weight.sum()),
    via_relays_synapses=int(premotor.weight.sum()),
    n_relay_interneurons=int(premotor.pre.nunique()),
    top_relays={k: int(v) for k, v in prem_types.items()})

# ---------------------------------------------------------------- Q4 is it a loop
print("\n" + "=" * 72)
print("Q4: is it a loop? DNp31's muscles vs the muscles whose sensors feed it")
print("=" * 72)
out31 = (edges[edges.pre.isin(dnp31) & edges.post.isin(wing)]
         .assign(ty=lambda x: x.post.map(meta["type"])).groupby("ty").weight.sum().sort_values(ascending=False))
sens_mn = (pd.concat([direct_mn, premotor]).assign(ty=lambda x: x.post.map(meta["type"]))
           .groupby("ty").weight.sum().sort_values(ascending=False))
shared = sorted(set(out31.index) & set(sens_mn.index))
print(f"  DNp31 drives {len(out31)} wing motor types; proprioceptors reach {len(sens_mn)}; "
      f"shared: {len(shared)}")
tab = pd.DataFrame({"DNp31_drives": out31, "proprioceptors_reach": sens_mn}).fillna(0).astype(int)
print(tab.sort_values("DNp31_drives", ascending=False).head(12).to_string())
report["questions"]["q4_loop_closure"] = dict(
    dnp31_targets={k: int(v) for k, v in out31.items()},
    proprioceptor_targets={k: int(v) for k, v in sens_mn.items()},
    shared_motor_types=shared,
    loop_closed=bool(len(shared) >= 3))

# ---------------------------------------------------------------- verdict
q1 = len(prop) > 0
q2 = report["questions"]["q2_to_DNp31"]["direct_synapses"] > 0 or \
     max((v["two_hop_to_DNp31"] for v in by_nerve.values()), default=0) > 0
q3 = report["questions"]["q3_to_wing_pool"]["via_relays_synapses"] > 0
q4 = report["questions"]["q4_loop_closure"]["loop_closed"]
report["verdict"] = dict(
    q1_afferents_identifiable=bool(q1), q2_reach_DNp31=bool(q2),
    q3_reach_wing_pool=bool(q3), q4_loop_closes=bool(q4),
    buildable=bool(q1 and q2 and q3 and q4),
    next_step=("If buildable: the surrogate needs firing rates for wing and haltere campaniform "
               "afferents during flight, from the literature, with the wingbeat phase relationship. "
               "Without a cited rate the loop is a guess and should not be built. Fenton/Dickinson "
               "haltere campaniform work and Dickerson et al. on wing campaniform fields are the "
               "places to look. If not buildable: record which question failed and stop."))
(OUT / "gate.json").write_text(json.dumps(report, indent=2, default=float))
print("\n" + "=" * 72)
for k, v in report["verdict"].items():
    if isinstance(v, bool):
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"\n  BUILDABLE: {report['verdict']['buildable']}")
print(f"\nwrote {OUT / 'gate.json'}")
