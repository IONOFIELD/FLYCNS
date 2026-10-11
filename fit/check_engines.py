"""
Do the compiled and the pure-Python engines give the same spikes on the REAL connectome?

tests/unit.py checks this on the toy graph. The toy has 900 neurons; the connectome has 170,000, and
a difference in floating-point evaluation order would show up there first. Both engines run the
escape protocol at the declared parameters on the same data, and every spike (time and cell) must be
identical: exact equality, not a tolerance.

Writes results/checks/engines_real.json (stamped): spike counts, a hash of each engine's spike table,
and the first differing spike if any. Exits non-zero if the engines differ.

Run:  python fit/check_engines.py [n_trials] [data_dir]      (10 trials; needs the C++ compiler,
                                                              so the compiled engine exists)
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import CNSModel, LIFParams, load_graph, loom_protocol  # noqa: E402
from flycns.bench import provenance  # noqa: E402
from flycns.protocols import LOOM_TUNING  # noqa: E402
from flycns.windows import codegen_target  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else 10
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/checks"); OUT.mkdir(parents=True, exist_ok=True)

if codegen_target() != "cython":
    raise SystemExit("the compiled engine is not available on this machine (no C++ compiler): nothing to compare")
neurons, edges = load_graph(DATA)
frames, hashes = {}, {}
for eng in ("cython", "numpy"):
    print(f"running {N} looms on the {eng} engine ...", flush=True)
    m = CNSModel(neurons, edges, list(LOOM_TUNING), LIFParams(), electrical=True, codegen=eng)
    loom_protocol(m, n_trials=N)
    f = m.spike_frame().sort_values(["t_ms", "bodyId"], kind="stable").reset_index(drop=True)
    frames[eng] = f
    hashes[eng] = hashlib.sha256(f[["t_ms", "bodyId"]].to_numpy().tobytes()).hexdigest()
    print(f"  {len(f):,} spikes, hash {hashes[eng][:16]}", flush=True)
a, b = frames["cython"], frames["numpy"]
same = len(a) == len(b) and np.array_equal(a.bodyId.values, b.bodyId.values) and np.array_equal(a.t_ms.values, b.t_ms.values)
first_diff = None
if not same:
    k = min(len(a), len(b))
    bad = np.flatnonzero((a.t_ms.values[:k] != b.t_ms.values[:k]) | (a.bodyId.values[:k] != b.bodyId.values[:k]))
    i = int(bad[0]) if len(bad) else k
    first_diff = dict(index=i, cython=a.iloc[i].to_dict() if i < len(a) else None,
                      numpy=b.iloc[i].to_dict() if i < len(b) else None)
report = dict(benchmark="engines_real", n_trials=N, identical=bool(same),
              spikes={k: int(len(v)) for k, v in frames.items()}, sha256=hashes, first_difference=first_diff,
              provenance=provenance(DATA))
(OUT / "engines_real.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(f"\n{'IDENTICAL' if same else 'DIFFERENT'}: compiled {len(a):,} vs pure-Python {len(b):,} spikes"
      + ("" if same else f"; first difference {first_diff}"))
sys.exit(0 if same else 1)
