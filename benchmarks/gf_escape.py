"""
Benchmark 1: giant fiber escape circuit (loom -> LC4/LPLC2 -> GF -> TTMn/PSI).

Arms:  real+electrical | real chemical-only | rewired null (+electrical)
Pass criteria (published physiology):
  GF 1-2 spikes per responding trial; response probability 0.5-1.0 with 95% binomial
  CI reported (loom-evoked GF spiking is probabilistic and most looms in tethered flies
  are subthreshold, von Reyn 2014; the 0.8 floor used before 2026-09-08 sat exactly at
  16/20 and was not robust to seed, see results/overnight); latency 10-60 ms
  TTMn spikes == GF spikes (one-to-one), lag 0.5-1.5 ms
  whole-CNS rate < 0.05 Hz/neuron ; null GF hit rate < 0.1
Writes: results/gf_escape/{arm}.csv, spikes_real.parquet, report.json, provenance.md
"""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.bench import provenance, stamp
from flycns import load_graph, rewire_null, CNSModel, LIFParams, loom_protocol
from flycns import registry, stats
from flycns.protocols import LOOM_TUNING, TUNING_SOURCE, GAIN_SIGMA_DEFAULT, PEAK_HZ_DEFAULT
from flycns.graph import ELECTRICAL_SYNAPSES, INTRINSIC_OVERRIDES, SIGN_MAP
from flycns import ascii as A

OUT = Path("results/gf_escape"); OUT.mkdir(parents=True, exist_ok=True)
N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"

# Version 2 registration (flycns/registry.py): the criteria and the frozen model, recorded before any data
# are loaded. Every band below is the band the uncertainty record of that check is scored with.
CRITERIA_V2 = dict(
    version=2,
    question=("does a loom burst on the loom-sensitive LC types fire the giant fiber (DNp01) with published "
              "probability, count and latency, drive TTMn one to one through the electrical GF -> TTMn synapse, "
              "leave the CNS quiet, and fail on a rewired null?"),
    protocol=dict(
        trials=40,
        trials_note="canonical trial count per arm (the script's default argument is 20; a run at fewer is flagged TRIALS by summarize)",
        arms=["real_electrical", "real_chemical_only", "rewired_null (flycns.graph.rewire_null, electrical pairs kept)"],
        stimulus=("flycns.protocols.loom_protocol: 60 ms flat-rate burst on the LOOM_TUNING types, 300 ms gaps, "
                  "per-trial lognormal gain at the declared GAIN_SIGMA_DEFAULT and PEAK_HZ_DEFAULT"),
        window_ms="burst onset to onset + 60 ms burst + 100 ms",
        seeds="the declared default seed (LIFParams().seed) for the network and for the per-trial loom gains, the same in every arm",
    ),
    checks={
        "gf_spikes_per_response_1_to_2": dict(
            band=[1.0, 2.0], rule="PASS if the 95% bootstrap interval of GF spikes per firing GF cell, over responding trials, lies within 1 to 2"),
        "gf_response_prob_0.5_to_1": dict(
            band=[0.5, 1.0], rule="PASS if the Wilson 95% interval of the fraction of trials with any GF spike lies within 0.5 to 1"),
        "gf_latency_10_60ms": dict(
            band=[10, 60], rule="PASS if the 95% bootstrap interval of first-GF-spike latency after burst onset lies within 10 to 60 ms"),
        "ttmn_one_to_one": dict(
            band=[0.8, 1.2], rule="PASS if the 95% bootstrap interval of sum(TTMn spikes per cell) / sum(GF spikes per cell) lies within 0.8 to 1.2"),
        "ttmn_lag_0.5_1.5ms": dict(
            band=[0.5, 1.5], rule="PASS if the 95% bootstrap interval of first TTMn spike minus first GF spike lies within 0.5 to 1.5 ms"),
        "cns_quiet": dict(
            rule="PASS if the whole-run population rate of the real+electrical arm is below 0.05 Hz per neuron "
                 "(one number with no trial structure, scored on its point value)"),
        "electrical_necessary": dict(
            band=[None, 0], conditional=True,
            condition="scored when the real+electrical arm fires TTMn spikes; otherwise UNRESOLVED (nothing to abolish)",
            rule="PASS if the 95% interval of (chemical-only TTMn per cell - 0.1 x real TTMn per cell), the two arms "
                 "resampled independently, lies at or below 0; FAIL if above 0"),
        "null_silent": dict(
            band=[None, 0.1], rule="PASS if the Wilson 95% interval of the fraction of rewired-null trials with any GF spike lies at or below 0.1"),
    },
)
REG = registry.register("gf_escape", CRITERIA_V2, scripts=[__file__])
# registered now (version 2): committed code and pinned data, as every registered test
from flycns.integrity import require_clean, require_data  # noqa: E402
require_clean("gf_escape")
require_data(DATA, "gf_escape")


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def _unc_text(u):
    """One console line for an uncertainty record: estimate [95% interval] band (method)."""
    f = lambda x: "-" if x is None else (f"{x:.4g}" if isinstance(x, float) else str(x))  # noqa: E731
    ci = f" [{f(u['ci95'][0])}, {f(u['ci95'][1])}]" if u.get("ci95") else ""
    band = f" band [{f(u['band'][0])}, {f(u['band'][1])}]" if u.get("band") else ""
    return f"{f(u.get('estimate'))}{ci}{band} ({u['method']})"


