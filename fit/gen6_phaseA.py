"""
Generation 6, phase A: the reset rule and MN9_R's input on the male data (docs/gen6_phaseA_DRAFT.md).

Phase 1b ended in outcome C: on the male data no synaptic scale is both functional and stable
(results/gen6_screen/screen_v2.json). docs/gen6_rule.md names the reset rule as the first setting to test before
any change of synapse model, and Phase 1b left MN9's one-sided response (laterality 1.0; MN9_R has 633 input
synapses against MN9_L's 6,358) and the antennal-lobe tail unexplained. This phase runs, under ONE registration:

  A1 x A2   2 x 3 cells: reset (v-only, flycns | v-and-g, Shiu) x MN9_R input (as in the data | mirrored from
            MN9_L, primary | normalised to MN9_L's total, reported), each swept over w_scale {0.4 .. 1.0} under the
            sugar and the blind drive. Everything else at the flycns (generation 5) settings.
  A3        specificity: M1 against 100 degree-corrected rewirings (PASS iff it beats at least 95).
  A4        where the blind-drive loop is: two drive compositions, two projection cuts (AL PN -> LH; AL PN -> LH and
            MB) and two in-AL cuts (cholinergic LN outputs; every cholinergic PN -> PN/LN), under cell 1.

Scoring is fit/gen6_phaseA_score.py; both files are hashed into this registration.

    python fit/gen6_phaseA.py parts                         the cloud jobs and their arms
    python fit/gen6_phaseA.py part <part>                   run one job's arms, in parallel processes
    python fit/gen6_phaseA.py arm <arm> [data_dir] [trials] run one arm; a data_dir other than "data" or a trial
                                                            override is a SMOKE run, written under
                                                            results/gen6_phaseA/smoke/ and never scored
    python fit/gen6_phaseA.py preflight [data_dir]          no simulation: builds every transformed edge table
                                                            and prints what each transform and cut does; writes
                                                            results/gen6_phaseA/preflight.json (run on the pinned
                                                            data before registering; its numbers go into the
                                                            registration's context)
    python fit/gen6_phaseA.py selftest                      the transforms on a hand-made table, with exact checks

A smoke arm (and parts, preflight, selftest) reads and writes no registration, so it runs before the registration
exists and never leaves a registration file behind.
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

LABEL = "gen6_phaseA"
OUT = ROOT / "results" / LABEL
SCORE_SCRIPT = ROOT / "fit" / "gen6_phaseA_score.py"
CELLTYPES = ROOT / "data" / "gen6_phaseA_celltypes.json"
CELLTYPES_SHA256 = "7d5e0846538a078490f83fee6418c138eeae446c71f199e22501bff204029e05"   # data/gen6_phaseA_celltypes.json as committed
MN9_L_ID, MN9_R_ID = 10331, 16949          # MaleCNS v1.0; asserted against type == "MN9" and soma side
LADDER_TRIALS, LADDER_MS = 30, 1000         # as M1 (phase 1, phase 1b)
SWEEP_TRIALS, SETTLE_MS, DRIVE_MS, TAIL_MS = 10, 200, 1000, 500
BIN_MS = 50
GRID_W = [0.4, 0.5, 0.6, 0.8, 1.0]
DRIVES = ("sugar", "blind")
NULL_DRAWS, NULL_PER_ARM = 100, 25
ALIVE_FRACTION = 0.1          # Phase 1b: null median whole-CNS rate >= 10% of the real arm's median
MALE_SUGAR = ["LB3b", "LB3c"]
SUGAR_HZ, BLIND_HZ = 100.0, 20.0
EXCLUDED_SUBCLASSES_EXTRA = {"auditory", "wind_gravity", "campaniform sensilla"}
EXCLUDED_PREFIXES = ("JO-", "LC", "LPLC", "SNpp", "pC1", "DNg02", "L1", "L2", "L3", "L5", "Pm3", "Mi1", "Tm2")
LH_ROIS, CA_ROIS = ("LH(L)", "LH(R)"), ("CA(L)", "CA(R)")
MULTIGLOM_PREFIXES = ("M_", "MZ_", "CB")    # multiglomerular mlACT PN names; reported within cut (ii), not excluded

# Settings. FLY = the declared flycns model (generation 5 defaults; fit/shiu2024_phase1b.py FLY). M1 = the phase-1
# male arm (Shiu's choices), used only by A3, as Phase 1b's MS2 used it.
FLY = dict(reset="v", stimulation="source", integration="euler", adaptation=True, w_scale=0.4, floor=5,
           amines="dropped", electrical=True)
M1 = dict(reset="v_and_g", stimulation="kick", integration="exact", adaptation=False, w_scale=1.0, floor=5,
          amines="excitatory", electrical=False)
# The 2 x 3 design. Cells 1-4 decide (B1); 2b and 4b are reported and never decide.
CELLS = {"c1": dict(reset="v", mn9="data"), "c2": dict(reset="v", mn9="mirror"), "c2b": dict(reset="v", mn9="normalise"),
         "c3": dict(reset="v_and_g", mn9="data"), "c4": dict(reset="v_and_g", mn9="mirror"),
         "c4b": dict(reset="v_and_g", mn9="normalise")}
DECIDING = ("c1", "c2", "c3", "c4")
SEED_BASE, TOPUP_BASE, A3_REAL_SEED, A3_NULL_BUILD_SEED, A3_REWIRE_BASE = 6000, 7000, 6100, 6101, 30000
CUTS = ("lh", "lhmb", "i", "ii")
COMPOSITIONS = ("b", "c")


def _w(w):
    return f"w{int(round(w * 100)):03d}"


def _pair_index(drive, w):
    """Index of (drive, w): the seed offset shared by every arm at that (drive, w), so comparisons are paired (M5)."""
    return DRIVES.index(drive) * len(GRID_W) + GRID_W.index(w)


def _arms():
    arms = {}
    for cell, c in CELLS.items():
        for drive in DRIVES:
            for w in GRID_W:
                i = _pair_index(drive, w)
                st = {**FLY, "reset": c["reset"], "w_scale": w}
                base = dict(kind="sweep", settings=st, drive=drive, mn9=c["mn9"], trials=SWEEP_TRIALS)
                arms[f"{cell}_{drive}_{_w(w)}"] = dict(seed=SEED_BASE + i, **base)
                arms[f"{cell}_{drive}_{_w(w)}_topup"] = dict(seed=TOPUP_BASE + i, topup_of=f"{cell}_{drive}_{_w(w)}", **base)
    arms["A3_real_m1"] = dict(kind="ladder", settings=M1, seed=A3_REAL_SEED, trials=LADDER_TRIALS, mn9="data")
    for j in range(NULL_DRAWS // NULL_PER_ARM):
        arms[f"A3_null_dc_{j}"] = dict(kind="null_dc", settings=M1, seed=A3_NULL_BUILD_SEED, mn9="data",
                                       draw_start=j * NULL_PER_ARM, draws=NULL_PER_ARM, trials=1)
    for w in GRID_W:
        i = _pair_index("blind", w)
        st = {**FLY, "w_scale": w}
        for comp in COMPOSITIONS:
            arms[f"A4_drive_{comp}_{_w(w)}"] = dict(kind="sweep", settings=st, drive="blind", composition=comp,
                                                    mn9="data", seed=SEED_BASE + i, trials=SWEEP_TRIALS)
        for cut in CUTS:
            arms[f"A4_cut_{cut}_{_w(w)}"] = dict(kind="sweep", settings=st, drive="blind", cut=cut, mn9="data",
                                                 seed=SEED_BASE + i, trials=SWEEP_TRIALS)
    return arms


ARMS = _arms()
PARTS = {}
for _cell in CELLS:
    for _drive in DRIVES:
        PARTS[f"pa-{_cell}-{_drive}"] = [f"{_cell}_{_drive}_{_w(w)}" for w in GRID_W]
        PARTS[f"pa-topup-{_cell}-{_drive}"] = [f"{_cell}_{_drive}_{_w(w)}_topup" for w in GRID_W]
PARTS["pa-a3-real"] = ["A3_real_m1"]
for _j in range(NULL_DRAWS // NULL_PER_ARM):
    PARTS[f"pa-a3-null-{_j}"] = [f"A3_null_dc_{_j}"]
for _comp in COMPOSITIONS:
    PARTS[f"pa-a4-drive-{_comp}"] = [f"A4_drive_{_comp}_{_w(w)}" for w in GRID_W]
for _cut in CUTS:
    PARTS[f"pa-a4-cut-{_cut}"] = [f"A4_cut_{_cut}_{_w(w)}" for w in GRID_W]
assert sorted(a for p in PARTS.values() for a in p) == sorted(ARMS), "every arm in exactly one part"
CONDITIONAL_PARTS = sorted(p for p in PARTS if p.startswith("pa-topup-"))   # run only when the scorer asks (B1)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def celltypes(check=True):
    """The committed type lists (data/gen6_phaseA_celltypes.json, B2). A registered run refuses another file."""
    if not CELLTYPES.exists():
        raise SystemExit(f"[phaseA] {CELLTYPES.relative_to(ROOT)} missing: run scripts/make_gen6_celltypes.py")
    got = sha256(CELLTYPES)
    if check and got != CELLTYPES_SHA256:
        raise SystemExit(f"[phaseA] {CELLTYPES.relative_to(ROOT)} sha256 {got[:12]} is not the registered "
                         f"{CELLTYPES_SHA256[:12]}")
    rec = json.loads(CELLTYPES.read_text(encoding="utf-8"))
    return {k: set(v) for k, v in rec["classes"].items()}, rec


CRITERIA = dict(
    question=("on the male CNS: does the reset rule, or completing MN9_R's input, give a synaptic scale that is both "
              "functional and stable; is M1's MN9 response specific to the real wiring at 100 draws; and where does "
              "the blind-drive reverberation sustain itself?"),
    plan="docs/gen6_phaseA_DRAFT.md (every definition there, section 'Definitions fixed before registering' wins)",
    sources=dict(phase1b="results/shiu2024_phase1b/registration_v5.json, phase1b.json",
                 gen6_rule=["docs/gen6_rule.md", "docs/gen6_rule_v2.md"],
                 screen="results/gen6_screen/screen_v2.json (outcome C)",
                 celltypes=dict(file="data/gen6_phaseA_celltypes.json", sha256=CELLTYPES_SHA256,
                                built_by="scripts/make_gen6_celltypes.py from the MaleCNS Cell Type Explorer repository")),
    settings=dict(flycns=FLY, M1=M1, cells=CELLS, deciding=list(DECIDING), grid=GRID_W),
    protocol=dict(
        sweep=(f"per trial: restore, {SETTLE_MS} ms silence, {DRIVE_MS} ms drive, {TAIL_MS} ms with every stimulus rate at "
               f"0; {SWEEP_TRIALS} trials; one network per arm; readouts as Phase 1b's run_sweep_trial"),
        drives=dict(sugar=f"every {' and '.join(MALE_SUGAR)} cell at {SUGAR_HZ:.0f} Hz",
                    blind=(f"fit/select_wscale.py's drive, as Phase 1b: a fixed 10% (numpy default_rng(0)) of the "
                           f"eligible sensory cells, at {BLIND_HZ:.0f} Hz"),
                    composition=("A4 (M3): the stimulated types and the driven set of the blind drive kept, so the "
                                 "network is the same; rate set to 0 for (b) driven cells with superclass ol_sensory or a "
                                 "transmitter (consensusNt, else predictedNt) other than acetylcholine; (c) those, plus "
                                 "types starting ORN_ or HRN_")),
        ladder=f"A3 real arm: as M1, {LADDER_TRIALS} trials of {LADDER_MS} ms at sugar {SUGAR_HZ:.0f} Hz, seed {A3_REAL_SEED}",
        null=(f"A3: {NULL_DRAWS} degree-corrected rewirings (flycns.graph.rewire_null, mode degree_corrected), one "
              f"{LADDER_MS} ms trial each under M1; alive iff the null median whole-CNS rate >= {ALIVE_FRACTION} x the real "
              "arm's median (Phase 1b's rule)"),
        seeds=(f"sweep, drive and cut arms: {SEED_BASE} + index of (drive, w), shared by every arm at the same (drive, w) "
               f"(paired, M5); top-ups {TOPUP_BASE} + the same index; A3 real {A3_REAL_SEED}; A3 null model "
               f"{A3_NULL_BUILD_SEED} with rewiring seeds {A3_REWIRE_BASE} + k, k = 0..{NULL_DRAWS - 1}")),
    mn9=dict(
        cells=dict(L=MN9_L_ID, R=MN9_R_ID, check="asserted against type == 'MN9' and soma side on the pinned data"),
        mirror=("cells c2 and c4 (B3): applied to load_graph's signed edges (at or above the floor), before the model is "
                "built. MN9_R's input is REPLACED by the mirror of MN9_L's: each partner P -> MN9_L (weight w) becomes "
                "P' -> MN9_R for every SIMULATED cell P' of P's type on the opposite side (one with at least one edge at "
                "or above the floor; adding an edgeless cell would change the simulated cell set), weight w / (number "
                "of such cells), "
                "kept as a float even below the floor. Side = flycns.graph.infer_side without the soma-x fallback "
                "(somaSide, then instance _L/_R); anything else is midline. Untyped, midline and no-match partners stay "
                "on P (P -> MN9_R, w). A mirrored edge takes P''s own model sign (the model signs every edge by its "
                "sender); if P' has no signed output, P's sign. MN9_R -> MN9_L becomes MN9_L -> MN9_R. MN9_R's "
                "outputs are unchanged. Repeated (pre, post) pairs are summed"),
        normalise=("cells c2b and c4b: MN9_R's existing input weights multiplied by (MN9_L's signed input total / "
                   "MN9_R's), both from load_graph's edges (M8); partners unchanged")),
    cuts=dict(
        rule=("A4 (B2): applied to load_graph's signed edges; defined by cell type (the committed lists) and the post "
              "cell's dominant_roi (data/roi_membership.parquet). A cell whose every edge is cut keeps a zero-weight "
              "self-edge, so the simulated cell set equals the uncut one (m5); such a cell has no input at or above the "
              "floor and never fires either way. On the pinned data a cut that removes no edge refuses to run"),
        lh="remove edges with pre an AL PN (type in ALPN) and post dominant_roi in LH(L), LH(R)",
        lhmb=("as lh, and also edges with pre an AL PN and post type in Kenyon_Cell or post dominant_roi in CA(L), "
              "CA(R)"),
        i="remove every out-edge of cells with type in ALLN whose transmitter (the edge's nt) is acetylcholine",
        ii=("remove edges with pre of an ALPN type and nt acetylcholine (all cholinergic ALPN types: uniglomerular, "
            "the two-glomerulus '+' types and the multiglomerular M_/MZ_/CB types; Jayson's decisions of 18 "
            "October), and post type in ALPN or ALLN. GABAergic and glutamatergic PNs are not cut. The synapses "
            "removed from the '+' types and from the M_/MZ_/CB types are reported (descriptions, not arms)")),
    thresholds=dict(
        responds_hz=0.5, rate_bar_hz=1.0, fraction_bar=0.10, li_bar=0.8, function_q_min_trials=5,
        function_q_need=0.5, wstar_min_self_sustained=5, null_pass_draws=95, alive_fraction=ALIVE_FRACTION,
        tail_share_factor=2.0, bimodal_factor=2.0,
        meaning=("FUNCTION (screen): sugar MN9 two-cell-mean interval wholly above responds_hz (lower edge exclusive). "
                 "FUNCTION-q: of the non-self-sustained sugar trials, the fraction with MN9 > responds_hz is at least "
                 "function_q_need, with at least function_q_min_trials such trials, else UNRESOLVED. STABILITY (a)/(b): "
                 "0 self-sustained trials; (c): blind intervals of whole-CNS rate and fraction active wholly below "
                 "rate_bar_hz and fraction_bar (PASS iff upper edge < bar; FAIL iff lower edge >= bar). LATERALITY: "
                 "median sugar LI < li_bar. W*: grid w with at least wstar_min_self_sustained of 10 baseline blind "
                 "trials self-sustained. A3: PASS iff real > draw (strict) for at least null_pass_draws valid draws "
                 "(absolute; with fewer valid draws it cannot pass). M9: tail share >= tail_share_factor x drive "
                 "share. m3: bimodal iff max n_active > bimodal_factor x min n_active")),
    decision=dict(
        viable=("a grid w at which FUNCTION (screen), FUNCTION-q and STABILITY (a), (b), (c) all PASS; the decision w is "
                "the smallest such w"),
        table=("c1 viable: stop for review (Phase 1b's C not replicated). Else c2 viable: mirror at c2's w (c3 reported "
               "if also viable). c3 only: v-and-g reset at c3's w. c4 only: both at c4's w. None: C"),
        laterality=("M7: an outcome that adopts the mirror (mirror, both) also needs LATERALITY PASS in its cell (c2, c4) "
                    "at its decision w; otherwise the outcome is H (rule v2 section 2): no default changes; v-and-g, "
                    "if viable, is reported"),
        top_up=("a candidate w (no component FAILs, at least one UNRESOLVED) in a deciding cell names its arm(s) for "
                "ONE top-up (seed 7000 + the pair index, 10 trials); the scorer pools the 10 + 10 trials for every "
                "component of that arm (STABILITY (a)/(b) then need 0 of 20; FUNCTION-q counts over the 20); after "
                "it, UNRESOLVED counts as not passing"),
        provisional="an adopted w is provisional until gen6_rule.md's refine and confirm steps (both nulls) pass"),
    scoring=("fit/gen6_phaseA_score.py, hashed into this registration: B1 decision table over cells 1-4; FUNCTION "
             "(screen), FUNCTION-q, STABILITY (a), (b), (c), LATERALITY for c2/c4 (M7); A3 null at 95 of 100 (M4); A4 "
             "readings against W* (M1, M2, M9); the top-up rule; every verdict as the draft defines it"),
    predictions={
        "Q1": ["The v-and-g reset makes the male blind drive stable at some w, by itself", "moderate"],
        "Q2": ["The MN9_R correction brings male laterality below 0.8", "high"],
        "Q3": ["A3 still UNRESOLVED at 100 draws", "moderate"],
        "Q4": ["the antennal-lobe tail persists after both projection cuts (they do not stop it by the M1 rule)", "high"],
        "Q5": ["No cell is viable, so the outcome stays C", "moderate"],
        "Q6": ["At least one in-AL cut stops it by the M1 rule", "moderate"]},
    deviation=("A3's bar (at least 95 of 100 draws) differs from Phase 1b's MS2 (every one of 20), and was proposed after "
               "MS2 came out at 19 of 20; MS2 is not re-scored (M4)"),
)


# ------------------------------------------------------------------------------------------------ data and drives
def male_tables(data, st):
    from flycns.graph import load_graph
    from flycns.integrity import LOADED
    neurons, edges = load_graph(data, min_weight=st["floor"], amines=st["amines"])
    unknown = dict(edges=LOADED.get("n_dropped_unsigned_edges"), synapses=LOADED.get("n_dropped_unsigned_synapses"),
                   silent_presynaptic=LOADED.get("n_silent_presynaptic"))
    return neurons, edges, unknown


def male_blind_pool(neurons):
    """fit/select_wscale.py's eligible pool and its fixed 10% sample (as fit/shiu2024_phase1b.py)."""
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
        raise SystemExit("[phaseA] no eligible sensory neurons for the blind drive")
    stim_types = sorted(set(t[neurons.bodyId.isin(driven)]))
    return stim_types, driven, int(len(pool))


