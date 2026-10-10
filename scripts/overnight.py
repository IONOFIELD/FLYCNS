"""
Robustness battery: seed replicates, transmitter sign inversion (random and targeted), connection weight
scale, connection-size threshold, and a stricter (superclass-preserving) null. Each run is the
three-benchmark core suite (about 25 min); twelve runs in all. Keeps Windows awake while it runs.

Results go to results\\overnight\\<tag>\\ : SUITE.md plus one <benchmark>_report.json per benchmark, and
each tag is committed and pushed as it finishes. The CANONICAL results (results\\<benchmark>\\,
results\\SUITE.md) are snapshotted first and restored at the end, even after an error or Ctrl+C, so a
perturbed run can never be left standing as the headline result.

    .venv\\Scripts\\python.exe scripts\\overnight.py         (menu option 7)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns.windows import console, keep_awake  # noqa: E402

console()
keep_awake()
os.chdir(ROOT)
PY = sys.executable
BENCHES = ["gf_escape", "auditory", "feeding"]
RES = Path("results")

# tag, seed, random sign-flip fraction, weight scale, extra settings
RUNS = [
    ("seed1", 1, 0, 0.3, {}),
    ("seed2", 2, 0, 0.3, {}),
    ("signflip05_a", 0, 0.05, 0.3, {}),
    ("signflip05_b", 1, 0.05, 0.3, {}),
    ("signflip10", 0, 0.10, 0.3, {}),
    ("wscale025", 0, 0, 0.25, {}),
    ("wscale035", 0, 0, 0.35, {}),
    ("wscale040", 0, 0, 0.40, {}),
    # targeted perturbation: only the neurons the transmitter classifier is unsure about
    ("signflip_targeted", 0, 0, 0.3, {"FLYCNS_SIGNFLIP_TARGETED": "1"}),
    # connection-size threshold (default 5 synapses): looser and stricter inclusion of connections
    ("minweight3", 0, 0, 0.3, {"FLYCNS_MIN_WEIGHT": "3"}),
    ("minweight10", 0, 0, 0.3, {"FLYCNS_MIN_WEIGHT": "10"}),
    # stricter null: shuffle targets only within the same superclass (flycns/graph.py rewire_null)
    ("null_superclass", 0, 0, 0.3, {"FLYCNS_NULL": "superclass"}),
]


def checks_line(suite):
    for line in suite.read_text(encoding="utf-8").splitlines():
        if "checks pass" in line:
            return line.strip("* ")
    return "?"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    for args in (["fit/audit_stimuli.py", "data"], ["-m", "flycns.integrity", "verify", "data"]):
        if subprocess.run([PY, *args]).returncode != 0:
            sys.exit("pre-flight check failed (see above); battery not started")
    snap = Path(tempfile.mkdtemp(prefix="flycns_canonical_"))
    for b in BENCHES:
        if (RES / b).exists():
            shutil.copytree(RES / b, snap / b)
    if (RES / "SUITE.md").exists():
        shutil.copy2(RES / "SUITE.md", snap / "SUITE.md")
    try:
        for tag, seed, flip, wscale, extra in RUNS:
            env = {k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_")}
            env.update(FLYCNS_SEED=str(seed), FLYCNS_SIGNFLIP=str(flip), FLYCNS_WSCALE=str(wscale),
                       FLYCNS_RUN_TAG=tag, **extra)
            print(f"=== {time.strftime('%H:%M')} start {tag} (seed {seed}, signflip {flip}, wscale {wscale}"
                  + "".join(f", {k[7:].lower()} {v}" for k, v in extra.items()) + ")", flush=True)
            out = RES / "overnight" / tag
            out.mkdir(parents=True, exist_ok=True)
            for b in BENCHES:
                with open(RES / "overnight" / f"{tag}_{b}.log", "w", encoding="utf-8") as log:
                    code = subprocess.run([PY, f"benchmarks/{b}.py", "40", "data"], env=env,
                                          stdout=log, stderr=subprocess.STDOUT).returncode
                if code != 0:
                    print(f"  {b} errored (see results\\overnight\\{tag}_{b}.log)")
                if (RES / b / "report.json").exists():
                    shutil.copy2(RES / b / "report.json", out / f"{b}_report.json")
            subprocess.run([PY, "benchmarks/summarize.py"], env=env, capture_output=True)
            shutil.copy2(RES / "SUITE.md", out / "SUITE.md")
            line = checks_line(out / "SUITE.md")
            print(f"  {line}")
            git("add", "-A", "results/overnight")
            if git("commit", "-qm", f"overnight: {tag} {line}").returncode == 0:
                git("push", "-q")
            print(f"=== {time.strftime('%H:%M')} done  {tag}", flush=True)
    finally:
        for b in BENCHES:
            if (snap / b).exists():
                shutil.rmtree(RES / b, ignore_errors=True)
                shutil.copytree(snap / b, RES / b)
        if (snap / "SUITE.md").exists():
            shutil.copy2(snap / "SUITE.md", RES / "SUITE.md")
        shutil.rmtree(snap, ignore_errors=True)
        print("canonical results restored")
    print("\nSUMMARY")
    for d in sorted((RES / "overnight").iterdir()):
        if (d / "SUITE.md").exists():
            print(f"{d.name:<20} {checks_line(d / 'SUITE.md')}")


if __name__ == "__main__":
    main()
