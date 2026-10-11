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
      Hürkey et al. 2023). The smallest such k is k*, chosen by this rule.
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
from brian2 import Synapses, mV
from flycns import load_graph, CNSModel, LIFParams
from flycns import registry, stats
from flycns.bench import provenance, spike_source
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

# ---- version 2 registration (flycns/registry.py): criteria, bands and the frozen model, before any data.
# It supersedes the version 1 registration below (criteria.json), which is kept as it was.
LABEL = "flight_snpp16_graded"
_K = "scored only if k* exists (some k puts mean DVMn 1a-c in band, the G2 rule); otherwise UNRESOLVED (stats.unresolved, no band)"
CRITERIA_V2 = dict(
    version=2,
    hypothesis=f"{TARGET} selectively drives the DVM motor neurons",
    protocol=dict(
        n_cycles=N_CYCLES, wingbeat_hz=WINGBEAT_HZ, jitter_ms=JITTER_MS, n_draws=N_DRAWS, band=list(BAND),
        target_type=TARGET, partner_type=PARTNER, k=f"1 .. the number of {TARGET} cells",
        draws=("draw d = 0..n_draws-1 at k recruits k cells chosen with seed 1000 + 17 k + d, each firing one "
               "spike per wingbeat cycle at a uniform random phase with gaussian jitter (seed d; an 8 mV kick "
               "into each afferent), after 200 ms of settling"),
        k_star_rule="the smallest k with mean DVMn 1a-c over the draws in 2-12 Hz",
        null="rewire_null(edges, seed=0) at k*, the same cell and phase draws",
        reported=f"{PARTNER} alone (phase seeds 0-2) and k* plus {PARTNER}; not scored",
        scoring=("per draw (stats.per_draw, need 0.8): PASS if 4 of the 5 draws are in band, FAIL if at most 1, "
                 "else UNRESOLVED; G1 on bootstrap intervals of adjacent differences")),
    checks=dict(
        G1_graded=dict(
            bands=[[-0.5, None]],
            rule=("every adjacent step k -> k+1 of mean DVMn 1a-c is at least -0.5 Hz: the bootstrap 95% interval "
                  "of the difference (independent draws) lies at or above -0.5; all steps must pass")),
        G2_in_band_window=dict(
            bands=[list(BAND)],
            rule="some k puts DVMn 1a-c in 2-12 Hz, scored per draw at each k (any of the k)"),
        G3_selective_at_k_star=dict(
            bands=[[None, 1.0]], conditional=True, condition=_K,
            rule=("at k*: steering MN, b1 MN and DLMn c-f rates each below 1 Hz, each scored per draw, all three "
                  "(the check is strict, per_draw's edge is inclusive)")),
        G4_wiring_specific_at_k_star=dict(
            band=[None, 1.0], conditional=True,
            condition=(_K + "; and only if the rewired null fires outside the driven cells in some draw, since a "
                       "silent null cannot fail; otherwise UNRESOLVED"),
            rule="at k*: the rewired null gives DVMn 1a-c below 1 Hz, scored per draw"),
        G5_reliable_at_k_star=dict(
            band=list(BAND), conditional=True, condition=_K,
            rule=f"at k*: DVMn 1a-c in 2-12 Hz in at least 4 of the {N_DRAWS} draws"),
    ),
)
_v1 = OUT / "criteria.json"
REG = registry.register(LABEL, CRITERIA_V2, scripts=[__file__], supersedes=dict(
    file="criteria.json", git_commit=(json.loads(_v1.read_text(encoding="utf-8")).get("git_commit") or None) if _v1.exists() else None))

# ---- register the criteria before simulating anything
# Registered test: refuse uncommitted code and data that differ from data/MANIFEST.json, so the
# registered result can be traced to an exact commit and an exact dataset (flycns/integrity.py).
from flycns.integrity import require_clean, require_data, criteria_differ  # noqa: E402
require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem)   # every table pinned in the manifest, rehashed
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
    if criteria_differ(crit_f, CRITERIA):
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test. "
                         "Delete it deliberately only if the design has genuinely changed.")
else:
    crit_f.write_text(json.dumps(registered, indent=2), encoding="utf-8")
registered = json.loads(crit_f.read_text(encoding="utf-8"))   # the report carries the registration, not this run
reg = registered.get("git_commit") or "?"
print(f"criteria registered at commit {reg}; this run at {commit or '?'}{' (SCRIPT UNCOMMITTED: commit before running)' if dirty else ''}")

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
    gen = spike_source(len(idx), ids[keep], times[keep])
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

    # spikes in cells other than the driven ones: 0 means nothing downstream fired (a silent null cannot
    # fail a "null below 1 Hz" check, so its uncertainty record is UNRESOLVED)
    undriven = int((~sp.bodyId.isin(list(src))).sum())
    return dict(dvmn=rate(dvm), dlmn=rate(dlm), steer=rate(steer), b1=rate(b1), cns=float(m.population_rate_hz()),
                undriven_spikes=undriven)


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
                dvmn_in_band=int(sum(BAND[0] <= x <= BAND[1] for x in agg["dvmn"])),
                draws={f: [float(x) for x in v] for f, v in agg.items()})   # unrounded, for the uncertainty records


report = dict(benchmark="flight_snpp16_graded", criteria=CRITERIA, registration=registered, sweep=[])
t0 = time.time()
for k in range(1, len(target) + 1):
    r = draws_at_k(k)
    report["sweep"].append(r)
    print(f"k={k:>2} | DVMn {r['dvmn_mean']:6.2f} Hz (draws {'/'.join(f'{x:.1f}' for x in r['dvmn_per_draw'])}; "
          f"{r['dvmn_in_band']}/{N_DRAWS} in band) | steer {r['steer_mean']:5.2f} | b1 {r['b1_mean']:5.2f} | "
          f"DLMn {r['dlmn_mean']:4.2f} | CNS {r['cns_mean']:.3f} | {round(time.time() - t0)}s")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")

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


