# Generation 6: the w_scale rule (committed before Phase 1b runs)

Status: DRAFT for review, 14 October 2026. Commit this file **before** `FLYCNS_REGISTER_ONLY=1 python
fit/shiu2024_phase1b.py`, so the Phase 1b registration's git commit contains it. Phase 1b's own registration
says the generation-6 defaults are decided "in a separate registration"; this file is the rule that
registration will implement. It is frozen once the Phase 1b registration is committed; after that a change is a
new file (`gen6_rule_v2.md`) committed before the data it would be applied to. (Revised 17 October 2026, before
registration, after the read-only audit of that date: reset held fixed, MN9 per-cell readout, Outcome B data.)

## Why

Generation 5 picked w_scale 0.4 for quietness alone (`fit/select_wscale.py`). On the female data that value
silences MN9 under sugar (0 Hz, 0 of 30 trials), the only circuit with ground truth (Shiu et al. 2024). A
scale has to pass two tests, not one.

## Definitions

All readouts come from the Phase 1b sweep, family `male_flycns` (the declared flycns settings, `FLY` in
`fit/shiu2024_phase1b.py`, with only w_scale varied), on the grid `GRID_W = {0.4, 0.5, 0.6, 0.8, 1.0}`,
10 trials per arm. Intervals: `flycns.stats` percentile bootstrap over trials, 2,000 resamples, seed 0.

| Term | Definition |
|---|---|
| MN9 statistic | Mean spikes per MN9 cell per second over the drive window (the M1 statistic: mean of every MN9 cell). Each cell is also reported separately, with its bodyId. |
| MN9 max cell | The larger of the MN9 cells per trial (Phase 1b `mn9_max_cell_hz`). Reported next to every MN9 statistic. Run 22's male response is one cell (42.8 Hz vs 0.13 Hz, firing in 4 of 30 trials), so the two-cell mean halves a one-sided response. |
| FUNCTION (screen) | Under the sugar drive, the 95% interval of the MN9 statistic lies wholly above 0.5 Hz (lower edge exclusive). |
| FUNCTION (confirm) | At the candidate w, the MN9 statistic beats **both** nulls by `stats.null_percentile` (PASS = exceeds every one of 20 draws): the weight permutation and the degree-corrected rewiring, as Phase 1b defines them. UNRESOLVED counts as not passing. |
| Self-sustained trial | As Phase 1b registers it: whole-CNS rate in the last half of the 500 ms tail is at least 10% of the rate during the drive and at least 0.01 Hz. |
| STABILITY | All three: (a) 0 of 10 trials self-sustained under the sugar drive; (b) 0 of 10 under the blind drive; (c) under the blind drive, the 95% intervals of whole-CNS rate and fraction active lie wholly below 1 Hz and 10% (the generation-3 quietness bars, now with intervals). |
| Window | The set of grid w that pass FUNCTION (screen) and STABILITY. |

Stimulated cells are excluded from every whole-CNS readout, as in Phase 1b.

## What is held fixed, and why

Only w_scale moves. Every other setting stays at its generation-5 value, **the v-only reset included**. That
is a choice, not an oversight: on the female ladder (Phase 1, run 22) the v-only reset alone moves MN9 from
0 Hz to 231.8 Hz, so the reset is the other setting that dominates this circuit, and the sharp quiet-to-runaway
step between w 0.4 and 0.5 (`results/select_wscale/report.json`: whole-CNS rate 0.015 to 2.51 Hz) may be partly
a property of that reset. Changing two dominant settings at once would leave a result that names neither.
The reset is therefore not re-picked here. If the outcome is B or C, the reset is the first setting to test
next, in its own registration, before conductance-based synapses are considered.

## The rule

1. **Screen** the five grid points with the Phase 1b sweep table.
2. **Refine.** If the window is not empty, let w_hi be its smallest grid point and w_lo the grid point below
   it (or 0.35 if w_hi is 0.4). `fit/select_wscale_v2.py` runs w_lo + 0.05, w_lo + 0.10, ... up to w_hi, with
   the same arms, 10 trials, seeds disjoint from Phase 1b (base 5000) and from every scored generation-6 run.
3. **Confirm.** At each refined point in increasing order, run both nulls (20 draws each). The generation-6
   w_scale is the **smallest** point that passes FUNCTION (screen), FUNCTION (confirm) and STABILITY.
   If none of the refined points passes, try w_hi itself, then the next window point upward.
4. **Outcome:**

| Outcome | Condition | Action |
|---|---|---|
| **A** | A w passes step 3 | Change w_scale only. Refit every calibration that depends on w (list below). |
| **B** | FUNCTION passes at some w, but every such w fails STABILITY, and at the smallest of them one neuropil group (Phase 1b `tail_by_neuropil`, per trial, with `group_sizes`; summarised in phase1b.json `tail_groups`) carries at least 50% of tail spikes in the self-sustained trials, and STABILITY passes when that group's cells are left out of the readout | Report; no default changes on this basis. Name the group (expected: the VNC). Move Phase 4 earlier. |
| **C** | FUNCTION passes at some w, but no w passes STABILITY, and B's condition does not hold | Switch to conductance-based synapses (a new model; generation 7 planning). |
| **D** | FUNCTION (screen) fails at every grid point, 1.0 included | w_scale is not the cause on the male flycns settings. Stop. Name the setting from the Phase 1b ladder. No default changes. |

If Phase 1b's own registered checks change the picture (`ML_wscale04_silent` FAILS, or `MS1`/`MS2` FAIL),
their decision rules apply first and this rule waits for review.

## Generation 6 changes regardless of outcome (A only applies the w change)

- Drop the cb_motor 10 mV adaptation (no source; `flycns/graph.py` INTRINSIC_OVERRIDES).
- Refit every calibration whose value was chosen with w 0.4 in place (docs/CALIBRATION.md lists them: at least
  GF adaptation, the PEAK_HZ check, the A2 working point and the flight afferent load). The list is fixed in the
  generation-6 registration before any refit runs.
- Mark F3/F4 as calibrated (role change in `flycns/calibration.py`).
- Correct the frozen comment at the top of `flycns/protocols.py` (see below). Comments in model files change
  the model hash, so they ride with a refreeze; this is the next one.
- Keep out: the 3 mV sound value, the loom drive, background drive.

## Frozen comment to correct at the gen-6 freeze

`flycns/protocols.py` says loom responses "are larger when the fly walks", citing Turner et al. 2022 as
reproduced by `fit/extract_turner_loom.py`. Two problems:

1. The paper reports **no** significant modulation of loom responses by walking (Fig 5E-F, n = 8 flies),
   while small-object responses are suppressed.
2. The extractor normalises each state to its own maximum (LC12 = 1.0 in both), so "LC6 0.64 vs 0.40" is a
   change in the *shape* of the profile, not in absolute size. The walking and stationary series also come
   from different days and protocols (8 vs 13 series).

Corrected text should say: the stationary profile is used; the per-state profiles differ in shape after
normalisation; the paper finds loom gain unaffected by walking; absolute state effects are not claimed.

## Predictions (logged before the run)

| | Prediction | Confidence |
|---|---|---|
| P1 | `ML_wscale04_silent` PASSES on the male data | high |
| P2 | v-only reset alone (ML1) drives MN9 far above M1 (runaway, > 100 Hz) | high |
| P3 | MS1 and MS2: M1 exceeds both nulls | moderate |
| P4 | Outcome B: FUNCTION passes at 0.6-0.8, STABILITY fails there, with the tail activity concentrated in the VNC | low |