def nt_used(neurons):
    """The transmitter the fetch wrote on each cell's edges: consensusNt, else predictedNt (lower case)."""
    nt = neurons.set_index("bodyId")["consensusNt"]
    if "predictedNt" in neurons:
        nt = nt.fillna(neurons.set_index("bodyId")["predictedNt"])
    return nt.astype("string").str.lower()


def composition_zero(neurons, driven, comp):
    """A4 drive arms (M3): the driven cells whose rate is set to 0, and the count by reason."""
    meta = neurons.set_index("bodyId")
    ids = np.array(sorted(driven), dtype="int64")
    sc = meta["superclass"].reindex(ids).fillna("").astype(str)
    nt = nt_used(neurons).reindex(ids).fillna("<none>")
    t = meta["type"].reindex(ids).fillna("").astype(str)
    photo = (sc == "ol_sensory").to_numpy()
    non_ach = (nt != "acetylcholine").to_numpy()
    zero = photo | non_ach
    log = dict(driven=int(len(ids)), ol_sensory=int(photo.sum()), non_acetylcholine=int(non_ach.sum()))
    if comp == "c":
        olf = t.str.startswith(("ORN_", "HRN_")).to_numpy()
        log["orn_hrn"] = int(olf.sum())
        zero = zero | olf
    log["zeroed"] = int(zero.sum())
    log["kept"] = int(len(ids) - zero.sum())
    return set(int(b) for b in ids[zero]), log


