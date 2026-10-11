"""
Registration against a frozen model (audit 2026-10-11, gaps 2 and 3).

Version 1 registrations (results/<benchmark>/criteria.json) froze the criteria but not the model: the
model changed under them three times and the registered tests were rerun each time. A version 2
registration (results/<benchmark>/registration.json) records, besides the criteria:

  model   the content hash of every file that defines the model and its input (flycns model code, the loom
          tuning file, the data manifest, the package lock) and of the benchmark's own scripts, so that
          a threshold edited in scoring code is a changed registration, not a quiet change
  values  the declared parameter values, for a human reader (the hashes are what is enforced)

A registered run refuses to score if its criteria or any registered file differ (FLYCNS_ALLOW_DIRTY=1
overrides, is stamped, and is flagged ALLOW-DIRTY in the summary). A changed model needs a NEW
registration that names the one it supersedes. The registration is written by

    FLYCNS_REGISTER_ONLY=1 python benchmarks/<name>.py

which records it and exits before any data is loaded, so registrations can be committed before any
result exists. Every check's band must equal the band its criteria state: verify_bands() refuses a
report whose scoring used a different number.
"""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

from .integrity import PLUMBING, ROOT, _box, _git, allow_dirty, git_state, overrides

NAME = "registration.json"
VERSION = 2
# files that define the model and its inputs; guard, display and platform code is not listed (it does
# not change a number), and neither is the role table (it does not change a verdict)
# (the role table is listed: relabelling a failed independent check after the fact is a design change)
MODEL_FILES = ["flycns/__init__.py", "flycns/anatomy.py", "flycns/bench.py", "flycns/calibration.py",
               "flycns/graph.py", "flycns/model.py", "flycns/protocols.py", "flycns/stats.py",
               "data/loom_tuning_measured.json", "data/MANIFEST.json", "requirements.lock"]
PACKAGES = ("brian2", "numpy", "pandas", "scipy")


def _content_hash(path):
    """sha256 of a text file with line endings normalised, so a Windows checkout (CRLF) hashes the same
    as the committed file."""
    b = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def model_state(scripts=()):
    files = {}
    for rel in list(MODEL_FILES) + [str(Path(s).resolve().relative_to(ROOT)).replace("\\", "/") for s in scripts]:
        p = ROOT / rel
        files[rel] = _content_hash(p) if p.exists() else None
    combined = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return dict(files=files, hash=combined)


def _declared_values():
    """The declared parameter values, for the reader of a registration (not enforced: the files are)."""
    try:
        from .model import LIFParams
        from .graph import ELECTRICAL_SYNAPSES, INTRINSIC_OVERRIDES, SIGN_MAP, MIN_WEIGHT_DEFAULT
        from . import protocols as P
        return json.loads(json.dumps(dict(
            lif=LIFParams().__dict__, electrical=ELECTRICAL_SYNAPSES, intrinsic=INTRINSIC_OVERRIDES,
            sign_map=SIGN_MAP, min_weight=MIN_WEIGHT_DEFAULT, peak_hz=P.PEAK_HZ_DEFAULT,
            gain_sigma=P.GAIN_SIGMA_DEFAULT, loom_state=P.LOOM_STATE), default=str))
    except Exception as e:      # a registration must never fail on its human-readable part
        return dict(error=str(e)[:200])


def _versions():
    import importlib
    out = {}
    for name in PACKAGES:
        try:
            out[name] = importlib.import_module(name).__version__
        except Exception:
            out[name] = None
    return out


def _committed(f):
    """Is this registration file committed, and unchanged since? (A registration that only exists in the
    working tree could have been written by the very run that scores it.)"""
    rel = str(Path(f).resolve().relative_to(ROOT)).replace("\\", "/")
    code, _ = _git("ls-files", "--error-unmatch", rel)
    if code != 0:
        return False
    code, _ = _git("diff", "--quiet", "HEAD", "--", rel)
    return code == 0


def path(label):
    return ROOT / "results" / label / NAME


