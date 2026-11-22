"""
Generation 7: the synapse model on the male data (docs/gen7_synapse_model_DRAFT.md; the section "Definitions fixed
before registering", D1-D8, is the plan and wins over anything else in that file).

Phase A ended in outcome C: no setting of the reset rule or of MN9_R's input gives a synaptic scale that is both
functional and stable, and the blind-drive loop sits in the antennal lobe's own recurrent synapses
(results/gen6_phaseA/phaseA.json). This generation changes the synapse model, under ONE registration:

  sweep arms   17 arm sets x {sugar, blind} x w_scale {0.4 .. 1.0}, 10 trials each (D2). Every arm set uses the
               generation-6 settings (v-only reset, MN9_R as in the data) and differs only in
                 synapse   current-based (as before) | conductance-based (E_e 0 mV, E_i -70 mV, tau_i 5 ms)
                 STD       none | "in" (ORN -> antennal-lobe PN/LN) | "al" (those and PN/LN -> PN/LN) | "all"
                 fix       "unclear" connections signed by the sender's predicted transmitter (off in P0 only)
               P0 is the positive control (must replicate phase A's cell 1); B is the baseline; S-in, C and
               CS-in decide; the rest are reported and can never be adopted.
  V7a          report-only validation: the ORN -> PN input-output curve of four glomeruli against Olsen et al.
               2010's fits, for six arm sets at each w (D7).
  conditional  top-ups (10 more trials of both drives at one (arm set, w)), the dt 0.05 ms repeat of the candidate
               and that repeat's own top-up, each run only when the scorer names it (D3, D6).

Scoring is fit/gen7_synapse_score.py. Both files, and fit/gen6_phaseA.py (whose drives, sweep protocol and readouts
are used here unchanged), are hashed into this registration.

    python fit/gen7_synapse.py parts                         the cloud jobs and their arms
    python fit/gen7_synapse.py part <part>                   run one job's arms, in parallel processes
    python fit/gen7_synapse.py arm <arm> [data_dir] [trials] run one arm; a data_dir other than "data" or a trial
                                                             override is a SMOKE run, written under
                                                             results/gen7_synapse/smoke/ and never scored
    python fit/gen7_synapse.py preflight [data_dir]          no simulation: what the fix, the depression scopes and
                                                             the V7a mapping are on the given data; writes
                                                             results/gen7_synapse/preflight.json (run on the pinned
                                                             data and committed before registering)
    python fit/gen7_synapse.py probe                         the preflight, then four arms built with 0 trials (no
                                                             simulation): build time and memory on this machine, and
                                                             P0's network against phase A's; the cloud job g7-preflight
    python fit/gen7_synapse.py selftest                      the marking rule, the curve fit and the design, with
                                                             exact checks; then a few arms on a hand-made network

A smoke arm (and parts, preflight, probe, selftest) reads and writes no registration.
"""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns import registry  # noqa: E402
from flycns.integrity import require_clean, require_data, refuse_overrides  # noqa: E402

LABEL = "gen7_synapse"
OUT = ROOT / "results" / LABEL
SCORE_SCRIPT = ROOT / "fit" / "gen7_synapse_score.py"
PHASEA_SCRIPT = ROOT / "fit" / "gen6_phaseA.py"


def _load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Phase A's script under a name that is not its own: no registration is read or written by the import. Its drives,
# sweep trial, readouts, seeds, grid and thresholds are used as they are (D1); the file is hashed into this
# registration, so a change there is a changed registration here.
PA = _load_module("gen6_phaseA_design", PHASEA_SCRIPT)
GRID_W, DRIVES, _w = PA.GRID_W, PA.DRIVES, PA._w
SEED_BASE, TOPUP_BASE, V7A_BASE = PA.SEED_BASE, PA.TOPUP_BASE, 9000
SWEEP_TRIALS = PA.SWEEP_TRIALS
FLY = dict(PA.FLY)                      # generation-6 settings: v-only reset, source stimulation, euler, adaptation
DT_MS, DT_CHECK_MS = 0.1, 0.05
E_EXC_MV, E_INH_MV, TAU_INH_MS = 0.0, -70.0, 5.0
STD_F, STD_TAU_MS = 0.78, 893.0         # Nagel et al. 2015 (primary)
STD_KW_F, STD_KW_TAU_MS = 0.72, 2400.0  # Kazama & Wilson 2009 (sensitivity)
NUMERICS_MARGIN_MV = 1.0                # D6: lowest v below E_i - 1 mV is a numerics FAIL

# D2. The 17 arm sets. std: "off" | "in" | "al" | "all". Keys beyond synapse/std/unclear override SimOptions.
SETS = {
    "p0":       dict(synapse="current", std="off", unclear="dropped", role="control"),
    "b":        dict(synapse="current", std="off", unclear="predicted", role="baseline"),
    "sin":      dict(synapse="current", std="in", unclear="predicted", role="deciding"),
    "c":        dict(synapse="conductance", std="off", unclear="predicted", role="deciding"),
    "csin":     dict(synapse="conductance", std="in", unclear="predicted", role="deciding"),
    "sal":      dict(synapse="current", std="al", unclear="predicted", role="reported"),
    "csal":     dict(synapse="conductance", std="al", unclear="predicted", role="reported"),
    "sall":     dict(synapse="current", std="all", unclear="predicted", role="reported"),
    "csall":    dict(synapse="conductance", std="all", unclear="predicted", role="reported"),
    "cei55":    dict(synapse="conductance", std="off", unclear="predicted", role="sensitivity", of="c", e_inh_mV=-55.0),
    "cei80":    dict(synapse="conductance", std="off", unclear="predicted", role="sensitivity", of="c", e_inh_mV=-80.0),
    "cti10":    dict(synapse="conductance", std="off", unclear="predicted", role="sensitivity", of="c", tau_inh_ms=10.0),
    "csinei55": dict(synapse="conductance", std="in", unclear="predicted", role="sensitivity", of="csin", e_inh_mV=-55.0),
    "csinei80": dict(synapse="conductance", std="in", unclear="predicted", role="sensitivity", of="csin", e_inh_mV=-80.0),
    "csinti10": dict(synapse="conductance", std="in", unclear="predicted", role="sensitivity", of="csin", tau_inh_ms=10.0),
    "sinkw":    dict(synapse="current", std="in", unclear="predicted", role="sensitivity", of="sin",
                     std_f=STD_KW_F, std_tau_ms=STD_KW_TAU_MS),
    "csinkw":   dict(synapse="conductance", std="in", unclear="predicted", role="sensitivity", of="csin",
                     std_f=STD_KW_F, std_tau_ms=STD_KW_TAU_MS),
}
ORDER = ("sin", "c", "csin")            # D3.3: the first viable of these, in this order, is the candidate
DECISION = ("b",) + ORDER               # the arm sets whose viability enters the outcome: top-ups and the dt repeat
OPTION_KEYS = ("e_inh_mV", "tau_inh_ms", "std_f", "std_tau_ms")

