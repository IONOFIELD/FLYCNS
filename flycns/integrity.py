"""
Run integrity: which code, which data and which settings produced a result.

Three guards, each cheap enough to run on every benchmark:

  1. CODE   git commit plus whether any tracked code differs from it. A result stamped with a
            commit is only reproducible if the working tree matched that commit. Registered
            (pre-registered) benchmarks refuse to run on a dirty tree; set FLYCNS_ALLOW_DIRTY=1
            to override, and the override is stamped into the report.
  2. DATA   a content fingerprint of every input table, independent of row order and of the
            parquet writer's version, checked against data/MANIFEST.json. The manifest is
            committed, so anyone who fetches the connectome later can prove they hold the same
            data, or learn exactly which table differs.
  3. SETTINGS  every FLYCNS_* environment override is announced in a banner when the graph is
            loaded and stamped into every report, so a stale `export` cannot silently change a run.

Command line (also menu option 49):
    python -m flycns.integrity status [data_dir]     code state, overrides, data vs manifest
    python -m flycns.integrity write  [data_dir]     (re)write data_dir/MANIFEST.json
    python -m flycns.integrity verify [data_dir]     exit 1 unless the data match the manifest
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Committed files that shape every result: model inputs inside data/ count as code for the guard
MODEL_INPUTS = ("data/loom_tuning_measured.json",)
CODE_PATHSPECS = ["*.py", "*.cmd", "requirements*.txt", "requirements*.lock", *MODEL_INPUTS]
NOT_CODE_PREFIXES = ("results/", "data/", "testdata/")
CORE_TABLES = ("neurons.parquet", "edges.parquet")   # must be present; derived tables are optional
FINGERPRINT_ALGO = "rowhash-v2"   # v2: dtype-family labels and None for missing text, so pandas 2 and 3 agree
MANIFEST = "MANIFEST.json"
CACHE = ".fingerprints.json"      # per data dir, gitignored; keyed by size and mtime

# Settings that only route output or count trials; announced but not treated as model overrides.
PLUMBING = {"FLYCNS_RUN_TAG", "FLYCNS_AUDITORY_OUT", "FLYCNS_A2_TRIALS", "FLYCNS_ALLOW_DIRTY",
            "FLYCNS_CODEGEN", "FLYCNS_EXPECT_ENGINE"}   # engine: same equations, recorded as `engine`
# A setting equal to its declared default changes nothing and is not an override.
DEFAULTS = {"FLYCNS_SEED": "0", "FLYCNS_SIGNFLIP": "0", "FLYCNS_SIGNFLIP_TARGETED": "0", "FLYCNS_WSCALE": "0.3",
            "FLYCNS_PEPTIDE": "0", "FLYCNS_NULL": "global", "FLYCNS_MIN_WEIGHT": "5", "FLYCNS_PEAK_HZ": "5.0",
            "FLYCNS_LOOM_STATE": "stationary", "FLYCNS_BASELINE_DEPOL": "0", "FLYCNS_BASELINE_NOISE": "0"}


def _git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=10)
        return r.returncode, r.stdout
    except Exception:
        return 1, ""


# ---------------------------------------------------------------------------------------- code
def git_state():
    """Commit and dirty files (tracked code changes plus untracked code), relative to ROOT."""
    rc, out = _git("rev-parse", "--is-inside-work-tree")
    if rc != 0 or out.strip() != "true":
        return dict(is_repo=False, commit="", dirty_files=[], clean=False)
    _, commit = _git("rev-parse", "--short", "HEAD")
    rc, status = _git("status", "--porcelain", "--untracked-files=all", "--", *CODE_PATHSPECS)
    if rc != 0:     # an unreadable state is never "clean"
        return dict(is_repo=True, commit=commit.strip(), dirty_files=["? git status failed"], clean=False)
    dirty = []
    for line in status.splitlines():
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path in MODEL_INPUTS or not path.startswith(NOT_CODE_PREFIXES):
            dirty.append(f"{line[:2].strip() or '?'} {path}")
    return dict(is_repo=True, commit=commit.strip(), dirty_files=dirty, clean=not dirty)


def allow_dirty():
    return os.environ.get("FLYCNS_ALLOW_DIRTY") == "1"


def require_clean(label):
    """Refuse a registered run unless the code that will produce it is committed."""
    st = git_state()
    if st["clean"]:
        return st
    why = ("this is not a git checkout, so the result cannot be tied to a commit"
           if not st["is_repo"] else
           f"{len(st['dirty_files'])} code file(s) differ from commit {st['commit']}: "
           + ", ".join(st["dirty_files"][:8]) + (" ..." if len(st["dirty_files"]) > 8 else ""))
    if allow_dirty():
        _box([f"{label}: RUNNING ON UNCOMMITTED CODE (FLYCNS_ALLOW_DIRTY=1)", why,
              "The report is stamped dirty and must not be quoted as a registered result."])
        return st
    raise SystemExit(f"[integrity] {label} is a registered test and refuses to run: {why}.\n"
                     f"  Commit (or stash) the changes first, so the result can be traced to code.\n"
                     f"  For a throwaway run, in PowerShell: $env:FLYCNS_ALLOW_DIRTY=1 (stamped into the report).")


# -------------------------------------------------------------------------------------- settings
def _is_default(key, value):
    d = DEFAULTS.get(key)
    if d is None:
        return False
    try:
        return float(value) == float(d)
    except ValueError:
        return value.strip().lower() == d


def overrides():
    """FLYCNS_* settings that differ from the declared defaults (empty values are unset)."""
    return {k: v for k, v in sorted(os.environ.items())
            if k.startswith("FLYCNS_") and v.strip() != "" and not _is_default(k, v)}


_ANNOUNCED = False


def announce_overrides():
    """Print a banner once per process if any FLYCNS_* setting is present."""
    global _ANNOUNCED
    if _ANNOUNCED:
        return
    _ANNOUNCED = True
    model = {k: v for k, v in overrides().items() if k not in PLUMBING}
    if model:
        _box(["SETTINGS OVERRIDDEN BY ENVIRONMENT (not the declared parameter set):"]
             + [f"  {k}={v}" for k, v in model.items()]
             + ["These are stamped into the report. Unset them for a canonical run."])


def _box(lines):
    w = min(max(len(s) for s in lines) + 4, 110)
    bar = "!" * w
    print(bar, file=sys.stderr)
    for s in lines:
        print(f"! {s}", file=sys.stderr)
    print(bar, file=sys.stderr, flush=True)


# ------------------------------------------------------------------------------------------ data
def table_fingerprint(path):
    """Content fingerprint of a parquet table, independent of row order, column order and file
    encoding. Per-row 64-bit hashes (pandas hash_pandas_object over columns in sorted order) are
    sorted, then sha256-hashed. Also returns portable invariants (row count, columns, column sums)
    that anyone can recompute without pandas, as a cross-check if the hashing library changes."""
    import numpy as np
    import pandas as pd
    df = pd.read_parquet(path)
    cols = sorted(map(str, df.columns))
    df.columns = list(map(str, df.columns))
    df = df[cols]
    # Version-independent: text columns are labelled "text" and missing text is None, because pandas 2
    # reads them as object (missing None) and pandas 3 as str (missing NaN), which would hash apart.
    kinds = []
    for c in cols:
        if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object:
            df[c] = df[c].astype(object).where(df[c].notna(), None)
            kinds.append([c, "text"])
        else:
            kinds.append([c, str(df[c].dtype)])
    rows = np.array(pd.util.hash_pandas_object(df, index=False).to_numpy(dtype="uint64"), copy=True)
    rows.sort()
    h = hashlib.sha256()
    h.update(json.dumps(kinds).encode())
    h.update(rows.tobytes())
    sums = {}
    for c in cols:
        s = df[c]
        if pd.api.types.is_bool_dtype(s):
            sums[c] = int(s.fillna(False).astype(bool).sum())
        elif pd.api.types.is_integer_dtype(s):
            sums[c] = str(int(s.fillna(0).astype("int64").astype(object).sum()))  # exact, no overflow
        elif pd.api.types.is_float_dtype(s):
            sums[c] = float(np.round(np.nansum(s.to_numpy(dtype="float64")), 6))
    return dict(digest=h.hexdigest(), rows=int(len(df)), columns=cols, sums=sums)


def _cached_fingerprint(path, cache):
    st = path.stat()
    import pandas as pd
    key = f"{path.name}:{st.st_size}:{st.st_mtime_ns}:{FINGERPRINT_ALGO}:pandas{pd.__version__.split('.')[0]}"
    if key not in cache:
        cache[key] = table_fingerprint(path)
    return cache[key]


def fingerprints(data_dir="data", names=None):
    """Fingerprints for the named parquet files (default: every top-level *.parquet)."""
    d = Path(data_dir)
    paths = [d / n for n in names] if names else sorted(d.glob("*.parquet"))
    paths = [p for p in paths if p.exists()]
    cf = d / CACHE
    try:
        cache = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    except Exception:
        cache = {}
    out = {p.name: _cached_fingerprint(p, cache) for p in paths}
    live = {k for k in cache if (d / k.split(":", 1)[0]).exists()}   # keep entries for every table on disk
    try:
        cf.write_text(json.dumps({k: cache[k] for k in live}), encoding="utf-8")
    except OSError:
        pass
    return out


def write_manifest(data_dir="data"):
    fps = fingerprints(data_dir)
    if not fps:
        raise SystemExit(f"[integrity] no *.parquet in {data_dir}; nothing to record")
    import pandas as pd
    man = dict(algorithm=FINGERPRINT_ALGO, pandas=pd.__version__,
               dataset="male-cns:v1.0 (neuprint.janelia.org)",
               written_at=datetime.datetime.now().isoformat(timespec="seconds"),
               files={k: v for k, v in sorted(fps.items())})
    (Path(data_dir) / MANIFEST).write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    return man


def verify_data(data_dir="data", names=None):
    """Compare data_dir against its manifest. Returns dict(status, problems, ...).
    status: 'match' | 'mismatch' | 'no-manifest' | 'no-data'."""
    d = Path(data_dir)
    mf = d / MANIFEST
    if not mf.exists():
        return dict(status="no-manifest", problems=[], data_dir=str(d))
    man = json.loads(mf.read_text(encoding="utf-8"))
    want = man.get("files", {})
    check = [n for n in (names or want) if n in want]
    have = fingerprints(data_dir, check)
    problems = []
    for n in check:
        if n not in have:
            if n in CORE_TABLES:      # derived tables (synapse transmitters, ROI membership) are optional
                problems.append(f"{n}: listed in manifest but missing")
            continue
        a, b = have[n], want[n]
        if a["digest"] != b["digest"]:
            same_inv = (a["rows"], a["columns"], a["sums"]) == (b["rows"], b["columns"], b["sums"])
            problems.append(f"{n}: content differs from manifest"
                            + (" (row count, columns and column sums all match: likely a hashing-library change,"
                               " not a data change; review, then rewrite the manifest)" if same_inv else
                               f" (rows {a['rows']} vs {b['rows']}; columns "
                               f"{'same' if a['columns'] == b['columns'] else 'differ'})"))
    if names:
        problems += [f"{n}: not listed in manifest" for n in names if n not in want and (d / n).exists()]
    return dict(status="match" if not problems else "mismatch", problems=problems, data_dir=str(d),
                manifest_written_at=man.get("written_at"))


def require_data(data_dir, label, names=None):
    """Registered runs: refuse on a manifest mismatch; warn loudly when there is no manifest."""
    v = verify_data(data_dir, names)
    if v["status"] == "mismatch":
        if allow_dirty():
            _box([f"{label}: DATA DIFFER FROM {data_dir}/{MANIFEST} (FLYCNS_ALLOW_DIRTY=1)"] + v["problems"])
            return v
        raise SystemExit(f"[integrity] {label} refuses to run: {data_dir} differs from its manifest:\n  "
                         + "\n  ".join(v["problems"])
                         + "\n  If the data were deliberately refetched, review, then rewrite the fingerprint: "
                           f".venv\\Scripts\\python.exe -m flycns.integrity write {data_dir}")
    if v["status"] == "no-manifest" and Path(data_dir).resolve() == (ROOT / "data").resolve():
        _box([f"{label}: no {data_dir}/{MANIFEST}; the input data are not pinned.",
              "Run setup.cmd once: it records the fingerprint (menu 51 then commits it)."])
    return v


def criteria_differ(crit_file, criteria):
    """True if a registered test's committed criteria differ from the ones in its code. Compared in
    the JSON form they are stored in: a tuple in code and the list it was saved as are the same
    criterion (compared raw, a registered test with a tuple could never be rerun)."""
    stored = json.loads(Path(crit_file).read_text(encoding="utf-8")).get("criteria")
    return stored != json.loads(json.dumps(criteria))


# ----------------------------------------------------------------------------- canonical results
class preserved:
    """Context manager: snapshot result folders and files, and put them back exactly on exit, even
    after an error or Ctrl+C. Paths that did not exist before are removed. Used wherever a perturbed
    run writes into a canonical result folder (the robustness battery, the stricter null). If a
    restore fails (a file held open by another program on Windows), the snapshot is kept and its
    location printed, so nothing is lost."""

    def __init__(self, *paths):
        self.paths = [Path(p) for p in paths]

    def __enter__(self):
        import shutil
        import tempfile
        self.snap = Path(tempfile.mkdtemp(prefix="flycns_canonical_"))
        self.had = {}
        for i, p in enumerate(self.paths):
            self.had[p] = p.exists()
            if p.is_dir():
                shutil.copytree(p, self.snap / str(i))
            elif p.exists():
                shutil.copy2(p, self.snap / str(i))
        return self

    def __exit__(self, *exc):
        import shutil
        failed = []
        for i, p in enumerate(self.paths):
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.exists():
                    p.unlink()
                if self.had[p]:
                    src = self.snap / str(i)
                    (shutil.copytree(src, p) if src.is_dir() else shutil.copy2(src, p))
            except OSError as e:
                failed.append(f"{p}: {e}")
        if failed:
            _box(["could not fully restore the canonical results:"] + failed
                 + [f"the untouched copies are kept in {self.snap}"])
        else:
            shutil.rmtree(self.snap, ignore_errors=True)
            print("canonical results restored", flush=True)
        return False


# ------------------------------------------------------------------------------------ provenance
LOADED = {}   # filled by graph.load_graph: data_dir, min_weight, counts


def provenance_record():
    """Everything needed to reproduce a report, or to know it cannot be reproduced."""
    st = git_state()
    rec = dict(written_at=datetime.datetime.now().isoformat(timespec="seconds"),
               git_commit=st["commit"], git_is_repo=st["is_repo"], git_dirty=not st["clean"],
               dirty_files=st["dirty_files"][:20], allow_dirty=allow_dirty(),
               env=overrides(), python=sys.version.split()[0])
    try:
        import brian2, numpy, pandas
        rec["versions"] = dict(brian2=brian2.__version__, numpy=numpy.__version__, pandas=pandas.__version__)
        from .windows import _DONE
        rec["engine"] = _DONE.get("codegen", "not used")
        rec["platform"] = sys.platform
    except Exception:
        pass
    proto = sys.modules.get("flycns.protocols")
    if proto is not None:    # the measured loom input, whenever this run could have used it
        lf = Path(proto.LOOM_FILE)
        rec["loom_input"] = dict(source=proto.TUNING_SOURCE, state=proto.LOOM_STATE,
                                 sha256=hashlib.sha256(lf.read_bytes()).hexdigest()[:16] if lf.exists() else None)
    if LOADED:
        rec["graph"] = {k: v for k, v in LOADED.items()}
        dd = LOADED.get("data_dir")
        if dd:
            # the anatomical SEZ table changes region readouts, so it is stamped too when present
            names = ["neurons.parquet", "edges.parquet"] + \
                (["roi_membership.parquet"] if (Path(dd) / "roi_membership.parquet").exists() else [])
            try:
                fps = fingerprints(dd, names)
                rec["data"] = dict(dir=str(dd), digests={k: v["digest"][:16] for k, v in fps.items()},
                                   manifest=verify_data(dd, names)["status"])
            except Exception as e:   # provenance must never crash a finished run
                rec["data"] = dict(dir=str(dd), error=str(e)[:200])
    return rec


def _cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "data"
    if cmd == "write":
        man = write_manifest(data_dir)
        print(f"wrote {data_dir}/{MANIFEST}:")
        for n, f in man["files"].items():
            print(f"  {n:<28} {f['rows']:>12,} rows  {f['digest'][:16]}")
        print(f"commit it:  git add {data_dir}/{MANIFEST}   then   git commit -m \"pin input data\"")
    elif cmd == "verify":
        v = verify_data(data_dir)
        print(f"{data_dir}: {v['status']}")
        for p in v["problems"]:
            print("  " + p)
        sys.exit(0 if v["status"] in ("match", "no-manifest") else 1)
    elif cmd == "status":
        st = git_state()
        print(f"code     commit {st['commit'] or '-'}  "
              + ("clean" if st["clean"] else ("not a git checkout" if not st["is_repo"]
                                              else f"DIRTY: {', '.join(st['dirty_files'][:6])}")))
        ov = overrides()
        print("settings " + (", ".join(f"{k}={v}" for k, v in ov.items()) if ov else "declared defaults (no FLYCNS_* overrides)"))
        v = verify_data(data_dir)
        print(f"data     {data_dir}: {v['status']}" + (f" (manifest {v.get('manifest_written_at')})" if v.get("manifest_written_at") else ""))
        for p in v["problems"]:
            print("  " + p)
    else:
        raise SystemExit("usage: python -m flycns.integrity [status|write|verify] [data_dir]")


if __name__ == "__main__":
    _cli()