# ------------------------------------------------------------------------------------------------ MN9 transforms
def side_of(neurons):
    """flycns.graph.infer_side without the soma-x fallback (B3): somaSide, then instance _L/_R; else None."""
    from flycns.graph import infer_side
    meta = neurons.set_index("bodyId")
    side = infer_side(meta.drop(columns=[c for c in ("x",) if c in meta]))
    return side.where(side.isin(["L", "R"]))


def mn9_cells(neurons, strict=True):
    """(MN9_L, MN9_R) bodyIds. On the pinned data they must be the registered ids."""
    meta = neurons.set_index("bodyId")
    side = side_of(neurons)
    cells = meta.index[meta["type"] == "MN9"]
    L = [int(b) for b in cells if side.get(b) == "L"]
    R = [int(b) for b in cells if side.get(b) == "R"]
    if len(L) != 1 or len(R) != 1:
        raise SystemExit(f"[phaseA] expected one MN9 per side, found L {L}, R {R}")
    if strict and (L[0], R[0]) != (MN9_L_ID, MN9_R_ID):
        raise SystemExit(f"[phaseA] MN9 cells {L[0]}, {R[0]} are not the registered {MN9_L_ID}, {MN9_R_ID}")
    return L[0], R[0]


def _sender_sign(edges):
    s = edges.groupby("pre")["sign"].first()
    return s


