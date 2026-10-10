"""
Audit every stimulus set the benchmarks use against the dataset, without simulating anything.

Stimulus neurons are selected by EXACT type name. MaleCNS splits many populations into
subtypes, so a name that looks right can match nothing and a run proceeds without its input
(flight_loop, commit ce8b9d2: "DNg02" matched 0 of the 29 DNg02_a..g cells). The model now
raises on a set that matches nothing and warns on a partial one; this script checks all the
sets up front, in a few seconds, so a long run never starts on a bad list.

Run:  python fit/audit_stimuli.py [data_dir]      exits non-zero if any set is empty
"""
import os
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.protocols import LOOM_TUNING
from flycns.graph import ELECTRICAL_SYNAPSES, GUSTATORY_MN9_DRIVING, PEPTIDE_MODULATION, afferents_by_subclass

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
    "declared electrical synapses (both ends)": [x for e in ELECTRICAL_SYNAPSES for x in e[:2]],
    "pc1_song / scored pC1 groups": ["pC1_14a", "pC1_13a", "pC1_14b", "pC1_15a", "pC1_15b", "pC1_15c"]
                                    + sorted(x for x in types if str(x).startswith("pC1_16")),
    "pc1_song, dnp13_control / song readouts": ["pMP2", "DNp13", "pIP10", "pC1_1b"],
    "taste benchmarks / labellar types": ["LB3a", "LB3b", "LB3c", "LB3d", "LB1a", "LB1b", "LB1c", "LB1d",
                                          "LB2a", "LB2b", "LB2c"],
    "taste benchmarks / feeding motor neurons": ["MN9", "MN6", "MN11D", "MN11V"],
    "flight_snpp16* / wing campaniform types": [os.environ.get("FLYCNS_TARGET_TYPE", "SNpp16"),
                                                os.environ.get("FLYCNS_PARTNER_TYPE", "SNpp07")],
}
bad = 0
for name, members in SETS.items():
    lst = [x for x in dict.fromkeys(members) if x and not str(x).endswith("*")]
    hit = [x for x in lst if x in types]
    miss = [x for x in lst if x not in types]
    cells = int(sum(count.get(x, 0) for x in hit))
    if not hit:
        status, bad = "EMPTY", bad + 1
    elif miss:
        status = "PARTIAL"
    else:
        status = "ok"
    print(f"  {status:<8} {name:<44} {len(hit):>3}/{len(lst):<3} types  {cells:>6} cells"
          + (f"   missing: {miss[:6]}" if miss else ""))
print(f"\n{'ALL SETS RESOLVE' if not bad else f'{bad} EMPTY SET(S): a benchmark using them would run without its input'}")
sys.exit(1 if bad else 0)
