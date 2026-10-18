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
| Q4 | H4 holds: the antennal-lobe tail persists after the projection cut, LH-only and LH + MB alike (raised from low after the local audit: LH -> LH and LH -> AL are net inhibitory) | high |
| Q6 | At least one in-AL cut ((i) or (ii)) brings STABILITY (b) to 0 of 10 at some w where the uncut network fails it | low |
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
- **Local run on the pinned data (18 October 2026)**, `al_lh_sign_audit.py` and the follow-up
  `al_other_check.py` (both read-only; outputs kept with the registration as context). Signed synapses between
  dominant-ROI groups, both sides pooled:

  | path | excitatory | inhibitory | dropped (unsigned) | excitatory share |
  |---|---|---|---|---|
  | AL -> AL | 2,282,863 | 420,718 | 235,340 | 0.844 |
  | AL -> LH | 354,095 | 44,207 | 5,052 | 0.889 |
  | LH -> LH | 132,870 | 257,265 | 8,025 | 0.341 |
  | LH -> AL | 4,307 | 50,940 | 2,356 | 0.078 |

  - The LH is net inhibitory internally, and its feedback to the AL is inhibitory. An AL-LH excitatory loop
    is not supported by the wiring. The LH tail is most likely relayed feed-forward from the AL.
  - The in-AL recurrence is among central-brain intrinsic cells (PNs and LNs): 1,097,279 excitatory vs
    326,910 inhibitory. By sender: cholinergic ALLNs 586,857; cholinergic ALPNs 495,371; all ALLN GABA 337,755.
  - Sensory cells (2,730 AL-dominant, nearly all cholinergic) send 1,139,291 excitatory synapses, almost all
    feed-forward onto intrinsic cells (1,050,448). Sensory -> sensory is 81,456, and input onto sensory cells
    is about balanced (110,836 exc, 90,197 inh). **A sensory axo-axonic loop was hypothesised and is not
    supported**, so no sensory-input cut is added.
  - Right-left difference: AL(R) -> AL(R) 1,054,583 excitatory vs AL(L) -> AL(L) 770,803 (about 1.37x),
    consistent with AL(R) as the top tail group.
  - The `"unclear"` drop in the AL: 477 cells lose their outputs, 235,340 AL -> AL synapses (8%). The largest
    are GABA-predicted LNs (lLN2F_a, lLN2T_d). Restoring them would add inhibition but leave AL -> AL near
    80% excitatory: worth fixing at the freeze, not the explanation for the tail.
  - Biology (checked by Grok against the papers, 18 October): excitatory (cholinergic) LNs depolarise PNs
    largely, if not purely, through electrical coupling, which is shakB-dependent (Yaksi & Wilson 2010, Fig. 4;
    PN-PN sister coupling is also electrical, Fig. 6). Huang et al. (2010, abstract only read) also report a
    cholinergic dendrodendritic component. In Yaksi & Wilson, eLN output onto inhibitory LNs is mainly
    chemical and nicotinic, so eLNs inhibit PNs indirectly; Huang et al. found eLN-iLN connections rare. EM
    connectomes annotate chemical synapses only (to confirm against the dataset papers before citing). So this
    model has no eLN -> PN electrical path, and every ACh-LN output it carries is chemical. Cut (i) removes
    that chemical output, most of which, in the fly, is not how eLNs excite PNs.
