# Generation 6, phase A: DRAFT plan (not registered)

Status: DRAFT for review, 18 October 2026. Nothing here is registered and no code exists for it yet.
Revised 18 October 2026 (05:19 PDT): the three open choices are decided by Jayson (section "Decisions");
findings from Grok's read-only signing audit are added (section "Signing audit"). It
follows from Phase 1b's outcome C (`RESULTS.md`, 18 October; `results/gen6_screen/screen_v2.json`): on the male
data no synaptic scale is both functional and stable. `docs/gen6_rule.md` says the reset rule is the first
setting to test before any change of synapse model. This phase does that, and fixes what Phase 1b could not
decide.

## Process rule learned in Phase 1b

The amendments to the rule were committed after the result branches existed, so their order could not be
proven. In this phase, **every rule, amendment, prediction and analysis script is committed before the cloud
runs are launched.** Anything decided after launch goes in a new file, dated, that is explicitly applied only
to later runs.

## Questions

| # | question | why |
|---|---|---|
| A1 | Does the reset rule (v-only vs v-and-g) decide male stability? | Phase 1b: the v-only reset multiplies the male whole-CNS rate about six-fold, while MN9 falls |
| A2 | Does correcting MN9_R's input make the male MN9 response two-sided? | MN9_R has 633 vs 6,358 input synapses; laterality is 1.0 |
| A3 | Is the male MN9 response specific to the real wiring? | MS2 was UNRESOLVED at 19 of 20 draws |
| A4 | Where does the blind-drive reverberation sustain itself? | about 55% of the tail is in the antennal lobe and lateral horn, against 17% of the drive |
| A5 | Does MN9 respond without the network running away? | at w 0.6 the FUNCTION pass came only from the runaway trials |

## Design

**A1 x A2: one 2 x 2 registration, crossed so the two effects separate.**

| | MN9_R as in the data | MN9_R mirrored (primary) | MN9_R normalised (reported) |
|---|---|---|---|
| v-only reset (flycns) | cell 1 | cell 2 | cell 2b |
| v-and-g reset (Shiu) | cell 3 | cell 4 | cell 4b |

- Every cell runs the Phase 1b sweep (w 0.4 to 1.0), under the sugar drive and the blind drive. Everything
  else stays at the flycns settings.
- **MN9_R correction (decided):** (i) **mirror** is primary; (ii) **normalise** is reported alongside it,
  in its own cells (2b, 4b), never deciding. Mirroring tests the real question (would MN9_R behave like MN9_L
  if its wiring were complete); normalising only scales whatever partners MN9_R kept.
  - **Mirror, defined before registering:** MN9_R's input is **replaced** by the mirror of MN9_L's input. Each
    partner P -> MN9_L (weight w, sign of P) becomes P' -> MN9_R, where P' is P's opposite-side partner of the
    same `type`, side taken from `instance`/`somaSide`.
  - **Partners with no opposite-side match, or on the midline:** kept on the same partner (P -> MN9_R, weight
    w). Their count and total weight are logged in the registration.
  - **Several cells of the same type on the opposite side:** to fix before registering (see open items).
  - **Normalise:** MN9_R's existing input weights scaled by (MN9_L total / MN9_R total), partners unchanged.
  - **Reported under both fixes:** LI. If LI falls below 0.8 under mirroring only, that is direct evidence the
    asymmetry came from the reconstruction.
- **Before registering**, record MN9_R's reconstruction status from `data/neurons.parquet` (the `status`
  column) in the registration.

**A3: specificity null with power.**
- Degree-corrected rewiring only. The weight permutation is dropped, because it silences the network.
- **100 draws.** PASS iff the real MN9 exceeds at least 95 of them. FAIL iff it does not exceed the null
  median. Otherwise UNRESOLVED. The alive rule is as in Phase 1b.
- Run at M1's settings, as Phase 1b's MS2 did, so the two can be compared. Phase 1b's MS2 stays UNRESOLVED;
  it is not re-scored.

**A4: where the loop is.**
- **Drive composition arms:** (a) the Phase 1b blind drive, unchanged; (b) excitatory sensory cells only
  (photoreceptors removed); (c) non-olfactory only (ORNs and HRNs also removed).
- **Projection cut (decided):** with drive (a), remove the antennal-lobe projection neurons' outputs.
  - Primary arm, **LH only:** AL PN -> LH edges removed.
  - Secondary arm, **LH + MB:** AL PN -> LH and AL PN -> MB (calyx) edges removed.
  - "Stops the instability" means STABILITY (b) and (c) pass under the blind drive at that w.
- **Interpretation, registered before launch:**

  | LH-only cut | LH + MB cut | reading |
  |---|---|---|
  | stops it | (any) | the AL-LH loop sustains the tail |
  | does not | stops it | the MB route matters |
  | does not | does not | the loop runs inside the AL itself (see A4-AL) |

- **A4-AL, direct test of the in-AL loop** (so the third reading is tested, not inferred by elimination). Drive
  (a), single cuts inside the AL:
  - (i) outputs of cholinergic AL local neurons removed;
  - (ii) uniglomerular PN -> PN and PN -> LN edges inside the AL removed (PN -> LH kept).
  These come from the signing audit, which found that the only excitatory recurrence left in AL and LH runs
  through cholinergic cells.
- **Secondary:** under drive (c), whether antennal lobe plus lateral horn still hold at least twice their
  drive share of the tail.

**A5: FUNCTION without runaway (decided).** FUNCTION-q, scored per w under the sugar drive:
- **Runaway trial:** a self-sustained trial as Phase 1b registers it (tail rate at least 10% of the drive rate
  and at least 0.01 Hz). This is the per-trial rule STABILITY (a) and (b) already count; no new threshold.
