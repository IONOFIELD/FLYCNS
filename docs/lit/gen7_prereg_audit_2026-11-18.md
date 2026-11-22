<!-- Pre-registration audit by Grok (read-only), 18 November 2026, of the plan at 728ac03, committed as received. Each finding's resolution is in docs/gen7_synapse_model_DRAFT.md, "Definitions fixed before registering". -->

# FLYCNS gen 7: adversarial pre-registration audit (2026-11-18, PST)

Read-only. Nothing was committed, pushed, branched, commented or edited in any repo. No messages were sent. No personal identifiers went into any request. Findings only: no parameter values are proposed. Where a finding says "the plan must state X", it names a gap, not a value.

**Tags.** Severity: **BLOCKER** (a scorer or implementer cannot proceed without choosing, or a verdict could flip), **SHOULD-FIX**, **NOTE**. Evidence: **VERIFIED** (read in the file or code at the sha given), **INFERRED** (my reasoning or arithmetic), **CAN'T VERIFY**.

## 0. What was read

| Item | Ref | Tag |
|---|---|---|
| Plan `docs/gen7_synapse_model_DRAFT.md` (189 lines) | `gen7/synapse-model-draft` @ **728ac03a4a34** (branch tip at fetch time; the commit message reads "gen7 draft: drop the unsupported Windows-reproduction claim", 2026-10-18 22:31 PDT) | VERIFIED |
| `docs/lit/synapse_model_lit_2026-10-18.md` (222 lines), `docs/lit/gen7_lit_std_validation_2026-10-18.md` (146), `docs/lit/v7a_nagel_check_2026-10-18.md` (129) | same sha | VERIFIED |
| Phase A plan `docs/gen6_phaseA_DRAFT.md` (455 lines) | `gen6/phaseA-decisions` @ **c1e6e6244570** | VERIFIED |
| Phase A registered criteria `results/gen6_phaseA/registration_v5.json` | @ c1e6e62 (`git_commit` ff816c1; model hash dcb44bf09a88) | VERIFIED |
| `data/gen6_phaseA_celltypes.json` | @ c1e6e62, sha256 `ea8bad7d…5585504` (matches the registration) | VERIFIED |
| `flycns/model.py`, `flycns/registry.py`, `docs/CALIBRATION.md` | @ 728ac03 | VERIFIED |
| My own context: `phaseA_scorer/choices.md` (28 choices), `phaseA_scorer/diff_vs_registered_scorer.md`, `v7a_mn9r_check_2026-11-13.md`, `v7a_mn9r_check_2026-10-18.md` | /workspace/flycns | read |

Line numbers below are for the plan at 728ac03 unless another file is named. "lit-STD" = `gen7_lit_std_validation_2026-10-18.md`, "lit-SYN" = `synapse_model_lit_2026-10-18.md`, "lit-V7A" = `v7a_nagel_check_2026-10-18.md`, all at 728ac03.

## Summary

| Section | BLOCKER | SHOULD-FIX | NOTE | Total |
|---|---|---|---|---|
| 1. Ambiguities | 10 | 13 | 5 | 28 |
| 2. Source mismatches | 0 | 6 | 10 | 16 |
| 3. Confounds | 1 | 6 | 2 | 9 |
| 4. Predictions | 1 | 4 | 1 | 6 |
| 5. Missing controls / stop rules | 1 | 6 | 2 | 9 |
| 6. VM7 split and other V7a flags | 1 | 3 | 2 | 6 |
| **Total** | **14** | **38** | **22** | **74** |

**Top blockers, one line each:**
1. **F1.** "Viable" and adoption are inherited from phase A's B1, but B1 is written for cells c1–c4 and the mirror/reset. Gen 7 has no list of deciding arms and no outcome table.
2. **F2.** "LATERALITY -> H" (104) is undefined for gen 7, where MN9_R stays as in the data. Read literally, it could turn every adoption into H.
3. **F3.** The tie and preference rule (104–106) does not rank stage-2 arms or the fix. It does not say whether arm choice comes before or after the smallest-w rule, or what "mechanism" counts.
4. **F4.** The E_i sweep runs only if stage 1 fails (103), yet H7a's falsifier needs "any E_i in the sweep" (55). Nothing says how a stage-2 arm, or its E_i, is adopted.
5. **F5.** V7a has no metric, window, cells, aggregation, tolerance or pass rule. The plan itself lists them as "Still open (fix before registering)" (179–184).
6. **F6.** V7b has no operational readout. The model has no water, caffeine, denatonium or concentration stimulus, and its scored or report-only status is not decided (135, 153–156).
7. **F7.** Which phase A text is "reused unchanged" (82–83) is not pinned. The phase A DRAFT on the gen 7 branch is the 112-line pre-"Definitions" version, and the cell-type JSON that H7c-in needs (69) is not on the branch.
8. **F8.** The positive control "replicates phase A's cell 1" (94) has no replication criterion and no stop rule if it fails or turns viable.
9. **F9.** STD placement is not specified. Under the blind drive, ORNs are Poisson sources whose outputs run through a separate `S_stim` synapse group (model.py:236), so STD-in could act on nothing unless `S_stim` is named. Nothing states whether A is per edge or per sender, or whether "restore" resets A.
10. **F10.** The refit of every calibration "chosen under the current synapse model" (19–21) has no order or scope. If it runs per arm, every arm comparison mixes synapse change and refit, and the positive control stops being a replication.
11. **F54.** H7a's falsifier counts only STABILITY ("no w passes STABILITY", 54–55), while the hypothesis claims "functional and stable". H7b–H7d have no criterion beyond "viable".
12. **F69.** VM7 is split in MaleCNS into VM7d and VM7v, while Olsen 2010 fits one "VM7". The plan's mapping rule (182–184) cannot be applied to VM7 as written.
13. **F45.** The confound side of F10: if calibrations are refit per arm, no stage-1 comparison isolates "the synapse change alone" (95).
14. **F60.** The stop-rule side of F8: there is no V1-style stop if the positive control does not replicate or turns viable.

Section 6 covers VM7 and the other V7a flags. Section 7 compares gen 7 with phase A.

---

## 1. Ambiguities

**F1. BLOCKER: "viable" and the decision table for gen 7.**
- Lines 82–83: "\"Viable\", FUNCTION, FUNCTION-q, STABILITY (a), (b), (c), LATERALITY … are **reused unchanged** from phase A's registered criteria."
- Line 104: "Adoption follows phase A's B1 logic (smallest viable w, top-up rule, LATERALITY -> H)".
- Phase A's registered `decision.viable` reads "a grid w at which FUNCTION (screen), FUNCTION-q and STABILITY (a), (b), (c) all PASS". Its `decision.table` is specific to c1–c4 ("c1 viable: stop for review … Else c2 viable: mirror … c3 only: v-and-g reset … c4 only: both … None: C"), and `settings.deciding` is ["c1","c2","c3","c4"] (registration_v5.json @ c1e6e62). VERIFIED.
- Gen 7 states neither a deciding-arm list nor an outcome table. Line 103 uses "no viable deciding arm" without defining "deciding". Open questions:
  - Is H7c-all ("secondary, explicitly extrapolating", 74) deciding?
  - Is the no-fix baseline deciding?
  - Are stage-2 arms deciding?
