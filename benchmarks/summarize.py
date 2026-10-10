"""Collect every results/*/report.json into results/SUITE.md with one parameter set declared.

Every check is shown with its ROLE (flycns/calibration.py): only checks that were not a target of
any fit count as tests of the model. Reports are flagged when they were produced under settings
overrides (a robustness perturbation, not the declared parameter set), on uncommitted code, on
data that do not match data/MANIFEST.json, or more than an hour before the newest report."""
import json, os, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import LIFParams
from flycns.calibration import role
from flycns.integrity import PLUMBING

rows, stamps, flags = [], {}, {}
counts, passed_by_role = Counter(), Counter()
reports = sorted(Path("results").glob("*/report.json"))
mtimes = {rep: rep.stat().st_mtime for rep in reports}
newest = max(mtimes.values()) if mtimes else 0
for rep in reports:
    r = json.loads(rep.read_text())
    name = r.get("benchmark", rep.parent.name)
    prov = r.get("provenance", {})
    model_env = {k: v for k, v in (prov.get("env") or {}).items() if k not in PLUMBING}
    f = []
    if model_env:
        f.append("PERTURBED")
    if prov.get("git_dirty"):
        f.append("DIRTY")
    if (prov.get("data") or {}).get("manifest") == "mismatch":
        f.append("DATA-MISMATCH")
    if newest - mtimes[rep] > 3600:
        f.append("STALE")
    if not prov or "git_dirty" not in prov:
        f.append("UNSTAMPED")   # written before integrity stamping (2026-10-10); rerun to stamp
    flags[name] = f
    stamps[name] = dict(written_at=prov.get("written_at", "unstamped"), commit=prov.get("git_commit", ""),
                        env=model_env, data=((prov.get("data") or {}).get("digests") or {}))
    for k, v in r.get("checks", {}).items():
        rl, why = role(name, k) if v is not None else ("reported", "reported, not scored")
        if v is not None:
            counts[rl] += 1
            passed_by_role[rl] += bool(v)
        res = "SKIP" if v is None else ("PASS" if v else "FAIL")
        rows.append(f"| {name} | {k} | {res} | {rl} | {', '.join(f) or '-'} |")

total, passed = sum(counts.values()), sum(passed_by_role.values())
canonical = not any(("PERTURBED" in f or "DIRTY" in f or "DATA-MISMATCH" in f) for f in flags.values())
p = LIFParams().__dict__
tag = os.environ.get("FLYCNS_RUN_TAG", "")
role_line = " | ".join(f"{rl} {passed_by_role[rl]}/{counts[rl]}" for rl in
                       ["independent", "control", "robustness", "calibrated", "construction", "unclassified"] if counts[rl])
md = ["# MaleCNS v1.0 LIF benchmark suite" + (f"  [{tag}]" if tag else ""), "",
      (f"**{passed}/{total} checks pass under ONE parameter set** (same LIFParams for every circuit)."
       if canonical else
       f"**{passed}/{total} checks pass, but NOT all under the declared parameter set:** see the flags column."),
      "", f"**By role:** {role_line}",
      "", "Only *independent* checks test the model; *calibrated* and *construction* checks were made to pass "
          "by a declared parameter (docs/CALIBRATION.md). *control* checks show the machinery is not trivial.", "",
      "## Parameters", "```", json.dumps(p, indent=2), "```",
      f"effective chemical kick per synapse: {p['w_syn_mV']*p['w_scale']:.4f} mV "
      f"(Shiu 2024 unitary {p['w_syn_mV']} mV x MaleCNS rescale {p['w_scale']})", "",
      "## Checks", "| benchmark | check | result | role | flags |", "|---|---|---|---|---|"] + rows + [
      "", "Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; "
          "DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = over an hour older than the newest report; "
          "UNSTAMPED = written before integrity stamping, rerun to stamp.",
      "", "Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py."]
# citation integrity: every author-year tag in code must resolve in REFERENCES.md
refs = Path("REFERENCES.md").read_text() if Path("REFERENCES.md").exists() else ""
code = "".join(f.read_text() for f in list(Path("flycns").glob("*.py")) + list(Path("benchmarks").glob("*.py")))
tags = set(re.findall(r"([A-Z][A-Za-zé\-]+(?: et al\.| & [A-Z][A-Za-z]+)?) (19\d\d|20\d\d)", code))
missing = sorted(f"{a} {y}" for a, y in tags if a.split()[0].rstrip(",") not in refs or y not in refs)
stale = [b for b, f in flags.items() if "STALE" in f]
if stale:
    md += ["", f"**WARNING: reports more than an hour older than the newest are included: "
                f"{', '.join(stale)}. Rerun the suite (`scripts/run_all.sh`) before quoting this table.**"]
md += ["", "## Report provenance", "| benchmark | written | commit | data (neurons / edges) | env overrides |",
       "|---|---|---|---|---|"]
md += [f"| {b} | {v['written_at']} | {v['commit']} | "
       f"{' / '.join(v['data'].get(n, '-') for n in ('neurons.parquet', 'edges.parquet')) if v['data'] else '-'} | "
       f"{v['env'] or '-'} |" for b, v in sorted(stamps.items())]
md += ["", f"## Citation check: {len(tags)-len(missing)}/{len(tags)} tags resolve in REFERENCES.md"]
if missing:
    md += ["Unresolved: " + ", ".join(missing)]
Path("results/SUITE.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