- **Response:** MN9 two-cell mean above 0.5 Hz over the drive window, in that trial (FUNCTION's bar).
- **Minimum:** at least 5 non-runaway trials. Fewer gives UNRESOLVED, not PASS or FAIL. (Phase 1b's ML0 split
  15/15 into quiet and active trials; at some w almost every trial may run away.)
- **PASS** iff at least half of the non-runaway trials respond. **FAIL** otherwise. Wilson 95% interval
  reported.
- FUNCTION-q sits alongside FUNCTION (the two-cell mean, unchanged) and does not replace it.

## Readouts and reporting

- Activity is reported **by mode** wherever trials are bimodal, never as one median across the gap. Phase 1b's
  ML0 had two modes, about 4-6k and about 11-12k active cells.
- **MN9:** both cells with bodyId and side, the two-cell mean (deciding), the max cell, laterality, and
  laterality restricted to trials with at least 5 spikes.
- **Tail groups:** per-label counts, the v2 grouping (VNC including `VNC-unspecified`), and rates from summed
  spikes over summed cells.
- **Every summary** is computed by a committed script (as `fit/gen6_screen_v2.py`), never in conversation.

## Decision rule (to finalise before registering)

1. A cell is **viable** if FUNCTION passes, FUNCTION-q passes and STABILITY (a), (b), (c) pass at some w.
2. If cell 2 or 4 is viable and cells 1 and 3 are not, the MN9_R correction is necessary. (Cells 2b and 4b
   are reported and never decide.) It is adopted, as a
   data correction, in the generation-6 freeze.
3. If cell 3 or 4 is viable and cells 1 and 2 are not, the reset rule is necessary. Generation 6 adopts the
   v-and-g reset.
4. If no cell is viable, the outcome stays C. The next phase is a change of synapse model (conductance-based),
   in its own plan.
5. Specificity (A3) and the antennal-lobe hypothesis (A4) are reported with their own verdicts. Neither changes
   1-4.

## Predictions (to log before launch)

| | prediction | confidence |
|---|---|---|
| Q1 | The v-and-g reset makes the male blind drive stable at some w, by itself | moderate |
| Q2 | The MN9_R correction brings male laterality below 0.8 | high |
| Q3 | A3 still UNRESOLVED at 100 draws (the real value sits inside the null's upper tail) | moderate |
| Q4 | H4 holds: the antennal-lobe tail persists after the projection cut | low |
| Q5 | No cell is viable, so the outcome stays C | moderate |

## Signing audit (Grok, 18 October 2026), checked against the code

- **Glutamate and GABA signing is correct.** One table (`flycns/graph.py` `SIGN_MAP`), glutamate -1 everywhere,
  as Shiu et al. 2024. The GABAergic ventral-lineage iPNs are -1. No per-type override touches AL or LH.
  Checked in the code on `main`. A sign error does not explain the AL/LH tail. **No sign is changed.**
- **The `"unclear"` fallback defect is real.** `scripts/fetch_malecns.py` writes
  `consensusNt.fillna(predictedNt)` into `edges.parquet`'s `nt` column. MaleCNS stores `"unclear"` as a
  string, not null, so the fallback never fires and those cells' outputs are dropped. The repo's own
  `results/checks/modulator_checks.json` shows it (ENS4: consensusNt `unclear`, predictedNt acetylcholine).
  The comment ("consensusNt, else predictedNt") is wrong for these cells. Grok's Explorer-based count:
  63 AL local neurons in 19 types; the exact model count needs the local data.
  - The fix can be made either at the fetch (changes the `edges.parquet` pin) or in `load_graph`, which
    re-derives `nt` from `neurons.parquet` (changes a hashed model file, not the data pin). Either way it
    rides with a generation freeze and is **not** part of phase A, so phase A stays comparable with Phase 1b.
  - Before deciding, record from `al_lh_sign_audit.py`: how many dropped AL/LH cells have `predictedNt` GABA
    or glutamate, and their AL -> AL output weight.
- **To run locally before registering** (read-only): `al_lh_sign_audit.py` (Grok, tested only on synthetic
  data). Its AL -> AL / AL -> LH / LH -> LH exc/inh/dropped totals go into the registration as context.
- **Not adopted for phase A:** a slow GABA_B-like inhibition and PN adaptation (Grok's (iv), (v)). Both are
  model changes. They belong in the synapse-model plan that outcome C points to, not in a phase that changes
  only the reset and MN9_R's input.

## Size

- 6 cells x 5 w x 2 drives = 60 sweep arms (cells 2b and 4b add 20).
- 100 null draws.
- 2 extra drive compositions x 5 w.
- 2 projection cuts (LH only; LH + MB) x 5 w.
- 2 in-AL cuts x 5 w.

That is about 35-40 cloud jobs. Branch names stay under 150 characters, split as in Phase 1b.

## Decisions (Jayson, 18 October 2026)

1. MN9_R: mirror primary, normalise reported; unmatched and midline partners kept on the same partner, count
   logged; LI reported under both.
2. Projection cut: LH only primary, LH + MB secondary, with the registered three-way reading.
3. FUNCTION-q: half of non-runaway trials; runaway = the Phase 1b self-sustained rule; response = 0.5 Hz per
   trial; fewer than 5 non-runaway trials gives UNRESOLVED.

## Open items before registering

1. Mirror mapping when the opposite side has several cells of the partner's type: split w equally across
   them, or match cell to cell by `instance`.
2. Whether `instance` or `somaSide` decides side when they disagree.
3. MN9_R's `status` from `data/neurons.parquet`.
4. The output of `al_lh_sign_audit.py` on the pinned data.