- For an STD arm, "viable" inherits STABILITY (a)/(b)'s "0 self-sustained trials", defined on the tail: "whole-CNS rate in the last half of the tail >= 0.1 x the rate during the drive" over a 500 ms tail (registration `definitions.self_sustained`, `protocol.sweep`). Recovery τ is 893 ms primary and 2.4 s sensitivity (123), so A is still depressed through the whole tail. The plan must state that this is intended, or say how the tail is read for STD arms. INFERRED (arithmetic: 500 ms < 893 ms).

**F2. BLOCKER: what "LATERALITY -> H" means in gen 7.**
- Line 104: "LATERALITY -> H".
- In phase A, LATERALITY gated only outcomes that adopt the MN9_R mirror: "an outcome that adopts the mirror (mirror, both) also needs LATERALITY PASS … otherwise the outcome is H" (registration `decision.laterality`). VERIFIED.
- Gen 7 runs "MN9_R as in the data" (8, 89). MN9_R has 633 inputs against MN9_L's 6,358 (phase A DRAFT @ c1e6e62:391), and its v1.0 statusLabel is "RT Hard to trace" (v7a_mn9r_check_2026-11-13.md, row "statusLabel (v1.0)"). VERIFIED.
- If LATERALITY now gates every adoption, every arm may end in H for a reason unrelated to the synapse model. INFERRED. The plan must state whether LATERALITY gates any gen 7 adoption, which cell and w it is read at, and what H means when no data fix is being adopted.

