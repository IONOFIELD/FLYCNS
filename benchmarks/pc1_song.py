"""
Can the dynamic model explain pC1 song phenotypes that static connectivity could not?

The male-specific pC1/pC1x neurons (48 cell types) were activated line by line while courtship
song was recorded (Current Biology 36:4697-4716, 2026, Fig. 5). Activating pC1_13 and pC1_14
enhanced pulse song and suppressed sine song; pC1_14a alone was necessary and sufficient for pulse;
activating pC1_15 with pC1_16 suppressed both. The song command neurons are pMP2 (pulse), DNp13
(sine) and pIP10 (both). The authors traced two- and three-synapse paths, split by transmitter,
and concluded many activation phenotypes cannot be easily explained by chemical synaptic
connections and neurotransmitter predictions alone. This benchmark asks whether a signed,
spiking simulation of the same wiring does better.

HARD LIMIT, stated in advance: suppression phenotypes are untestable here. The model has no
background activity, so there is no ongoing song-neuron firing to suppress (the same reason the
feeding circuit fails). Only excitatory phenotypes are scored.

Groups (exact MaleCNS type names; aborts before registering if a scored group is missing):
  pC1_14a            pC1_14a
  pC1_13_14          pC1_13a, pC1_14a, pC1_14b
  pC1_15_16          pC1_15a, pC1_15b, pC1_15c, and every pC1_16 subtype present
  P1a  (reported)    pC1_12b, pC1_4a, pC1_4b
  pC1_17 (reported)  pC1_17a, pC1_17b
Readouts: pMP2 (pulse), DNp13 (sine), pIP10 (both).
Drive: Poisson at 100 Hz on every cell of the group, 10 pulses of 200 ms, declared parameter set;
50 Hz reported. Readout: spikes per cell per pulse in a 250 ms window.

CRITERIA (registered after names resolve, before anything is simulated):
  P1  pC1_14a at 100 Hz: pMP2 >= 0.5 spikes/cell/pulse AND pMP2 > DNp13
  P2  pC1_13_14 at 100 Hz: pMP2 >= 0.5 AND pMP2 > DNp13
  P3  pMP2 under pC1_14a exceeds pMP2 under pC1_15_16 (both at 100 Hz)
  P4  pC1_14a at 100 Hz on a degree-preserving rewired null: pMP2 < 0.1
Reported: signed input-normalised path products (hops 1-4) from each group onto each readout,
i.e. the static analysis the paper found insufficient, beside the dynamic result.

Run:  python benchmarks/pc1_song.py [n_trials] [data_dir]
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
from flycns.graph import rewire_null
from flycns import stats

N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/pc1_song")
OUT.mkdir(parents=True, exist_ok=True)
READOUTS = ["pMP2", "DNp13", "pIP10"]
RATES = [50.0, 100.0]

# Version 2 registration (flycns/registry.py): criteria plus the frozen model, written before any data is loaded;
# it supersedes the version 1 criteria.json below, which is kept and still checked. pC1_15_16 takes every pC1_16
# subtype present, which is only known after loading, so that group is stated in words here.
from flycns import registry  # noqa: E402
_v1 = OUT / "criteria.json"
CRITERIA_V2 = dict(
    version=2,
    question=("does a signed spiking simulation reproduce the excitatory pC1 song phenotypes that static "
              "connectivity could not explain?"),
    source=("Current Biology 36:4697-4716 (2026), Fig. 5 (pC1/pC1x song phenotypes); pMP2 pulse, DNp13 sine, "
            "pIP10 both"),
    groups=dict(pC1_14a=["pC1_14a"], pC1_13_14=["pC1_13a", "pC1_14a", "pC1_14b"],
                pC1_15_16="pC1_15a, pC1_15b, pC1_15c and every pC1_16 subtype present",
                P1a=["pC1_12b", "pC1_4a", "pC1_4b"], pC1_17=["pC1_17a", "pC1_17b"]),
    readouts=READOUTS,
    protocol=dict(n_trials=N_TRIALS, drive_hz=100.0, rates_hz=RATES, pulse_ms=200, gap_ms=300, readout_window_ms=250,
                  null=("degree-preserving rewired null (flycns/graph.py rewire_null, seed 0; mode FLYCNS_NULL, default "
                        "global), pC1_14a at 100 Hz"),
                  model="declared parameter set (LIFParams), electrical synapses on"),
    checks=dict(
        P1_pc1_14a_pulse_over_sine=dict(
            bands=[[0.5, None]], optional_bands=[[0.0, None]],
            rule=("conjunction, pC1_14a at 100 Hz: (a) pMP2 spikes/cell/pulse, bootstrap over pulses, 95% interval at "
                  "or above 0.5; (b) pMP2 minus DNp13 paired per pulse, bootstrap over pulses, 95% interval above 0, "
                  "UNRESOLVED (not scorable) if DNp13 fires in no pulse of any group and rate on the real network; "
                  "PASS only if both parts pass")),
        P2_pc1_13_14_pulse_over_sine=dict(
            bands=[[0.5, None]], optional_bands=[[0.0, None]],
            rule=("conjunction, pC1_13_14 at 100 Hz: (a) pMP2 spikes/cell/pulse, bootstrap over pulses, 95% interval "
                  "at or above 0.5; (b) pMP2 minus DNp13 paired per pulse, bootstrap over pulses, 95% interval above "
                  "0, UNRESOLVED (not scorable) if DNp13 fires in no pulse of any group and rate on the real network; "
                  "PASS only if both parts pass")),
        P3_14a_exceeds_15_16_on_pulse=dict(
            band=[0, None], band_lower_exclusive=True,
            rule=("pMP2 under pC1_14a minus under pC1_15_16, both at 100 Hz: two separate simulations, each resampled "
                  "over its own pulses: PASS if the 95% interval lies above 0")),
        P4_null_silent=dict(
            band=[None, 0.1],
            rule=("pMP2 under pC1_14a at 100 Hz on the rewired null, bootstrap over pulses: PASS if the 95% interval "
                  "lies at or below 0.1 spikes/cell/pulse")),
    ),
    limit="suppression phenotypes untestable: no background activity",
)
REG = registry.register("pc1_song", CRITERIA_V2, scripts=[__file__],
                        supersedes=dict(file="criteria.json", git_commit=(
                            json.loads(_v1.read_text(encoding="utf-8")).get("git_commit") if _v1.exists() else None)))

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
types = set(meta["type"].dropna())
pc1_present = sorted(x for x in types if str(x).startswith(("pC1_", "pC1x")))
print(f"pC1/pC1x types present ({len(pc1_present)}): {pc1_present}")
GROUPS = {
    "pC1_14a": ["pC1_14a"],
    "pC1_13_14": ["pC1_13a", "pC1_14a", "pC1_14b"],
    "pC1_15_16": ["pC1_15a", "pC1_15b", "pC1_15c"] + [x for x in pc1_present if x.startswith("pC1_16")],
    "P1a": ["pC1_12b", "pC1_4a", "pC1_4b"],
    "pC1_17": ["pC1_17a", "pC1_17b"],
}
SCORED = ["pC1_14a", "pC1_13_14", "pC1_15_16"]
missing_readouts = [r for r in READOUTS if r not in types]
problems = {g: [x for x in GROUPS[g] if x not in types] for g in SCORED}
if missing_readouts or any(problems.values()):
    raise SystemExit(f"ABORT before registration: readouts missing {missing_readouts}; "
                     f"scored-group names missing {problems}. pC1 types present are listed above.")

CRITERIA = dict(
    source="Current Biology 36:4697-4716 (2026), Fig. 5 (pC1/pC1x song phenotypes); pMP2 pulse, DNp13 sine, pIP10 both",
    groups=GROUPS, readouts=READOUTS, drive_hz=100.0, n_trials=N_TRIALS,
    P1="pC1_14a: pMP2 >= 0.5 spikes/cell/pulse AND pMP2 > DNp13",
    P2="pC1_13_14: pMP2 >= 0.5 AND pMP2 > DNp13",
    P3="pMP2 under pC1_14a > pMP2 under pC1_15_16",
    P4="pC1_14a on rewired null: pMP2 < 0.1",
    limit="suppression phenotypes untestable: no background activity")
# Registered test: refuse uncommitted code and data that differ from data/MANIFEST.json, so the
# registered result can be traced to an exact commit and an exact dataset (flycns/integrity.py).
from flycns.integrity import require_clean, require_data, criteria_differ  # noqa: E402
require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem)   # every table pinned in the manifest, rehashed
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/pc1_song.py"],
                                capture_output=True, text=True, timeout=5).stdout.strip())
except Exception:
    commit, dirty = "", True
if crit_f.exists():
    if criteria_differ(crit_f, CRITERIA):
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test.")
else:
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=commit, script_uncommitted=dirty), indent=2), encoding="utf-8")
reg = json.loads(crit_f.read_text(encoding="utf-8")).get("git_commit") or "?"
print(f"criteria registered at commit {reg}; this run at {commit or '?'}{' (SCRIPT UNCOMMITTED: commit before running)' if dirty else ''}")

# ---- static: signed input-normalised path products, the analysis the paper found insufficient
e = edges.copy()
e["sgn"] = e["sign"]   # the signs the dynamic model uses, including any FLYCNS_SIGNFLIP perturbation
ids = pd.Index(sorted(set(e.pre) | set(e.post)))
pos = pd.Series(np.arange(len(ids)), index=ids)
W = csr_matrix((e.weight.values * e.sgn.values, (pos[e.pre].values, pos[e.post].values)), shape=(len(ids), len(ids)))
W = W.multiply(1.0 / np.maximum(np.asarray(np.abs(W).sum(axis=0)).ravel(), 1.0)).tocsr()
rpos = {r: pos[[b for b in meta.index[meta["type"] == r] if b in pos.index]].values for r in READOUTS}
static = {}
print("\nstatic signed influence (cumulative hops 1-4):")
for g, tl in GROUPS.items():
    src = [b for b in meta.index[meta["type"].isin(tl)] if b in pos.index]
    v = np.zeros(len(ids)); v[pos[src].values] = 1.0
    acc = {r: 0.0 for r in READOUTS}
    for _ in range(4):
        v = np.asarray(W.T.dot(v)).ravel()
        for r in READOUTS:
            acc[r] += float(v[rpos[r]].sum())
    static[g] = acc
    print(f"  {g:<10} ({len(src):>3} cells) " + "  ".join(f"{r} {acc[r]:+.2e}" for r in READOUTS))

# ---- dynamic
def drive(group, edge_df, hz):
    tl = [x for x in GROUPS[group] if x in types]
    m = CNSModel(neurons, edge_df, tl, LIFParams(), electrical=True)
    on = pulse_protocol(m, {x: hz for x in tl}, n_trials=N_TRIALS, pulse_ms=200)
    out, per_trial = {}, {}
    for r in READOUTS:
        rr = readout_rates(m, on, [r], 250, meta)
        out[r] = float(rr.spikes_per_cell.mean()) if len(rr) else 0.0
        # the same readout per pulse (mean over sides within a pulse); their mean is out[r]
        per_trial[r] = [float(x) for x in rr.groupby("trial").spikes_per_cell.mean().sort_index()] if len(rr) else []
    out["cns_hz"] = float(m.population_rate_hz())
    out["per_trial"] = per_trial
    return out

dynamic = {}
print("\ndynamic (spikes per cell per 200 ms pulse):")
for g in GROUPS:
    if not any(x in types for x in GROUPS[g]):
        print(f"  {g:<10} skipped: no types present"); continue
    dynamic[g] = {}
    for hz in RATES:
        t0 = time.time()
        d = drive(g, edges, hz); dynamic[g][f"{hz:.0f}Hz"] = d
        print(f"  {g:<10} {hz:>5.0f} Hz | " + "  ".join(f"{r} {d[r]:5.2f}" for r in READOUTS)
              + f" | CNS {d['cns_hz']:.4f} Hz | {round(time.time() - t0)}s")
null = drive("pC1_14a", rewire_null(edges, seed=0), 100.0)
print("  null pC1_14a 100 Hz | " + "  ".join(f"{r} {null[r]:5.2f}" for r in READOUTS))

d14 = dynamic["pC1_14a"]["100Hz"]; d1314 = dynamic["pC1_13_14"]["100Hz"]; d1516 = dynamic["pC1_15_16"]["100Hz"]
report = dict(benchmark="pc1_song", criteria=CRITERIA, pc1_types_present=pc1_present, static=static,
              dynamic=dynamic, null_pc1_14a_100Hz=null,
              checks={"P1_pc1_14a_pulse_over_sine": bool(d14["pMP2"] >= 0.5 and d14["pMP2"] > d14["DNp13"]),
                      "P2_pc1_13_14_pulse_over_sine": bool(d1314["pMP2"] >= 0.5 and d1314["pMP2"] > d1314["DNp13"]),
                      "P3_14a_exceeds_15_16_on_pulse": bool(d14["pMP2"] > d1516["pMP2"]),
                      "P4_null_silent": bool(null["pMP2"] < 0.1)})


# ---- uncertainty (flycns/stats.py): 95% intervals over pulses, three-way verdicts
def _pp(d, r):
    """Per-pulse values of readout r in arm d; a readout with no cells is 0 in every pulse, as d[r] is."""
    return d["per_trial"][r] or [0.0] * N_TRIALS


# "pMP2 > DNp13" only tests a pulse-versus-sine choice if DNp13 fires somewhere on the real network
dnp13_silent = all(not any(_pp(d, "DNp13")) for arms in dynamic.values() for d in arms.values())


def _pulse_floor(d):
    v = _pp(d, "pMP2"); est, lo, hi = stats.bootstrap(v)
    return stats.scored(est, lo, hi, low=0.5, n=len(v), note="pMP2 spikes/cell/pulse, bootstrap over pulses")


def _pulse_over_sine(d):
    if dnp13_silent:
        return stats.unresolved("DNp13 is silent in every arm (0 spikes in every pulse of every group and rate on the "
                                "real network), so 'pMP2 > DNp13' adds nothing to 'pMP2 >= 0.5' and cannot show a "
                                "pulse-over-sine choice; benchmarks/dnp13_control.py tests whether DNp13 is reachable",
                                estimate=d["pMP2"] - d["DNp13"])
    diff = np.asarray(_pp(d, "pMP2")) - np.asarray(_pp(d, "DNp13"))
    est, lo, hi = stats.bootstrap(diff)
    return stats.scored(est, lo, hi, low=0, strict=True, n=len(diff),
                        note="pMP2 - DNp13 paired per pulse (same simulation and pulses), bootstrap over pulses")


_a, _b = _pp(d14, "pMP2"), _pp(d1516, "pMP2")
_p3 = stats.bootstrap_diff(_a, _b)
_p4 = _pp(null, "pMP2")
report["uncertainty"] = {
    "P1_pc1_14a_pulse_over_sine": stats.combine([_pulse_floor(d14), _pulse_over_sine(d14)]),
    "P2_pc1_13_14_pulse_over_sine": stats.combine([_pulse_floor(d1314), _pulse_over_sine(d1314)]),
    "P3_14a_exceeds_15_16_on_pulse": stats.scored(*_p3, low=0, strict=True,
                                                  note=f"pMP2 under pC1_14a minus under pC1_15_16: two separate "
                                                       f"simulations, each resampled over its own pulses ({len(_a)} and {len(_b)})"),
    "P4_null_silent": stats.scored(*stats.bootstrap(_p4), high=0.1, n=len(_p4),
                                   note="pMP2 on the rewired null, bootstrap over pulses"),
}
registry.verify_bands(REG, report["uncertainty"])
report["registration"] = registry.stamp(REG)
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print("\nCHECKS (criteria registered before the run)")
for k, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")


def _g(x):
    return "-" if x is None else (f"{x:.3g}" if isinstance(x, float) else str(x))


def _desc(u):
    """One line for an uncertainty record: estimate [95% interval] in band (method); a conjunction lists its parts."""
    if u.get("parts"):
        return "; ".join(f"{p['verdict']} {_desc(p)}" for p in u["parts"])
    s, ci, band = _g(u.get("estimate")), u.get("ci95"), u.get("band")
    if ci:
        s += f" [{_g(ci[0])}, {_g(ci[1])}]"
    if band and any(b is not None for b in band):
        s += (f" in {'(' if u.get('band_lower_exclusive') else '['}{'-inf' if band[0] is None else _g(band[0])}, "
              f"{'inf' if band[1] is None else _g(band[1])}]")
    return s + f" ({u['method']})" + (f": {u['note']}" if u["method"] == "not scorable as designed" else "")


print("UNCERTAINTY (95% intervals, flycns/stats.py: PASS only if the whole interval lies in the band)")
for k, u in report["uncertainty"].items():
    print(f"  {u['verdict']:<10}  {k}: {_desc(u)}")
print(f"wrote {OUT / 'report.json'}")
