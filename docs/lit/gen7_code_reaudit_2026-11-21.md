# Gen 7 code re-audit after fixes (PR #26), 21 Nov 2026

## Summary

- **Commit:** `gen7/model-code` at 33aae64 (`33aae64a17eb891712671704d80ad125ee0ce38d`), PR #26 head, PR open. VERIFIED: public API, plus `git archive` to /tmp/g7r.
- **Baseline:** my 18 Nov audit at 80c5501 (`docs/lit/gen7_code_audit_2026-11-18.md`). Jayson's response is D10 of `docs/gen7_synapse_model_DRAFT.md` (lines 414–441).
- **Read-only:** nothing was written to any repo. `/workspace/flycns_ro` is clean.

### Probe status

| Probe | 18 Nov | 33aae64 | Status |
|---|---|---|---|
| P1 NaN first | PASS | NUMERICS FAIL | CLOSED |
| P1b NaN later | PASS | FAIL | CLOSED |
| P1c all NaN | PASS | FAIL | CLOSED |
| P3a dt missing | final | not final | CLOSED |
| P3b dt differs | final | not final, undet. | CLOSED |
| P4 irrelevant top-ups | blocking | hyp-only | CLOSED |
| P7 empty arm | PASS a/b | UNRESOLVED | CLOSED |
| P8 ORN diff | weak diag | fields listed | CLOSED |
| P8b no orn key | silent | refused | CHANGED (closed) |
| V1 V7a gap | dropped | missing / refused | CLOSED |
| P6 (F13) dup top-up | flips | still flips | STILL OPEN (by decision) |

### Findings by rank

- **BLOCKER: 0.** F1, the 18 Nov blocker, is closed.
- **SHOULD-FIX: 1.**
  - **R1.** A candidate that is viable only because of its top-up becomes FINAL when the dt 0.05 ms repeat is UNRESOLVED on the same component as the unpooled main arms. Viability at the decision w is never shown at dt 0.05 ms.
- **NOTE: 7** (R2–R8).

### Other results

- **New breaking inputs:**
  - R1 (Fa, N1d), and R4 (the top-up and repeat are copies of the main rows, and the outcome is FINAL with no new data).
  - `name_topups`: no input found where a top-up that can change the outcome is left unnamed or non-blocking. All 6,561 configurations were checked.
- **F13 verdict:** the reason holds against a *refusal* rule (VERIFIED). It does not hold against a *flag*. The seed check verifies the declared spec, not the rows (VERIFIED by a run).

## Method and adaptations

- **Scripts:** the 18 Nov scripts in /tmp/g7probe were re-run against /tmp/g7r.
- **Adaptations:**
  - `mk2.py` = `mk.py` with the scorer path changed from /tmp/g7repo to /tmp/g7r.
  - `probes2.py` writes to `R_*` directories. The ORN field was renamed from `max_abs_difference` to `differing_fields`.
  - `v7aprobe2.py` uses `olsen_fit_hz`, renamed from `olsen_hz`.
  - **V1 non-smoke path:** the box has no registration, so `SC.load` was monkeypatched to its smoke reader and `v7a(D, smoke=False)` was called directly (`v1b.py`).
  - **Seed and spec checks in `load`:** run with a fake `G.REG` and fake registration stamps (`f13.py`).
- **New scripts:**
  - `fz.py`: finalize probes.
  - `nt_enum.py`: exhaustive enumeration over `name_topups`.
  - `f13.py`: top-up duplication.
  - `sm.py`: `std_marks` old vs new.
- **Unit tests:** `tests/unit.py` gen-7 tests were run in /tmp/g7venv:
  - `t_gen7_scoring_rules`: True.
  - `t_gen7_parts_match_rerun_jobs`: True (63 parts).
  - `t_gen7_design_and_toy_run`: True.
- **Not run:** a real simulation on the pinned data (no MaleCNS data or neuPrint token on the box), and `probe` mode.

## PART 1

### Probe detail (actual vs expected)

- **P1, P1b, P1c (NaN lowest v in c w040).**
  - Expected: NUMERICS FAIL.
  - Actual: `numerics: None FAIL`, c w040 "fails", outcome C7, and the flag lists `c_w040`. VERIFIED by run.
  - Code: `numerics` treats NaN or no trials as FAIL (score.py ~117). The unit test asserts NaN-first, NaN-later and empty.
- **P2 (boundary, unchanged).**
  - −71.0 passes. −71.0000001 and −inf fail. VERIFIED.
- **P3a (repeat missing).**
  - Expected: not final.
  - Actual: `sin w 0.4 final False`, with flag "run g7-dt-sin-w040; until then the candidate is unchecked at dt 0.05 ms". VERIFIED.
