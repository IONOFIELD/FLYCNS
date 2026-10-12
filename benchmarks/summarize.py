"""Collect every results/*/report.json (or only the named benchmarks: summarize.py gf_escape auditory)
into results/SUITE.md with one parameter set declared.

Every check is shown with its ROLE (flycns/calibration.py): only checks that were not a target of
any fit count as tests of the model. Reports are flagged when they were produced under settings
overrides (a robustness perturbation, not the declared parameter set), on uncommitted code, on
data that do not match data/MANIFEST.json, or by model code that has changed since (STALE)."""
import json, os, re, subprocess, sys, unicodedata
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import LIFParams
from flycns.calibration import role
from flycns.integrity import PLUMBING, is_registration_name

rows, stamps, flags = [], {}, {}
counts, passed_by_role, unresolved_by_role = Counter(), Counter(), Counter()
with_interval = 0


def _fmt(x):
    return "-" if x is None else (f"{x:.3g}" if isinstance(x, float) else str(x))


def interval_text(u):
    """The estimate, its interval and band (or how it was scored) for the checks table."""
    if not u:
        return "point, no interval"
    est, ci, band = u.get("estimate"), u.get("ci95"), u.get("band")
    m = u.get("method", "")
    if m.startswith("per-draw") and u.get("draws") is not None:
        # the measurement (each draw's value) and the count of draws in band, kept apart: the estimate of a
        # per-draw record is the SHARE of draws in band, which printed beside the band read as a measurement
        d = [float(x) for x in u["draws"]]                      # in draw order
        s_ = sorted(d)
        vals = ("none" if not d else ", ".join(_fmt(x) for x in d) if len(d) <= 8 else
                f"median {_fmt(s_[len(s_) // 2] if len(s_) % 2 else (s_[len(s_) // 2 - 1] + s_[len(s_) // 2]) / 2)}, "
                f"range {_fmt(s_[0])} to {_fmt(s_[-1])}")
        lo_b = "(" if u.get("band_lower_exclusive") else "["
        bt = (f"{lo_b}{_fmt(band[0]) if band[0] is not None else '-inf'}, {_fmt(band[1]) if band[1] is not None else 'inf'}]"
              if band and any(b is not None for b in band) else "its band")
        mm = re.match(r"per-draw \((\d+) of (\d+) in band; pass needs (\d+)\)", m)
        count = f"{mm.group(1)} of {mm.group(2)} draws in band, pass needs {mm.group(3)}" if mm else m
        return f"draws {vals}; band {bt}; {count}"
    txt = _fmt(est)
    if ci:
        txt += f" [{_fmt(ci[0])}, {_fmt(ci[1])}]"
    if band and any(b is not None for b in band):
        lo_b = "(" if u.get("band_lower_exclusive") else "["
        txt += f" in {lo_b}{_fmt(band[0]) if band[0] is not None else '-inf'}, {_fmt(band[1]) if band[1] is not None else 'inf'}]"
    m = u.get("method", "")
    return txt + (f"; {m}" if m and m not in ("bootstrap",) else "")
# optional benchmark names restrict the summary (the battery summarises only the suite it reran)
only = set(sys.argv[1:])
reports = sorted(p for p in Path("results").glob("*/report.json") if not only or p.parent.name in only)
# STALE: the code that produced a report has changed since. Reports from one parallel cloud rerun are
# written hours apart and are not stale; a report whose commit git cannot compare falls back to time
# (written over an hour before the newest report)
import datetime as _dt
MODEL_CODE = ["flycns", "benchmarks", ":(exclude)benchmarks/summarize.py", "fit", "scripts/export_brainsets.py",
              "data/loom_tuning_measured.json",
              "requirements.lock"]
_changed = {}
# the trial counts the committed results are run at (fly.py defaults, scripts/run_all.py, rerun.yml)
CANONICAL_TRIALS = {"gf_escape": 40, "auditory": 40, "feeding": 6, "peptide_asta": 10, "pc1_song": 10,
                    "dnp13_control": 10, "feeding_by_modality": 6, "a2_registered": 120, "a2_robustness": 100,
                    "flight_loop": 400, "flight_snpp16": 400, "flight_snpp16_graded": 400, "flight_snpp16_robustness": 400,
                    "null_dc_escape": 40, "null_dc_song": 30, "null_dc_auditory": 40,
                    "a2_contact_em": 120, "a2_contact_em_flip": 120}


def trial_count(r):
    crit = r.get("criteria") if isinstance(r.get("criteria"), dict) else {}
    for k in ("n_trials", "n_trials_per_arm", "n_cycles"):
        if isinstance(r.get(k), (int, float)):
            return r[k]
    for k in ("trials_per_arm", "n_trials", "n_cycles"):
        if isinstance(crit.get(k), (int, float)):
            return crit[k]
    return None


def code_changed_since(commit):
    """True or False: does the model code differ between this commit and HEAD? None if git cannot tell."""
    if commit and commit not in _changed:
        r = subprocess.run(["git", "diff", "--quiet", commit, "HEAD", "--", *MODEL_CODE], capture_output=True)
        _changed[commit] = {0: False, 1: True}.get(r.returncode)
    return _changed.get(commit)


