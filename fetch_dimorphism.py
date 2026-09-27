"""
Add sex-related annotations (dimorphism, fruitless, doublesex, synonyms) to data/neurons.parquet.

The exact property names MaleCNS uses in neuprint are not assumed. The script first lists every
property present on a sample of neurons (including male-suffixed "...m" types, where such fields are
most likely to be set), keeps those whose names mention dimorph, sex, fru, dsx or synonym, and then
fetches exactly those for every neuron. It prints what it found before writing anything.

Why: eight of the ten strongest excitatory inputs to the sine-song neuron DNp13 carry an "m"
suffix (SIP108m, PVLP204m, SIP109m, ...), and SIP108m alone drives DNp13 selectively
(benchmarks/dnp13_control.py). Whether those types are male-specific decides whether the sine
pathway is a sexually dimorphic circuit. The local data had no field to answer that.

Run:  python fetch_dimorphism.py          (needs NEUPRINT_TOKEN)   Safe to rerun.
"""
import os
import re

import pandas as pd
from neuprint import Client, fetch_custom

token = os.environ.get("NEUPRINT_TOKEN")
if not token:
    raise SystemExit('Set NEUPRINT_TOKEN first: export NEUPRINT_TOKEN=$(cat ~/.neuprint_token)')
c = Client("neuprint.janelia.org", dataset="male-cns:v1.0", token=token)

keys = set()
for where in ["", "WHERE n.type ENDS WITH 'm'", "WHERE n.type STARTS WITH 'pC1'"]:
    q = f"MATCH (n:Neuron) {where} WITH n LIMIT 3000 UNWIND keys(n) AS k RETURN DISTINCT k AS key"
    keys |= set(fetch_custom(q, client=c)["key"])
print(f"{len(keys)} distinct neuron properties seen in the sample")
pat = re.compile(r"dimorph|sex|fru|dsx|synonym", re.I)
want = sorted(k for k in keys if pat.search(k))
print("sex-related properties found:", want or "NONE")
if not want:
    print("All properties seen:", sorted(keys))
    raise SystemExit("No sex-related property found; nothing written. The list above shows what exists.")

ret = ", ".join(f"n.`{k}` AS `{k}`" for k in want)
ann = fetch_custom(f"MATCH (n:Neuron) RETURN n.bodyId AS bodyId, {ret}", client=c)
n = pd.read_parquet("data/neurons.parquet")
n = n.drop(columns=[k for k in want if k in n.columns]).merge(ann, on="bodyId", how="left")
n.to_parquet("data/neurons.parquet", index=False)
for k in want:
    vc = n[k].astype(str).replace({"None": pd.NA, "nan": pd.NA}).dropna().value_counts()
    print(f"\n{k}: {int(n[k].notna().sum()):,} neurons annotated; values: {vc.head(8).to_dict()}")

# the question that prompted this: are the song pathway types sex-specific?
song = ["SIP108m", "PVLP204m", "SIP109m", "SIP110m_a", "SIP110m_b", "AVLP713m", "PVLP214m",
        "AVLP711m", "pC1_14a", "pC1_13a", "pC1_14b", "pC1_1b", "DNp13", "pMP2", "pIP10"]
print("\nsong-pathway types:")
for t in song:
    r = n[n["type"] == t]
    if len(r):
        vals = {k: sorted({str(x) for x in r[k].dropna()}) for k in want}
        print(f"  {t:<10} {len(r)} cells  {vals}")
print("\nwrote data/neurons.parquet")
