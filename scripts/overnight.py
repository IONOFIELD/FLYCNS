"""
Robustness battery: seed replicates, transmitter sign inversion (random and targeted), connection weight
scale, connection-size threshold, and a stricter (superclass-preserving) null. Each run is the
three-benchmark core suite (about 25 min); twelve runs in all. Keeps Windows awake while it runs.

Results go to results\\overnight\\<tag>\\ : SUITE.md plus one <benchmark>_report.json per benchmark, and
each tag is committed and pushed as it finishes. The CANONICAL results (results\\<benchmark>\\,
results\\SUITE.md) are snapshotted first and restored at the end, even after an error or Ctrl+C, so a
perturbed run can never be left standing as the headline result.

    .venv\\Scripts\\python.exe scripts\\overnight.py         (menu option 7)
    .venv\\Scripts\\python.exe scripts\\overnight.py seed1   (only the named runs; used by the cloud rerun)
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns.integrity import DEFAULTS, preserved  # noqa: E402
from flycns.windows import console, keep_awake  # noqa: E402

console()
keep_awake()
os.chdir(ROOT)
PY = sys.executable
BENCHES = {"gf_escape": "40", "auditory": "40", "feeding": "6"}   # trials, as in the canonical suite (run_all.py)
RES = Path("results")

# tag, seed, random sign-flip fraction, weight scale, extra settings. W0 is the declared weight scale; the
# weight-scale arms sit around it: 0.30 (the value declared until 11 October 2026, so a result that holds at
# W0 but not there shows it depends on sitting next to the runaway transition), 0.35, and 0.45 (between W0
# and 0.5, where the blind selection found the network runs away).
W0 = float(DEFAULTS["FLYCNS_WSCALE"])
RUNS = [
    ("seed1", 1, 0, W0, {}),
    ("seed2", 2, 0, W0, {}),
    ("signflip05_a", 0, 0.05, W0, {}),
    ("signflip05_b", 1, 0.05, W0, {}),
    ("signflip10", 0, 0.10, W0, {}),
    ("wscale030", 0, 0, 0.30, {}),
    ("wscale035", 0, 0, 0.35, {}),
    ("wscale045", 0, 0, 0.45, {}),
    # targeted perturbation: only the neurons the transmitter classifier is unsure about
    ("signflip_targeted", 0, 0, W0, {"FLYCNS_SIGNFLIP_TARGETED": "1"}),
    # connection-size threshold: stricter than the default 5 synapses (the fetch keeps nothing below 5,
    # so a looser threshold is impossible and graph.py refuses one)
    ("minweight10", 0, 0, W0, {"FLYCNS_MIN_WEIGHT": "10"}),
    ("minweight20", 0, 0, W0, {"FLYCNS_MIN_WEIGHT": "20"}),
    # stricter null: shuffle targets only within the same superclass (flycns/graph.py rewire_null)
    ("null_superclass", 0, 0, W0, {"FLYCNS_NULL": "superclass"}),
    # audit 2026-10-11: glutamate from nerve-cord neurons onto non-motor targets made excitatory (gap 10);
    # half the time step, as a numerics check (the 0.9 ms TTMn lag is 0.8 ms delay + one step);
    # the JON -> GF contact as EM annotates it, chemical with no calibrated coupling (gap 1)
    ("glu_vnc_excitatory", 0, 0, W0, {"FLYCNS_GLU_VNC": "excitatory"}),
    ("dt005", 0, 0, W0, {"FLYCNS_DT_MS": "0.05"}),
    ("jon_em", 0, 0, W0, {"FLYCNS_JON": "em"}),
]


def checks_line(suite):
    for line in suite.read_text(encoding="utf-8").splitlines():
        if "checks pass" in line:
            return line.strip("* ")
    return "?"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    only = sys.argv[1:]
    unknown = sorted(set(only) - {r[0] for r in RUNS})
    if unknown:
        sys.exit(f"unknown run(s) {unknown}; choose from {[r[0] for r in RUNS]}")
    for args in (["fit/audit_stimuli.py", "data"], ["-m", "flycns.integrity", "verify", "data"]):
        if subprocess.run([PY, *args]).returncode != 0:
            sys.exit("pre-flight check failed (see above); battery not started")
    incomplete = []
    with preserved(*(RES / b for b in BENCHES), RES / "SUITE.md"):   # canonical results come back exactly
        for tag, seed, flip, wscale, extra in (r for r in RUNS if not only or r[0] in only):
            env = {k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_")}
            env.update(FLYCNS_SEED=str(seed), FLYCNS_SIGNFLIP=str(flip), FLYCNS_WSCALE=str(wscale),
                       FLYCNS_RUN_TAG=tag, **extra)
            print(f"=== {time.strftime('%H:%M')} start {tag} (seed {seed}, signflip {flip}, wscale {wscale}"
                  + "".join(f", {k[7:].lower()} {v}" for k, v in extra.items()) + ")", flush=True)
            out = RES / "overnight" / tag
            out.mkdir(parents=True, exist_ok=True)
            failed = []
            for b, trials in BENCHES.items():
                (RES / b / "report.json").unlink(missing_ok=True)   # never file an earlier run's report here
                with open(RES / "overnight" / f"{tag}_{b}.log", "w", encoding="utf-8") as log:
                    code = subprocess.run([PY, f"benchmarks/{b}.py", trials, "data"], env=env,
                                          stdout=log, stderr=subprocess.STDOUT).returncode
                if code == 0 and (RES / b / "report.json").exists():
                    shutil.copy2(RES / b / "report.json", out / f"{b}_report.json")
                else:
                    failed.append(b)
                    print(f"  {b} errored (see results\\overnight\\{tag}_{b}.log)")
            # summarise only the benchmarks this run reran, so every tag's line counts the same checks
            if subprocess.run([PY, "benchmarks/summarize.py", *BENCHES], env=env, capture_output=True).returncode != 0:
                failed.append("summary")
            else:
                shutil.copy2(RES / "SUITE.md", out / "SUITE.md")
            line = checks_line(out / "SUITE.md") if (out / "SUITE.md").exists() else "no summary"
            print(f"  {line}" + (f"  (incomplete: {', '.join(failed)})" if failed else ""))
            if failed:
                incomplete.append(tag)
            git("add", "-A", "--", "results/overnight")
            if git("commit", "-qm", f"overnight: {tag} {line}" + (" INCOMPLETE" if failed else ""),
                   "--", "results/overnight").returncode == 0:
                if git("push", "-q").returncode != 0:
                    print("  (push failed; the commit is kept locally, run git push later)")
            print(f"=== {time.strftime('%H:%M')} done  {tag}", flush=True)
    print("\nSUMMARY")
    for d in sorted((RES / "overnight").iterdir()):
        if (d / "SUITE.md").exists():
            print(f"{d.name:<20} {checks_line(d / 'SUITE.md')}")
    if incomplete:
        sys.exit(f"incomplete runs: {', '.join(incomplete)} (see their logs in results\\overnight)")


if __name__ == "__main__":
    main()