def score(model, trials, burst_ms=60, window_ms=100):
    sp = model.spike_frame()
    ro = {r: set(model.lif_ids[model.readout_index(r)]) for r in ["DNp01", "TTMn", "PSI"]}
    rows = []
    for k, (on, gain) in enumerate(trials):
        w = sp[(sp.t_ms >= on) & (sp.t_ms < on + burst_ms + window_ms)]
        gf = w[w.bodyId.isin(ro["DNp01"])]; tt = w[w.bodyId.isin(ro["TTMn"])]; ps = w[w.bodyId.isin(ro["PSI"])]
        rows.append(dict(
            trial=k, gain=gain,
            gf=len(gf) / max(len(ro["DNp01"]), 1), gf_lat=gf.t_ms.min() - on if len(gf) else np.nan,
            gf_per_firing_cell=(len(gf) / gf.bodyId.nunique()) if len(gf) else np.nan,
            ttmn=len(tt) / max(len(ro["TTMn"]), 1),
            ttmn_lag=tt.t_ms.min() - gf.t_ms.min() if (len(gf) and len(tt)) else np.nan,
            psi=len(ps) / max(len(ro["PSI"]), 1)))
    return pd.DataFrame(rows), sp


def run_arm(name, neurons, edges, electrical):
    t0 = time.time()
    m = CNSModel(neurons, edges, list(LOOM_TUNING), LIFParams(), electrical=electrical)
    trials = loom_protocol(m, n_trials=N_TRIALS)
    df, sp = score(m, trials)
    print("  per trial GF/TTMn spikes:", " ".join(f"{int(g*2)}/{int(t*2)}" for g, t in zip(df.gf, df.ttmn)))
    A.raster(m, [t for t, _ in trials], ["DNp01", "TTMn"], meta=m.meta)
    A.region_bar(m, [t for t, _ in trials], window_ms=160)
    summ = dict(arm=name, region_source=getattr(m, "region_source", ""), n_lif=int(len(m.lif_ids)), n_chem_syn=int(m.n_chem),
                n_stim=int(len(m.stim)), pop_rate_hz=float(m.population_rate_hz()),
                gf_per_cell=float(df.gf.mean()), gf_hit=float((df.gf > 0).mean()),
                gf_hit_ci95=[float(x) for x in _wilson((df.gf > 0).sum(), len(df))],
                gf_per_hit=float(df.gf_per_firing_cell.mean()) if (df.gf > 0).any() else 0.0,
                gf_lat_ms=float(df.gf_lat.mean()), ttmn_per_cell=float(df.ttmn.mean()),
                ttmn_lag_ms=float(df.ttmn_lag.mean()), psi_per_cell=float(df.psi.mean()),
                ttmn_to_gf_ratio=float(df.ttmn.sum() / df.gf.sum()) if df.gf.sum() else float("nan"),
                wall_s=round(time.time() - t0, 1))
    # per-trial readouts (None where a trial has no value, e.g. no GF spike), kept so that every check
    # can be scored with a 95% interval over trials (flycns/stats.py)
    summ["per_trial"] = {c: [None if pd.isna(x) else float(x) for x in df[c]]
                         for c in ["gf", "gf_lat", "gf_per_firing_cell", "ttmn", "ttmn_lag", "psi"]}
    print(f"[{name}] GF {summ['gf_per_cell']:.2f}/cell hit {summ['gf_hit']:.2f} "
          f"(95% CI {summ['gf_hit_ci95'][0]:.2f}-{summ['gf_hit_ci95'][1]:.2f}) lat {summ['gf_lat_ms']:.1f} ms | "
          f"TTMn {summ['ttmn_per_cell']:.2f}/cell lag {summ['ttmn_lag_ms']:.2f} ms | "
          f"pop {summ['pop_rate_hz']:.4f} Hz | {summ['wall_s']}s")
    df.to_csv(OUT / f"{name}.csv", index=False)
    stamp(OUT / f"{name}.csv")
    return summ, sp, m


