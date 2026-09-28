"""
Export simulated sessions in a brainsets-style HDF5 layout for POYO / POYO+ (torch_brain).

Each session: one stimulus family (loom / sound / taste), N trials with per-trial condition
labels, spikes from a recorded subset of neurons, and a units table carrying connectome
features that could seed unit embeddings:
    type, superclass, subclass, side, in_synapses, out_synapses, in_degree, out_degree,
    synaptic_depth_from_stimulus (BFS hops), and a stable unit_id (MaleCNS bodyId).

Layout (per file, groups/datasets):
    /spikes/timestamps  float64 [s]      /spikes/unit_index int32
    /units/id, /units/<feature>...      /trials/start, /trials/end, /trials/condition
    attrs: session_id, subject_id="malecns_v1.0_lif", brainset="flycns_sim", sampling=event
This follows the structure brainsets uses (temporaldata Data: spikes, units, trials,
domain); verify field names against the installed brainsets version before training.

Run:  python export_brainsets.py [n_trials] [out_dir]
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
import h5py
import temporaldata as td
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flycns import load_graph, CNSModel, LIFParams
from flycns.protocols import LOOM_TUNING
from flycns.bench import find_types, pulse_protocol
from flycns.graph import GUSTATORY_MN9_DRIVING

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "results/brainsets"); OUT.mkdir(parents=True, exist_ok=True)
neurons, edges = load_graph("data")
meta = neurons.set_index("bodyId")
jo = [t for t in find_types(neurons, [r"^JO-A", r"^JO-B"]) if not t.endswith("unclear")]
taste = [t for t in GUSTATORY_MN9_DRIVING if (neurons.type == t).any()]

SESSIONS = {
    "loom":  dict(stim=list(LOOM_TUNING), conditions={"weak": 0.5, "medium": 1.0, "strong": 2.0}),
    "sound": dict(stim=jo,               conditions={"soft": 50, "loud": 150}),
    "taste": dict(stim=taste,            conditions={"low": 50, "high": 150}),
}
# recorded population: everything within 3 synapses downstream of any stimulus type (capped)
import networkx as nx
G = nx.DiGraph(); G.add_edges_from(edges[["pre", "post"]].itertuples(index=False))
deg_in = edges.groupby("post").weight.sum(); deg_out = edges.groupby("pre").weight.sum()
nin = edges.groupby("post").size(); nout = edges.groupby("pre").size()

for name, cfg in SESSIONS.items():
    stim_ids = set(neurons.loc[neurons.type.isin(cfg["stim"]), "bodyId"])
    depth = {}
    frontier = {b: 0 for b in stim_ids if b in G}
    seen = dict(frontier)
    for hop in range(1, 4):
        nxt = {}
        for b in frontier:
            for s in G.successors(b):
                if s not in seen:
                    seen[s] = hop; nxt[s] = hop
        frontier = nxt
    recorded = [b for b, h in seen.items() if h >= 1]
    rng = np.random.default_rng(0)
    if len(recorded) > 3000:
        recorded = list(rng.choice(recorded, 3000, replace=False))
    recorded = sorted(recorded)
    print(f"[{name}] {len(stim_ids)} stimulated, recording {len(recorded)} downstream neurons")

    m = CNSModel(neurons, edges, cfg["stim"], LIFParams(), electrical=True)
    tuning = m.stim["type"].map(LOOM_TUNING).fillna(0).values if name == "loom" else None
    trials = []
    for k in range(N):
        cond = list(cfg["conditions"])[k % len(cfg["conditions"])]
        val = cfg["conditions"][cond]
        m.run(300); t0 = m.t_ms
        rates = tuning * 5.0 * val if name == "loom" else np.full(len(m.stim), float(val))
        m.set_stim_rates(rates); m.run(60 if name == "loom" else 200)
        m.set_stim_rates(np.zeros(len(m.stim)))
        trials.append(dict(start=t0 / 1000, end=(m.t_ms + 200) / 1000, condition=cond, value=val))
    m.run(300)
    sp = m.spike_frame(); sp = sp[sp.bodyId.isin(recorded)]
    uidx = pd.Series(np.arange(len(recorded)), index=recorded)

    f = OUT / f"flycns_sim_{name}.h5"
    t_end = m.t_ms / 1000.0
    ts = (sp.t_ms.values / 1000.0).astype("f8")
    ui = uidx.loc[sp.bodyId].values.astype("i8")
    order = np.argsort(ts, kind="stable")
    whole = td.Interval(start=np.array([0.0]), end=np.array([t_end]))
    spikes = td.IrregularTimeSeries(timestamps=ts[order], unit_index=ui[order], domain=whole)
    ufields = dict(id=np.array([f"malecns:{b}" for b in recorded]), body_id=np.array(recorded, dtype="i8"))
    for col in ["type", "superclass", "subclass", "somaSide", "consensusNt"]:
        if col in meta:
            ufields[col] = np.array(meta.loc[recorded, col].fillna("").astype(str))
    ufields.update(in_synapses=deg_in.reindex(recorded).fillna(0).values.astype("f4"),
                   out_synapses=deg_out.reindex(recorded).fillna(0).values.astype("f4"),
                   in_degree=nin.reindex(recorded).fillna(0).values.astype("f4"),
                   out_degree=nout.reindex(recorded).fillna(0).values.astype("f4"),
                   synaptic_depth_from_stimulus=np.array([seen[b] for b in recorded], dtype="i2"))
    for c in ["x", "y", "z"]:
        ufields[f"soma_{c}"] = meta.loc[recorded, c].fillna(np.nan).values.astype("f4")
    units = td.ArrayDict(**ufields)
    trial_iv = td.Interval(start=np.array([t["start"] for t in trials], dtype="f8"),
                           end=np.array([t["end"] for t in trials], dtype="f8"),
                           condition=np.array([t["condition"] for t in trials]),
                           value=np.array([t["value"] for t in trials], dtype="f4"))
    data = td.Data(brainset="flycns_sim", session=f"flycns_sim_{name}", subject="malecns_v1.0_lif",
                   spikes=spikes, units=units, trials=trial_iv, domain=whole)
    with h5py.File(f, "w") as h:
        data.to_hdf5(h)
        h.attrs["model_params"] = json.dumps(LIFParams().__dict__, default=str)
        h.attrs["stimulus_types"] = json.dumps(cfg["stim"])
        h.attrs["note"] = "simulated; connectome-constrained LIF; see flycns RESULTS.md"
    # validate with the real loader: a file it cannot read, or reads differently, fails here
    with h5py.File(f, "r") as h:
        back = td.Data.from_hdf5(h, lazy=False)
        ok = (np.array_equal(back.spikes.timestamps, spikes.timestamps)
              and np.array_equal(back.spikes.unit_index, spikes.unit_index)
              and len(back.units.id) == len(recorded) and len(back.trials) == len(trials))
    if not ok:
        raise SystemExit(f"VALIDATION FAILED: {f} does not round-trip through temporaldata.Data.from_hdf5")
    print(f"  wrote {f}: {len(sp):,} spikes, {len(recorded)} units, {N} trials, {t_end:.1f} s "
          f"(validated: reloads with temporaldata {td.__version__})")
print("\nevery file was reloaded with temporaldata.Data.from_hdf5 and compared to what was written")
