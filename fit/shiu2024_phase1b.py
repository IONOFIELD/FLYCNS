"""
Phase 1b (Gen 5): settle the synaptic scale on the male data, before Phase 2 builds on it.

Phase 1 (fit/shiu2024_phase1.py, run 22) ended "A1 passes and M1 responds: the male MN9 zero is caused by
flycns settings; the ladder names which". Its ladder ran on the female brain only, and named one setting:
w_scale 0.4 alone leaves MN9 at 0 Hz in 0 of 30 trials, while the v-only reset triples it (231.8 Hz) and
every other setting is mild. w_scale 0.4 is the value the blind rule picked for QUIETNESS (fit/select_wscale.py:
whole-CNS rate < 1 Hz and < 10% active under 1,470 effective driven sources at 20 Hz (1,575 drawn; about 105
drawn cells never enter the model, results/select_wscale/report.json); Shiu et al. 2024 picked 1.0 for
FUNCTION (80% of maximal MN9). On the male data at 1.0 the network is broadly active (M1: ~7,600 neurons per
trial, bimodal across trials, against 358 on the female). Three things are open, and this phase answers them
in one cloud run before any default is changed:

  LADDER (registered)       the Phase-1 ladder on MaleCNS: from M1, switch ONE setting at a time to the
                            flycns value. The female ladder predicts w_scale is the only setting that
                            silences MN9; that prediction is registered here as two checks.
  SPECIFICITY (registered)  M1's "responds" against two nulls: Shiu's weight permutation (as S6) and this
                            repository's degree-corrected rewiring (audit gap 5). At 7,600 active neurons a
                            21 Hz MN9 could be nonspecific; without this control M1 is not a result. A null
                            that cannot fire scores UNRESOLVED, never PASS (stats.null_percentile).
  RUNAWAY ANATOMY (reported) a w_scale sweep {0.4, 0.5, 0.6, 0.8, 1.0} on both datasets, under the sugar drive
                            (physiological: 21 GRNs / 34 LB3 cells at 100 Hz) and the blind rule's drive, with
                            500 ms of silence after the drive. "Runs away" is operational: activity that
                            persists after the drive is removed (self-sustained), reported per trial, by cell
                            class and by neuropil. This decides whether the 0.4 -> 0.5 transition of the
                            blind rule is a property of the male network or of that rule's drive.

    python fit/shiu2024_phase1b.py parts                          the cloud jobs and their arms
    python fit/shiu2024_phase1b.py part <part> [shiu_repo|-]       run one job's arms, in parallel processes
    python fit/shiu2024_phase1b.py arm <arm> [shiu_repo|-] [data_dir] [trials]
                                                                   run one arm; a data_dir other than "data" or
                                                                   a trial override is a SMOKE run: it is written
                                                                   under results/<label>/smoke/ and never scored
    python fit/shiu2024_phase1b.py score [shiu_repo|-]             score every check from the arms; phase1b.json
The reference repository (SHIU_REPO) is needed only by the FlyWire sweep arms and by scoring when they exist.
Like phase 1, the report is a diagnostic of the simulator (phase1b.json), kept out of results/SUITE.md.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns import registry, stats  # noqa: E402
from flycns.integrity import require_clean, require_data, refuse_overrides  # noqa: E402

LABEL = "shiu2024_phase1b"
OUT = ROOT / "results" / LABEL
PHASE1 = "results/shiu2024_phase1/registration_v5.json"
PHASE1_REPORT = "results/shiu2024_phase1/phase1.json"
MN9_CONTRA, MN9_IPSI = 720575940660219265, 720575940645521262
COMP, CON = "2023_03_23_completeness_630_final.csv", "2023_03_23_connectivity_630_final.parquet"
LADDER_TRIALS, LADDER_MS = 30, 1000              # as M1 (phase 1): restore, set rates, run 1000 ms
SWEEP_TRIALS, SETTLE_MS, DRIVE_MS, TAIL_MS = 10, 200, 1000, 500
NULL_DRAWS = 20
ALIVE_FRACTION = 0.1          # benchmarks/null_distribution.py: null median whole-CNS rate >= 10% of the real one
BIN_MS = 50
RESPONDS = 0.5                # Hz, M1's registered band: "responds" = interval above 0.5 Hz (lower edge exclusive)
GRID_W = [0.4, 0.5, 0.6, 0.8, 1.0]
LI_HOLD = 0.8                 # gen-6 rule: median MN9 laterality index at or above this holds w_scale
# Outcome B grouping (docs/gen6_rule.md): every VNC neuropil, every side, is ONE group "VNC". A label is VNC if
# the part before its first "(" is one of the MANC neuropil families below. Every other label keeps its own
# name and is never VNC: the neck connective, brain and optic-lobe neuropils, nerves, "?" and unassigned.
VNC_STEMS = ("LegNp", "Ov", "mVAC", "WTct", "HTct", "NTct", "IntTct", "LTct", "ANm")
MALE_SUGAR = ["LB3b", "LB3c"]  # M1's sugar set (phase 1): every cell of both types
SUGAR_HZ, BLIND_HZ = 100.0, 20.0
# the blind rule's exclusions, copied from fit/select_wscale.py (importing it would run the selection)
EXCLUDED_SUBCLASSES_EXTRA = {"auditory", "wind_gravity", "campaniform sensilla"}
EXCLUDED_PREFIXES = ("JO-", "LC", "LPLC", "SNpp", "pC1", "DNg02", "L1", "L2", "L3", "L5", "Pm3", "Mi1", "Tm2")

# Settings. M1 = the phase-1 male arm (Shiu's choices, floor 5, amines excitatory, no electrical synapses).
# FLY = the declared flycns model (generation 5 defaults). floor is not a rung: the male data are fetched at a
# floor of 5, so M1 and flycns already agree on it (the phase-1 addendum).
M1 = dict(reset="v_and_g", stimulation="kick", integration="exact", adaptation=False, w_scale=1.0, floor=5,
          amines="excitatory", electrical=False)
FLY = dict(reset="v", stimulation="source", integration="euler", adaptation=True, w_scale=0.4, floor=5,
           amines="dropped", electrical=True)
A1 = dict(reset="v_and_g", stimulation="kick", integration="exact", adaptation=False, w_scale=1.0, floor=1,
          amines="column", electrical=False)       # FlyWire: the sign column is Shiu's (amines excitatory)
LADDER = {"ML1_reset": ["reset"], "ML2_stimulation": ["stimulation"], "ML4_wscale04": ["w_scale"],
          "ML5_adaptation": ["adaptation"], "MLe_euler": ["integration"], "ML7_amines_dropped": ["amines"],
          "ML_all": ["reset", "stimulation", "w_scale", "adaptation", "integration", "amines", "electrical"]}
SINGLE = ["ML1_reset", "ML2_stimulation", "ML5_adaptation", "MLe_euler", "ML7_amines_dropped"]
FAMILIES = {"male_shiu_exc": ("malecns", M1), "male_shiu_drop": ("malecns", {**M1, "amines": "dropped"}),
            "male_flycns": ("malecns", FLY), "fw_shiu": ("flywire", A1)}


def _w(w):
    return f"w{int(round(w * 100)):03d}"


def _arms():
    arms = {}
    seed = 200

    def add(name, **spec):
        nonlocal seed
        seed += 1
        arms[name] = dict(seed=seed, **spec)
    add("ML0_m1", kind="ladder", data="malecns", settings=M1, trials=LADDER_TRIALS)
    for name, keys in LADDER.items():
        add(name, kind="ladder", data="malecns", settings={**M1, **{k: FLY[k] for k in keys}}, trials=LADDER_TRIALS)
    add("null_weightperm", kind="null_weightperm", data="malecns", settings=M1, trials=1, draws=NULL_DRAWS)
    add("null_dc", kind="null_dc", data="malecns", settings=M1, trials=1, draws=NULL_DRAWS)
    for fam, (data, st) in FAMILIES.items():
        for drive in ("sugar", "blind"):
            for w in GRID_W:
                add(f"sw_{fam}_{drive}_{_w(w)}", kind="sweep", data=data, settings={**st, "w_scale": w},
                    drive=drive, trials=SWEEP_TRIALS)
    return arms


ARMS = _arms()
PARTS = {"p1b-ladder-a": ["ML0_m1", "ML1_reset", "ML2_stimulation"],
         "p1b-ladder-b": ["ML4_wscale04", "ML5_adaptation", "MLe_euler"],
         "p1b-ladder-c": ["ML7_amines_dropped", "ML_all"],
         "p1b-null-weightperm": ["null_weightperm"], "p1b-null-dc": ["null_dc"]}
for fam in FAMILIES:
    for drive in ("sugar", "blind"):
        PARTS[f"p1b-sw-{fam.replace('_', '-')}-{drive}"] = [f"sw_{fam}_{drive}_{_w(w)}" for w in GRID_W]
assert sorted(a for p in PARTS.values() for a in p) == sorted(ARMS), "every arm in exactly one part"
NEEDS_SHIU = {p for p, arms in PARTS.items() if any(ARMS[a]["data"] == "flywire" for a in arms)}


def _phase1():
    reg = json.loads((ROOT / PHASE1).read_text(encoding="utf-8"))
    rep = json.loads((ROOT / PHASE1_REPORT).read_text(encoding="utf-8"))
    m1 = rep["reported"]["m1_mn9_hz"]
    return dict(registration=dict(file=PHASE1, git_commit=reg.get("git_commit"), registered_at=reg.get("registered_at"),
                                  model_hash=reg["model"]["hash"]),
                result=dict(file=PHASE1_REPORT, outcome=rep["outcome"], m1=rep["m1"],
                            m1_mn9_hz_mean=float(np.mean(m1)), m1_mn9_ci95=rep["uncertainty"]["M1_male_mn9"]["ci95"],
                            ladder_female={k: dict(switched=v["switched"], mn9_contra_hz=v["mn9_contra_hz"],
                                                   fired_trials=v["fired_trials"])
                                           for k, v in rep["reported"]["ladder"].items()}))


P1 = _phase1()

CRITERIA = dict(
    question=("on the male CNS, is w_scale the one flycns setting that silences MN9 under sugar (as the female ladder "
              "says); is M1's MN9 response specific to the real wiring; and at which synaptic scale, under which "
              "drive, does either network stop being drive-dependent?"),
    phase1=P1,
    implementation=dict(
        settings=dict(M1=M1, flycns=FLY, A1=A1, ladder=LADDER,
                      note=("M1 and A1 as registered in phase 1 (results/shiu2024_phase1/registration_v5.json); "
                            "flycns = LIFParams() and SimOptions() defaults, electrical synapses on, amines dropped "
                            "(flycns/graph.py SIGN_MAP). amines='column' on FlyWire: the repository's Excitatory "
                            "column, in which Shiu et al. count amines as excitatory")),
        data=dict(malecns="data/ as pinned by data/MANIFEST.json (neurons, edges, roi_membership); sugar: every "
                          f"{' and '.join(MALE_SUGAR)} cell at {SUGAR_HZ:.0f} Hz; MN9: every cell of type MN9",
                  flywire="the reference repository's completeness and connectivity tables at the phase-1 commit "
                          "and sha256; sugar: the 21 neu_sugar ids of figures.ipynb; MN9: the two ids of phase 1"),
        ladder=dict(protocol=f"as M1: one network per arm, built once; per trial restore, set the sugar rate, run "
                             f"{LADDER_MS} ms; {LADDER_TRIALS} trials; seeds in arm order from 201",
                    readout=("mean spikes per MN9 cell per second, per trial (the M1 statistic); each cell reported "
                             "with its bodyId (mn9_cells, mn9_per_cell_hz); secondary: the larger of the cells "
                             "(mn9_max_cell_hz), because run 22's male response is one cell (42.8 vs 0.13 Hz)"),
                    floor="not a rung: the male tables are fetched at a floor of 5, M1's and flycns's value"),
        nulls=dict(weightperm=(f"{NULL_DRAWS} draws: the signed per-connection weights of the recurrent network "
                               "permuted among the existing connections (numpy default_rng(10000 + k), as phase-1 S6), "
                               f"one {LADDER_MS} ms trial at sugar {SUGAR_HZ:.0f} Hz under M1's settings"),
                   degree_corrected=(f"{NULL_DRAWS} draws: flycns.graph.rewire_null(mode='degree_corrected', "
                                     "seed=20000 + k): targets permuted among connections sharing the target's "
                                     "superclass, neuropil (data/roi_membership.parquet), the connection's sign and "
                                     "size class; the model rebuilt per draw under M1's settings; one trial each"),
                   real="ML0_m1 (M1 under a fresh seed, this phase): mean over trials of the MN9 statistic",
                   alive_rule=f"median null whole-CNS rate >= {ALIVE_FRACTION} x ML0's median (benchmarks/null_distribution.py)"),
        sweep=dict(grid=GRID_W, families={k: v[0] for k, v in FAMILIES.items()},
                   protocol=(f"per trial: restore, {SETTLE_MS} ms silence, {DRIVE_MS} ms drive, {TAIL_MS} ms with every "
                             f"stimulus rate at 0; {SWEEP_TRIALS} trials; one network per arm"),
                   drives=dict(sugar=f"the sugar set of the dataset at {SUGAR_HZ:.0f} Hz",
                               blind=(f"MaleCNS: exactly fit/select_wscale.py's drive: a fixed random 10% (numpy "
                                      f"default_rng(0)) of the sensory-superclass neurons no benchmark drives, at "
                                      f"{BLIND_HZ:.0f} Hz. FlyWire has no class annotation in the reference "
                                      "repository, so its proxy is the cells with no input and at least one output "
                                      "at the arm's floor (afferent-like), sampled the same way; the cross-dataset "
                                      "comparison under this drive is approximate and is said so")),
                   readouts=("per trial, excluding the stimulated cells: active neurons and spikes during the drive, "
                             "whole-CNS rate (spikes per neuron per second) and fraction active; the same in the last "
                             f"{TAIL_MS // 2} ms of the tail; spikes per {BIN_MS} ms bin over the whole trial; spikes and "
                             "active cells by superclass and by dominant neuropil (MaleCNS); MN9 (sugar drive). For "
                             "every superclass and every dominant neuropil (all groups, zeros included), in the drive "
                             "and in the tail window: spikes, active cells and rate per cell of the group "
                             "(drive_by_*, tail_by_*), with the group sizes (group_sizes), so self-sustained can be "
                             "recomputed with any one group left out"),
                   self_sustained=("a trial is self-sustained if the whole-CNS rate in the last half of the tail is at "
                                   "least 10% of the rate during the drive and at least 0.01 Hz"),
                   role="reported, not scored"),
        intervals="flycns.stats: percentile bootstrap over trials, 2,000 resamples, seed 0"),
    checks={
        "ML0_responds": dict(band=[RESPONDS, None], arm="ML0_m1",
                             scored_as="M1 replicated under a fresh seed: interval above 0.5 Hz, lower edge exclusive"),
        "ML_wscale04_silent": dict(band=[None, RESPONDS], arm="ML4_wscale04",
                                   scored_as=("PASS = the whole interval lies at or below 0.5 Hz (MN9 does not respond, as "
                                              "on the female); FAIL = the whole interval lies above it")),
        "ML_single_switches_respond": dict(bands=[[RESPONDS, None]] * len(SINGLE), arms=SINGLE,
                                           scored_as=("every other single switch leaves MN9 responding: all parts PASS "
                                                      "(interval above 0.5 Hz, lower edge exclusive); FAIL if any part FAILs")),
        "MS1_weightperm_specific": dict(rule=("stats.null_percentile: PASS if ML0's MN9 exceeds every weight-permutation "
                                              "draw; FAIL if it does not exceed the null median; UNRESOLVED in between, or "
                                              "if the null is not active by the alive rule"), arm="null_weightperm"),
        "MS2_degree_corrected_specific": dict(rule="as MS1, against the degree-corrected rewiring draws", arm="null_dc"),
    },
    secondary=dict(
        rule=("pre-registered secondary readouts, reported with verdicts; they do not enter the ladder or specificity "
              "outcomes: the four MN9 checks repeated on mn9_max_cell_hz (the larger MN9 cell per trial) instead of "
              "the two-cell mean, with the same bands and null rule"),
        checks={"ML0_responds_maxcell": dict(band=[RESPONDS, None], arm="ML0_m1"),
                "ML_wscale04_silent_maxcell": dict(band=[None, RESPONDS], arm="ML4_wscale04"),
                "MS1_weightperm_specific_maxcell": dict(rule="as MS1, on the larger cell", arm="null_weightperm"),
                "MS2_degree_corrected_specific_maxcell": dict(rule="as MS2, on the larger cell", arm="null_dc")},
        laterality=dict(
            statistic=("per trial, LI = (max - min) / (max + min) over the MN9 cells' rates; undefined (not 0) when "
                       "no MN9 cell fires; each cell's bodyId and soma side recorded (mn9_cells, mn9_sides)"),
            reported=("median LI with a 95% bootstrap interval over the trials where it is defined, and that count: "
                      "for every ladder arm, for both null arms (every draw), and for every sugar sweep arm"),
            why=("the male drive is two-sided and symmetric (LB3b/LB3c, both sides) and the connectome paths give "
                 "the two MN9 cells roughly equal input, yet run 22 split about 300:1; in Shiu et al.'s model, "
                 "reproduced in phase 1, both cells fire (68.3 and 50.4 Hz)"),
            gen6_use=(f"docs/gen6_rule.md: a median LI >= {LI_HOLD} at the candidate scale holds w_scale until a "
                      "one-side-at-a-time run explains the asymmetry; the two-cell mean stays the FUNCTION statistic"))),
    outcome_b_grouping=dict(
        rule=("for gen-6 Outcome B, the dominant-neuropil groups with every VNC neuropil merged into one group 'VNC', "
              "left and right together: a label is VNC if the part before its first '(' is one of "
              f"{', '.join(VNC_STEMS)}. Every other label keeps its own name and is never VNC: the neck connective, "
              "brain and optic-lobe neuropils, nerves, '?' and unassigned"),
        audit=("phase1b.json reports every label and its group (tail_groups.label_map); a VNC neuropil found outside "
               "the list after the run is fixed only by a new registration, never by re-scoring")),
    prediction=("from the female ladder (phase 1): ML_wscale04_silent PASSES and ML_single_switches_respond PASSES. "
                "ML7_amines_dropped was not on the female ladder (FlyWire's sign column fixes amines); it is predicted "
                "to respond because amines carry about 1.6% of the signed synapses"),
    decision_rule=dict(
        ladder=("both ladder checks PASS: w_scale alone accounts for the male zero, as on the female. ML_wscale04_silent "
                "FAILS: the male zero is not w_scale (unexpected; stop for review). ML_single_switches_respond FAILS: "
                "the failing switch is a second cause on the male data and is named"),
        specificity=("MS1 and MS2 PASS: M1's response is wiring-specific and stands. Either FAILS: M1's 'responds' at "
                     "w_scale 1.0 is not evidence about the sugar circuit (the network responds to that drive on "
                     "rewired wiring too) and phase 1's outcome is downgraded accordingly. UNRESOLVED (a null that "
                     "cannot fire, or a real value inside the null range) is reported as such"),
        sweep=("reported: for every family and drive, the largest grid scale at which no trial is self-sustained and "
               "the whole-CNS rate stays below 1 Hz (drive-dependent), and the smallest at which a majority of trials "
               "are self-sustained (runaway). The generation-6 defaults are decided from this table together with the "
               "two registered outcomes above, in a separate registration; nothing here changes a default")),
)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def shiu_repo(arg=None):
    """The reference repository, checked against the phase-1 registration (commit and file sha256)."""
    reg = json.loads((ROOT / PHASE1).read_text(encoding="utf-8"))
    ref = reg["criteria"]["sources"]["preregistered"]["criteria"]["reference"]
    repo = Path(arg or os.environ.get("SHIU_REPO") or "")
    if not repo.is_dir():
        raise SystemExit("[phase1b] the reference repository is needed for FlyWire arms: pass its folder or set SHIU_REPO")
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()
    bad = [] if head == ref["commit"] else [f"commit {head or '?'} is not {ref['commit']}"]
    for rel in (COMP, CON, "figures.ipynb"):
        want, p = ref["sha256"].get(rel), repo / rel
        if want and (not p.exists() or sha256(p) != want):
            bad.append(f"{rel}: sha256 differs from the phase-1 registration")
    if bad:
        raise SystemExit("[phase1b] reference repository differs from the registration: " + "; ".join(bad))
    return repo


def notebook_ids(repo, name):
    """A list literal `name = [...]` from figures.ipynb (as fit/shiu2024_phase1.py)."""
    import ast
    nb = json.loads((repo / "figures.ipynb").read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code" and f"{name} = [" in src:
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
                    return [int(x) for x in ast.literal_eval(node.value)]
    raise SystemExit(f"figures.ipynb: no {name} list")


def flywire(repo, floor, drive):
    """The v630 network as flycns tables (as fit/shiu2024_phase1.py), with the drive's cells typed."""
    import pandas as pd
    from flycns.integrity import LOADED
    ids = pd.read_csv(repo / COMP, index_col=0).index.astype("int64")
    con = pd.read_parquet(repo / CON, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory"])
    edges = pd.DataFrame({"pre": con["Presynaptic_ID"].astype("int64"), "post": con["Postsynaptic_ID"].astype("int64"),
                          "weight": con["Connectivity"].astype("int64"), "sign": con["Excitatory"].astype(float)})
    edges = edges[edges["weight"] >= floor].reset_index(drop=True)
    typ = pd.Series("fw", index=ids)
    typ[[MN9_CONTRA, MN9_IPSI]] = ["fw_MN9_contra", "fw_MN9_ipsi"]
    sc = pd.Series("", index=ids)
    sc[[MN9_CONTRA, MN9_IPSI]] = "cb_motor"
    if drive == "sugar":
        sugar = notebook_ids(repo, "neu_sugar")
        if len(sugar) != 21:
            raise SystemExit(f"[phase1b] expected 21 sugar GRNs, found {len(sugar)}")
        typ[sugar] = "fw_sugar_GRN"
        stim_types, driven, pool = ["fw_sugar_GRN"], set(sugar), len(sugar)
    else:   # afferent-like proxy: no input, at least one output, at this floor
        has_in, has_out = set(edges["post"]), set(edges["pre"])
        cand = np.array(sorted(b for b in has_out if b not in has_in and b not in (MN9_CONTRA, MN9_IPSI)), dtype="int64")
        pick = np.random.default_rng(0).choice(cand, max(1, len(cand) // 10), replace=False)
        typ[cand] = "fw_afferent_like"
        stim_types, driven, pool = ["fw_afferent_like"], set(int(x) for x in pick), int(len(cand))
    neurons = pd.DataFrame({"bodyId": ids, "type": typ.values, "superclass": sc.values})
    LOADED.clear()
    LOADED.update(data_dir=str(repo), min_weight=int(floor), n_neurons=int(len(neurons)),
                  n_signed_edges=int(len(edges)), n_signed_synapses=int(edges["weight"].sum()), dataset="FlyWire v630")
    return neurons, edges, stim_types, driven, pool


def male_blind_pool(neurons):
    """fit/select_wscale.py's eligible pool and its fixed 10% sample, reproduced exactly."""
    from flycns.graph import GUSTATORY_MN9_DRIVING, GUSTATORY_SUBCLASSES, PEPTIDE_MODULATION
    from flycns.protocols import LOOM_TUNING
    t = neurons["type"].fillna("").astype(str)
    sub = neurons["subclass"].fillna("").astype(str) if "subclass" in neurons else t.map(lambda _: "")
    sensory = neurons["superclass"].fillna("").astype(str).str.contains("sensory")
    used = set(LOOM_TUNING) | set(GUSTATORY_MN9_DRIVING) | {e["source"] for e in PEPTIDE_MODULATION}
    excluded = sorted(set(GUSTATORY_SUBCLASSES) | EXCLUDED_SUBCLASSES_EXTRA)
    eligible = sensory & ~t.isin(used) & ~sub.isin(excluded) & ~t.str.startswith(EXCLUDED_PREFIXES)
    pool = np.sort(neurons.loc[eligible, "bodyId"].to_numpy())
    rng = np.random.default_rng(0)
    driven = set(int(x) for x in rng.choice(pool, max(1, len(pool) // 10), replace=False)) if len(pool) else set()
    if not driven:
        raise SystemExit("[phase1b] no eligible sensory neurons for the blind drive")
    stim_types = sorted(set(t[neurons.bodyId.isin(driven)]))
    return stim_types, driven, int(len(pool))


def male_tables(data, st):
    from flycns.graph import load_graph
    from flycns.integrity import LOADED
    neurons, edges = load_graph(data, min_weight=st["floor"], amines=st["amines"])
    unknown = dict(edges=LOADED.get("n_dropped_unsigned_edges"), synapses=LOADED.get("n_dropped_unsigned_synapses"),
                   silent_presynaptic=LOADED.get("n_silent_presynaptic"))
    return neurons, edges, unknown


def _opt(st):
    from flycns.model import SimOptions
    return SimOptions(reset=st["reset"], stimulation=st["stimulation"], integration=st["integration"],
                      adaptation=st["adaptation"])


def build(neurons, edges, stim_types, st, seed, codegen=None):
    from flycns.model import CNSModel, LIFParams
    m = CNSModel(neurons, edges, stim_types, LIFParams(w_scale=st["w_scale"], seed=seed), electrical=st["electrical"],
                 codegen=codegen, options=_opt(st))
    m.store()
    return m


def _counts(m, sp, t0, t1, exclude):
    """Spikes and active cells in [t0, t1) ms, excluding the stimulated cells."""
    w = sp[(sp.t_ms >= t0) & (sp.t_ms < t1) & ~sp.bodyId.isin(exclude)]
    n = len(m.lif_ids) - int(np.isin(m.lif_ids, list(exclude)).sum())
    return w, n, int(len(w)), int(w.bodyId.nunique())


def _mn9(m, sp, seconds, data):
    """MN9 rates from the spikes in a window (a spike_frame slice) lasting `seconds`. mn9_per_cell_hz is
    aligned with mn9_cells (bodyIds, ascending). mn9_max_cell_hz is the pre-registered secondary readout:
    the male M1 response is carried by one of the two cells (run 22: 42.8 vs 0.13 Hz), so the two-cell
    mean halves a one-sided response."""
    if data == "flywire":
        contra = float((sp.bodyId == MN9_CONTRA).sum() / seconds)
        ipsi = float((sp.bodyId == MN9_IPSI).sum() / seconds)
        return dict(mn9_contra_hz=contra, mn9_ipsi_hz=ipsi, mn9_cells=[MN9_CONTRA, MN9_IPSI],
                    mn9_sides=["contra", "ipsi"], mn9_per_cell_hz=[contra, ipsi], mn9_max_cell_hz=max(contra, ipsi),
                    mn9_li=_li([contra, ipsi]))
    cells = sorted(int(b) for b in m.meta.index[m.meta["type"] == "MN9"] if b in m.lif_index.index)
    side = m.meta["somaSide"] if "somaSide" in m.meta else None
    sides = [str(side.get(b)) if side is not None and isinstance(side.get(b), str) else "?" for b in cells]
    per = [float((sp.bodyId == b).sum() / seconds) for b in cells]
    nan = float("nan")
    return dict(mn9_hz=float(np.mean(per)) if per else nan, mn9_cells=cells, mn9_sides=sides, mn9_per_cell_hz=per,
                mn9_max_cell_hz=float(max(per)) if per else nan, mn9_li=_li(per))


def _li(per):
    """MN9 laterality index of one trial, (max - min) / (max + min) over the cells; None if no cell fired
    (undefined, not 0). 0 = both cells equal, 1 = one cell only."""
    if len(per) < 2 or max(per) + min(per) <= 0:
        return None
    return float((max(per) - min(per)) / (max(per) + min(per)))


def _li_summary(trials):
    """Median laterality index over the trials where it is defined, its 95% interval, and the count."""
    li = np.array([t["mn9_li"] for t in trials if t.get("mn9_li") is not None], dtype=float)
    if not len(li):
        return dict(median=None, ci95=None, n_defined=0, n_trials=len(trials), at_or_above_hold=None)
    e, lo, hi = stats.bootstrap(li, stat=np.median)
    return dict(median=e, ci95=[lo, hi], n_defined=int(len(li)), n_trials=len(trials),
                at_or_above_hold=bool(e >= LI_HOLD), values=li.tolist())


def run_ladder_trial(m, rates, data, exclude):
    """One M1-style trial: set the rate, run LADDER_MS, read MN9 and the network."""
    m.restore()
    m.set_stim_rates(rates)
    m.run(LADDER_MS)
    sp = m.spike_frame()
    _, n, n_sp, n_act = _counts(m, sp, 0, LADDER_MS, exclude)
    row = dict(n_active=n_act, n_spikes=n_sp, cns_rate_hz=n_sp / n / (LADDER_MS / 1000.0), fraction_active=n_act / n)
    row.update(_mn9(m, sp, LADDER_MS / 1000.0, data))
    return row


def _groups(m, exclude, roi):
    """Per simulated (non-stimulated) cell: its superclass and, on MaleCNS, its dominant neuropil; and the
    number of such cells per group, so a per-group rate (spikes per cell per second) can be formed and the
    whole-CNS rate recomputed with any one group left out (gen-6 Outcome B, docs/gen6_rule.md)."""
    import pandas as pd
    ids = np.asarray(m.lif_ids, dtype="int64")
    ids = ids[~np.isin(ids, list(exclude))]
    sc = m.meta["superclass"].reindex(ids) if "superclass" in m.meta else pd.Series(None, index=ids, dtype=object)
    out = dict(superclass=sc.fillna("?").astype(str))
    if roi is not None:
        out["neuropil"] = roi.reindex(ids).fillna("?").astype(str)
    sizes = {k: {g: int(n) for g, n in v.value_counts().items()} for k, v in out.items()}
    return out, sizes


def _by_group(w, labels, sizes, seconds):
    """{group: [spikes, active cells, rate Hz]} over EVERY group (zeros included) for one window."""
    if len(w):
        lab = w["bodyId"].map(labels).fillna("?").astype(str)
        agg = w.groupby(lab)["bodyId"].agg(["size", "nunique"])
    else:
        agg = None
    out = {}
    for g, n in sizes.items():
        s, a = (int(agg.loc[g, "size"]), int(agg.loc[g, "nunique"])) if agg is not None and g in agg.index else (0, 0)
        out[g] = [s, a, s / n / seconds if n else 0.0]
    return out


def run_sweep_trial(m, rates, data, exclude, roi, groups=None):
    m.restore()
    m.set_stim_rates(np.zeros_like(rates))
    m.run(SETTLE_MS)
    m.set_stim_rates(rates)
    m.run(DRIVE_MS)
    m.set_stim_rates(np.zeros_like(rates))
    m.run(TAIL_MS)
    sp = m.spike_frame()
    total = SETTLE_MS + DRIVE_MS + TAIL_MS
    d, n, d_sp, d_act = _counts(m, sp, SETTLE_MS, SETTLE_MS + DRIVE_MS, exclude)
    half = TAIL_MS // 2
    tw, _, t_sp, t_act = _counts(m, sp, total - half, total, exclude)
    _, _, s_sp, s_act = _counts(m, sp, 0, SETTLE_MS, exclude)
    drive_hz, tail_hz = d_sp / n / (DRIVE_MS / 1000.0), t_sp / n / (half / 1000.0)
    bins = np.histogram(sp.t_ms[~sp.bodyId.isin(exclude)], bins=np.arange(0, total + 1, BIN_MS))[0]
    by_sc = d.groupby(d["superclass"].fillna("?").astype(str)).agg(spikes=("bodyId", "size"), active=("bodyId", "nunique"))
    row = dict(n_active=d_act, n_spikes=d_sp, cns_rate_hz=drive_hz, fraction_active=d_act / n,
               settle_spikes=s_sp, tail_spikes=t_sp, tail_active=t_act, tail_rate_hz=tail_hz,
               self_sustained=bool(tail_hz >= 0.1 * drive_hz and tail_hz >= 0.01),
               bins_ms=BIN_MS, spikes_per_bin=[int(x) for x in bins],
               by_superclass={k: [int(v.spikes), int(v.active)] for k, v in by_sc.iterrows()})
    if roi is not None and len(d):
        r = d["bodyId"].map(roi).fillna("?").astype(str)
        by_roi = d.groupby(r).agg(spikes=("bodyId", "size"), active=("bodyId", "nunique")).sort_values("spikes", ascending=False)
        row["by_neuropil_top15"] = {k: [int(v.spikes), int(v.active)] for k, v in by_roi.head(15).iterrows()}
    if groups is not None:      # every group, both windows: [spikes, active cells, Hz per cell of the group]
        labels, sizes = groups
        for key, lab in labels.items():
            row[f"drive_by_{key}"] = _by_group(d, lab, sizes[key], DRIVE_MS / 1000.0)
            row[f"tail_by_{key}"] = _by_group(tw, lab, sizes[key], half / 1000.0)
    row.update(_mn9(m, sp[(sp.t_ms >= SETTLE_MS) & (sp.t_ms < SETTLE_MS + DRIVE_MS)], DRIVE_MS / 1000.0, data))
    return row


def run_arm(name, repo, data_dir="data", trials=None):
    from flycns.bench import provenance
    from flycns.graph import _dominant_roi, rewire_null
    spec = ARMS[name]
    st = spec["settings"]
    reduced = data_dir != "data" or (trials is not None and trials != spec["trials"])
    n_trials = trials if trials is not None else spec["trials"]
    out_dir = OUT / ("smoke" if reduced else "arms")
    t0 = time.time()
    unknown, roi, pool, group_sizes = None, None, None, None
    if spec["data"] == "flywire":
        neurons, edges, stim_types, driven, pool = flywire(repo, st["floor"], spec.get("drive", "sugar"))
    else:
        if not reduced:
            require_data(data_dir, LABEL, ["neurons.parquet", "edges.parquet", "roi_membership.parquet"])
        neurons, edges, unknown = male_tables(data_dir, st)
        roi = _dominant_roi(data_dir)
        if spec.get("drive") == "blind":
            stim_types, driven, pool = male_blind_pool(neurons)
        else:
            stim_types = list(MALE_SUGAR)
            driven = set(int(b) for b in neurons.loc[neurons["type"].isin(stim_types), "bodyId"])
    opt = _opt(st)
    hz = BLIND_HZ if spec.get("drive") == "blind" else SUGAR_HZ
    kind = spec["kind"]
    rows, m = [], None
    if kind != "null_dc":
        m = build(neurons, edges, stim_types, st, spec["seed"])
    built = time.time() - t0

    def rates_of(model):
        return np.where(np.isin(model.stim["bodyId"].to_numpy(), list(driven)), hz, 0.0)
    if kind == "ladder":
        rates, exclude = rates_of(m), set(int(b) for b in m.stim["bodyId"])
        for k in range(n_trials):
            rows.append(dict(k=k, **run_ladder_trial(m, rates, spec["data"], exclude)))
            print(f"[phase1b] {name} {k + 1}/{n_trials} ({time.time() - t0:.0f} s)", flush=True)
    elif kind == "sweep":
        rates, exclude = rates_of(m), set(int(b) for b in m.stim["bodyId"])
        groups = _groups(m, exclude, roi)
        group_sizes = groups[1]
        for k in range(n_trials):
            rows.append(dict(k=k, **run_sweep_trial(m, rates, spec["data"], exclude, roi, groups)))
            print(f"[phase1b] {name} {k + 1}/{n_trials} ({time.time() - t0:.0f} s)", flush=True)
    elif kind == "null_weightperm":
        rates, exclude = rates_of(m), set(int(b) for b in m.stim["bodyId"])
        rec_syn = [o for o in m.net.objects if type(o).__name__ == "Synapses" and o.source is m.G and o.target is m.G
                   and "w" in o.variables]
        base_w = np.array(rec_syn[0].w_[:])
        draws = spec["draws"] if not reduced else min(spec["draws"], max(1, n_trials))
        for k in range(draws):
            m.restore()
            rec_syn[0].w_[:] = np.random.default_rng(10000 + k).permutation(base_w)
            m.set_stim_rates(rates)
            m.run(LADDER_MS)
            sp = m.spike_frame()
            _, n, n_sp, n_act = _counts(m, sp, 0, LADDER_MS, exclude)
            rows.append(dict(k=k, n_active=n_act, n_spikes=n_sp, cns_rate_hz=n_sp / n / (LADDER_MS / 1000.0),
                             fraction_active=n_act / n, **_mn9(m, sp, LADDER_MS / 1000.0, spec["data"])))
            print(f"[phase1b] {name} draw {k + 1}/{draws} ({time.time() - t0:.0f} s)", flush=True)
    elif kind == "null_dc":
        draws = spec["draws"] if not reduced else min(spec["draws"], max(1, n_trials))
        for k in range(draws):
            nd = rewire_null(edges, seed=20000 + k, mode="degree_corrected", neurons=neurons, data_dir=data_dir)
            mk = build(neurons, nd, stim_types, st, spec["seed"])
            row = run_ladder_trial(mk, rates_of(mk), spec["data"], set(int(b) for b in mk.stim["bodyId"]))
            row.update(k=k, neuropil_source=nd.attrs.get("neuropil_source"), n_recurrent=int(mk.n_chem),
                       n_lif=int(len(mk.lif_ids)))
            rows.append(row)
            if k == 0:
                size = dict(n_lif=int(len(mk.lif_ids)), n_recurrent=None, n_stimulated=int(len(mk.stim)),
                            n_driven=int((rates_of(mk) > 0).sum()))
            del mk        # one network in memory at a time
            print(f"[phase1b] {name} draw {k + 1}/{draws} ({time.time() - t0:.0f} s)", flush=True)
    if kind != "null_dc":
        size = dict(n_lif=int(len(m.lif_ids)), n_recurrent=int(m.n_chem), n_stimulated=int(len(exclude)),
                    n_driven=int((rates > 0).sum()))
    rec = dict(arm=name, spec=spec, options=opt.__dict__, reduced=reduced, data_dir=data_dir, **size, pool=pool, drive_hz=hz,
               group_sizes=group_sizes, unknown_transmitter=unknown, build_s=round(built, 1),
               wall_s=round(time.time() - t0, 1), trials=rows,
               registration=registry.stamp(REG), provenance=provenance(data_dir if spec["data"] != "flywire" else None))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(rec, indent=1, default=float), encoding="utf-8")
    print(f"[phase1b] {name}: {len(rows)} runs in {rec['wall_s']} s -> {out_dir / (name + '.json')}"
          + ("   (SMOKE: not a result)" if reduced else ""))


def run_part(part, repo, parallel=2):
    arms = PARTS[part]
    (OUT / "arms").mkdir(parents=True, exist_ok=True)
    procs, failed = [], []
    for a in arms:
        while len([p for p in procs if p[1].poll() is None]) >= parallel:
            time.sleep(5)
        log = open(OUT / "arms" / f"{a}.log", "w", encoding="utf-8")
        procs.append((a, subprocess.Popen([sys.executable, __file__, "arm", a, str(repo or "-")], stdout=log,
                                          stderr=subprocess.STDOUT, cwd=ROOT)))
    for a, p in procs:
        if p.wait() != 0:
            failed.append(a)
    for a in arms:
        print(f"--- {a}\n" + "".join((OUT / "arms" / f"{a}.log").read_text(encoding="utf-8").splitlines(True)[-5:]))
    if failed:
        raise SystemExit(f"[phase1b] {part}: arms failed: {failed}")


# ------------------------------------------------------------------------------------------------ scoring
def _load_arm(name, required=True):
    f = OUT / "arms" / f"{name}.json"
    if not f.exists():
        if required:
            raise SystemExit(f"[phase1b] arm {name} has no result ({f.relative_to(ROOT)})")
        return None
    rec = json.loads(f.read_text(encoding="utf-8"))
    st = rec["registration"]
    if st.get("model_hash") != REG["model"]["hash"] or not st.get("matches"):
        raise SystemExit(f"[phase1b] arm {name} was not run under this registration ({st})")
    if rec.get("reduced"):
        raise SystemExit(f"[phase1b] arm {name} is a smoke run (reduced), not a result")
    if json.loads(json.dumps(rec["spec"])) != json.loads(json.dumps(ARMS[name])):
        raise SystemExit(f"[phase1b] arm {name} was run with another specification than the registered one")
    return rec


def _col(rec, key):
    return np.array([t[key] for t in rec["trials"]], dtype=float)


def _responds(rec, note):
    x = _col(rec, "mn9_hz")
    e, lo, hi = stats.bootstrap(x)
    return stats.scored(e, lo, hi, low=RESPONDS, strict=True, n=len(x), note=note)


def vnc_group(label):
    """Outcome B grouping: "VNC" for every VNC neuropil label (VNC_STEMS, any side), else the label itself."""
    return "VNC" if str(label).split("(")[0] in VNC_STEMS else str(label)


def _merge(by_label, fn):
    out = {}
    for g, v in by_label.items():
        k = fn(g)
        out[k] = [a + b for a, b in zip(out.get(k, [0] * len(v)), v)] if k in out else list(v)
    return out


def _self_sustained_without(trial, key, group, sizes):
    """The self-sustained rule recomputed with one group's cells left out of both windows (gen-6 Outcome B)."""
    n = sum(sizes.values()) - sizes.get(group, 0)
    if n <= 0:
        return None
    d = trial["n_spikes"] - trial[f"drive_by_{key}"].get(group, [0])[0]
    t = trial["tail_spikes"] - trial[f"tail_by_{key}"].get(group, [0])[0]
    drive_hz, tail_hz = d / n / (DRIVE_MS / 1000.0), t / n / ((TAIL_MS // 2) / 1000.0)
    return bool(tail_hz >= 0.1 * drive_hz and tail_hz >= 0.01)


def _tail_groups(r):
    """Per arm, for gen-6 Outcome B: the group with the largest share of tail spikes over the self-sustained
    trials, that share, and how many trials stay self-sustained without it. On MaleCNS the groups are the
    dominant neuropils with every VNC neuropil merged into one group "VNC" (vnc_group); the label -> group
    map is reported so a VNC label missing from VNC_STEMS is visible. FlyWire: superclass."""
    sizes_all = r.get("group_sizes") or {}
    key = "neuropil" if "neuropil" in sizes_all else "superclass"
    if key == "neuropil":       # merge VNC labels in the sizes and in every trial's per-group counts
        labels = sorted(sizes_all["neuropil"])
        label_map = {g: vnc_group(g) for g in labels}
        sizes_m = {}
        for g, n in sizes_all["neuropil"].items():
            sizes_m[label_map[g]] = sizes_m.get(label_map[g], 0) + n
        r = dict(r, group_sizes=dict(sizes_all, vnc_merged=sizes_m), trials=[
            dict(t, tail_by_vnc_merged=_merge(t["tail_by_neuropil"], vnc_group),
                 drive_by_vnc_merged=_merge(t["drive_by_neuropil"], vnc_group))
            for t in r["trials"] if "tail_by_neuropil" in t])
        sizes_all, key = r["group_sizes"], "vnc_merged"
    else:
        label_map = None
    tr = [t for t in r["trials"] if f"tail_by_{key}" in t]
    ss = [t for t in tr if t["self_sustained"]]
    if not ss or key not in sizes_all:
        return dict(key=key, top_group=None, top_share=None, self_sustained_without_top=None, label_map=label_map)
    tot = {}
    for t in ss:
        for g, (spk, _, _) in t[f"tail_by_{key}"].items():
            tot[g] = tot.get(g, 0) + spk
    allspk = sum(tot.values())
    top = max(tot, key=tot.get)
    without = [_self_sustained_without(t, key, top, sizes_all[key]) for t in tr]
    return dict(key=key, top_group=top, top_share=(tot[top] / allspk) if allspk else None,
                self_sustained_without_top=int(sum(bool(x) for x in without)),
                tail_spikes_by_group={g: int(v) for g, v in sorted(tot.items(), key=lambda kv: -kv[1])},
                label_map=label_map)


def _sweep_summary(recs):
    """Per family and drive: the drive-dependent and runaway scales, from the per-trial records."""
    out = {}
    for fam in FAMILIES:
        for drive in ("sugar", "blind"):
            rows = []
            for w in GRID_W:
                r = recs.get(f"sw_{fam}_{drive}_{_w(w)}")
                if r is None:
                    continue
                tr = r["trials"]
                ss = [t["self_sustained"] for t in tr]
                rows.append(dict(w_scale=w, cns_rate_hz=float(np.median([t["cns_rate_hz"] for t in tr])),
                                 fraction_active=float(np.median([t["fraction_active"] for t in tr])),
                                 n_active=[t["n_active"] for t in tr], tail_rate_hz=float(np.median([t["tail_rate_hz"] for t in tr])),
                                 self_sustained_trials=int(sum(ss)), trials=len(tr),
                                 mn9=[t.get("mn9_hz", t.get("mn9_contra_hz")) for t in tr] if drive == "sugar" else None,
                                 mn9_max_cell=[t.get("mn9_max_cell_hz") for t in tr] if drive == "sugar" else None,
                                 mn9_li=_li_summary(tr) if drive == "sugar" else None,
                                 tail_groups=_tail_groups(r)))
            dep = [x["w_scale"] for x in rows if x["self_sustained_trials"] == 0 and x["cns_rate_hz"] < 1.0]
            run = [x["w_scale"] for x in rows if x["self_sustained_trials"] > x["trials"] / 2]
            out[f"{fam}_{drive}"] = dict(grid=rows, largest_drive_dependent=max(dep) if dep else None,
                                         smallest_runaway=min(run) if run else None,
                                         bimodal_hint=[x["w_scale"] for x in rows
                                                       if len(x["n_active"]) > 1 and max(x["n_active"]) > 2 * max(1, min(x["n_active"]))])
    return out


def score(repo):
    from flycns.bench import provenance
    ladder = {a: _load_arm(a) for a in ["ML0_m1"] + list(LADDER)}
    nulls = {a: _load_arm(a) for a in ("null_weightperm", "null_dc")}
    sweep = {a: _load_arm(a, required=False) for a in ARMS if ARMS[a]["kind"] == "sweep"}
    missing_sweep = sorted(a for a, r in sweep.items() if r is None)
    sweep = {a: r for a, r in sweep.items() if r is not None}
    U = {}
    U["ML0_responds"] = _responds(ladder["ML0_m1"], "M1 under a fresh seed: MaleCNS MN9 rate (mean of its cells), Hz")
    x = _col(ladder["ML4_wscale04"], "mn9_hz")
    e, lo, hi = stats.bootstrap(x)
    U["ML_wscale04_silent"] = stats.scored(e, lo, hi, high=RESPONDS, n=len(x),
                                           note="w_scale 0.4 alone (every other setting M1's): MN9 rate, Hz; PASS = silent")
    U["ML_single_switches_respond"] = stats.combine(
        [_responds(ladder[a], f"{a}: {', '.join(LADDER[a])} switched to flycns's value") for a in SINGLE],
        note="every single switch other than w_scale leaves MN9 responding")
    real_mn9 = float(np.mean(_col(ladder["ML0_m1"], "mn9_hz")))
    real_cns = float(np.median(_col(ladder["ML0_m1"], "cns_rate_hz")))
    for check, arm in (("MS1_weightperm_specific", "null_weightperm"), ("MS2_degree_corrected_specific", "null_dc")):
        nv = _col(nulls[arm], "mn9_hz")
        null_cns = float(np.median(_col(nulls[arm], "cns_rate_hz")))
        alive = bool(len(nv)) and real_cns > 0 and null_cns >= ALIVE_FRACTION * real_cns
        rec = stats.null_percentile(real_mn9, nv.tolist(), null_alive=alive,
                                    note=f"real = ML0's mean MN9; null whole-CNS median {null_cns:.4f} Hz vs real {real_cns:.4f} Hz")
        rec.update(null_cns_rate_hz_median=null_cns, real_cns_rate_hz_median=real_cns, n_draws=int(len(nv)),
                   null_n_active=[t["n_active"] for t in nulls[arm]["trials"]])
        U[check] = rec
    registry.verify_bands(REG, U)
    # pre-registered secondary readouts (CRITERIA["secondary"]): the same checks on the larger MN9 cell
    S = {}
    x = _col(ladder["ML0_m1"], "mn9_max_cell_hz")
    e, lo, hi = stats.bootstrap(x)
    S["ML0_responds_maxcell"] = stats.scored(e, lo, hi, low=RESPONDS, strict=True, n=len(x),
                                             note="ML0: the larger MN9 cell per trial, Hz")
    x = _col(ladder["ML4_wscale04"], "mn9_max_cell_hz")
    e, lo, hi = stats.bootstrap(x)
    S["ML_wscale04_silent_maxcell"] = stats.scored(e, lo, hi, high=RESPONDS, n=len(x),
                                                   note="ML4 (w_scale 0.4): the larger MN9 cell per trial, Hz")
    real_max = float(np.mean(_col(ladder["ML0_m1"], "mn9_max_cell_hz")))
    for check, arm in (("MS1_weightperm_specific_maxcell", "null_weightperm"),
                       ("MS2_degree_corrected_specific_maxcell", "null_dc")):
        null_cns = float(np.median(_col(nulls[arm], "cns_rate_hz")))
        alive = real_cns > 0 and null_cns >= ALIVE_FRACTION * real_cns
        S[check] = stats.null_percentile(real_max, _col(nulls[arm], "mn9_max_cell_hz").tolist(), null_alive=alive,
                                         note="real = ML0's mean of the larger MN9 cell")
    # pre-registered laterality readout (CRITERIA["secondary"]["laterality"]): reported, not a verdict here;
    # the gen-6 rule holds w_scale if the median is at or above LI_HOLD at its candidate scale
    LI = dict(hold_threshold=LI_HOLD, ladder={a: _li_summary(r["trials"]) for a, r in ladder.items()},
              nulls={a: _li_summary(r["trials"]) for a, r in nulls.items()},
              cells=dict(ids=ladder["ML0_m1"]["trials"][0]["mn9_cells"], sides=ladder["ML0_m1"]["trials"][0]["mn9_sides"]))
    v = {k: r["verdict"] for k, r in U.items()}
    lad = v["ML_wscale04_silent"], v["ML_single_switches_respond"]
    if lad == ("PASS", "PASS"):
        ladder_outcome = "w_scale alone accounts for the male MN9 zero, as on the female"
    elif lad[0] == "FAIL":
        ladder_outcome = "MN9 still responds at w_scale 0.4 on the male data: the male zero is not w_scale; stop for review"
    elif lad[1] == "FAIL":
        bad = [p["note"].split(":")[0] for p in U["ML_single_switches_respond"]["parts"] if p["verdict"] == "FAIL"]
        ladder_outcome = f"a second setting silences MN9 on the male data: {', '.join(bad)}"
    else:
        ladder_outcome = "the ladder does not decide (UNRESOLVED parts); more trials before any conclusion"
    sp = v["MS1_weightperm_specific"], v["MS2_degree_corrected_specific"]
    if sp == ("PASS", "PASS"):
        spec_outcome = "M1's response is wiring-specific against both nulls and stands"
    elif "FAIL" in sp:
        spec_outcome = ("M1's 'responds' at w_scale 1.0 is not specific to the real wiring: rewired networks drive MN9 "
                        "as well; phase 1's outcome is downgraded")
    else:
        spec_outcome = "specificity undecided: " + "; ".join(
            f"{c}: {U[c].get('note', '')}" for c in ("MS1_weightperm_specific", "MS2_degree_corrected_specific")
            if v[c] == "UNRESOLVED")
    reported = dict(
        ladder_male={a: dict(switched=LADDER.get(a, []), mn9_hz=list(stats.bootstrap(_col(r, "mn9_hz"))),
                             fired_trials=int((_col(r, "mn9_hz") > 0).sum()), trials=len(r["trials"]),
                             n_active_median=float(np.median(_col(r, "n_active"))),
                             n_active_min_max=[int(_col(r, "n_active").min()), int(_col(r, "n_active").max())],
                             mn9_cells=r["trials"][0]["mn9_cells"],
                             per_cell_fired=[int(sum(t["mn9_per_cell_hz"][i] > 0 for t in r["trials"]))
                                             for i in range(len(r["trials"][0]["mn9_per_cell_hz"]))],
                             per_cell_mean_hz=[float(np.mean([t["mn9_per_cell_hz"][i] for t in r["trials"]]))
                                               for i in range(len(r["trials"][0]["mn9_per_cell_hz"]))],
                             mn9_max_cell_hz=list(stats.bootstrap(_col(r, "mn9_max_cell_hz"))))
                     for a, r in ladder.items()},
        ladder_female=P1["result"]["ladder_female"],
        m1_run22=dict(mn9_hz_mean=P1["result"]["m1_mn9_hz_mean"], ci95=P1["result"]["m1_mn9_ci95"]),
        nulls={a: dict(mn9_hz=_col(r, "mn9_hz").tolist(), n_active=[t["n_active"] for t in r["trials"]],
                       cns_rate_hz=_col(r, "cns_rate_hz").tolist()) for a, r in nulls.items()},
        sweep=_sweep_summary(sweep), sweep_missing=missing_sweep,
        wall_s={a: r["wall_s"] for a, r in {**ladder, **nulls, **sweep}.items()})
    report = dict(benchmark=LABEL, criteria=CRITERIA, uncertainty=U, checks={k: x == "PASS" for k, x in v.items()},
                  secondary=S, laterality=LI,
                  ladder_outcome=ladder_outcome, specificity_outcome=spec_outcome, reported=reported,
                  registration=registry.stamp(REG), provenance=provenance())
    (OUT / "phase1b.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    for k, x in v.items():
        print(f"  {x:<10} {k}")
    for k, r in S.items():
        print(f"  {r['verdict']:<10} {k}   (secondary)")
    m0 = LI["ladder"]["ML0_m1"]
    print(f"  MN9 laterality, ML0: median {m0['median']} over {m0['n_defined']}/{m0['n_trials']} trials "
          f"(hold at >= {LI_HOLD})")
    print(f"ladder: {ladder_outcome}\nspecificity: {spec_outcome}")
    for key, s in reported["sweep"].items():
        print(f"  {key:<24} drive-dependent up to {s['largest_drive_dependent']}; runaway from {s['smallest_runaway']}"
              + (f"; bimodal at {s['bimodal_hint']}" if s["bimodal_hint"] else ""))
    if missing_sweep:
        print(f"  sweep arms not run (reported section incomplete): {len(missing_sweep)}")


REG = registry.register(LABEL, CRITERIA, scripts=[__file__])     # exits here under FLYCNS_REGISTER_ONLY
require_clean(LABEL)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "parts":
        for p, arms in PARTS.items():
            print(f"{p:<28} {', '.join(arms)}" + ("   (needs the reference repository)" if p in NEEDS_SHIU else ""))
    elif mode in ("part", "arm", "score"):
        data_dir = sys.argv[4] if mode == "arm" and len(sys.argv) > 4 else "data"
        trials = int(sys.argv[5]) if mode == "arm" and len(sys.argv) > 5 else None
        smoke = mode == "arm" and (data_dir != "data" or trials is not None)
        if not smoke:         # a smoke run is quarantined under results/<label>/smoke/ and can never be scored
            refuse_overrides(f"phase 1b {mode}")
        repo_arg = {"part": 3, "arm": 3, "score": 2}[mode]
        given = sys.argv[repo_arg] if len(sys.argv) > repo_arg and sys.argv[repo_arg] != "-" else None
        needs = (mode == "part" and sys.argv[2] in NEEDS_SHIU) or (mode == "arm" and ARMS[sys.argv[2]]["data"] == "flywire")
        repo = shiu_repo(given) if (needs or given or os.environ.get("SHIU_REPO")) else None
        if mode == "part":
            run_part(sys.argv[2], repo)
        elif mode == "arm":
            run_arm(sys.argv[2], repo, data_dir, trials)
        else:
            score(repo)
    else:
        raise SystemExit(__doc__)
