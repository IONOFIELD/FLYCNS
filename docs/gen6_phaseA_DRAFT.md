# Generation 6, phase A: plan (final for registration; not yet registered)

Status: final for registration, 18 October 2026. The code is `fit/gen6_phaseA.py` and `fit/gen6_phaseA_score.py`
(both hashed into the registration), with `data/gen6_phaseA_celltypes.json` (sha256 pinned in the code). Nothing
is registered yet. The file name keeps "DRAFT" because the registration's criteria cite this path.
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
  - **Several cells of the same type on the opposite side:** equal split (B3, decided by the audit).
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
  - "Stops the instability" is defined by M1 (W*), below. (The earlier "at that w" wording is struck.)
- **Interpretation, registered before launch:**

  | LH-only cut | LH + MB cut | reading |
  |---|---|---|
  | stops it | (any) | the AL-LH loop sustains the tail |
  | does not | stops it | the MB route matters |
  | does not | does not | the loop runs inside the AL itself (see A4-AL) |

- **A4-AL, direct test of the in-AL loop** (so the third reading is tested, not inferred by elimination). Drive
  (a), single cuts inside the AL:
  - (i) outputs of cholinergic AL local neurons removed;
  - (ii) PN -> PN and PN -> LN edges of every cholinergic ALPN type removed (PN -> LH kept).
  These come from the signing audit, which found that the only excitatory recurrence left in AL and LH runs
  through cholinergic cells.
- **Secondary:** under drive (c), whether antennal lobe plus lateral horn still hold at least twice their
  drive share of the tail.

**A5: FUNCTION without runaway (decided).** FUNCTION-q, scored per w under the sugar drive:
- **Self-sustained trial:** as as Phase 1b registers it (tail rate at least 10% of the drive rate
  and at least 0.01 Hz). This is the per-trial rule STABILITY (a) and (b) already count; no new threshold.
- **Response:** MN9 two-cell mean above 0.5 Hz over the drive window, in that trial (FUNCTION's bar).
- **Minimum:** at least 5 non-self-sustained trials. Fewer gives UNRESOLVED, not PASS or FAIL. (Phase 1b's ML0 split
  15/15 into quiet and active trials; at some w almost every trial may run away.)
- **PASS** iff at least half of the non-self-sustained trials respond. **FAIL** otherwise. Wilson 95% interval
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
| Q4 | H4 holds: the antennal-lobe tail persists after the projection cut, LH-only and LH + MB alike. Reason: the local audit puts the loop inside the AL; LH -> LH (0.34 excitatory) and LH -> AL (0.08) are net inhibitory. "Persists" = the cut does not stop it by the M1 rule (W*). Signed off by Jayson, 18 Oct. | high |
| Q6 | At least one in-AL cut ((i) or (ii)) stops it by the M1 rule (blind STABILITY (b) 0/10 and (c) PASS at some w in W*). Reason for moderate, not high: AL -> AL is 84% excitatory and the two cuts remove its two largest excitatory sources (ACh LNs 587,339; ACh PNs 495,371 synapses, final list), but (b) and (c) are whole-network tests. In Phase 1b's blind self-sustained trials, AL + LH carry 61% of the tail at w 0.5, 56% at 0.6, 43% at 0.8 and 34% at 1.0 (VNC 7-14%). Whether the rest is relayed from the AL or sustains itself is not known, so a cut can end the AL loop and still fail (b). Raised from low by Jayson, 18 Oct. | moderate |
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
    **Recomputed on the final class list (preflight on 64279cb, `al_to_al_by_sender`, 18 October):**
    cholinergic ALLNs 587,339; cholinergic ALPNs 495,371; ALLN GABA 337,755; ALLN glutamate 41,117; other
    (sensory and unclassed) cholinergic 1,200,153. (The intermediate 177/76/14 list gave 586,857 / 495,023 /
    337,550.) The audit's conclusions stand. The
    region-level flows in the table above do not depend on the class list.
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
- **Electrical synapses are missing from the connectome (sources checked by Grok, 18 October, full texts).**
  FlyWire: "Our connectome includes only chemical synapses; the identification of electrical synapses awaits a
  future electron microscopy dataset with higher resolution" (Dorkenwald et al. 2024). Hemibrain: gap junctions
  "could not be included", being "difficult to reliably detect by FIB-SEM" (Scheffer et al. 2020). MaleCNS
  (Berg et al. 2025) detects synapses as presynaptic T-bars and their postsynaptic partners and reports no
  electrical synapses (no statement either way; read as an absence). Shiu et al. (2024): "Gap junctions cannot
  be identified in the electron microscopy dataset, so we ignore their possibility." FLYCNS adds electrical
  coupling only where documented and named (the giant-fibre circuit, `flycns/graph.py`), none in the AL. This
  paragraph goes into RESULTS.md's limitations with the phase A result.
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
3. FUNCTION-q: half of the non-self-sustained trials; self-sustained = the Phase 1b rule; response = 0.5 Hz
   per trial; fewer than 5 non-self-sustained trials gives UNRESOLVED.

## Definitions fixed before registering (from Grok's blind referee review, 18 October 2026)

Each finding of `phaseA_review_full_2026-10-18` is adopted as proposed unless a different choice is stated.
Code citations were checked against `d0f65b4`. Where this section and the sections above differ, this section
wins.

**B1. Decision rule (replaces rules 1-4 of "Decision rule").** Adopted.
- Viable(c): there is a grid w at which FUNCTION (screen), FUNCTION-q, STABILITY (a), (b) and (c) all PASS.
  The cell's decision w is the smallest such w. (LATERALITY is not on this list; see M7 and the answers
  below: it decides H for an outcome that adopts the mirror.)
