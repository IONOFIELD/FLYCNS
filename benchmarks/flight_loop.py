"""
Proprioceptive drive to the wing motor system: open loop, then closed (surrogate body).

The wing and haltere campaniform afferents are in MaleCNS v1.0 under nerve-based labels
(ADMN = wing nerve, DMetaN = haltere nerve; Court et al. 2020). They contact wing motor
neurons directly (11,412 synapses, all excitatory) and through ~1,100 relay interneurons,
with net drive that excites the power muscles and inhibits most steering muscles. DNp31,
the strongest descending input to the wing pool, is driven by the same afferents. None of
this fires under visual loom, because campaniform organs report self-generated wing load.

This benchmark supplies that load. There is no physics: a phase variable at the Drosophila
wingbeat frequency drives the afferents, and a scalar LOAD sets what fraction of them are
recruited. Parameters are cited but cross-species; that is stated, not hidden.

DRIVE (per afferent)
  wingbeat        202 Hz                   Vogel 1967 (tethered D. melanogaster, 202 +/- 2.8 Hz SE)
  locking         one spike per cycle      Fox & Daniel 2008: haltere afferents follow 1:1 to 150 Hz
                                           (Holorusia); Yarger & Fox 2018: natural ~200 Hz (Sarcophaga)
  jitter          0.8 ms SD                Fox, Fairhall & Daniel 2010 (0.81 +/- 0.15 ms, n=18, Holorusia)
  recruitment     fraction = LOAD          Yarger & Fox 2018: threshold-based recruitment shifts with
                                           displacement. Mapping load -> fraction is an ASSUMPTION.
  phase           afferents spread uniformly over the cycle (no measured phase map for Drosophila)

ANCHOR (the one free parameter): the load -> recruitment mapping is not measured in any
species, so LOAD is chosen by rule, like PEAK_HZ for the loom: the smallest load at which
DVMn 1a-c (the power neuron with direct afferent input) sits in the measured 2-12 Hz band.
The null and the closed loop run at that anchor.

TARGETS (measured, the benchmark criteria), scored PER TYPE because averaging across the
power pool hid a silent DLM behind an active DVM in the first run:
  L1a DVMn 1a-c fire 2-12 Hz             Harcombe & Wyman 1977; Koenig & Ikeda 1983;
  L1b DLMn c-f fire 2-12 Hz              Huerkey et al. 2023 (Nature): 2-12 Hz, splay state
  L2  b1 fires 0.5-1.2 spikes per wingbeat   Fayyazuddin & Dickinson 1996, Calliphora
  L3  leg motor neurons are not entrained by the wingbeat
  L4  specificity vs rewired null at the anchor load: real steering (b1 + others) rate at
      least 5x the null's
STAGE 2, DESCENDING FLIGHT COMMAND. Under proprioceptive drive alone the DLMn c-f relay
layer is subthreshold (4 of 92 excitatory relays active at the anchor). DNg02 is a population
of ~15 homomorphic descending neuron pairs whose optogenetic activation raises wingbeat
amplitude linearly with the number of cells recruited and, at maximum, drives the indirect
flight muscle motor neurons to a constant-power ceiling (Namiki, Ros, Morrow, Rowell, Card,
Korff & Dickinson 2022, Curr Biol 32:1189-1196, Figs 1, 3). In MaleCNS v1.0 there are 29
cholinergic DNg02 cells contacting DLMn c-f directly (423 synapses), 20 of its 92 excitatory
relays (1,060) and the wing motor pool (3,670). The paper gives no firing rate (optogenetic
activation, kinematic and calcium readout), so DNg02_HZ is this stage's declared free
parameter, swept, and chosen by rule: the smallest rate at which DLMn c-f enters the measured
2-12 Hz band while DVMn stays in band. The proprioceptive loop runs at its anchor load.
  L5  DLMn c-f in 2-12 Hz with DNg02 drive at the rule-chosen rate
  L6  DVMn 1a-c still in 2-12 Hz under the same drive (the command does not saturate power output)

  REPORTED (not scored): b1 phase locking (vector strength), untestable while afferent phase
  is uniform by assumption; DNp31 rate; the per-type sign split; closed-loop behaviour; and
  the DLM gating diagnostic (do DLMn c-f's excitatory relays fire at all, and do the
  inhibitory ones fire first).

HOW THE DRIVE ENTERS: the phase-locked spike train is injected into the campaniform afferent
neurons themselves (a suprathreshold kick that makes each one spike on schedule). Everything
downstream then flows through the connectome's own synapses at the declared weight, so the
only thing imposed is "these afferents fire phase-locked at the wingbeat"; no synaptic
strength is invented.

CANNOT CLAIM: DLM/DVM are asynchronous muscles; the model reproduces the motor NEURON rate,
not muscle contraction. Afferent encoding parameters are from crane fly, flesh fly and blowfly.
The load -> recruitment mapping is not measured in any species.

Run:  python benchmarks/flight_loop.py [n_cycles_per_trial] [data_dir]   (default 400 cycles = 2 s)
"""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brian2 import SpikeGeneratorGroup, Synapses, ms, mV, Hz, second
from flycns import load_graph, CNSModel, LIFParams
from flycns.bench import provenance
from flycns.graph import rewire_null, SIGN_MAP

