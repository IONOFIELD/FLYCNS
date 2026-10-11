"""
Wiring specificity against a null that can fire (audit 2026-10-11, gap 5).

The suite's earlier nulls permute connection targets across the whole CNS (or within a superclass).
Scattering each source's synapses that widely removes convergence everywhere: the global null's whole-CNS
rate is 2e-6 Hz against 4e-3 Hz for the real network, so "the null is silent" said more about the null
than about the circuit, and one draw gave no distribution to compare with.

This benchmark uses the degree-corrected null (flycns/graph.py rewire_null, mode "degree_corrected"):
targets are permuted only among connections that share the target's superclass, its neuropil, the
connection's sign and its size class. Every cell keeps its input per sign and size, its class and its
neuropil; every sender keeps its outputs. Only WHICH cell of that kind receives each connection changes.

For one circuit it runs the real network once and the null DRAWS times (draw k uses null seed 1000 + k;
the stimulus noise is the same in every arm, FLYCNS_SEED, so arms differ only in wiring), then scores the
real readout as a percentile of the null distribution (flycns/stats.py null_percentile):
  PASS        the real readout exceeds every null draw (one-sided p < 1 / (DRAWS + 1))
  FAIL        the real readout does not exceed the null median
  UNRESOLVED  in between, or the null is not active (median whole-CNS rate below 10% of the real one),
              because a null that cannot fire cannot test anything

Circuits (argument 1):
  escape    loom (LC4/LPLC2 ... at the declared tuning), readout: giant fiber response probability
  song      pC1_14a at 100 Hz, 200 ms pulses, readout: pMP2 spikes per cell per pulse
  auditory  auditory JO afferents at 150 Hz, chemical synapses as EM annotates them and no declared
            electrical coupling, readout: giant fiber peak depolarisation (mV). This asks whether the
            JO -> GF chemical wiring itself is specific, without the calibrated gap junction.

Run:  python benchmarks/null_distribution.py escape|song|auditory [draws=20] [trials] [data_dir]
Writes results/null_dc_<circuit>/report.json (stamped).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import CNSModel, LIFParams, load_graph, loom_protocol, rewire_null  # noqa: E402
from flycns import registry, stats  # noqa: E402
from flycns.bench import provenance, pulse_protocol, readout_rates  # noqa: E402
from flycns.graph import afferents_by_subclass  # noqa: E402
from flycns.protocols import LOOM_TUNING  # noqa: E402

CIRCUITS = ("escape", "song", "auditory")
CIRCUIT = sys.argv[1] if len(sys.argv) > 1 else ""
if CIRCUIT not in CIRCUITS:
    raise SystemExit(f"usage: null_distribution.py {'|'.join(CIRCUITS)} [draws] [trials] [data_dir]")
DRAWS = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else 20
DEFAULT_TRIALS = {"escape": 40, "song": 30, "auditory": 40}
N_TRIALS = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else DEFAULT_TRIALS[CIRCUIT]
DATA = sys.argv[4] if len(sys.argv) > 4 else "data"
ALIVE_FRACTION = 0.1          # a null is active if its median whole-CNS rate is >= 10% of the real one
OUT = Path(f"results/null_dc_{CIRCUIT}"); OUT.mkdir(parents=True, exist_ok=True)
CHECK = {"escape": "N1_escape_gf_wiring_specific", "song": "N2_song_pmp2_wiring_specific",
         "auditory": "N3_jo_gf_chemical_wiring_specific"}[CIRCUIT]

# ---- version 2 registration (flycns/registry.py), per circuit: criteria and the frozen model, before any data.
# The record is a null percentile with no band, so the rule is registered in words.
LABEL = f"null_dc_{CIRCUIT}"
CRITERIA_V2 = dict(
    version=2,
    question=f"is the {CIRCUIT} circuit's readout wiring-specific against a degree-corrected null that can fire?",
    circuit=CIRCUIT,
    protocol=dict(
        stimulus={"escape": "loom on the declared loom tuning types (loom_protocol), electrical synapses on",
                  "song": "pC1_14a at 100 Hz, 200 ms pulses (pulse_protocol), electrical synapses on",
                  "auditory": ("the auditory JO afferent types at 150 Hz, 60 ms pulses (pulse_protocol); chemical "
                               "synapses as EM annotates them, no electrical coupling")}[CIRCUIT],
        readout={"escape": "giant fiber (DNp01) response probability: a spike within 160 ms of loom onset, per trial",
                 "song": "pMP2 spikes per cell per pulse, 250 ms window, mean over trials",
                 "auditory": "giant fiber (DNp01) peak depolarisation in mV, 100 ms window, mean over trials"}[CIRCUIT],
        n_trials=N_TRIALS, draws=DRAWS, null_mode="degree_corrected",
        null_seeds=[1000 + k for k in range(DRAWS)],
        null_seed_rule="null draw k = 0..draws-1 rewires with seed 1000 + k (rewire_null, mode degree_corrected)",
        stimulus_noise="FLYCNS_SEED, the same in every arm, so the arms differ only in wiring",
        alive_fraction=ALIVE_FRACTION,
        alive_rule=f"median null whole-CNS rate >= {ALIVE_FRACTION} x real"),
    checks={CHECK: dict(rule=(
        "the real readout as a percentile of the null draws (stats.null_percentile): PASS if it exceeds every null "
        "draw (one-sided p < 1 / (draws + 1)); FAIL if it does not exceed the null median; UNRESOLVED in between, "
        "or if the null is not active by the alive rule (it cannot test anything), or if there are no null draws"))},
)
REG = registry.register(LABEL, CRITERIA_V2, scripts=[__file__], supersedes=None)

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
types = set(neurons["type"].dropna())


def escape(edge_df):
    m = CNSModel(neurons, edge_df, list(LOOM_TUNING), LIFParams(), electrical=True)
    trials = loom_protocol(m, n_trials=N_TRIALS)
    sp = m.spike_frame()
    gf = set(m.lif_ids[m.readout_index("DNp01")])
    hits = [int(((sp.t_ms >= on) & (sp.t_ms < on + 160) & sp.bodyId.isin(gf)).any()) for on, _ in trials]
    return dict(readout=float(np.mean(hits)), per_trial=hits, cns_hz=float(m.population_rate_hz()))


def song(edge_df):
    tl = [t for t in ("pC1_14a",) if t in types]
    if not tl:
        raise SystemExit("pC1_14a is not in this dataset")
    m = CNSModel(neurons, edge_df, tl, LIFParams(), electrical=True)
    on = pulse_protocol(m, {t: 100.0 for t in tl}, n_trials=N_TRIALS, pulse_ms=200)
    rr = readout_rates(m, on, ["pMP2"], 250, meta)
    per = rr.groupby("trial")["spikes_per_cell"].mean().reindex(range(len(on)), fill_value=0.0)
    return dict(readout=float(per.mean()), per_trial=[float(x) for x in per], cns_hz=float(m.population_rate_hz()))


JO = [t for t in afferents_by_subclass(neurons, ["auditory"], "JO-") if not t.endswith("unclear")]


def auditory(edge_df):
    if not JO:
        raise SystemExit("no auditory JO types in this dataset")
    m = CNSModel(neurons, edge_df, JO, LIFParams(), electrical=False, monitor_types=("DNp01",))
    on = pulse_protocol(m, {t: 150.0 for t in JO}, n_trials=N_TRIALS, pulse_ms=60)
    depol = m.peak_depolarization_mV(on, 100)
    return dict(readout=float(np.nanmean(depol)), per_trial=[float(x) for x in np.ravel(depol)],
                cns_hz=float(m.population_rate_hz()))


RUN = {"escape": escape, "song": song, "auditory": auditory}[CIRCUIT]
READOUT = {"escape": "giant fiber response probability", "song": "pMP2 spikes per cell per pulse",
           "auditory": "giant fiber peak depolarisation, mV"}[CIRCUIT]

t0 = time.time()
print(f"{CIRCUIT}: real network, {N_TRIALS} trials ...", flush=True)
real = RUN(edges)
print(f"  real {READOUT}: {real['readout']:.4f}; whole CNS {real['cns_hz']:.5f} Hz", flush=True)
nulls, sources = [], set()
for k in range(DRAWS):
    nd = rewire_null(edges, seed=1000 + k, mode="degree_corrected", neurons=neurons, data_dir=DATA)
    sources.add(nd.attrs.get("neuropil_source", "?"))
    r = RUN(nd)
    nulls.append(r)
    print(f"  null {k + 1:>2}/{DRAWS}: {r['readout']:.4f}; whole CNS {r['cns_hz']:.5f} Hz "
          f"({round(time.time() - t0)}s)", flush=True)

null_vals = [r["readout"] for r in nulls]
null_cns = float(np.median([r["cns_hz"] for r in nulls])) if nulls else float("nan")
alive = bool(nulls) and real["cns_hz"] > 0 and null_cns >= ALIVE_FRACTION * real["cns_hz"]
name = CHECK
rec = stats.null_percentile(real["readout"], null_vals, null_alive=alive)
registry.verify_bands(REG, {name: rec})
report = dict(
    benchmark=f"null_dc_{CIRCUIT}", circuit=CIRCUIT, readout=READOUT, n_trials=N_TRIALS, draws=DRAWS,
    null_mode="degree_corrected", null_seeds=[1000 + k for k in range(DRAWS)], neuropil_source=sorted(sources),
    real=real, null=[{k: v for k, v in r.items() if k != "per_trial"} for r in nulls],
    null_cns_hz_median=null_cns, null_alive=alive, alive_rule=f"median null whole-CNS rate >= {ALIVE_FRACTION} x real",
    checks={name: bool(rec["verdict"] == "PASS")}, uncertainty={name: rec}, registration=registry.stamp(REG),
    wall_s=round(time.time() - t0, 1), provenance=provenance(DATA))
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print(f"\nreal {real['readout']:.4f} vs null median {np.median(null_vals) if null_vals else float('nan'):.4f}, "
      f"max {max(null_vals) if null_vals else float('nan'):.4f} (percentile {rec['percentile']:.2f}); "
      f"null CNS {null_cns:.5f} Hz vs real {real['cns_hz']:.5f} Hz ({'active' if alive else 'NOT active'})")
print(f"  {rec['verdict']}  {name}" + (f"  ({rec['note']})" if rec.get("note") else ""))
print(f"wrote {OUT / 'report.json'}")