# D7. V7a: Olsen et al. 2010's per-glomerulus fits (R_max, sigma in spikes/s; exponent 1.5), and the MaleCNS types.
V7A = {
    "DM4":  dict(orn="ORN_DM4", pn="DM4_adPN", r_max=170.0, sigma=16.3, compared=True),
    "DL5":  dict(orn="ORN_DL5", pn="DL5_adPN", r_max=167.0, sigma=11.8, compared=True),
    "VM7d": dict(orn="ORN_VM7d", pn="VM7d_adPN", r_max=163.0, sigma=12.4, compared=True),    # Olsen's "VM7"
    "DM1":  dict(orn="ORN_DM1", pn="DM1_lPN", r_max=144.0, sigma=44.8, compared=True),
    "VM7v": dict(orn="ORN_VM7v", pn="VM7v_adPN", r_max=163.0, sigma=12.4, compared=False),   # reported beside VM7d
}
V7A_SETS = ("b", "sin", "c", "csin", "sall", "csall")
V7A_RATES = [5.0, 10.0, 20.0, 40.0, 80.0, 120.0]
V7A_MS, V7A_TRIALS, V7A_EXPONENT = 500, 2, 1.5
V7A_RMAX_TOL, V7A_SIGMA_FACTOR = 0.25, 2.0
V7A_SIGMA_GRID = (0.1, 1000.0, 4001)    # sigma is searched on this fixed log grid; R_max is then closed-form

# D3.1. Phase A's cell 1 (results/gen6_phaseA/phaseA.json, registration ff816c1): per w, the five component verdicts
# (FUNCTION, FUNCTION-q, STABILITY a, b, c) and the self-sustained counts (sugar, blind) of 10 trials. P0 must give
# exactly this table. The selftest checks the literal against the committed file.
P, F, U = "PASS", "FAIL", "UNRESOLVED"
EXPECT_C1 = {
    "w040": dict(function=F, function_q=F, stability_a=P, stability_b=P, stability_c=P, self_sustained=[0, 0]),
    "w050": dict(function=F, function_q=F, stability_a=P, stability_b=F, stability_c=U, self_sustained=[0, 7]),
    "w060": dict(function=P, function_q=F, stability_a=F, stability_b=F, stability_c=F, self_sustained=[2, 10]),
    "w080": dict(function=P, function_q=U, stability_a=F, stability_b=F, stability_c=F, self_sustained=[10, 10]),
    "w100": dict(function=P, function_q=U, stability_a=F, stability_b=F, stability_c=F, self_sustained=[10, 10]),
}
COMPONENTS = ("function", "function_q", "stability_a", "stability_b", "stability_c")


def settings_of(s):
    """What an arm of set s is run with, written into the arm's specification."""
    c = SETS[s]
    st = dict(FLY, synapse=c["synapse"], std=c["std"], unclear=c["unclear"],
              e_exc_mV=E_EXC_MV, e_inh_mV=c.get("e_inh_mV", E_INH_MV), tau_inh_ms=c.get("tau_inh_ms", TAU_INH_MS),
              std_f=c.get("std_f", STD_F), std_tau_ms=c.get("std_tau_ms", STD_TAU_MS))
    st.pop("w_scale")
    return st


def _arms():
    arms = {}
    for s in SETS:
        for drive in DRIVES:
            for w in GRID_W:
                i = PA._pair_index(drive, w)
                base = dict(kind="sweep", set=s, drive=drive, w_scale=w, trials=SWEEP_TRIALS, settings=settings_of(s))
                name = f"{s}_{drive}_{_w(w)}"
                arms[name] = dict(seed=SEED_BASE + i, dt_ms=DT_MS, **base)
                if s in DECISION:
                    arms[name + "_topup"] = dict(seed=TOPUP_BASE + i, dt_ms=DT_MS, topup_of=name, **base)
                    arms[name + "_dt005"] = dict(seed=SEED_BASE + i, dt_ms=DT_CHECK_MS, dt_check_of=name, **base)
                    arms[name + "_dt005_topup"] = dict(seed=TOPUP_BASE + i, dt_ms=DT_CHECK_MS,
                                                       dt_check_of=name + "_topup", **base)
    for s in V7A_SETS:
        for w in GRID_W:
            arms[f"v7a_{s}_{_w(w)}"] = dict(kind="v7a", set=s, w_scale=w, trials=V7A_TRIALS, settings=settings_of(s),
                                            seed=V7A_BASE + GRID_W.index(w), dt_ms=DT_MS)
    return arms


ARMS = _arms()
PARTS = {}
for _s in SETS:
    PARTS[f"g7-{_s}"] = [f"{_s}_{d}_{_w(w)}" for d in DRIVES for w in GRID_W]
for _s in V7A_SETS:
    PARTS[f"g7-v7a-{_s}"] = [f"v7a_{_s}_{_w(w)}" for w in GRID_W]
for _s in DECISION:
    for _wv in GRID_W:
        PARTS[f"g7-topup-{_s}-{_w(_wv)}"] = [f"{_s}_{d}_{_w(_wv)}_topup" for d in DRIVES]
        PARTS[f"g7-dt-{_s}-{_w(_wv)}"] = [f"{_s}_{d}_{_w(_wv)}_dt005" for d in DRIVES]
        PARTS[f"g7-dtt-{_s}-{_w(_wv)}"] = [f"{_s}_{d}_{_w(_wv)}_dt005_topup" for d in DRIVES]
assert sorted(a for p in PARTS.values() for a in p) == sorted(ARMS), "every arm in exactly one part"
CONDITIONAL_PARTS = sorted(p for p in PARTS if p.startswith(("g7-topup-", "g7-dt-", "g7-dtt-")))   # only when the scorer asks