- Outcomes over V1-V4 (2b and 4b never enter):
  - V1: Phase 1b's outcome C is not replicated. Stop for review; no default changes.
  - not V1, V2, not V3: adopt the MN9_R mirror.
  - not V1, V3, not V2: adopt the v-and-g reset.
  - not V1, V2 and V3: adopt the mirror only (a data fix with its own justification); report V3.
  - not V1, V4 only: adopt both.
  - none: outcome stays C.
- If a component at a candidate w is UNRESOLVED and none FAILs, run one top-up of 10 trials for that arm (next
  seed block). After that, UNRESOLVED counts as not passing.
- **Answered while coding (Grok's checklist, AMB1, AMB8, AMB9, AMB10, AMB12):**
  - LATERALITY is not a viability component. An outcome that adopts the mirror (mirror, both) also needs
    LATERALITY PASS in its cell at its decision w; otherwise the outcome is H (M7, rule v2 section 2).
  - The adopted w is the decision w of the cell that is adopted: c2 for mirror, c3 for reset, c4 for both.
  - Top-up seed block 7000 + the pair index. The top-up's 10 trials are pooled with the arm's 10 for every
    component of that arm: STABILITY (a)/(b) then need 0 of 20, and FUNCTION-q counts over the 20.
    Top-ups are run only for deciding cells.
  - A3's bar is 95 valid draws, absolute. NaN draws are dropped and counted. With fewer than 95 valid draws
    it cannot pass (UNRESOLVED unless FAIL applies).
  - Every bar lives in the registered criteria (`thresholds`); the scorer reads them from there.
- An adopted w still goes through gen6_rule.md's refine and confirm steps in the generation-6 registration.

**B2. Edge sets for the cuts.** Adopted, with one change to cut (ii).
- `data/gen6_phaseA_celltypes.json` is committed before launch, its sha256 in the registration. It holds the
  Cell Type Explorer type lists for ALPN, ALLN and Kenyon_Cell, with the source URL, date and extraction rule.
  **Built (18 October)** by `scripts/make_gen6_celltypes.py` from the Explorer's own repository
  (reiserlab/celltype-explorer-drosophila-male-cns, commit 789cc6c, 10 September 2026; `types.html` sha256
  3213642...). **Corrected the same day after the preflight:** the first extractor read names from the card
  text, which truncates long names ("M_l2PN10t..."), and skipped cards whose link is quoted (472 of 11,751),
  which also hid the alpha'/beta' Kenyon cells. It now parses the page with html.parser and takes each name
  from the link target. Result: ALPN 177 types, ALLN 76, Kenyon_Cell 14 (KCa'b'-ap1, -ap2 and -m
  included), no truncated names, no overlap between the lists. Earlier class tables built with the same
  pattern (the AL/LH sign audit's class counts) carry the same error; its region-level numbers do not depend
  on it.
  `neurons.parquet` has no class column, and edges carry no synapse location, so cuts are defined by cell
  type and by the post cell's `dominant_roi`.
- AL PN = cells whose type is in ALPN, every transmitter.
- LH-only cut: remove signed edges with pre in AL PN and `dominant_roi(post)` in {LH(L), LH(R)}.
- LH + MB cut: also remove edges with pre in AL PN and (post type in Kenyon_Cell, or `dominant_roi(post)` in
  {CA(L), CA(R)}). Kenyon cells are mostly lobe-dominated, so a calyx-ROI rule alone would miss them.
- Logged: AL PN out-weight by post `dominant_roi`, so what the cuts keep (for example SLP) is visible.
- Cut (i): remove every out-edge of cells with type in ALLN and edge `nt` == "acetylcholine".
- Cut (ii), **changed twice (18 October):** remove edges with pre of any ALPN type (it was "uniglomerular", then
  "not starting M_, MZ_ or CB"; see the decisions above) **with
  `nt` == "acetylcholine"**, and post in ALPN or ALLN. Reason: the cut tests excitatory PN recurrence; without
  the transmitter condition it would also remove the GABAergic uniglomerular vPNs (for example DA1_vPN).

- **Cells a cut isolates (preflight, 18 October).** Every cut removes all the edges of a few cells (LH 4, LH + MB
  6, (i) 6, (ii) 1, on the first list). Such a cell had no input at or above the floor, so it never fires. To
  keep the simulated cell set equal to the uncut one (m5), it keeps a zero-weight self-edge. Its readouts and
  the network's dynamics are unchanged; only the cell counts in the denominators stay as in the uncut network.
  On the pinned data a cut that removes no edge refuses to run.
- **Corrected again after Grok's acceptance check (18 October):** 469 cards have no name link; they name the
  type in `<span class=neuron-name title="<name> has N cells...">`, and the extractor skipped them silently
  (the `names_from_link_text: 469` counter counted skipped cards). It now reads that span, and stops if any card
  yields no name. **Final list: ALPN 180, ALLN 79, Kenyon_Cell 15** (added: CB3383 and M_lvPNm27, both
  cholinergic, and M_vPNml78; CB3679, lLN14, OA-VUMa5; KCg). Grok's independent lxml extraction gives the same
  three lists. Names by source: 11,282 from the link, 469 from the span title.
- **Decided (Jayson, 18 October): the "+" PN types stay in cut (ii)** (16 counted at the time among the types
  then called uniglomerular; the corrected list has 18 "+" ALPN types, 15 cholinergic, 1 glutamatergic, 2
  GABAergic, by the Explorer's transmitter; only the cholinergic ones are cut). They have two glomeruli in their name
  (for example VP1m+VP5_ilPN, VP2+Z_lvPN); a cholinergic PN covering two glomeruli is still part of the
  excitatory recurrence the cut tests.
- **Decided (Jayson, 18 October, same logic): the cholinergic M_/MZ_/CB (multiglomerular mlACT) PN types go in
  too.** **Cut (ii) removes every cholinergic ALPN type's edges onto ALPN and ALLN cells** ("all cholinergic ALPN
  types"; the GABAergic M_vPN and other inhibitory PNs are not cut). The synapses removed from the "+" types and
  from the M_/MZ_/CB types are reported next to each other in every cut (ii) arm and in the preflight, as
  descriptions, not arms.

**B3. The mirror.** Adopted, with one change to the sign.
- A function on `load_graph`'s returned edges (signed, at or above the floor), applied before CNSModel, in
  cells 2 and 4 only. Not in A3, A4 or the cuts.
- Side: `flycns.graph.infer_side` without the soma-x fallback (somaSide, then instance `_[LR]$`). Anything else
  counts as midline. Confirmed by the audit: no disagreements on the pinned data.
- Mapping: (A) the weight is split equally across every same-type opposite-side cell. MaleCNS instances are
  type plus side, so instance matching (B) cannot pick one cell among several and falls back to (A).
  Confirmed by the audit: (A) and (B) differ on 36 synapses only.
- Split weights below 5 are kept, as floats. The model takes float weights (`model.py:227`).
- **Sign, changed:** a mirrored edge takes P''s own model sign, because the model signs every edge by its
  presynaptic cell. If P' has no signed output, P's sign is used. The weight with a sign mismatch is logged.
- Untyped, midline and no-match partners stay on P. MN9_R's outputs are unchanged. The MN9_R -> MN9_L edge
  becomes MN9_L -> MN9_R.
- **Added while writing the code (18 October):** a mirrored partner P' must be a simulated cell, that is, one with
  at least one edge at or above the floor. An opposite-side cell with no edge at all is not in the network;
  adding it would change the simulated cell set (m5). Such cells are skipped. If none is left, the weight stays
  on P. The count is logged (`opposite_not_in_network`). On the toy data this affected 5 cells; on the pinned
  data the preflight reports it.
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

## MN9 mirror audit on the pinned data (18 October 2026)

`mn9_mirror_audit.py` (Grok; read-only), run by Jayson on the MANIFEST-pinned data, `amines=dropped`. The
output is kept with the registration as context.

| | MN9_L (10331) | MN9_R (16949) |
|---|---|---|
| status | Traced | Traced |
| input synapses, all (neuPrint `post`) | 6,358 | 633 |
| signed input >= 5 (model) | 5,651 (exc 2,805, inh 2,846) | 364 (exc 161, inh 203) |
| signed partner cells | 93 | 25 |

- **Both MN9 cells are `Traced`.** The status column does not flag MN9_R as incomplete, so "incomplete
  reconstruction" stays an interpretation. Two observations favour a thin input arbor over different wiring
  (INFERRED): MN9_R's partners are mostly the same types as MN9_L's, each at about 5-10% of the weight
  (17 types in both, 2 types into MN9_R only, 54 into MN9_L only); and MN9_R's output is not short (244 vs 172
  presynapses). v2 section 2's condition (MN9_R below a third of MN9_L's input) is met on counts, 364/5,651 =
  0.064; the registration states that the status column does not confirm it.
- **Mapping (open item 1): (A) equal split, confirmed.** 98.1% of MN9_L's signed input weight comes from
  partners whose type has exactly one opposite-side cell. Only 5 partners (36 synapses, 0.6%) have more than
  one. (A) and (B) give the same totals; they differ only in which cell carries those 36 synapses. One partner
  (DNg90, 34 synapses) has an opposite cell with a non-standard instance and falls back to (A) under (B).
- **Side tiebreak (open item 2): moot, somaSide first as in B3.** No partner's instance side disagrees with
  its somaSide, and the two tiebreaks decide the same side for every partner. Five partners are midline or
  missing on one field (215 synapses): GNG654 (somaSide null; instance gives L and R, so it maps normally),
  GNG297_M (one cell, no opposite: kept, 21), GNG001_M (midline: kept, 6), one untyped cell (kept, 44).
- **Kept on the same partner:** 3 partners, 71 synapses. **Split edges below the floor:** 11 edges, 21
  synapses (kept as floats, B3). **Sign mismatch P vs P':** 0. **P' with no signed output:** 2.5 synapses.
- **Mirror total:** 5,651 (exc 2,805, inh 2,846) onto MN9_R, from 100 presynaptic cells. It drops two types that
  reach MN9_R only (GNG017, GNG140; 10 synapses).
- **Normalise factor (M8):** signed L/R = 15.525, so 5,651 in total, with MN9_R's own exc/inh mix (2,499 /
  3,152). The neuPrint-based factor (10.044) is reported only.
