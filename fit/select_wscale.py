"""
Re-select the global synaptic scale w_scale on a criterion blind to every benchmark (audit 2026-10-11, gap 6).

Until 11 October 2026 the declared w_scale was 0.3, chosen in September with an earlier simulator (exact
integration, no gap junctions, no adaptation, the on-disk sign column without histamine), on a grid
{1.0, 0.5, 0.25} that does not contain 0.3, and partly by looking at the giant fiber (docs/CALIBRATION.md).
This script makes the choice again with the current model and a criterion that sees no benchmark:

  DRIVE     a fixed random 10% (seed 0) of the sensory neurons whose types and subclasses no benchmark
            uses as a stimulus, at 20 Hz Poisson for 1 s (after 200 ms of silence)
  MEASURE   whole-CNS rate (spikes per neuron per second) and the fraction of neurons that fire at all,
            over the driven second, for each w_scale on the grid
  CRITERION the largest w_scale on the grid with whole-CNS rate < 1 Hz AND fraction active < 10% (the
            two quietness conditions of the September sweep, without its giant fiber condition)

The criterion is registered in results/select_wscale/criteria.json before anything runs. Its answer, 0.4,
was adopted as the declared value on 11 October 2026 (registration generation 3, flycns/registry.py), with
the giant fiber adaptation refit under it. (The registered criteria's "consequence" text still says
"other than 0.3": a registered text is never edited.) A rerun that selects anything other than the
declared value says so in its report (agrees_with_declared).

Run:  python fit/select_wscale.py [data_dir]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import CNSModel, LIFParams, load_graph  # noqa: E402
from flycns.bench import provenance  # noqa: E402
from flycns.graph import GUSTATORY_MN9_DRIVING, GUSTATORY_SUBCLASSES, PEPTIDE_MODULATION  # noqa: E402
from flycns.integrity import criteria_differ, require_clean, require_data  # noqa: E402
from flycns.protocols import LOOM_TUNING  # noqa: E402

DATA = sys.argv[1] if len(sys.argv) > 1 else "data"
OUT = Path("results/select_wscale"); OUT.mkdir(parents=True, exist_ok=True)
GRID = [0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.75, 1.0]   # 1.0 is Shiu et al. 2024's unscaled value
# subclasses and type prefixes that any benchmark drives; their afferents are never part of the blind drive
EXCLUDED_SUBCLASSES = sorted(set(GUSTATORY_SUBCLASSES) | {"auditory", "wind_gravity", "campaniform sensilla"})
EXCLUDED_PREFIXES = ("JO-", "LC", "LPLC", "SNpp", "pC1", "DNg02", "L1", "L2", "L3", "L5", "Pm3", "Mi1", "Tm2")
CRITERIA = dict(
    purpose="re-select the global synaptic scale w_scale blind to every benchmark (audit gap 6)",
    drive=("a fixed random 10% (numpy default_rng(0)) of sensory-superclass neurons whose type is not driven by any "
           "benchmark (types in LOOM_TUNING, GUSTATORY_MN9_DRIVING, peptide sources, and prefixes "
           + ", ".join(EXCLUDED_PREFIXES) + ") and whose subclass is not " + ", ".join(EXCLUDED_SUBCLASSES)
           + "; 20 Hz Poisson for 1000 ms after 200 ms of silence"),
    measure="whole-CNS rate (spikes/neuron/s) and fraction of neurons with >= 1 spike, over the driven 1000 ms",
    grid=GRID,
    rule="the largest grid value with whole-CNS rate < 1 Hz AND fraction active < 0.10",
    consequence="a recommendation; adopting a value other than 0.3 requires recalibrating PEAK_HZ, b_adapt and the A2 working point",
)

require_clean(Path(__file__).stem)
require_data(DATA, Path(__file__).stem)
crit_f = OUT / "criteria.json"
if crit_f.exists():
    if criteria_differ(crit_f, CRITERIA):
        raise SystemExit("criteria.json exists with DIFFERENT criteria; refusing to overwrite a registered selection.")
else:
    st = provenance()
    crit_f.write_text(json.dumps(dict(criteria=CRITERIA, registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      git_commit=st["git_commit"], script_uncommitted=st["git_dirty"]), indent=2),
                      encoding="utf-8")
print(f"criteria registered: {json.loads(crit_f.read_text(encoding='utf-8'))['git_commit'] or '?'}")

neurons, edges = load_graph(DATA)
t = neurons["type"].fillna("").astype(str)
sub = neurons["subclass"].fillna("").astype(str) if "subclass" in neurons else t.map(lambda _: "")
sensory = neurons["superclass"].fillna("").astype(str).str.contains("sensory")
used = set(LOOM_TUNING) | set(GUSTATORY_MN9_DRIVING) | {e["source"] for e in PEPTIDE_MODULATION}
eligible = sensory & ~t.isin(used) & ~sub.isin(EXCLUDED_SUBCLASSES) & ~t.str.startswith(EXCLUDED_PREFIXES)
pool = np.sort(neurons.loc[eligible, "bodyId"].to_numpy())
rng = np.random.default_rng(0)
driven = set(rng.choice(pool, max(1, len(pool) // 10), replace=False)) if len(pool) else set()
print(f"blind drive: {len(driven):,} of {len(pool):,} eligible sensory neurons "
      f"({int(sensory.sum()):,} sensory in all) at 20 Hz")
if not driven:
    raise SystemExit("no eligible sensory neurons: nothing to drive")
# drive by body: every cell of a sampled type becomes an input source, and only the sampled cells are
# given a rate (the others are silent sources, so they do not count towards the fraction active)
stim_types = sorted(set(t[neurons.bodyId.isin(driven)]))

rows = []
t0 = time.time()
for w in GRID:
    m = CNSModel(neurons, edges, stim_types, LIFParams(w_scale=w), electrical=True)
    rates = np.where(np.isin(m.stim["bodyId"].to_numpy(), list(driven)), 20.0, 0.0)
    m.run(200)
    m.set_stim_rates(rates)
    m.run(1000)
    sp = m.spike_frame()
    sp = sp[sp.t_ms >= 200]
    n = len(m.lif_ids)
    rate = len(sp) / n / 1.0
    active = sp.bodyId.nunique() / n
    rows.append(dict(w_scale=w, cns_rate_hz=float(rate), fraction_active=float(active),
                     quiet=bool(rate < 1.0 and active < 0.10), n_lif=int(n), n_driven=int((rates > 0).sum())))
    print(f"  w_scale {w:<5} CNS {rate:8.4f} Hz  active {active:6.2%}  {'quiet' if rows[-1]['quiet'] else 'NOT quiet'} "
          f"({round(time.time() - t0)}s)", flush=True)

quiet = [r["w_scale"] for r in rows if r["quiet"]]
selected = max(quiet) if quiet else None
# a selection at the edge of the grid means the criterion did not bind inside it
at_edge = selected is not None and selected == max(GRID)
report = dict(benchmark="select_wscale", criteria=CRITERIA, grid=rows, selected_w_scale=selected,
              criterion_binds_inside_grid=bool(quiet) and not at_edge,
              declared_w_scale=LIFParams().w_scale, n_eligible=int(len(pool)), n_driven=int(len(driven)),
              agrees_with_declared=(selected == LIFParams().w_scale), wall_s=round(time.time() - t0, 1),
              provenance=provenance(DATA))
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
print(f"\nselected w_scale: {selected} (declared {LIFParams().w_scale}); "
      + ("agrees" if report["agrees_with_declared"] else "DIFFERS: adopting it is a model-freeze decision"))
