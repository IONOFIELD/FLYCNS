"""Shared helpers for benchmark scripts: type discovery, pulse protocol, readout scoring."""
import numpy as np
import pandas as pd


def find_types(neurons, patterns):
    """Return list of distinct types matching any regex (case-insensitive), with counts."""
    t = neurons["type"].fillna("")
    hits = {}
    for pat in patterns:
        m = t[t.str.contains(pat, case=False, regex=True)]
        for k, v in m.value_counts().items():
            hits[k] = int(v)
    return hits


def present_types(neurons, wanted):
    have = set(neurons["type"].dropna().unique())
    return [w for w in wanted if w in have], [w for w in wanted if w not in have]


def pulse_protocol(model, rates_by_type, n_trials=10, pulse_ms=200, gap_ms=300, seed=0):
    """Drive stimulated types at given Hz for pulse_ms, n_trials times. Returns onsets."""
    rates = model.stim["type"].map(rates_by_type).fillna(0).values
    onsets = []
    for _ in range(n_trials):
        model.run(gap_ms)
        onsets.append(model.t_ms)
        model.set_stim_rates(rates)
        model.run(pulse_ms)
        model.set_stim_rates(np.zeros_like(rates))
    model.run(gap_ms)
    return onsets


def readout_rates(model, onsets, types, window_ms, meta):
    """Mean spikes per neuron of each type in the window after each onset, per side."""
    from .graph import infer_side
    side_all = infer_side(meta)
    sp = model.spike_frame()
    out = []
    for typ in types:
        ids = model.lif_ids[model.readout_index(typ)]
        if len(ids) == 0:
            continue
        side = side_all.loc[ids].where(lambda x: x.isin(["L", "R"]), "unsided")
        for k, on in enumerate(onsets):
            w = sp[(sp.t_ms >= on) & (sp.t_ms < on + window_ms) & sp.bodyId.isin(ids)]
            for s in ["L", "R", "unsided"]:
                cells = side.index[side == s]
                if len(cells):
                    ws = w[w.bodyId.isin(cells)]          # this side only: count and latency
                    out.append(dict(trial=k, type=typ, side=s, spikes_per_cell=len(ws) / len(cells),
                                    latency_ms=(ws.t_ms.min() - on) if len(ws) else np.nan))
    return pd.DataFrame(out)


def provenance(data_dir=None):
    """Stamp every report so a stale one can never be mistaken for a current one: commit and
    whether the code matched it, FLYCNS_* overrides, library versions, graph settings and the
    content fingerprint of the input data (flycns/integrity.py). Scripts that read the tables
    without graph.load_graph pass their data_dir."""
    from .integrity import provenance_record
    return provenance_record(data_dir)


def stamp(path, data_dir=None, **extra):
    """The stamp for an output that cannot carry one itself (CSV, HDF5): written beside it as
    <file>.stamp.json with the script, its arguments and anything in extra. results/SUITE.md
    lists every result file without a stamp."""
    import json
    import sys
    from pathlib import Path
    path = Path(path)
    rec = dict(file=path.name, script=Path(sys.argv[0]).as_posix(), args=sys.argv[1:], **extra,
               provenance=provenance(data_dir))
    path.with_name(path.name + ".stamp.json").write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")


def spike_source(n, ids, times_ms, dt_ms=0.1):
    """SpikeGeneratorGroup for jittered spike trains. Brian2 refuses a source that spikes twice in one
    time step, which jitter makes possible (about 9% of runs at 400 sources); the later duplicate in a
    bin is dropped, so committed runs (which had none) are unchanged."""
    from brian2 import SpikeGeneratorGroup, ms
    ids = np.asarray(ids, dtype=int)
    t = np.asarray(times_ms, dtype=float)
    bins = ((t + 1e-3 * dt_ms) / dt_ms).astype(np.int64)        # Brian2's own binning
    keep = ~pd.DataFrame(dict(i=ids, b=bins)).duplicated().to_numpy()
    return SpikeGeneratorGroup(n, ids[keep], t[keep] * ms)