N_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 400
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
OUT = Path("results/flight_loop"); OUT.mkdir(parents=True, exist_ok=True)
WINGBEAT_HZ, JITTER_MS = 202.0, 0.8
LOADS = [0.125, 0.25, 0.3, 0.35, 0.4, 0.5, 1.0]
DNG02_HZ = [10.0, 25.0, 50.0, 100.0]     # swept; no measured rate exists (Namiki 2022 is optogenetic)   # 0.3-0.4 added: DVMn jumps 1.9 -> 18.6 Hz between 0.25 and 0.5
WING_MN = r"^(DLMn|DVMn|b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
POWER = r"^(DLMn|DVMn)"
STEER = r"^(b[123] MN|hg[1-4] MN|i[12] MN|iii[13] MN|tp[12] MN|ps1 MN)"
LEG_MN = r"^(Ti|Fe|Tr|Ta|Co).*MN|MN.*(tibia|femur|trochanter|coxa)"

neurons, edges = load_graph(DATA)
meta = neurons.set_index("bodyId")
t = meta["type"].fillna(""); sub = meta["subclass"].fillna(""); nerve = meta["entryNerve"].fillna("")
aff_wing = meta.index[(sub == "campaniform sensilla") & (nerve == "ADMN")]
aff_halt = meta.index[(sub == "campaniform sensilla") & (nerve == "DMetaN")]
aff = list(aff_wing) + list(aff_halt)
print(f"wing campaniform (ADMN) {len(aff_wing)}, haltere campaniform (DMetaN) {len(aff_halt)}")
if len(aff) < 50:
    raise SystemExit("too few campaniform afferents identified; check entryNerve annotation")

wing = meta.index[t.str.match(WING_MN)]
print(f"wing motor neurons: {len(wing)} across {t[wing].nunique()} types")


def phase_locked_spikes(n_aff, n_cycles, load, rng, t0_ms=0.0):
    """One spike per cycle for a recruited fraction of afferents, uniform phase, gaussian jitter."""
    period = 1000.0 / WINGBEAT_HZ
    n_rec = max(1, int(round(load * n_aff)))
    idx = rng.choice(n_aff, n_rec, replace=False)
    phase = rng.uniform(0, period, size=n_rec)
    cycles = np.arange(n_cycles) * period
    times = (cycles[None, :] + phase[:, None] + rng.normal(0, JITTER_MS, size=(n_rec, n_cycles))).ravel()
    ids = np.repeat(idx, n_cycles)
    keep = times >= 0
    return ids[keep], times[keep] + t0_ms


