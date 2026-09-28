"""
Is sound's facilitation of the giant fiber robust across near-threshold working points?

The registered A2 test (benchmarks/a2_registered.py) found strong facilitation at the one working
point its calibration chose (loom gain 0.6): GF response 0.042 alone, 0.450 with sound, difference
+0.41 (95% CI +0.31 to +0.50). The calibrated point moves with the loom input (it was 0.8 before the
input changed to measured stationary amplitudes), so the result should not depend on landing on one
gain. This sweep measures A2 at a fixed grid of gains using exactly the benchmark's own protocol
(auditory.py in A2-only mode, working point fixed by FLYCNS_A2_GAIN), reporting into its own folder.

CRITERION (registered before the run):
  RA2  "near-threshold" is defined in advance as loom-alone GF response probability <= 0.3 (the
       calibration rule's own threshold). At EVERY grid gain that qualifies, the 95% CI on
       P(GF | loom + sound) - P(GF | loom) lies entirely above zero, AND at least 3 grid gains qualify
       (otherwise the sweep has not tested robustness at all).
Gains above threshold (loom alone > 0.3) are reported, not scored: there, facilitation has little room.
Interval: Newcombe 1998 method 10, recomputed from counts.

Run:  python benchmarks/a2_robustness.py [trials_per_arm] [data_dir]      (default 100; ~1.5-2 h)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 100
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/a2_robustness")
OUT.mkdir(parents=True, exist_ok=True)
GAINS = [0.4, 0.5, 0.6, 0.7, 0.8]
NEAR = 0.3

CRITERIA = dict(
    source="Tootoonian et al. 2012, J Neurosci 32:787-798, Fig. 2D; builds on the registered A2 result (c097e41)",
    gains=GAINS, trials_per_arm=TRIALS, near_threshold="loom-alone GF probability <= 0.3",
    RA2="at every qualifying gain the 95% CI on the difference lies above zero, and >= 3 gains qualify",
    ci_method="Newcombe 1998 method 10, recomputed from counts")
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/a2_robustness.py", "benchmarks/auditory.py"],
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


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


rows, t0 = [], time.time()
for g in GAINS:
    sub = OUT / f"gain_{g}"
    env = dict(os.environ, FLYCNS_A2_ONLY="1", FLYCNS_A2_GAIN=str(g), FLYCNS_A2_TRIALS=str(TRIALS),
               FLYCNS_AUDITORY_OUT=str(sub))
    p = subprocess.run([sys.executable, "-u", "benchmarks/auditory.py", str(TRIALS), DATA], env=env,
                       capture_output=True, text=True)
    (OUT / f"gain_{g}.log").write_text(p.stdout + p.stderr)
    if p.returncode != 0:
        raise SystemExit(f"auditory.py failed at gain {g}; see {OUT / f'gain_{g}.log'}")
    a = json.loads((sub / "report.json").read_text())["arms"]["A2_prediction"]
    n = int(a["n_trials_per_arm"]); k1 = int(round(a["loom_alone_hit"] * n)); k2 = int(round(a["loom_plus_jo_hit"] * n))
    p1, p2 = k1 / n, k2 / n
    l1, u1 = wilson(k1, n); l2, u2 = wilson(k2, n)
    d = p2 - p1
    lo = d - np.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2); hi = d + np.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    row = dict(gain=g, n=n, k_alone=k1, k_sound=k2, p_alone=p1, p_sound=p2, difference=d, ci=[lo, hi],
               near_threshold=bool(p1 <= NEAR), facilitation=bool(lo > 0),
               depol_alone_mV=a.get("loom_alone_depol_mV"))
    rows.append(row)
    print(f"gain {g:<4} | alone {k1:>3}/{n} = {p1:.3f} | with sound {k2:>3}/{n} = {p2:.3f} | difference {d:+.3f} "
          f"(95% CI {lo:+.3f} to {hi:+.3f}) | {'near-threshold' if row['near_threshold'] else 'above threshold'}"
          f"{'  FACILITATION' if row['facilitation'] else ''} | {round(time.time() - t0)}s", flush=True)
    (OUT / "report.json").write_text(json.dumps(dict(criteria=CRITERIA, rows=rows), indent=2, default=float))

qual = [r for r in rows if r["near_threshold"]]
ok = len(qual) >= 3 and all(r["facilitation"] for r in qual)
report = dict(benchmark="a2_robustness", criteria=CRITERIA, rows=rows, n_qualifying=len(qual),
              checks={"RA2_facilitation_at_every_near_threshold_gain": ok}, wall_s=round(time.time() - t0))
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print(f"\n{len(qual)} of {len(GAINS)} gains near threshold; facilitation at "
      f"{sum(r['facilitation'] for r in qual)} of them")
print(f"CHECK (criterion registered before the run)\n  {'PASS' if ok else 'FAIL'}  RA2_facilitation_at_every_near_threshold_gain")
print(f"wrote {OUT / 'report.json'}")
