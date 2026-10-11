"""
Registered: does sound-loom facilitation at the giant fiber survive the JON -> GF contact as the
connectome annotates it? (audit 2026-10-11, gap 1)

The declared model represents the JON -> GF mixed synapse as electrical coupling calibrated to a 3 mV
compound potential that no source reports (docs/CALIBRATION.md, "Literature check"). With that value,
the A2 facilitation (a2_registered) is close to guaranteed by construction. Here the contact is the
679 chemical synapses EM annotates, signed by their transmitter, with no hand-set coupling
(FLYCNS_JON=em), and, as a control, the same synapses with their sign inverted (FLYCNS_JON=em_flip).
Everything else is the registered A2 protocol (benchmarks/auditory.py, A2-only mode): the working point
calibrated per run on its own seeds, 120 trials per arm, independent seeds for the two arms, the
Newcombe interval on the difference in giant fiber response probability.

Checks (registered in results/a2_contact_<variant>/registration.json before the run):
  em       C1_em_facilitation      the 95% interval on P(GF | loom + sound) - P(GF | loom) lies above 0
  em_flip  C2_flip_no_facilitation the 95% interval lies at or below 0 (sign-inverted input cannot
                                   facilitate); above 0 fails; spanning 0 is unresolved

Run:  python benchmarks/a2_contact.py em|em_flip [trials_per_arm=120] [data_dir]
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import registry, stats  # noqa: E402
from flycns.bench import provenance  # noqa: E402
from flycns.integrity import require_clean, require_data  # noqa: E402

VARIANTS = ("em", "em_flip")
VARIANT = sys.argv[1] if len(sys.argv) > 1 else ""
if VARIANT not in VARIANTS:
    raise SystemExit(f"usage: a2_contact.py {'|'.join(VARIANTS)} [trials_per_arm] [data_dir]")
TRIALS = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else 120
DATA = sys.argv[3] if len(sys.argv) > 3 else "data"
LABEL = f"a2_contact_{VARIANT}"
OUT = Path("results") / LABEL
CHECK = {"em": "C1_em_facilitation", "em_flip": "C2_flip_no_facilitation"}[VARIANT]
BAND = {"em": [0.0, None], "em_flip": [None, 0.0]}[VARIANT]
CRITERIA = dict(
    question="sound-loom facilitation at the giant fiber with the JON -> GF contact as EM annotates it",
    contact=dict(em="679 EM chemical synapses, transmitter-signed, no electrical coupling (FLYCNS_JON=em)",
                 em_flip="the same synapses with their sign inverted (FLYCNS_JON=em_flip)")[VARIANT],
    protocol=("benchmarks/auditory.py in A2-only mode: working point calibrated per run on seeds BASE+1000.., "
              "loom alone on seed BASE, loom + sound on seed BASE+1, 150 Hz on the auditory JO types"),
    trials_per_arm=TRIALS,
    statistic="P(GF | loom + sound) - P(GF | loom), Newcombe 1998 method 10 95% interval",
    checks={CHECK: dict(band=BAND, band_lower_exclusive=(VARIANT == "em"),
                        rule=("PASS if the interval lies above 0; FAIL if at or below 0; UNRESOLVED if it spans 0"
                              if VARIANT == "em" else
                              "PASS if the interval lies at or below 0; FAIL if above 0; UNRESOLVED if it spans 0"))},
)
REG = registry.register(LABEL, CRITERIA, scripts=[__file__, Path(__file__).with_name("auditory.py")])
require_clean(LABEL)
require_data(DATA, LABEL)
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
child_out = OUT / "auditory"
env = {k: v for k, v in os.environ.items() if k not in ("FLYCNS_AUDITORY_OUT", "FLYCNS_A2_GAIN", "FLYCNS_A2_ONLY")}
env.update(FLYCNS_JON=VARIANT, FLYCNS_A2_ONLY="1", FLYCNS_A2_TRIALS=str(TRIALS), FLYCNS_AUDITORY_OUT=str(child_out))
proc = subprocess.run([sys.executable, "-u", "benchmarks/auditory.py", "40", DATA], env=env,
                      capture_output=True, text=True, encoding="utf-8", errors="replace")
(OUT / "auditory_run.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
if proc.returncode != 0:
    raise SystemExit(f"auditory.py failed (exit {proc.returncode}); see {OUT / 'auditory_run.log'}")
child = json.loads((child_out / "report.json").read_text(encoding="utf-8"))
a2 = child["arms"]["A2_prediction"]
d, (lo, hi) = a2["difference"], a2["difference_ci95"]
if VARIANT == "em":
    rec = stats.scored(d, lo, hi, low=0.0, strict=True, method="newcombe", n=a2["n_trials_per_arm"])
else:
    rec = stats.scored(d, lo, hi, high=0.0, method="newcombe", n=a2["n_trials_per_arm"])
uncertainty = {CHECK: rec}
registry.verify_bands(REG, uncertainty)
report = dict(benchmark=LABEL, variant=VARIANT, criteria=CRITERIA, a2=a2,
              construction=child["arms"].get("A2_construction"), calibration=child["arms"].get("A2_calibration"),
              checks={CHECK: rec["verdict"] == "PASS"}, uncertainty=uncertainty,
              registration=registry.stamp(REG), wall_s=round(time.time() - t0, 1), provenance=provenance(DATA))
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print(f"{VARIANT}: loom alone {a2['loom_alone_hit']:.3f} -> with sound {a2['loom_plus_jo_hit']:.3f}; "
      f"difference {d:+.3f} (95% CI {lo:+.3f} to {hi:+.3f})")
print(f"  {rec['verdict']}  {CHECK}")
