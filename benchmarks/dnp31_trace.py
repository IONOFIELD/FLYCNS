"""
What is DNp31, and can anything in this model drive it?

DNp31 is the strongest DESCENDING input to the wing motor pool in MaleCNS v1.0 (3,019 signed
synapses onto wing motor neurons, ahead of every other descending neuron; the larger inputs are
all VNC premotor interneurons). None of the four descending neurons on the ear-to-flight route
comes close. It was not on any of our shortlists, so this script asks three questions:

  1. What drives it? Its presynaptic partners by type, sign and modality.
  2. Two-hop weighted input from each sensory modality we can stimulate (auditory JO,
     wind/gravity JO, loom-sensitive LC types, gustatory afferents), the same measure used in
     benchmarks/auditory_wing_trace.py so the numbers are comparable.
  3. Where it lands: its postsynaptic targets in the cord, and which wing muscles those
     motor neurons serve.

Read-only apart from one short simulation at the end, which asks whether DNp31 fires under
measured loom drive. Writes results/dnp31/trace.json.

Run:  python benchmarks/dnp31_trace.py [data_dir]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import load_graph, CNSModel, LIFParams, loom_protocol
from flycns.bench import provenance
from flycns.graph import SIGN_MAP
from flycns.protocols import LOOM_TUNING, TUNING_SOURCE

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = Path("results/dnp31")
OUT.mkdir(parents=True, exist_ok=True)
WING_MN = r"^(DLMn|DVMn|b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
TARGET = "DNp31"

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna("")
sub = meta["subclass"].fillna("") if "subclass" in meta else pd.Series("", index=meta.index)
edges["sgn"] = edges["nt"].str.lower().map(SIGN_MAP).fillna(0)

ids = meta.index[meta["type"] == TARGET]
if not len(ids):
    raise SystemExit(f"{TARGET} not present in this dataset")
info = meta.loc[ids, ["instance", "somaSide", "consensusNt", "superclass"]]
report = dict(target=TARGET, n_cells=int(len(ids)), tuning_source=TUNING_SOURCE,
              cells=info.reset_index().to_dict("records"))
print(f"{TARGET}: {len(ids)} cells")
print(info.to_string())

# ---- 1. what drives it
inp = edges[edges.post.isin(ids)].assign(ty=lambda x: x.pre.map(meta["type"]),
                                         sc=lambda x: x.pre.map(meta["superclass"]).fillna(""),
                                         sw=lambda x: x.weight * x.sgn)
top_in = inp.groupby(["ty", "sc"]).sw.sum().sort_values(ascending=False)
exc_w = int(inp.loc[inp.sgn > 0, "weight"].sum())
inh_w = int(inp.loc[inp.sgn < 0, "weight"].sum())
report["input_balance"] = dict(excitatory=exc_w, inhibitory=inh_w, net=exc_w - inh_w)
report["top_inputs"] = [dict(type=k[0], superclass=k[1], signed_weight=int(v))
                        for k, v in list(top_in.head(12).items())]
print(f"\ninput balance: {exc_w:,} excitatory vs {inh_w:,} inhibitory (net {exc_w - inh_w:+,})")
print("\nstrongest inputs (signed):")
print(top_in.head(12).astype(int).to_string())

# ---- 2. modality, two-hop weighted, same measure as the ear-to-wing trace
def two_hop(src, min_first=20):
    f = edges[edges.pre.isin(src)].groupby("post").weight.sum()
    f = f[f >= min_first]
    s = edges[edges.pre.isin(f.index)].assign(w2=lambda x: x.weight * x.pre.map(f))
    return s.groupby("post").w2.sum()

MODALITIES = {
    "auditory (JO)": meta.index[t.str.startswith("JO-") & (sub == "auditory")],
    "wind/gravity (JO)": meta.index[t.str.startswith("JO-") & (sub == "wind_gravity")],
    "loom (LC types)": meta.index[t.isin(LOOM_TUNING)],
    "gustatory": meta.index[sub.isin(["labellar bristle", "taste peg", "pharyngeal sensillum"])],
    "leg/body bristle": meta.index[sub.isin(["mechanosensory bristle", "leg bristle", "wing bristle"])],
    "chordotonal / campaniform": meta.index[sub.isin(["chordotonal organ", "campaniform sensilla"])],
}
mod = {}
print("\ntwo-hop weighted input by modality:")
for name, src in MODALITIES.items():
    if not len(src):
        continue
    v = float(two_hop(src).reindex(ids).fillna(0).sum())
    mod[name] = v
    print(f"  {name:<28} {v:>14,.0f}   ({len(src)} afferents)")
report["modality_two_hop"] = mod
if mod:
    best = max(mod, key=mod.get)
    print(f"  -> dominant modality: {best}")
    report["dominant_modality"] = best

# ---- 3. where it lands
wing = meta.index[t.str.match(WING_MN)]
out = edges[edges.pre.isin(ids)].assign(ty=lambda x: x.post.map(meta["type"]),
                                        sc=lambda x: x.post.map(meta["superclass"]).fillna(""),
                                        sw=lambda x: x.weight * x.sgn)
report["top_outputs"] = [dict(type=k[0], superclass=k[1], signed_weight=int(v)) for k, v in
                         list(out.groupby(["ty", "sc"]).sw.sum().sort_values(ascending=False).head(12).items())]
print("\nstrongest outputs (signed):")
print(out.groupby(["ty", "sc"]).sw.sum().sort_values(ascending=False).head(12).astype(int).to_string())
onto_wing = out[out.post.isin(wing)]
by_muscle = onto_wing.groupby("ty").agg(signed=("sw", "sum"), synapses=("weight", "sum"))
report["onto_wing_motor"] = {k: dict(signed=int(v.signed), synapses=int(v.synapses))
                             for k, v in by_muscle.sort_values("synapses", ascending=False).iterrows()}
print(f"\nonto wing motor neurons, {int(onto_wing.weight.sum()):,} synapses total:")
print(by_muscle.sort_values("synapses", ascending=False).astype(int).to_string())

# ---- 4. does it fire under anything we can deliver
m = CNSModel(neurons, edges, list(LOOM_TUNING), LIFParams(), electrical=True)
loom_protocol(m, n_trials=6)
sp = m.spike_frame()
mine = set(m.lif_ids[m.readout_index(TARGET)])
wing_lif = set(m.lif_ids[[m.lif_index[b] for b in wing if b in m.lif_index.index]])
report["under_measured_loom"] = dict(n_trials=6, dnp31_spikes=int(sp.bodyId.isin(mine).sum()),
                                     wing_motor_spikes=int(sp.bodyId.isin(wing_lif).sum()))
print(f"\nunder measured loom drive (6 trials): {TARGET} {report['under_measured_loom']['dnp31_spikes']} spikes, "
      f"wing motor pool {report['under_measured_loom']['wing_motor_spikes']} spikes")

report["provenance"] = provenance()
(OUT / "trace.json").write_text(json.dumps(report, indent=2, default=float))
print(f"\nwrote {OUT / 'trace.json'}")
