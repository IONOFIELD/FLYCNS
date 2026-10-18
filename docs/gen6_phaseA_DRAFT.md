# Generation 6, phase A: DRAFT plan (not registered)

Status: DRAFT for review, 18 October 2026. Nothing here is registered and no code exists for it yet. It
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

| | MN9_R as in the data | MN9_R corrected |
|---|---|---|
| v-only reset (flycns) | cell 1 | cell 2 |
| v-and-g reset (Shiu) | cell 3 | cell 4 |

- Every cell runs the Phase 1b sweep (w 0.4 to 1.0), under the sugar drive and the blind drive. Everything
  else stays at the flycns settings.
- **MN9_R correction**, to choose one before registering:
  - (i) **mirror**: MN9_L's input partners copied onto MN9_R, swapping sides;
  - (ii) **normalise**: MN9_R's input weights scaled to MN9_L's total.
  Mirroring changes wiring; normalising keeps MN9_R's partners. Recommendation: (i), with (ii) reported.
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
- **Projection cut:** with drive (a), remove the antennal lobe's projection-neuron outputs to the lateral horn
  and the mushroom body, and measure whether the antennal-lobe tail persists.
- **Hypothesis, registered:**
  - H4: the reverberation sustains itself inside the antennal lobe. The antennal-lobe tail persists after the
    projection cut.
  - H4-null: it needs the lateral horn and beyond. The antennal-lobe tail collapses after the cut.
- **Secondary:** under drive (c), whether antennal lobe plus lateral horn still hold at least twice their
  drive share of the tail.

**A5: FUNCTION without runaway.** A new criterion, FUNCTION-q: per trial, MN9 above 0.5 Hz **in trials that
are not self-sustained**. It is scored as the fraction of non-self-sustained trials that respond, with a Wilson
interval. It sits alongside FUNCTION (the two-cell mean, unchanged) and does not replace it.

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
2. If cell 2 or 4 is viable and cells 1 and 3 are not, the MN9_R correction is necessary. It is adopted, as a
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

## Size

- 4 cells x 5 w x 2 drives = 40 sweep arms.
- 100 null draws.
- 2 extra drive compositions x 5 w.
- 1 projection cut x 5 w.

That is about 25-30 cloud jobs. Branch names stay under 150 characters, split as tonight.

## Open choices for review

1. The MN9_R correction: (i) mirror or (ii) normalise.
2. Whether A4's projection cut also removes the mushroom-body output, or only the lateral-horn output.
3. FUNCTION-q's bar: is "at least half of the non-self-sustained trials respond" right?