def mirror_mn9(edges, neurons, L, R):
    """B3: MN9_R's input replaced by the mirror of MN9_L's. Returns (edges, log)."""
    import pandas as pd
    meta = neurons.set_index("bodyId")
    side = side_of(neurons)
    typ = meta["type"]
    sign_of = _sender_sign(edges)
    nt_of = edges.groupby("pre")["nt"].first() if "nt" in edges else None
    by_type_side = {}
    for b, t in typ.dropna().items():
        s = side.get(b)
        if s in ("L", "R"):
            by_type_side.setdefault((t, s), []).append(int(b))
    in_net = set(edges["pre"]) | set(edges["post"])
    into_L = edges[edges["post"] == L]
    rows, log = [], dict(partners=int(len(into_L)), weight_in=float(into_L["weight"].sum()), kept=0, kept_w=0.0,
                         split_partners=0, below_floor_edges=0, below_floor_w=0.0, sign_mismatch_w=0.0,
                         no_signed_output_w=0.0, mn9_swap=0, opposite_not_in_network=0)
    floor = float(edges["weight"].min()) if len(edges) else 0.0
    for e in into_L.itertuples(index=False):
        P, w, sgn = int(e.pre), float(e.weight), float(e.sign)
        nt = getattr(e, "nt", None)
        if P == R:                                   # MN9_R -> MN9_L becomes MN9_L -> MN9_R
            rows.append(dict(pre=L, post=R, weight=w, sign=sgn, nt=nt))
            log["mn9_swap"] += 1
            continue
        t, s = typ.get(P), side.get(P)
        opp = by_type_side.get((t, {"L": "R", "R": "L"}.get(s)), []) if isinstance(t, str) and s in ("L", "R") else []
        absent = [q for q in opp if q not in in_net]      # a cell with no edge is not simulated; adding it would
        if absent:                                        # change the simulated cell set (m5), so it is not used
            log["opposite_not_in_network"] += len(absent)
            opp = [q for q in opp if q in in_net]
        if not opp:
            rows.append(dict(pre=P, post=R, weight=w, sign=sgn, nt=nt))
            log["kept"] += 1
            log["kept_w"] += w
            continue
        if len(opp) > 1:
            log["split_partners"] += 1
        for q in opp:
            wq = w / len(opp)
            if q in sign_of.index:
                sq = float(sign_of[q])
                if sq != sgn:
                    log["sign_mismatch_w"] += wq
            else:
                sq = sgn
                log["no_signed_output_w"] += wq
            if wq < floor:
                log["below_floor_edges"] += 1
                log["below_floor_w"] += wq
            rows.append(dict(pre=q, post=R, weight=wq, sign=sq,
                             nt=(nt_of.get(q, nt) if nt_of is not None else nt)))
    new = pd.DataFrame(rows, columns=["pre", "post", "weight", "sign", "nt"])
    new = (new.groupby(["pre", "post"], as_index=False)
           .agg(weight=("weight", "sum"), sign=("sign", "first"), nt=("nt", "first")))
    removed = edges[edges["post"] == R]
    log.update(removed_partners=int(len(removed)), removed_w=float(removed["weight"].sum()),
               new_partners=int(len(new)), weight_out=float(new["weight"].sum()))
    keep = edges[edges["post"] != R]
    cols = [c for c in keep.columns if c in new.columns]
    out = pd.concat([keep, new[cols]], ignore_index=True)
    out["weight"] = out["weight"].astype(float)
    return out, log


