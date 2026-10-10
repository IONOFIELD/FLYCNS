"""
Core suite, repeatable: data check, stimulus audit, the three core benchmarks, suite summary, 3D view.

    .venv\\Scripts\\python.exe scripts\\run_all.py [n_trials] [data_dir]        (menu option 4; about 40 min)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns.windows import console  # noqa: E402

console()
N = sys.argv[1] if len(sys.argv) > 1 else "40"
D = sys.argv[2] if len(sys.argv) > 2 else "data"
PY = sys.executable


def step(args, fatal=True, note=""):
    code = subprocess.run([PY, *args], cwd=ROOT).returncode
    if code != 0:
        if fatal:
            sys.exit(f"stopped: {' '.join(args)} failed{note}")
        print(f"{args[0]} did not complete (see above)")
    return code


# refuse to start on data that differ from the committed fingerprint (flycns/integrity.py)
step(["-m", "flycns.integrity", "verify", D], note=f": the data differ from {D}/MANIFEST.json")
# refuse to start if any benchmark's stimulus set resolves to no neurons (fit/audit_stimuli.py)
step(["fit/audit_stimuli.py", D], note=": fix the stimulus lists above before running")
step(["benchmarks/gf_escape.py", N, D])
step(["benchmarks/auditory.py", N, D])
step(["benchmarks/feeding.py", "6", D], fatal=False)
step(["benchmarks/summarize.py"])
step(["viz/cascade_3d.py", "", D], fatal=False)
print("\nsuite summary: results\\SUITE.md    3D: results\\gf_escape\\cascade_3d.html (menu 16 opens it)")