- **P3b (repeat differs).**
  - Expected: not final, stop for review.
  - Actual: `final False`, differs `['function','function_q','stability_b','stability_c']`, overall and H7c-in "undetermined". VERIFIED.
- **P4 (irrelevant top-ups).**
  - The sin w080 top-up lies above sin's viable w and is no longer named.
  - The csin w060 top-up (csin has no viable w) is listed only in `topups_for_hypothesis_only`.
  - `final True`. VERIFIED.
- **P7 (blind arm with 0 trials).**
  - Expected: not PASS.
  - Actual: stability_b UNRESOLVED and stability_c UNRESOLVED. The top-up is named and blocking, so `final False`. VERIFIED (`count_zero`, score.py ~105).
- **P8 (ORN under sugar, differs only in mn9_li).**
  - Actual: `differing_fields: ['mn9_li'], trials_differing: 1`, and the flag is raised. VERIFIED.
- **P8b (no `orn_spikes`).**
  - Actual: "sin_sugar_w040: a trial has no orn_spikes; scoring refused". VERIFIED.
  - This changes the behaviour from a silent result to a refusal, as D10 states.
- **V1 (DM1 120 Hz dropped, DM4 120 Hz duplicated).**
  - Smoke: compared 4, consistent 3, `missing: ['DM1']`. VERIFIED.
  - Non-smoke: refused with "glomerulus DM4 has [2, 2, 2, 2, 2, 4] runs per rate, not 2". VERIFIED (score.py 401–403).
  - The DM4 fit reports `rms_residual_hz` 0.0126 and `monotone` True (F9). VERIFIED.

### Other findings D10 claims to address

| F | D10 claim | Check | Tag |
|---|---|---|---|
| F1 | final needs agreeing repeat | P3a/b closed; see R1 | VERIFIED (run) |
| F2 | named only below min viable | enumeration, 0 misses | VERIFIED (run) |
| F3 | NaN → FAIL | P1* | VERIFIED |
| F4 | stated | D6 line 358–359 | VERIFIED |
| F5 | renamed | `olsen_fit_hz` 410 | VERIFIED |
| F6 | stated | CRITERIA V7a limits | VERIFIED (read) |
| F7 | NUMERICS in viable | D3 + CRITERIA 227 | VERIFIED |
| F8 | grid-edge rule | D3 "made exact" | VERIFIED |
| F9 | RMS + monotone | V1 output | VERIFIED |
| F10 | refuse / count 4 | V1 | VERIFIED |
| F11 | fields listed | P8/P8b | VERIFIED |
| F12 | UNRESOLVED | P7 | VERIFIED |
| F14 | label | sal → "extrapolated: never adopted" | VERIFIED (run) |
| F16 | V7a flagged | NaN v7a_c_w040 flagged | VERIFIED (run) |
| F18 | V7a seed | D6 line 367 | VERIFIED |
| F19 | codes | CRITERIA 256 | VERIFIED |
| F21 | settle | DRAFT 233 "200 ms settle" | VERIFIED |
| F22 | arm states | `arm_set_states`, `not_passing` 474 | VERIFIED (run) |
| F23 | listed | `unresolved_in_both` 444 | VERIFIED (read); not in flags (R1) |

Two further notes on the table:
- F15 says "the dt repeat covers them". The repeat covers only the candidate's two arms at one w. INFERRED from score.py 429–446; see R6.
- F17, F20 and F24 are stated, not changed. VERIFIED (D10 text).

### F13: D10's reason and assessment

D10 (DRAFT ~437–438), quoted: "F13 (a top-up duplicating the main rows): two silent arms have identical rows by right, so comparing rows would refuse valid data. A registered top-up must carry its own registered seed, which `load` checks."

1. **The first half holds.** All-silent arms can have identical rows, so a *refusal* would reject valid data. INFERRED from the trial schema.
2. **The second half is true only of the metadata.**
   - VERIFIED, score.py 62: `rec["spec"] != G.ARMS[name]` → refuse.
   - A top-up file whose spec carries the main arm's seed was refused: "was run with another specification than the registered one" (`f13.py`).
   - A top-up whose *rows* are a copy of the main arm's, under the registered top-up spec, was ACCEPTED by the non-smoke `load`.
3. **The effect is unchanged from 18 Nov.**
   - In the run, stability_c went from UNRESOLVED, rate CI [0.79, 1.033], to PASS, CI [0.79, 0.993], and sin became viable.
   - A dt005 file copied the same way agreed (both UNRESOLVED on stability_c), so the outcome was `sin 0.4 final True` with no new data at all. No flag was raised. VERIFIED (run).
