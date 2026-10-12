"""
Does EACH giant fiber get the declared JON -> GF compound potential on the real connectome?

The compound potential (flycns/graph.py ELECTRICAL_SYNAPSES, 3 mV at 150 Hz) is calibrated per post cell
since 11 October 2026: each giant fiber's spikelet and coupling are computed from the afferents coupled
to THAT cell. Run 12 measured 3.65 and 0.73 mV under the earlier calibration, which used one value from
the mean count per side. tests/unit.py checks the arithmetic on a toy; this checks it on the connectome.

For every giant fiber (DNp01) it reports:
  coupling      the coupled afferents, the spikelet and the summed coupling load (from the model's own
                electrical table), and the steady state they predict
  electrical    sound alone (the auditory JO types at 150 Hz in 60 ms pulses, the auditory benchmark's
                protocol) with every chemical input to the giant fibers removed, so only the calibrated
                coupling acts: the mean depolarisation over the last 30 ms of each pulse (the plateau)
                and the mean peak over the 100 ms window
  network       the same, with the chemical inputs kept: what the auditory benchmark's sound-alone arm sees
PASS if every giant fiber's electrical plateau is within 10% of the target times the charging factor:
the mean of 1 - exp(-(t - d) / tau_eff) over the plateau window (the potential cannot reach its steady state
within a 60 ms pulse; tau_eff = tau_m / (1 + G_GAP_RELAY); d is the 0.8 ms gap-junction delay). The network
numbers are reported, not scored: chemical paths add to the calibrated coupling by design.

Writes results/checks/jon_calibration.json (stamped). Exits non-zero on FAIL.
Run:  python fit/check_jon_calibration.py [n_trials=40] [data_dir]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import CNSModel, LIFParams, load_graph  # noqa: E402
from flycns.bench import provenance, pulse_protocol  # noqa: E402
from flycns.graph import (ELECTRICAL_SYNAPSES, G_GAP_RELAY, afferents_by_subclass, infer_side,  # noqa: E402
                          jon_compound_mv, jon_mode)

N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else 40
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/checks"); OUT.mkdir(parents=True, exist_ok=True)
PULSE_MS, WINDOW_MS, PLATEAU_MS, HZ = 60, 100, 30, 150
TOL = 0.10

if jon_mode() != "electrical":
    raise SystemExit("FLYCNS_JON is not 'electrical': there is no calibrated coupling to check")
entry = next(e for e in ELECTRICAL_SYNAPSES if e[1] == "DNp01" and isinstance(e[3], dict))
TARGET = jon_compound_mv()
assert entry[3]["at_hz"] == HZ, "the check's rate must be the calibration rate"
p = LIFParams()
tau_eff = p.tau_m_ms / (1 + G_GAP_RELAY)
# mean of the charging curve 1 - exp(-(t - d) / tau_eff) over the plateau window [pulse - plateau, pulse]
a, b = PULSE_MS - PLATEAU_MS - p.gap_delay_ms, PULSE_MS - p.gap_delay_ms
charge = 1 - tau_eff / PLATEAU_MS * (math.exp(-a / tau_eff) - math.exp(-b / tau_eff))
want = TARGET * charge

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
side = infer_side(meta)
JO = [t for t in afferents_by_subclass(neurons, ["auditory"], "JO-") if not t.endswith("unclear")]
if not JO:
    raise SystemExit("no auditory JO types in this dataset")
gf_ids = meta.index[meta["type"] == "DNp01"]


def arm(edge_df, label):
    m = CNSModel(neurons, edge_df, JO, LIFParams(), electrical=True, monitor_types=("DNp01",))
    on = pulse_protocol(m, {t: HZ for t in JO}, n_trials=N, pulse_ms=PULSE_MS)
    from brian2 import mV, ms
    t = np.array(m.vmon.t / ms); v = np.array(m.vmon.v / mV) - p.v_rest_mV
    ids = list(m.vmon_ids)
    plateau = np.array([v[:, (t >= o + PULSE_MS - PLATEAU_MS) & (t < o + PULSE_MS)].mean(axis=1) for o in on])
    peak = np.array([v[:, (t >= o) & (t < o + WINDOW_MS)].max(axis=1) for o in on])
    sp = m.spike_frame()
    out = {}
    for k, b in enumerate(ids):
        fired = sum(int(((sp.t_ms >= o) & (sp.t_ms < o + WINDOW_MS) & (sp.bodyId == b)).any()) for o in on)
        out[int(b)] = dict(plateau_mV=float(plateau[:, k].mean()), peak_mV=float(peak[:, k].mean()),
                           fired_trials=int(fired))
        print(f"  [{label}] GF {b} ({side.get(b)}): plateau {out[int(b)]['plateau_mV']:.2f} mV, "
              f"peak {out[int(b)]['peak_mV']:.2f} mV, fired on {fired}/{len(on)} trials", flush=True)
    return m, out


print(f"sound alone: {len(JO)} JO types at {HZ} Hz, {PULSE_MS} ms pulses, {N} trials; target {TARGET} mV "
      f"steady state, {want:.2f} mV expected over the plateau window (charging factor {charge:.3f})", flush=True)
no_chem = edges[~edges["post"].isin(gf_ids)].reset_index(drop=True)
m_e, elec = arm(no_chem, "electrical only")
_, net = arm(edges, "network")
tab = m_e.electrical_table
tab = tab[tab.post.isin(gf_ids)]
cells, ok = [], True
for b in gf_ids:
    rows = tab[tab.post == b]
    n = int(len(rows))
    spk = sorted(set(round(x, 9) for x in rows.spikelet_mV))
    load = float(rows.g_gap.sum())
    predicted = n * HZ * (spk[0] if spk else 0.0) * (p.tau_m_ms / 1000) / (1 + load) if n else 0.0
    e = elec.get(int(b), {})
    good = n > 0 and abs(e.get("plateau_mV", float("nan")) - want) <= TOL * want
    ok &= bool(good)
    cells.append(dict(bodyId=int(b), side=side.get(b), n_coupled_afferents=n,
                      afferent_types=sorted(rows.pre_type.unique()), spikelet_mV=spk, coupling_load=load,
                      predicted_steady_mV=predicted, electrical=e, network=net.get(int(b), {}),
                      verdict="PASS" if good else "FAIL"))
report = dict(benchmark="jon_calibration", target_mV=TARGET, rate_hz=HZ, pulse_ms=PULSE_MS,
              plateau_window_ms=PLATEAU_MS, tau_eff_ms=tau_eff, charging_factor=charge,
              expected_plateau_mV=want, tolerance=TOL, n_trials=N, jo_types=JO, giant_fibers=cells,
              rule=(f"PASS if every giant fiber's electrical-only plateau (last {PLATEAU_MS} ms of a {PULSE_MS} ms "
                    f"pulse, mean over trials) is within {TOL:.0%} of target x the mean charging factor over that window "
                    "(tau_eff = tau_m / (1 + G_GAP_RELAY), gap-junction delay included); the network arm is reported, "
                    "not scored"),
              verdict="PASS" if ok else "FAIL", provenance=provenance(DATA))
(OUT / "jon_calibration.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(f"\n{'PASS' if ok else 'FAIL'}: " + "; ".join(
    f"GF {c['bodyId']} ({c['side']}) {c['n_coupled_afferents']} afferents, plateau "
    f"{c['electrical'].get('plateau_mV', float('nan')):.2f} mV (want {want:.2f})" for c in cells))
sys.exit(0 if ok else 1)
