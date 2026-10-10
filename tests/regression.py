"""
Regression test: does every benchmark still run end to end, and do the fixed checks still hold?

Runs in an ISOLATED COPY of the repository (a temporary directory), on the synthetic toy graph from
scripts/make_testdata.py. Isolation matters: several benchmarks are pre-registered and write criteria files
the first time they run; running them on toy data inside the real repo would lock out the real runs.

What it checks:
  - unit: the Newcombe two-proportion interval reproduces the published worked example
  - the stimulus audit runs and finds no EMPTY set on the toy graph
  - each listed benchmark exits cleanly and writes its report
  - sentinel: gf_escape reports BENCHMARK PASS on the toy graph (it always has)
  - the brainsets export reloads through temporaldata (the exporter asserts this itself)
  - tests/unit.py: data fingerprints and manifest, null models, connection threshold, provenance
    stamping, the settings banner, the clean-tree guard on registered tests, the check-role table
  - the stricter null, the battery's new variants, the manifest CLI and the role-aware summary run
Toy numbers are artificial, so pass/fail on the toy says nothing about the fly; only that the code
runs and the fixed invariants hold.

The copy is taken from the working tree, so run it on a FRESH CLONE to reproduce CI exactly: on
27 September 2026 it passed locally but failed on GitHub, because a fresh clone has no testdata/
folder (git keeps no empty folders) and scripts/make_testdata.py did not create one. Both now do.

Run:  python tests/regression.py        (a few minutes; exits non-zero on any failure)
"""
import os
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
    ("null_strict", ["benchmarks/null_strict.py", "testdata"], {}, None),
    ("battery variant: min_weight 10", ["benchmarks/gf_escape.py", "2", "testdata"], {"FLYCNS_MIN_WEIGHT": "10"}, "min_weight 10"),
    ("battery variant: superclass null", ["benchmarks/gf_escape.py", "2", "testdata"], {"FLYCNS_NULL": "superclass"}, None),
    ("data manifest write + verify", ["-m", "flycns.integrity", "write", "testdata"], {}, "wrote testdata/MANIFEST.json"),
    ("integrity status", ["-m", "flycns.integrity", "verify", "testdata"], {}, "testdata: match"),
    ("suite summary with roles", ["benchmarks/summarize.py"], {}, "By role:"),
    # the toy graph scores checks the real data leaves unscored; every one of them needs a role too
    ("every toy-scored check has a role", ["-c", "import sys,pathlib; t=pathlib.Path('results/SUITE.md').read_text(); "
     "bad=[l for l in t.splitlines() if '| unclassified |' in l]; print('\\n'.join(bad) or 'all classified'); "
     "sys.exit(1 if bad else 0)"], {}, "all classified"),
]
# The isolated copy is not a git checkout, so the registered tests' clean-tree guard would refuse to
# run; the override is the documented escape hatch and is stamped into every toy report.
# (The guard itself is exercised against a real temporary git repository in tests/unit.py.)
BASE_ENV = {"FLYCNS_ALLOW_DIRTY": "1", "PYTHONUTF8": "1"}
STEP_TIMEOUT_S = 2400      # generous: the pure-Python engine on a slow Windows machine
TEXT = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")   # never cp1252 on Windows


def newcombe_unit():
    src = (ROOT / "benchmarks/auditory.py").read_text(encoding="utf-8")
    ns = {"np": np}
    exec(src[src.index("def wilson("):src.index("def two_prop_ci(")], ns)
    exec(src[src.index("def two_prop_ci("):src.index("    return d, lo, hi\n") + len("    return d, lo, hi\n")], ns)
    d, lo, hi = ns["two_prop_ci"](48, 80, 56, 70)
    return abs(lo - 0.0524) < 5e-4 and abs(hi - 0.3339) < 5e-4, f"{lo:.4f} to {hi:.4f} (want 0.0524 to 0.3339)"


def main():
    results = []
    ok, msg = newcombe_unit()
    results.append(("unit: Newcombe interval", ok, msg))
    sys.path.insert(0, str(ROOT))
    from tests.unit import run_all as unit_checks
    for label, ok, msg in unit_checks():
        results.append((label, ok, msg))
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<44} {msg}", flush=True)
    with tempfile.TemporaryDirectory(prefix="flycns_regress_", ignore_cleanup_errors=True) as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "data", "results", ".venv", "__pycache__", "*.log"))
        (work / "results").mkdir(); (work / "data").mkdir()
        (work / "testdata").mkdir(exist_ok=True)
        r = subprocess.run([sys.executable, "scripts/make_testdata.py"], cwd=work, **TEXT, env={**os.environ, **BASE_ENV})
        results.append(("make toy graph", r.returncode == 0, r.stderr.strip()[-200:]))
        for f in (work / "testdata").glob("*.parquet"):
            shutil.copy(f, work / "data" / f.name)          # scripts that read data/ directly
        for label, argv, env, sentinel in RUNS:
            t0 = time.time()
            try:
                r = subprocess.run([sys.executable, *argv], cwd=work, **TEXT,
                                   timeout=STEP_TIMEOUT_S, env={**os.environ, **BASE_ENV, **env})
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
            print(f"  {'PASS' if ok else 'FAIL'}  {label:<34} {note}", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, "scripts/export_brainsets.py", "2", "results/brainsets"], cwd=work,
                           **TEXT, timeout=STEP_TIMEOUT_S, env={**os.environ, **BASE_ENV})
        ok = r.returncode == 0 and "validated: reloads with temporaldata" in r.stdout
        results.append(("brainsets export reloads", ok, f"exit {r.returncode}, {round(time.time() - t0)}s"))
    print("\nREGRESSION SUMMARY")
    for label, ok, note in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<44} {note}")
    failed = [l for l, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed" + (f"; FAILED: {failed}" if failed else ""))
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # GitHub annotations: the key results show on the pull request page (GitHub caps notices per step)
        from flycns.windows import codegen_target
        eng = next((n for l, _, n in results if "engines" in l), "")
        print(f"::notice title=engine::{codegen_target()} engine on {sys.platform}, Python {sys.version.split()[0]}. {eng}")
        print(f"::notice title=regression::{len(results) - len(failed)}/{len(results)} passed")
        for l, ok, n in results:
            if not ok:
                print(f"::error title={l}::{n}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