CRITERIA = dict(
    question=("on the male CNS: does signing the 'unclear' connections, a conductance-based synapse, short-term "
              "depression of the measured ORN input synapses, or the two together, give a synaptic scale that is both "
              "functional and stable?"),
    plan=("docs/gen7_synapse_model_DRAFT.md: the section 'Definitions fixed before registering' (D1-D8) is the plan "
          "and wins over the text above it"),
    inherits=dict(
        from_registration="results/gen6_phaseA/registration_v5.json (git ff816c1)",
        script="fit/gen6_phaseA.py, hashed into this registration: its drives, sweep trial, readouts and seeds",
        thresholds=dict(PA.CRITERIA["thresholds"]),
        self_sustained=PA.CRITERIA["definitions"]["self_sustained"],
        sweep=PA.CRITERIA["protocol"]["sweep"],
        drives=dict(sugar=PA.CRITERIA["protocol"]["drives"]["sugar"], blind=PA.CRITERIA["protocol"]["drives"]["blind"]),
        grid=GRID_W, flycns=FLY,
        intervals="percentile bootstrap over trials, 2,000 resamples, seed 0 (flycns.stats.bootstrap), also when pooled",
        celltypes=dict(file="data/gen6_phaseA_celltypes.json", sha256=PA.CELLTYPES_SHA256),
        simulator_hash_before="df7e16022378 (generations 5 and 6)"),
    arms=dict(
        sets=SETS, order=list(ORDER), decision_sets=list(DECISION),
        common="every arm: v-only reset, MN9_R as in the data, generation-6 values of every calibration (none refit)",
        synapse=dict(
            current="a spike adds the signed kick n_synapses x 0.275 mV x w x gain to g (generations 1-6)",
            conductance=(f"ge += kick / (E_e - V_rest) for an excitatory connection, gi += |kick| / (V_rest - E_i) for an "
                         f"inhibitory one, so one connection gives the same initial PSP at rest as in the current "
                         f"model; E_e {E_EXC_MV} mV; E_i {E_INH_MV} mV (sensitivity -55, -80); ge decays with tau_syn "
                         f"5 ms, gi with tau_i {TAU_INH_MS} ms (sensitivity 10)"),
            depression=(f"per connection, on recurrent and stimulus-source synapses alike: a spike is delivered with "
                        f"w x A, then A -> f x A; A recovers to 1 with tau_D; f {STD_F}, tau_D {STD_TAU_MS} ms (Nagel "
                        f"et al. 2015); sensitivity f {STD_KW_F}, tau_D {STD_KW_TAU_MS} ms (Kazama & Wilson 2009); the "
                        "per-trial restore returns A to 1")),
        std_scopes=dict(
            off="no synapse depresses",
            **{"in": "pre type starts 'ORN_' and post type is in the ALPN or ALLN list",
               "al": "pre type starts 'ORN_' or is in the ALPN or ALLN list, and post type is in the ALPN or ALLN list",
               "all": "every chemical synapse"},
            note="'al' and 'all' extrapolate the ORN -> PN measurement; arm sets that use them are never adopted"),
        fix=("unclear='predicted' (flycns.graph.load_graph): a connection whose transmitter is 'unclear' takes its "
             "presynaptic cell's predictedNt; it stays dropped when that is unclear, missing or an amine. Off in P0"),
        not_run="E_e +/-10 mV, tau_e 2 ms, V7b"),
    protocol=dict(
        seeds=(f"sweep arms {SEED_BASE} + index(drive, w), phase A's, in every arm set (all arms paired with each other "
               f"and with phase A); top-ups {TOPUP_BASE} + the same index; the dt repeat uses its main arm's seed; V7a "
               f"{V7A_BASE} + index(w), the same in every V7a arm set"),
        dt=f"{DT_MS} ms; the candidate's repeat {DT_CHECK_MS} ms",
        recorded_per_trial=("phase A's sweep readouts, and: orn_spikes (spikes of simulated cells whose type starts "
                            "'ORN_', whole trial), lowest_v_mV (conductance arms: the lowest v reached by any cell "
                            "without spike-triggered adaptation or electrical coupling; flycns.model lowest_v_mV)")),
    decision=dict(
        viable=("a grid w at which FUNCTION (screen), FUNCTION-q and STABILITY (a), (b), (c) all PASS, as phase A; in a "
                "conductance arm also NUMERICS; the decision w is the smallest such w"),
        numerics=(f"conductance arms: FAIL iff lowest_v_mV in any sugar or blind trial at that w is not a number or below "
                  f"E_i - {NUMERICS_MARGIN_MV} mV (for the cells it covers dv/dt > 0 at v = E_i, so a lower value can "
                  "only come from the integration step); a conductance arm without the record refuses scoring"),
        order=["R: P0's table (five component verdicts and the two self-sustained counts per w) differs from "
               "EXPECT_C1: stop for review, nothing adopted",
               "F: B is viable: the candidate is the fix alone, at B's smallest viable w",
               "else the first viable of S-in, C, CS-in (by arm set first, then the smallest w): the candidate",
               "C7: none viable"],
        expect_c1=EXPECT_C1,
        laterality="reported for every arm set; gates nothing",
        provisional=("a candidate is provisional: it becomes a default only after a confirm step in its own "
                     "registration and a refit of the calibrations under it"),
        top_up=("decision sets (B, S-in, C, CS-in) only. A candidate w (no component FAILs, at least one UNRESOLVED) "
                "that lies below its set's smallest viable w (or in a set with no viable w) names 10 more trials of "
                "BOTH drives at that (set, w), seeds 7000 + index, judged on the main arms alone. Through the outcome "
                "order, up to and including the first set that is already viable, a named top-up can change the "
                "outcome: while one of those is missing the outcome is PROVISIONAL. In a later set a top-up is named "
                "only if the set has no viable w (its hypothesis verdict rests on it); it does not hold the outcome. "
                "Whether a still-missing top-up holds the outcome is judged again, by the same rule, after pooling the "
                "top-ups that were run (a top-up that made an earlier set viable releases the later ones). "
                "The 10 + 10 trials are pooled for every component; a top-up counts only if both drives were run, "
                "otherwise scoring is refused; after it UNRESOLVED counts as not "
                "passing"),
        dt_check=(f"the candidate's arms at its decision w are repeated at dt {DT_CHECK_MS} ms with the same seeds (the "
                  "Poisson input is drawn per time step, so the repeat is also a new draw of the input), with as many "
                  "trials as the candidate's verdict rests on: the two main arms, and the two top-up arms too if the "
                  "decision w was reached with a top-up (pooled the same way). Until the repeat has run the outcome is "
                  "PROVISIONAL and the candidate's arm set is undetermined for the hypothesis verdicts. If a component "
                  "verdict of the repeat differs from the candidate's (which are all PASS), whatever the cause, the "
                  "candidate is flagged numerics-sensitive, the outcome is not final and the arm set stays "
                  "undetermined: stop for review. Only the candidate is repeated: another viable arm set is not "
                  "checked at the smaller step"),
        identical_rows=("a top-up or a dt repeat whose trial rows equal its main arm's, when that arm is not silent, is "
                        "flagged (different seeds or steps cannot give identical rows unless nothing spikes)"),
        codes="R, F, sin, c, csin (the candidate's arm set), C7",
        not_adoptable=("a reported or sensitivity arm set that is viable is listed with the label 'extrapolated: never "
                       "adopted' or 'sensitivity: never adopted'"),
        missing_arm="a missing or crashed registered arm refuses scoring: it fails safe, never PASS"),
    hypotheses={
        "H7-P": ["P0 replicates phase A's cell 1", "held", "high"],
        "H7-F": ["the fix alone gives a viable w (B)", "not held", "high"],
        "H7a": ["conductance-based synapses alone give a viable w (C; the E_i variants are reported beside it)",
                "not held", "moderate"],
        "H7b": ["slower inhibition (tau_i 10 ms) gives a viable w where 5 ms does not (C at tau_i 10 against C)",
                "not held", "moderate"],
        "H7c-in": ["depression of the ORN input synapses alone gives a viable w (S-in)", "not held", "high"],
        "H7d": ["conductance-based with input depression gives a viable w where neither C nor S-in does (CS-in)",
                "not held", "moderate"],
        "H7c-al": ["(reported) depression of the antennal-lobe synapses gives a viable w (S-al or CS-al)", "held", "low"],
        "H7c-all": ["(reported) depression of every synapse gives a viable w (S-all or CS-all)", "held", "low"],
        "overall": ["the outcome is C7", "held", "moderate"]},
    hypothesis_verdicts=("held, not held or undetermined. An arm set is 'viable' if some w is; 'not viable' if every w "
                         "has a FAIL or stayed UNRESOLVED after its top-up; otherwise (an UNRESOLVED w without a "
                         "top-up: a missing named top-up, or a reported arm set, which gets none) 'undetermined'. "
                         "Under outcome R every verdict but H7-P's is undetermined. An uncorrected screen (phase A's M6)"),
    validation=dict(
        v7a=dict(
            status="report-only: no verdict enters the outcome",
            sets=list(V7A_SETS), glomeruli=V7A, rates_hz=V7A_RATES, ms=V7A_MS, trials=V7A_TRIALS,
            drive=("every cell of the five ORN types is a Poisson source; per glomerulus, rate and trial: restore, the "
                   "glomerulus's ORN sources at the rate and all others at 0 for 500 ms; readout: the mean rate of the "
                   "PN type's simulated cells over the same 500 ms, mean over the trials"),
            fit=(f"R = R_max r^n / (r^n + sigma^n), n = {V7A_EXPONENT} fixed: least squares over sigma on a log grid "
                 f"({V7A_SIGMA_GRID[0]} to {V7A_SIGMA_GRID[1]} spikes/s, {V7A_SIGMA_GRID[2]} points) with R_max >= 0 in "
                 "closed form; no PN spike at any rate: R_max 0, sigma undefined"),
            consistent=(f"per compared glomerulus: R_max within +/-{V7A_RMAX_TOL:.0%} and sigma within a factor of "
                        f"{V7A_SIGMA_FACTOR:g} of Olsen et al. 2010's fit, and sigma not at an edge of the grid"),
            source="Olsen, Bhandawat & Wilson 2010, Methods (docs/lit/v7a_nagel_check_2026-10-18.md)",
            reported=("the fits, the model's rates beside Olsen's FITTED curve at the six rates (the paper's data points "
                      "are not tabulated), the RMS residual of the model's fit, whether the model's rates rise "
                      "monotonically, and for conductance arms the lowest v"),
            limits=("not the paper's quantities, only the same window length: Olsen's ORN and PN responses are "
                    "single-cell spike counts in the 500 ms odor period minus the baseline rate of the preceding 500 ms; "
                    "the model's ORN rate is the commanded Poisson rate of every source of the type and its PN rate is "
                    "the mean over the type's cells, both from silence (baseline 0, no spontaneous activity). VM7d is "
                    "compared with Olsen's VM7 (INFERRED: the Or42a glomerulus); only cholinergic uniglomerular PNs "
                    "are read; all five ORN types are sources in every V7a trial (the undriven ones silent); the model "
                    "has no presynaptic inhibition of ORN terminals. 'Consistent' has no goodness-of-fit term")),
        also_reported="per arm set: the AL and LH share of the blind tail (phase A's M9 measure), by-mode summaries"),
    integrity_checks=dict(
        orn_under_sugar=("per sugar trial the ORN spikes are recorded; where S-in's (CS-in's) sugar arm has none at a "
                         "w, its trials are compared with B's (C's) at that w, field by field, and the result reported"),
        cell_counts="each arm records its simulated cell count; the preflight records it with and without the fix",
        p0_rows="P0's trial rows are compared with phase A's cell-1 arm files where present (reported)"),
    scoring="fit/gen7_synapse_score.py, hashed into this registration",
    context=("results/gen7_synapse/preflight.json: the fix, the depression scopes and the V7a mapping on the pinned "
             "data, committed before registering"),
)


