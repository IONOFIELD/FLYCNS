"""
Is DVMn's proprioceptive drive carried by one named wing campaniform type?

Across five random recruitment draws at the flight anchor, DVMn 1a-c ranged from 0 to 15 Hz
(benchmarks/flight_loop.py), because its drive is concentrated: of the 413 wing and haltere
campaniform afferents, 41 contact DVMn 1a-c, and one type, SNpp16 (13 cells, wing nerve ADMN),
carries 664 of its 1,017 synapses (65%); SNpp07 adds 130. A random draw is a lottery over
whether those cells fire. This benchmark removes the lottery by driving identified sets
deterministically, all recruited, phase-locked at the 202 Hz wingbeat (Vogel 1967) with 0.8 ms
jitter (Fox, Fairhall & Daniel 2010). Only phase and jitter remain random, so each arm runs over
several seeds.

Arms:
  S1  SNpp16 alone                        sufficiency: does one named field drive DVMn into band?
  S2  every other afferent, SNpp16 withheld  necessity: does DVMn collapse without it?
  S3  all 413 afferents                   reference (full recruitment)

Criteria (DVMn 1a-c in the measured 2-12 Hz band, Harcombe & Wyman 1977; Huerkey et al. 2023):
  N1  S1 puts DVMn in band in every seed            (SNpp16 sufficient at physiological rate)
  N2  S2 gives DVMn below 2 Hz in every seed        (SNpp16 necessary)
Reported: DLMn c-f, steering, b1 in each arm; whether SNpp16 alone is wiring-specific
(S1 vs the same cells on a rewired null).

This is a prediction about the fly, not a fit: if it holds, silencing SNpp16 in a flying fly
should suppress DVM motor neuron activity while leaving much of the rest of the flight motor
output intact.

Run:  python benchmarks/flight_snpp16.py [n_cycles] [data_dir]
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
from flycns.graph import rewire_null

N_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 400
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/flight_snpp16")
OUT.mkdir(parents=True, exist_ok=True)
WINGBEAT_HZ, JITTER_MS = 202.0, 0.8
SEEDS = [0, 1, 2]
import os
TARGET = os.environ.get("FLYCNS_TARGET_TYPE", "SNpp16")   # override only for smoke tests on the toy graph
STEER = r"^(b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna("")
sub = meta["subclass"].fillna("")
nerve = meta["entryNerve"].fillna("")
aff_all = sorted(meta.index[(sub == "campaniform sensilla") & nerve.isin(["ADMN", "DMetaN"])])
target = sorted(b for b in aff_all if t[b] == TARGET)
others = sorted(b for b in aff_all if t[b] != TARGET)
dvm = meta.index[t == "DVMn 1a-c"]
dlm = meta.index[t == "DLMn c-f"]
steer = meta.index[t.str.match(STEER)]
b1 = meta.index[t == "b1 MN"]
syn_to_dvm = int(edges[edges.pre.isin(target) & edges.post.isin(dvm)].weight.sum())
syn_all = int(edges[edges.pre.isin(aff_all) & edges.post.isin(dvm)].weight.sum())
print(f"afferents: {len(aff_all)} total | {TARGET} {len(target)} cells | others {len(others)}")
print(f"{TARGET} -> DVMn 1a-c: {syn_to_dvm} of {syn_all} afferent synapses ({syn_to_dvm / max(syn_all, 1):.0%})")
if not target:
    raise SystemExit(f"{TARGET} not found among campaniform afferents")


def drive(src, edge_df, seed):
    t0 = time.time()
    m = CNSModel(neurons, edge_df, [], LIFParams(), electrical=True)
    idx = [m.lif_index[b] for b in src if b in m.lif_index.index]
    rng = np.random.default_rng(seed)
    period, pre_ms = 1000.0 / WINGBEAT_HZ, 200.0
    dur_ms = N_CYCLES * period
    phase = rng.uniform(0, period, size=len(idx))
    cyc = np.arange(N_CYCLES) * period
    times = (cyc[None, :] + phase[:, None] + rng.normal(0, JITTER_MS, (len(idx), N_CYCLES))).ravel() + pre_ms
    ids = np.repeat(np.arange(len(idx)), N_CYCLES)
    keep = times >= 0
    gen = SpikeGeneratorGroup(len(idx), ids[keep], times[keep] * ms)
    S = Synapses(gen, m.G, on_pre="v_post += kick", namespace=dict(kick=8.0 * mV))
    S.connect(i=np.arange(len(idx)), j=np.array(idx))
    m.net.add(gen, S)
    m.run(pre_ms + dur_ms)
    sp = m.spike_frame()
    sp = sp[sp.t_ms >= pre_ms]
    dur_s = dur_ms / 1000.0

    def rate(ids_):
        ids_ = [b for b in ids_ if b in m.lif_index.index]
        return float(sp.bodyId.isin(ids_).sum() / max(len(ids_), 1) / dur_s)

    return dict(dvmn=rate(dvm), dlmn=rate(dlm), steer=rate(steer), b1=rate(b1),
                cns=float(m.population_rate_hz()), n_driven=len(idx), wall_s=round(time.time() - t0))


def arm(label, src, edge_df=edges):
    runs = [drive(src, edge_df, sd) for sd in SEEDS]
    agg = {k: [r[k] for r in runs] for k in ("dvmn", "dlmn", "steer", "b1", "cns")}
    rec = dict(arm=label, n_driven=runs[0]["n_driven"],
               **{f"{k}_mean": float(np.mean(v)) for k, v in agg.items()},
               **{f"{k}_per_seed": [round(x, 2) for x in v] for k, v in agg.items() if k in ("dvmn", "dlmn")})
    print(f"[{label:<24}] {rec['n_driven']:>3} afferents | DVMn 1a-c {rec['dvmn_mean']:6.2f} Hz "
          f"(seeds {agg['dvmn'][0]:.1f}/{agg['dvmn'][1]:.1f}/{agg['dvmn'][2]:.1f}) | DLMn c-f {rec['dlmn_mean']:5.2f} | "
          f"steering {rec['steer_mean']:6.1f} | b1 {rec['b1_mean']:6.1f} | CNS {rec['cns_mean']:.3f} | "
          f"{sum(r['wall_s'] for r in runs)}s")
    return rec


report = dict(benchmark="flight_snpp16", target_type=TARGET, n_target=len(target), n_others=len(others),
              target_share_of_dvmn_synapses=syn_to_dvm / max(syn_all, 1), seeds=SEEDS, arms={})
report["arms"]["S1_snpp16_alone"] = arm(f"S1 {TARGET} alone", target)
report["arms"]["S2_all_but_snpp16"] = arm(f"S2 all but {TARGET}", others)
report["arms"]["S3_all_afferents"] = arm("S3 all afferents", aff_all)
report["arms"]["null_snpp16_alone"] = arm(f"null: {TARGET} alone", target, rewire_null(edges, seed=0))

s1 = report["arms"]["S1_snpp16_alone"]; s2 = report["arms"]["S2_all_but_snpp16"]
report["checks"] = {
    "N1_snpp16_sufficient_dvmn_in_band": all(2.0 <= x <= 12.0 for x in s1["dvmn_per_seed"]),
    "N2_snpp16_necessary_dvmn_below_2hz": all(x < 2.0 for x in s2["dvmn_per_seed"]),
}
report["reported"] = dict(
    specificity=dict(real=s1["dvmn_mean"], rewired_null=report["arms"]["null_snpp16_alone"]["dvmn_mean"]),
    prediction=(f"silencing {TARGET} in a flying fly should suppress DVM motor neuron activity; the "
                f"model's DVMn output under proprioceptive drive is set by this one wing campaniform type"))
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print("\nCHECKS")
for k, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"\nwrote {OUT / 'report.json'}")