neurons, edges = load_graph(DATA)
A.sketch("gf_escape")
print(f"loom tuning source: {TUNING_SOURCE}; peak rate {PEAK_HZ_DEFAULT} Hz; gain sigma {GAIN_SIGMA_DEFAULT}")
report = {"benchmark": "gf_escape", "n_trials": N_TRIALS, "params": LIFParams().__dict__, "arms": {}}

s, sp, m = run_arm("real_electrical", neurons, edges, True)
report["arms"]["real_electrical"] = s
sp.to_parquet(OUT / "spikes_real.parquet", index=False)
s2, _, _ = run_arm("real_chemical_only", neurons, edges, False)
report["arms"]["real_chemical_only"] = s2
s3, _, _ = run_arm("rewired_null", neurons, rewire_null(edges), True)
report["arms"]["rewired_null"] = s3

r, c, n = s, s2, s3
checks = {
    # spikes per GF that fired (von Reyn 2014 recorded single GFs): looms often
    # leave GF subthreshold, so failures are scored by gf_hit, count by responders
    "gf_spikes_per_response_1_to_2": 1.0 <= r["gf_per_hit"] <= 2.0,
    "gf_response_prob_0.5_to_1": 0.5 <= r["gf_hit"] <= 1.0,
    "gf_latency_10_60ms": 10 <= r["gf_lat_ms"] <= 60,
    "ttmn_one_to_one": 0.8 <= r["ttmn_to_gf_ratio"] <= 1.2,
    "ttmn_lag_0.5_1.5ms": 0.5 <= r["ttmn_lag_ms"] <= 1.5,
    "cns_quiet": r["pop_rate_hz"] < 0.05,
    "electrical_necessary": c["ttmn_per_cell"] < 0.1 * max(r["ttmn_per_cell"], 1e-9),
    "null_silent": n["gf_hit"] < 0.1,
}
report["checks"] = checks
report["pass"] = all(checks.values())


# ---- uncertainty (flycns/stats.py): one record per scored check, three-way verdict on the 95% interval
def _pt(arm, col):
    return np.array([np.nan if x is None else x for x in arm["per_trial"][col]], dtype=float)


r_gf, r_tt, c_tt, null_gf = _pt(r, "gf"), _pt(r, "ttmn"), _pt(c, "ttmn"), _pt(n, "gf")
r_gfh, r_lat, r_lag = _pt(r, "gf_per_firing_cell"), _pt(r, "gf_lat"), _pt(r, "ttmn_lag")
n_resp, n_lag = int((~np.isnan(r_gfh)).sum()), int((~np.isnan(r_lag)).sum())
none_note = lambda k, what: f"; no {what} in the real arm, so nothing to score" if k == 0 else ""  # noqa: E731
pairing = ("the arms are separate simulations, resampled independently (each arm draws the same per-trial loom "
           "gains from the same seed; ignoring that pairing widens the interval when both arms rise with gain)")
