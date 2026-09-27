"""
Re-test of the feeding mechanism with taste afferents split by modality.

Why. The feeding benchmark's drive (GUSTATORY_MN9_DRIVING) mixed modalities. Tastekin, de Haan
Vicente et al. 2026 (Cell 189:5527-5551, Fig. 2) type the MaleCNS labellar GRNs and assign them by
driver-line anatomy: LB1a-d bitter (Gr33a), LB3a water (ppk28), LB3b and LB3c sugar (Gr64f; LB3b
also low salt, Ir56b), LB3d aversive high salt / heavy metal (Ir7c, ppk23, Ir47a), which they
propose inhibits attractive circuits through glutamate. Our "sugar proxy" contained LB3a-d, i.e.
water, sugar and an aversive type. The measured mechanism (afferents favour MN9's inhibitory
relays about 3:1; signed path products negative at two hops) was therefore made on mixed drive.
That paper's own effective connectivity is UNSIGNED and states that sign could change predicted
influence; this test is the signed complement.

Groups (exact MaleCNS type names; the script aborts if a scored group resolves to no neurons):
  sugar            LB3b, LB3c
  bitter           LB1a, LB1b, LB1c, LB1d
  water            LB3a
  aversive_salt    LB3d
  old_mixed_proxy  the previous GUSTATORY_MN9_DRIVING set, for direct comparison

Structural measures (deterministic, from the signed graph):
  ratio   synapses onto MN9's excitatory relays / onto its inhibitory relays
  hop_k   signed, input-normalised path product from the group to MN9 at k = 1..5 hops
          (the same measure as benchmarks/feeding_mechanism.py M3)

Dynamic measure: MN9 spikes per cell per 200 ms pulse, group driven at 50 and 100 Hz, 6 trials,
declared parameter set (no baseline, no regional gain).

CRITERIA, registered to results/feeding_by_modality/criteria.json before anything is computed:
  F1  decisive for the published feeding negative. If SUGAR alone has ratio >= 1.0 OR a positive
      signed product at 2 hops, the negative was an artefact of mixing modalities and is RETRACTED
      for feeding. Otherwise (ratio < 1.0 AND 2-hop product < 0) the negative is STRENGTHENED:
      it holds with a correctly assigned sugar drive.
  F2  valence is encoded in sign: sugar's ratio exceeds bitter's ratio.
  F3  dynamic: sugar alone at 100 Hz gives MN9 at least 0.5 spikes per cell per pulse.
  F4  dynamic valence: MN9 response to bitter at 100 Hz is below sugar's.
F1 is reported as a verdict (retract / strengthen), not as pass or fail, because either outcome is
informative. F2-F4 are scored.

Run:  python benchmarks/feeding_by_modality.py [n_trials] [data_dir]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import load_graph, CNSModel, LIFParams
from flycns.bench import pulse_protocol, readout_rates, provenance
from flycns.graph import SIGN_MAP, GUSTATORY_MN9_DRIVING

N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/feeding_by_modality")
OUT.mkdir(parents=True, exist_ok=True)
GROUPS = {
    "sugar": ["LB3b", "LB3c"],
    "bitter": ["LB1a", "LB1b", "LB1c", "LB1d"],
    "water": ["LB3a"],
    "aversive_salt": ["LB3d"],
    "old_mixed_proxy": list(GUSTATORY_MN9_DRIVING),
}
SCORED = ["sugar", "bitter"]
RATES = [50.0, 100.0]
CRITERIA = dict(
    source="Tastekin, de Haan Vicente et al. 2026, Cell 189:5527-5551, Fig. 2 (modality assignments)",
    groups=GROUPS,
    F1="verdict: sugar ratio >= 1.0 OR sugar hop_2 > 0 -> RETRACT feeding negative; else STRENGTHEN",
    F2="sugar ratio > bitter ratio",
    F3="sugar at 100 Hz: MN9 >= 0.5 spikes/cell/pulse",
    F4="bitter at 100 Hz: MN9 below sugar at 100 Hz",
    n_trials=N_TRIALS, rates_hz=RATES)

crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/feeding_by_modality.py"],
                                capture_output=True, text=True, timeout=5).stdout.strip())
except Exception:
    commit, dirty = "", True
if crit_f.exists():
    if json.loads(crit_f.read_text()).get("criteria") != CRITERIA:
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test.")
else:
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=commit, script_uncommitted=dirty), indent=2))
print(f"criteria registered at commit {commit or '?'}{' (SCRIPT UNCOMMITTED: commit before running)' if dirty else ''}")

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
types = set(meta["type"].dropna())
resolved = {}
for g, lst in GROUPS.items():
    hit = [x for x in lst if x in types]
    miss = [x for x in lst if x not in types]
    ids = meta.index[meta["type"].isin(hit)]
    resolved[g] = dict(types=hit, missing=miss, n_cells=int(len(ids)))
    print(f"  {g:<16} {len(ids):>4} cells  types {hit}" + (f"  MISSING {miss}" if miss else ""))
    if g in SCORED and not hit:
        raise SystemExit(f"ABORT: scored group '{g}' resolves to no neurons")

mn9 = meta.index[meta["type"] == "MN9"]
e = edges.copy()
e["sgn"] = e["nt"].str.lower().map(SIGN_MAP).fillna(0)
inp = e[e.post.isin(mn9)]
exc_relays = set(inp.loc[inp.sgn > 0, "pre"])
inh_relays = set(inp.loc[inp.sgn < 0, "pre"])

ei = e[e.sgn != 0]
ids_all = pd.Index(sorted(set(ei.pre) | set(ei.post)))
pos = pd.Series(np.arange(len(ids_all)), index=ids_all)
W = csr_matrix((ei.weight.values * ei.sgn.values, (pos[ei.pre].values, pos[ei.post].values)),
               shape=(len(ids_all), len(ids_all)))
Wn = W.multiply(1.0 / np.maximum(np.abs(W).sum(axis=0), 1)).tocsr()
tgt = pos[[b for b in mn9 if b in pos.index]].values

structural = {}
print("\nstructural (signed):")
for g, r in resolved.items():
    src = meta.index[meta["type"].isin(r["types"])]
    d = e[e.pre.isin(src)]
    de = float(d[d.post.isin(exc_relays)].weight.sum())
    di = float(d[d.post.isin(inh_relays)].weight.sum())
    v = np.zeros(len(ids_all))
    v[pos[[b for b in src if b in pos.index]].values] = 1.0
    hops = {}
    for h in range(1, 6):
        v = np.asarray(Wn.T.dot(v)).ravel()
        hops[f"hop_{h}"] = round(float(v[tgt].sum()), 6)
    structural[g] = dict(onto_exc_relays=de, onto_inh_relays=di, ratio=round(de / max(di, 1.0), 3), **hops)
    print(f"  {g:<16} exc {int(de):>5} / inh {int(di):>5}  ratio {structural[g]['ratio']:>5.2f} | "
          + " ".join(f"h{h} {hops[f'hop_{h}']:+.4f}" for h in range(1, 6)))

dynamic = {}
print("\ndynamic (declared parameter set):")
for g in ["sugar", "bitter", "old_mixed_proxy"]:
    dynamic[g] = {}
    for hz in RATES:
        t0 = time.time()
        m = CNSModel(neurons, edges, resolved[g]["types"], LIFParams(), electrical=True)
        on = pulse_protocol(m, {x: hz for x in resolved[g]["types"]}, n_trials=N_TRIALS, pulse_ms=200)
        r = readout_rates(m, on, ["MN9"], 250, meta)
        val = float(r.spikes_per_cell.mean()) if len(r) else 0.0
        dynamic[g][f"{hz:.0f}Hz"] = dict(mn9_spikes_per_cell=val, cns_hz=float(m.population_rate_hz()))
        print(f"  {g:<16} {hz:>5.0f} Hz | MN9 {val:5.2f} spikes/cell/pulse | CNS {m.population_rate_hz():.4f} Hz | "
              f"{round(time.time() - t0)}s")

s, b = structural["sugar"], structural["bitter"]
retract = (s["ratio"] >= 1.0) or (s["hop_2"] > 0)
report = dict(benchmark="feeding_by_modality", criteria=CRITERIA, resolved=resolved,
              structural=structural, dynamic=dynamic,
              F1_verdict=("RETRACT: the feeding negative was an artefact of mixing modalities" if retract else
                          "STRENGTHEN: the feeding negative holds with a correctly assigned sugar drive"),
              checks={"F2_sugar_ratio_exceeds_bitter": bool(s["ratio"] > b["ratio"]),
                      "F3_sugar_drives_mn9_at_100hz": bool(dynamic["sugar"]["100Hz"]["mn9_spikes_per_cell"] >= 0.5),
                      "F4_bitter_below_sugar_at_100hz": bool(dynamic["bitter"]["100Hz"]["mn9_spikes_per_cell"]
                                                             < dynamic["sugar"]["100Hz"]["mn9_spikes_per_cell"])})
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print(f"\nF1 VERDICT: {report['F1_verdict']}")
print("CHECKS (criteria registered before the run)")
for k, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"wrote {OUT / 'report.json'}")