def run_arm(label, edge_df, load, closed=False, dn_hz=0.0):
    t0 = time.time()
    rng = np.random.default_rng(0)
    p = LIFParams()
    stim = ["DNg02"] if dn_hz > 0 else []
    m = CNSModel(neurons, edge_df, stim, p, electrical=True)        # afferent spikes are injected below
    lif_idx = [m.lif_index[b] for b in aff if b in m.lif_index.index]
    n_aff = len(lif_idx)
    G = m.G
    period = 1000.0 / WINGBEAT_HZ
    pre_ms, dur_ms = 200.0, N_CYCLES * period
    if not closed:
        ids, times = phase_locked_spikes(n_aff, N_CYCLES, load, rng, t0_ms=pre_ms)
        gen = SpikeGeneratorGroup(n_aff, ids, times * ms)
        S = Synapses(gen, G, on_pre="v_post += kick", namespace=dict(kick=8.0 * mV))
        S.connect(i=np.arange(n_aff), j=np.array(lif_idx))
        m.net.add(gen, S)
        m.run(pre_ms)
        if dn_hz > 0:
            m.set_stim_rates(np.full(len(m.stim), dn_hz))
        m.run(dur_ms)
        if dn_hz > 0:
            m.set_stim_rates(np.zeros(len(m.stim)))
        m.run(200)
    else:
        # closed loop: recruitment fraction follows recent power-MN output, updated every 50 ms
        power_ids = set(m.lif_ids[[m.lif_index[b] for b in wing if t[b].startswith(("DLMn", "DVMn")) and b in m.lif_index.index]])
        cur_load, chunk_ms = load, 50.0
        gen = SpikeGeneratorGroup(n_aff, np.array([], dtype=int), np.array([]) * ms)
        S = Synapses(gen, G, on_pre="v_post += kick", namespace=dict(kick=8.0 * mV))
        S.connect(i=np.arange(n_aff), j=np.array(lif_idx))
        m.net.add(gen, S)
        m.run(pre_ms)
        trace = []
        for k in range(int(dur_ms // chunk_ms)):
            t_start = m.t_ms
            ids, times = phase_locked_spikes(n_aff, int(chunk_ms // period) + 1, cur_load, rng, t0_ms=t_start)
            keep = times < t_start + chunk_ms
            gen.set_spikes(ids[keep], times[keep] * ms)
            m.run(chunk_ms)
            sp = m.spike_frame()
            recent = sp[(sp.t_ms >= t_start) & sp.bodyId.isin(power_ids)]
            rate = len(recent) / max(len(power_ids), 1) / (chunk_ms / 1000.0)
            # surrogate body: load tracks power-MN rate relative to the 6 Hz target, bounded
            cur_load = float(np.clip(0.5 + 0.5 * (rate / 6.0), 0.05, 1.0))
            trace.append(dict(t_ms=m.t_ms, power_hz=rate, load=cur_load))
        m.run(200)
    sp = m.spike_frame()
    win = (sp.t_ms >= pre_ms) & (sp.t_ms < pre_ms + dur_ms)
    sp = sp[win]
    dur_s = dur_ms / 1000.0

    def rate_of(mask_types):
        ids = [b for b in wing if mask_types(t[b]) and b in m.lif_index.index]
        if not ids:
            return np.nan, 0
        cnt = sp.bodyId.isin(ids).sum()
        return cnt / len(ids) / dur_s, len(ids)

    power_hz, n_power = rate_of(lambda s: bool(pd.Series([s]).str.match(POWER)[0]))
    steer_hz, n_steer = rate_of(lambda s: bool(pd.Series([s]).str.match(STEER)[0]))
    b1_ids = [b for b in wing if t[b] == "b1 MN" and b in m.lif_index.index]
    b1_hz = sp.bodyId.isin(b1_ids).sum() / max(len(b1_ids), 1) / dur_s
    dn31 = [b for b in meta.index[meta.type == "DNp31"] if b in m.lif_index.index]
    dn31_hz = sp.bodyId.isin(dn31).sum() / max(len(dn31), 1) / dur_s
    leg_ids = meta.index[t.str.match(LEG_MN)]
    leg_hz = sp.bodyId.isin(leg_ids).sum() / max(len(leg_ids), 1) / dur_s if len(leg_ids) else np.nan
    per_type = (sp[sp.bodyId.isin(wing)].assign(ty=lambda d: d.bodyId.map(meta["type"]))
                .groupby("ty").size() / dur_s)
    per_type = {k: round(float(v / max((t[wing] == k).sum(), 1)), 2) for k, v in per_type.items()}
    # phase locking of b1 to the wingbeat: vector strength
    b1_sp = sp[sp.bodyId.isin(b1_ids)].t_ms.values
    vs = float(np.abs(np.mean(np.exp(2j * np.pi * (b1_sp % period) / period)))) if len(b1_sp) > 5 else np.nan
    rec_sp = sp  # keep for diagnostics
    rec = dict(arm=label, load=load, closed=closed, dng02_hz=dn_hz, n_afferents=n_aff, wingbeat_hz=WINGBEAT_HZ,
               power_mn_hz=power_hz, n_power=n_power, steer_mn_hz=steer_hz, n_steer=n_steer,
               b1_hz=b1_hz, b1_vector_strength=vs, dnp31_hz=dn31_hz, leg_mn_hz=leg_hz,
               pop_rate_hz=float(m.population_rate_hz()), per_wing_type_hz=per_type,
               wall_s=round(time.time() - t0))
    if closed:
        rec["load_trace"] = trace
    rec["_spikes"] = rec_sp
    print(f"[{label}] load {load:.2f} DNg02 {dn_hz:>5.0f} Hz | power MN {power_hz:6.2f} Hz | steering MN {steer_hz:6.2f} Hz | "
          f"b1 {b1_hz:6.1f} Hz (VS {vs if vs == vs else 0:.2f}) | DNp31 {dn31_hz:5.1f} Hz | leg MN {leg_hz if leg_hz == leg_hz else 0:.2f} Hz | "
          f"CNS {rec['pop_rate_hz']:.3f} Hz | {rec['wall_s']}s")
    return rec


report = dict(benchmark="flight_loop", n_cycles=N_CYCLES, arms={}, checks={})
for L in LOADS:
    report["arms"][f"open_load_{L}"] = run_arm(f"open_load_{L}", edges, L)

# ---- anchor by rule: smallest load with DVMn 1a-c in the measured band
def dvmn_rate(arm):
    return arm["per_wing_type_hz"].get("DVMn 1a-c", 0.0)
def dlmn_rate(arm):
    return arm["per_wing_type_hz"].get("DLMn c-f", 0.0)
open_arms = [report["arms"][f"open_load_{L}"] for L in LOADS]
in_band = [a for a in open_arms if 2.0 <= dvmn_rate(a) <= 12.0]
anchor = min(in_band, key=lambda a: a["load"]) if in_band else min(open_arms, key=lambda a: abs(dvmn_rate(a) - 6.0))
ANCHOR_LOAD = anchor["load"]
print(f"\nanchor load by rule (smallest with DVMn 1a-c in 2-12 Hz): {ANCHOR_LOAD}"
      + ("" if in_band else "  (no load in band; nearest to 6 Hz used and flagged)"))
report["anchor"] = dict(load=ANCHOR_LOAD, rule="smallest load with DVMn 1a-c in 2-12 Hz", in_band=bool(in_band))
null = run_arm(f"rewired_null_load_{ANCHOR_LOAD}", rewire_null(edges, seed=0), ANCHOR_LOAD)
report["arms"][null["arm"]] = null
closed = run_arm(f"closed_from_{ANCHOR_LOAD}", edges, ANCHOR_LOAD, closed=True)
report["arms"][closed["arm"]] = closed
best = anchor

# ---- DLM gating diagnostic at the anchor: did the excitatory relays onto DLMn c-f fire?
sp = best["_spikes"]
dlm_ids = meta.index[meta.type == "DLMn c-f"]
f = edges[edges.pre.isin(aff)].groupby("post").weight.sum(); relays = f[f >= 20].index
onto = edges[edges.pre.isin(relays) & edges.post.isin(dlm_ids)]
sgn = onto["nt"].str.lower().map(SIGN_MAP).fillna(0)
exc_relays = set(onto[sgn > 0].pre); inh_relays = set(onto[sgn < 0].pre)
dur_s = N_CYCLES / WINGBEAT_HZ
def pop_stats(ids):
    r = sp[sp.bodyId.isin(ids)]
    return dict(n=len(ids), n_active=int(r.bodyId.nunique()), hz_per_cell=float(len(r) / max(len(ids), 1) / dur_s),
                first_spike_ms=float(r.t_ms.min()) if len(r) else None)
report["dlm_gating"] = dict(excitatory_relays=pop_stats(exc_relays), inhibitory_relays=pop_stats(inh_relays),
                            dlmn_cf=pop_stats(set(dlm_ids)),
                            structural=dict(exc_synapses=int(onto[sgn > 0].weight.sum()), inh_synapses=int(onto[sgn < 0].weight.sum()),
                                            direct_from_afferents=int(edges[edges.pre.isin(aff) & edges.post.isin(dlm_ids)].weight.sum())),
                            note=("if excitatory relays are largely silent the gate is a threshold problem in the relay layer; "
                                  "if they fire but inhibitory relays fire earlier/harder the gate is dynamic competition"))
g = report["dlm_gating"]
print(f"DLM gating at anchor: excitatory relays {g['excitatory_relays']['n_active']}/{g['excitatory_relays']['n']} active at "
      f"{g['excitatory_relays']['hz_per_cell']:.1f} Hz (first {g['excitatory_relays']['first_spike_ms']}) | inhibitory relays "
      f"{g['inhibitory_relays']['n_active']}/{g['inhibitory_relays']['n']} active at {g['inhibitory_relays']['hz_per_cell']:.1f} Hz "
      f"(first {g['inhibitory_relays']['first_spike_ms']}) | DLMn c-f {g['dlmn_cf']['hz_per_cell']:.2f} Hz")

# ---- STAGE 2: descending flight command onto the silent relay layer
print("\nSTAGE 2: proprioceptive loop at anchor + DNg02 descending command")
stage2 = []
for hz in DNG02_HZ:
    a = run_arm(f"anchor_plus_DNg02_{hz:.0f}Hz", edges, ANCHOR_LOAD, dn_hz=hz)
    a["dlmn_cf_hz"] = dlmn_rate(a); a["dvmn_hz"] = dvmn_rate(a)
    report["arms"][a["arm"]] = a
    stage2.append(a)
ok2 = [a for a in stage2 if 2.0 <= a["dlmn_cf_hz"] <= 12.0 and 2.0 <= a["dvmn_hz"] <= 12.0]
chosen = min(ok2, key=lambda a: a["dng02_hz"]) if ok2 else None
report["stage2"] = dict(rule="smallest DNg02 rate with DLMn c-f AND DVMn 1a-c both in 2-12 Hz",
                        chosen_dng02_hz=(chosen["dng02_hz"] if chosen else None),
                        sweep=[dict(dng02_hz=a["dng02_hz"], dlmn_cf_hz=a["dlmn_cf_hz"], dvmn_hz=a["dvmn_hz"],
                                    b1_hz=a["b1_hz"], steer_hz=a["steer_mn_hz"], cns_hz=a["pop_rate_hz"]) for a in stage2],
                        source="Namiki et al. 2022 Curr Biol 32:1189-1196: DNg02 activation drives indirect flight muscle motor neurons; rate not measured",
                        connectome=dict(n_dng02=29, onto_dlmn_cf_direct=423, onto_dlm_exc_relays=1060, onto_wing_mn=3670))
print("DNg02 rate rule:", "chosen %.0f Hz" % chosen["dng02_hz"] if chosen else "no rate puts both DLMn c-f and DVMn in band")
if chosen:
    g2 = chosen["_spikes"]
    exc_act = g2[g2.bodyId.isin(exc_relays)].bodyId.nunique(); inh_act = g2[g2.bodyId.isin(inh_relays)].bodyId.nunique()
    report["stage2"]["dlm_relays_with_command"] = dict(excitatory_active=int(exc_act), of=len(exc_relays),
                                                      inhibitory_active=int(inh_act), of_inh=len(inh_relays))
    print(f"  with command: excitatory DLM relays active {exc_act}/{len(exc_relays)}, inhibitory {inh_act}/{len(inh_relays)}")

steer_real = best["steer_mn_hz"]; steer_null = null["steer_mn_hz"]
report["checks"] = {
    "L1a_DVMn_2_to_12_hz": bool(2.0 <= dvmn_rate(best) <= 12.0),
    "L1b_DLMn_cf_2_to_12_hz": bool(2.0 <= dlmn_rate(best) <= 12.0),
    "L2_b1_0.5_to_1.2_spikes_per_wingbeat": bool(0.5 * WINGBEAT_HZ <= best["b1_hz"] <= 1.2 * WINGBEAT_HZ),
    "L3_leg_mn_not_entrained": bool((best["leg_mn_hz"] if best["leg_mn_hz"] == best["leg_mn_hz"] else 0) < 0.1 * WINGBEAT_HZ),
    "L4_steering_specific_vs_null": bool(steer_real > 5.0 * max(steer_null, 0.2)),
    "L5_DLMn_cf_2_to_12_hz_with_DNg02": bool(chosen is not None),
    "L6_DVMn_still_in_band_with_DNg02": bool(chosen is not None and 2.0 <= chosen["dvmn_hz"] <= 12.0),
}
report["reported"] = dict(
    b1_vector_strength=best["b1_vector_strength"],
    b1_phase_locking_note="uniform afferent phase by assumption; no Drosophila phase map exists, so locking is untestable here",
    dnp31_hz=best["dnp31_hz"],
    per_type_hz_at_anchor=best["per_wing_type_hz"],
    sign_split_prediction=dict(predicted_inhibited=["tp1 MN", "ps1 MN", "hg3 MN", "hg4 MN", "hg2 MN", "b3 MN", "iii3 MN"],
                               predicted_excited=["iii1 MN", "b2 MN", "i1 MN", "hg1 MN", "b1 MN", "i2 MN", "DLMn c-f", "DVMn 1a-c"]),
    closed_loop=dict(final_load=closed["load_trace"][-1]["load"] if closed.get("load_trace") else None,
                     saturated=bool(closed.get("load_trace") and closed["load_trace"][-1]["load"] >= 0.99),
                     note="the surrogate body maps power output monotonically to load, which is positive feedback by construction; saturation reflects that choice, not the biology"),
    afferent_params_cross_species="Holorusia (Fox & Daniel 2008; Fox et al. 2010), Sarcophaga (Yarger & Fox 2018), Calliphora (Fayyazuddin & Dickinson 1996)")
for a in report["arms"].values():
    a.pop("_spikes", None)
report["pass"] = all(report["checks"].values())
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float))
print("\nCHECKS")
for k, v in report["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
if chosen:
    print(f"STAGE 2  DNg02 {chosen['dng02_hz']:.0f} Hz: DLMn c-f {chosen['dlmn_cf_hz']:.1f} Hz, DVMn {chosen['dvmn_hz']:.1f} Hz, "
          f"b1 {chosen['b1_hz']:.0f} Hz, steering {chosen['steer_mn_hz']:.0f} Hz, CNS {chosen['pop_rate_hz']:.3f} Hz")
print(f"\nREPORTED  anchor load {ANCHOR_LOAD} | DVMn {dvmn_rate(best):.1f} Hz DLMn c-f {dlmn_rate(best):.2f} Hz | b1 {best['b1_hz']:.0f} Hz VS {best['b1_vector_strength'] or 0:.2f} | "
      f"DNp31 {best['dnp31_hz']:.1f} Hz | closed loop saturated={report['reported']['closed_loop']['saturated']}")
print(f"\nBENCHMARK {'PASS' if report['pass'] else 'FAIL'}  -> {OUT / 'report.json'}")