- **The `"unclear"` defect at MN9:** one partner is dropped, GNG002, with 92 synapses onto MN9_L. Its
  `predictedNt` is serotonin, so it would stay dropped under `amines=dropped` even after the fallback fix.
- Note: MN9_L's signed input is almost balanced, 49.6% excitatory.

## Open items before registering

1. ~~Mirror mapping~~: closed, (A) equal split (audit above).
2. ~~Side tiebreak~~: closed, somaSide first; no disagreements on the pinned data.
3. ~~MN9_R status~~: closed, `Traced` (both cells). Recorded as a caveat on the reconstruction reading.
4. ~~Q4 and Q6~~: signed off (Q4 high, Q6 moderate, reasons logged).
5. ~~Code~~: `data/gen6_phaseA_celltypes.json`, `fit/gen6_phaseA.py`, `fit/gen6_phaseA_score.py` written and
   smoke-tested on the toy data (B2, B4). Both scripts are hashed into the registration.
6. ~~Preflight on the pinned data~~: done on ddd9230 (`results/gen6_phaseA/preflight.json`, committed as
   registration context) on the 177/76/14 list. **Superseded: rerun on the 180/79/15 list before registering.**
   Every listed type was found in the data (ALPN 177 types / 679 cells, ALLN 76 / 394,
   Kenyon_Cell 14 / 4,063). MN9 10331 (L) and 16949 (R), both Traced. Mirror: 5,651 onto MN9_R from 100 cells,
   kept 3 / 71, 11 split edges below the floor (21 synapses), sign mismatch 0, no edgeless opposite cell.
   Normalise factor 15.525. Drive (b) zeroes 696 of 1,575 driven cells (603 ol_sensory, all non-cholinergic);
   drive (c) also 260 ORN/HRN cells, 619 kept. Cuts, synapses removed (placeholders): LH 413,772 (5); LH + MB
   801,428 (7); (i) 588,118 (6); (ii) 472,413 (2), of which the "+" types 36,687 (7.8%, 15 types) and the
   M_/MZ_/CB types 48,985 (10.4%, 47 types). Every cut keeps all 170,175 simulated cells.