4. **Mitigation.** The runner builds from `spec["seed"]` (gen7_synapse.py 487), so the rows match the seed whenever the runner writes them. VERIFIED (read). Only a manual or pipeline copy error triggers this. INFERRED.
5. **Verdict:** the reason is valid against refusing, but it does not answer *reporting* identical rows. NOTE (R4).

## PART 2: breaking the new code

### name_topups() (score.py 237–255)

- **Exhaustive check (`nt_enum.py`).** It uses the real `name_topups`, `state` and `decide` over every status combination for 4 decision sets × 2 w values (3^8 = 6,561 configurations), and every resolution of the candidate rows.
  - Top-ups that could change (code, w) but are not blocking: **0**.
  - Blocking top-ups that can never change the outcome (from the main arms): **0**.
  - VERIFIED (run). Scope: 2 w values per set; INFERRED to generalise, because the rule is per-set monotone in w.
- **Dynamic over-blocking: found (R3, NOTE).**
  - In 3,025 of the 6,561 configurations, some reachable state has the outcome fixed while a still-missing blocking top-up keeps it PROVISIONAL.
  - End-to-end example (N1): B pending at w060, S-in pending at w040, C viable.
    - After B's top-up makes B viable, the outcome is `F 0.6 final False`, because `sin_*_w040_topup` is missing.
    - S-in can no longer change F.
    - Cause: naming is computed from pass 1 only (score.py 452–462).
  - This follows D3's "judged on the main arms alone", so it is plan-conform. It only delays finality.

### finalize() (score.py 313–329) and dt_check() (429–446)

| Case | Result | Final? | Tag |
|---|---|---|---|
| repeat missing (Fm) | not done | False | VERIFIED |
| sugar only (Fp) | not done | False | VERIFIED |
| wrong w (Fw) | not done | False | VERIFIED |
| wrong arm, C (Fr) | not done | False | VERIFIED |
| NaN v in repeat (Fn) | differs: numerics | False | VERIFIED |
| empty repeat (Fe) | differs: all 5 | False | VERIFIED |
| B top-up switches to F (Fx2) | needs b repeat | False | VERIFIED |
| main U, top-up PASS, repeat U (Fa) | agree | **True** | VERIFIED: R1 |
| same via F (N1d) | agree | **True** | VERIFIED: R1 |
| main U, top-up PASS, repeat PASS (Fb) | differs | False, review | VERIFIED: R2 |
| repeat = copy of main (Fd) | agree | **True** | VERIFIED: R4 |
| repeat = 20 dup rows (Fd2) | agree (smoke) | True | VERIFIED smoke; non-smoke refuses by count, INFERRED from load 64–66 |
| mismatched seed in spec | refused | — | VERIFIED (fake REG) |
| non-candidate viable C (Fh) | H7a "held" | n/a | VERIFIED: R6 |

### Findings

**R1 SHOULD-FIX: viability at the decision w is never confirmed at dt 0.05 ms.**
- **Code.** `dt_check` compares `set_at(..., pool=False)` (score.py 438) with the 10-trial repeat. `numerics_sensitive = a != b` (443).
- **Where it breaks.** When the candidate is viable only after pooling, the unpooled main arms show UNRESOLVED.
  - A repeat that is also UNRESOLVED "agrees", and `finalize` returns the outcome unchanged (329).
  - Fa: `sin 0.4 final True` with stability_c main=UNRESOLVED and dt005=UNRESOLVED. N1d is the same for outcome F.
- **The plan is followed literally.** D6 (DRAFT 352–354) and CRITERIA (gen7_synapse.py 252–253) both say "(10 trials each, unpooled)".
- **Conflict with D10.** D10 F1 says "A candidate is final only after its repeat has run and agrees". Here the repeat agrees only that the decision w is *not* shown PASS.
- **Not flagged.** `unresolved_in_both` is computed (444) but is not added to `flags` (score.py 492–500).
- **Tags.** VERIFIED (run, quotes above). The rank is my judgement.

**R2 NOTE: false alarm in the opposite direction.**
- Fb: the same pooled candidate with a repeat that PASSes is flagged numerics-sensitive, and the result stops for review.
- Fe: an empty repeat is reported as numerics-sensitive instead of "not run".
- Both are conservative. VERIFIED.

**R3 NOTE: dynamic over-blocking.** See the name_topups section above. VERIFIED.

**R4 NOTE: copied rows are accepted (F13 still open).** See the F13 assessment above. VERIFIED.