# ---- uncertainty (flycns/stats.py): one record per scored check, three-way verdict. The draws at each k
# are independent seed replicates (cell identity and phase), so readouts are scored per draw (stats.per_draw:
# PASS needs 4 of 5 draws in band, FAIL at most 1), never on the mean of the draws. G1 is a trend of means
# over k and is scored on bootstrap intervals of adjacent differences instead. k* is the registered rule's
# k* (mean-based, unchanged).
def _any(records, note=None):
    """Disjunction of parts, the counterpart of stats.combine: PASS if any part passes, FAIL if every part
    fails, else UNRESOLVED. The parts are kept in the record."""
    vs = [r["verdict"] for r in records]
    vd = "PASS" if "PASS" in vs else ("FAIL" if all(v == "FAIL" for v in vs) else "UNRESOLVED")
    rec = dict(estimate=None, ci95=None, band=None, method=f"any of {len(records)} parts", parts=list(records), verdict=vd)
    if note:
        rec["note"] = note
    return rec


def _rec_text(r):
    """One console line for an uncertainty record: method, estimate [95% interval] or draws, note."""
    txt = r["method"]
    if r.get("ci95") and None not in r["ci95"] and r.get("estimate") is not None:
        txt += f", est {r['estimate']:.3g} [{r['ci95'][0]:.3g}, {r['ci95'][1]:.3g}]"
    elif r.get("draws") is not None:
        txt += f", draws {[round(x, 2) for x in r['draws']]}"
    return txt + (f" ({r['note']})" if r.get("note") else "")


def _print_record(name, u):
    print(f"  {u['verdict']:<10}  {name}: {_rec_text(u)}")
    parts = u.get("parts", [])
    if parts:
        tally = {v: sum(p["verdict"] == v for p in parts) for v in ("PASS", "UNRESOLVED", "FAIL")}
        print(f"      parts: {tally['PASS']} PASS, {tally['UNRESOLVED']} UNRESOLVED, {tally['FAIL']} FAIL")
        for p in parts if len(parts) <= 6 else [p for p in parts if p["verdict"] != "FAIL"][:6]:
            print(f"      {p['verdict']:<10}  {_rec_text(p)}")


unc = {}
g1_parts = []
for a, b in zip(sw[:-1], sw[1:]):
    d, lo, hi = stats.bootstrap_diff(b["draws"]["dvmn"], a["draws"]["dvmn"])
    g1_parts.append(stats.scored(d, lo, hi, low=-0.5, method="bootstrap difference, independent draws", n=N_DRAWS,
                                 note=f"mean DVMn at k={b['k']} minus k={a['k']}"))
unc["G1_graded"] = stats.combine(g1_parts, note="every adjacent step of the mean DVMn >= -0.5 Hz; adjacent k use "
                                               "different cells and seeds, so each step is two independent arms")
unc["G2_in_band_window"] = _any(
    [stats.per_draw(r["draws"]["dvmn"], *BAND, note=f"DVMn at k={r['k']}") for r in sw],
    note="some k with DVMn in band per draw (the registered rule reads the mean over draws)")
if kstar:
    dk = kstar["draws"]
    unc["G3_selective_at_k_star"] = stats.combine(
        [stats.per_draw(dk[f], high=1.0, note=f"{f} at k*={kstar['k']}") for f in ("steer", "b1", "dlmn")],
        note="steering, b1 and DLMn c-f each below 1 Hz per draw (the check is strict; per_draw's edge is inclusive)")
    if sum(null_at_k["draws"]["undriven_spikes"]) > 0:
        unc["G4_wiring_specific_at_k_star"] = stats.per_draw(
            null_at_k["draws"]["dvmn"], high=1.0, note=f"rewired null, DVMn at k*={kstar['k']}; the null fired "
                                                         f"{int(sum(null_at_k['draws']['undriven_spikes']))} spikes "
                                                         f"outside the driven cells, so it can fail")
    else:
        unc["G4_wiring_specific_at_k_star"] = stats.unresolved(
            "the rewired null fired no spike outside the driven cells in any draw, so 'null DVMn below 1 Hz' "
            "cannot fail", estimate=null_at_k["dvmn_mean"])
    unc["G5_reliable_at_k_star"] = stats.per_draw(dk["dvmn"], *BAND, note=f"DVMn at k*={kstar['k']}")
else:
    for kk in ("G3_selective_at_k_star", "G4_wiring_specific_at_k_star", "G5_reliable_at_k_star"):
        unc[kk] = stats.unresolved("no k* (no k put mean DVMn in band, G2), so the condition at k* cannot be evaluated")
report["uncertainty"] = unc

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
# verify_bands skips a conditional check only when its record is absent; a check whose condition was not met
# carries a stats.unresolved record (no band), so the band check reads the records scored as designed
registry.verify_bands(REG, {k: u for k, u in report["uncertainty"].items() if u["method"] != "not scorable as designed"})
report["registration_v1"] = report["registration"]      # the version 1 record (criteria.json), kept
report["registration"] = registry.stamp(REG)
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print("\nCHECKS (criteria registered before the run)")
for kk, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {kk}")
print("\nUNCERTAINTY (flycns/stats.py; three-way verdict on the 95% interval or per draw)")
for kk, u in report["uncertainty"].items():
    _print_record(kk, u)
print(f"\nBENCHMARK {'PASS' if all(report['checks'].values()) else 'FAIL'}  -> {OUT / 'report.json'}")
