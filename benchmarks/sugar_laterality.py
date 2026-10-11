"""
Does unilateral labellar sugar input favour the contralateral MN9? (Shiu et al. 2024)

Shiu et al. 2024 (Nature 634:210-219) predicted that activating labellar sugar GRNs on one side
drives the contralateral MN9 more strongly than the ipsilateral one. This project recorded that
test as "not applicable" because MaleCNS had no labellar sugar annotation. The companion gustatory
paper (Tastekin, de Haan Vicente et al. 2026, Cell 189:5527-5551, Fig. 2) now identifies LB3b and
LB3c as the sugar-sensing labellar types, so the prediction can be tested structurally. A dynamic
test is not informative here: MN9 does not fire to sugar in this model at all.

Sides. Only EXPLICIT sides are used: the annotated somaSide, else the MaleCNS instance suffix
(_L/_R). The generic side fallback guesses from soma position without checking orientation, so it
is deliberately not used; cells without an explicit side are excluded and counted.

Measure. Input-normalised path products (as in benchmarks/gustatory_signed_map.py), cumulative
over hops 1..5, from each side's afferents onto the left and right MN9 cells separately.

CRITERION (registered after the side sets resolve, before anything is computed):
  L1  for sugar (LB3b + LB3c), on BOTH sides: cumulative SIGNED influence on the contralateral MN9
      and on the ipsilateral MN9 are both positive, and contralateral >= 1.10 x ipsilateral. The 10%
      margin exists because without one, near-equal values are decided by differences in the fifth
      significant figure, which is noise, not a bias.
Reported: the same unsigned; bitter (LB1a-d); the old mixed proxy, which earlier showed a strong
ipsilateral bias; and the hop at which each side's bias first appears.

Run:  python benchmarks/sugar_laterality.py [data_dir]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import load_graph
from flycns.bench import provenance
from flycns.graph import GUSTATORY_MN9_DRIVING
from flycns import stats

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = Path("results/sugar_laterality")
OUT.mkdir(parents=True, exist_ok=True)
N_HOPS, CUM = 6, 5
GROUPS = {"sugar": ["LB3b", "LB3c"], "bitter": ["LB1a", "LB1b", "LB1c", "LB1d"],
          "old_mixed_proxy": list(GUSTATORY_MN9_DRIVING)}

# Version 2 registration (flycns/registry.py): criteria plus the frozen model, written before any data is loaded;
# it supersedes the version 1 criteria.json below, which is kept and still checked. L1 is graph arithmetic scored
# on its point value, so its rule is stated in words with its threshold, not as a band.
from flycns import registry  # noqa: E402
_v1 = OUT / "criteria.json"
CRITERIA_V2 = dict(
    version=2,
    question=("does unilateral labellar sugar input (LB3b, LB3c) favour the contralateral MN9, as Shiu et al. 2024 "
              "predicted?"),
    source=("Shiu et al. 2024 Nature 634:210-219 (prediction); Tastekin et al. 2026 Cell 189:5527-5551 "
            "(LB3b, LB3c sugar)"),
    groups=GROUPS, sides="explicit only (somaSide, else _L/_R instance suffix); cells without one are excluded",
    measure=dict(kind=("input-normalised signed path products from each side's afferents onto the left and the right "
                       "MN9 cells separately (the model's edge signs)"), hops=N_HOPS, cumulative_hops=CUM),
    checks=dict(
        L1_sugar_contralateral_bias=dict(
            threshold=1.10,
            rule=("point record: for the left and for the right sugar afferents separately, cumulative signed "
                  "influence on the contralateral and on the ipsilateral MN9 are both above 0 and contralateral >= "
                  "1.10 x ipsilateral; PASS only if both sides do")),
    ),
    reported="the same unsigned; bitter (LB1a-d); the old mixed proxy; the hop at which each side's bias first appears",
)
REG = registry.register("sugar_laterality", CRITERIA_V2, scripts=[__file__],
                        supersedes=dict(file="criteria.json", git_commit=(
                            json.loads(_v1.read_text(encoding="utf-8")).get("git_commit") if _v1.exists() else None)))

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
explicit = meta["somaSide"].where(meta["somaSide"].isin(["L", "R"]))
if "instance" in meta:
    suf = meta["instance"].fillna("").str.extract(r"_([LR])$")[0]
    explicit = explicit.where(explicit.isin(["L", "R"]), suf)

mn9 = meta.index[meta["type"] == "MN9"]
mn9_side = explicit.reindex(mn9)
if set(mn9_side.dropna()) != {"L", "R"}:
    raise SystemExit(f"ABORT before registration: MN9 cells lack explicit L and R sides: {mn9_side.to_dict()}")
sets = {}
for g, tl in GROUPS.items():
    ids = meta.index[meta["type"].isin(tl)]
    sd = explicit.reindex(ids)
    sets[g] = dict(L=list(sd.index[sd == "L"]), R=list(sd.index[sd == "R"]),
                   excluded=int(sd.isna().sum()), n=int(len(ids)))
    print(f"  {g:<16} {len(ids):>4} cells | L {len(sets[g]['L']):>3} R {len(sets[g]['R']):>3} | "
          f"no explicit side (excluded) {sets[g]['excluded']}")
if not (sets["sugar"]["L"] and sets["sugar"]["R"]):
    raise SystemExit("ABORT before registration: sugar afferents lack explicit sides on one or both sides")

CRITERIA = dict(
    source="Shiu et al. 2024 Nature 634:210-219 (prediction); Tastekin et al. 2026 Cell 189:5527-5551 (LB3b, LB3c sugar)",
    L1="sugar, both sides: contra > 0, ipsi > 0, contra >= 1.10 x ipsi (cumulative signed, hops 1-5)",
    margin=1.10,
    sides="explicit only (somaSide, else _L/_R instance suffix)", groups=GROUPS)
# Registered test: refuse uncommitted code and data that differ from data/MANIFEST.json, so the
# registered result can be traced to an exact commit and an exact dataset (flycns/integrity.py).
from flycns.integrity import require_clean, require_data, criteria_differ  # noqa: E402
require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem)   # every table pinned in the manifest, rehashed
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/sugar_laterality.py"],
                                capture_output=True, text=True, timeout=5).stdout.strip())
except Exception:
    commit, dirty = "", True
if crit_f.exists():
    if criteria_differ(crit_f, CRITERIA):
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test.")
else:
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=commit, script_uncommitted=dirty), indent=2), encoding="utf-8")
reg = json.loads(crit_f.read_text(encoding="utf-8")).get("git_commit") or "?"
print(f"criteria registered at commit {reg}; this run at {commit or '?'}{' (SCRIPT UNCOMMITTED: commit before running)' if dirty else ''}")

e = edges.copy()
e["sgn"] = e["sign"]   # the signs the dynamic model uses, including any FLYCNS_SIGNFLIP perturbation
ids_all = pd.Index(sorted(set(e.pre) | set(e.post)))
pos = pd.Series(np.arange(len(ids_all)), index=ids_all)


def normalised(vals):
    W = csr_matrix((e.weight.values * vals, (pos[e.pre].values, pos[e.post].values)),
                   shape=(len(ids_all), len(ids_all)))
    return W.multiply(1.0 / np.maximum(np.asarray(np.abs(W).sum(axis=0)).ravel(), 1.0)).tocsr()


Ws = normalised(e["sgn"].values)
Wu = normalised((e["sgn"].values != 0).astype(float))
mnL = pos[[b for b in mn9 if mn9_side[b] == "L" and b in pos.index]].values
mnR = pos[[b for b in mn9 if mn9_side[b] == "R" and b in pos.index]].values


def onto_sides(W, src):
    src = [b for b in src if b in pos.index]
    v = np.zeros(len(ids_all)); v[pos[src].values] = 1.0
    L, R = [], []
    for _ in range(N_HOPS):
        v = np.asarray(W.T.dot(v)).ravel()
        L.append(float(v[mnL].sum())); R.append(float(v[mnR].sum()))
    return dict(onto_MN9_L=L, onto_MN9_R=R, cum_L=float(sum(L[:CUM])), cum_R=float(sum(R[:CUM])))


res = {}
print("\ncumulative influence on MN9 (hops 1-5)          ipsi          contra     bias")
for g in GROUPS:
    res[g] = {}
    for kind, W in (("signed", Ws), ("unsigned", Wu)):
        for side in ("L", "R"):
            r = onto_sides(W, sets[g][side])
            ipsi = r["cum_L"] if side == "L" else r["cum_R"]
            contra = r["cum_R"] if side == "L" else r["cum_L"]
            first = next((h + 1 for h in range(N_HOPS)
                          if abs((r["onto_MN9_R"][h] if side == "L" else r["onto_MN9_L"][h])
                                 - (r["onto_MN9_L"][h] if side == "L" else r["onto_MN9_R"][h])) > 1e-9), None)
            ratio = contra / ipsi if ipsi > 0 and contra > 0 else None
            r.update(ipsi=ipsi, contra=contra, contra_over_ipsi=ratio,
                     contralateral=bool(ratio is not None and ratio >= 1.10), first_hop_with_difference=first)
            res[g][f"{kind}_{side}"] = r
            label = (f"contra/ipsi {ratio:.2f}" if ratio is not None else "not both positive")
            print(f"  {g:<16} {kind:<8} {side} afferents   {ipsi:+.3e}   {contra:+.3e}   {label}"
                  f"{'  CONTRALATERAL' if r['contralateral'] else ''}")

s = res["sugar"]
l1 = bool(s["signed_L"]["contralateral"] and s["signed_R"]["contralateral"])
report = dict(benchmark="sugar_laterality", criteria=CRITERIA, sets={g: {k: (len(v) if isinstance(v, list) else v)
                                                                          for k, v in d.items()} for g, d in sets.items()},
              results=res, checks={"L1_sugar_contralateral_bias": l1}, provenance=provenance())
# ---- uncertainty (flycns/stats.py): graph arithmetic, no sampling, so the check is scored on its point value
_ratios = [s["signed_L"]["contra_over_ipsi"], s["signed_R"]["contra_over_ipsi"]]
report["uncertainty"] = {"L1_sugar_contralateral_bias": stats.point(
    min(_ratios) if None not in _ratios else None, l1,
    note="graph arithmetic over the fixed connectome (signed path products from explicitly sided afferents), no "
         "simulation and no random draws; estimate is the smaller contra/ipsi ratio of the two sides (needs >= 1.10 "
         f"with both positive): L afferents {_ratios[0]}, R afferents {_ratios[1]}")}
registry.verify_bands(REG, report["uncertainty"])
report["registration"] = registry.stamp(REG)
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print("\nCHECK (criterion registered before the run)")
print(f"  {'PASS' if l1 else 'FAIL'}  L1_sugar_contralateral_bias")
_u = report["uncertainty"]["L1_sugar_contralateral_bias"]
print(f"UNCERTAINTY (flycns/stats.py): {_u['verdict']}  L1_sugar_contralateral_bias: {_u['estimate']} ({_u['method']}; "
      "graph arithmetic, no sampling)")
print(f"wrote {OUT / 'report.json'}")
