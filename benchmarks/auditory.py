"""
Benchmark 3: Johnston's organ -> giant fiber (mechanosensory input to escape).

Why this circuit: JON -> GF is a documented MIXED synapse, electrical (shakB) plus
cholinergic chemical (Pezier et al. 2014, J Neurosci 34:11691); shakB2 abolishes JON-GF
transmission (Pezier et al. 2016, PLoS One 11:e0152211). The model represents it as electrical
only, calibrated to a subthreshold compound potential. In vivo, sound alone leaves GF
subthreshold and summates with visual drive (von Reyn 2014). That yields
ablation predictions with opposite signs to the GF->TTMn case:

  A1 JO-A/B drive alone (pulse-song rates): GF response probability low, <= 0.3
  A2 REPORTED, NOT SCORED: effect of JO drive on GF response to a NEAR-THRESHOLD loom.
     The working point is calibrated per run (sweep of loom gain; take the largest gain
     with GF hit rate <= 0.3 and mean depolarisation >= 2 mV), because the direction of
     the effect depends on where the loom sits relative to threshold: with a loom that
     already fires GF there is only room to suppress, with one that never depolarises GF
     only room to facilitate. Earlier runs reported both directions at fixed gains (0.55
     -> 0.20 with the ordinal tuning at gain 0.6; 0.00 -> 0.07 with the measured tuning
     at the same gain) before this calibration existed; neither is quotable. The in vivo
     direction is not established in our references (von Reyn 2014 tested visual-visual
     integration; Pezier and colleagues characterised the JON-GF synapse itself).
  A3 pathway ablation: MaleCNS EM annotates the mixed JON-GF contact as
     chemical (679 synapses). Removing BOTH the electrical model and those
     EM edges must abolish the JO-evoked GF depolarisation (measured from GF
     membrane voltage); with the electrical model it
     must exceed 0.5 mV. "chem_only_EM" (EM as annotated, no electrical) is
     reported for reference: it double-counts nothing but mislabels the contact.
  A4 rewired null, chemical only: no JO -> GF depolarisation (the electrical
     pairs are declared anatomy and bypass rewiring, so they are removed here)
  A5 CNS stays quiet (< 0.05 Hz/neuron)

JO-A and JO-B are the vibration-sensitive subgroups (Kamikouchi et al. 2009);
pulse song drives them at ~100-200 Hz burst rates.
Writes results/auditory/{report.json, provenance.md, *.csv}
"""
import json, os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import load_graph, rewire_null, CNSModel, LIFParams
from flycns import stats
from flycns.graph import drop_mixed_chemical
from flycns.protocols import LOOM_TUNING
from flycns.bench import find_types, pulse_protocol
from flycns.graph import afferents_by_subclass
from flycns.bench import provenance
from flycns import ascii as A

# FLYCNS_AUDITORY_OUT redirects the report (used by benchmarks/a2_robustness.py so a sweep never
# overwrites the suite's own results/auditory/report.json).
OUT = Path(os.environ.get("FLYCNS_AUDITORY_OUT", "results/auditory")); OUT.mkdir(parents=True, exist_ok=True)
# FLYCNS_A2_GAIN fixes the A2 working point instead of calibrating it; FLYCNS_A2_ONLY=1 runs only the
# two A2 arms. Both exist for the registered robustness sweep; with neither set, behaviour is unchanged.
A2_GAIN_FIXED = os.environ.get("FLYCNS_A2_GAIN")
A2_ONLY = os.environ.get("FLYCNS_A2_ONLY") == "1"
N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
# A2 compares two response probabilities, so it needs far more trials than the pass/fail
# checks: 20 trials cannot separate 0.15 from 0.30 (3 vs 6 events). Set FLYCNS_A2_TRIALS
# to run it properly (>=120 per arm); with fewer, A2 reports "unresolved".
A2_TRIALS = int(os.environ.get("FLYCNS_A2_TRIALS", str(N_TRIALS)))
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
JO_HZ = 150
SUB_LOOM_GAIN = None    # calibrated per run: largest gain with hit rate <= 0.3 and GF depolarised

