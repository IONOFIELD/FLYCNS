"""
Graded test of the claim that SNpp16 selectively drives the DVM motor neurons.

Background. SNpp16, 13 wing campaniform afferents (ADMN), carries 664 of DVMn 1a-c's 1,017
afferent synapses (65%). Driven alone with all 13 cells firing every wingbeat, it drove DVMn to
33.6 Hz and no other flight motor neuron (benchmarks/flight_snpp16.py). That run's pre-stated
checks both failed (not in band, not necessary); the selectivity observation was reported, not
scored. This benchmark scores it, with criteria FIXED BEFORE THE RUN and written to
results/flight_snpp16_graded/criteria.json (stamped with the git commit) before any simulation.

Design. Recruit k of the 13 SNpp16 cells, k = 1..13, phase-locked at the 202 Hz wingbeat
(Vogel 1967) with 0.8 ms jitter (Fox, Fairhall & Daniel 2010). At each k, N_DRAWS draws
randomise WHICH k cells fire as well as their phase, so the result cannot rest on a lucky subset.

Scored criteria:
  G1  graded: mean DVMn 1a-c rate is non-decreasing in k (tolerance 0.5 Hz)
  G2  an in-band window exists: some k gives mean DVMn in 2-12 Hz (Harcombe & Wyman 1977;
      Huerkey et al. 2023). The smallest such k is k*, chosen by this rule.
  G3  selective at k*: mean steering motor neuron rate, b1 and DLMn c-f each below 1 Hz
  G4  wiring-specific at k*: the same spikes into a degree-preserving rewired null give DVMn
      below 1 Hz
  G5  reliable at k*: DVMn in band in at least 4 of the N_DRAWS draws

Reported, not scored:
  - SNpp07 alone (the next strongest type onto DVMn, 5 cells, 130 synapses): is selectivity
    special to SNpp16?
  - SNpp16 at k* plus SNpp07: does supralinear summation reappear at physiological rates?

If G1-G5 all pass, the model makes a specific prediction: activating SNpp16 in a flying fly
should raise DVM motor neuron activity without recruiting the steering muscles.

Run:  python benchmarks/flight_snpp16_graded.py [n_cycles] [data_dir]
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
from flycns.graph import rewire_null

N_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 400
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/flight_snpp16_graded")
OUT.mkdir(parents=True, exist_ok=True)
WINGBEAT_HZ, JITTER_MS = 202.0, 0.8
N_DRAWS = 5
BAND = (2.0, 12.0)
TARGET = os.environ.get("FLYCNS_TARGET_TYPE", "SNpp16")   # override only for toy smoke tests
PARTNER = os.environ.get("FLYCNS_PARTNER_TYPE", "SNpp07")
STEER = r"^(b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"

CRITERIA = dict(
    hypothesis=f"{TARGET} selectively drives the DVM motor neurons",
    G1="mean DVMn 1a-c non-decreasing in k, tolerance 0.5 Hz",
    G2=f"some k gives mean DVMn in {BAND[0]}-{BAND[1]} Hz; smallest such k is k*",
    G3="at k*: mean steering, b1 and DLMn c-f each below 1 Hz",
    G4="at k*: rewired null gives DVMn below 1 Hz",
    G5=f"at k*: DVMn in band in at least 4 of {N_DRAWS} draws",
    n_draws=N_DRAWS, n_cycles=N_CYCLES, wingbeat_hz=WINGBEAT_HZ, jitter_ms=JITTER_MS)

# ---- register the criteria before simulating anything
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/flight_snpp16_graded.py"],
                                capture_output=True, text=True, timeout=5).stdout.strip())
except Exception:
    commit, dirty = "", True
registered = dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                  git_commit=commit, script_uncommitted=dirty)
if crit_f.exists():
    prior = json.loads(crit_f.read_text())
    if prior.get("criteria") != CRITERIA:
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test. "
                         "Delete it deliberately only if the design has genuinely changed.")
else:
    crit_f.write_text(json.dumps(registered, indent=2))
print(f"criteria registered at commit {commit or '?'}{' (SCRIPT UNCOMMITTED: commit before running)' if dirty else ''}")

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna("")
sub = meta["subclass"].fillna("")
nerve = meta["entryNerve"].fillna("")
aff = sorted(meta.index[(sub == "campaniform sensilla") & nerve.isin(["ADMN", "DMetaN"])])
target = sorted(b for b in aff if t[b] == TARGET)
partner = sorted(b for b in aff if t[b] == PARTNER)
dvm = meta.index[t == "DVMn 1a-c"]
dlm = meta.index[t == "DLMn c-f"]
steer = meta.index[t.str.match(STEER)]
b1 = meta.index[t == "b1 MN"]
print(f"{TARGET}: {len(target)} cells | {PARTNER}: {len(partner)} cells | DVMn 1a-c {len(dvm)}")
if not target:
    raise SystemExit(f"{TARGET} not found among campaniform afferents")

_NULL = None


def null_edges():
    global _NULL
    if _NULL is None:
        _NULL = rewire_null(edges, seed=0)
    return _NULL


def drive(src, edge_df, seed):
    m = CNSModel(neurons, edge_df, [], LIFParams(), electrical=True)
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
    sp = m.spike_frame()
    sp = sp[sp.t_ms >= pre_ms]
    dur_s = dur_ms / 1000.0

    def rate(ids_):
        ids_ = [b for b in ids_ if b in m.lif_index.index]
        return float(sp.bodyId.isin(ids_).sum() / max(len(ids_), 1) / dur_s)

    return dict(dvmn=rate(dvm), dlmn=rate(dlm), steer=rate(steer), b1=rate(b1), cns=float(m.population_rate_hz()))


def draws_at_k(k, edge_df=None, extra=()):
    """N_DRAWS draws of k SNpp16 cells (identity and phase randomised), plus any fixed extra cells."""
    edge_df = edges if edge_df is None else edge_df
    out = []
    for d in range(N_DRAWS):
        rng = np.random.default_rng(1000 + 17 * k + d)
        chosen = list(rng.choice(target, size=k, replace=False)) + list(extra)
        out.append(drive(chosen, edge_df, seed=d))
    agg = {f: [r[f] for r in out] for f in out[0]}
    return dict(k=k, **{f"{f}_mean": float(np.mean(v)) for f, v in agg.items()},
                dvmn_per_draw=[round(x, 2) for x in agg["dvmn"]],
                dvmn_in_band=int(sum(BAND[0] <= x <= BAND[1] for x in agg["dvmn"])))


report = dict(benchmark="flight_snpp16_graded", criteria=CRITERIA, registration=registered, sweep=[])
t0 = time.time()
for k in range(1, len(target) + 1):
    r = draws_at_k(k)
    report["sweep"].append(r)
    print(f"k={k:>2} | DVMn {r['dvmn_mean']:6.2f} Hz (draws {'/'.join(f'{x:.1f}' for x in r['dvmn_per_draw'])}; "
          f"{r['dvmn_in_band']}/{N_DRAWS} in band) | steer {r['steer_mean']:5.2f} | b1 {r['b1_mean']:5.2f} | "
          f"DLMn {r['dlmn_mean']:4.2f} | CNS {r['cns_mean']:.3f} | {round(time.time() - t0)}s")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))

sw = report["sweep"]
means = [r["dvmn_mean"] for r in sw]
g1 = all(means[i + 1] >= means[i] - 0.5 for i in range(len(means) - 1))
in_band = [r for r in sw if BAND[0] <= r["dvmn_mean"] <= BAND[1]]
kstar = in_band[0] if in_band else None
g2 = kstar is not None
g3 = bool(kstar and kstar["steer_mean"] < 1.0 and kstar["b1_mean"] < 1.0 and kstar["dlmn_mean"] < 1.0)
null_at_k = None
if kstar:
    print(f"\nk* = {kstar['k']} (smallest k with mean DVMn in band). Running rewired null at k*...")
    null_at_k = draws_at_k(kstar["k"], edge_df=null_edges())
    print(f"null k={kstar['k']} | DVMn {null_at_k['dvmn_mean']:.2f} Hz | steer {null_at_k['steer_mean']:.2f}")
g4 = bool(null_at_k and null_at_k["dvmn_mean"] < 1.0)
g5 = bool(kstar and kstar["dvmn_in_band"] >= 4)
report["k_star"] = kstar["k"] if kstar else None
report["null_at_k_star"] = null_at_k
report["checks"] = {"G1_graded": g1, "G2_in_band_window": g2, "G3_selective_at_k_star": g3,
                    "G4_wiring_specific_at_k_star": g4, "G5_reliable_at_k_star": g5}

# ---- reported, not scored
rep = {}
if partner:
    pa = [drive(partner, edges, seed=d) for d in range(3)]
    rep["partner_alone"] = {f: float(np.mean([x[f] for x in pa])) for f in pa[0]}
    print(f"\n{PARTNER} alone ({len(partner)} cells) | DVMn {rep['partner_alone']['dvmn']:.2f} | "
          f"steer {rep['partner_alone']['steer']:.2f} | b1 {rep['partner_alone']['b1']:.2f}")
    if kstar:
        comb = draws_at_k(kstar["k"], extra=partner)
        rep["k_star_plus_partner"] = dict(dvmn=comb["dvmn_mean"], steer=comb["steer_mean"], b1=comb["b1_mean"])
        s = kstar["dvmn_mean"] + rep["partner_alone"]["dvmn"]
        rep["summation_ratio"] = comb["dvmn_mean"] / s if s > 0 else None
        print(f"{TARGET} k*={kstar['k']} + {PARTNER} | DVMn {comb['dvmn_mean']:.2f} Hz vs sum of parts {s:.2f} "
              f"(ratio {rep['summation_ratio']:.2f})" if rep["summation_ratio"] else "")
report["reported"] = rep
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print("\nCHECKS (criteria registered before the run)")
for kk, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {kk}")
print(f"\nBENCHMARK {'PASS' if all(report['checks'].values()) else 'FAIL'}  -> {OUT / 'report.json'}")