def normalise_mn9(edges, L, R):
    """MN9_R's input weights x (MN9_L's signed total / MN9_R's) (M8). Returns (edges, log)."""
    tl = float(edges.loc[edges["post"] == L, "weight"].sum())
    tr = float(edges.loc[edges["post"] == R, "weight"].sum())
    if tr <= 0:
        raise SystemExit("[phaseA] MN9_R has no signed input; cannot normalise")
    f = tl / tr
    out = edges.copy()
    out["weight"] = out["weight"].astype(float)
    out.loc[out["post"] == R, "weight"] *= f
    return out, dict(factor=f, mn9_L_in=tl, mn9_R_in_before=tr, mn9_R_in_after=float(out.loc[out["post"] == R, "weight"].sum()))


# ------------------------------------------------------------------------------------------------ cuts
def cut_mask(edges, neurons, roi, cut, ct):
    """Boolean mask of the edges a cut removes (B2)."""
    meta = neurons.set_index("bodyId")
    typ = meta["type"]
    pre_t, post_t = edges["pre"].map(typ), edges["post"].map(typ)
    post_roi = edges["post"].map(roi) if roi is not None else edges["post"].map(lambda _: None)
    nt = edges["nt"].astype("string").str.lower() if "nt" in edges else None
    is_pn = pre_t.isin(ct["ALPN"])
    if cut == "lh":
        return is_pn & post_roi.isin(LH_ROIS)
    if cut == "lhmb":
        return is_pn & (post_roi.isin(LH_ROIS) | post_t.isin(ct["Kenyon_Cell"]) | post_roi.isin(CA_ROIS))
    if cut == "i":
        return pre_t.isin(ct["ALLN"]) & (nt == "acetylcholine")
    if cut == "ii":
        return is_pn & (nt == "acetylcholine") & (post_t.isin(ct["ALPN"]) | post_t.isin(ct["ALLN"]))
    raise ValueError(cut)


def apply_cut(edges, neurons, roi, cut, ct):
    """The cut, keeping the simulated cell set (m5): a cell whose every edge is cut would leave the network (the
    model simulates the cells its edges name), so it keeps a zero-weight self-edge. Such a cell had no input at or
    above the floor, so it never fires with or without the placeholder; the placeholder only keeps it in every
    readout's cell count, as in the uncut network."""
    import pandas as pd
    m = cut_mask(edges, neurons, roi, cut, ct).fillna(False).to_numpy(dtype=bool)
    before = set(edges["pre"]) | set(edges["post"])
    out = edges[~m].reset_index(drop=True)
    after = set(out["pre"]) | set(out["post"])
    lost = sorted(before - after)
    if lost:
        ph = pd.DataFrame(dict(pre=lost, post=lost, weight=0.0, sign=1.0))
        if "nt" in out:
            ph["nt"] = "placeholder"
        out = pd.concat([out, ph[[c for c in out.columns if c in ph.columns]]], ignore_index=True)
    log = dict(removed_edges=int(m.sum()), removed_synapses=float(edges.loc[m, "weight"].sum()),
               removed_exc=float(edges.loc[m & (edges["sign"] > 0).to_numpy(), "weight"].sum()),
               removed_inh=float(edges.loc[m & (edges["sign"] < 0).to_numpy(), "weight"].sum()),
               placeholders=len(lost), placeholder_ids=lost[:20])
    if cut == "ii":           # descriptions only: how much of the cut comes from the '+' and the M_/MZ_/CB types
        pre_t = edges["pre"].map(neurons.set_index("bodyId")["type"]).fillna("").astype(str)
        multi = pre_t.str.startswith(MULTIGLOM_PREFIXES).to_numpy()
        plus = pre_t.str.contains("+", regex=False).to_numpy() & ~multi
        tot = float(edges.loc[m, "weight"].sum())
        for key, sel in (("from_plus_types", m & plus), ("from_m_mz_cb_types", m & multi)):
            syn = float(edges.loc[sel, "weight"].sum())
            log[key] = dict(types=int(pre_t[sel].nunique()), edges=int(sel.sum()), synapses=syn,
                            share=(syn / tot) if tot else None)
    return out, log


def transform(spec, neurons, edges, roi, smoke):
    """The arm's edge table (MN9 transform or cut) and what was done to it."""
    log = {}
    if spec.get("mn9") in ("mirror", "normalise"):
        L, R = mn9_cells(neurons, strict=not smoke)
        if spec["mn9"] == "mirror":
            edges, log = mirror_mn9(edges, neurons, L, R)
        else:
            edges, log = normalise_mn9(edges, L, R)
    if spec.get("cut"):
        ct, _ = celltypes(check=not smoke)
        edges, log = apply_cut(edges, neurons, roi, spec["cut"], ct)
        if not smoke and log["removed_edges"] == 0:
            raise SystemExit(f"[phaseA] cut {spec['cut']} removes no edge on the pinned data")
    return edges, log


# ------------------------------------------------------------------------------------------------ simulation
def _opt(st):
    from flycns.model import SimOptions
    return SimOptions(reset=st["reset"], stimulation=st["stimulation"], integration=st["integration"],
                      adaptation=st["adaptation"])


def build(neurons, edges, stim_types, st, seed):
    from flycns.model import CNSModel, LIFParams
    m = CNSModel(neurons, edges, stim_types, LIFParams(w_scale=st["w_scale"], seed=seed), electrical=st["electrical"],
                 options=_opt(st))
    m.store()
    return m


def _counts(m, sp, t0, t1, exclude):
    w = sp[(sp.t_ms >= t0) & (sp.t_ms < t1) & ~sp.bodyId.isin(exclude)]
    n = len(m.lif_ids) - int(np.isin(m.lif_ids, list(exclude)).sum())
    return w, n, int(len(w)), int(w.bodyId.nunique())


def _li(per):
    if len(per) < 2 or max(per) + min(per) <= 0:
        return None
    return float((max(per) - min(per)) / (max(per) + min(per)))