neurons, edges = load_graph(DATA)
A.sketch("auditory")
meta = neurons.set_index("bodyId")
# Modality from the connectome's own annotation, not the A/B type names: MaleCNS labels JO
# neurons auditory / wind_gravity / grooming, and JO-B2, B3 and B4 are mostly wind_gravity.
jo_types = afferents_by_subclass(neurons, ["auditory"], "JO-") or \
           [t for t in find_types(neurons, [r"^JO-A", r"^JO-B"]) if not t.endswith("unclear")]
jo_types = [t for t in jo_types if not t.endswith("unclear")]
wind_types = afferents_by_subclass(neurons, ["wind_gravity"], "JO-") or ["JO-FV"]
n_jo = int(neurons.type.isin(jo_types).sum())
print(f"auditory JO types ({len(jo_types)}, {n_jo} neurons): {jo_types}")
print(f"wind/gravity control types ({len(wind_types)}): {wind_types[:6]}{'...' if len(wind_types) > 6 else ''}")
if not jo_types:
    raise SystemExit("no JO-A/JO-B types found")
report = {"benchmark": "auditory", "n_trials": N_TRIALS, "jo_types": jo_types, "jo_hz": JO_HZ,
          "arms": {}, "checks": {}}


def gf_stats(model, onsets, window_ms=160):
    sp = model.spike_frame()
    gf_ids = set(model.lif_ids[model.readout_index("DNp01")])
    rows = []
    for on in onsets:
        w = sp[(sp.t_ms >= on) & (sp.t_ms < on + window_ms) & sp.bodyId.isin(gf_ids)]
        rows.append(dict(gf=len(w) / max(len(gf_ids), 1), hit=int(len(w) > 0),
                         lat=(w.t_ms.min() - on) if len(w) else np.nan))
    df = pd.DataFrame(rows)
    # per_trial keeps the values the means average away (None where a trial has no GF spike), so the
    # checks can be scored with 95% intervals over trials (flycns/stats.py)
    return dict(gf_per_cell=float(df.gf.mean()), gf_hit=float(df.hit.mean()),
                gf_lat_ms=float(df.lat.mean()), pop_rate_hz=float(model.population_rate_hz()),
                per_trial=dict(gf=[float(x) for x in df.gf], hit=[int(x) for x in df.hit],
                               lat_ms=[None if pd.isna(x) else float(x) for x in df.lat]))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def two_prop_ci(k1, n1, k2, n2, z=1.96):
    """95% CI on p2 - p1, Newcombe (1998) hybrid score interval, method 10.

    lower = d - sqrt((p2 - l2)^2 + (u1 - p1)^2),  upper = d + sqrt((u2 - p2)^2 + (p1 - l1)^2),
    with (l, u) the Wilson score limits of each proportion. Checked against Newcombe's worked
    example (56/70 vs 48/80 -> 0.0524 to 0.3339). CORRECTION 2026-09-25: an earlier version paired
    each bound with the other bound's Wilson limits and multiplied by an extra z, making every A2
    interval reported before this date roughly twice too wide.
    """
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z); l2, u2 = wilson(k2, n2, z)
    d = p2 - p1
    lo = d - np.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    hi = d + np.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return d, lo, hi


def _unc_text(u):
    """One console line for an uncertainty record: estimate [95% interval] band (method)."""
    f = lambda x: "-" if x is None else (f"{x:.4g}" if isinstance(x, float) else str(x))  # noqa: E731
    ci = f" [{f(u['ci95'][0])}, {f(u['ci95'][1])}]" if u.get("ci95") else ""
    band = f" band [{f(u['band'][0])}, {f(u['band'][1])}]" if u.get("band") else ""
    return f"{f(u.get('estimate'))}{ci}{band} ({u['method']})"