- **Not adopted for phase A:** a slow GABA_B-like inhibition and PN adaptation (Grok's (iv), (v)). Both are
  model changes. They belong in the synapse-model plan that outcome C points to, not in a phase that changes
  only the reset and MN9_R's input.

## Size

- 4 deciding cells x 5 w x 2 drives = 40 sweep arms, plus cells 2b and 4b = 20: 60 in all.
- 1 fresh 30-trial M1 arm and 100 null draws (A3).
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

## Definitions fixed before registering (from Grok's blind referee review, 18 October 2026)

Each finding of `phaseA_review_full_2026-10-18` is adopted as proposed unless a different choice is stated.
Code citations were checked against `d0f65b4`. Where this section and the sections above differ, this section
wins.

**B1. Decision rule (replaces rules 1-4 of "Decision rule").** Adopted.
- Viable(c): there is a grid w at which FUNCTION (screen), FUNCTION-q, STABILITY (a), (b) and (c) all PASS.
  The cell's decision w is the smallest such w. LATERALITY joins this list for cells 2 and 4 (M7).
- Outcomes over V1-V4 (2b and 4b never enter):
  - V1: Phase 1b's outcome C is not replicated. Stop for review; no default changes.
  - not V1, V2, not V3: adopt the MN9_R mirror.
  - not V1, V3, not V2: adopt the v-and-g reset.
  - not V1, V2 and V3: adopt the mirror only (a data fix with its own justification); report V3.
  - not V1, V4 only: adopt both.
  - none: outcome stays C.
- If a component at a candidate w is UNRESOLVED and none FAILs, run one top-up of 10 trials for that arm (next
  seed block). After that, UNRESOLVED counts as not passing.
- An adopted w still goes through gen6_rule.md's refine and confirm steps in the generation-6 registration.

**B2. Edge sets for the cuts.** Adopted, with one change to cut (ii).
- `data/gen6_phaseA_celltypes.json` is committed before launch, its sha256 in the registration. It holds the
  Cell Type Explorer type lists for ALPN, ALLN and Kenyon_Cell, with the source URL, date and extraction rule.
  `neurons.parquet` has no class column, and edges carry no synapse location, so cuts are defined by cell
  type and by the post cell's `dominant_roi`.
- AL PN = cells whose type is in ALPN, every transmitter.
- LH-only cut: remove signed edges with pre in AL PN and `dominant_roi(post)` in {LH(L), LH(R)}.
- LH + MB cut: also remove edges with pre in AL PN and (post type in Kenyon_Cell, or `dominant_roi(post)` in
  {CA(L), CA(R)}). Kenyon cells are mostly lobe-dominated, so a calyx-ROI rule alone would miss them.
- Logged: AL PN out-weight by post `dominant_roi`, so what the cuts keep (for example SLP) is visible.
- Cut (i): remove every out-edge of cells with type in ALLN and edge `nt` == "acetylcholine".
- Cut (ii), **changed:** remove edges with pre a uniglomerular ALPN (type not starting M_, MZ_ or CB) **with
  `nt` == "acetylcholine"**, and post in ALPN or ALLN. Reason: the cut tests excitatory PN recurrence; without
  the transmitter condition it would also remove the GABAergic uniglomerular vPNs (for example DA1_vPN).

**B3. The mirror.** Adopted, with one change to the sign.
- A function on `load_graph`'s returned edges (signed, at or above the floor), applied before CNSModel, in
  cells 2 and 4 only. Not in A3, A4 or the cuts.
- Side: `flycns.graph.infer_side` without the soma-x fallback (somaSide, then instance `_[LR]$`). Anything else
  counts as midline. This settles open item 2, provisionally, until the audit output is read.
- Mapping: (A) the weight is split equally across every same-type opposite-side cell. MaleCNS instances are
  type plus side, so instance matching (B) cannot pick one cell among several and falls back to (A). This
  settles open item 1, provisionally, until the audit confirms the fallback on the pinned data.
- Split weights below 5 are kept, as floats. The model takes float weights (`model.py:227`).
- **Sign, changed:** a mirrored edge takes P''s own model sign, because the model signs every edge by its
  presynaptic cell. If P' has no signed output, P's sign is used. The weight with a sign mismatch is logged.
- Untyped, midline and no-match partners stay on P. MN9_R's outputs are unchanged. The MN9_R -> MN9_L edge
  becomes MN9_L -> MN9_R.
- bodyIds fixed: 10331 (L), 16949 (R), asserted against `type == "MN9"` and the sides.
- Recorded in the registration from `mn9_mirror_audit.py`: kept count and weight, below-floor count,
  sign-mismatch weight, and how many partners are unclear-silent.

**B4. Code before launch.** Adopted. `fit/gen6_phaseA.py` (registration and arms) and
`fit/gen6_phaseA_score.py` hold the mirror and normalise transforms, the cuts, the drive pools, FUNCTION-q,
the 95-of-100 null score and the B1 table. Both are committed with smoke runs on `scripts/make_testdata.py`
data before any cloud job. `stats.null_percentile` stays unchanged; the new score is a separate function.

**M1. What "stops it" means.** Adopted.
- Baseline: cell 1 (v-only reset, MN9_R as in the data), blind drive, seeds paired with the cut arms.
- W* = the grid w at which baseline cell 1 has at least 5/10 self-sustained blind trials. (In Phase 1b's
  `male_flycns` blind arms that was w 0.5 to 1.0; at w 0.4 only 1/10.)
- A cut stops it if, at some w in W*, the cut arm has STABILITY (b) 0/10 and (c) PASS. Q6 uses the same W*.

**M2. Readings for the in-AL cuts.** Adopted, with the biology caveat attached.
- (i) stops it: in the model, ACh-LN chemical output sustains the AL loop. Because the fly's eLN -> PN path is
  electrical, this is read as a model-structure finding, not as fly biology.
- (ii) stops it: excitatory PN recurrence sustains it.
- Both: either is enough. Neither: no single cut removes it; mechanism UNRESOLVED.
- Reported only. These readings never feed B1.

**M3. Drive arms (b) and (c).** Adopted. stim_types and the driven set of arm (a) are kept, so the network
is the same. The rate is set to 0 for (b) driven cells with superclass `ol_sensory` or edge `nt` not
acetylcholine; (c) those, plus types starting `ORN_` or `HRN_`. Driven count and total input rate are reported
per arm.

**M4. A3 null.** Adopted.
- Real value: a fresh 30-trial M1 arm (phase A seed block), MN9_R as in the data.
- 100 draws, one trial each, seeds 30000 + k (Phase 1b used 20000 + k).
- PASS iff #(real > draw), strict, is at least 95. FAIL iff real is at or below the null median. Otherwise
  UNRESOLVED. The alive rule is Phase 1b's (`fit/shiu2024_phase1b.py:735`, ALIVE_FRACTION of the real arm's
  median whole-CNS rate).