def _mn9(m, sp, seconds):
    cells = sorted(int(b) for b in m.meta.index[m.meta["type"] == "MN9"] if b in m.lif_index.index)
    side = m.meta["somaSide"] if "somaSide" in m.meta else None
    sides = [str(side.get(b)) if side is not None and isinstance(side.get(b), str) else "?" for b in cells]
    per = [float((sp.bodyId == b).sum() / seconds) for b in cells]
    nan = float("nan")
    return dict(mn9_hz=float(np.mean(per)) if per else nan, mn9_cells=cells, mn9_sides=sides, mn9_per_cell_hz=per,
                mn9_max_cell_hz=float(max(per)) if per else nan, mn9_li=_li(per),
                mn9_spikes=int(sum(round(x * seconds) for x in per)))


def _groups(m, exclude, roi):
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


def run_sweep_trial(m, rates, exclude, groups):
    """As fit/shiu2024_phase1b.py run_sweep_trial (settle, drive, tail), MaleCNS only."""
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
    _, _, s_sp, _ = _counts(m, sp, 0, SETTLE_MS, exclude)
    drive_hz, tail_hz = d_sp / n / (DRIVE_MS / 1000.0), t_sp / n / (half / 1000.0)
    bins = np.histogram(sp.t_ms[~sp.bodyId.isin(exclude)], bins=np.arange(0, total + 1, BIN_MS))[0]
    row = dict(n_active=d_act, n_spikes=d_sp, cns_rate_hz=drive_hz, fraction_active=d_act / n,
               settle_spikes=s_sp, tail_spikes=t_sp, tail_active=t_act, tail_rate_hz=tail_hz,
               self_sustained=bool(tail_hz >= 0.1 * drive_hz and tail_hz >= 0.01),
               bins_ms=BIN_MS, spikes_per_bin=[int(x) for x in bins])
    labels, sizes = groups
    for key, lab in labels.items():
        row[f"drive_by_{key}"] = _by_group(d, lab, sizes[key], DRIVE_MS / 1000.0)
        row[f"tail_by_{key}"] = _by_group(tw, lab, sizes[key], half / 1000.0)
    row.update(_mn9(m, sp[(sp.t_ms >= SETTLE_MS) & (sp.t_ms < SETTLE_MS + DRIVE_MS)], DRIVE_MS / 1000.0))
    return row


def run_ladder_trial(m, rates, exclude):
    m.restore()
    m.set_stim_rates(rates)
    m.run(LADDER_MS)
    sp = m.spike_frame()
    _, n, n_sp, n_act = _counts(m, sp, 0, LADDER_MS, exclude)
    row = dict(n_active=n_act, n_spikes=n_sp, cns_rate_hz=n_sp / n / (LADDER_MS / 1000.0), fraction_active=n_act / n)
    row.update(_mn9(m, sp, LADDER_MS / 1000.0))
    return row