**R5 NOTE: a missing repeat makes the candidate "undetermined" for the hypotheses.**
- **Code.** score.py 321–323 sets the candidate's state to "undetermined" when the repeat is missing, and the unit test asserts it.
- **Plan and CRITERIA.** D6 (DRAFT 355–357) and CRITERIA (251–252) say only that the outcome is PROVISIONAL until the repeat has run. "Undetermined" is stated only for a repeat that *differs*.
- **Status.** DIFFERS; the code is stricter. VERIFIED.

**R6 NOTE: viable sets other than the candidate are never dt-checked.**
- Fh: S-in is the final candidate, and C and CS-in are viable. H7a is "held" for C, although C never ran at dt 0.05 ms.
- This follows the plan (only the candidate is repeated). D10's F15 reason ("the dt repeat covers them") is therefore partial. VERIFIED (run).

**R7 NOTE: new `std_marks` (gen7_synapse.py 332–362).**
- **Equivalence.** Old and new agree on 6,000 random cases: duplicate bodyIds, float ids, missing ids, None types, empty tables. Masks and logs are identical apart from the new `orn_cells_marked`. VERIFIED (`sm.py`).
- **NaN bodyId.** Same result as the old version. VERIFIED.
- **String ids.** The new version raises TypeError where the old one silently marked nothing. VERIFIED. This is an improvement.

**R8 NOTE: `probe` passes silently when phase A's file is absent.**
- If `results/gen6_phaseA/arms/c1_sugar_w040.json` is missing in a non-smoke run, `ok` stays None. The run does not fail and records no `p0_network_is_phase_a` key (gen7_synapse.py 593–604).
- VERIFIED by reading; not run (needs pinned data).

### Rule table: plan vs CRITERIA vs code

| Rule | Plan | CRITERIA | Code | Verdict |
|---|---|---|---|---|
| Which w get a top-up | D3: below the set's smallest viable w, or a set with none; main arms only | top_up 241–243, same | 247–249 | MATCH |
| Which top-ups hold the outcome | D3: up to and including the first viable set | 243–245 | 250–254; decide 305 | MATCH |
| Later set | D3: only if the set has no viable w; holds nothing | 245–246 | 252–253 | MATCH |
| Final needs repeat | D6/D10: PROVISIONAL until run | 251–252 | 320–323 | MATCH |
| Missing repeat → hypotheses | not stated | not stated | undetermined | DIFFERS (R5) |
| Repeat differs | D6: not final, undetermined, review | 252–255 | 324–328 | MATCH |
| What is compared | D6: "10 trials each, unpooled" | same | 438–443 | MATCH (R1 gap) |
| Both UNRESOLVED | D10 F23: listed | not stated | 444, not flagged | MATCH (weak) |
| NaN lowest v | D6: FAIL | 229 | ~117 | MATCH |
| Codes | D3 | 256 | decide 297–303 | MATCH |
| Not-adoptable label | D3 | 257–258 | 487–489 | MATCH |
| Top-up seed | D6: 7000 + index | 243 | ARMS 156; load 62 | MATCH (R4) |

### New edge cases from `git diff 80c5501..33aae64`

- **`count_zero` and `numerics` on empty input:** UNRESOLVED and FAIL. VERIFIED (P7, unit test).
- **V7a:** smoke reports a missing glomerulus. Non-smoke refuses any glomerulus with a run count other than `V7A_TRIALS` at any rate, which covers a wholly absent glomerulus (0 ≠ 2). VERIFIED for the DM4 case; the absent case is INFERRED from 401.
- **V7a NaN check** (`x != x`, 418): flags NaN and None. VERIFIED.
- **Pooling with a one-drive top-up:** still refused (P5). VERIFIED.
- **`rerun.yml`:** adds a manual `g7-preflight` job running `fit/gen7_synapse.py probe`. VERIFIED (diff). Not run.
- **`std_marks`:** see R7. **`probe`:** see R8.

## Not done or inaccessible

- No real-data run (no pinned MaleCNS data or neuPrint token on the box). `gh` is not authenticated; public API only.
- The literature report `gen7_density_lit_2026-11-21.md` (pt66u PART 3) was not in this brief and was not done.

## Scratch

- **Archive at 33aae64:** /tmp/g7r.
- **Probes:** /tmp/g7probe. Outputs are in `R_*` and `probes2.out`. Scripts: `mk2.py`, `probes2.py`, `v7aprobe2.py`, `v1b.py`, `fz.py`, `nt_enum.py`, `f13.py`, `sm.py`.
- **Python environment:** /tmp/g7venv.
