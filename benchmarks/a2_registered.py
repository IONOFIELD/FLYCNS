"""
Registered test of multisensory facilitation at the giant fiber (auditory A2, 120 trials per arm).

Tootoonian et al. 2012 (J Neurosci 32:787-798, Fig. 2D) played sound together with a somatic
current injection that was subthreshold on its own and obtained a full GF spike: facilitation.
benchmarks/auditory.py measures the model's equivalent at a near-threshold working point, calibrated
per run (the largest loom gain with GF hit rate <= 0.3 and mean depolarisation >= 2 mV), comparing GF
response probability for loom alone against loom plus Johnston's organ drive. At 20-40 trials per arm
that difference has never been resolved. This wrapper registers a criterion, runs the benchmark with
120 trials per arm, and scores it, recomputing the interval from the counts rather than trusting one
function.

NOTE: before 2026-09-25 the interval function in auditory.py was wrong (crossed Wilson limits and an
extra factor of z), so every earlier A2 interval was roughly twice too wide. It is now Newcombe
(1998) method 10, verified against the paper's worked example. This test uses the corrected method.

CRITERION (registered before the run):
  A2R  the 95% CI on (P[GF | loom + sound] - P[GF | loom]) at the calibrated working point lies
       entirely ABOVE zero: facilitation, as Tootoonian et al. 2012 Fig. 2D.
Outcomes fixed in advance:
  CI above zero   PASS: facilitation reproduced
  CI below zero   FAIL: suppression, contradicting Tootoonian et al. 2012
  CI spans zero   FAIL: unresolved even at 120 trials per arm
Added with the version 2 registration (results/a2_registered/registration.json, which supersedes criteria.json):
  A2R2 facilitation beyond summation: the 95% bootstrap interval on the observed P(GF | loom + sound) minus
       what adding the declared compound sound potential to each loom-alone trial predicts lies above zero
       (auditory.py, A2_construction). Above zero PASS, at or below zero FAIL, spanning zero UNRESOLVED.

Run:  python benchmarks/a2_registered.py [trials_per_arm] [data_dir]      (default 120; ~40+ min)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

A2_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 120
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/a2_registered")
OUT.mkdir(parents=True, exist_ok=True)

CRITERIA = dict(
    source="Tootoonian, Coen, Kawadler & Murthy 2012, J Neurosci 32:787-798, Fig. 2D (sound + subthreshold input -> GF spike)",
    A2R="95% CI on P(GF|loom+sound) - P(GF|loom) at the calibrated working point lies entirely above zero",
    ci_method="Newcombe 1998 method 10 (hybrid score), recomputed from counts",
    trials_per_arm=A2_TRIALS,
    outcomes=dict(above="PASS facilitation", below="FAIL suppression (contradicts Tootoonian 2012)",
                  spans="FAIL unresolved at this trial count"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Version 2 registration (flycns/registry.py): the criteria with every band the scoring uses, and the frozen
# model, recorded before any data are loaded. It supersedes the version 1 criteria.json, which stays as is.
from flycns import registry  # noqa: E402
CRITERIA_V2 = dict(
    version=2,
    hypothesis=("sound facilitates the giant fiber's response to a near-threshold loom (Tootoonian et al. 2012, "
                "J Neurosci 32:787-798, Fig. 2D), and does so beyond what adding the declared compound sound "
                "potential to the loom alone predicts"),
    protocol=dict(
        trials_per_arm=A2_TRIALS,
        child=("benchmarks/auditory.py 40 <data_dir> as a full run with FLYCNS_A2_TRIALS = trials_per_arm "
               "(FLYCNS_AUDITORY_OUT, FLYCNS_A2_GAIN and FLYCNS_A2_ONLY removed)"),
        working_point=("calibrated per run over loom gains [0.4, 0.6, 0.8, 1.0, 1.3] on seeds BASE + 1000 + gain index: "
                       "the largest gain with loom-alone GF hit <= 0.3 and mean depolarisation >= 2 mV"),
        arms=("loom alone on seed BASE, loom + sound on seed BASE + 1 (BASE = LIFParams().seed); sound = the auditory "
              "JO types at 150 Hz during each 60 ms loom burst"),
        statistics=("A2R: Newcombe 1998 method 10 interval on the difference, recomputed from counts. A2R2: percentile "
                    "bootstrap of observed minus summation-predicted response, each arm resampled on its own"),
    ),
    checks={
        "A2R_facilitation": dict(
            band=[0.0, None], band_lower_exclusive=True,
            rule=("PASS if the 95% interval on P(GF | loom + sound) - P(GF | loom) lies above 0; FAIL if below 0; "
                  "FAIL also if it spans 0 (fixed in advance: unresolved at this trial count)")),
        "A2R2_beyond_summation": dict(
            band=[0.0, None], band_lower_exclusive=True, conditional=True,
            condition=("scored when the auditory report carries A2_construction (the registered auditory.py always "
                       "writes it); otherwise UNRESOLVED"),
            rule=("facilitation beyond summation: PASS if the 95% interval on the observed P(GF | loom + sound) minus "
                  "the probability predicted by adding the declared compound potential to each loom-alone trial's "
                  "peak depolarisation lies above 0; FAIL if at or below 0; UNRESOLVED if it spans 0")),
    },
)
_v1 = OUT / "criteria.json"
REG = registry.register(
    "a2_registered", CRITERIA_V2, scripts=[__file__, Path(__file__).with_name("auditory.py")],
    supersedes=dict(file="criteria.json",
                    git_commit=json.loads(_v1.read_text(encoding="utf-8")).get("git_commit") if _v1.exists() else None))
# Registered test: refuse uncommitted code and data that differ from data/MANIFEST.json, so the
# registered result can be traced to an exact commit and an exact dataset (flycns/integrity.py).
from flycns.integrity import require_clean, require_data, criteria_differ  # noqa: E402
require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem)   # every table pinned in the manifest, rehashed
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/a2_registered.py", "benchmarks/auditory.py"],
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
print(f"criteria registered at commit {reg}; this run at {commit or '?'}{' (SCRIPTS UNCOMMITTED: commit before running)' if dirty else ''}")

t0 = time.time()
started = time.strftime("%Y-%m-%dT%H:%M:%S")
# the child must run the registered protocol: no inherited output folder, fixed gain or A2-only mode
env = {k: v for k, v in os.environ.items() if k not in ("FLYCNS_AUDITORY_OUT", "FLYCNS_A2_GAIN", "FLYCNS_A2_ONLY")}
env["FLYCNS_A2_TRIALS"] = str(A2_TRIALS)
proc = subprocess.run([sys.executable, "-u", "benchmarks/auditory.py", "40", DATA], env=env,
                      capture_output=True, text=True, encoding="utf-8", errors="replace")
(OUT / "auditory_run.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
if proc.returncode != 0:
    raise SystemExit(f"auditory.py failed (exit {proc.returncode}); see {OUT / 'auditory_run.log'}")
rep = json.loads(Path("results/auditory/report.json").read_text(encoding="utf-8"))
a2 = rep["arms"]["A2_prediction"]
n = int(a2["n_trials_per_arm"])
# score only the report this run just wrote, at the registered trial count and calibration rule
fresh = rep.get("provenance", {}).get("written_at", "") >= started
rule_ok = rep["arms"].get("A2_calibration", {}).get("rule", "").startswith("largest gain")
if not (fresh and n == A2_TRIALS and rule_ok):
    raise SystemExit(f"refusing to score results/auditory/report.json: fresh={fresh}, trials {n} (registered "
                     f"{A2_TRIALS}), calibration rule {'ok' if rule_ok else 'not the registered one'}")
k1 = int(round(a2["loom_alone_hit"] * n)); k2 = int(round(a2["loom_plus_jo_hit"] * n))


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


p1, p2 = k1 / n, k2 / n
l1, u1 = wilson(k1, n); l2, u2 = wilson(k2, n)
d = p2 - p1
lo = d - np.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
hi = d + np.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
outcome = "above" if lo > 0 else "below" if hi < 0 else "spans"
report = dict(benchmark="a2_registered", criteria=CRITERIA, working_point_loom_gain=a2.get("loom_gain"),
              n_trials_per_arm=n, loom_alone=dict(k=k1, p=p1, ci=[l1, u1]),
              loom_plus_sound=dict(k=k2, p=p2, ci=[l2, u2]),
              difference=d, difference_ci95=[lo, hi], outcome=CRITERIA["outcomes"][outcome],
              auditory_report_ci=a2.get("difference_ci95"),
              checks={"A2R_facilitation": outcome == "above"}, wall_s=round(time.time() - t0))
# Uncertainty record (flycns/stats.py), expressing the registered rule with the registered interval. The
# three-way verdict would call a CI that spans zero UNRESOLVED; the registered outcomes fix that case as
# FAIL ("unresolved at this trial count") in advance, so the record keeps the registered verdict.
from flycns import stats  # noqa: E402
unc = stats.scored(d, lo, hi, low=0, strict=True, method="newcombe (as registered)", n=n,
                   note="P(GF|loom+sound) - P(GF|loom) at the calibrated working point; Newcombe 1998 method 10 "
                        "recomputed from counts (n per arm). Registered outcomes: CI above zero PASS, below zero "
                        "FAIL, spans zero FAIL (unresolved at this trial count)")
if outcome == "spans":
    unc["verdict"] = "FAIL"
unc["registered_outcome"] = CRITERIA["outcomes"][outcome]
report["uncertainty"] = {"A2R_facilitation": unc}
# A2R2 (registered version 2): facilitation beyond what summation of the declared compound potential predicts
cons = rep["arms"].get("A2_construction")
if cons and cons.get("residual_ci95"):
    rlo, rhi = cons["residual_ci95"]
    unc2 = stats.scored(cons["residual"], rlo, rhi, low=0.0, strict=True, method="bootstrap",
                        note=(f"observed P(GF|loom+sound) {cons['observed_hit']:.3f} minus the {cons['predicted_hit_by_summation']:.3f} "
                              f"predicted by adding the declared compound potential ({cons['compound_mV']} mV, JON "
                              f"{cons['jon_mode']}) to each loom-alone trial's peak depolarisation (rest to threshold "
                              f"{cons['gap_mV']} mV); percentile bootstrap over trials, the two arms resampled on their "
                              f"own (auditory.py A2_construction)"))
else:
    unc2 = stats.unresolved("the auditory report carries no A2_construction, so facilitation beyond summation "
                            "cannot be scored")
report["uncertainty"]["A2R2_beyond_summation"] = unc2
report["checks"]["A2R2_beyond_summation"] = (unc2["verdict"] == "PASS")
# a check that could not be scored as designed (stats.unresolved) has no band to compare; only a check
# registered as conditional may be missing from the comparison
registry.verify_bands(REG, {k: u for k, u in report["uncertainty"].items() if u.get("method") != "not scorable as designed"})
report["registration"] = registry.stamp(REG)
from flycns.bench import provenance  # noqa: E402
report["provenance"] = provenance(DATA)
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print(f"working point: loom gain {a2.get('loom_gain')}, {n} trials per arm")
print(f"loom alone      {k1}/{n} = {p1:.3f}  (95% CI {l1:.3f} to {u1:.3f})")
print(f"loom + sound    {k2}/{n} = {p2:.3f}  (95% CI {l2:.3f} to {u2:.3f})")
print(f"difference      {d:+.3f}  (95% CI {lo:+.3f} to {hi:+.3f})")
print(f"\nCHECK (criterion registered before the run)\n  {'PASS' if outcome == 'above' else 'FAIL'}  A2R_facilitation"
      f"  -> {CRITERIA['outcomes'][outcome]}")
print(f"UNCERTAINTY (95% interval, registered rule)\n  {unc['verdict']:<10}  A2R_facilitation: difference {d:+.4g} "
      f"[{lo:+.4g}, {hi:+.4g}] band (0, -) ({unc['method']})")
_f = lambda x: "-" if x is None else f"{x:+.4g}"  # noqa: E731
_r = unc2["ci95"] or [None, None]
print(f"  {unc2['verdict']:<10}  A2R2_beyond_summation: residual {_f(unc2['estimate'])} [{_f(_r[0])}, {_f(_r[1])}] "
      f"band (0, -) ({unc2['method']})")
print(f"wrote {OUT / 'report.json'}  ({report['wall_s']}s)")