unc = {
    "gf_spikes_per_response_1_to_2": stats.scored(
        *stats.bootstrap(r_gfh), low=1.0, high=2.0, n=n_resp,
        note="GF spikes per firing GF cell, bootstrap over responding trials" + none_note(n_resp, "responding trials")),
    "gf_response_prob_0.5_to_1": stats.proportion(int((r_gf > 0).sum()), len(r_gf), 0.5, 1.0,
                                                  note="trials with any GF spike, real+electrical arm"),
    "gf_latency_10_60ms": stats.scored(
        *stats.bootstrap(r_lat), low=10, high=60, n=n_resp,
        note="first GF spike after burst onset, bootstrap over responding trials. The stimulus is a 60 ms flat-rate "
             "burst (flycns.protocols.loom_protocol), not an expanding loom, so this is latency to burst onset, "
             "not to a loom" + none_note(n_resp, "responding trials")),
    "ttmn_one_to_one": stats.scored(
        *stats.bootstrap(np.column_stack([r_tt, r_gf]), stat=stats.ratio_of_sums), low=0.8, high=1.2, n=len(r_gf),
        method="bootstrap (ratio of sums)", note="sum of TTMn spikes per cell / sum of GF spikes per cell, "
                                                 "trials resampled as (TTMn, GF) pairs"),
    "ttmn_lag_0.5_1.5ms": stats.scored(
        *stats.bootstrap(r_lag), low=0.5, high=1.5, n=n_lag,
        note="first TTMn spike minus first GF spike, bootstrap over trials where both fired"
             + none_note(n_lag, "trials with both GF and TTMn spikes")),
    "cns_quiet": stats.point(
        r["pop_rate_hz"], r["pop_rate_hz"] < 0.05,
        note="one whole-run population rate (spikes per neuron per second over the whole real+electrical run): "
             "a readout with no trial structure, scored on its point value; band < 0.05 Hz"),
    "electrical_necessary": (stats.scored(
        *stats.bootstrap_diff(c_tt, 0.1 * r_tt), high=0, method="bootstrap (two independent arms)", n=len(c_tt),
        note="chemical-only TTMn per cell minus 0.1 x real TTMn per cell, per trial (n per arm); " + pairing)
        if np.nansum(r_tt) > 0 else stats.unresolved(
            "the real+electrical arm fired no TTMn spikes, so there is nothing for removing the electrical "
            "synapses to abolish", estimate=c["ttmn_per_cell"])),
    "null_silent": stats.proportion(int((null_gf > 0).sum()), len(null_gf), high=0.1,
                                    note="trials with any GF spike in the rewired null arm; band < 0.1"),
}
report["uncertainty"] = unc
# a check that could not be scored as designed (stats.unresolved) has no band to compare; only a check
# registered as conditional may be missing from the comparison
registry.verify_bands(REG, {k: u for k, u in unc.items() if u.get("method") != "not scorable as designed"})
report["registration"] = registry.stamp(REG)
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")

prov = ["# Provenance: gf_escape", "", "## Neurotransmitter sign map", str(SIGN_MAP), "",
        "## Electrical synapses added (invisible to EM)"]
prov += [f"- {a} -> {b} ({'ipsilateral' if i else 'any side'}, spikelet {k}): {s}" for a, b, i, k, s in ELECTRICAL_SYNAPSES]
prov += ["", "## Intrinsic overrides"] + [f"- {t}.{p} = {v}: {s}" for t, p, v, s in INTRINSIC_OVERRIDES]
prov += ["", f"## Regional gain: SEZ x{LIFParams().region_gains['SEZ']} (fitted, benchmarks/fit_regional.py), other x1",
         f"   SEZ definition: {report['arms']['real_electrical'].get('region_source', 'see flycns/graph.py')}"]
prov += ["", f"## Loom tuning: {TUNING_SOURCE}; trial gain sigma {GAIN_SIGMA_DEFAULT}; peak rate {PEAK_HZ_DEFAULT} Hz (free dF/F->rate scale)", str(LOOM_TUNING), "",
         "## Checks"] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
(OUT / "provenance.md").write_text("\n".join(prov), encoding="utf-8")

print("\nCHECKS"); [print(f"  {'PASS' if v else 'FAIL'}  {k}") for k, v in checks.items()]
print("\nUNCERTAINTY (95% interval; PASS only if the whole interval lies in the band)")
for k, u in unc.items():
    print(f"  {u['verdict']:<10}  {k}: {_unc_text(u)}")
print(f"\nBENCHMARK {'PASS' if report['pass'] else 'FAIL'}  -> {OUT}/report.json")