- **Deviation, stated plainly:** the bar moved from "exceeds every draw" (MS2, 20 draws) to "exceeds at least
  95 of 100". It was proposed after MS2 came out at 19 of 20. The reason is power: 20 draws give a smallest
  attainable p of 1/21 only if the real value beats all of them, so one tie or near-miss decides the
  verdict. MS2 is not re-scored.

**M5. Seeds and trials.** Adopted. 10 trials per sweep, cut and drive arm. Seed = 6000 + index of (drive, w),
shared by cells 1-4b and the cut and drive arms at the same (drive, w), so comparisons are paired. A3 real arm
seed 6100; null draws 30000 + k. All are disjoint from Phase 1b (201+, 20000+k) and the gen6_rule refine block
(5000).

**M6. Multiple comparisons.** Adopted. No correction. Declared as an uncorrected screen; B1's same-w and
smallest-w rule limits the search, and adoption still needs gen6_rule's confirm step (both nulls).

**M7. Laterality.** Adopted. Adopting the mirror under B1 also needs a median sugar LI below 0.8 in cell 2 (or
4) at its decision w; otherwise outcome H as amended in v2 section 2. "Below 0.8 under mirroring only" means
cell 2 median LI < 0.8 and cell 1 median LI >= 0.8 at the same w.

**M8. Normalise factor.** Adopted. From the signed `load_graph` totals (MN9_L / MN9_R), as the audit script's
variant (ii).

**M9. A4 secondary.** Adopted. Per w under drive (c), pool `tail_by_neuropil` spikes over the self-sustained
blind trials. Tail share = (AL(L) + AL(R) + LH(L) + LH(R)) / all; drive share from `drive_by_neuropil` over the
same trials. Test: tail share >= 2 x drive share. With no self-sustained trial: not scorable.

**Minor, all adopted:**
- m1: the response bar (two-cell mean > 0.5 Hz over 1 s) means at least 2 MN9 spikes, both possibly from
  MN9_L. Stated, not changed. A 3/6 pass has a Wilson interval of about 0.19-0.81.
- m2: the per-trial rule is called "self-sustained (`fit/shiu2024_phase1b.py:474`)" everywhere; "runaway" is
  kept only for Phase 1b's `smallest_runaway` (more than half the trials self-sustained).
- m3: bimodal iff max n_active > 2 x min n_active; split at the largest gap in n_active.
- m4: the size arithmetic is corrected above.
- m5: every cut arm asserts that `len(m.lif_ids)` equals the uncut value (`model.py:146` builds it from
  the edges present).
- m6: the `"unclear"` defect also touches MN9. Grok inferred that GNG002 (92 synapses to MN9_L) is dropped. The
  audit's figures are recorded in the registration.
- m7: the soma-x fallback of `infer_side` is not used (B3).
- m8: A4 runs under the v-only reset only. If B1 adopts v-and-g, the A4 readings describe the gen-5 dynamics.
- m9: verdicts use the point fraction; the Wilson interval is reported only.

## Open items before registering

1. Mirror mapping: (A) equal split, provisionally (B3). **OPEN** until `mn9_mirror_audit.py` output confirms
   that instance matching falls back to (A) on the pinned data.
2. Side tiebreak: somaSide first, provisionally (B3). **OPEN** until the audit's disagreement list (section d)
   is read; GNG654 is the case to check.
3. MN9_R's `status` from `data/neurons.parquet`. **OPEN** (audit section a).
4. Q4 and Q6: Jayson's sign-off.
5. `data/gen6_phaseA_celltypes.json`, `fit/gen6_phaseA.py`, `fit/gen6_phaseA_score.py`: to be written and
   smoke-tested (B2, B4).