def _pt(arm, key):
    """An arm's per-trial values as a float array (NaN where the trial has no value)."""
    return np.array([np.nan if x is None else x for x in arm["per_trial"][key]], dtype=float)


# Seeds (audit 2026-10-11, gap 7). Before, every arm ran at the same seed, so the calibration arm at
# the chosen gain was bit-identical to the scored loom-alone arm: the trials that chose the working
# point were the trials that scored it. Now the calibration arms draw their own seeds, disjoint from
# the scored arms, and the two scored A2 arms draw different seeds, so they are independent samples
# (what the Newcombe interval assumes).
BASE_SEED = LIFParams().seed
CAL_SEED = BASE_SEED + 1000          # calibration arms: BASE_SEED + 1000 + index of the gain
A2_SEEDS = dict(loom_alone=BASE_SEED, loom_plus_jo=BASE_SEED + 1)


def run(label, stim_types, electrical=True, edge_df=edges, jo=True, loom=False, n_trials=None, seed=None):
    t0 = time.time()
    m = CNSModel(neurons, edge_df, stim_types, LIFParams(seed=BASE_SEED if seed is None else seed),
                 electrical=electrical, monitor_types=("DNp01",))
    N = N_TRIALS if n_trials is None else n_trials
    if loom and jo:
        # loom protocol drives LC types; add JO at fixed rate during each loom burst
        tuning = m.stim["type"].map(LOOM_TUNING).fillna(0).values
        is_jo = m.stim["type"].isin(jo_types).values
        onsets = []
        for _ in range(N):
            m.run(300); onsets.append(m.t_ms)
            m.set_stim_rates(tuning * 5.0 * SUB_LOOM_GAIN + is_jo * JO_HZ); m.run(60)
            m.set_stim_rates(np.zeros(len(m.stim)))
        m.run(300)
    elif loom:
        tuning = m.stim["type"].map(LOOM_TUNING).fillna(0).values
        onsets = []
        for _ in range(N):
            m.run(300); onsets.append(m.t_ms)
            m.set_stim_rates(tuning * 5.0 * SUB_LOOM_GAIN); m.run(60)
            m.set_stim_rates(np.zeros(len(m.stim)))
        m.run(300)
    else:
        onsets = pulse_protocol(m, {t: JO_HZ for t in stim_types}, n_trials=N, pulse_ms=60)
    s = gf_stats(m, onsets); s["wall_s"] = round(time.time() - t0, 1); s["n_trials"] = len(onsets)
    A.raster(m, onsets, ["DNp01"], window_ms=100, max_trials=2)
    depol = m.peak_depolarization_mV(onsets, 100)
    s["gf_depol_mV"] = float(np.nanmean(depol))
    s["per_trial"]["depol_mV"] = [None if np.isnan(x) else float(x) for x in depol]
    print(f"[{label}] GF {s['gf_per_cell']:.2f}/cell hit {s['gf_hit']:.2f} lat {s['gf_lat_ms']:.1f} ms "
          f"depol {s['gf_depol_mV']:.2f} mV | CNS {s['pop_rate_hz']:.4f} Hz | {s['wall_s']}s")
    report["arms"][label] = s
    return s


# ---- calibrate the near-threshold loom working point
CAL_GAINS = [0.4, 0.6, 0.8, 1.0, 1.3]
cal = []
for i, g in enumerate([] if A2_GAIN_FIXED else CAL_GAINS):
    SUB_LOOM_GAIN = g
    globals()["SUB_LOOM_GAIN"] = g
    c = run(f"cal_loom_gain_{g}", list(LOOM_TUNING), electrical=True, jo=False, loom=True, seed=CAL_SEED + i)
    cal.append((g, c["gf_hit"], c["gf_depol_mV"]))
    print(f"  calibration: loom gain {g} -> GF hit {c['gf_hit']:.2f}, depol {c['gf_depol_mV']:.2f} mV")
