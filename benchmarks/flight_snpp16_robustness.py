"""
Robustness of the SNpp16 selectivity claim, with criteria registered before the run.

The claim (benchmarks/flight_snpp16_graded.py, 4/5 pre-registered criteria): SNpp16, 13 wing
campaniform afferents, drives the DVM motor neurons without recruiting any steering muscle,
reliably from about seven of its thirteen cells, through its actual wiring. This battery asks
whether that claim survives three things it could plausibly rest on. Criteria are fixed below and
written to results/flight_snpp16_robustness/criteria.json, stamped with the commit, before any
simulation; the script refuses to run against changed criteria.

  R1  transmitter uncertainty. Invert the sign of every neuron whose own per-T-bar predictions
      disagree with its aggregate label (fit/synapse_nt.py; ~2% of synaptic weight). At k=7:
      DVMn 1a-c in 2-12 Hz in >= 4 of 5 draws, and steering, b1, DLMn c-f each below 1 Hz.
  R2  cord single-neuron parameters. Vary tau_m (5, 10, 40 ms), threshold gap (4, 10 mV) and
      refractory period (1, 5 ms), one at a time, for the relay-layer superclasses read from the
      data. At k=7: steering, b1 and DLMn c-f each below 1 Hz at EVERY setting. DVMn is reported
      at each setting but not scored, since its rate is expected to move with the relay layer.
  R3  fresh draws. Repeat the k = 1..13 sweep with a new, independent set of cell-identity and
      phase draws. Pass if the smallest in-band k (k*) is within one step of the original k* = 5,
      AND k=7 is in band in >= 4 of 5 draws. Monotonicity is reported, not scored, to see
      whether the original G1 failure recurs or was a feature of those particular draws.

Run:  python benchmarks/flight_snpp16_robustness.py [n_cycles] [data_dir]
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brian2 import SpikeGeneratorGroup, Synapses, ms, mV
from flycns import load_graph, CNSModel, LIFParams
from flycns.bench import provenance
from flycns.graph import SIGN_MAP

N_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 400
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/flight_snpp16_robustness")
OUT.mkdir(parents=True, exist_ok=True)
WINGBEAT_HZ, JITTER_MS, N_DRAWS, K_TEST, K_STAR_ORIG = 202.0, 0.8, 5, 7, 5
BAND = (2.0, 12.0)
TARGET = os.environ.get("FLYCNS_TARGET_TYPE", "SNpp16")      # override only for toy smoke tests
STEER = r"^(b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
R2_SWEEP = [("tau_m_ms", 5.0), ("tau_m_ms", 10.0), ("tau_m_ms", 40.0),
            ("v_thresh_gap_mV", 4.0), ("v_thresh_gap_mV", 10.0),
            ("refractory_ms", 1.0), ("refractory_ms", 5.0)]
FRESH_SEED_BASE = 50000          # the original sweep used 1000 + 17k + d

CRITERIA = dict(
    claim=f"{TARGET} selectively drives DVM motor neurons, reliably from k={K_TEST}",
    R1=f"targeted NT sign inversion, k={K_TEST}: DVMn in band in >=4/{N_DRAWS} draws; steering, b1, DLMn each < 1 Hz",
    R2=f"relay-layer parameter sweep {R2_SWEEP}, k={K_TEST}: steering, b1, DLMn each < 1 Hz at every setting",
    R3=f"fresh draws (seed base {FRESH_SEED_BASE}): k* within 1 of {K_STAR_ORIG}, and k={K_TEST} in band in >=4/{N_DRAWS}",
    band=BAND, n_draws=N_DRAWS, n_cycles=N_CYCLES)

crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/flight_snpp16_robustness.py"],
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
os.environ["FLYCNS_SIGNFLIP_TARGETED"] = "1"
_, edges_flipped = load_graph(DATA)
os.environ.pop("FLYCNS_SIGNFLIP_TARGETED", None)
n_flipped = int((edges_flipped["sign"].values != edges["sign"].values).sum()) if len(edges_flipped) == len(edges) else -1
print(f"targeted sign inversion: {n_flipped} edges differ from the declared graph")
if n_flipped <= 0:
    raise SystemExit("ABORT: the targeted sign inversion changed no edges (is data/edges_nt.parquet present? "
                     "run fit/synapse_nt.py). R1 would otherwise score an unperturbed graph as a perturbation test.")

meta = neurons.set_index("bodyId")
t = meta["type"].fillna(""); sub = meta["subclass"].fillna(""); nerve = meta["entryNerve"].fillna("")
sc = meta["superclass"].fillna("")
aff = sorted(meta.index[(sub == "campaniform sensilla") & nerve.isin(["ADMN", "DMetaN"])])
target = sorted(b for b in aff if t[b] == TARGET)
dvm = meta.index[t == "DVMn 1a-c"]; dlm = meta.index[t == "DLMn c-f"]
steer = meta.index[t.str.match(STEER)]; b1 = meta.index[t == "b1 MN"]
if not target:
    raise SystemExit(f"{TARGET} not found")
first = edges[edges.pre.isin(aff)].groupby("post").weight.sum()
relays = first[first >= 20].index
onto = edges[edges.pre.isin(relays) & edges.post.isin(dlm)]
exc_relays = set(onto[onto["nt"].str.lower().map(SIGN_MAP).fillna(0) > 0].pre)
RELAY_SC = sorted({sc.get(b, "") for b in exc_relays} - {""})
print(f"{TARGET} {len(target)} cells | relay superclasses for R2: {RELAY_SC}")


def drive(src, edge_df, seed, params=None):
    m = CNSModel(neurons, edge_df, [], params or LIFParams(), electrical=True)
    idx = [m.lif_index[b] for b in src if b in m.lif_index.index]
    rng = np.random.default_rng(seed)
    period, pre_ms = 1000.0 / WINGBEAT_HZ, 200.0
    dur_ms = N_CYCLES * period
    phase = rng.uniform(0, period, size=len(idx))
    cyc = np.arange(N_CYCLES) * period
    times = (cyc[None, :] + phase[:, None] + rng.normal(0, JITTER_MS, (len(idx), N_CYCLES))).ravel() + pre_ms
    ids = np.repeat(np.arange(len(idx)), N_CYCLES)
    keep = times >= 0
    gen = SpikeGeneratorGroup(len(idx), ids[keep], times[keep] * ms)
    S = Synapses(gen, m.G, on_pre="v_post += kick", namespace=dict(kick=8.0 * mV))
    S.connect(i=np.arange(len(idx)), j=np.array(idx))
    m.net.add(gen, S)
    m.run(pre_ms + dur_ms)
    sp = m.spike_frame(); sp = sp[sp.t_ms >= pre_ms]; dur_s = dur_ms / 1000.0

    def rate(ids_):
        ids_ = [b for b in ids_ if b in m.lif_index.index]
        return float(sp.bodyId.isin(ids_).sum() / max(len(ids_), 1) / dur_s)

    return dict(dvmn=rate(dvm), dlmn=rate(dlm), steer=rate(steer), b1=rate(b1))


def at_k(k, seed_base, edge_df=None, params=None):
    edge_df = edges if edge_df is None else edge_df
    out = []
    for d in range(N_DRAWS):
        rng = np.random.default_rng(seed_base + 17 * k + d)
        out.append(drive(list(rng.choice(target, size=k, replace=False)), edge_df, seed=d, params=params))
    agg = {f: [r[f] for r in out] for f in out[0]}
    return dict(k=k, **{f"{f}_mean": float(np.mean(v)) for f, v in agg.items()},
                **{f"{f}_max": float(np.max(v)) for f, v in agg.items() if f != "dvmn"},
                dvmn_per_draw=[round(x, 2) for x in agg["dvmn"]],
                dvmn_in_band=int(sum(BAND[0] <= x <= BAND[1] for x in agg["dvmn"])))


def selective(r):
    return r["steer_max"] < 1.0 and r["b1_max"] < 1.0 and r["dlmn_max"] < 1.0


def line(tag, r):
    print(f"{tag:<28} DVMn {r['dvmn_mean']:6.2f} Hz ({'/'.join(f'{x:.1f}' for x in r['dvmn_per_draw'])}; "
          f"{r['dvmn_in_band']}/{N_DRAWS} in band) | steer max {r['steer_max']:.2f} | b1 max {r['b1_max']:.2f} | "
          f"DLMn max {r['dlmn_max']:.2f}")


report = dict(benchmark="flight_snpp16_robustness", criteria=CRITERIA, checks={}, arms={})
t0 = time.time()

print("\nR1  targeted transmitter-sign inversion")
r1 = at_k(K_TEST, 1000, edge_df=edges_flipped); line(f"  k={K_TEST}, flipped", r1)
report["arms"]["R1"] = r1
report["checks"]["R1_survives_transmitter_uncertainty"] = bool(r1["dvmn_in_band"] >= 4 and selective(r1))

print("\nR2  relay-layer single-neuron parameters")
base = LIFParams()
r2 = []
for param, val in R2_SWEEP:
    if param == "v_thresh_gap_mV":
        over = {s: {"v_thresh_mV": base.v_rest_mV + val} for s in RELAY_SC}
    else:
        over = {s: {param: val} for s in RELAY_SC}
    r = at_k(K_TEST, 1000, params=LIFParams(superclass_params=over)); r.update(param=param, value=val)
    line(f"  {param}={val}", r); r2.append(r)
report["arms"]["R2"] = r2
report["checks"]["R2_selectivity_holds_across_cord_params"] = bool(all(selective(r) for r in r2))

print("\nR3  fresh cell-identity and phase draws")
r3 = []
for k in range(1, len(target) + 1):
    r = at_k(k, FRESH_SEED_BASE); line(f"  k={k:>2}", r); r3.append(r)
    (OUT / "report.json").write_text(json.dumps(report | dict(R3_partial=r3), indent=2, default=float))
in_band = [r for r in r3 if BAND[0] <= r["dvmn_mean"] <= BAND[1]]
kstar_fresh = in_band[0]["k"] if in_band else None
r3_k7 = next(r for r in r3 if r["k"] == K_TEST)
means = [r["dvmn_mean"] for r in r3]
report["arms"]["R3"] = dict(sweep=r3, k_star=kstar_fresh,
                            monotone_within_0p5=bool(all(means[i + 1] >= means[i] - 0.5 for i in range(len(means) - 1))))
report["checks"]["R3_replicates_with_fresh_draws"] = bool(
    kstar_fresh is not None and abs(kstar_fresh - K_STAR_ORIG) <= 1 and r3_k7["dvmn_in_band"] >= 4)
print(f"  fresh k* = {kstar_fresh} (original {K_STAR_ORIG}); monotone within 0.5 Hz: "
      f"{report['arms']['R3']['monotone_within_0p5']} (reported, not scored)")

report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print(f"\nCHECKS (criteria registered before the run) | {round(time.time() - t0)}s")
for kk, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {kk}")
print(f"\nBATTERY {'PASS' if all(report['checks'].values()) else 'FAIL'}  -> {OUT / 'report.json'}")
