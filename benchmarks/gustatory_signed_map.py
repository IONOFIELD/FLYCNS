"""
A SIGNED sensory-to-motor influence map for the gustatory system of MaleCNS.

Tastekin, de Haan Vicente et al. 2026 (Cell 189:5527-5551) computed effective connectivity from
every gustatory receptor neuron (GRN) type to the feeding motor neurons and state that their metric
"does not incorporate synaptic sign", so predicted influences may be over- or underestimated. This
script computes the same kind of map WITH sign, on the same graph, beside an unsigned version built
identically, so the two can be compared type by type. It is deterministic (no simulation).

Measure. Input-normalised path products (as in benchmarks/feeding_mechanism.py): each neuron's
incoming weights are divided by its total absolute input, and a unit vector on a GRN type is
propagated 1..6 hops. SIGNED uses transmitter signs (ACh +1; GABA, Glu, His -1; amines 0);
UNSIGNED uses |weight| with the same normalisation. Influence on a motor neuron type is the summed
value on its cells; the cumulative value over hops 1..5 is the headline number.

Counterfactual. MaleCNS classifies LB3d as cholinergic; the companion paper matches it to
glutamatergic driver lines. The map is recomputed with LB3d's outgoing sign set to -1.

CRITERIA (registered after every named type is confirmed present, before anything is computed):
  S1  on proboscis-extension MNs (MN9 + MN6), mean cumulative signed influence of the appetitive
      labellar types (LB3a, LB3b, LB3c) is > 0, AND the bitter types' (LB1a-d) mean is below it
  S2  at least 5 of those 7 types have cumulative signed influence on MN9 whose sign matches
      valence (appetitive > 0, bitter < 0)
  S3  LB2 (LB2a-d pooled) has the largest absolute cumulative signed influence of any labellar
      group (LB1a-d, LB1e, LB2, LB3a-c, LB3d, LB4) on pharyngeal pumping (MN11D + MN11V)
Reported, not scored: the full signed and unsigned tables; how often sign disagrees with the
unsigned ranking; the LB3d counterfactual; optional MNs (MN4a, MN8, CEM) if present.

Run:  python benchmarks/gustatory_signed_map.py [data_dir]
Writes results/gustatory_signed_map/{criteria.json, signed.csv, unsigned.csv, report.json}
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
from flycns.graph import SIGN_MAP, GUSTATORY_SUBCLASSES

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = Path("results/gustatory_signed_map")
OUT.mkdir(parents=True, exist_ok=True)
N_HOPS, CUM_HOPS = 6, 5

REQUIRED_MN = ["MN9", "MN6", "MN11D", "MN11V"]
OPTIONAL_MN = ["MN4a", "MN4b", "MN8", "MN10", "MN7", "CEM"]
APPETITIVE = ["LB3a", "LB3b", "LB3c"]
BITTER = ["LB1a", "LB1b", "LB1c", "LB1d"]
LABELLAR_GROUPS = {"LB1a-d": BITTER, "LB1e": ["LB1e"], "LB2": ["LB2a", "LB2b", "LB2c", "LB2d"],
                   "LB3a-c": APPETITIVE, "LB3d": ["LB3d"], "LB4": ["LB4a", "LB4b"]}
PROBOSCIS = ["MN9", "MN6"]
INGESTION = ["MN11D", "MN11V"]

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
types = set(meta["type"].dropna())

# ---- resolve every named type BEFORE registering
must = REQUIRED_MN + APPETITIVE + BITTER + ["LB2a", "LB2b", "LB2c"]
missing = [x for x in must if x not in types]
if missing:
    near = sorted({x for x in types if any(str(x).startswith(m[:3]) for m in missing)})[:20]
    raise SystemExit(f"ABORT before registration: required types missing {missing}. Near names: {near}")
optional_present = [x for x in OPTIONAL_MN if x in types]
grn_types = sorted(meta.loc[meta["subclass"].isin(GUSTATORY_SUBCLASSES), "type"].dropna().unique())
extra = sorted({x for x in types if str(x).startswith(("LgAG", "LgLG", "WG"))})
grn_types = sorted(set(grn_types) | set(extra))
mn_types = REQUIRED_MN + optional_present
print(f"GRN types: {len(grn_types)} | motor neuron types: {mn_types}")

CRITERIA = dict(
    source="Tastekin, de Haan Vicente et al. 2026, Cell 189:5527-5551 (valence assignments; their map is unsigned)",
    measure=f"input-normalised signed path products, cumulative over hops 1..{CUM_HOPS}",
    S1="proboscis (MN9+MN6): mean cumulative signed of LB3a-c > 0 AND mean of LB1a-d below it",
    S2="at least 5 of LB3a-c, LB1a-d have cumulative signed influence on MN9 with sign matching valence",
    S3="LB2 has the largest |cumulative signed| on MN11D+MN11V among labellar groups",
    groups=LABELLAR_GROUPS, required_mn=REQUIRED_MN)
crit_f = OUT / "criteria.json"
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "benchmarks/gustatory_signed_map.py"],
                                capture_output=True, text=True, timeout=5).stdout.strip())
except Exception:
    commit, dirty = "", True
if crit_f.exists():
    if json.loads(crit_f.read_text()).get("criteria") != CRITERIA:
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered test.")
else:
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=commit, script_uncommitted=dirty), indent=2))
print(f"criteria registered at commit {commit or '?'}{' (SCRIPT UNCOMMITTED: commit before running)' if dirty else ''}")

# ---- matrices
e = edges.copy()
e["sgn"] = e["nt"].str.lower().map(SIGN_MAP).fillna(0.0)
ids = pd.Index(sorted(set(e.pre) | set(e.post)))
pos = pd.Series(np.arange(len(ids)), index=ids)


def normalised(sign_vals):
    w = e.weight.values * sign_vals
    W = csr_matrix((w, (pos[e.pre].values, pos[e.post].values)), shape=(len(ids), len(ids)))
    denom = np.maximum(np.asarray(np.abs(W).sum(axis=0)).ravel(), 1.0)
    return W.multiply(1.0 / denom).tocsr()


Ws = normalised(e["sgn"].values)
Wu = normalised(np.abs(e["sgn"].values) + (e["sgn"].values == 0))       # unsigned: every connection +1
lb3d_ids = set(meta.index[meta["type"] == "LB3d"])
sgn_cf = np.where(e["pre"].isin(lb3d_ids).values, -1.0, e["sgn"].values)
Wcf = normalised(sgn_cf)
mn_pos = {m: pos[[b for b in meta.index[meta["type"] == m] if b in pos.index]].values for m in mn_types}


def influence(W, src_types):
    src = [b for b in meta.index[meta["type"].isin(src_types)] if b in pos.index]
    v = np.zeros(len(ids)); v[pos[src].values] = 1.0
    per_hop = {m: [] for m in mn_types}
    for _ in range(N_HOPS):
        v = np.asarray(W.T.dot(v)).ravel()
        for m in mn_types:
            per_hop[m].append(float(v[mn_pos[m]].sum()))
    return {m: dict(per_hop=h, cumulative=float(sum(h[:CUM_HOPS]))) for m, h in per_hop.items()}


t0 = time.time()
signed, unsigned = {}, {}
for g in grn_types:
    signed[g] = influence(Ws, [g]); unsigned[g] = influence(Wu, [g])
group_cells = {k: int(meta["type"].isin(v).sum()) for k, v in LABELLAR_GROUPS.items()}
empty = [k for k, c in group_cells.items() if c == 0]
print("labellar group sizes: " + ", ".join(f"{k} {c}" for k, c in group_cells.items())
      + (f"  | EMPTY (reported as missing, not zero): {empty}" if empty else ""))
groups_signed = {k: influence(Ws, v) for k, v in LABELLAR_GROUPS.items()}
groups_cf = {k: influence(Wcf, v) for k, v in LABELLAR_GROUPS.items()}
print(f"propagated {len(grn_types)} GRN types and {len(LABELLAR_GROUPS)} groups in {round(time.time() - t0)}s")

cum = lambda d, ms: float(np.mean([d[m]["cumulative"] for m in ms]))
tab_s = pd.DataFrame({g: {m: signed[g][m]["cumulative"] for m in mn_types} for g in grn_types}).T
tab_u = pd.DataFrame({g: {m: unsigned[g][m]["cumulative"] for m in mn_types} for g in grn_types}).T
tab_s.to_csv(OUT / "signed.csv"); tab_u.to_csv(OUT / "unsigned.csv")

app = np.mean([cum(signed[t], PROBOSCIS) for t in APPETITIVE])
bit = np.mean([cum(signed[t], PROBOSCIS) for t in BITTER])
s1 = bool(app > 0 and bit < app)
agree = sum(signed[t]["MN9"]["cumulative"] > 0 for t in APPETITIVE) + sum(signed[t]["MN9"]["cumulative"] < 0 for t in BITTER)
s2 = bool(agree >= 5)
ing = {k: abs(cum(v, INGESTION)) for k, v in groups_signed.items() if k not in empty}
s3 = bool(max(ing, key=ing.get) == "LB2")

# sign disagreement with the unsigned picture: among the strongest unsigned influences on MN9,
# how many are net inhibitory once sign is included
top_u = tab_u["MN9"].sort_values(ascending=False).head(15).index
neg_among_top = [g for g in top_u if tab_s.loc[g, "MN9"] < 0]
report = dict(benchmark="gustatory_signed_map", criteria=CRITERIA, n_grn_types=len(grn_types),
              motor_neurons=mn_types,
              S1=dict(appetitive_mean=app, bitter_mean=bit), S2=dict(n_agree=int(agree), of=7),
              S3=dict(abs_ingestion_by_group=ing), group_cells=group_cells, empty_groups=empty,
              checks={"S1_valence_signed_on_proboscis": s1, "S2_per_type_sign_agreement": s2,
                      "S3_LB2_dominates_pharyngeal_pumping": s3},
              reported=dict(
                  top15_unsigned_on_MN9=list(top_u), net_inhibitory_among_them=neg_among_top,
                  groups_signed={k: {m: v[m]["cumulative"] for m in mn_types} for k, v in groups_signed.items()},
                  lb3d_counterfactual={k: {m: groups_cf[k][m]["cumulative"] for m in mn_types} for k in groups_cf},
                  lb3d_effect_on_proboscis=dict(declared=cum(groups_signed["LB3d"], PROBOSCIS),
                                                as_glutamatergic=cum(groups_cf["LB3d"], PROBOSCIS))))
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))

pd.set_option("display.width", 160)
print("\nlabellar groups, cumulative SIGNED influence (hops 1-5):")
print(pd.DataFrame(report["reported"]["groups_signed"]).T.map(lambda x: f"{x:+.2e}").to_string())
print(f"\nS1 appetitive mean on MN9+MN6 {app:+.3e} | bitter {bit:+.3e}")
print(f"S2 sign agreement on MN9: {agree}/7")
print("S3 |signed| on MN11D+MN11V: " + ", ".join(f"{k} {v:.2e}" for k, v in sorted(ing.items(), key=lambda x: -x[1])))
print(f"\nof the 15 strongest UNSIGNED influences on MN9, net inhibitory with sign: {len(neg_among_top)} {neg_among_top[:8]}")
lb = report["reported"]["lb3d_effect_on_proboscis"]
print(f"LB3d on proboscis MNs: declared (ACh) {lb['declared']:+.3e} -> as glutamatergic {lb['as_glutamatergic']:+.3e}")
print("\nCHECKS (criteria registered before the run)")
for k, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"wrote {OUT}/signed.csv, unsigned.csv, report.json")