stamps_written = [json.loads(r.read_text(encoding="utf-8")).get("provenance", {}).get("written_at", "") for r in reports]
newest_written = max((w for w in stamps_written if w), default="")
for rep in reports:
    r = json.loads(rep.read_text(encoding="utf-8"))
    name = r.get("benchmark", rep.parent.name)
    prov = r.get("provenance", {})
    model_env = {k: v for k, v in (prov.get("env") or {}).items() if k not in PLUMBING and k != "FLYCNS_ALLOW_DIRTY"}
    f = []
    if model_env:
        f.append("PERTURBED")
    if prov.get("allow_dirty") or (prov.get("env") or {}).get("FLYCNS_ALLOW_DIRTY") == "1":
        f.append("ALLOW-DIRTY")   # the guards were waived for this run
    if prov.get("git_dirty"):
        f.append("DIRTY")
    if (prov.get("data") or {}).get("manifest") == "mismatch":
        f.append("DATA-MISMATCH")
    written = prov.get("written_at", "")
    changed = code_changed_since(prov.get("git_commit", ""))
    if changed or (changed is None and written and newest_written and newest_written > written and (
            _dt.datetime.fromisoformat(newest_written) - _dt.datetime.fromisoformat(written)).total_seconds() > 3600):
        f.append("STALE")
    if not prov or "git_dirty" not in prov:
        f.append("UNSTAMPED")   # written before integrity stamping (2026-10-10); rerun to stamp
    elif not prov.get("data"):
        f.append("UNPINNED")    # no record of which input tables produced it
    scored_here = any(v is not None for v in (r.get("checks") or {}).values())
    if scored_here and not (r.get("registration") or {}).get("matches"):
        f.append("UNREGISTERED")   # not scored under a matching version 2 registration (flycns/registry.py)
    n_run, n_canon = trial_count(r), CANONICAL_TRIALS.get(name)
    if n_run is not None and n_canon is not None and n_run < n_canon:
        f.append(f"TRIALS {n_run}<{n_canon}")
    flags[name] = f
    stamps[name] = dict(written_at=prov.get("written_at", "unstamped"), commit=prov.get("git_commit", ""),
                        env=model_env, data=((prov.get("data") or {}).get("digests") or {}))
    unc = r.get("uncertainty") or {}
    for k, v in r.get("checks", {}).items():
        rl, why = role(name, k) if v is not None else ("reported", "reported, not scored")
        u = unc.get(k) if v is not None else None
        # the three-way verdict (flycns/stats.py) when the report carries one; else the point verdict
        res = "SKIP" if v is None else (u["verdict"] if u else ("PASS" if v else "FAIL"))
        if v is not None:
            counts[rl] += 1
            passed_by_role[rl] += res == "PASS"
            unresolved_by_role[rl] += res == "UNRESOLVED"
            with_interval += bool(u)
        rows.append(f"| {name} | {k} | {res} | {interval_text(u) if v is not None else '-'} | {rl} | {', '.join(f) or '-'} |")

total, passed = sum(counts.values()), sum(passed_by_role.values())
unresolved = sum(unresolved_by_role.values())
canonical = not any(("PERTURBED" in f or "DIRTY" in f or "ALLOW-DIRTY" in f or "DATA-MISMATCH" in f or "UNPINNED" in f
                     or "STALE" in f or "UNREGISTERED" in f
                     or any(x.startswith("TRIALS") for x in f)) for f in flags.values())
p = LIFParams().__dict__
tag = os.environ.get("FLYCNS_RUN_TAG", "")
role_line = " | ".join(f"{rl} {passed_by_role[rl]}/{counts[rl]}"
                       + (f" ({unresolved_by_role[rl]} unresolved)" if unresolved_by_role[rl] else "") for rl in
                       ["independent", "control", "robustness", "structural", "calibrated", "construction", "unclassified"] if counts[rl])
md = ["# MaleCNS v1.0 LIF benchmark suite" + (f"  [{tag}]" if tag else ""), "",
      (f"**{passed}/{total} checks pass under ONE parameter set** (same LIFParams for every circuit)."
       if canonical else
       f"**{passed}/{total} checks pass, but NOT all as registered under the declared parameter set:** see the "
       f"flags column."),
      "", f"**By role:** {role_line}",
      "", f"**Uncertainty:** {with_interval} of {total} scored checks carry a 95% interval or a per-draw or null "
          f"score (flycns/stats.py); {unresolved} are UNRESOLVED (the interval crosses a band edge) and count as not "
          f"passing. A PASS means the whole interval lies inside the band.",
      "", "Only *independent* checks test the model; *calibrated* and *construction* checks were made to pass "
          "by a declared parameter (docs/CALIBRATION.md). *control* checks show the machinery is not trivial. "
          "*structural* checks count over the wiring with no simulation.", "",
      "## Parameters", "```", json.dumps(p, indent=2), "```",
      f"effective chemical kick per synapse: {p['w_syn_mV']*p['w_scale']:.4f} mV "
      f"(Shiu 2024 unitary {p['w_syn_mV']} mV x MaleCNS rescale {p['w_scale']})", "",
      "## Checks", "| benchmark | check | result | estimate [95% interval] and band | role | flags |",
      "|---|---|---|---|---|---|"] + rows + [
      "", "Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; "
          "DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = the model code has changed since this report (unstamped: over an hour older than the newest); "
          "UNSTAMPED = written before integrity stamping, rerun to stamp; UNPINNED = no record of the input tables; "
          "ALLOW-DIRTY = run with FLYCNS_ALLOW_DIRTY=1, which waives the integrity guards; "
          "UNREGISTERED = not scored under a matching registration of the frozen model (flycns/registry.py); "
          "TRIALS a<b = run at fewer trials than the canonical b.",
      "", "Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py."]
