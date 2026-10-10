"""
Stricter null, registered: do the wiring-specificity controls survive a shuffle that keeps cell class?

The standard null (flycns/graph.py rewire_null, mode "global") permutes every connection's target
across the whole CNS. It keeps degrees but destroys which class of cell each neuron talks to, so
almost any circuit goes silent on it, and "the null is silent" says little. The "superclass" mode
permutes targets only among cells of the same superclass: every neuron keeps how many synapses it
sends to sensory, central, descending, motor ... cells, and only the identity of the target within
the class is shuffled. If a pathway still fails on that null, the result depends on the specific
wiring, not on class-level statistics.

CRITERIA (registered to results/null_strict/criteria.json before anything runs):
  S1  benchmarks/gf_escape.py, 40 trials, FLYCNS_NULL=superclass: rewired-null GF hit rate < 0.1
      (the same threshold as the escape benchmark's null_silent check)
  S2  benchmarks/pc1_song.py at its registered trial count, FLYCNS_NULL=superclass: pMP2 under
      pC1_14a at 100 Hz on the null < 0.1 spikes/cell/pulse (the same threshold as P4)
Reported, not scored: whole-CNS rate on each null beside the real network, because a null that is
merely dead proves less than one that stays active and still fails to drive the readout.

The canonical results of both benchmarks are snapshotted before the runs and restored after, so
this test never replaces them. Its own report goes to results/null_strict/.

Run:  python benchmarks/null_strict.py [data_dir]          (about the time of one escape run plus one pc1 run)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.bench import provenance  # noqa: E402
from flycns.integrity import require_clean, require_data  # noqa: E402

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = Path("results/null_strict")
OUT.mkdir(parents=True, exist_ok=True)
ESCAPE_TRIALS = 40
pc1_crit = Path("results/pc1_song/criteria.json")
PC1_TRIALS = int(json.loads(pc1_crit.read_text(encoding="utf-8"))["criteria"]["n_trials"]) if pc1_crit.exists() else 10

CRITERIA = dict(
    null_mode="superclass (flycns/graph.py rewire_null): targets permuted only within the post cell's superclass",
    S1="gf_escape, 40 trials: rewired-null GF hit rate < 0.1 (threshold of null_silent)",
    S2="pc1_song at its registered trial count: pMP2 under pC1_14a at 100 Hz on the null < 0.1 spikes/cell/pulse (threshold of P4)",
    reported="whole-CNS rate on each null beside the real network",
)

require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem, ["neurons.parquet", "edges.parquet"])
crit_f = OUT / "criteria.json"
if crit_f.exists():
    if json.loads(crit_f.read_text(encoding="utf-8")).get("criteria") != CRITERIA:
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test.")
else:
    st = provenance()
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=st["git_commit"], script_uncommitted=st["git_dirty"]), indent=2), encoding="utf-8")
print(f"criteria registered: {json.loads(crit_f.read_text(encoding="utf-8"))['git_commit'] or '?'}")

env = dict(os.environ, FLYCNS_NULL="superclass", FLYCNS_RUN_TAG="null_strict")
snap = Path(tempfile.mkdtemp(prefix="flycns_null_strict_"))
canon = [Path("results/gf_escape"), Path("results/pc1_song")]
for d in canon:
    if d.exists():
        shutil.copytree(d, snap / d.name)
try:
    t0 = time.time()
    for argv in (["benchmarks/gf_escape.py", str(ESCAPE_TRIALS), DATA], ["benchmarks/pc1_song.py", str(PC1_TRIALS), DATA]):
        print(f"running {' '.join(argv)} with FLYCNS_NULL=superclass ...", flush=True)
        r = subprocess.run([sys.executable, "-u", *argv], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / f"{Path(argv[0]).stem}.log").write_text(r.stdout + r.stderr, encoding="utf-8")
        if r.returncode != 0:
            raise SystemExit(f"{argv[0]} failed (exit {r.returncode}); see {OUT}/{Path(argv[0]).stem}.log")
    esc = json.loads(Path("results/gf_escape/report.json").read_text(encoding="utf-8"))
    pc1 = json.loads(Path("results/pc1_song/report.json").read_text(encoding="utf-8"))
finally:
    for d in canon:
        if (snap / d.name).exists():
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(snap / d.name, d)
    shutil.rmtree(snap, ignore_errors=True)
    print("canonical gf_escape and pc1_song results restored")

null_e, real_e = esc["arms"]["rewired_null"], esc["arms"]["real_electrical"]
null_p = pc1["null_pc1_14a_100Hz"]
real_p = pc1["dynamic"]["pC1_14a"]["100Hz"]
checks = {"S1_escape_null_silent_superclass": bool(null_e["gf_hit"] < 0.1),
          "S2_pc1_null_silent_superclass": bool(null_p["pMP2"] < 0.1)}
report = dict(benchmark="null_strict", criteria=CRITERIA, checks=checks,
              escape=dict(null_gf_hit=null_e["gf_hit"], null_pop_rate_hz=null_e["pop_rate_hz"],
                          real_gf_hit=real_e["gf_hit"], real_pop_rate_hz=real_e["pop_rate_hz"]),
              pc1=dict(null=null_p, real=real_p, n_trials=PC1_TRIALS),
              wall_s=round(time.time() - t0, 1), provenance=provenance())
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print(f"\nescape: null GF hit {null_e['gf_hit']:.2f} (real {real_e['gf_hit']:.2f}); "
      f"null CNS {null_e['pop_rate_hz']:.4f} Hz vs real {real_e['pop_rate_hz']:.4f} Hz")
print(f"pc1:    null pMP2 {null_p['pMP2']:.2f} (real {real_p['pMP2']:.2f}); "
      f"null CNS {null_p.get('cns_hz', float('nan')):.4f} Hz vs real {real_p.get('cns_hz', float('nan')):.4f} Hz")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
