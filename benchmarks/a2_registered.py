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
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/a2_registered.py", "benchmarks/auditory.py"],
                                capture_output=True, text=True, timeout=5).stdout.strip())
except Exception:
    commit, dirty = "", True
if crit_f.exists():
    if json.loads(crit_f.read_text()).get("criteria") != CRITERIA:
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test.")
else:
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=commit, script_uncommitted=dirty), indent=2))
print(f"criteria registered at commit {commit or '?'}{' (SCRIPTS UNCOMMITTED: commit before running)' if dirty else ''}")

t0 = time.time()
env = dict(os.environ, FLYCNS_A2_TRIALS=str(A2_TRIALS))
proc = subprocess.run([sys.executable, "-u", "benchmarks/auditory.py", "40", DATA], env=env,
                      capture_output=True, text=True)
(OUT / "auditory_run.log").write_text(proc.stdout + proc.stderr)
if proc.returncode != 0:
    raise SystemExit(f"auditory.py failed (exit {proc.returncode}); see {OUT / 'auditory_run.log'}")
rep = json.loads(Path("results/auditory/report.json").read_text())
a2 = rep["arms"]["A2_prediction"]
n = int(a2["n_trials_per_arm"])
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
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print(f"working point: loom gain {a2.get('loom_gain')}, {n} trials per arm")
print(f"loom alone      {k1}/{n} = {p1:.3f}  (95% CI {l1:.3f} to {u1:.3f})")
print(f"loom + sound    {k2}/{n} = {p2:.3f}  (95% CI {l2:.3f} to {u2:.3f})")
print(f"difference      {d:+.3f}  (95% CI {lo:+.3f} to {hi:+.3f})")
print(f"\nCHECK (criterion registered before the run)\n  {'PASS' if outcome == 'above' else 'FAIL'}  A2R_facilitation"
      f"  -> {CRITERIA['outcomes'][outcome]}")
print(f"wrote {OUT / 'report.json'}  ({report['wall_s']}s)")
