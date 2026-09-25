"""
Audit every stimulus set the benchmarks use against the dataset, without simulating anything.

Stimulus neurons are selected by EXACT type name. MaleCNS splits many populations into
subtypes, so a name that looks right can match nothing and a run proceeds without its input
(flight_loop, commit ce8b9d2: "DNg02" matched 0 of the 29 DNg02_a..g cells). The model now
raises on a set that matches nothing and warns on a partial one; this script checks all the
sets up front, in a few seconds, so a long run never starts on a bad list.

Run:  python fit/audit_stimuli.py [data_dir]      exits non-zero if any set is empty
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.protocols import LOOM_TUNING
from flycns.graph import GUSTATORY_MN9_DRIVING, PEPTIDE_MODULATION, afferents_by_subclass

DATA = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
n = pd.read_parquet(DATA / "neurons.parquet")
types = set(n["type"].dropna())
count = n["type"].value_counts()

SETS = {
    "gf_escape / loom (LOOM_TUNING)": list(LOOM_TUNING),
    "auditory / JO auditory afferents": afferents_by_subclass(n, ["auditory"], "JO-"),
    "auditory / wind control": afferents_by_subclass(n, ["wind_gravity"], "JO-") or ["JO-FV"],
    "feeding / MN9-driving gustatory subset": list(GUSTATORY_MN9_DRIVING),
    "feeding / MN9 readout": ["MN9"],
    "peptide_asta / drive (L3, L5)": ["L3", "L5"],
    "peptide_asta / AstA source": [e["source"] for e in PEPTIDE_MODULATION],
    "peptide_asta / AstA receptor targets": [t for e in PEPTIDE_MODULATION for t in e["targets"]],
    "flight_loop / DNg02 command": sorted(n.loc[n["type"].fillna("").str.match(r"^DNg02"), "type"].unique()),
    "escape readouts": ["DNp01", "TTMn", "PSI"],
    "flight readouts": ["DNp31", "b1 MN", "DLMn c-f", "DVMn 1a-c"],
}
bad = 0
for name, lst in SETS.items():
    lst = [x for x in dict.fromkeys(lst) if x]
    hit = [x for x in lst if x in types]
    miss = [x for x in lst if x not in types]
    cells = int(sum(count.get(x, 0) for x in hit))
    if not hit:
        status, bad = "EMPTY", bad + 1
    elif miss:
        status = "PARTIAL"
    else:
        status = "ok"
    print(f"  {status:<8} {name:<42} {len(hit):>3}/{len(lst):<3} types  {cells:>6} cells"
          + (f"   missing: {miss[:6]}" if miss else ""))
print(f"\n{'ALL SETS RESOLVE' if not bad else f'{bad} EMPTY SET(S): a benchmark using them would run without its input'}")
sys.exit(1 if bad else 0)
