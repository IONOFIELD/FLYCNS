"""
Does the flight result depend on the relay layer's inherited single-neuron parameters?

The flight benchmark's headline is that DLMn c-f, which receives about twice DVMn's descending
drive per cell, stays silent because that drive is disynaptic and its relay layer is
subthreshold. Those relays are nerve-cord interneurons running on Shiu et al.'s central-brain
membrane values (tau_m 20 ms, threshold 7 mV above rest, refractory 2.2 ms). The escape
benchmark was invariant to cord parameters because its cascade is monosynaptic through a
declared electrical relay (benchmarks/sensitivity_cord.py); flight is the first result that
asks the cord to compute, so it may not be.

This is a SENSITIVITY test, not a fit: nothing is chosen, and no value found here enters the
declared parameter set. The relay superclasses are read from the data (the superclasses of the
excitatory interneurons onto DLMn c-f), and only those are varied, one parameter at a time,
over the same ranges as the escape sweep. Every other neuron keeps the declared values.

Conditions at each setting, both at the flight anchor (proprioceptive load 0.35, where DVMn
sits at ~9 Hz without any command):
  A  proprioceptive drive only
  B  proprioceptive drive + DNg02 at 10 Hz (the rate at which DVMn is in band)

Reads as:
  - DLMn c-f silent across the whole sweep   -> the flight claim does not rest on relay
    parameters; the gap is the missing background activity, as stated.
  - DLMn c-f enters 2-12 Hz at some setting WITH DVMn still in band and steering still specific
    -> the flight claim is parameter-dependent and must be worded that way; the setting is a
    hypothesis about cord interneuron physiology, not a fit.
  - DLMn c-f wakes only when the whole cord floods -> a lower threshold is not a rescue.

Run:  python benchmarks/sensitivity_flight.py [n_cycles] [data_dir]   (default 400 cycles = 2 s)
Writes results/sensitivity_flight/grid.csv and summary.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brian2 import SpikeGeneratorGroup, Synapses, ms, mV
from flycns import load_graph, CNSModel, LIFParams
from flycns.bench import provenance
from flycns.graph import SIGN_MAP

N_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 400
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/sensitivity_flight")
OUT.mkdir(parents=True, exist_ok=True)

WINGBEAT_HZ, JITTER_MS, LOAD, DNG02_HZ = 202.0, 0.8, 0.35, 10.0
STEER = r"^(b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
BASE = LIFParams()

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna("")
sub = meta["subclass"].fillna("")
nerve = meta["entryNerve"].fillna("")
sc = meta["superclass"].fillna("")

aff = list(meta.index[(sub == "campaniform sensilla") & nerve.isin(["ADMN", "DMetaN"])])
dlm = meta.index[t == "DLMn c-f"]
dvm = meta.index[t == "DVMn 1a-c"]
steer = meta.index[t.str.match(STEER)]
dng02_types = sorted(meta.loc[t.str.match(r"^DNg02"), "type"].dropna().unique())

first = edges[edges.pre.isin(aff)].groupby("post").weight.sum()
relays = first[first >= 20].index
onto = edges[edges.pre.isin(relays) & edges.post.isin(dlm)]
sgn = onto["nt"].str.lower().map(SIGN_MAP).fillna(0)
exc_relays = set(onto[sgn > 0].pre)
relay_sc = pd.Series([sc.get(b, "") for b in exc_relays]).value_counts()
RELAY_SUPERCLASSES = [s for s in relay_sc.index if s]
print(f"campaniform afferents {len(aff)}; DLMn c-f {len(dlm)}; DVMn 1a-c {len(dvm)}; DNg02 subtypes {len(dng02_types)}")
print(f"excitatory relays onto DLMn c-f: {len(exc_relays)}, by superclass: {relay_sc.to_dict()}")
print(f"varying ONLY: {RELAY_SUPERCLASSES}")

SWEEP = ([("tau_m_ms", v) for v in (5.0, 10.0, 20.0, 40.0)]
         + [("v_thresh_mV", BASE.v_rest_mV + g) for g in (4.0, 5.5, 7.0, 10.0)]
         + [("refractory_ms", v) for v in (1.0, 2.2, 5.0)])


def phase_locked(n_aff, n_cycles, load, rng, t0_ms):
    period = 1000.0 / WINGBEAT_HZ
    n_rec = max(1, int(round(load * n_aff)))
    idx = rng.choice(n_aff, n_rec, replace=False)
    phase = rng.uniform(0, period, size=n_rec)
    cyc = np.arange(n_cycles) * period
    times = (cyc[None, :] + phase[:, None] + rng.normal(0, JITTER_MS, (n_rec, n_cycles))).ravel()
    ids = np.repeat(idx, n_cycles)
    keep = times >= 0
    return ids[keep], times[keep] + t0_ms


def run(param, value, with_command):
    t0 = time.time()
    over = {s: {param: value} for s in RELAY_SUPERCLASSES}
    stim = dng02_types if with_command else []
    m = CNSModel(neurons, edges, stim, LIFParams(superclass_params=over), electrical=True)
    lif_idx = [m.lif_index[b] for b in aff if b in m.lif_index.index]
    rng = np.random.default_rng(0)
    pre_ms, period = 200.0, 1000.0 / WINGBEAT_HZ
    dur_ms = N_CYCLES * period
    ids, times = phase_locked(len(lif_idx), N_CYCLES, LOAD, rng, pre_ms)
    gen = SpikeGeneratorGroup(len(lif_idx), ids, times * ms)
    S = Synapses(gen, m.G, on_pre="v_post += kick", namespace=dict(kick=8.0 * mV))
    S.connect(i=np.arange(len(lif_idx)), j=np.array(lif_idx))
    m.net.add(gen, S)
    m.run(pre_ms)
    if with_command:
        m.set_stim_rates(np.full(len(m.stim), DNG02_HZ))
    m.run(dur_ms)
    sp = m.spike_frame()
    sp = sp[(sp.t_ms >= pre_ms) & (sp.t_ms < pre_ms + dur_ms)]
    dur_s = dur_ms / 1000.0

    def rate(ids_):
        ids_ = [b for b in ids_ if b in m.lif_index.index]
        return float(sp.bodyId.isin(ids_).sum() / max(len(ids_), 1) / dur_s)

    exc_active = int(sp[sp.bodyId.isin(exc_relays)].bodyId.nunique())
    n_changed = sum(x["n"] for x in m.superclass_params_applied)
    row = dict(param=param, value=value, with_dng02=with_command, n_relay_cells_changed=n_changed,
               dlmn_cf_hz=rate(dlm), dvmn_hz=rate(dvm), steering_hz=rate(steer),
               exc_relays_active=exc_active, exc_relays_total=len(exc_relays),
               cns_hz=float(m.population_rate_hz()), wall_s=round(time.time() - t0))
    row["dlm_in_band"] = 2.0 <= row["dlmn_cf_hz"] <= 12.0
    row["dvm_in_band"] = 2.0 <= row["dvmn_hz"] <= 12.0
    row["both_in_band"] = row["dlm_in_band"] and row["dvm_in_band"]
    row["flooded"] = row["cns_hz"] > 1.0
    tag = "+DNg02" if with_command else "      "
    print(f"{param:<14}={value:>6} {tag} | DLMn c-f {row['dlmn_cf_hz']:6.2f} | DVMn {row['dvmn_hz']:6.2f} | "
          f"steer {row['steering_hz']:6.1f} | exc relays {exc_active:>3}/{len(exc_relays)} | "
          f"CNS {row['cns_hz']:.3f}{'  BOTH IN BAND' if row['both_in_band'] else ''}"
          f"{'  FLOODED' if row['flooded'] else ''} | {row['wall_s']}s")
    return row


rows = []
for param, value in SWEEP:
    for cmd in (False, True):
        rows.append(run(param, value, cmd))
        pd.DataFrame(rows).to_csv(OUT / "grid.csv", index=False)

df = pd.DataFrame(rows)
woke = df[df.dlmn_cf_hz >= 2.0]
both = df[df.both_in_band & ~df.flooded]
if not len(woke):
    verdict = ("DLMn c-f stays below 2 Hz across the whole sweep of relay-layer tau_m, threshold gap and "
               "refractory period, with and without the DNg02 command: the flight claim does not rest on "
               "the relay layer's inherited parameters.")
elif len(both):
    verdict = ("DLMn c-f and DVMn 1a-c are both in the measured band at "
               + "; ".join(f"{r.param}={r.value}{' +DNg02' if r.with_dng02 else ''}" for r in both.itertuples())
               + ", without flooding: the flight claim is parameter-dependent and must be worded that way. "
                 "These settings are hypotheses about cord interneuron physiology, not fits.")
else:
    verdict = ("DLMn c-f wakes at some settings but never with DVMn also in band"
               + (" and/or only when the cord floods" if (woke.flooded.any()) else "")
               + ": a different relay parameter does not rescue the two-pool result.")
summary = dict(relay_superclasses_varied=RELAY_SUPERCLASSES, n_exc_relays=len(exc_relays),
               load=LOAD, dng02_hz=DNG02_HZ, n_settings=len(SWEEP),
               dlm_woke_at=[dict(param=r.param, value=r.value, dng02=bool(r.with_dng02), dlm_hz=r.dlmn_cf_hz,
                                 dvm_hz=r.dvmn_hz, cns_hz=r.cns_hz) for r in woke.itertuples()],
               both_in_band_unflooded=[dict(param=r.param, value=r.value, dng02=bool(r.with_dng02))
                                       for r in both.itertuples()],
               verdict=verdict, provenance=provenance())
(OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
print("\nVERDICT:", verdict)
print(f"wrote {OUT / 'grid.csv'} and summary.json")