ok = [(g, h, d) for g, h, d in cal if h <= 0.3 and d >= 2.0]
SUB_LOOM_GAIN = float(A2_GAIN_FIXED) if A2_GAIN_FIXED else (max(g for g, _, _ in ok) if ok else CAL_GAINS[0])
globals()["SUB_LOOM_GAIN"] = SUB_LOOM_GAIN
report["arms"]["A2_calibration"] = dict(gains=[dict(gain=g, hit=h, depol_mV=d) for g, h, d in cal],
                                        chosen_gain=SUB_LOOM_GAIN,
                                        rule=("fixed by FLYCNS_A2_GAIN" if A2_GAIN_FIXED else
                                              "largest gain with GF hit <= 0.3 and depol >= 2 mV"))
print(f"A2 working point: loom gain {SUB_LOOM_GAIN}")


def construction_prediction(lo, a2):
    """What summation alone predicts for loom + sound (audit gap 1): a loom-alone trial would become a
    giant fiber response if its peak depolarisation plus the declared compound sound potential reaches
    the rest-to-threshold gap. The facilitation the model shows beyond this is the part that is not
    arithmetic (polysynaptic effects, timing); only that residual can be a test."""
    from flycns.graph import jon_compound_mv, jon_mode
    p = LIFParams()
    gap = p.v_thresh_mV - p.v_rest_mV
    c = jon_compound_mv() if jon_mode() == "electrical" else 0.0
    hit = np.asarray(lo["per_trial"]["hit"], dtype=float)
    dep = np.asarray([np.nan if x is None else x for x in lo["per_trial"]["depol_mV"]], dtype=float)
    pred = np.where(hit > 0, 1.0, np.where(np.isnan(dep), np.nan, (dep + c >= gap).astype(float)))
    obs = np.asarray(a2["per_trial"]["hit"], dtype=float)
    est, rlo, rhi = stats.bootstrap_diff(obs, pred)
    return dict(compound_mV=c, gap_mV=gap, jon_mode=jon_mode(), loom_alone_hit=float(np.nanmean(hit)),
                predicted_hit_by_summation=float(np.nanmean(pred)), observed_hit=float(np.nanmean(obs)),
                residual=est, residual_ci95=[rlo, rhi],
                note=("residual = observed loom+sound response probability minus the probability predicted by adding "
                      "the declared compound potential to each loom-alone trial's peak depolarisation; arms are "
                      "independent (different seeds), so the interval resamples each on its own"))