def run_arm(name, data_dir="data", trials=None):
    from flycns.bench import provenance
    from flycns.graph import _dominant_roi, rewire_null
    spec = ARMS[name]
    st = spec["settings"]
    reduced = data_dir != "data" or (trials is not None and trials != spec["trials"])
    n_trials = trials if trials is not None else spec["trials"]
    out_dir = OUT / ("smoke" if reduced else "arms")
    t0 = time.time()
    if not reduced:
        require_data(data_dir, LABEL, ["neurons.parquet", "edges.parquet", "roi_membership.parquet"])
    neurons, edges, unknown = male_tables(data_dir, st)
    roi = _dominant_roi(data_dir)
    uncut_cells = len(set(edges["pre"]) | set(edges["post"]))
    edges, tlog = transform(spec, neurons, edges, roi, smoke=reduced)
    if spec.get("drive") == "blind":
        stim_types, driven, pool = male_blind_pool(neurons)
    else:
        stim_types = list(MALE_SUGAR)
        driven, pool = set(int(b) for b in neurons.loc[neurons["type"].isin(stim_types), "bodyId"]), None
    hz = BLIND_HZ if spec.get("drive") == "blind" else SUGAR_HZ
    zero, clog = (set(), None)
    if spec.get("composition"):
        zero, clog = composition_zero(neurons, driven, spec["composition"])
        if not reduced and spec["composition"] == "c" and not clog.get("orn_hrn"):
            raise SystemExit("[phaseA] drive (c): no ORN_/HRN_ cell in the driven set; the composition is not what "
                             "the plan describes")

    def rates_of(model):
        b = model.stim["bodyId"].to_numpy()
        return np.where(np.isin(b, list(driven)) & ~np.isin(b, list(zero)), hz, 0.0)
    kind, rows, size = spec["kind"], [], None
    if kind in ("sweep", "ladder"):
        m = build(neurons, edges, stim_types, st, spec["seed"])
        rates, exclude = rates_of(m), set(int(b) for b in m.stim["bodyId"])
        if spec.get("cut") or spec.get("mn9") in ("mirror", "normalise"):
            n_now = len(set(edges["pre"]) | set(edges["post"]))
            if n_now != uncut_cells:
                raise SystemExit(f"[phaseA] {name}: the transformed network has {n_now} cells, the untransformed "
                                 f"{uncut_cells} (m5)")
        groups = _groups(m, exclude, roi) if kind == "sweep" else None
        for k in range(n_trials):
            row = run_sweep_trial(m, rates, exclude, groups) if kind == "sweep" else run_ladder_trial(m, rates, exclude)
            rows.append(dict(k=k, **row))
            print(f"[phaseA] {name} {k + 1}/{n_trials} ({time.time() - t0:.0f} s)", flush=True)
        size = dict(n_lif=int(len(m.lif_ids)), n_recurrent=int(m.n_chem), n_stimulated=int(len(exclude)),
                    n_driven=int((rates > 0).sum()), total_input_hz=float(rates.sum()),
                    group_sizes=groups[1] if groups else None)
    elif kind == "null_dc":
        draws = spec["draws"] if not reduced else min(spec["draws"], max(1, n_trials))
        for j in range(draws):
            k = spec["draw_start"] + j
            nd = rewire_null(edges, seed=A3_REWIRE_BASE + k, mode="degree_corrected", neurons=neurons, data_dir=data_dir)
            mk = build(neurons, nd, stim_types, st, spec["seed"])
            row = run_ladder_trial(mk, rates_of(mk), set(int(b) for b in mk.stim["bodyId"]))
            row.update(k=k, neuropil_source=nd.attrs.get("neuropil_source"), n_lif=int(len(mk.lif_ids)))
            rows.append(row)
            if size is None:
                size = dict(n_lif=int(len(mk.lif_ids)), n_stimulated=int(len(mk.stim)), n_driven=int((rates_of(mk) > 0).sum()))
            del mk
            print(f"[phaseA] {name} draw {k} ({j + 1}/{draws}, {time.time() - t0:.0f} s)", flush=True)
    rec = dict(arm=name, spec=spec, options=_opt(st).__dict__, reduced=reduced, data_dir=data_dir, **size, pool=pool,
               drive_hz=hz, transform=tlog, composition=clog, unknown_transmitter=unknown,
               wall_s=round(time.time() - t0, 1), trials=rows,
               registration=registry.stamp(REG) if REG else None,
               provenance=provenance(data_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(rec, indent=1, default=float), encoding="utf-8")
    print(f"[phaseA] {name}: {len(rows)} runs in {rec['wall_s']} s -> {out_dir / (name + '.json')}"
          + ("   (SMOKE: not a result)" if reduced else ""))


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
        raise SystemExit(f"[phaseA] {part}: arms failed: {failed}")


# ------------------------------------------------------------------------------------------------ preflight
def preflight(data_dir="data"):
    """Every transform and cut on the given data, without simulating. Its numbers go into the registration's
    context; a cut that would drop cells, or a drive (c) without ORNs, shows here instead of in the cloud."""
    from flycns.graph import _dominant_roi
    smoke = data_dir != "data"
    if not smoke:
        require_data(data_dir, LABEL, ["neurons.parquet", "edges.parquet", "roi_membership.parquet"])
    neurons, edges, unknown = male_tables(data_dir, FLY)
    roi = _dominant_roi(data_dir)
    ct, ctrec = celltypes(check=False)
    out = dict(data_dir=data_dir, celltypes=dict(sha256=sha256(CELLTYPES), registered=CELLTYPES_SHA256,
                                                 counts=ctrec["counts"], source=ctrec["source"]),
               unknown_transmitter=unknown)
    meta = neurons.set_index("bodyId")
    out["celltypes_in_data"] = {c: dict(types=int(meta["type"].isin(v).groupby(meta["type"]).any().sum()),
                                        cells=int(meta["type"].isin(v).sum()),
                                        types_missing=sorted(set(v) - set(meta["type"].dropna()))[:30])
                                for c, v in ct.items()}
    L, R = mn9_cells(neurons, strict=not smoke)
    out["mn9"] = dict(L=L, R=R, status={b: (str(meta.loc[b, "status"]) if "status" in meta else None) for b in (L, R)})
    _, out["mirror"] = mirror_mn9(edges, neurons, L, R)
    _, out["normalise"] = normalise_mn9(edges, L, R)
    n_all = len(set(edges["pre"]) | set(edges["post"]))
    cuts = {}
    for cut in CUTS:
        cut_edges, log = apply_cut(edges, neurons, roi, cut, ct)
        log["cells_before"] = n_all
        log["cells_after"] = len(set(cut_edges["pre"]) | set(cut_edges["post"]))
        cuts[cut] = log
    out["cuts"] = cuts
    # a description on the committed lists, not an arm: the AL -> AL synapses by sender class x transmitter (corrects
    # the sign audit's class sums, which were built on a truncated type list)
    t_of = meta["type"]
    reg = edges["pre"].map(roi).fillna("").str.extract(r"^(AL)\(")[0]
    regp = edges["post"].map(roi).fillna("").str.extract(r"^(AL)\(")[0]
    alal = edges[(reg == "AL").to_numpy() & (regp == "AL").to_numpy()]
    cls = alal["pre"].map(t_of)
    sender = np.select([cls.isin(ct["ALPN"]), cls.isin(ct["ALLN"]), cls.isin(ct["Kenyon_Cell"])],
                       ["ALPN", "ALLN", "Kenyon_Cell"], default="other")
    sign = np.where(alal["sign"] > 0, "exc", "inh")
    nt_al = alal["nt"].astype("string").str.lower().fillna("?")
    g = alal.assign(sender=sender, nt_=nt_al.values, sgn=sign).groupby(["sender", "nt_", "sgn"])["weight"].sum()
    out["al_to_al_by_sender"] = {f"{a} {b} {c}": float(v) for (a, b, c), v in g.sort_values(ascending=False).items()}
    pn = edges[edges["pre"].map(meta["type"]).isin(ct["ALPN"])]
    by_roi = pn.groupby(pn["post"].map(roi).fillna("?"))["weight"].sum().sort_values(ascending=False)
    out["al_pn_out_weight_by_post_roi"] = {k: float(v) for k, v in by_roi.head(25).items()}
    _, driven, pool = male_blind_pool(neurons)
    out["blind"] = dict(pool=pool, driven=len(driven))
    out["compositions"] = {c: composition_zero(neurons, driven, c)[1] for c in COMPOSITIONS}
    OUT.mkdir(parents=True, exist_ok=True)
    f = (OUT / "smoke" / "preflight.json") if smoke else (OUT / "preflight.json")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1, default=float))
    print(f"[phaseA] preflight -> {f.relative_to(ROOT)}")
    return out