**F3. BLOCKER: the tie and preference rule.**
- Lines 104–106: "the simplest viable arm wins (fewest added mechanisms; ties: current-based before conductance-based, STD-in before STD-all, because STD-in uses measured synapses only)."
- Unstated:
  - (a) What counts as a "mechanism". Does the "unclear" fix count? Is tau_i 10 ms one (H7b's "slow inhibition", 56)? Is an E_i other than −70 one?
  - (b) How stage-2 arms rank against each other: six (E_i, tau_i) combinations per conductance arm.
  - (c) Whether "smallest viable w" is applied within the chosen arm only, or across arms. For example, if a simpler arm is viable only at w 1.0 and a more complex arm at w 0.4.
  - (d) The order of the two tie-breaks when both apply.
  - (e) What happens when only the no-fix baseline is viable, or only the with-fix baseline is.
  - (f) Whether the "adopted" setting includes the STD scope and the E_i value.
- Phase A had an explicit ordered table (CHOICE-25 in my phase A scorer resolved its reading order).

**F4. BLOCKER: how the E_i sweep enters adoption.**
- Line 97: "Stage 2 … E_i sweep {-55, -70, -80} mV x tau_i {5, 10} ms."
- Line 98: "Run only the conductance-based arms of stage 1 that are not already viable."
- Line 103: "stage 2 runs only if stage 1 leaves no viable deciding arm."
- Lines 54–55, H7a: "Falsified if no w passes STABILITY at any E_i in the sweep."
- Gaps:
  - (a) If stage 1 has any viable arm, stage 2 never runs, so H7a cannot be scored "at any E_i". The plan must state H7a's verdict in that case.
  - (b) Line 98's "not already viable" clause cannot bind under line 103's trigger: if any arm were viable, stage 2 would not run. The two lines need reconciling. INFERRED.
  - (c) The cell (−70, 5) duplicates the stage-1 conductance arm. Rerun, or reuse?
  - (d) Stage 2 covers 3 conductance arms × 6 cells = 18 arms (15 if the duplicates are reused). The plan gives no count. INFERRED arithmetic.
  - (e) Is a viable stage-2 arm adopted with its E_i and tau_i? Is the "primary" E_i (−70, 120) then replaced?
  - (f) Is stage 2 inside the same registration as stage 1? Lines 88 and 167 say one registration for "the 2x3 core" only.

**F5. BLOCKER: what is scored for V7a.**
- Line 180: "Still open (fix before registering): V7a: the ORN rates to drive, the tolerance, and how a glomerulus's ORNs are driven in the model."
- Lines 182–184: "drive every `ORN_<glomerulus>` cell … at the target rate … and read the uniglomerular PNs of that glomerulus".
- Nothing below is stated. Each needs a registered choice:
  - **Metric:** PN rate per cell, the mean over cells, or a fitted R_max/σ compared with Olsen's.
  - **Window:** Olsen used a 500 ms odor period, with ORN rates baseline-subtracted (lit-V7A A2c). The phase A sweep drives for 1,000 ms (registration `protocol.sweep`).
  - **Baseline subtraction:** the model's basal rate is 0 Hz (157–158).
  - **ORN rate set:** which points; Olsen's ORN axis is about 0–125 Hz (143).
  - **Cells:** see F69–F74.
  - **Sides:** both antennae's ORNs, or one side, and which PN side.
  - **Aggregation:** over PN cells, trials and seeds.
  - **Tolerance and pass rule:** absolute or relative, per point or per curve, how many points must pass.
  - **Arm and w:** which arm(s) and which w (adopted only, every viable arm, or every arm at its decision w), and what happens when no arm is viable.
  - **Drive mode:** "source" (Poisson replacement, model.py:236) or "kick".
- It is report-only (177), but line 133 says "criterion fixed in the registration, before any run".

**F6. BLOCKER: what is scored for V7b.**
- Lines 153–156: "only orderings are testable: sucrose > water (about 48% vs 2% dF/F); sucrose plus caffeine or denatonium is not different from water; 1 M sucrose gives about twice the 100 mM response; both MN9 somata respond (bilateral)."
- The model's sugar drive is "every LB3b and LB3c cell at 100 Hz" (registration `protocol.drives.sugar`). VERIFIED. The plan defines none of the following:
  - a "water" condition;
  - a caffeine or denatonium (bitter) drive;
  - a mapping from 100 mM and 1 M to GRN rates;
  - an MN9 readout (rate, window, the two-cell mean or per cell);
  - what "about twice" and "not different" mean (tolerance or test);
  - trials and seeds;
  - a pass rule.
- Line 135 says the validation is "scored but not part of viability (open choice 6 decides whether it should be)". Line 177 decides V7a only ("V7a report-only"). V7b's status is undecided.

**F7. BLOCKER: which phase A text and which scorer resolutions are inherited.**
- Lines 6–7 and 82–83 cite `docs/gen6_phaseA_DRAFT.md` and "phase A's registered criteria".
- At 728ac03, `docs/gen6_phaseA_DRAFT.md` is the 112-line pre-registration draft. It has no "Definitions fixed before registering" section, and its status line reads "DRAFT for review … no code exists for it yet". It differs from c1e6e62's 455-line version (29 insertions, 372 deletions). VERIFIED (git diff).
- `data/gen6_phaseA_celltypes.json`, `fit/gen6_phaseA_score.py` and `results/gen6_phaseA/registration_v5.json` do not exist at 728ac03. The gen 7 branch's merge base with c1e6e62 is 7defd8a. VERIFIED.
- The plan must pin the criteria (registration_v5.json at ff816c1 / c1e6e62), the cell-type JSON's sha256, and the scorer whose readings apply.
- Of my 28 phase A choices, the registered scorer and mine disagreed on a partial top-up (CHOICE-10) and on B1 while top-ups are pending (CHOICE-12, `diff_vs_registered_scorer.md` "B1 outcome: agree, except while top-ups are pending (s08, s15)"). Both carry into gen 7 by reference unless resolved. VERIFIED (my files); carry-over INFERRED.

**F8. BLOCKER: the positive control's replication criterion.**
- Lines 93–94: "cell (current, no STD) runs twice, without the fix (replicates phase A's cell 1; positive control)".
- Not stated:
  - (a) what "replicates" means: bit-identical spikes, the same per-w verdicts, or the same outcome;
  - (b) the seeds; phase A used "6000 + index of (drive, w)" (registration `protocol.seeds`);
  - (c) what happens if it does not replicate, or if it is viable. Phase A had V1: "c1 viable: stop for review".
- The gen 7 code changes the model hash (17–19), so replication is not automatic. INFERRED.

**F9. BLOCKER: where STD lives in the code.**
- Line 123: "the synaptic weight is scaled by A (w_eff = w x A, A = 1 at rest) … A -> f*A per spike, tau_D dA/dt = 1 - A".
- In model.py @ 728ac03, recurrent synapses are `S_rec = Synapses(G, G, …)` (l. 224). Under `stimulation "source"`, stimulated cells "are replaced by Poisson spike sources" whose output is `S_stim = Synapses(P, G, …)` (l. 230–236). VERIFIED.
- Under the blind drive, driven ORNs are sources. If STD sits only on `S_rec`, H7c-in has no effect on driven ORNs. INFERRED.
- The plan must also state:
  - (a) whether A is per edge (per pre→post pair) or per presynaptic cell; for H7c-in only some of an ORN's targets are depressed;
  - (b) whether the PSP uses A before or after the decrement (line 123's "the first PSP after rest equals the current model's" implies before; it is not said);
  - (c) whether the per-trial "restore" (registration `protocol.sweep`) resets A to 1.

**F10. BLOCKER: the calibration refit's order and scope.**
- Lines 19–21: "a refit of every calibration chosen under the current synapse model (`docs/CALIBRATION.md`; the list is fixed in the gen-7 registration before any refit)."
- CALIBRATION.md @ 728ac03 lists w_scale 0.4 (chosen by `fit/select_wscale.py`), PEAK_HZ, GF b_adapt and others. VERIFIED.
- Not stated:
  - whether the refit runs before stage 1 or after adoption;
  - whether it runs once (on which arm) or per arm;
  - whether the w grid {0.4, 0.5, 0.6, 0.8, 1.0} (registration `settings.grid`) stays in the same units after a refit.
- If the refit runs per arm, every arm comparison mixes two changes (see F33), and the positive control (F8) no longer runs phase A's settings. INFERRED.

**F11. SHOULD-FIX: which H7c the verdict scores.**
- Line 57: "**H7c (short-term depression):** STD on every chemical synapse".
- Line 64: "**H7c-in**, STD on sensory-afferent synapses only".
- Lines 67–68: "H7c-in is primary and means the measured synapses only … presynaptic type starting `ORN_` (not `HRN_`) onto a postsynaptic type in the ALPN or ALLN list".
- Three different scopes appear under one label. Gustatory and HRN afferents are sensory but excluded by 67–73. The plan must state which text defines H7c, H7c-in and H7c-all for scoring, and whether "H7c" has its own verdict.

**F12. SHOULD-FIX: seeds, n and top-up seeds.**
- No seed block is given for stage 1, stage 2, the second baseline or top-ups. "The sweep protocol" is reused (83), which fixes 10 trials, but phase A's seeds were a phase-specific M5 rule.
- The plan must state the seed formula, whether arms are paired on seeds (phase A M5: "shared by cells … so comparisons are paired"), and whether seeds are disjoint from phase A's (6000+, 7000+, 6100, 30000+k).

**F13. SHOULD-FIX: bootstrap specification.** Not mentioned. Phase A's intervals come from gen6_rule.md ("percentile bootstrap over trials, 2,000 resamples, seed 0", quoted in my `choices.md` CHOICE-01). The plan must state whether this applies unchanged, including to pooled top-ups.

**F14. SHOULD-FIX: the w grid's meaning under conductance and STD.**
- "The grid" is reused (83). Phase A's grid is [0.4, 0.5, 0.6, 0.8, 1.0] (registration). VERIFIED.
- Line 109 converts "w_syn_mV". The plan must define w_syn_mV in terms of the grid w and the per-synapse 0.275 mV (CALIBRATION.md: "0.275 mV × 0.4 = 0.11 mV per synapse").
- It must also state the sign convention. As written, g_syn = w_syn_mV / (V_cal − E_e) with V_cal −52 and E_e 0 gives a negative denominator (−52 mV). Line 111's "52 / 18" uses magnitudes. INFERRED arithmetic.

**F15. SHOULD-FIX: listed sensitivities that no stage runs.**
- Line 119: "E_e … 0 mV (sensitivity -10, +10)".
- Line 121: "tau_e | 5 ms (sweep 2-5)".
- Line 123: "sensitivity U 0.28, tau_D 2.4 s".
- None of these appears in stage 1 or stage 2 (88–98). The plan must state whether, when and on which arms they run, whether they are scored, and whether they can affect adoption.

**F16. SHOULD-FIX: how the "unclear" fix enters the run order.** Line 22 places it in "`scripts/fetch_malecns.py` / `load_graph`". Line 170 gives sizes "on the pinned data, floor 5". The plan must state:
- whether the fix runs before the floor is applied;
- which data pin is used (MANIFEST hash; `data/MANIFEST.json` is in MODEL_FILES);
- whether "with fix" changes the simulated cell set (see F51).

**F17. SHOULD-FIX: NaN, a failed arm, or a numerics-assertion failure.**
- Lines 128–131: "checked by asserting v >= E_i - 1 mV in a smoke run" and "the existing dt 0.05 ms numerics check."
- Not stated:
  - what happens if the assertion fails in a registered (non-smoke) run;
  - which arms get the dt 0.05 check, and what happens if verdicts differ between dt values;
  - whether a missing or crashed arm refuses scoring, as phase A's `definitions.missing_arm` did ("fails safe, never PASS").

**F18. SHOULD-FIX: multiple comparisons.** Stage 1 has 7 arms × 5 w × 2 drives. Stage 2 adds up to 18 arms. Several hypotheses are scored. Phase A declared "M6. Multiple comparisons. Adopted. No correction. Declared as an uncorrected screen" (phase A DRAFT @ c1e6e62:354). Gen 7 is silent.

**F19. SHOULD-FIX: "the first viable one".** Lines 91–92: "an STD arm is the first viable one, if any is." "First" is undefined: by stage, by smallest w, or by preference order. A scorer must choose.

**F20. SHOULD-FIX: STD in the sugar drive.**
- Lines 71–73: "the number of ORN spikes per sugar trial is reported. Otherwise H7c-in's sugar arms equal the no-STD arms'".
- The plan must state whether H7c-in's sugar arms are run or copied from the with-fix baseline. It must also say whether "equal" is asserted (and what happens if ORNs fire and the arms differ).

**F21. SHOULD-FIX: the reported ORN-spike count has no use.** Line 72 asks for "the number of ORN spikes per sugar trial is reported" but gives no statistic (mean over trials? per w?) and no reading.

**F22. SHOULD-FIX: what a refit means for "smallest viable w".** If w_scale is refit (F10), the plan must state whether the adopted value is the grid w or the refit w_scale. CALIBRATION.md's w_scale rule picks "the largest grid value with whole-CNS rate < 1 Hz and < 10% of neurons active". VERIFIED (CALIBRATION.md @ 728ac03).

**F23. SHOULD-FIX: the gen 8 trigger.** Line 101: "They move to generation 8, on gen 7's outcome." The plan does not say which gen 7 outcome triggers which gen 8 content. H7e's "on top of the best of H7a-H7d" (78) leaves "best" undefined.

**F24. NOTE: "about" and "≈" in values that could be read as criteria.**
- Line 38: "about 200x slower … (about 1-2 s …)".
- Line 111: "about 2.9x".
- Line 143: "about 0-125 spikes/s".
- Line 146: "PN about 64-118 Hz around a plateau of about 90 Hz".
- Line 154: "about 48% vs 2%".
- Line 155: "about twice".
- Line 172: "about 0.3%".
- These are descriptive, but V7a and V7b (146, 154–155) could be scored from them. The plan must say which, if any, are criteria.

**F25. NOTE: thresholds whose source is implicit.** The 1 Hz STABILITY (c) bar (160) is phase A's `rate_bar_hz` 1.0, with `fraction_bar` 0.1 and `responds_hz` 0.5 (registration). VERIFIED. The plan names only the 1 Hz bar. The other two are inherited silently.

**F26. NOTE: "deciding" vs "reported" arms.** Phase A said 2b and 4b "are reported and never decide". Gen 7 says H7c-all is "secondary … reported" (74–75) but also lists it in the preference order (106, "STD-in before STD-all"). This implies it can be adopted. The plan must make the two statements agree.

**F27. NOTE: model hash.** Line 18: "`df7e16022378` for generations 5 and 6". I recomputed registry.model_state's MODEL_FILES hash from git blobs: df7e16022378 at 728ac03, c1e6e62 and 7defd8a. VERIFIED. Phase A's registration hash dcb44bf09a88 also includes the two phase A fit scripts. The plan must say which hash gen 7's "refreeze" is compared against.

**F28. NOTE: data version.** The plan never names the connectome release or Explorer commit. Phase A's cell types come from Explorer 789cc6c (celltypes JSON `source.commit`), and MaleCNS v1.0 is the release (phase A DRAFT). VERIFIED. The plan must state both.

## 2. Mismatches with sources

Every numeric claim in the plan was checked against the three lit files at 728ac03. Rows marked "✓" match. Mismatches are numbered findings.

| Plan line | Plan text | Lit text | Result |
|---|---|---|---|
| 30 | v_rest −52, threshold −45, tau_m 20 ms (Shiu) | lit-SYN:41 "V_rest −52 mV, V_th −45 mV, τ_m 20 ms" | ✓ |
| 35 | Brunel "H state near 1/tau_rp at g < 4" | lit-SYN:128 quote | ✓ |
| 37 | "mIPSC decay 3.3-5.4 ms vs mEPSC 1.4-1.7 ms in the same culture preparation" | lit-SYN:47,51,52 | see F29 |
| 38 | GABA_B "about 1-2 s"; "about 200x" | lit-SYN:92 "≈1–2 s … VERIFIED-fig"; 200× is lit-SYN:135, INFERRED synthesis | F30 |
| 39 | p "about 0.79 (Kazama & Wilson 2008)" | lit-STD:36 "0.79 ± 0.02" | ✓ |
| 40 | "each spike leaves 72-78% … recovery takes 0.9-2.4 s" | lit-STD:41,43 (α 0.72, τ 2.4 s; f 0.78, τ 893 ms) | ✓ values; F31 wording |
| 41 | ORN→LN f 0.75, tau 1.57 s | lit-STD:49 "f = 0.75, τ = 1566 ms" | ✓ |
| 43–48 | Huang 2018: reversals 0/−70; I/E up to 100 "did not completely eliminate"; "never stopped"; STD ≤50% for τ > 125 ms; randomized brain not stabilised | lit-SYN:114,120–121 | ✓; F32 (DOI) |
| 109–111 | Cavallari matching; 52/18 ≈ 2.9 | lit-SYN:131 "g_syn = J/(⟨V⟩ − V_syn)"; 52/18 = 2.889 | ✓ (V_cal = v_rest replaces ⟨V⟩, which the plan states) |
| 119 | E_e +8.9 ± 1.7 (pupal), "0 mV" (embryonic) | lit-STD:58–59 | ✓ |
| 120 | GABA −37 ± 3, −41.5 ± 2.1, E_Cl −45; larval −56 ± 3 and −55 ± 2 "UNVERIFIED"; models −70 | lit-STD:60–63; lit-SYN:32 | ✓ (F34 on tags) |
| 121 | half-decay 2.1–2.5 ms PN; KC 5.2 ms | lit-SYN:43 "≈2.1–2.45 ms" VERIFIED-fig; lit-SYN:48 "5.23 ± 0.41" | ✓ (see F35) |
| 122 | tau_i culture 3.3–5.4 ms | lit-SYN:51–52 | ✓ |
| 123 | f 0.78 / 893 ms, n = 19, DM6 or VM2, female | lit-V7A:83 (B1c legend quote); lit-STD:43 | ✓ |
| 123 | K&W 2009: DM4, 4 Hz, n = 3, female 2–5 d; α 0.72, τ 2.4 s | lit-V7A:90 (B2d) | ✓ (F36) |
| 123 | U = 1 − f is depletion, not release probability; p 0.79 | lit-V7A:104–107 | ✓ |
| 123 | No TM U factor, no facilitation | lit-V7A:105–106 (points 2, 3) | ✓ |
| 124 | GABA_B onset alpha 25 ms, decay 1 s | lit-SYN:60 (25 ms VERIFIED); 1 s from lit-SYN:151 "suggested default" | F37 |
| 125 | g_gap/g_L 0.02; coefficients 0.003–0.034 | lit-SYN:68, 152 | ✓ (deferred) |
| 126 | PN rest −55 to −60 mV | lit-SYN:34 | ✓ |
| 140 | R_max 170/167/163/144, σ 16.3/11.8/12.4/44.8 | lit-V7A:37 (A1b Methods quote) | ✓; F38 (cited file) |
| 141 | 165/12 simulation defaults, not a fit | lit-V7A:38 (A1c) | ✓ vs lit-V7A; ✗ vs lit-STD (F38) |
| 141–142 | DM1 σ from GABA, reverts with PTX + CGP54626 | lit-V7A:41 (A1f) | ✓ |
| 143 | ORN 0–125 Hz; 6–12 recordings; "ORNs and PNs were recorded separately" | lit-V7A:45–46, 49 (A2g: INFERRED / CAN'T VERIFY) | F39 |
| 144–145 | no goodness of fit reported | lit-V7A:52 (A3a: main text only; supplement CAN'T VERIFY) | F40 |
| 146 | VM2 PN 64–118 Hz, plateau ≈90 Hz, VERIFIED-fig | lit-V7A:57 (A3f) | ✓ |
| 147–148 | "PN ≈ 3× ORN", J&W 2015, DA1, ORN ≈2–22 Hz, males, "VERIFIED" | lit-V7A:58–59 (A4a/b: quote and sex VERIFIED; ranges VERIFIED-fig; not in Olsen or Bhandawat) | ✓ source; F41 tag |
| 151 | four glomeruli of Olsen Fig 1B | lit-V7A:43 | ✓ |
| 153–156 | MN9 calcium ≈48% vs 2%; caffeine/denatonium = water; 1 M ≈ 2×; both somata | lit-STD:100–101, 104 | ✓ values; F42 |
| 157–159 | PN spont 1–9 Hz; ORN ≈1.5 Hz; no whole-brain spike rate | lit-STD:84–85, 98, 118, 128 | F43 |
| 170–174 | "unclear" fix sizes | no lit source; the plan cites a "read-only script" | F44 |

**F29. SHOULD-FIX: "the same culture preparation" (line 37).**
- The 3.3–5.4 ms mIPSC range spans two preparations: Su & O'Dowd 2003 (pupal, 3.3–3.7 ms; lit-SYN:51) and Lee et al. 2003 (embryonic, 5.4 ms; lit-SYN:52).
- The mEPSC 1.4–1.7 ms values are Su & O'Dowd only (lit-SYN:47).
- lit-SYN:83 restricts "same preparation" to "Su & O'Dowd Table 1: 1.4 vs 3.7 ms in KCs" and tags the 2–3× ratio INFERRED. VERIFIED (both texts).

**F30. NOTE: "about 200x slower for GABA_B".** The ratio appears only in lit-SYN:135, inside a section headed "INFERRED synthesis". The 1–2 s duration is VERIFIED-fig (lit-SYN:92). Line 33's header does say "INFERRED from VERIFIED quotes", so this is a tag-precision note.

**F31. NOTE: "recovery takes 0.9-2.4 s".** The sources give recovery time constants (τ 893 ms, 2.4 s; lit-STD:41, 43), not recovery durations. "Takes" reads as a duration.

**F32. NOTE: Huang 2018 DOI.** Line 44 gives "doi:10.3389/fninf.2018.00099". The lit files cite PMC6335393 (lit-SYN:32, 114) and contain no DOI. CAN'T VERIFY from the cited lit.

**F33. NOTE: tag drift for Rohrbough & Broadie.** The plan (120) follows lit-STD:62–63 ("UNVERIFIED (excerpt only)"). lit-SYN:27–28 tags the same values "VERIFIED via a search-index excerpt only". The two cited lit files disagree on the tag. The plan is consistent with the stricter one.

**F34. NOTE: "measured" vs "modelled" for tau_e.** Line 121 tags tau_e 5 ms "modelled" and cites a half-decay of "about 2.1-2.5 ms". lit-SYN:43 gives half-decay ≈2.1–2.45 ms as VERIFIED-fig, which is not an exponential τ. The plan must not let a scorer read the 5 ms value as measured. It does not; this is a note only.

**F35. NOTE: the KC value is in situ, not in vivo.** Line 121's "KC 5.2 ms in situ" matches lit-SYN:48 ("adult brain explant, RT"). ✓. Recorded because line 121 sits next to "in vivo" PN values.

**F36. NOTE: an internal lit inconsistency the plan inherits.** lit-STD:41 and its UNVERIFIED list item 2 (lit-STD:134) still say K&W 2009's "sex, saline and stimulation frequency" are UNVERIFIED. lit-V7A:90 (B2d) resolves them (female 2–5 d, 4 Hz, n = 3). The plan uses the resolved values (123), so a reader of lit-STD alone would see a mismatch. VERIFIED.

**F37. NOTE: GABA_B decay "1 s" (line 124).**
- The 25 ms onset is measured (lit-SYN:60).
- "Decay 1 s" appears only as a "Suggested default" in lit-SYN:151 ("decay ≈ 1 s"). The measured statements are durations: "lasts ≈1 s or more" (lit-SYN:57) and "≈1–2 s" (lit-SYN:92).
- The plan's status cell says "modelled from in vivo pharmacology". The row is deferred to gen 8, so this is a note.

**F38. SHOULD-FIX: V7a's cited source still carries the superseded 165/12.**
- Line 137: "Targets, from `docs/lit/gen7_lit_std_validation_2026-10-18.md`".
- That file says the opposite of plan line 141:
  - lit-STD:56 "R_max = 165 spikes/s, σ = 12 spikes/s … FITTED";
  - lit-STD:89 "fitted R_max 165, σ 12 spikes/s";
  - lit-STD:126 "I/O saturation: Olsen 2010 (R_max 165 spikes/s, fitted)".
- The correct per-glomerulus fits and the "simulation defaults" reading are in lit-V7A:37–38, which the plan cites only for the STD legend (123). The sources header (9–11) does not list lit-V7A at all. VERIFIED (all three texts).

**F39. SHOULD-FIX: "ORNs and PNs were recorded separately" (line 144) is stated flatly.** lit-V7A:49 (A2g) tags it "INFERRED (separate recordings); CAN'T VERIFY (same vs different fly)", because the Olsen supplement was not obtained.

**F40. SHOULD-FIX: "No goodness of fit or residual scatter is reported for these fits" (144–145) omits the caveat.** lit-V7A:52 (A3a) reads "VERIFIED (absent from main text); CAN'T VERIFY (supplement)". The tolerance argument at line 145 rests on this absence.

**F41. NOTE: the tag on line 148.** "ORN about 2-22 Hz … VERIFIED". In lit-V7A:59 the "three-fold" quote and "males" are VERIFIED, while the 2–22 Hz range is VERIFIED-fig.

**F42. SHOULD-FIX: V7b's "both MN9 somata respond (bilateral)" (156).**
- lit-STD:104 gives "Both somata respond in Fig 6A (by eye)", which is VERIFIED-fig only.
- lit-STD:100 says imaging was "one cell body per fly" and the sex "not stated for imaging". The model is male (MaleCNS).
- With MN9_R at 633 inputs and statusLabel "RT Hard to trace" (my 11-13 file), a bilateral ordering in the model is confounded with reconstruction. INFERRED.

**F43. NOTE: absence claims stated as facts.**
- Line 153: "No MN9 firing rate has been recorded". lit-STD:113 says "none found (WebSearch 18 Oct 2026)".
- Line 159: "no fly whole-brain spike-rate measurement exists". lit-STD:118 says "none found".
- These are search results, not established absences.
- Line 159's "about 1.5 Hz measured" ORN rate is DA1-specific (lit-STD:98, Jeanne & Wilson Fig 1H, VERIFIED-fig). lit-V7A:67 quotes K&W 2008 for DM4 ORNs at "4 spikes/s" and VM2 at "about 7 spikes/s".

**F44. SHOULD-FIX: the "unclear" fix numbers (170–174) have no committed source.**
- My arithmetic checks pass (INFERRED):
  - 8,673 + 404 + 716 = 9,793;
  - 329 + 320 + 53 + 14 = 716;
  - 111,043 + 142,690 = 253,733;
  - 2,282,863 / (2,282,863 + 420,718) = 84.4%;
  - 2,292,250 / (2,292,250 + 469,396) = 83.0%;
  - 469,396 / 420,718 = +11.6% (the plan rounds to "+12%").
- The script is described only as "read-only script on the pinned data". Its path, commit and output file are not cited, and "about 0.3% of the signed graph" has no stated denominator. CAN'T VERIFY.

## 3. Confounds

**F45. BLOCKER: a refit per arm mixes two changes in every comparison.** This follows from F10. If calibrations are refit separately per synapse model or per STD arm, each stage-1 difference from the with-fix baseline is (synapse change + refit), not "the synapse change alone" (95). Line 95's cleanliness claim holds only if the refit happens once, after adoption, or not at all for stage 1. INFERRED.

**F46. SHOULD-FIX: H7c-all vs H7c-in is not "recurrent vs input".**
- Lines 65–66: "If only H7c-all is viable, depression of the recurrent synapses is the operative mechanism".
- H7c-all minus H7c-in adds STD to every non-ORN→ALPN/ALLN chemical synapse. That includes the gustatory and sugar pathway to MN9, HRN, visual and VNC synapses, and all central synapses, not just the AL recurrent ones (PN→LN, LN→PN, PN→PN) named at 60–61.
- The pair therefore mixes "AL recurrence depressed" with "every other pathway depressed". The reading at 65–66 needs an arm that isolates AL recurrence, or a narrower stated reading. INFERRED (from the definitions at 57 and 67–70).

**F47. SHOULD-FIX: the E_i sweep mixes reversal with conductance size.**
- By the matching rule (109–111), g_i = w/(V_cal − E_i) with V_cal −52 mV.
- Per-synapse inhibitory conductance relative to excitatory is therefore 52/3 ≈ 17.3 at E_i −55, 52/18 ≈ 2.9 at −70 and 52/28 ≈ 1.9 at −80. INFERRED arithmetic.
- So the sweep changes both the reversal and the shunting conductance, by about 9× across the range. Line 113 names only "how inhibition scales as a cell depolarizes". The plan must state that conductance size co-varies with E_i.

**F48. SHOULD-FIX: tau_i 10 vs 5 mixes "slower" with "more" inhibition.**
- The matching rule fixes the initial PSP (110), not the integrated charge. Doubling tau_i at a fixed per-spike increment roughly doubles inhibitory charge per spike. INFERRED.
- H7b (56) is about "slow inhibition". The plan must state whether the comparison is meant to hold charge or peak constant.

**F49. SHOULD-FIX: STD vs no STD mixes dynamics with mean gain.** With w_eff = w × A and A ≤ 1, any spike train lowers the time-averaged weight. Line 63 recognises this for input synapses ("weakening the drive"). The same holds for STD-all on recurrent synapses, where "limiting recurrence" and "weakening recurrence" cannot be separated by this design. INFERRED.

**F50. SHOULD-FIX: STD-all also depresses the sugar → MN9 pathway.** Under STD-all, FUNCTION and FUNCTION-q (sugar drive) can fail because the gustatory path is depressed, while STABILITY improves. A non-viable STD-all arm could then reflect lost function rather than failed stability. The plan must state that component verdicts are reported per arm, or how this is read. INFERRED.

**F51. SHOULD-FIX: is the cell set held constant across fix-on and fix-off?**
- Phase A asserted the simulated cell set was unchanged (m5: "every cut arm asserts that `len(m.lif_ids)` equals the uncut value").
- The fix adds 20,428 edges (172). If any cell gains its first edge at or above the floor, the cell count, and with it STABILITY (c)'s whole-CNS rate and fraction-active denominators, differ between the two baselines. CAN'T VERIFY whether this happens. The plan must state it or assert it.

**F52. NOTE: conductance vs current also changes stimulus synapses.** Lines 108–113 do not say whether `S_stim` (Poisson source → target) and the giant-fibre gap junctions (I_gap) and `g_shunt` term (model.py:165) change with the synapse model. If `S_stim` stays current-based in conductance arms, the drive differs between arms in kind, not just the recurrent synapses. INFERRED.

**F53. NOTE: clean pairs exist for H7d.** The pairs (current, STD-x) vs (conductance, STD-x) and (conductance, none) vs (conductance, STD-x) are each single-change pairs inside stage 1, all with the fix. VERIFIED from 88–95. H7d's verdict still needs the pairing named (F57).

## 4. Predictions

**F54. BLOCKER: H7a's criterion does not match its claim.**
- Lines 53–55: "conductance-based synapses alone … give at least one w that is functional and stable. *Prediction: FAILS* (Huang 2018). Falsified if no w passes STABILITY at any E_i in the sweep."
- The falsifier tests STABILITY only, while the claim is "functional and stable", i.e. viable. Two readings follow:
  - "no w passes STABILITY" leaves H7a's verdict undefined when STABILITY passes but FUNCTION fails;
  - "any E_i in the sweep" depends on stage 2 running (F4).
- Also not stated: which STABILITY components ((a), (b), (c)) and which tau_i.

**F55. SHOULD-FIX: H7b has no criterion or prediction.**
- Line 56: "separate time constants with tau_i > tau_e, on top of H7a, give a viable w."
- At the primary settings tau_i equals tau_e (both 5 ms, 121–122), so stage 1 never tests H7b. Only stage 2's tau_i 10 does, and stage 2 is conditional.
- No prediction is logged. Nothing states which E_i, which STD setting, or what verdict applies if stage 2 does not run.

**F56. SHOULD-FIX: H7c-in and H7c-all have no logged predictions or confidence.** Lines 57–75 give only the design. The stage-1 prediction (91–92, "an STD arm is the first viable one, if any is") does not say which scope. Phase A logged a prediction with confidence for each question (Q1–Q6, phase A DRAFT @ c1e6e62:120–129).

**F57. SHOULD-FIX: H7d needs its comparison set.**
- Line 76: "conductance-based + STD gives a viable w where neither alone does."
- Not stated:
  - which STD scope(s);
  - whether "neither alone" means (conductance, none) and (current, the same STD scope), at any w or at the same w;
  - its verdict if one single arm is viable;
  - whether stage-2 variants count.
- No prediction is logged.

**F58. SHOULD-FIX: "registered as a set; each is a separate verdict" (line 51) has no verdict vocabulary.** Phase A used held / not held / undetermined, with "undetermined" rules (my CHOICE-15 to -18). Gen 7 must state when each H7 verdict is undetermined: for example, pending top-ups, stage 2 not run, or V1-like stops.

**F59. NOTE: H7e and H7f are deferred.** Lines 77–80 say both are deferred to generation 8 "(decided 18 Oct)". H7f is "reported … not a viability arm". Neither has a gen 7 verdict. Recorded so that a scorer does not score them.

## 5. Missing controls and stop rules

**F60. BLOCKER: no stop rule when the positive control misbehaves.** See F8. Phase A's V1 "Phase 1b's outcome C is not replicated. Stop for review; no default changes" (phase A DRAFT @ c1e6e62:226) has no gen 7 counterpart.

**F61. SHOULD-FIX: no outcome when every arm fails, including stage 2.** Line 101 points to generation 8 "on gen 7's outcome" with no mapping. Phase A's rule 4 ("If no cell is viable … The next phase is …") is the precedent.

**F62. SHOULD-FIX: no confirm or specificity step for an adopted arm.**
- Phase A required "an adopted w is provisional until gen6_rule.md's refine and confirm steps (both nulls) pass" (registration `decision.provisional`) and ran a specificity null (A3).
- Line 104's list ("smallest viable w, top-up rule, LATERALITY -> H") omits the confirm step and any null for gen 7.

**F63. SHOULD-FIX: the scorer and the "commit before launch" rule are not stated.**
- Phase A: "every rule, amendment, prediction and analysis script is committed before the cloud runs are launched", with `fit/gen6_phaseA_score.py` hashed into the registration and smoke-tested on toy data (phase A DRAFT @ c1e6e62:16, 315–318).
- Gen 7 states only that the registration is "committed before any generation-7 run" (3–4). It says nothing about a hashed scorer, a smoke test or a preflight.
- It also has no blind-scoring provision for an independent recompute (the phase A outcome was "confirmed by an independent blind recompute", 5–6).

**F64. SHOULD-FIX: no numerics stop rule for real runs.** See F17. The v ≥ E_i − 1 mV assertion is smoke-only (130).
- With strong conductances, explicit Euler at dt 0.1 ms can overshoot when the effective membrane τ (τ_m / (1 + Σg)) falls near dt. INFERRED (standard numerics).
- The plan must state what a registered run does on overshoot, and what a dt 0.05 disagreement does.

**F65. SHOULD-FIX: no STD reset or tail control.** See F1 and F9. No control shows that A starts at 1 at each trial's drive onset, or that the tail-based self-sustained test measures the same thing in STD arms.

**F66. SHOULD-FIX: no rule for ORN spikes in H7c-in under sugar.** Line 72 reports the count but gives no rule if it is non-zero and changes FUNCTION. (Line 73's "Otherwise … equal" covers only the zero case.)

**F67. NOTE: reporting rules not carried over.** Phase A's by-mode reporting for bimodal arms (m3/mi3), MN9 per-cell reporting, and "every summary is computed by a committed script" are not in the gen 7 "reused unchanged" list (82–83). The list names viability components, drives, protocol and grid only.

**F68. NOTE: the A4-style AL readout is not repeated.** Gen 7 is motivated by "the blind-drive tail sits inside the antennal lobe" (31). Nothing in gen 7 reports whether an arm moves the AL tail share (phase A's M9 measure). This is a reporting gap, not a viability one.

## 6. The VM7 split and other V7a flags (from `v7a_mn9r_check_2026-11-13.md`)

**F69. BLOCKER: VM7 is split in MaleCNS but single in Olsen 2010.**
- MaleCNS v1.0 / Explorer @ 789cc6c has no `ORN_VM7` and no `VM7_*PN`. It has:
  - ORN_VM7d, 36 cells ("View all ORN_VM7d (36 cells)");
  - ORN_VM7v, 25 cells;
  - VM7d_adPN, 7 cells (3 L / 4 R);
  - VM7v_adPN, 3 cells (2 L / 1 R).
  VERIFIED (11-13 file §2a/2b).
- Olsen 2010 reports one "VM7" fit (R_max 163, σ 12.4; lit-V7A:37). Its odor is 2-butanone, and the text never says VM7d or VM7v or names a receptor (10-18 file: "It never says VM7d/VM7v or names a receptor"). VERIFIED. Which MaleCNS half Olsen's "VM7" corresponds to: CAN'T VERIFY.
- The plan's rule, "drive every `ORN_<glomerulus>` cell … read the uniglomerular PNs of that glomerulus" (182–183), matches zero cells for a literal ORN_VM7. A prefix ORN_VM7* merges two receptor channels. INFERRED.
- The plan must specify, for VM7:
  - (a) the mapping of Olsen's "VM7" to VM7d, VM7v or both, with its stated basis or flagged as an assumption;
  - (b) which ORN types are driven (one half, the other, or both together);
  - (c) which PN types are read;
  - (d) whether PN rates are pooled across VM7d_adPN and VM7v_adPN, and with what weighting (by cell or by type);
  - (e) which curve or value the single Olsen VM7 fit is compared with: each half, the pool, or one designated half;
  - (f) whether VM7 is excluded if (a) cannot be sourced.

**F70. SHOULD-FIX: DM4 has a GABAergic uniglomerular PN.**
- DM4_vPN (2 cells) is "gaba" ("GABA (86.5% CL)"). Its largest input is DM4_adPN (28.7%); ORN_DM4 supplies 10.1%. VERIFIED (11-13 file §2b).
- It is in the ALPN list (celltypes JSON @ c1e6e62, together with DL5_adPN, DM1_lPN, DM4_adPN, VM7d_adPN, VM7v_adPN). VERIFIED.
- "Read the uniglomerular PNs of that glomerulus" (183–184) would include it. Which DM4 PNs Olsen recorded: CAN'T VERIFY. The plan must state whether DM4_vPN is read.

**F71. SHOULD-FIX: ORN types are not in the pinned cell-type list, and the title format differs.**
- `data/gen6_phaseA_celltypes.json` (sha `ea8bad7d…`) holds only ALPN/ALLN/Kenyon_Cell. No ORN_DM4, ORN_DL5, ORN_VM7d, ORN_VM7v or ORN_DM1 is in it. VERIFIED (parsed today).
- None of the 11 V7a types uses the "has N cells" span title. All use `title="View all <type> (N cells)"`. VERIFIED (11-13 file §2.0).
- The plan's "the type mapping is listed in the registration" (183–184) must state the source of the ORN type names and counts (neurons.parquet `type`, or an Explorer extraction with its rule). Any extractor keyed on "has N cells" finds none of these types.

**F72. SHOULD-FIX: "the real ORN count" vs simulated and side-known cells.**
- ORN_DM4 and ORN_DL5 each have one body with `rootSide` "unknown". DM4 has 2 "RT Hard to trace" ORN bodies, DL5 1, VM7v 2 and DM1 2. VERIFIED (11-13 file §2a).
- A cell with no edge at or above floor 5 is not simulated (phase A B3: "a mirrored partner P' must be a simulated cell").
- The plan must state whether the driven count is the type count or the simulated count, how side-unknown ORNs are handled if PNs are read per side, and whether any ORN_* type in V7a is absent from the pinned `neurons.parquet`. That last point: CAN'T VERIFY (11-13 file, unverifiable item 6).

**F73. NOTE: DM4 PNs are "Prelim Roughly traced"; PN n is small.** DM4_adPN and DM4_vPN are "Prelim Roughly traced". Four PN types have one cell per side. VERIFIED (11-13 file §2b, §2c items 6). Per-glomerulus readouts rest on 2 cells for DM4, DL5 and DM1, which bears on the aggregation and tolerance choice in F5.

**F74. NOTE: cross-glomerular and multiglomerular input.** ORN_DL2v supplies 5.3% of DM4_adPN's input. Multiglomerular PNs (e.g. M_l2PNl20 from ORN_DM1, 3.8%) receive the driven ORNs' output but are not "of that glomerulus". VERIFIED (11-13 file §2b, §2c). Olsen checked that "these odors do not activate non-cognate ORNs" (lit-V7A:65). The plan's rule implicitly matches this. Recorded so that the registration states it.

## 7. Comparison with `docs/gen6_phaseA_DRAFT.md` @ c1e6e62

| Phase A safeguard (location @ c1e6e62) | Gen 7 @ 728ac03 | Status |
|---|---|---|
| "Definitions fixed before registering" section that "wins" over the rest (215–219) | none | **absent** |
| Explicit deciding cells and outcome table, incl. V1 stop (221–231) | preference order only (104–106) | **weaker** (F1, F3, F60) |
| Process rule: rules, predictions **and analysis scripts** committed before launch (13–18) | registration before runs (3–4); no scorer named | **weaker** (F63) |
| Seeds M5 (6000 + index; top-up 7000 + index; paired) (349–352) | none | **absent** (F12) |
| Top-up rule incl. pooling, named arms (232–240) | "top-up rule" by reference (104) | **by reference only** (F7) |
| Multiple comparisons M6, declared uncorrected (354–355) | none | **absent** (F18) |
| Predictions with confidence for every question (120–129) | H7a and one stage-wide sentence | **weaker** (F54–F57) |
| Missing arm fails safe (mi8, 449; `definitions.missing_arm`) | none | **absent** (F17) |
| Simulated cell set constant across arms (m5, 375–376) | none; the fix may change it | **absent** (F51) |
| Pinned type list with sha256 (247–249) | file cited (69), not on branch, no sha | **weaker** (F7, F71) |
| Smoke tests on toy data, preflight on pinned data (315–318, 427–435, 450–455) | none | **absent** (F63) |
| Adopted w provisional until refine/confirm with both nulls (244) | not mentioned | **absent** (F62) |
| Specificity null A3 at 95/100 (338–347) | none | **absent** (F62) |
| By-mode reporting, committed summaries (97–105) | not in the reused list | **weaker** (F67) |
| Bootstrap via gen6_rule.md | not mentioned | **by implication only** (F13) |
| Reconstruction status recorded (53–54, 395–400) | not mentioned for V7b's MN9 or V7a's ORNs/PNs | **absent** (F42, F72) |

## 8. What I could not access or verify

- The script behind the "unclear" fix sizes (170–174): no path or commit is cited. CAN'T VERIFY the counts, only their arithmetic.
- Whether the ORN_* types for V7a, and any newly signed cells from the fix, exist as simulated cells in the pinned `neurons.parquet`. That data is not in git; I did not fetch it.
- Which MaleCNS half Olsen's "VM7" is. The Olsen supplement is still unobtained (cell.com 403, per lit-V7A:19).
- The Huang 2018 DOI on line 44, which is not in the lit files.
- I did not run any FLYCNS simulation code. The only computation was the model-hash recomputation from git blobs (F27), plus arithmetic.

## 9. Scratch and repo state

- `/workspace/flycns_ro`: I ran `git fetch` of `gen7/synapse-model-draft` and `gen6/phaseA-decisions`, and a general `git fetch origin`, which updated remote-tracking refs only. The working tree is unchanged at 46e7d25 and clean.
- `/tmp/g7/` (164 KB): extracted copies of the plan, the three lit files, both phase A DRAFT versions, and the cell-type JSON. It is removable.
- No new clones were made.