# ------------------------------------------------------------------------------------------------ data
def tables(data, unclear):
    """load_graph at the generation-6 settings; P0 makes exactly phase A's call."""
    from flycns.graph import load_graph
    from flycns.integrity import LOADED
    if unclear == "dropped":
        neurons, edges = load_graph(data, min_weight=FLY["floor"], amines=FLY["amines"])
    else:
        neurons, edges = load_graph(data, min_weight=FLY["floor"], amines=FLY["amines"], unclear=unclear)
    info = dict(unclear=unclear, edges=int(len(edges)), synapses=float(edges["weight"].sum()),
                cells=int(len(np.union1d(edges["pre"].unique(), edges["post"].unique()))),
                dropped_unsigned=dict(edges=LOADED.get("n_dropped_unsigned_edges"),
                                      synapses=LOADED.get("n_dropped_unsigned_synapses"),
                                      silent_presynaptic=LOADED.get("n_silent_presynaptic")),
                resigned=(dict(edges=LOADED.get("n_resigned_edges"), synapses=LOADED.get("n_resigned_synapses"),
                               cells=LOADED.get("n_resigned_cells")) if unclear != "dropped" else
                          dict(edges=None, synapses=None, cells=None)))
    return neurons, edges, info


def std_marks(edges, neurons, scope, ct):
    """D2: which connections depress under scope "in" or "al". Returns (boolean array over the edge rows, log).
    Works on per-cell flags looked up by position, so no per-connection string column is built."""
    if scope not in ("in", "al"):
        raise ValueError(f"[gen7] no marking rule for scope {scope!r}")
    n = neurons.drop_duplicates("bodyId")
    ids = n["bodyId"].to_numpy()
    t = n["type"].fillna("").astype(str)
    order = np.argsort(ids, kind="stable")
    ids_s = ids[order]

    def look(col, flag):                          # flag: one boolean per row of n -> one per connection
        x = edges[col].to_numpy()
        if not len(ids_s):
            return np.zeros(len(x), dtype=bool)
        pos = np.minimum(np.searchsorted(ids_s, x), len(ids_s) - 1)
        return (ids_s[pos] == x) & flag[order][pos]
    is_orn = t.str.startswith("ORN_").to_numpy()
    is_pn, is_ln = t.isin(set(ct["ALPN"])).to_numpy(), t.isin(set(ct["ALLN"])).to_numpy()
    pre_orn, pre_al = look("pre", is_orn), look("pre", is_pn | is_ln)
    post_pn, post_ln = look("post", is_pn), look("post", is_ln)
    post_al = post_pn | post_ln
    m = (pre_orn & post_al) if scope == "in" else ((pre_orn | pre_al) & post_al)
    w = edges["weight"].to_numpy()
    part = lambda k: dict(edges=int(k.sum()), synapses=float(w[k].sum()))     # noqa: E731
    marked_orn = np.unique(edges["pre"].to_numpy()[pre_orn & m])
    log = dict(scope=scope, **part(m), of_edges=int(len(edges)), of_synapses=float(w.sum()),
               orn_to_pn=part(pre_orn & post_pn), orn_to_ln=part(pre_orn & post_ln), al_to_al=part(pre_al & post_al),
               orn_types=int(t[np.isin(ids, np.unique(edges["pre"].to_numpy()[pre_orn]))].nunique()),
               orn_cells_marked=int(len(marked_orn)))
    return m, log


def sim_options(st):
    from flycns.model import SimOptions
    if st["synapse"] == "current" and st["std"] == "off":      # P0 and B: exactly phase A's options object
        return PA._opt(st)
    kw = dict(reset=st["reset"], stimulation=st["stimulation"], integration=st["integration"],
              adaptation=st["adaptation"], synapse=st["synapse"],
              std={"off": "off", "in": "marked", "al": "marked", "all": "all"}[st["std"]])
    if st["synapse"] == "conductance":
        kw.update(e_exc_mV=st["e_exc_mV"], e_inh_mV=st["e_inh_mV"], tau_inh_ms=st["tau_inh_ms"])
    if st["std"] != "off":
        kw.update(std_f=st["std_f"], std_tau_ms=st["std_tau_ms"])
    return SimOptions(**kw)


def build(neurons, edges, stim_types, st, w, seed, dt_ms):
    from flycns.model import CNSModel, LIFParams
    par = LIFParams(w_scale=w, seed=seed) if dt_ms == DT_MS else LIFParams(w_scale=w, seed=seed, dt_ms=dt_ms)
    m = CNSModel(neurons, edges, stim_types, par, electrical=st["electrical"], options=sim_options(st))
    m.store()
    return m