if A2_ONLY:
    lo = run("subthreshold_loom_alone", list(LOOM_TUNING), electrical=True, jo=False, loom=True, n_trials=A2_TRIALS,
             seed=A2_SEEDS["loom_alone"])
    a2 = run("A2_loom_plus_jo", list(LOOM_TUNING) + jo_types, electrical=True, jo=True, loom=True, n_trials=A2_TRIALS,
             seed=A2_SEEDS["loom_plus_jo"])
    k1, n1 = int(round(lo["gf_hit"] * lo["n_trials"])), lo["n_trials"]
    k2, n2 = int(round(a2["gf_hit"] * a2["n_trials"])), a2["n_trials"]
    d, dlo, dhi = two_prop_ci(k1, n1, k2, n2)
    report["arms"]["A2_prediction"] = dict(loom_gain=SUB_LOOM_GAIN, n_trials_per_arm=n1,
        loom_alone_hit=lo["gf_hit"], loom_plus_jo_hit=a2["gf_hit"], difference=d, difference_ci95=[dlo, dhi],
        loom_alone_depol_mV=lo["gf_depol_mV"], loom_plus_jo_depol_mV=a2["gf_depol_mV"], mode="A2 only",
        seeds=A2_SEEDS, calibration_seed_base=CAL_SEED)
    report["arms"]["A2_construction"] = construction_prediction(lo, a2)
    report["provenance"] = provenance()
    (OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    print(f"A2 only at gain {SUB_LOOM_GAIN}: {lo['gf_hit']:.3f} -> {a2['gf_hit']:.3f}, difference {d:+.3f} "
          f"(95% CI {dlo:+.3f} to {dhi:+.3f})")
    sys.exit(0)

a1 = run("A1_jo_alone_electrical", jo_types, electrical=True)
a3 = run("A3_jo_alone_no_electrical_no_mixed_edges", jo_types, electrical=False,
         edge_df=drop_mixed_chemical(edges, neurons))
ref = run("ref_jo_alone_chem_only_EM_as_annotated", jo_types, electrical=False)
lo = run("subthreshold_loom_alone", list(LOOM_TUNING), electrical=True, jo=False, loom=True, n_trials=A2_TRIALS,
         seed=A2_SEEDS["loom_alone"])
a2 = run("A2_loom_plus_jo", list(LOOM_TUNING) + jo_types, electrical=True, jo=True, loom=True, n_trials=A2_TRIALS,
         seed=A2_SEEDS["loom_plus_jo"])
a4 = run("A4_jo_rewired_null_chem", jo_types, electrical=False,
         edge_df=rewire_null(drop_mixed_chemical(edges, neurons)))

report["checks"] = {
    "A1_jo_alone_mostly_subthreshold": a1["gf_hit"] <= 0.3,
    "A2_jo_effect_on_near_threshold_loom_REPORTED": None,
    "A3_declared_pairs_carry_jo_drive": (a1["gf_depol_mV"] > 0.5) and (a3["gf_depol_mV"] < 0.5 * a1["gf_depol_mV"]),
    "A4_null_silent": a4["gf_hit"] < 0.1 and a4["gf_depol_mV"] < 0.5,
    "A5_cns_quiet": max(a1["pop_rate_hz"], a2["pop_rate_hz"]) < 0.05,
}
k1, n1 = int(round(lo["gf_hit"] * lo["n_trials"])), lo["n_trials"]
k2, n2 = int(round(a2["gf_hit"] * a2["n_trials"])), a2["n_trials"]
d, dlo, dhi = two_prop_ci(k1, n1, k2, n2)
resolved = (dlo > 0) or (dhi < 0)
direction = ("facilitation" if d > 0 else "suppression" if d < 0 else "none") if resolved else "UNRESOLVED"
report["arms"]["A2_prediction"] = dict(loom_gain=SUB_LOOM_GAIN, n_trials_per_arm=n1,
    loom_alone_hit=lo["gf_hit"], loom_alone_ci95=list(wilson(k1, n1)),
    loom_plus_jo_hit=a2["gf_hit"], loom_plus_jo_ci95=list(wilson(k2, n2)),
    difference=d, difference_ci95=[dlo, dhi], resolved=bool(resolved), direction=direction,
    loom_alone_depol_mV=lo["gf_depol_mV"], loom_plus_jo_depol_mV=a2["gf_depol_mV"],
    note=("model measurement at a calibrated near-threshold working point; in vivo direction not "
          "established in cited references. With few trials the difference is not resolvable: "
          "set FLYCNS_A2_TRIALS>=120 for a usable estimate."), seeds=A2_SEEDS, calibration_seed_base=CAL_SEED)
report["arms"]["A2_construction"] = construction_prediction(lo, a2)
_c = report["arms"]["A2_construction"]
print(f"A2 by summation alone: {_c['loom_alone_hit']:.2f} -> predicted {_c['predicted_hit_by_summation']:.2f}, "
      f"observed {_c['observed_hit']:.2f}; residual {_c['residual']:+.2f} "
      f"(95% CI {_c['residual_ci95'][0]:+.2f} to {_c['residual_ci95'][1]:+.2f})")
print(f"A2 (reported, {n1} trials/arm): loom alone {lo['gf_hit']:.2f} -> with JO {a2['gf_hit']:.2f}; "
      f"difference {d:+.2f} (95% CI {dlo:+.2f} to {dhi:+.2f}) -> {direction}")
report["pass"] = all(v for v in report["checks"].values() if v is not None)

# ---- uncertainty (flycns/stats.py): one record per scored check, three-way verdict on the 95% interval.
# A2 is reported, not scored, so it has no record. The A1/A3/A4 arms are separate simulations, so a
# comparison between two of them resamples each arm on its own.
a1_hit, a4_hit = _pt(a1, "hit"), _pt(a4, "hit")
a1_dep, a3_dep, a4_dep = _pt(a1, "depol_mV"), _pt(a3, "depol_mV"), _pt(a4, "depol_mV")
n_ok = lambda v: int((~np.isnan(v)).sum())  # noqa: E731
unc = {
    "A1_jo_alone_mostly_subthreshold": stats.proportion(
        int(a1_hit.sum()), len(a1_hit), high=0.3, note="trials with any GF spike, JO drive alone (electrical); band <= 0.3"),
    "A3_declared_pairs_carry_jo_drive": stats.combine([
        stats.scored(*stats.bootstrap(a1_dep), low=0.5, strict=True, n=n_ok(a1_dep),
                     note="A1 GF peak depolarisation (mV) per trial, with the electrical JON-GF pairs; must exceed 0.5 mV"),
        stats.scored(*stats.bootstrap_diff(a3_dep, 0.5 * a1_dep), high=0, method="bootstrap (two independent arms)",
                     n=n_ok(a3_dep), note="A3 depolarisation (no electrical, no mixed EM edges) minus 0.5 x A1 "
                                          "depolarisation, per trial (n per arm); must be < 0"),
    ], note="A1 depolarisation > 0.5 mV and A3 depolarisation < 0.5 x A1"),
    "A4_null_silent": stats.combine([
        stats.proportion(int(a4_hit.sum()), len(a4_hit), high=0.1,
                         note="trials with any GF spike, rewired null (chemical only); band < 0.1"),
        stats.scored(*stats.bootstrap(a4_dep), high=0.5, n=n_ok(a4_dep),
                     note="GF peak depolarisation (mV) per trial, rewired null; band < 0.5 mV"),
    ], note="GF hit rate < 0.1 and GF depolarisation < 0.5 mV in the rewired null"),
    "A5_cns_quiet": stats.point(
        max(a1["pop_rate_hz"], a2["pop_rate_hz"]), max(a1["pop_rate_hz"], a2["pop_rate_hz"]) < 0.05,
        note="the larger of two whole-run population rates (A1 and A2 arms; spikes per neuron per second over each "
             "whole run): readouts with no trial structure, scored on the point value; band < 0.05 Hz"),
}
report["uncertainty"] = unc
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
prov = ["# Provenance: auditory (JON -> GF)", "", f"JO types: {jo_types} at {JO_HZ} Hz",
        f"A2 reported (not scored): JO drive {report['arms']['A2_prediction']['direction']} of near-threshold loom response",
        "Electrical JON->GF calibrated to a 3 mV compound GF potential at 150 Hz (Pezier & Blagburn 2013)",
        "", "## Checks"] + [f"- {k}: {'REPORTED' if v is None else ('PASS' if v else 'FAIL')}" for k, v in report["checks"].items()]
(OUT / "provenance.md").write_text("\n".join(prov), encoding="utf-8")
print("\nCHECKS"); [print(f"  {'REPORTED' if v is None else ('PASS' if v else 'FAIL')}  {k}") for k, v in report["checks"].items()]
print("\nUNCERTAINTY (95% interval; PASS only if the whole interval lies in the band)")
for k, u in unc.items():
    print(f"  {u['verdict']:<10}  {k}: {_unc_text(u)}")
    for p in u.get("parts", []):
        print(f"      {p['verdict']:<10}  {_unc_text(p)}")
print(f"\nBENCHMARK {'PASS' if report['pass'] else 'FAIL'}  -> {OUT}/report.json")
