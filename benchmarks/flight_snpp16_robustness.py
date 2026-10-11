"""
Robustness of the SNpp16 selectivity claim, with criteria registered before the run.

The claim (benchmarks/flight_snpp16_graded.py, 4/5 pre-registered criteria): SNpp16, 13 wing
campaniform afferents, drives the DVM motor neurons without recruiting any steering muscle,
reliably from about seven of its thirteen cells, through its actual wiring. This battery asks
whether that claim survives three things it could plausibly rest on. Criteria are fixed below and
written to results/flight_snpp16_robustness/criteria.json, stamped with the commit, before any
simulation; the script refuses to run against changed criteria.

  R1  transmitter uncertainty. Invert the sign of every neuron whose own per-T-bar predictions
      disagree in sign with its aggregate label (fit/synapse_nt.py; 1.6% of the model's signed weight). At k=7:
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
from brian2 import Synapses, mV
from flycns import load_graph, CNSModel, LIFParams
from flycns import registry, stats
from flycns.bench import provenance, spike_source
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

# ---- version 2 registration (flycns/registry.py): criteria, bands and the frozen model, before any data.
# It supersedes the version 1 registration below (criteria.json), which is kept as it was.
LABEL = "flight_snpp16_robustness"
_SEL = "steering MN, b1 MN and DLMn c-f each below 1 Hz in every draw (per_draw need 1.0; the check is strict, per_draw's edge is inclusive)"
CRITERIA_V2 = dict(
    version=2,
    claim=f"{TARGET} selectively drives DVM motor neurons, reliably from k={K_TEST}",
    protocol=dict(
        n_cycles=N_CYCLES, wingbeat_hz=WINGBEAT_HZ, jitter_ms=JITTER_MS, n_draws=N_DRAWS, k_test=K_TEST,
        band=list(BAND), target_type=TARGET,
        drive=("draw d at k recruits k cells chosen with seed SEED_BASE + 17 k + d, each firing one spike per wingbeat "
               "cycle at a uniform random phase with gaussian jitter (an 8 mV kick into each afferent), after 200 ms "
               "of settling"),
        R1=(f"k={K_TEST} on the targeted transmitter-sign inversion (FLYCNS_SIGNFLIP_TARGETED=1: every neuron whose "
            f"per-T-bar predictions disagree in sign with its aggregate label, data/edges_nt.parquet); cells seed "
            f"base 1000, phase seed d"),
        R2_sweep=R2_SWEEP,
        R2=(f"k={K_TEST}, one parameter at a time for the relay-layer superclasses (read from the data: superclasses "
            f"of the excitatory relays onto DLMn c-f, sensory excluded); cells seed base 1000, phase seed d"),
        R3=(f"k = 1 .. the number of {TARGET} cells with fresh draws: cells seed base {FRESH_SEED_BASE}, phase seed "
            f"{FRESH_SEED_BASE} + d"),
        k_star_original=K_STAR_ORIG,
        scoring=("per draw (stats.per_draw): DVMn 1a-c in band needs 4 of 5 draws (need 0.8, FAIL at most 1); "
                 "steering, b1 and DLMn c-f below 1 Hz need every draw (need 1.0, FAIL if none)")),
    checks=dict(
        R1_survives_transmitter_uncertainty=dict(
            bands=[list(BAND), [None, 1.0]], conditional=True,
            condition=("scored only if the inversion flips a connection on the path under test (both ends among the "
                       f"driven {TARGET} cells, the readouts and the relay layer); otherwise UNRESOLVED "
                       "(stats.unresolved, no band)"),
            rule=(f"on the flipped graph at k={K_TEST}: DVMn 1a-c in 2-12 Hz in at least 4 of {N_DRAWS} draws "
                  f"(first band), and {_SEL} (second band)")),
        R2_selectivity_holds_across_cord_params=dict(
            bands=[[None, 1.0]], conditional=True,
            condition="scored only if a relay superclass is found in the data; otherwise UNRESOLVED (stats.unresolved, no band)",
            rule=f"at every setting of the sweep, k={K_TEST}: {_SEL}"),
        R3_replicates_with_fresh_draws=dict(
            bands=[list(BAND)], k_star_original=K_STAR_ORIG, k_star_tolerance=1,
            rule=(f"with fresh draws, k* is within 1 of {K_STAR_ORIG} (no k below {K_STAR_ORIG - 1} in band and some k "
                  f"in {K_STAR_ORIG - 1}..{K_STAR_ORIG + 1} in band, 'in band at k' meaning DVMn 1a-c in 2-12 Hz per "
                  f"draw) and DVMn 1a-c at k={K_TEST} is in 2-12 Hz in at least 4 of {N_DRAWS} draws")),
    ),
)
_v1 = OUT / "criteria.json"
REG = registry.register(LABEL, CRITERIA_V2, scripts=[__file__], supersedes=dict(
    file="criteria.json", git_commit=(json.loads(_v1.read_text(encoding="utf-8")).get("git_commit") or None) if _v1.exists() else None))

# Registered test: refuse uncommitted code and data that differ from data/MANIFEST.json, so the
# registered result can be traced to an exact commit and an exact dataset (flycns/integrity.py).
from flycns.integrity import require_clean, require_data, criteria_differ  # noqa: E402
require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem)   # every table pinned in the manifest, rehashed
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/flight_snpp16_robustness.py"],
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
# the driven afferents are excluded: varying their own threshold would change the stimulus, not the relays
RELAY_SC = sorted({sc.get(b, "") for b in exc_relays} - {""} - {s for s in set(sc) if "sensory" in s})
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
    gen = spike_source(len(idx), ids[keep], times[keep])
    S = Synapses(gen, m.G, on_pre="v_post += kick", namespace=dict(kick=8.0 * mV))
    S.connect(i=np.arange(len(idx)), j=np.array(idx))
    m.net.add(gen, S)
    m.run(pre_ms + dur_ms)
    sp = m.spike_frame(); sp = sp[sp.t_ms >= pre_ms]; dur_s = dur_ms / 1000.0

    def rate(ids_):
        ids_ = [b for b in ids_ if b in m.lif_index.index]
        return float(sp.bodyId.isin(ids_).sum() / max(len(ids_), 1) / dur_s)

    return dict(dvmn=rate(dvm), dlmn=rate(dlm), steer=rate(steer), b1=rate(b1))


def at_k(k, seed_base, edge_df=None, params=None, phase_base=0):
    edge_df = edges if edge_df is None else edge_df
    out = []
    for d in range(N_DRAWS):
        rng = np.random.default_rng(seed_base + 17 * k + d)
        out.append(drive(list(rng.choice(target, size=k, replace=False)), edge_df, seed=phase_base + d, params=params))
    agg = {f: [r[f] for r in out] for f in out[0]}
    return dict(k=k, **{f"{f}_mean": float(np.mean(v)) for f, v in agg.items()},
                **{f"{f}_max": float(np.max(v)) for f, v in agg.items() if f != "dvmn"},
                dvmn_per_draw=[round(x, 2) for x in agg["dvmn"]],
                dvmn_in_band=int(sum(BAND[0] <= x <= BAND[1] for x in agg["dvmn"])),
                draws={f: [float(x) for x in v] for f, v in agg.items()})   # unrounded, for the uncertainty records


def selective(r):
    return r["steer_max"] < 1.0 and r["b1_max"] < 1.0 and r["dlmn_max"] < 1.0


def line(tag, r):
    print(f"{tag:<28} DVMn {r['dvmn_mean']:6.2f} Hz ({'/'.join(f'{x:.1f}' for x in r['dvmn_per_draw'])}; "
          f"{r['dvmn_in_band']}/{N_DRAWS} in band) | steer max {r['steer_max']:.2f} | b1 max {r['b1_max']:.2f} | "
          f"DLMn max {r['dlmn_max']:.2f}")


report = dict(benchmark="flight_snpp16_robustness", criteria=CRITERIA, checks={}, arms={})
t0 = time.time()

# R1 is a perturbation test only if the flip touches the path under test. The path: the cells the battery
# drives (every TARGET cell; each draw recruits K_TEST of them) and reads out (DVMn 1a-c, DLMn c-f, steering,
# b1), plus the relay layer defined above (cells receiving >= 20 synapses from the campaniform afferents).
# Count the flipped connections among those cells. The flip itself is unchanged.
_flipped = edges_flipped["sign"].values != edges["sign"].values      # row-aligned: n_flipped > 0 checked above
_ends = set(target) | set(dvm) | set(dlm) | set(steer) | set(b1)
_path = _ends | set(relays)
_on_path = edges.pre.isin(_path).values & edges.post.isin(_path).values
_direct = edges.pre.isin(_ends).values & edges.post.isin(_ends).values
report["R1_flipped_edges_on_path"] = int((_flipped & _on_path).sum())
report["R1_path"] = dict(
    definition=(f"connections with both ends among the driven {TARGET} cells, the readouts (DVMn 1a-c, DLMn c-f, "
                "steering MNs, b1 MN) and the relay layer (cells receiving >= 20 synapses from the campaniform afferents)"),
    n_cells=len(_path), n_connections=int(_on_path.sum()), n_flipped=report["R1_flipped_edges_on_path"],
    n_flipped_driven_and_readout_cells_only=int((_flipped & _direct).sum()), n_flipped_whole_graph=n_flipped)
print(f"targeted sign inversion on the path under test: {report['R1_flipped_edges_on_path']} of "
      f"{report['R1_path']['n_connections']} connections among {len(_path)} cells "
      f"({report['R1_path']['n_flipped_driven_and_readout_cells_only']} between driven and readout cells directly)")

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
    # fresh cells AND fresh phase/jitter draws, as registered (before 2026-10-10 the phases reused seeds 0-4)
    r = at_k(k, FRESH_SEED_BASE, phase_base=FRESH_SEED_BASE); line(f"  k={k:>2}", r); r3.append(r)
    (OUT / "report.json").write_text(json.dumps(report | dict(R3_partial=r3), indent=2, default=float), encoding="utf-8")
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


# ---- uncertainty (flycns/stats.py): one record per scored check, three-way verdict. Every readout is
# repeated over N_DRAWS independent draws (cell identity and phase), so each is scored per draw
# (stats.per_draw), never on the mean. "DVMn in band in >= 4/5 draws" is per_draw at its default need (4 of 5);
# "steering, b1, DLMn each < 1 Hz" is read on the maximum over draws, i.e. in EVERY draw, so need=1.0 keeps
# that band (PASS only if all draws are below 1 Hz, FAIL only if none is). per_draw's edge is inclusive where
# the checks are strict (< 1 Hz); a rate of exactly 1 Hz is the only case that differs.
def _any(records, note=None):
    """Disjunction of parts, the counterpart of stats.combine: PASS if any part passes, FAIL if every part
    fails, else UNRESOLVED. The parts are kept in the record."""
    vs = [r["verdict"] for r in records]
    vd = "PASS" if "PASS" in vs else ("FAIL" if all(v == "FAIL" for v in vs) else "UNRESOLVED")
    rec = dict(estimate=None, ci95=None, band=None, method=f"any of {len(records)} parts", parts=list(records), verdict=vd)
    if note:
        rec["note"] = note
    return rec


def _not(rec, note=None):
    """Negation of a three-way record: PASS and FAIL swap, UNRESOLVED stays."""
    vd = {"PASS": "FAIL", "FAIL": "PASS"}.get(rec["verdict"], "UNRESOLVED")
    out = dict(estimate=None, ci95=None, band=None, method="negation of 1 part", parts=[rec], verdict=vd)
    if note:
        out["note"] = note
    return out


def _selective(r, where):
    """Steering, b1 and DLMn c-f below 1 Hz in every draw (the check reads the maximum over draws)."""
    return [stats.per_draw(r["draws"][f], high=1.0, need=1.0, note=f"{f} {where}, every draw below 1 Hz")
            for f in ("steer", "b1", "dlmn")]


def _rec_text(r):
    """One console line for an uncertainty record: method, estimate [95% interval] or draws, note."""
    txt = r["method"]
    if r.get("ci95") and None not in r["ci95"] and r.get("estimate") is not None:
        txt += f", est {r['estimate']:.3g} [{r['ci95'][0]:.3g}, {r['ci95'][1]:.3g}]"
    elif r.get("draws") is not None:
        txt += f", draws {[round(x, 2) for x in r['draws']]}"
    return txt + (f" ({r['note']})" if r.get("note") else "")


def _print_record(name, u, ind="  ", depth=0):
    print(f"{ind}{u['verdict']:<10}  {name}{': ' if name else ''}{_rec_text(u)}")
    if depth < 1:   # one level of parts on the console; the report keeps them all
        for part in u.get("parts", []):
            _print_record("", part, ind + "    ", depth + 1)


unc = {}
if report["R1_flipped_edges_on_path"] == 0:
    unc["R1_survives_transmitter_uncertainty"] = stats.unresolved(
        "the perturbation touches no connection on the path under test")
else:
    unc["R1_survives_transmitter_uncertainty"] = stats.combine(
        [stats.per_draw(r1["draws"]["dvmn"], *BAND, note=f"DVMn at k={K_TEST}, flipped graph, >= 4 of {N_DRAWS} draws")]
        + _selective(r1, f"at k={K_TEST}, flipped graph"),
        note=f"{report['R1_flipped_edges_on_path']} flipped connections on the path under test")
if RELAY_SC:
    unc["R2_selectivity_holds_across_cord_params"] = stats.combine(
        [stats.combine(_selective(r, f"{r['param']}={r['value']}"), note=f"{r['param']}={r['value']}") for r in r2],
        note=f"selective at every setting; relay superclasses {RELAY_SC}")
else:
    unc["R2_selectivity_holds_across_cord_params"] = stats.unresolved(
        "no relay superclass was found, so the parameter sweep changes no neuron")
# R3: the smallest in-band k within one step of K_STAR_ORIG means no k below the window is in band and some k
# in the window is; "in band at k" is scored per draw at each k (three-valued, so the logic keeps UNRESOLVED)
_inb = {r["k"]: stats.per_draw(r["draws"]["dvmn"], *BAND, note=f"DVMn at k={r['k']}, fresh draws") for r in r3}
_lo, _hi = K_STAR_ORIG - 1, K_STAR_ORIG + 1
_kstar_parts = [stats.combine([_not(_inb[k], note=f"k={k} not in band") for k in sorted(_inb) if k < _lo],
                              note=f"no k below {_lo} in band")] if any(k < _lo for k in _inb) else []
_kstar_parts.append(_any([_inb[k] for k in sorted(_inb) if _lo <= k <= _hi], note=f"some k in {_lo}..{_hi} in band"))
unc["R3_replicates_with_fresh_draws"] = stats.combine(
    [stats.combine(_kstar_parts, note=f"fresh k* within 1 of {K_STAR_ORIG}, with 'in band at k' scored per draw"),
     stats.per_draw(r3_k7["draws"]["dvmn"], *BAND, note=f"DVMn at k={K_TEST}, fresh draws, >= 4 of {N_DRAWS}")],
    note="replication with fresh cell-identity and phase draws")
report["uncertainty"] = unc

# verify_bands skips a conditional check only when its record is absent; a check whose condition was not met
# carries a stats.unresolved record (no band), so the band check reads the records scored as designed
registry.verify_bands(REG, {k: u for k, u in report["uncertainty"].items() if u["method"] != "not scorable as designed"})
report["registration"] = registry.stamp(REG)
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print(f"\nCHECKS (criteria registered before the run) | {round(time.time() - t0)}s")
for kk, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {kk}")
print("\nUNCERTAINTY (flycns/stats.py; three-way verdict, scored per draw)")
for kk, u in report["uncertainty"].items():
    _print_record(kk, u)
print(f"\nBATTERY {'PASS' if all(report['checks'].values()) else 'FAIL'}  -> {OUT / 'report.json'}")