def prepared(spec, data_dir, smoke):
    """The arm's tables: the edges as its arm set loads and marks them."""
    st = spec["settings"]
    neurons, edges, info = tables(data_dir, st["unclear"])
    mlog = None
    if st["std"] in ("in", "al"):
        ct, _ = PA.celltypes(check=not smoke)
        mask, mlog = std_marks(edges, neurons, st["std"], ct)
        if not smoke and not mask.any():
            raise SystemExit(f"[gen7] depression scope {st['std']!r} marks no connection on the pinned data")
        edges = edges.assign(std=mask)
    return neurons, edges, info, mlog


# ------------------------------------------------------------------------------------------------ V7a
def hill(r, r_max, sigma, n=V7A_EXPONENT):
    r = np.asarray(r, dtype=float)
    return r_max * r ** n / (r ** n + sigma ** n)


def hill_fit(rates, y):
    """D7: least squares of R_max r^n / (r^n + sigma^n), n fixed, over a fixed sigma grid; R_max >= 0 closed-form."""
    r, y = np.asarray(rates, dtype=float), np.asarray(y, dtype=float)
    if not np.any(y > 0):
        return dict(r_max=0.0, sigma=None, sse=float((y ** 2).sum()), at_bound=False, note="no PN spike at any rate")
    lo, hi, k = V7A_SIGMA_GRID
    grid = np.logspace(np.log10(lo), np.log10(hi), k)
    f = r[None, :] ** V7A_EXPONENT / (r[None, :] ** V7A_EXPONENT + grid[:, None] ** V7A_EXPONENT)
    rm = np.maximum((f * y).sum(axis=1) / (f * f).sum(axis=1), 0.0)
    sse = ((rm[:, None] * f - y) ** 2).sum(axis=1)
    i = int(np.argmin(sse))
    return dict(r_max=float(rm[i]), sigma=float(grid[i]), sse=float(sse[i]), at_bound=bool(i in (0, k - 1)))


def v7a_consistent(fit, g):
    if fit["sigma"] is None or fit["at_bound"]:
        return False
    ref = V7A[g]
    return bool(abs(fit["r_max"] - ref["r_max"]) <= V7A_RMAX_TOL * ref["r_max"]
                and ref["sigma"] / V7A_SIGMA_FACTOR <= fit["sigma"] <= ref["sigma"] * V7A_SIGMA_FACTOR)


def run_v7a(m, neurons, edges, smoke, t0, name):
    meta = neurons.drop_duplicates("bodyId").set_index("bodyId")
    stim_type = m.stim["type"].to_numpy()
    stim_ids = m.stim["bodyId"].to_numpy()
    out_of = set(edges["pre"])
    rows, cells = [], {}
    for g, ref in V7A.items():
        src = stim_type == ref["orn"]
        pn = np.array(sorted(int(b) for b in meta.index[meta["type"] == ref["pn"]] if b in m.lif_index.index),
                      dtype="int64")
        cells[g] = dict(orn_cells=int(src.sum()), orn_with_output=int(sum(int(b) in out_of for b in stim_ids[src])),
                        pn_cells=int(len(pn)), pn_ids=[int(b) for b in pn])
        if not src.any() or not len(pn):
            if not smoke:
                raise SystemExit(f"[gen7] V7a {g}: {int(src.sum())} {ref['orn']} sources and {len(pn)} simulated "
                                 f"{ref['pn']} cells on the pinned data; the mapping is not what the plan describes")
            continue
        for r in V7A_RATES:
            for k in range(m._v7a_trials):
                m.restore()
                m.set_stim_rates(np.where(src, r, 0.0))
                m.run(V7A_MS)
                sp = m.spike_frame()
                per = [float((sp.bodyId == b).sum() / (V7A_MS / 1000.0)) for b in pn]
                rows.append(dict(glomerulus=g, orn_hz=r, k=k, pn_hz=float(np.mean(per)), pn_per_cell_hz=per,
                                 n_spikes=int(len(sp)), n_active=int(sp.bodyId.nunique()),
                                 lowest_v_mV=m.lowest_v_mV()))
        print(f"[gen7] {name} {g} done ({time.time() - t0:.0f} s)", flush=True)
    return rows, cells


