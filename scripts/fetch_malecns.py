"""
Phase 0: pull the MaleCNS v1.0 graph from neuprint and cache it locally.

Run once:  python scripts/fetch_malecns.py
Outputs:   data/neurons.parquet   one row per neuron
           data/edges.parquet     one row per (pre, post) pair, weight >= MIN_WEIGHT

Requires:  a neuPrint token (setup.cmd asks for it once and saves it)
"""

import time
from pathlib import Path

import pandas as pd
from neuprint import Client, fetch_custom

# ---------------------------------------------------------------- settings
DATASET = "male-cns:v1.0"
MIN_WEIGHT = 5          # drop pre->post pairs with fewer than this many synapses
BATCH = 2000            # source neurons per edge query; lower if queries time out
OUT = Path("data")
OUT.mkdir(exist_ok=True)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.windows import neuprint_token  # noqa: E402
token = neuprint_token()
if not token:
    raise SystemExit("No neuPrint token: run setup.cmd once; it asks for the token and saves it")

client = Client("neuprint.janelia.org", dataset=DATASET, token=token)
print("connected to", DATASET)

# ---------------------------------------------------------------- neurons
# Cypher returns null for properties a neuron lacks, so missing fields
# will not crash the query. We ask for every field we might want and
# inspect what actually comes back.
neuron_query = """
MATCH (n:Neuron)
RETURN n.bodyId        AS bodyId,
       n.type          AS type,
       n.instance      AS instance,
       n.status        AS status,
       n.predictedNt   AS predictedNt,
       n.consensusNt   AS consensusNt,
       n.somaLocation  AS somaLocation,
       n.somaSide      AS somaSide,
       n.superclass    AS superclass,
       n.pre           AS pre,
       n.post          AS post
"""
t0 = time.time()
neurons = fetch_custom(neuron_query, client=client)
print(f"neurons: {len(neurons):,} rows in {time.time()-t0:.0f}s")
print("columns present:", list(neurons.columns))
print("non-null counts:\n", neurons.notna().sum())

# somaLocation arrives as a dict like {'coordinates': [x, y, z]}; flatten it
def _xyz(v):
    if isinstance(v, dict) and "coordinates" in v:
        return v["coordinates"]
    return [None, None, None]

xyz = neurons["somaLocation"].apply(_xyz).tolist()
neurons[["x", "y", "z"]] = pd.DataFrame(xyz, index=neurons.index)
neurons = neurons.drop(columns=["somaLocation"])
# preserve annotation columns from a previous fetch_annotations.py run
_old = OUT / "neurons.parquet"
if _old.exists():
    prev = pd.read_parquet(_old)
    # annotation columns added by fetch_annotations.py and fetch_dimorphism.py (any sex-related field)
    keep = [c for c in prev.columns if c in ("subclass", "entryNerve", "exitNerve")
            or any(k in c.lower() for k in ("dimorph", "sex", "fru", "dsx", "synonym"))]
    if keep:
        neurons = neurons.merge(prev[["bodyId"] + keep], on="bodyId", how="left")
        print("preserved annotation columns:", keep)
neurons.to_parquet(OUT / "neurons.parquet", index=False)
print("wrote", OUT / "neurons.parquet")

# ---------------------------------------------------------------- edges
# One query for 125M synapses will time out, so batch by source bodyId.
edge_query = """
MATCH (a:Neuron)-[c:ConnectsTo]->(b:Neuron)
WHERE a.bodyId IN {ids} AND c.weight >= {minw}
RETURN a.bodyId AS pre, b.bodyId AS post, c.weight AS weight
"""
ids = neurons["bodyId"].tolist()
chunks = []
t0 = time.time()
for i in range(0, len(ids), BATCH):
    batch_ids = ids[i:i + BATCH]
    q = edge_query.format(ids=batch_ids, minw=MIN_WEIGHT)
    df = fetch_custom(q, client=client)
    chunks.append(df)
    done = min(i + BATCH, len(ids))
    print(f"  edges: {done:>7,}/{len(ids):,} sources, "
          f"{sum(len(c) for c in chunks):,} pairs, {time.time()-t0:.0f}s")

edges = pd.concat(chunks, ignore_index=True)

# ---------------------------------------------------------------- transmitter of each edge
# Each edge carries its sender's transmitter: consensusNt, else predictedNt, else unknown. No sign is
# written: there is ONE transmitter-to-sign table, flycns/graph.py SIGN_MAP, applied by load_graph
# (histamine included). Until generation 4 (October 2026) the fetch also wrote a legacy `sign` column
# from its own three-entry table, which nothing read; it was dropped at the generation-4 data re-pin.
from flycns.graph import SIGN_MAP  # noqa: E402
nt = neurons.set_index("bodyId")
nt_col = nt["consensusNt"].fillna(nt["predictedNt"]).str.lower()
edges["nt"] = edges["pre"].map(nt_col)

n_total = len(edges)
_sign = edges["nt"].map(SIGN_MAP)
n_unknown = (_sign.isna() | (_sign == 0)).sum()
print(f"\nedge pairs total:   {n_total:,}")
print(f"unsigned (unknown or modulatory transmitter, dropped by load_graph): {n_unknown:,} ({100*n_unknown/n_total:.1f}%)")
print("NT breakdown:\n", edges["nt"].value_counts(dropna=False))

edges.to_parquet(OUT / "edges.parquet", index=False)
print("wrote", OUT / "edges.parquet")
