"""
Regression test: does every benchmark still run end to end, and do the fixed checks still hold?

Runs in an ISOLATED COPY of the repository (a temporary directory), on the synthetic toy graph from
make_testdata.py. Isolation matters: several benchmarks are pre-registered and write criteria files
the first time they run; running them on toy data inside the real repo would lock out the real runs.

What it checks:
  - unit: the Newcombe two-proportion interval reproduces the published worked example
  - the stimulus audit runs and finds no EMPTY set on the toy graph
  - each listed benchmark exits cleanly and writes its report
  - sentinel: gf_escape reports BENCHMARK PASS on the toy graph (it always has)
  - the brainsets export reloads through temporaldata (the exporter asserts this itself)
Toy numbers are artificial, so pass/fail on the toy says nothing about the fly; only that the code
runs and the fixed invariants hold.

The copy is taken from the working tree, so run it on a FRESH CLONE to reproduce CI exactly: on
27 September 2026 it passed locally but failed on GitHub, because a fresh clone has no testdata/
folder (git keeps no empty folders) and make_testdata.py did not create one. Both now do.

Run:  python tests/regression.py        (a few minutes; exits non-zero on any failure)
"""
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNS = [  # (label, argv relative to the copy, extra env, sentinel substring or None)
    ("audit", ["fit/audit_stimuli.py", "testdata"], {}, None),
    ("gf_escape", ["benchmarks/gf_escape.py", "2", "testdata"], {}, "BENCHMARK PASS"),
    ("auditory", ["benchmarks/auditory.py", "2", "testdata"], {}, None),
    ("feeding", ["benchmarks/feeding.py", "2", "testdata"], {}, None),
    ("gustatory_signed_map", ["benchmarks/gustatory_signed_map.py", "testdata"], {}, None),
    ("sugar_laterality", ["benchmarks/sugar_laterality.py", "testdata"], {}, None),
    ("feeding_by_modality", ["benchmarks/feeding_by_modality.py", "2", "testdata"], {}, None),
    ("pc1_song", ["benchmarks/pc1_song.py", "2", "testdata"], {}, None),
    ("dnp13_control", ["benchmarks/dnp13_control.py", "2", "testdata"], {}, None),
    ("flight_snpp16", ["benchmarks/flight_snpp16.py", "20", "testdata"], {"FLYCNS_TARGET_TYPE": "SApp10"}, None),
    ("a2_registered", ["benchmarks/a2_registered.py", "4", "testdata"], {}, None),
    ("a2_robustness", ["benchmarks/a2_robustness.py", "2", "testdata"], {}, None),
]


def newcombe_unit():
    src = (ROOT / "benchmarks/auditory.py").read_text()
    ns = {"np": np}
    exec(src[src.index("def wilson("):src.index("def two_prop_ci(")], ns)
    exec(src[src.index("def two_prop_ci("):src.index("    return d, lo, hi\n") + len("    return d, lo, hi\n")], ns)
    d, lo, hi = ns["two_prop_ci"](48, 80, 56, 70)
    return abs(lo - 0.0524) < 5e-4 and abs(hi - 0.3339) < 5e-4, f"{lo:.4f} to {hi:.4f} (want 0.0524 to 0.3339)"


def main():
    results = []
    ok, msg = newcombe_unit()
    results.append(("unit: Newcombe interval", ok, msg))
    with tempfile.TemporaryDirectory(prefix="flycns_regress_") as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "data", "results", ".venv", "__pycache__", "*.log"))
        (work / "results").mkdir(); (work / "data").mkdir()
        (work / "testdata").mkdir(exist_ok=True)
        r = subprocess.run([sys.executable, "make_testdata.py"], cwd=work, capture_output=True, text=True)
        results.append(("make toy graph", r.returncode == 0, r.stderr.strip()[-200:]))
        for f in (work / "testdata").glob("*.parquet"):
            shutil.copy(f, work / "data" / f.name)          # scripts that read data/ directly
        for label, argv, env, sentinel in RUNS:
            t0 = time.time()
            try:
                r = subprocess.run([sys.executable, *argv], cwd=work, capture_output=True, text=True,
                                   timeout=900, env={**__import__("os").environ, **env})
                out = r.stdout + r.stderr
                ok = r.returncode == 0 and "Traceback" not in out
                if sentinel:
                    ok = ok and sentinel in out
                note = f"exit {r.returncode}, {round(time.time() - t0)}s"
                if not ok:
                    note += " | " + (out.strip().splitlines() or [""])[-1][:160]
            except subprocess.TimeoutExpired:
                ok, note = False, "timeout"
            results.append((label, ok, note))
            print(f"  {'PASS' if ok else 'FAIL'}  {label:<24} {note}", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, "export_brainsets.py", "2", "results/brainsets"], cwd=work,
                           capture_output=True, text=True, timeout=900)
        ok = r.returncode == 0 and "validated: reloads with temporaldata" in r.stdout
        results.append(("brainsets export reloads", ok, f"exit {r.returncode}, {round(time.time() - t0)}s"))
    print("\nREGRESSION SUMMARY")
    for label, ok, note in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<26} {note}")
    failed = [l for l, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed" + (f"; FAILED: {failed}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