# ------------------------------------------------------------------------------------------------ arms
def run_arm(name, data_dir="data", trials=None, out_dir=None):
    from flycns.bench import provenance
    from flycns.graph import _dominant_roi
    spec = ARMS[name]
    st, w = spec["settings"], spec["w_scale"]
    reduced = data_dir != "data" or (trials is not None and trials != spec["trials"]) or out_dir is not None
    n_trials = trials if trials is not None else spec["trials"]
    out_dir = Path(out_dir) if out_dir is not None else OUT / ("smoke" if reduced else "arms")
    t0 = time.time()
    if not reduced:
        require_data(data_dir, LABEL, ["neurons.parquet", "edges.parquet", "roi_membership.parquet"])
    neurons, edges, info, mlog = prepared(spec, data_dir, smoke=reduced)
    roi = _dominant_roi(data_dir)
    hz = pool = None
    if spec["kind"] == "sweep":
        if spec["drive"] == "blind":
            stim_types, driven, pool = PA.male_blind_pool(neurons)
        else:
            stim_types = list(PA.MALE_SUGAR)
            driven = set(int(b) for b in neurons.loc[neurons["type"].isin(stim_types), "bodyId"])
        hz = PA.BLIND_HZ if spec["drive"] == "blind" else PA.SUGAR_HZ
    else:
        present = set(neurons["type"].dropna())
        stim_types = [v["orn"] for v in V7A.values() if v["orn"] in present]
        if not stim_types:
            raise SystemExit("[gen7] V7a: none of the ORN types is in the data")
    m = build(neurons, edges, stim_types, st, w, spec["seed"], spec["dt_ms"])
    exclude = set(int(b) for b in m.stim["bodyId"])
    rows, extra = [], {}
    if spec["kind"] == "sweep":
        b = m.stim["bodyId"].to_numpy()
        rates = np.where(np.isin(b, list(driven)), hz, 0.0)
        groups = PA._groups(m, exclude, roi)
        t_of = m.meta["type"].reindex(m.lif_ids).fillna("").astype(str)
        orn_ids = set(int(x) for x in np.asarray(m.lif_ids)[t_of.str.startswith("ORN_").to_numpy()])
        for k in range(n_trials):
            row = PA.run_sweep_trial(m, rates, exclude, groups)
            row["orn_spikes"] = int(m.spike_frame().bodyId.isin(orn_ids).sum())
            row["lowest_v_mV"] = m.lowest_v_mV()
            rows.append(dict(k=k, **row))
            print(f"[gen7] {name} {k + 1}/{n_trials} ({time.time() - t0:.0f} s)", flush=True)
        extra = dict(n_driven=int((rates > 0).sum()), total_input_hz=float(rates.sum()), group_sizes=groups[1],
                     n_orn_simulated=int(len(orn_ids)), pool=pool, drive_hz=hz)
    else:
        m._v7a_trials = n_trials
        rows, cells = run_v7a(m, neurons, edges, reduced, t0, name)
        extra = dict(v7a_cells=cells)
    rec = dict(arm=name, spec=spec, options=dict(m.options.__dict__), reduced=reduced, data_dir=str(data_dir),
               n_lif=int(len(m.lif_ids)), n_recurrent=int(m.n_chem), n_stimulated=int(len(exclude)),
               n_std_syn=int(m.n_std_syn), std_marks=mlog, graph=info, **extra,
               peak_memory_mb=_peak_mb() if reduced else None,
               wall_s=round(time.time() - t0, 1), trials=rows,
               registration=registry.stamp(REG) if REG else None, provenance=provenance(data_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(rec, indent=1, default=float), encoding="utf-8")
    print(f"[gen7] {name}: {len(rows)} runs in {rec['wall_s']} s -> {out_dir / (name + '.json')}"
          + ("   (SMOKE: not a result)" if reduced else ""))
    return rec


def run_part(part, parallel=2):
    arms = PARTS[part]
    (OUT / "arms").mkdir(parents=True, exist_ok=True)
    procs, failed = [], []
    for a in arms:
        while len([p for p in procs if p[1].poll() is None]) >= parallel:
            time.sleep(5)
        log = open(OUT / "arms" / f"{a}.log", "w", encoding="utf-8")
        procs.append((a, subprocess.Popen([sys.executable, __file__, "arm", a], stdout=log, stderr=subprocess.STDOUT,
                                          cwd=ROOT)))
    for a, p in procs:
        if p.wait() != 0:
            failed.append(a)
    for a in arms:
        print(f"--- {a}\n" + "".join((OUT / "arms" / f"{a}.log").read_text(encoding="utf-8").splitlines(True)[-5:]))
    if failed:
        raise SystemExit(f"[gen7] {part}: arms failed: {failed}")
    print(f"done: {part} ({len(arms)} arms)")


# ------------------------------------------------------------------------------------------------ preflight
def _peak_mb():
    """Peak memory of this process in MB, best effort (None if it cannot be read). Used in smoke and probe runs only."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                    (k, ctypes.c_size_t) for k in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                                   "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                                   "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
            c = Counters()
            c.cb = ctypes.sizeof(Counters)
            kernel, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
                return None
            return round(c.PeakWorkingSetSize / 2 ** 20, 1)
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:
        return None


PROBE_ARMS = ("p0_sugar_w040", "sin_blind_w100", "csall_blind_w100", "v7a_csall_w100")


def probe(data_dir="data"):
    """The preflight, then PROBE_ARMS built with 0 trials, each in its own process: no simulation, so nothing that
    could be scored. Records build time and peak memory on this machine, and checks that P0's network is phase A's
    (cell and synapse counts of results/gen6_phaseA/arms/c1_sugar_w040.json). Exits 1 if it is not."""
    smoke = data_dir != "data"
    preflight(data_dir)
    out = dict(data_dir=str(data_dir), arms={})
    for a in PROBE_ARMS:
        t0 = time.time()
        r = subprocess.run([sys.executable, __file__, "arm", a, data_dir, "0"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        f = OUT / "smoke" / f"{a}.json"
        if r.returncode or not f.exists():
            print((r.stdout or "")[-1500:] + (r.stderr or "")[-3000:])
            raise SystemExit(f"[gen7] probe: {a} did not build (exit {r.returncode})")
        rec = json.loads(f.read_text(encoding="utf-8"))
        out["arms"][a] = dict(wall_s=round(time.time() - t0, 1), peak_memory_mb=rec.get("peak_memory_mb"),
                              n_lif=rec["n_lif"], n_recurrent=rec["n_recurrent"], n_stimulated=rec["n_stimulated"],
                              n_std_syn=rec["n_std_syn"], std_marks=rec.get("std_marks"), v7a_cells=rec.get("v7a_cells"))
        print(f"[gen7] probe {a}: {out['arms'][a]['wall_s']} s, peak {out['arms'][a]['peak_memory_mb']} MB, "
              f"{rec['n_lif']} cells, {rec['n_recurrent']} recurrent synapses, {rec['n_std_syn']} depressing", flush=True)
    ref = ROOT / "results" / "gen6_phaseA" / "arms" / "c1_sugar_w040.json"
    ok = None
    if not smoke and not ref.exists():
        raise SystemExit(f"[gen7] probe: {ref.relative_to(ROOT)} is missing, so P0's network cannot be checked")
    if not smoke:
        old = json.loads(ref.read_text(encoding="utf-8"))
        got = out["arms"]["p0_sugar_w040"]
        ok = bool((got["n_lif"], got["n_recurrent"], got["n_stimulated"]) == (old["n_lif"], old["n_recurrent"], old["n_stimulated"]))
        out["p0_network_is_phase_a"] = dict(ok=ok, phase_a=dict(n_lif=old["n_lif"], n_recurrent=old["n_recurrent"],
                                                                n_stimulated=old["n_stimulated"]))
    f = (OUT / "smoke" / "probe.json") if smoke else (OUT / "probe.json")
    f.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    if ok is False:
        raise SystemExit(f"[gen7] probe: P0's network is not phase A's: {out['p0_network_is_phase_a']} against {got}")
    print(f"done: probe ({len(PROBE_ARMS)} arms built, P0 network equals phase A's: {ok}) -> {f.relative_to(ROOT)}")
    return out


def preflight(data_dir="data"):
    """What the fix, the depression scopes and the V7a mapping are on the given data, without simulating. Its numbers
    go into the registration's context; a scope that marks nothing, or a V7a type without cells, shows here."""
    smoke = data_dir != "data"
    if not smoke:
        require_data(data_dir, LABEL, ["neurons.parquet", "edges.parquet", "roi_membership.parquet"])
    ct, ctrec = PA.celltypes(check=not smoke)
    import gc
    _, e0, off = tables(data_dir, "dropped")       # one table in memory at a time: keep only its pairs and cells
    old = e0[["pre", "post"]].drop_duplicates().assign(old=True)
    cells0 = np.union1d(e0["pre"].unique(), e0["post"].unique())
    del e0, _
    gc.collect()
    neurons, edges, on = tables(data_dir, "predicted")
    meta = neurons.drop_duplicates("bodyId").set_index("bodyId")
    cells1 = np.union1d(edges["pre"].unique(), edges["post"].unique())
    now = edges[["pre", "post"]]
    new = edges[now.merge(old, on=["pre", "post"], how="left")["old"].isna().to_numpy()]
    removed = int(old.merge(now.drop_duplicates().assign(now=True), on=["pre", "post"], how="left")["now"].isna().sum())
    del old, now
    gc.collect()
    out = dict(data_dir=str(data_dir), celltypes=dict(sha256=PA.sha256(PA.CELLTYPES), registered=PA.CELLTYPES_SHA256,
                                                      counts=ctrec["counts"]),
               fix=dict(without=off, with_fix=on, cells_added=int(len(np.setdiff1d(cells1, cells0))),
                        cells_removed=int(len(np.setdiff1d(cells0, cells1))), connections_added=int(len(new)),
                        connections_removed=removed,
                        added_excitatory=dict(edges=int((new["sign"] > 0).sum()),
                                              synapses=float(new.loc[new["sign"] > 0, "weight"].sum())),
                        added_inhibitory=dict(edges=int((new["sign"] < 0).sum()),
                                              synapses=float(new.loc[new["sign"] < 0, "weight"].sum())),
                        added_by_transmitter={str(k): float(v) for k, v in
                                              new.groupby(new["nt"].astype(str))["weight"].sum().items()}
                        if "nt" in new else None))
    out["std_scopes"] = {s: std_marks(edges, neurons, s, ct)[1] for s in ("in", "al")}
    t = meta["type"].fillna("").astype(str)
    orn = t[t.str.startswith("ORN_")]
    out["orn"] = dict(types=int(orn.nunique()), cells=int(len(orn)), simulated=int(orn.index.isin(cells1).sum()))
    v7a = {}
    for g, ref in V7A.items():
        o = meta.index[meta["type"] == ref["orn"]]
        p = meta.index[meta["type"] == ref["pn"]]
        into = edges[edges["post"].isin(p)]
        own = into[into["pre"].isin(o)]
        v7a[g] = dict(orn_type=ref["orn"], orn_cells=int(len(o)), orn_with_output=int(o.isin(edges["pre"]).sum()),
                      pn_type=ref["pn"], pn_cells=int(len(p)), pn_simulated=int(p.isin(cells1).sum()),
                      orn_to_pn=dict(edges=int(len(own)), synapses=float(own["weight"].sum())),
                      pn_input_synapses=float(into["weight"].sum()),
                      own_orn_share=(float(own["weight"].sum() / into["weight"].sum()) if len(into) else None),
                      pn_transmitters=sorted(set(edges.loc[edges["pre"].isin(p), "nt"].astype(str))) if "nt" in edges else None)
    out["v7a"] = v7a
    stim_types, driven, pool = PA.male_blind_pool(neurons)
    d_t = t.reindex(sorted(driven))
    out["drives"] = dict(sugar_cells=int(t.isin(PA.MALE_SUGAR).sum()), blind_pool=pool, blind_driven=int(len(driven)),
                         blind_source_types=int(len(stim_types)), blind_source_cells=int(t.isin(stim_types).sum()),
                         blind_driven_orn=int(d_t.str.startswith("ORN_").sum()),
                         blind_source_orn_types=int(sum(s.startswith("ORN_") for s in stim_types)))
    out["design"] = dict(sets=len(SETS), sweep_arms=sum(1 for a in ARMS.values() if a["kind"] == "sweep"
                                                        and "topup_of" not in a and "dt_check_of" not in a),
                         v7a_arms=sum(1 for a in ARMS.values() if a["kind"] == "v7a"), parts=len(PARTS),
                         conditional_parts=len(CONDITIONAL_PARTS))
    f = (OUT / "smoke" / "preflight.json") if smoke else (OUT / "preflight.json")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1, default=float))
    print(f"[gen7] preflight -> {f.relative_to(ROOT)}")
    return out


