"""
Auditory input to the wing motor system: a structural trace, not a benchmark.

WHY THIS IS NOT A BENCHMARK. The pathway exists in the wiring but the model cannot test
it: under measured loom drive (stationary amplitudes, Turner et al. 2022) the descending
neurons that carry it are silent and so is the entire wing motor pool, so a multisensory
test would compare zero against zero. This is the fourth circuit blocked by the absence of
cell-specific spontaneous activity (see RESULTS.md); it is recorded rather than tuned.

WHAT THE WIRING SHOWS (MaleCNS v1.0, this script):
  1. 114 Johnston's organ afferents are annotated subclass "auditory" (MaleCNS `subclass`;
     note this does NOT follow the JO-A/JO-B type split, JO-B2/B3/B4 are mostly
     wind_gravity). Their strongest first-order targets are SAD and WED types, consistent
     with the AMMC-to-wedge projection described for aPN1 (Vaughan et al. 2014;
     Tootoonian et al. 2012). No cell is named aPN1 or AMMC-B1 in this dataset.
  2. Wing motor neurons are driven almost entirely by VNC premotor interneurons
     (IN19B043, IN19B067, dMS2, AN19B001, IN19B075), not directly by descending neurons.
  3. Four descending neurons sit two hops from the auditory afferents AND project onto
     that premotor pool: DNp02, DNp06, DNp11 and DNg108. DNp01 (the giant fiber) does not
     (6 synapses), consistent with GF driving the tergotrochanteral jump muscle rather
     than steering (Tanouye & Wyman 1980; von Reyn et al. 2014).
  4. All four are LOOM-dominated in two-hop signed input by 3x to 32x, so the anatomy does
     not support a dedicated auditory-to-flight channel here; they are visual escape
     descending neurons that also receive auditory input.

Run:  python benchmarks/auditory_wing_trace.py [data_dir]
Writes results/auditory_wing/trace.json
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
OUT = Path("results/auditory_wing")
OUT.mkdir(parents=True, exist_ok=True)

WING_MN = r"^(DLMn|DVMn|b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
DNS = ["DNp02", "DNp06", "DNp11", "DNg108", "DNp01"]

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna("")
sub = meta["subclass"].fillna("") if "subclass" in meta else pd.Series("", index=meta.index)
edges["sgn"] = edges["nt"].str.lower().map(SIGN_MAP).fillna(0)

aud = meta.index[t.str.startswith("JO-") & (sub == "auditory")]
wind = meta.index[t.str.startswith("JO-") & (sub == "wind_gravity")]
loom = meta.index[t.isin(LOOM_TUNING)]
wing = meta.index[t.str.match(WING_MN)]
report = dict(benchmark="auditory_wing_trace", tuning_source=TUNING_SOURCE,
              n_auditory_afferents=int(len(aud)), n_wind_afferents=int(len(wind)),
              n_wing_motor=int(len(wing)))
print(f"auditory JO afferents {len(aud)}, wind/gravity {len(wind)}, wing motor neurons {len(wing)}")

# ---- 1. first-order targets of the auditory afferents
d = edges[edges.pre.isin(aud)].assign(ty=lambda x: x.post.map(meta["type"]))
first = (d.groupby("ty").agg(w=("weight", "sum"), cells=("post", "nunique"))
         .sort_values("w", ascending=False).head(12))
report["auditory_first_order"] = {k: dict(w=int(v.w), cells=int(v.cells)) for k, v in first.iterrows()}
print("\nfirst-order targets of auditory afferents:")
print(first.to_string())

# ---- 2. what drives the wing motor pool
inp = edges[edges.post.isin(wing)].assign(ty=lambda x: x.pre.map(meta["type"]),
                                          sw=lambda x: x.weight * x.sgn)
prem = inp.groupby("ty").sw.sum().sort_values(ascending=False).head(10)
report["wing_motor_drivers"] = {k: int(v) for k, v in prem.items()}
print("\nwing motor neuron input by presynaptic type (signed):")
print(prem.astype(int).to_string())

# ---- 3. do the candidate DNs reach the premotor pool
prem_types = list(prem.head(7).index)
prem_ids = meta.index[t.isin(prem_types)]
rows = []
for dn in DNS:
    src = meta.index[meta["type"] == dn]
    to_prem = int(edges[edges.pre.isin(src) & edges.post.isin(prem_ids)].weight.sum())
    to_mn = int(edges[edges.pre.isin(src) & edges.post.isin(wing)].weight.sum())
    rows.append(dict(dn=dn, onto_wing_premotor=to_prem, onto_wing_motor_direct=to_mn))
    print(f"  {dn:<8} -> wing premotor {to_prem:>6}   -> wing MN direct {to_mn:>6}")
report["dn_to_wing"] = rows

# ---- 4. modality dominance of those DNs (two-hop weight products)
def two_hop(src, min_first=20):
    f = edges[edges.pre.isin(src)].groupby("post").weight.sum()
    f = f[f >= min_first]
    s = edges[edges.pre.isin(f.index)].assign(w2=lambda x: x.weight * x.pre.map(f))
    return s.groupby("post").w2.sum()

a2, w2, l2 = two_hop(aud), two_hop(wind), two_hop(loom)
mod = []
print("\ntwo-hop weighted input by modality:")
for dn in DNS:
    ids = meta.index[meta["type"] == dn]
    va = float(a2.reindex(ids).fillna(0).sum())
    vw = float(w2.reindex(ids).fillna(0).sum())
    vl = float(l2.reindex(ids).fillna(0).sum())
    mod.append(dict(dn=dn, auditory=va, wind=vw, loom=vl,
                    loom_over_auditory=round(vl / va, 1) if va else None))
    print(f"  {dn:<8} auditory {va:>12,.0f}  wind {vw:>12,.0f}  loom {vl:>12,.0f}  "
          f"loom/auditory {vl / va:.1f}x" if va else f"  {dn}: no auditory input")
report["modality_dominance"] = mod

# ---- 5. and the reason this cannot be a benchmark: nothing fires
m = CNSModel(neurons, edges, list(LOOM_TUNING), LIFParams(), electrical=True)
trials = loom_protocol(m, n_trials=6)
sp = m.spike_frame()
fired = {}
for dn in DNS:
    ids = set(m.lif_ids[m.readout_index(dn)])
    fired[dn] = int(sp.bodyId.isin(ids).sum())
wing_ids = set(m.lif_ids[[m.lif_index[b] for b in wing if b in m.lif_index.index]])
n_wing_spikes = int(sp.bodyId.isin(wing_ids).sum())
report["under_measured_loom"] = dict(n_trials=6, dn_spikes=fired, wing_motor_spikes=n_wing_spikes,
                                     note=("nothing downstream of GF fires under physiological loom drive, "
                                           "so a multisensory test at the wing motor output would compare "
                                           "zero against zero; fourth circuit blocked by the absence of "
                                           "cell-specific spontaneous activity"))
print(f"\nunder measured loom drive (6 trials): DN spikes {fired}, wing motor spikes {n_wing_spikes}")

report["conclusion"] = (
    "The ear-to-flight route in MaleCNS v1.0 is four hops (auditory JO afferents -> SAD/WED relays -> "
    "DNp02/DNp06/DNp11/DNg108 -> VNC premotor interneurons -> wing motor neurons) and runs through "
    "descending neurons shared with the visual escape system rather than a dedicated auditory channel: "
    "all four are loom-dominated by 3x to 32x in two-hop signed input. The giant fiber does not "
    "participate (6 synapses onto the premotor pool), consistent with its role in the jump rather than "
    "steering. The model cannot test the pathway because none of those descending neurons, and no wing "
    "motor neuron, fires under measured loom drive.")
report["citations"] = [
    "Kamikouchi A, Inagaki HK, Effertz T, Hendrich O, Fiala A, Goepfert MC, Ito K (2009). The neural "
    "basis of Drosophila gravity-sensing and hearing. Nature 458:165-171. JO subgroup organisation and "
    "AMMC projection zones.",
    "Tootoonian S, Coen P, Kawadler JM, Murthy M (2012). Neural representations of courtship song in the "
    "Drosophila brain. J Neurosci 32:787-798. AMMC-A1/B1/B2 graded non-spiking sound responses; GF spikes "
    "to current injection and sound summates with subthreshold injection (Fig. 2D); AMMC-B1 cholinergic, "
    "B2 GABAergic.",
    "Vaughan AG, Zhou C, Manoli DS, Baker BS (2014). Neural pathways for the detection and discrimination "
    "of conspecific song in Drosophila melanogaster. Curr Biol 24:1039-1049. aPN1 (= AMMC-B1) necessary "
    "for behavioural song responses; AMMC-to-wedge projection.",
    "Tanouye MA, Wyman RJ (1980). Motor outputs of giant nerve fiber in Drosophila. J Neurophysiol "
    "44:405-421. GF drives TTM and, via PSI, DLM.",
    "von Reyn CR, Breads P, Peek MY, et al. (2014). A spike-timing mechanism for action selection. Nat "
    "Neurosci 17:962-970. GF escape behaviour and its visual drive.",
    "Turner MH, Krieger A, Pang MM, Clandinin TR (2022). Visual and motor signatures of locomotion "
    "dynamically shape a population code for feature detection in Drosophila. eLife 11:e82587. Source of "
    "the measured loom amplitudes used for the drive here.",
]
report["provenance"] = provenance()
(OUT / "trace.json").write_text(json.dumps(report, indent=2, default=float))
print(f"\nwrote {OUT / 'trace.json'}")