def register(label, criteria, scripts=(), supersedes=None):
    """Load or write this benchmark's version 2 registration and return its criteria. Call it before any
    data is loaded. Refuses on changed criteria or a changed model (unless FLYCNS_ALLOW_DIRTY=1).
    With FLYCNS_REGISTER_ONLY=1 it writes the registration (if absent) and exits."""
    f = path(label)
    crit = json.loads(json.dumps(criteria))
    state = model_state(scripts)
    register_only = os.environ.get("FLYCNS_REGISTER_ONLY") == "1"
    if not f.exists() and not register_only and not allow_dirty():
        raise SystemExit(f"[registry] {label} is not registered. Register first, commit, then run:\n"
                         f"  FLYCNS_REGISTER_ONLY=1 python benchmarks/<this script>   (writes {f.relative_to(ROOT)})")
    if not f.exists():
        st = git_state()
        if not st["clean"] and not allow_dirty():
            raise SystemExit(f"[registry] {label}: refusing to register on uncommitted code "
                             f"({', '.join(st['dirty_files'][:6])}); commit first")
        f.parent.mkdir(parents=True, exist_ok=True)
        rec = dict(version=VERSION, benchmark=label, criteria=crit, model=state, values=_declared_values(),
                   packages=_versions(),
                   supersedes=supersedes, git_commit=st["commit"], code_uncommitted=not st["clean"],
                   registered_at=datetime.datetime.now().isoformat(timespec="seconds"))
        f.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        print(f"[registry] {label}: registered (version {VERSION}, model {state['hash'][:12]}, commit {st['commit']})")
    reg = json.loads(f.read_text(encoding="utf-8"))
    if register_only:
        print(f"[registry] {label}: registration only; nothing run")
        sys.exit(0)
    problems = []
    if not _committed(f):
        problems.append(f"{f.relative_to(ROOT)} is not committed (or differs from the commit): a registration "
                        f"must be committed before the run it governs")
    if reg.get("criteria") != crit:
        problems.append("the criteria in the code differ from the registered ones")
    changed = sorted(k for k in set(reg["model"]["files"]) | set(state["files"])
                     if reg["model"]["files"].get(k) != state["files"].get(k))
    if changed:
        problems.append("the model changed since registration: " + ", ".join(changed[:8])
                        + (" ..." if len(changed) > 8 else ""))
    if problems:
        if not allow_dirty():
            raise SystemExit(f"[registry] {label} refuses to score: " + "; ".join(problems)
                             + f".\n  A changed design or model needs a NEW registration that supersedes {f.name}.")
        _box([f"{label}: REGISTRATION DOES NOT MATCH (FLYCNS_ALLOW_DIRTY=1); not a registered result"] + problems)
    # these run, but are not the registered result: a perturbation from the environment (the robustness
    # battery runs that way on purpose) or other package versions than the registration's
    caveats = []
    model_env = {k: v for k, v in overrides().items() if k not in PLUMBING and k != "FLYCNS_ALLOW_DIRTY"}
    if model_env:
        caveats.append("model settings overridden: " + ", ".join(f"{k}={v}" for k, v in model_env.items()))
    vers = _versions()
    if reg.get("packages") and vers != reg["packages"]:
        caveats.append(f"package versions {vers} differ from the registration's {reg['packages']}")
    if caveats:
        _box([f"{label}: runs, but is NOT the registered result"] + caveats)
    reg["_problems"], reg["_caveats"] = problems, caveats
    reg["_matches"] = not problems and not caveats
    return reg


def stamp(reg):
    """What a report records about the registration it was scored under."""
    bands = reg.get("_band_mismatches") or []
    return dict(file=f"results/{reg['benchmark']}/{NAME}", version=reg.get("version"),
                git_commit=reg.get("git_commit"), model_hash=reg["model"]["hash"],
                registered_at=reg.get("registered_at"), matches=bool(reg.get("_matches")) and not bands,
                problems=(reg.get("_problems") or []) + (reg.get("_caveats") or []) + bands)


def _all_bands(rec):
    """Every band a record was scored with, its own and those of its parts (combine records nest)."""
    out = [rec["band"]] if rec.get("band") is not None else []
    for part in rec.get("parts") or []:
        out += _all_bands(part)
    return out


def verify_bands(reg, uncertainty):
    """Every band the registration states for a check must be among the bands that check was scored
    with ("band" for one band, "bands" for a check made of parts), and every band a check was scored with
    must be registered for it. Mismatches are kept in the registration's stamp (so the report shows
    `matches: false` even under FLYCNS_ALLOW_DIRTY=1) and refuse the run otherwise. Returns them."""
    bad = []
    specs = reg["criteria"].get("checks") or {}
    for name, spec in specs.items():
        if not isinstance(spec, dict):
            continue
        wants = ([spec["band"]] if spec.get("band") is not None else []) + list(spec.get("bands") or [])
        if not wants:
            continue
        rec = uncertainty.get(name)
        if rec is None:
            if spec.get("conditional"):
                continue          # registered as scored only under a stated condition
            bad.append(f"{name}: registered but not scored")
            continue
        used = _all_bands(rec)
        if not used:
            continue              # scored without any band (unresolved as designed, or a point): nothing to compare
        for w in wants:
            if not any(_same_band(b, w) for b in used):
                bad.append(f"{name}: registered band {w} not among the bands it was scored with {used}")
        for b in used:
            if not any(_same_band(b, w) for w in wants):
                bad.append(f"{name}: scored with band {b}, which the registration does not state")
    for name, rec in uncertainty.items():
        spec = specs.get(name)
        has = isinstance(spec, dict) and (spec.get("band") is not None or spec.get("bands"))
        if _all_bands(rec) and not has:
            bad.append(f"{name}: scored with bands {_all_bands(rec)} but registered without any")
    reg["_band_mismatches"] = bad
    if bad and not allow_dirty():
        raise SystemExit("[registry] scoring used numbers that differ from the registration:\n  " + "\n  ".join(bad))
    return bad


def _same_band(a, b):
    if a is None or b is None or len(a) != 2 or len(b) != 2:
        return False
    return all((x is None and y is None) or (x is not None and y is not None and abs(float(x) - float(y)) < 1e-12)
               for x, y in zip(a, b))