# ------------------------------------------------------------------------------------------------ selftest
def toy(d):
    """A hand-made network with every part generation 7 touches: the sugar path to MN9, four glomeruli with ORNs,
    PNs and a local neuron, a sensory pool for the blind drive, and 'unclear' connections for the fix."""
    import pandas as pd
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    rows, bid = [], [1000]

    def add(t, n, sc, nt="acetylcholine", pred=None):
        ids = []
        for k in range(n):
            rows.append(dict(bodyId=bid[0], type=t, superclass=sc, somaSide="LR"[k % 2], consensusNt=nt,
                             predictedNt=pred or nt, instance=f"{t}_{'LR'[k % 2]}"))
            ids.append(bid[0])
            bid[0] += 1
        return ids
    lb = add("LB3b", 2, "cb_sensory") + add("LB3c", 2, "cb_sensory")
    relay = add("GNGtoy", 2, "cb_intrinsic")
    mn9 = add("MN9", 2, "cb_motor")
    glom = {g: (add(v["orn"], 4, "cb_sensory"), add(v["pn"], 2, "cb_intrinsic")) for g, v in V7A.items()}
    ln = add("ALBN1", 2, "cb_intrinsic", nt="gaba")
    sens = add("toySens", 20, "cb_sensory")
    fill = add("toyFill", 10, "cb_intrinsic")
    unc = add("toyUnclear", 2, "cb_intrinsic", nt="unclear", pred="gaba")
    lh = add("toyLH", 2, "cb_intrinsic")
    E = []

    def con(pre, post, w, nt="acetylcholine"):
        E.extend(dict(pre=a, post=b, weight=w, nt=nt) for a in pre for b in post if a != b)
    con(lb, relay, 40); con(relay, mn9, 40)
    for o, p in glom.values():
        con(o, p, 30); con(o, ln, 10); con(p, ln, 10); con(ln, p, 12, "gaba"); con(p, lh, 20)
    con(sens, fill, 30); con(fill[:5], fill[5:], 12); con(fill[5:], relay, 5)
    con(relay, unc, 10); con(unc, relay, 10, "unclear"); con(unc, fill[:2], 8, "unclear")
    nrn = pd.DataFrame(rows)
    nrn.to_parquet(d / "neurons.parquet", index=False)
    pd.DataFrame(E).to_parquet(d / "edges.parquet", index=False)
    roi_of = {b: "AL(R)" for o, p in glom.values() for b in o + p}
    roi_of.update({b: "AL(R)" for b in ln})
    roi_of.update({b: "LH(R)" for b in lh})
    pd.DataFrame(dict(bodyId=nrn.bodyId, dominant_roi=[roi_of.get(b, "GNG") for b in nrn.bodyId], dominant_frac=1.0,
                      sez_frac=[0.0 if b in roi_of else 1.0 for b in nrn.bodyId], n_syn=100)
                 ).to_parquet(d / "roi_membership.parquet", index=False)
    return d


