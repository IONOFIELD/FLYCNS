"""
Positive control for the sine-song neuron DNp13.

The pC1 song benchmark passed 4/4 (benchmarks/pc1_song.py): pC1_14a drives the pulse neuron pMP2
and not the sine neuron DNp13. But DNp13 fired in NO arm, so "pulse over sine" could mean either a
real pulse-versus-sine choice or simply that DNp13 is unreachable in this model. Those are very
different claims. This benchmark decides between them.

Arms (100 Hz Poisson on every cell of the driven type, 10 pulses of 200 ms, declared parameter set):
  best_input  DNp13's strongest excitatory input type, chosen by a FIXED RULE from the graph: the
              type with the largest total cholinergic synapse count onto DNp13 (DNp13 excluded).
  pC1_1b      the paper reports pC1_1b takes 13% of its input from LC10a and acts on DNp13
              (Current Biology 36:4697-4716, 2026).
  LC10a       reported: the visual input the paper links to pC1_1b.

CRITERIA (registered after names resolve and the rule picks best_input, before any simulation):
  D1  reachability (decisive): best_input drives DNp13 >= 0.5 spikes/cell/pulse
  D2  sine choice: pC1_1b drives DNp13 >= 0.5 AND DNp13 > pMP2
Interpretation fixed in advance:
  D1 pass, D2 pass  pulse/sine choice real in both directions; song result strengthened
  D1 pass, D2 fail  DNp13 reachable, so pC1_14a's pulse-over-sine is genuine selectivity; the
                    paper's pC1_1b -> sine link is not reproduced
  D1 fail           DNp13 unreachable even from its best input; the pc1_song P1/P2 passes are
                    reworded to "pulse neuron driven, sine neuron unreachable"
Reported: DNp13's excitatory and inhibitory input synapses; static signed paths (hops 1-4).

Run:  python benchmarks/dnp13_control.py [n_trials] [data_dir]
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
from flycns.graph import SIGN_MAP

N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/dnp13_control")
OUT.mkdir(parents=True, exist_ok=True)
READOUTS = ["DNp13", "pMP2", "pIP10"]
HZ = 100.0

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
types = set(meta["type"].dropna())
missing = [x for x in ["DNp13", "pMP2", "pIP10", "pC1_1b"] if x not in types]
if missing:
    near = sorted(x for x in types if str(x).startswith(("pC1_1", "DNp1", "LC10")))[:20]
    raise SystemExit(f"ABORT before registration: missing {missing}. Near names: {near}")

e = edges.copy()
e["sgn"] = e["nt"].str.lower().map(SIGN_MAP).fillna(0.0)
dnp13 = meta.index[meta["type"] == "DNp13"]
inp = e[e.post.isin(dnp13)].assign(ty=lambda d: d.pre.map(meta["type"]))
exc_by_type = inp[inp.sgn > 0].groupby("ty").weight.sum().drop(labels=["DNp13"], errors="ignore").sort_values(ascending=False)
if not len(exc_by_type):
    raise SystemExit("ABORT before registration: DNp13 has no excitatory input")
BEST = exc_by_type.index[0]
balance = dict(excitatory=int(inp.loc[inp.sgn > 0, "weight"].sum()), inhibitory=int(inp.loc[inp.sgn < 0, "weight"].sum()))
print(f"DNp13 input: {balance['excitatory']:,} excitatory vs {balance['inhibitory']:,} inhibitory synapses")
print(f"strongest excitatory input types: {exc_by_type.head(5).astype(int).to_dict()}")
print(f"rule picks best_input = {BEST}")
lc10a = sorted(x for x in types if str(x).startswith("LC10a"))

CRITERIA = dict(
    source="Current Biology 36:4697-4716 (2026): pC1_1b acts on DNp13 and takes 13% of input from LC10a",
    rule="best_input = type with largest cholinergic synapse count onto DNp13",
    best_input=BEST, drive_hz=HZ, n_trials=N_TRIALS,
    D1="best_input drives DNp13 >= 0.5 spikes/cell/pulse",
    D2="pC1_1b drives DNp13 >= 0.5 AND DNp13 > pMP2",
    interpretation=dict(both="pulse/sine choice real both ways", D1_only="pC1_14a selectivity genuine; pC1_1b link not reproduced",
                        D1_fail="reword pc1_song P1/P2: pulse driven, sine unreachable"))
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/dnp13_control.py"],
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

ids = pd.Index(sorted(set(e.pre) | set(e.post)))
pos = pd.Series(np.arange(len(ids)), index=ids)
W = csr_matrix((e.weight.values * e.sgn.values, (pos[e.pre].values, pos[e.post].values)), shape=(len(ids), len(ids)))
W = W.multiply(1.0 / np.maximum(np.asarray(np.abs(W).sum(axis=0)).ravel(), 1.0)).tocsr()
rpos = {r: pos[[b for b in meta.index[meta["type"] == r] if b in pos.index]].values for r in READOUTS}
ARMS = {"best_input": [BEST], "pC1_1b": ["pC1_1b"]}
if lc10a:
    ARMS["LC10a"] = lc10a

static, dynamic = {}, {}
for arm, tl in ARMS.items():
    src = [b for b in meta.index[meta["type"].isin(tl)] if b in pos.index]
    v = np.zeros(len(ids)); v[pos[src].values] = 1.0
    acc = {r: 0.0 for r in READOUTS}
    for _ in range(4):
        v = np.asarray(W.T.dot(v)).ravel()
        for r in READOUTS:
            acc[r] += float(v[rpos[r]].sum())
    static[arm] = acc
    t0 = time.time()
    m = CNSModel(neurons, edges, tl, LIFParams(), electrical=True)
    on = pulse_protocol(m, {x: HZ for x in tl}, n_trials=N_TRIALS, pulse_ms=200)
    d = {}
    for r in READOUTS:
        rr = readout_rates(m, on, [r], 250, meta)
        d[r] = float(rr.spikes_per_cell.mean()) if len(rr) else 0.0
    d["cns_hz"] = float(m.population_rate_hz()); d["n_cells"] = int(len(src))
    dynamic[arm] = d
    print(f"  {arm:<11} {str(tl)[:40]:<40} ({len(src):>3} cells) | " + "  ".join(f"{r} {d[r]:5.2f}" for r in READOUTS)
          + f" | static DNp13 {acc['DNp13']:+.2e} pMP2 {acc['pMP2']:+.2e} | {round(time.time() - t0)}s")

b, p = dynamic["best_input"], dynamic["pC1_1b"]
d1 = bool(b["DNp13"] >= 0.5)
d2 = bool(p["DNp13"] >= 0.5 and p["DNp13"] > p["pMP2"])
verdict = ("pulse/sine choice real in both directions; song result strengthened" if d1 and d2 else
           "DNp13 reachable, so pC1_14a's pulse-over-sine is genuine selectivity; pC1_1b -> sine not reproduced" if d1 else
           "DNp13 unreachable even from its best input: reword pc1_song P1/P2 to 'pulse neuron driven, sine neuron unreachable'")
report = dict(benchmark="dnp13_control", criteria=CRITERIA, dnp13_input_balance=balance,
              top_excitatory_inputs={k: int(v) for k, v in exc_by_type.head(10).items()},
              static=static, dynamic=dynamic, checks={"D1_dnp13_reachable": d1, "D2_pc1_1b_sine_choice": d2},
              verdict=verdict, provenance=provenance())
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print("\nCHECKS (criteria registered before the run)")
for k, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"VERDICT: {verdict}")
print(f"wrote {OUT / 'report.json'}")