# ------------------------------------------------------------------------------------------------ selftest
def selftest():
    """The transforms on a hand-made table, with exact expectations. Returns (ok, message)."""
    import pandas as pd
    nrn = pd.DataFrame(dict(
        bodyId=[1, 2, 10, 11, 20, 21, 22, 30, 40, 50, 60, 61, 70, 71, 80, 23, 24, 62],
        type=["MN9", "MN9", "A", "A", "B", "B", "B", "C", None, "D", "PNu", "PNm", "LNa", "LNa", "KCg-m", "E", "E",
              "M_lPNy"],
        somaSide=["L", "R", "R", "L", "R", "L", "L", "M", None, None, "R", "R", "R", "L", "R", "L", "R", "R"],
        instance=["MN9_L", "MN9_R", "A_R", "A_L", "B_R", "B_L", "B_L", "C_M", None, "D_L", "PNu_R", "M_x_R", "LNa_R",
                  "LNa_L", "KCg-m_R", "E_L", "E_R", "M_lPNy_R"],
        superclass=["cb_motor"] * 2 + ["cb_intrinsic"] * 16))
    nrn.loc[nrn.bodyId == 61, "type"] = "M_lPNx"
    E = pd.DataFrame(dict(
        pre=[10, 20, 30, 40, 50, 2, 21, 11, 60, 61, 70, 60, 60, 60, 99, 10, 24, 62],
        post=[1, 1, 1, 1, 1, 1, 2, 3, 70, 60, 60, 81, 80, 82, 60, 22, 1, 60],
        weight=[100, 30, 7, 9, 11, 6, 40, 5, 20, 8, 12, 50, 9, 6, 5, 5, 8, 7],
        sign=[1, -1, -1, 1, 1, 1, 1, -1, 1, -1, 1, 1, 1, 1, 1, 1, 1, 1],
        nt=["acetylcholine", "gaba", "gaba", "acetylcholine", "acetylcholine", "acetylcholine", "acetylcholine",
            "gaba", "acetylcholine", "gaba", "acetylcholine", "acetylcholine", "acetylcholine", "acetylcholine",
            "acetylcholine", "acetylcholine", "acetylcholine", "acetylcholine"]))
    checks = []
    m, log = mirror_mn9(E, nrn, 1, 2)
    into_R = m[m.post == 2].set_index("pre")["weight"].to_dict()
    # A_R (10) -> MN9_L mirrors onto A_L (11); B_R (20) splits over B_L (21, 22; 22 has an input only, so no
    # signed output); C_M (30), untyped 40 and D_L (50, no R cell of type D) are kept; E_R (24) has an opposite
    # cell, E_L (23), that has no edge at all and is not simulated, so 24 is kept; MN9_R -> MN9_L becomes
    # MN9_L -> MN9_R; the old 21 -> MN9_R edge is removed
    checks.append(("mirror weights", into_R == {11: 100.0, 21: 15.0, 22: 15.0, 30: 7.0, 40: 9.0, 50: 11.0, 1: 6.0,
                                                24: 8.0}))
    checks.append(("mirror conserves", abs(log["weight_out"] - E.loc[E.post == 1, "weight"].sum()) < 1e-9))
    s = m[m.post == 2].set_index("pre")["sign"].to_dict()
    # 11's own model sign is -1 (11 -> 3 is gaba), so the mirrored edge from 11 is -1, a mismatch of 100
    checks.append(("mirror sign of P'", s[11] == -1.0 and s[21] == 1.0 and s[22] == -1.0 and log["sign_mismatch_w"] == 115.0))
    checks.append(("mirror log", log["kept"] == 4 and log["mn9_swap"] == 1 and log["split_partners"] == 1
                   and log["no_signed_output_w"] == 15.0 and log["opposite_not_in_network"] == 1))
    checks.append(("mirror keeps the cell set", (set(m.pre) | set(m.post)) == (set(E.pre) | set(E.post))))
    a = m[m.post == 1][["pre", "post", "weight", "sign"]].astype(float).reset_index(drop=True)
    b = E[E.post == 1][["pre", "post", "weight", "sign"]].astype(float).reset_index(drop=True)
    checks.append(("mirror leaves MN9_L", a.equals(b)))
    n2, nlog = normalise_mn9(E, 1, 2)
    checks.append(("normalise", abs(nlog["factor"] - 171 / 40) < 1e-12 and abs(nlog["mn9_R_in_after"] - 171) < 1e-9))
    ct = dict(ALPN={"PNu", "M_lPNx", "M_lPNy"}, ALLN={"LNa"}, Kenyon_Cell={"KCg-m"})
    roi = pd.Series({81: "LH(R)", 82: "CA(R)", 80: "gL(R)", 70: "AL(R)", 60: "AL(R)", 61: "AL(R)", 62: "AL(R)"})
    got = {c: sorted(map(tuple, E.loc[cut_mask(E, nrn, roi, c, ct).fillna(False).to_numpy(), ["pre", "post"]].values.tolist()))
           for c in CUTS}
    # (ii): every cholinergic ALPN onto a PN or LN: 60 -> 70 and the multiglomerular 62 -> 60; 61 (M_, GABA) is not cut
    want = dict(lh=[(60, 81)], lhmb=[(60, 80), (60, 81), (60, 82)], i=[(70, 60)], ii=[(60, 70), (62, 60)])
    checks.append(("cuts", got == want))
    cl, clog = apply_cut(E, nrn, roi, "lh", ct)     # 81's only edge is 60 -> 81: it keeps a zero-weight self-edge
    ph = cl[(cl.pre == 81) & (cl.post == 81)]
    _, ii = apply_cut(E, nrn, roi, "ii", ct)
    checks.append(("cut (ii) shares", ii["removed_synapses"] == 27.0 and ii["from_m_mz_cb_types"]["synapses"] == 7.0
                   and ii["from_plus_types"]["synapses"] == 0.0))
    checks.append(("cut keeps the cell set", (set(cl.pre) | set(cl.post)) == (set(E.pre) | set(E.post))
                   and len(ph) == 1 and float(ph.weight.iloc[0]) == 0.0 and clog["placeholders"] == 1))
    bad = [n for n, ok in checks if not ok]
    return not bad, ("mirror, normalise and the four cuts give the hand-computed tables" if not bad
                     else f"failed: {bad}; cuts {got}")


_mode = sys.argv[1] if __name__ == "__main__" and len(sys.argv) > 1 else ""
_smoke_arm = _mode == "arm" and ((len(sys.argv) > 3 and sys.argv[3] != "data") or len(sys.argv) > 4)
if _mode in ("parts", "preflight", "selftest") or _smoke_arm or __name__ not in ("__main__", "gen6_phaseA"):
    REG = None             # these modes compute nothing that is scored; no registration is read or written
else:
    REG = registry.register(LABEL, CRITERIA, scripts=[__file__, str(SCORE_SCRIPT)])   # exits under FLYCNS_REGISTER_ONLY
    require_clean(LABEL)

if __name__ == "__main__":
    if _mode == "parts":
        for p, arms in PARTS.items():
            print(f"{p:<26} {', '.join(arms)}" + ("   (only when the scorer asks for a top-up)" if p in CONDITIONAL_PARTS else ""))
    elif _mode == "selftest":
        ok, msg = selftest()
        print(("PASS  " if ok else "FAIL  ") + msg)
        sys.exit(0 if ok else 1)
    elif _mode == "preflight":
        preflight(sys.argv[2] if len(sys.argv) > 2 else "data")
    elif _mode in ("part", "arm"):
        data_dir = sys.argv[3] if _mode == "arm" and len(sys.argv) > 3 else "data"
        trials = int(sys.argv[4]) if _mode == "arm" and len(sys.argv) > 4 else None
        smoke = _mode == "arm" and (data_dir != "data" or trials is not None)
        if not smoke:
            refuse_overrides(f"phase A {_mode}")
            celltypes(check=True)
        if _mode == "part":
            run_part(sys.argv[2])
        else:
            run_arm(sys.argv[2], data_dir, trials)
    else:
        raise SystemExit(__doc__)