7. ~~`rerun.yml` jobs~~: 23 unconditional parts, plus 8 top-up parts (deciding cells c1-c4 only; the c2b/c4b
   top-ups were dropped, since B1 never names them), run only if the scorer names them.
8. **Fixes from Grok's acceptance check of ddd9230 (18 October), all in one commit:**
   - BL1, the cell-type list (above).
   - MJ1, the laterality wording (above; the scorer's docstring is fixed too).
   - MJ2: the mirror removes every edge into MN9_R, so a cell whose only edge went there would leave the
     network and stop every c2/c4 arm at the m5 guard. Such a cell now keeps a zero-weight self-edge, as in the
     cuts. The mirror log reports cells before and after, and the placeholder count.
   - mi1: the swapped MN9_L -> MN9_R edge takes MN9_L's own sign (B3 read literally).
   - mi2: the mirror log adds the exc/inh split, in and out, and the count of P' cells with no signed output.
   - mi3: the bimodality rule is max > 2 x max(1, min), stated in the criteria.
   - mi4: the report carries the "A4 describes gen-5 dynamics" caveat when B1 adopts v-and-g.
   - mi7: the self-sustained rule, the A3 statistic and the pair-index formula are written into the criteria.
   - mi8: a missing arm refuses scoring (fails safe, never PASS); stated in the criteria.
9. ~~Rerun the preflight~~: done on 64279cb, final list 180/79/15 (`results/gen6_phaseA/preflight.json`,
   replaces the earlier run). Every type found (ALPN 180 / 682 cells, ALLN 79 / 399, Kenyon_Cell 15 / 4,064).
   Mirror: 5,651 (exc 2,805, inh 2,846) onto MN9_R, the same split as MN9_L's input; 0 placeholders; 1 P' cell
   with no signed output; 170,175 cells before and after. Cuts, synapses removed (placeholders): LH 413,873 (5);
   LH + MB 801,529 (7); (i) 588,606 (6); (ii) 473,474 (2), of which "+" types 36,687 (7.7%, 15 types) and
   M_/MZ_/CB types 49,606 (10.5%, **49 types**, as Grok predicted). Drives unchanged: (b) 879 kept, (c) 619.