def selftest(run=True, tmp=None):
    """The marking rule and the curve fit on hand-made inputs, and the design, with exact expectations; then (run)
    eight arms on the toy network, end to end. Returns (ok, message)."""
    import pandas as pd
    import tempfile
    checks = []
    nrn = pd.DataFrame(dict(bodyId=[1, 2, 3, 4, 5, 6, 7], type=["ORN_A", "PNa", "LNa", "KC", "ORN_B", None, "PNa"]))
    E = pd.DataFrame(dict(pre=[1, 1, 1, 2, 3, 2, 5, 4, 6, 7], post=[2, 3, 4, 3, 2, 4, 7, 2, 2, 6],
                          weight=[10, 20, 30, 5, 6, 7, 8, 9, 11, 12]), index=range(100, 110))
    ct = dict(ALPN={"PNa"}, ALLN={"LNa"})
    m_in, l_in = std_marks(E, nrn, "in", ct)
    m_al, l_al = std_marks(E, nrn, "al", ct)
    # "in": ORN -> PN or LN: 1->2, 1->3, 5->7. "al" adds PN/LN -> PN/LN: 2->3, 3->2. Not: ORN -> KC, PN -> KC,
    # KC -> PN, untyped -> PN, PN -> untyped
    checks.append(("marks in", m_in.tolist() == [True, True, False, False, False, False, True, False, False, False]
                   and (l_in["edges"], l_in["synapses"]) == (3, 38.0)))
    checks.append(("marks al", m_al.tolist() == [True, True, False, True, True, False, True, False, False, False]
                   and (l_al["edges"], l_al["synapses"], l_al["al_to_al"]["synapses"]) == (5, 49.0, 11.0)))
    f = hill_fit(V7A_RATES, hill(V7A_RATES, 170.0, 16.3))
    checks.append(("fit recovers", abs(f["r_max"] - 170.0) < 0.5 and abs(f["sigma"] - 16.3) < 0.05 and not f["at_bound"]
                   and v7a_consistent(f, "DM4") and not v7a_consistent(f, "DM1")))
    z = hill_fit(V7A_RATES, [0.0] * len(V7A_RATES))
    checks.append(("fit of silence", z["r_max"] == 0.0 and z["sigma"] is None and not v7a_consistent(z, "DM4")))
    edge = dict(r_max=170.0 * 1.25, sigma=16.3 * 2.0, at_bound=False)
    checks.append(("tolerance edges", v7a_consistent(edge, "DM4")
                   and not v7a_consistent(dict(edge, r_max=170.0 * 1.26), "DM4")
                   and not v7a_consistent(dict(edge, sigma=16.3 * 2.01), "DM4")
                   and not v7a_consistent(dict(edge, at_bound=True), "DM4")))
    main = [a for a, s in ARMS.items() if "topup_of" not in s and "dt_check_of" not in s]
    sweep = [a for a in main if ARMS[a]["kind"] == "sweep"]
    checks.append(("design", len(SETS) == 17 and len(sweep) == 170 and len(main) - len(sweep) == 30
                   and len(ARMS) - len(main) == 120 and len(PARTS) - len(CONDITIONAL_PARTS) == 23
                   and len(CONDITIONAL_PARTS) == 60))
    checks.append(("seeds are phase A's", all(ARMS[f"{s}_{d}_{_w(w)}"]["seed"] == PA.ARMS[f"c1_{d}_{_w(w)}"]["seed"]
                                              for s in SETS for d in DRIVES for w in GRID_W)))
    checks.append(("P0 is phase A's cell 1", sim_options(settings_of("p0")) == PA._opt(PA.ARMS["c1_sugar_w040"]["settings"])
                   and SETS["p0"]["unclear"] == "dropped"
                   and all(SETS[s]["unclear"] == "predicted" for s in SETS if s != "p0")))
    pj = ROOT / "results" / "gen6_phaseA" / "phaseA.json"
    if pj.exists():
        c1 = json.loads(pj.read_text(encoding="utf-8"))["cells"]["c1"]["grid"]
        got = {_w(r["w_scale"]): dict({k: r["components"][k]["verdict"] for k in COMPONENTS},
                                      self_sustained=[r["sugar"]["self_sustained"], r["blind"]["self_sustained"]])
               for r in c1}
        checks.append(("EXPECT_C1 is the committed phase A table", got == EXPECT_C1
                       and all(not r["topups_used"] for r in c1)))
    msg = "marking rule, curve fit, design, seeds and the phase A table are as written"
    if run:
        with tempfile.TemporaryDirectory(prefix="flycns_g7_") as td:
            td = Path(tmp) if tmp is not None else Path(td)
            d, o = toy(td / "toy"), td / "out"
            recs = {a: run_arm(a, str(d), 2, out_dir=o) for a in
                    ("p0_sugar_w100", "b_sugar_w100", "sin_sugar_w100", "sin_blind_w100", "csin_sugar_w100",
                     "csall_blind_w100", "sin_sugar_w100_dt005", "v7a_csin_w100")}
            strip = lambda r: [{k: v for k, v in t.items() if k != "lowest_v_mV"} for t in r["trials"]]   # noqa: E731
            b, s = recs["b_sugar_w100"], recs["sin_sugar_w100"]
            checks.append(("toy: the fix signs connections", recs["p0_sugar_w100"]["graph"]["resigned"]["edges"] is None
                           and b["graph"]["resigned"]["edges"] == 8 and b["graph"]["edges"] - recs["p0_sugar_w100"]["graph"]["edges"] == 8))
            checks.append(("toy: marks", s["std_marks"]["edges"] == 5 * 4 * 4 and s["n_std_syn"] == 80
                           and recs["csall_blind_w100"]["n_std_syn"] > 80 and b["n_std_syn"] == 0))
            checks.append(("toy: sugar drives MN9", all(t["mn9_hz"] > 0 for t in b["trials"])))
            # no ORN fires under the sugar drive, so no marked synapse delivers: S-in must equal B exactly (D6)
            checks.append(("toy: S-in equals B under sugar", all(t["orn_spikes"] == 0 for t in s["trials"])
                           and strip(s) == strip(b)))
            c = recs["csin_sugar_w100"]
            checks.append(("toy: conductance arm records lowest v", all(t["lowest_v_mV"] is not None
                                                                         and t["lowest_v_mV"] >= E_INH_MV - 1e-9
                                                                         for t in c["trials"])
                           and all(t["lowest_v_mV"] is None for t in b["trials"])))
            checks.append(("toy: dt repeat", recs["sin_sugar_w100_dt005"]["spec"]["dt_ms"] == 0.05
                           and len(recs["sin_sugar_w100_dt005"]["trials"]) == 2))
            v = recs["v7a_csin_w100"]
            by = {(t["glomerulus"], t["orn_hz"]): t["pn_hz"] for t in v["trials"] if t["k"] == 0}
            checks.append(("toy: V7a", len(v["trials"]) == len(V7A) * len(V7A_RATES) * 2
                           and by[("DM4", 120.0)] > by[("DM4", 5.0)] and v["v7a_cells"]["DM4"]["orn_cells"] == 4
                           and v["n_std_syn"] == 80))
            sc = _load_module("gen7_synapse_score_unit", SCORE_SCRIPT)
            rep = sc.score(o)
            checks.append(("toy: scorer runs", rep["outcome"]["code"] == "R" and rep["smoke"] is True
                           and "v7a_csin_w100" in rep["v7a"]["arms"]))
        msg += "; eight arms on the toy network run end to end and score"
    bad = [n for n, ok in checks if not ok]
    return not bad, (msg if not bad else f"failed: {bad}")


_mode = sys.argv[1] if __name__ == "__main__" and len(sys.argv) > 1 else ""
_smoke_arm = _mode == "arm" and ((len(sys.argv) > 3 and sys.argv[3] != "data") or len(sys.argv) > 4)
if _mode in ("parts", "preflight", "probe", "selftest") or _smoke_arm or __name__ not in ("__main__", "gen7_synapse"):
    REG = None             # these modes compute nothing that is scored; no registration is read or written
else:
    REG = registry.register(LABEL, CRITERIA, scripts=[__file__, str(SCORE_SCRIPT), str(PHASEA_SCRIPT)])
    require_clean(LABEL)   # (register exits under FLYCNS_REGISTER_ONLY)

if __name__ == "__main__":
    if _mode == "parts":
        for p, arms in PARTS.items():
            print(f"{p:<22} {', '.join(arms)}" + ("   (only when the scorer names it)" if p in CONDITIONAL_PARTS else ""))
    elif _mode == "selftest":
        ok, msg = selftest()
        print(("PASS  " if ok else "FAIL  ") + msg)
        sys.exit(0 if ok else 1)
    elif _mode == "preflight":
        preflight(sys.argv[2] if len(sys.argv) > 2 else "data")
    elif _mode == "probe":
        probe(sys.argv[2] if len(sys.argv) > 2 else "data")
    elif _mode in ("part", "arm"):
        data_dir = sys.argv[3] if _mode == "arm" and len(sys.argv) > 3 else "data"
        trials = int(sys.argv[4]) if _mode == "arm" and len(sys.argv) > 4 else None
        smoke = _mode == "arm" and (data_dir != "data" or trials is not None)
        if not smoke:
            refuse_overrides(f"gen 7 {_mode}")
            PA.celltypes(check=True)
        if _mode == "part":
            run_part(sys.argv[2])
        else:
            run_arm(sys.argv[2], data_dir, trials)
    else:
        print(__doc__)
