"""
Add sensory annotations to data/neurons.parquet without refetching edges:
subclass (e.g. 'pharyngeal sensillum', 'labellar bristle', 'taste peg') and
entryNerve (e.g. 'MxLbN', 'aPhN', 'AN'). Safe to rerun.

Run:  python scripts/fetch_annotations.py
"""
import os
import pandas as pd
from neuprint import Client, fetch_custom

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.windows import neuprint_token  # noqa: E402
token = neuprint_token()
if not token:
    raise SystemExit("No neuPrint token: run setup.cmd once; it asks for the token and saves it")
c = Client("neuprint.janelia.org", dataset="male-cns:v1.0", token=token)
q = """MATCH (n:Neuron) RETURN n.bodyId AS bodyId, n.subclass AS subclass,
       n.entryNerve AS entryNerve, n.exitNerve AS exitNerve"""
ann = fetch_custom(q, client=c)
n = pd.read_parquet("data/neurons.parquet")
for col in ["subclass", "entryNerve", "exitNerve"]:
    if col in n:
        n = n.drop(columns=col)
n = n.merge(ann, on="bodyId", how="left")
n.to_parquet("data/neurons.parquet", index=False)
print("annotated:", n.subclass.notna().sum(), "with subclass;", n.entryNerve.notna().sum(), "with entryNerve")
print(n.subclass.value_counts().head(20))
