"""Temporary (not for merge): fingerprint the PINNED tables with the legacy `sign` column dropped, to
compare with the generation-4 re-pin, which has no such column. Equal digests mean every other column of
every row is identical."""
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns.integrity import table_fingerprint  # noqa: E402

out = {}
for name in ("edges.parquet", "edges_nt.parquet"):
    df = pd.read_parquet(Path("data") / name)
    had = "sign" in df.columns
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / name
        df.drop(columns=["sign"], errors="ignore").to_parquet(p, index=False)
        fp = table_fingerprint(p)
    out[name] = dict(had_sign=had, digest_without_sign=fp["digest"], rows=fp["rows"], columns=fp["columns"], sums=fp["sums"])
    print(name, had, fp["digest"], fp["rows"])
Path("results/checks").mkdir(parents=True, exist_ok=True)
Path("results/checks/repin_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