# citation integrity: every author-year tag in code must resolve in REFERENCES.md
refs = Path("REFERENCES.md").read_text(encoding="utf-8") if Path("REFERENCES.md").exists() else ""
code = "".join(f.read_text(encoding="utf-8") for f in list(Path("flycns").glob("*.py")) + list(Path("benchmarks").glob("*.py")))
# a year inside a date (2026-10-10) is not a citation; accents are ignored (Pezier finds Pézier)
tags = set(re.findall(r"([A-Z][A-Za-zÀ-ÿ\-]+(?: et al\.| & [A-Z][A-Za-zÀ-ÿ]+)?) (19\d\d|20\d\d)(?![-\d])", code))
fold = lambda t: unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()  # noqa: E731
refs_folded = fold(refs)
missing = sorted(f"{a} {y}" for a, y in tags if fold(a.split()[0].rstrip(",")) not in refs_folded or y not in refs)
stale = [b for b, f in flags.items() if "STALE" in f]
if stale:
    md += ["", f"**WARNING: reports produced by code that has changed since: {', '.join(stale)}. "
                f"Rerun them before quoting this table.**"]
md += ["", "## Report provenance", "| benchmark | written | commit | data (neurons / edges) | env overrides |",
       "|---|---|---|---|---|"]
md += [f"| {b} | {v['written_at']} | {v['commit']} | "
       f"{' / '.join(v['data'].get(n, '-') for n in ('neurons.parquet', 'edges.parquet')) if v['data'] else '-'} | "
       f"{v['env'] or '-'} |" for b, v in sorted(stamps.items())]
md += ["", f"## Citation check: {len(tags)-len(missing)}/{len(tags)} tags resolve in REFERENCES.md"]
if missing:
    md += ["Unresolved: " + ", ".join(missing)]
# Stamp inventory: every result file (JSON, CSV, HDF5) must carry the stamp of the run that wrote it,
# in the file (a "provenance" key) or beside it (<file>.stamp.json, flycns/bench.py stamp)
EXEMPT = {"results/turner2022": "input extraction from 22 GB of Turner et al. 2022 imaging; its output is a "
                                "model input, hashed into every report's loom_input stamp"}
NOT_RESULTS = {"progress.json"}   # in-progress state; registrations (integrity.is_registration_name) are not results either


def file_stamp(f):
    if f.suffix == ".json":
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            return None
        return d.get("provenance") if isinstance(d, dict) else None
    side = f.with_name(f.name + ".stamp.json")
    return json.loads(side.read_text(encoding="utf-8")).get("provenance") if side.exists() else None


if not only:
    files = sorted(f for f in Path("results").rglob("*") if f.suffix in (".json", ".csv", ".h5")
                   and f.name not in NOT_RESULTS and not is_registration_name(f.name) and not f.name.endswith(".stamp.json")
                   and not any(f.as_posix().startswith(e + "/") for e in EXEMPT))
    unstamped, flagged, commits = [], [], Counter()
    for f in files:
        pv = file_stamp(f)
        if not pv or "git_dirty" not in pv:
            unstamped.append(f.as_posix()); continue
        commits[pv.get("git_commit", "?")] += 1
        why = [w for w, bad in (("STALE", code_changed_since(pv.get("git_commit", ""))), ("DIRTY", pv.get("git_dirty")),
                                ("DATA-MISMATCH", (pv.get("data") or {}).get("manifest") == "mismatch")) if bad]
        if why:
            flagged.append(f"{f.as_posix()} ({', '.join(why)})")
    md += ["", "## Stamp inventory",
           f"{len(files) - len(unstamped)} of {len(files)} result files carry a stamp "
           f"(commits: {', '.join(f'{c} x{n}' for c, n in commits.most_common()) or 'none'}); "
           f"{len(flagged)} flagged, {len(unstamped)} unstamped."]
    md += [f"- flagged: {x}" for x in flagged] + [f"- unstamped: {x}" for x in unstamped]
    md += [f"- exempt: {e}/ ({why})" for e, why in EXEMPT.items()]
Path("results/SUITE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
