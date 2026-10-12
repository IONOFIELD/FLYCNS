"""
Identity check: does a code change leave every simulation exactly as it was?

A full real-data rerun takes 3-4 hours. This runs every job of that rerun (.github/workflows/rerun.yml) with a
few trials instead of the full count, and records a fingerprint of every simulation (scripts/fingerprint/
sitecustomize.py): the wired network, and after every run step every neuron's state and every spike. Two
versions of the code are identical on a job if every fingerprint matches, in order. Run the same reduced jobs
on both versions and compare; the full rerun then becomes the record rather than the gate.

    python scripts/fingerprint.py run <job> [out.jsonl]     one job of the rerun, reduced (the cloud runs these)
    python scripts/fingerprint.py jobs                      the job names and their reduced commands
    python scripts/fingerprint.py compare <dirA> <dirB>     one <job>.jsonl per job in each; exit 1 on any difference

What it proves, and what not: identical fingerprints mean identical simulations for the first trials of every
arm of every job (same network, same state after every step, same spikes). Later trials run the same code with
the same random-number stream, so a difference there would need code that behaves differently by trial number;
the full rerun, run alongside, still catches that. Scores are not compared here (a few trials give no
meaningful score), and registration checks are relaxed (FLYCNS_ALLOW_DIRTY=1) so reduced runs are allowed. The
version-1 registrations (results/*/criteria.json) record trial counts and refuse any other count whatever the
setting, so they are set aside for the job and put back afterwards; the reduced runs' own criteria files are
discarded. Nothing here is a result: run it in a throwaway checkout (the cloud does).
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "fingerprint"
B = "benchmarks/"
CORE = [[B + "gf_escape.py", "2", "data"], [B + "auditory.py", "2", "data"], [B + "feeding.py", "1", "data"]]
SCREEN8 = "aPhM2a,aPhM5,TPMN1,PhG1c,BM_Taste,claw_tpGRN,JO-FV,BM_Vib"

# job -> commands (each an argument list for the environment's Python). The full rerun's arguments, with the
# trial (or cycle, draw) count cut down; scripts without a count run as they are.
JOBS = {
    "core": CORE + [[B + "null_strict.py", "data"]],
    "gf-adapt": [[B + "fit_gf_adapt.py", "40"]],     # the fit refuses fewer than 40 trials on real data
    "a2": [[B + "a2_registered.py", "2"]],
    "a2-robustness": [[B + "a2_robustness.py", "2"]],
    "a2-contact-em": [[B + "a2_contact.py", "em", "2"]],
    "a2-contact-em-flip": [[B + "a2_contact.py", "em_flip", "2"]],
    "dnp31": [[B + "dnp31_trace.py"]],
    "auditory-wing": [[B + "auditory_wing_trace.py"]],
    "peptide-asta": [[B + "peptide_asta.py", "2"]],
    "flight-robustness": [[B + "flight_snpp16_robustness.py", "20"]],
    "flight-loop": [[B + "flight_loop.py", "20"]],
    "sensitivity-flight": [[B + "sensitivity_flight.py", "20"]],
    "flight-snpp16": [[B + "flight_snpp16.py", "20"]],
    "flight-graded": [[B + "flight_snpp16_graded.py", "20"]],
    "pc1-song": [[B + "pc1_song.py", "2"]],
    "dnp13-control": [[B + "dnp13_control.py", "2"]],
    "feeding-by-modality": [[B + "feeding_by_modality.py", "1"]],
    "gustatory-map": [[B + "gustatory_signed_map.py"]],
    "sugar-laterality": [[B + "sugar_laterality.py"]],
    "check-modulators": [["fit/check_modulators.py"]],
    "engines-real": [["fit/check_engines.py", "2"]],
    "check-jon-calibration": [["fit/check_jon_calibration.py", "4"]],
    "select-wscale": [["fit/select_wscale.py"]],
    "null-dc-escape": [[B + "null_distribution.py", "escape", "2", "2"]],
    "null-dc-song": [[B + "null_distribution.py", "song", "2", "2"]],
    "null-dc-auditory": [[B + "null_distribution.py", "auditory", "2", "2"]],
    "fit-regional": [[B + "fit_regional.py", "1"]],
    "fit-baseline": [[B + "fit_baseline.py", "1"]],
    "fit-gains": [[B + "fit_gains.py", "1"]],
    "sensitivity-cord": [[B + "sensitivity_cord.py", "2"]],
    "embodiment-gate": [[B + "embodiment_gate.py"]],
    "feeding-mechanism": [[B + "feeding_mechanism.py"]],
    "diagnose-feeding": [[B + "diagnose_feeding.py"]],
    "screen-50hz": [[B + "screen_afferents.py", "1", "data", "50", "0.4"]],
    "screen-200hz": [[B + "screen_afferents.py", "1", "data", "200", "0.4"]],
    "screen-w045": [[B + "screen_afferents.py", "1", "data", "50", "0.45", SCREEN8]],
    "screen-w06": [[B + "screen_afferents.py", "1", "data", "50", "0.6", SCREEN8]],
    "screen-w075": [[B + "screen_afferents.py", "1", "data", "50", "0.75", SCREEN8]],
    "screen-w1": [[B + "screen_afferents.py", "1", "data", "50", "1.0"]],
    "export-brainsets": [["scripts/export_brainsets.py", "2"]],
}


def battery_runs():
    """The robustness battery's arms (scripts/overnight.py RUNS), read without importing that script."""
    from flycns.integrity import DEFAULTS
    tree = ast.parse((ROOT / "scripts" / "overnight.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "RUNS")
    return eval(compile(ast.Expression(node.value), "overnight.py", "eval"),
                {"W0": float(DEFAULTS["FLYCNS_WSCALE"])})


def commands(job):
    """[(argv, extra env)] for a job."""
    if job.startswith("battery-"):
        tag = job[len("battery-"):]
        run = next((r for r in battery_runs() if r[0] == tag), None)
        if run is None:
            raise SystemExit(f"unknown battery arm {tag!r}")
        _, seed, flip, wscale, extra = run
        env = dict(FLYCNS_SEED=str(seed), FLYCNS_SIGNFLIP=str(flip), FLYCNS_WSCALE=str(wscale),
                   FLYCNS_RUN_TAG=tag, **extra)
        return [(c, env) for c in CORE]
    if job not in JOBS:
        raise SystemExit(f"unknown job {job!r}; see: python scripts/fingerprint.py jobs")
    return [(c, {}) for c in JOBS[job]]


def run(job, out):
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    base = {k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_")}
    base.update(FPRINT_LOG=str(out), FLYCNS_ALLOW_DIRTY="1",
                PYTHONPATH=os.pathsep.join([str(HOOK)] + [p for p in [os.environ.get("PYTHONPATH")] if p]))
    failed = []
    aside = sorted((ROOT / "results").glob("*/criteria.json"))
    for f in aside:
        f.rename(f.with_name("criteria.json.fp-aside"))
    try:
        _run_all(job, out, base, failed)
    finally:
        for f in aside:
            f.unlink(missing_ok=True)                           # a reduced run's own criteria, discarded
            f.with_name("criteria.json.fp-aside").rename(f)
    n = sum(1 for line in out.read_text(encoding="utf-8").splitlines() if '"kind": "run"' in line) if out.exists() else 0
    print(f"[fingerprint] {job}: {n} simulation steps fingerprinted -> {out}"
          + (f"; exited non-zero: {failed}" if failed else ""))
    if not n:     # structural checks never simulate; compare shows the count for every job either way
        print(f"[fingerprint] {job}: no simulation step was fingerprinted")


def _run_all(job, out, base, failed):
    for argv, extra in commands(job):
        print(f"[fingerprint] {job}: {' '.join(argv)}" + (f"  ({', '.join(f'{k}={v}' for k, v in extra.items())})"
                                                           if extra else ""), flush=True)
        code = subprocess.run([sys.executable, *argv], cwd=ROOT, env={**base, **extra}).returncode
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(kind="exit", argv=argv, code=code), sort_keys=True) + "\n")
        if code != 0:
            failed.append(" ".join(argv))


def _load(f):
    return [json.loads(line) for line in Path(f).read_text(encoding="utf-8").splitlines() if line.strip()]


def compare(a_dir, b_dir):
    a_dir, b_dir = Path(a_dir), Path(b_dir)
    jobs = sorted({p.stem for p in a_dir.glob("*.jsonl")} | {p.stem for p in b_dir.glob("*.jsonl")})
    bad, total = [], 0
    for job in jobs:
        fa, fb = a_dir / f"{job}.jsonl", b_dir / f"{job}.jsonl"
        if not fa.exists() or not fb.exists():
            bad.append(f"{job}: missing in {'A' if not fa.exists() else 'B'}")
            continue
        ra, rb = _load(fa), _load(fb)
        na = sum(r["kind"] in ("net", "run") for r in ra)
        total += na
        first = next((k for k, (x, y) in enumerate(zip(ra, rb)) if x != y), None)
        if first is None and len(ra) == len(rb):
            print(f"  same      {job:<28} {na:>7} fingerprints")
            continue
        if first is None:
            first = min(len(ra), len(rb))
        x = ra[first] if first < len(ra) else "<end>"
        y = rb[first] if first < len(rb) else "<end>"
        bad.append(f"{job}: first difference at line {first + 1} of {len(ra)}/{len(rb)}:\n      A {x}\n      B {y}")
        print(f"  DIFFERENT {job:<28} (line {first + 1})")
    print(f"\n{len(jobs) - len(bad)} of {len(jobs)} jobs identical; {total} fingerprints compared")
    for b in bad:
        print("  " + b)
    return not bad


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "run" and len(sys.argv) >= 3:
        run(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ROOT / "fingerprints" / f"{sys.argv[2]}.jsonl")
    elif cmd == "jobs":
        for job in list(JOBS) + [f"battery-{r[0]}" for r in battery_runs()]:
            for argv, env in commands(job):
                print(f"{job:<28} {' '.join(argv)}" + (f"   {env}" if env else ""))
    elif cmd == "compare" and len(sys.argv) == 4:
        sys.exit(0 if compare(sys.argv[2], sys.argv[3]) else 1)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
