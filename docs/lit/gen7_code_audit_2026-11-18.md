# FLYCNS gen 7: code against plan audit

18 Nov 2026 (PT). Read-only. No repo file, branch or PR was changed.

## Summary

- **Sha read:** `80c5501f35b2fcf4a7e5ce77619e0b4ad2d13b4a` on `gen7/model-code`. This is the head of PR #26 ("Gen 7 synapse model: code, arms, scorer (DRAFT, not registered, do not merge)", open, base `gen6/phaseA-decisions`), per the public GitHub API. The only change since `fc6e4c2` is 5 lines in `fit/gen7_synapse.py` (preflight).
- **Plan:** `docs/gen7_synapse_model_DRAFT.md` @ 80c5501, section "Definitions fixed before registering", D1–D9 (lines 220–389).
- **Checklist (Part 1):** 95 rows. 87 MATCH, 4 DIFFERS, 3 MISSING and 1 not checkable in code.
- **Findings:** 24 in all: **1 BLOCKER, 6 SHOULD-FIX, 17 NOTE**.
- **BLOCKER F1:** D6 says a numerics-sensitive candidate "stays provisional", but `outcome.final` ignores the dt check. A missing or differing dt 0.05 ms repeat still gives `final: True` and final hypothesis verdicts. Reproduced (P3a, P3b).
- **Scorer inputs that give a wrong or plan-divergent verdict:**
  - P3a/P3b: dt repeat missing or differing, yet the outcome is final (F1).
  - P4: top-ups are named at w that cannot change the outcome, so the outcome is PROVISIONAL and "overall" is undetermined (F2).
  - P1: a NaN `lowest_v_mV` gives NUMERICS PASS and a viable C (F3).
  - V1: a V7a record missing one rate drops that glomerulus silently ("3 of 3", not "3 of 4") (F10).
  - H1–H3: Hill shapes that are wrong still count as "consistent" (F9).
  - P6b: duplicated top-up rows flip STABILITY (c) from UNRESOLVED to PASS (F13).
  - P7: a 0-trial arm passes STABILITY (a)/(b), in smoke only (F12).
- **3a:** P0 makes phase A's cell-1 call, options, seeds, trial function, dt and drive. On the toy network, the old (ff816c1) and new model default paths gave identical spikes. Rows could still differ through the engine, the compiler or the runner, not through the code.
- **3b:** No. For those cells, dv/dt > 0 at v = E_i under the equations as written. Only the Euler step can undershoot, and only when ge + gi > 199 (in leak units) at dt 0.1 ms.
- **3c:** No, they are not the same quantities. The two windows are the same length. Olsen's ORN and PN responses are baseline-subtracted and measured in single cells. The model's ORN rate is a commanded Poisson rate from silence, and its PN rate is a cell-type mean with a zero baseline.

Tags: VERIFIED (quote and location), INFERRED, UNVERIFIED. Ranks: BLOCKER, SHOULD-FIX, NOTE. File references are `path:line` at 80c5501. "Plan Lnnn" means a line of the DRAFT.

## Part 1: checklist, D1–D9

Short quotes: plan, then code. D8 is text corrections only, so it has no code rows.

| # | item (plan line) | code | verdict | note |
|---|---|---|---|---|
| 1 | Inherit FUNCTION, FUNCTION-q, STABILITY a–c, LATERALITY, self-sustained rule, drives (L228–229) | `fit/gen7_synapse.py:185-188`, `fit/gen7_synapse_score.py:40-42` | MATCH | Taken from `PA.CRITERIA`. VERIFIED in scratch: thresholds, sweep, self-sustained and drives equal `registration_v5.json`. |
| 2 | "10 trials, 1,000 ms drive, 500 ms tail, restore" (L229) | `fit/gen6_phaseA.py:55,581-588`; `gen7_synapse.py:465` | MATCH | The inherited code also has a 200 ms settle the plan text omits (F21). |
| 3 | Grid "0.4 / 0.5 / 0.6 / 0.8 / 1.0" (L230) | `gen6_phaseA.py:57` | MATCH | |
| 4 | Thresholds 0.5 Hz, 1.0 Hz, 0.10, 0.8 (L230–231) | score `:40-42` | MATCH | VERIFIED equal to the registration. |
| 5 | "percentile bootstrap… 2,000… seed 0… also for pooled" (L232–233) | `flycns/stats.py:40-54`; score `:74-84,110-113` | MATCH | N_BOOT 2000 (scratch). Applied to the pooled lists in `set_at`. |
| 6 | Cell types file, sha `ea8bad7d…` (L234–235) | `gen6_phaseA.py:52`; `gen7_synapse.py:361,726` | MATCH | INFERRED that `celltypes(check=True)` compares the sha (body not read). |
| 7 | "ORN types… by exact name" (L235) | `gen7_synapse.py:404` (`stim_type == ref["orn"]`) | MATCH | The STD scopes use the prefix `ORN_`, as D2 says. |
| 8 | Connectome pinned by MANIFEST (L235–236) | `gen7_synapse.py:439` (`require_data`) | MATCH | `data/MANIFEST.json` hash equals the registration's (scratch). |
| 9 | "Scorer readings: those of `gen6_phaseA_score.py`" (L237) | score `:74-135` vs `gen6_phaseA_score.py:71-123` | MATCH | Component functions are identical in text. Top-up naming changed, as D1 asks. |
| 10 | "a top-up counts only if both drives… otherwise scoring is refused" (L238) | score `:209-211` | MATCH | Probe P5: refusal confirmed. |
| 11 | "while a named top-up is missing the outcome is PROVISIONAL" (L239) | score `:274,277-278` | MATCH | |
| 12 | "refreeze is compared against… `df7e16022378`" (L240) | text only, `gen7_synapse.py:192` | MISSING | Not implemented in the files reviewed (F20). |
| 13 | "Every arm is a sweep: 5 w x {sugar, blind} x 10 trials, v-only reset, MN9_R as in the data" (L243) | `gen7_synapse.py:143-154`, `FLY` `gen6_phaseA.py:70` | MATCH | No mirror transform is called. |
| 14 | P0 current / none / off, control (L247) | `:81` | MATCH | |
| 15 | B current / none / on (L248) | `:82` | MATCH | |
| 16 | S-in, C, CS-in deciding (L249–251) | `:83-85,101` | MATCH | |
| 17 | S-al, CS-al reported (L252) | `:86-87` | MATCH | |
| 18 | S-all, CS-all "reported, never adopted" (L253) | `:88-89`; not in `ORDER` | MATCH | |
| 19 | Sensitivity arms, E_i -55 / -80, tau_i 10, f 0.72 / 2.4 s (L254) | `:90-99` | MATCH | 8 sets. |
| 20 | Scope "in": pre `ORN_`, post in ALPN/ALLN (L256–257) | `:319-320` | MATCH | Selftest "marks in" PASS. |
| 21 | Scope "AL" (L257–259) | `:320` | MATCH | |
| 22 | Scope "all": "every chemical synapse" (L259) | `:339`; `flycns/model.py:288` | MATCH | Applies to stimulus synapses too (`model.py:350-351`). |
| 23 | "There is no conditional stage" (L261–262) | `PARTS` `:164-173` | MATCH | Only top-up and dt parts are conditional. |
| 24 | "E_e +/-10 mV and tau_e 2 ms are not run" (L262–263) | `:214` | MATCH | |
| 25 | "17 arm sets, 170 sweep arms" (L264) | selftest `:647-649` | MATCH | PASS in scratch. |
| 26 | R: "P0's per-w component verdicts and self-sustained counts differ" (L267–269) | score `:236-242,263-265` | MATCH | `EXPECT_C1` equals the committed `phaseA.json`: the selftest check passed in scratch. |
| 27 | F: "B is viable" (L270) | score `:266-267` | MATCH | |
| 28 | "first viable… S-in, C, CS-in… by arm first, then by w" (L271–272) | score `:269,273`; `:395-397` | MATCH | Probe P9: S-in at w 1.0 beats C at w 0.4. |
| 29 | C7: "No deciding arm is viable" (L273) | score `:270-272` | MATCH | |
| 30 | C7: reported arms' viability "stated, with the label 'extrapolated'" (L273–275) | none | MISSING | No "extrapolat" string in the scorer (F14). |
| 31 | "'Viable' is phase A's: FUNCTION, FUNCTION-q and STABILITY (a), (b), (c)" (L276) | score `:195-196,216` | DIFFERS | The code adds NUMERICS, as D6 L337 says. The plan contradicts itself (F7). |
| 32 | "LATERALITY… gates nothing" (L277–278) | score `:131-135,221` | MATCH | Not among the components. |
| 33 | "A candidate is provisional" (L279–281) | score `:276` | MATCH | Text only. |
| 34 | "No calibration is refit… grid w is `w_scale` itself" (L281–282) | `gen7_synapse.py:349` | MATCH | |
| 35 | Top-ups: "an UNRESOLVED component at a w that could become a decision w names 10 more trials of both drives" (L283–284) | score `:216,219` | DIFFERS | Named at every candidate w, even above a viable w (F2, P4). |
| 36 | Top-ups only for B and the three deciding arms (L284–285) | `DECISION` `:102`; score `:219` | MATCH | |
| 37 | held / not held / undetermined; "not viable" if every w FAILs or stays UNRESOLVED after top-up (L288–289) | score `:227-233` | MATCH | |
| 38 | Reported arm with UNRESOLVED gives undetermined (L290–291) | score `:231-232` | MATCH | |
| 39 | H7-P, D3.1 (L295) | score `:296` | MATCH | |
| 40 | H7-F, B (L296) | `:296` | MATCH | |
| 41 | H7a, C primary (L297) | `:296` | MATCH | Can be decided by NUMERICS alone (F22). |
| 42 | H7b, C at tau_i 10 vs C (L298) | `:293` | MATCH | |
| 43 | H7c-in, S-in (L299) | `:297` | MATCH | |
| 44 | H7d, "CS-in where neither C nor S-in" (L300) | `:294-295` | MATCH | |
| 45 | H7c-al, "held for at least one" (L301) | `:289-291,297` | MATCH | |
| 46 | H7c-all (L302) | `:297` | MATCH | |
| 47 | overall: outcome C7 (L303) | `:298` | MATCH | |
| 48 | Under R every verdict is undetermined except H7-P (L288) | `:299-300` | MATCH | |
| 49 | "'H7c' alone has no verdict" (L308) | `:296-297` | MATCH | |
| 50 | "kick… n_synapses x 0.275 mV x w x gain, signed" (L313) | `model.py:294` | MATCH | |
| 51 | "Current-based: g += w_mV" (L313) | `model.py:307-308,338` | MATCH | |
| 52 | "ge += w_mV / (E_e - V_rest)… gi += \|w_mV\| / (V_rest - E_i)" (L314–315) | `model.py:320-321` | MATCH | |
| 53 | "ge decays with tau_syn (5 ms), gi with tau_i" (L315) | `model.py:209,45` | MATCH | |
| 54 | "stimulus sources' synapses follow the same rule" (L316) | `model.py:350-351` | MATCH | Closes prior F9. |
| 55 | "Electrical coupling is unchanged" (L316) | `model.py:367-392` | MATCH | Unchanged in the diff from ff816c1. |
| 56 | Depression "per connection… recurrent and stimulus-source" (L317) | `model.py:291-330,336,351` | MATCH | |
| 57 | "delivered with w x A, then A -> f x A; recovers… tau_D" (L318) | `model.py:314-315` | MATCH | |
| 58 | "A is advanced at delivery; same delay" (L318–319) | `model.py:328` | MATCH | |
| 59 | "per-trial restore returns A to 1" (L319–320) | `model.py:325-326,453-457` | MATCH | INFERRED: Brian2 `store`/`restore` covers synaptic variables. Toy S-in = B equality is consistent with that. |
| 60 | Component verdicts reported separately (L325–326) | score `:192-197,221` | MATCH | |
| 61 | Self-sustained "as in phase A" (L327) | `gen6_phaseA.py:600` | MATCH | |
| 62 | "A missing or crashed arm refuses scoring" (L331) | score `:50-52`; arms `:503-504` | MATCH | |
| 63 | Lowest v of cells "without spike-triggered adaptation and without electrical coupling" (L332–333) | `model.py:492-506`; arms `:467` | MATCH | |
| 64 | "Below E_i - 1 mV in any sugar or blind trial… NUMERICS, FAIL" (L336–337) | score `:116-123,196` | MATCH | NaN hole (F3). Equality at E_i - 1 is PASS (P2), per "below". |
| 65 | "a conductance arm without the record refuses scoring" (L337) | score `:119-120` | MATCH | |
| 66 | "repeated at dt 0.05 ms with the same seeds" (L338–339) | arms `:154`; score `:357-365` | MATCH | The same seed does not give the same input (F4). |
| 67 | "if a component verdict differs (10 trials each, unpooled)" (L339–340) | score `:366-371` | MATCH | |
| 68 | "flagged numerics-sensitive" (L340) | score `:412-413` | MATCH | |
| 69 | "…and stays provisional" (L340) | none | MISSING | `final` ignores the dt check (F1). |
| 70 | Fix "applied in `load_graph` to the pinned edges (already at the 5-synapse floor)" (L341) | `flycns/graph.py:252-261` | MATCH | Applied after the floor filter. |
| 71 | Cell count "with and without" the fix (L341–342) | arms `:516-527,477` | MATCH | |
| 72 | "each arm's rates use its own cell count" (L342) | `gen6_phaseA.py:551-554` | MATCH | |
| 73 | ORN spikes per sugar trial, "mean per w reported" (L343) | arms `:466`; score `:317-318` | MATCH | |
| 74 | "If it is zero, S-in's sugar arms must equal B's… field by field… flag" (L343–345) | score `:308-329,410-411` | MATCH | Whole-record equality. The diagnostics are weak (F11). |
| 75 | "Seeds: 6000 + index(drive, w)" (L346) | arms `:151` | MATCH | Selftest PASS. |
| 76 | "Top-ups 7000 + index" (L347) | `:153` | MATCH | |
| 77 | "V7a 9000 + index" (L347) | `:158` | MATCH | "index" is the w index here (F18). |
| 78 | Arms script and scorer hashed (L348) | `:707` | MATCH | |
| 79 | "toy-data smoke tests" (L349) | selftest `:617-699` | MATCH | PASS in scratch. |
| 80 | Preflight "reproduces the fix's sizes" (L349–350) | `:509-567` | MATCH | |
| 81 | V7a arms B, S-in, C, CS-in, S-all, CS-all, each w (L353) | `:113,155-158` | MATCH | |
| 82 | "every simulated cell of the ORN type becomes a Poisson source" (L354) | `:451-452,404` | MATCH | All five ORN types are sources in every V7a trial (F17). |
| 83 | Rates 5–120 Hz, 500 ms, 2 trials (L354–355) | `:114-115` | MATCH | |
| 84 | "mean rate of the PN type's cells over the same 500 ms, mean of the trials" (L355–356) | `:420-421`; score `:342-345` | MATCH | |
| 85 | "fitted with the exponent fixed at 1.5" (L356–357) | `:375-386` | MATCH | |
| 86 | "R_max within +/-25% and sigma within a factor of 2" (L357–358) | `:389-394` | DIFFERS | Adds "sigma not at an edge of the grid" (F8). |
| 87 | "the rates beside Olsen's points" (L358–359) | score `:347` | DIFFERS | `olsen_hz` is Olsen's fitted curve, not the Fig 1B points (F5). |
| 88 | "No verdict enters the outcome" (L359) | score `:353` | MATCH | |
| 89 | "side-unknown ORNs are driven with the rest" (L359–360) | `model.py:163` | MATCH | All cells of the type are sources. |
| 90 | "V7b is not run" (L361) | arms `:214` | MATCH | |
| 91 | AL share of the blind tail, by-mode summaries (L364–365) | score `:169-178,138-145` | MATCH | |
| 92 | Three files hashed (L379–381) | arms `:707` | MATCH | `gen6_phaseA.py` sha equals the registration_v5 entry. |
| 93 | Arm names `<set>_<drive>_<w>`, `v7a_<set>_<w>` (L382–383) | `:150,157` | MATCH | |
| 94 | 17 + 6 parts; 20 + 20 conditional (L384–385) | `:163-173`; `rerun.yml:168-` | MATCH | |
| 95 | Order of steps (L386–389) | process | n/a | Not checkable in code. |

## Part 2: trying to break the scorer

**Method.** I copied the repo at 80c5501 to `/tmp/g7repo` and imported the scorer in its own smoke mode (registration checks off). I then wrote synthetic arm JSONs for all 17 sets × 5 w × 2 drives. P0 is built to reproduce `EXPECT_C1` exactly: the scorer reports "replicates: True", and the baseline input gives C7, final.

Trial kinds used: "viable" means 10 sugar trials with MN9 5 Hz and blind trials at 0.1 Hz / 1% active. "ustraddle" means blind rates alternating 0.5 / 1.5 Hz, which makes STABILITY (c) UNRESOLVED.

One artefact of the probes: their synthetic `lowest_v_mV` of -60 mV makes the E_i -55 sensitivity sets FAIL NUMERICS in every probe, which is correct for that input. Their extra ORN-check flags come from the deliberately different synthetic rows. Neither affects the deciding sets.

| probe | input | actual | expected (plan) | finding |
|---|---|---|---|---|
| P3a | S-in viable at w 0.4; no `*_dt005` files | outcome `sin`, **final True**; flag "run g7-dt-sin-w040" | not final until the repeat (D6 L338–340, D9 L388) | F1, BLOCKER |
| P3b | as P3a, plus `sin_*_w040_dt005` with sugar MN9 0 and a loud blind drive | flag "numerics-sensitive: function, function_q, stability_b, stability_c"; **final True**; H7c-in "held"; overall "not held" | "stays provisional" | F1, BLOCKER |
| P4 | S-in viable at w 0.4; S-in w 0.8 and CS-in w 0.6 "ustraddle" | outcome `sin`, **final False**; top-ups named `sin_*_w080`, `csin_*_w060`; overall **undetermined** | those w cannot become the decision w (L283), so final | F2 |
| P1 | C viable at w 0.4; sugar trial 0 `lowest_v_mV` NaN | NUMERICS estimate NaN, **PASS**; C viable; outcome `c`, final | fail safe: FAIL or refuse (D6 L331) | F3 |
| P1b | NaN in trial 3 instead | estimate -60, PASS; the NaN is ignored | as P1 | F3 |
| P1c | every trial NaN | NaN, PASS | as P1 | F3 |
| P2 | blind trial 5 `lowest_v_mV` = -71.0, then -71.0000001, then -inf | PASS, FAIL, FAIL | "below E_i - 1": PASS at equality is correct | no defect |
| P5 | S-in w 0.8 candidate; only `sin_blind_w080_topup` exists | SystemExit "only one drive… Scoring refused" | refuse (D1 L238) | no defect |
| P6b | blind rates [0.6×8, 1.5×2] (CI upper 1.05, UNRESOLVED), with a top-up that duplicates the same rows | pooled CI upper 0.96, so **PASS** | duplicated rows are not new trials | F13 (non-smoke `load` checks spec and seed, not row content) |
| P7 | S-in `blind_w040` with 0 trials (smoke) | STABILITY (b) **PASS**, (c) UNRESOLVED | missing data never PASS | F12 (smoke only; non-smoke `load` checks the trial count) |
| P8 | `sin_sugar_w040` equals `b_sugar_w040` except trial 2 `mn9_li` 0.9; ORN spikes 0 | flagged (correct); `max_abs_difference` shows 0 for all four keys | a field-by-field report | F11 |
| P8b | one trial without the `orn_spikes` key | KeyError crash | refuse with a message | F11 |
| P9 | S-in viable at w 1.0 only; C viable at w 0.4 | `sin` at w 1.0 | arm order first (L272) | no defect |
| P10 | B "ustraddle" at w 0.6; S-in viable at w 0.4 | `sin`, final False; B top-up named | B could become F, so provisional | no defect |
| V1 | V7a record with 60 rows: DM1 at 120 Hz removed, DM4 at 120 Hz duplicated | DM1 dropped silently; "consistent 3 of 3" | 4 compared glomeruli, or refuse | F10 |
| H1 | DM4 Olsen curve, with PN 0 at 5 and 10 Hz | r_max 185.5, sigma 25.4: **consistent** | shape differs at low input | F9 |
| H2 | DM4 curve, falling 30% at 120 Hz | r_max 144.8, sigma 12.5: **consistent** | non-monotone | F9 |
| H3 | DM4 curve +40 / -20 Hz alternating | r_max 188, sigma 16.4: **consistent** | SSE 5115 | F9 |
| H4 | flat 170; linear 1.5·r; one nonzero point | sigma at a grid edge, or r_max 337: not consistent | | no defect |
| H5 | NaN or inf at one rate | sigma 0.1 `at_bound`, so not consistent (r_max NaN/inf reported) | fails closed, silently | NOTE in F9 |
| H6 | 1 point; 2 points | 1: at bound, not consistent; 2: exact fit, consistent | 2 points are fewer than needed to constrain shape; the scorer always has 6 rates | no defect |
| H7 | exact DM4 and DM1 curves; ×1.3; ×0.74 | recovered (sigma 16.29, 44.77); ×1.3 and ×0.74 not consistent | tolerance edges per the selftest | no defect |

**By component:**
- Top-up naming and pooling: names parse correctly to `g7-topup-<set>-<w>`. Pooling needs both drives (refuses otherwise). Over-naming is F2; content duplication is F13.
- `state()`: correct on every probe.
- `decide()`: order and B-pending cases are correct. Finality is F1.
- `hypotheses()`: H7b/H7d logic checked against the D4 table, including undetermined branches (P4: H7d "not held" because S-in is viable, correct).
- Numerics component: F3.
- dt repeat comparison: F1 and F4, plus F23.
- ORN-under-sugar check: F11.
- `hill_fit` / `v7a_consistent`: no convergence failure is possible (fixed grid). The weaknesses are F8, F9 and F10.

## Part 3

### a. Is P0 exactly phase A's cell 1?

Line by line:

| element | phase A c1 | gen 7 P0 | same? |
|---|---|---|---|
| graph | `load_graph(data, min_weight=st["floor"], amines=st["amines"])` (`gen6_phaseA.py:271`) | identical call, no `unclear=` (`gen7_synapse.py:296-297`); default `unclear="dropped"` (`graph.py:229`) | yes (VERIFIED) |
| transform | `transform()`: no mirror or cut for c1 (`gen6_phaseA.py:501-515`) | not called | yes, an identity for c1 (VERIFIED) |
| options | `_opt(st)` (`:519-522`) | `PA._opt(st)` when current and STD off (`gen7_synapse.py:335-336`) | yes; selftest "P0 is phase A's cell 1" PASS |
| params | `LIFParams(w_scale=st["w_scale"], seed=seed)` | `LIFParams(w_scale=w, seed=seed)` at dt 0.1 (`:349`) | yes |
| seeds | 6000 + index | `SEED_BASE + PA._pair_index` (`:148-151`) | yes; selftest PASS |
| drive | `MALE_SUGAR` 100 Hz; `male_blind_pool` 20 Hz | the same objects (`:445-449`) | yes |
| trial | `run_sweep_trial` (settle 200, drive 1000, tail 500) | `PA.run_sweep_trial` (`:465`) | yes |
| extra per trial | none | `spike_frame()`, `lowest_v_mV()` after the trial (None for current) | no state change (INFERRED) |
| model default path | `model.py` @ ff816c1 | the default branch rebuilds the same `S_rec`/`S_stim` objects in the same order (`model.py:332-357`) | yes |

On the toy network, 3 sugar + 3 blind trials (seed 6000, w 1.0) gave identical spike counts, spike-time sums and id sums with `flycns/` from ff816c1 and from 80c5501 (VERIFIED, scratch, numpy engine, brian2 2.11.0). `requirements.lock`, `fit/gen6_phaseA.py`, `fit/gen6_phaseA_score.py`, `flycns/stats.py` and `data/MANIFEST.json` hash identically to the registration_v5 entries (VERIFIED).

**What could still make rows differ** (INFERRED unless stated):
- Engine: `codegen_target()` picks cython or numpy at run time, and `FLYCNS_CODEGEN` is "plumbing", so it is not refused (VERIFIED `integrity.py:55-56`).
- Compiler and runner: `windows-latest`, with MSVC flags `/Ox` plus a CPU-dependent `/arch` slot (brian2 default; the slot is empty in my scratch). A runner image or CPU change can change float results and flip a spike.
- Data: the cache key hashes the fetch scripts and the MANIFEST. A cache miss re-fetches from neuPrint.
- Not a cause: RNG order (no new RNG draws in the default path) and float summation order (one `S_rec` layer, same order).

The R test compares only verdicts and self-sustained counts (`score:236-242`), as D3.1 says. Row identity is reported only (`p0_rows`, `score:245-258`) (F24).

### b. Can anything but the Euler step take v below E_i?

**No** (VERIFIED from the equations; derivation INFERRED). The membrane equation (`model.py:212`, with `:205`):
- `dv/dt = (v_rest + I_base - v + ge*(E_e - v) + gi*(E_i - v) + I_gap + g_shunt*(v_rest - v) - a)/tau_m`, unless refractory.

For a cell with `b_adapt` 0 and no electrical pair (`model.py:501-504`):
- `a` starts at 0 and gets `+= b_adapt` = 0, so a ≡ 0.
- `I_gap` is a summed variable written only by `S_gap` (`:374-376`), so it is 0.
- `g_shunt` is set only for stimulus-coupled posts (`:386`), which are excluded, so it is 0.
- `I_base` and the noise term are 0 at the declared defaults (`:79-80,189`); `refuse_overrides` refuses non-default values (`integrity.py:58-61`).
- ge ≥ 0 and gi ≥ 0, because `we`, `wi` ≥ 0 (`:320-321`), A ∈ (0, 1] and the peptide factor is 1 with peptides off.

So at v = E_i, tau_m·dv/dt = (v_rest − E_i) + ge·(E_e − E_i) > 0, since E_i < V_rest is enforced at `:195-199`. Reset goes to -52 mV (`:232`), refractory freezes v, and there is no clipping and no kick.

The Euler step, with h = dt/tau_m:
- v' − E_i = (1 − h(1+ge+gi))(v − E_i) + h[(v_rest − E_i) + ge(E_e − E_i)].
- It can go negative only if h(1+ge+gi) > 1, i.e. ge + gi > 199 at dt 0.1 ms (399 at 0.05).

Demo (scratch, toy, 20 sources at 200 Hz onto one cell with no adaptation and no coupling):
- gi ≈ 102: lowest v -69.87 mV.
- gi ≈ 341: -100.3 mV.
- gi ≈ 1022: -178.6 mV, with spurious spikes.

`v_low` is recorded at `when="end"` every step (`:239`), so the guard catches each of these (VERIFIED).

### c. V7a against Olsen et al. 2010 (Neuron 66:287–299, doi 10.1016/j.neuron.2010.04.009, PMID 20435004)

Identity is VERIFIED via the Europe PMC API. The quotes are VERIFIED from my saved PMC full text, `lit/PMC2866644.txt` (saved 17 Nov 2026, 16:01 PT). A live re-fetch today failed: PMC returned 403 and the Europe PMC full text timed out.

- Experimental Procedures, Data Analysis (txt line 226): "Each cell was tested with multiple stimuli, typically with 4 trials per stimulus spaced 40-60 sec apart. The response magnitude for each cell/stimulus combination was quantified as the trial-averaged number of spikes during the 500-msec odor stimulus period, minus the trial-averaged baseline spike rate during the preceding 500 msec."
- Same section, line 221: "ORN spikes were recorded extracellularly from sensilla… Whole-cell patch-clamp recordings were made from PN somata in current-clamp mode."
- Results, line 90: "PN is the response of an individual PN to a private odor stimulus, and ORN is the response of an individual presynaptic ORN to the same stimulus."
- Line 228: "R max and σ were free parameters. R max = 170, 167, 163, and 144, and σ = 16.3, 11.8, 12.4, and 44.8".
- Fig 1B legend, line 81: "All values are means of 6 -12 recordings, ± SEM."

**Is the rate baseline-subtracted?** Yes (VERIFIED, line 226). That it applies to both ORNs and PNs is INFERRED: the sentence says "each cell" and follows the description of both recording types. The text mixes "number of spikes" with "baseline spike rate"; that the result was converted to spikes/s is INFERRED from the figure axes.

**Same quantities?**

| | Olsen 2010 | model (`gen7_synapse.py:414-421`) |
|---|---|---|
| ORN rate | measured, single ORN, odor-evoked, baseline-subtracted, mean over 4 trials then 6–12 recordings | commanded Poisson rate of every source of the type; baseline 0 by construction |
| PN rate | individual PN, baseline-subtracted | mean over the type's cells (2–7), both sides; no subtraction (baseline 0) |
| window | 500 ms odor period; baseline from the preceding 500 ms | [0, 500) ms after `restore`, drive on at t = 0, no pre-period |
| other input | private odor, checked not to drive non-cognate ORNs (Results, Fig S1 not read) | only the target type driven; the other four V7a ORN types clamped at 0 |

The window lengths match. Neither rate is the same quantity: an increment over spontaneous firing in vivo, against an absolute rate from silence in the model. The two coincide only if spontaneous activity does not change the evoked increment (INFERRED, untested). This is F6.

## Findings (ranked)

**F1. BLOCKER: the dt check never affects finality.**
- D6 (L338–340): "the candidate is flagged numerics-sensitive and stays provisional". D9 (L388): "run any named top-up and dt parts; score again".
- Code: `final = not missing_topups` (`score:274`); `dt_check` (`:357-371`) only adds a flag (`:412-415`). Hypothesis verdicts and `prediction_correct` are emitted as final.
- P3a and P3b reproduce it. VERIFIED.
- Because the scorer is hashed into the registration, this cannot be changed after registering.

**F2. SHOULD-FIX: top-ups are named beyond "could become a decision w".**
- Plan L283–284 vs `score:216,219`: every candidate w of a decision set is named, including w above an already viable w, and candidates in sets later in the order than a viable set.
- Result: a PROVISIONAL outcome and an undetermined "overall" until parts that cannot change the outcome are run (P4). VERIFIED.

**F3. SHOULD-FIX: NUMERICS fails open on NaN.**
- `float(min(lows))` (`score:121`) returns NaN when the first value is NaN and skips later NaNs. `NaN < bar` is False, so the verdict is PASS (P1, P1b, P1c; VERIFIED).
- D6 L331: "A deciding arm cannot PASS on missing data."
- I could not make the model produce NaN: a diverging Euler step overshoots past threshold and resets. NaN is therefore unlikely from the model itself (INFERRED).

**F4. SHOULD-FIX: the dt repeat's "same seeds" does not repeat the input.**
- A Brian2 `PoissonGroup` with seed 6000 at dt 0.1 and dt 0.05 gave different trains (411 vs 409 spikes; first spike 0.1 vs 2.45 ms; VERIFIED in scratch).
- So the dt comparison mixes the step change with a new Poisson draw. A 10-trial verdict near a bar can flip from sampling alone (INFERRED).

**F5. SHOULD-FIX: V7a reports Olsen's fitted curve, not Olsen's points.**
- `olsen_hz = hill(V7A_RATES, r_max, sigma)` (`score:347`).
- The plan asks for "the rates beside Olsen's points" (L358–359) and "next to Olsen's Fig 1B points (VERIFIED-fig)" (L182–183).
- VERIFIED.

**F6. SHOULD-FIX: the V7a quantities differ from Olsen's (Part 3c).**
- Plan L187 says "PN rate over the same 500 ms, as in the paper". That holds for window length only.
- The baseline-subtracted, single-cell, measured-ORN quantities of the paper are not what the model reads.

**F7. SHOULD-FIX: the plan contradicts itself on "viable".**
- D3 L276 lists five components. D6 L337 adds NUMERICS as "a sixth component".
- The code follows D6. A blind scorer reading D3 alone would differ. VERIFIED.

**F8. NOTE:** `v7a_consistent` adds "sigma not at an edge of the grid" (`gen7_synapse.py:390`; stated in CRITERIA `:274-275`), which is not in D7 L357–358.

**F9. NOTE:** "consistent" has no goodness-of-fit term, so shapes that are wrong pass (H1–H3). NaN or inf inputs fail closed silently (H5). This is consistent with the plan as written; V7a is report-only.

**F10. NOTE:** `v7a()` skips a glomerulus whose rates are incomplete (`score:343-344`), and the compared count shrinks with it (V1). Non-smoke `load` checks only the total row count.

**F11. NOTE:** the ORN-under-sugar diagnostics are weak.
- `max_abs_difference` covers 4 keys and shows zeros when the difference lies elsewhere (P8).
- A missing `orn_spikes` key crashes (P8b), while `arm_summary` defaults it to 0 (`score:187`).

**F12. NOTE:** `count_zero` passes with 0 trials (P7). This is smoke-only; non-smoke `load` refuses a wrong trial count (`score:63-65`).

**F13. NOTE:** top-up rows are not checked for being distinct from the main rows. Duplicated rows narrow the interval (P6b: UNRESOLVED to PASS). The non-smoke spec and seed check limits this to edited files.

**F14. NOTE:** the C7 "extrapolated" label (L273–275) is absent from the output.

**F15. NOTE:** the numerics guard excludes every adapting or coupled cell, so MN9 (the FUNCTION readout) and the giant fibres are not covered. Only the dt repeat speaks to them. This is a stated design choice (D6 L333–336).

**F16. NOTE:** V7a arms record `lowest_v_mV` (`gen7_synapse.py:423`), but no verdict or flag uses it.

**F17. NOTE:** in V7a every trial makes all five ORN types sources (`:451-452`). The undriven glomeruli's ORNs are clamped silent instead of being LIF cells, a network that differs from the sweep arms'.

**F18. NOTE:** "V7a 9000 + index" (L347) is undefined. The code uses the w index, 0–4 (`:158`), the same seed in every V7a set.

**F19. NOTE:** the D3.3 outcome code is the set name (`sin`, `c`, `csin`; `score:270`). The plan names no code.

**F20. NOTE:** the D1 L240 refreeze comparison is not in these files. It is the D9 step-2 fingerprint run.

**F21. NOTE:** the D1 L229 protocol text omits the inherited 200 ms settle (`gen6_phaseA.py:55`). It is present in registration_v5's sweep text.

**F22. NOTE:** H7a (and H7d) can be "not held" from NUMERICS alone. D5 L325–326 says arms are read "by which component failed", but the hypothesis output carries no component.

**F23. NOTE:** the dt repeat compares unpooled main arms. If the decision w needed pooling, both sides may be UNRESOLVED, and "not sensitive" says little.

**F24. NOTE:** the R test is coarse (verdicts and counts). Row identity is reported only; see 3a for the engine and runner causes.

### Prior audit blockers (728ac03), where relevant

| prior | status at 80c5501 |
|---|---|
| F1 viable / decision table | fixed in D3 and the scorer; D3/D6 text conflict (F7) |
| F2 LATERALITY -> H | fixed: gates nothing (`score:131-135`) |
| F3 tie rule | fixed: fixed order, arm first |
| F4 E_i sweep in adoption | fixed: sensitivity arms always run; H7a on C |
| F5 / F6 V7a / V7b | V7a defined and report-only (F5, F6, F8–F10 here); V7b not run |
| F7 inherited phase A text | fixed: pinned to registration_v5 (thresholds VERIFIED equal) |
| F8 / F60 positive control, stop rule | fixed: R from `EXPECT_C1` (VERIFIED against phaseA.json) |
| F9 where STD sits | fixed: stimulus synapses depress (`model.py:350-351`) |
| F10 / F45 refits | fixed: none in gen 7 |
| F54 H7a criterion | fixed: viability of C |
| F69 VM7 | decided VM7d compared, VM7v reported; VM7d = Or42a still INFERRED in the plan |

## What could not be accessed

- Live Olsen 2010 full text today: PMC returned 403 and Europe PMC full text timed out; I used the saved copy. The Olsen supplement: `lit/olsen2010_supp.pdf` is 1,816 bytes, not the PDF.
- Real MaleCNS data: the parquets are not in the repo and there is no neuPrint token, so nothing ran on the pinned data and the preflight numbers are unchecked.
- `gh` is not authenticated; the PR head sha came from the public API.
- Probes ran on brian2 2.11.0 / numpy 2.5.5 with the numpy engine (no compiler), not the locked 2.10.1 / 2.5.3. The selftest still passed ("PASS marking rule, curve fit, design, seeds and the phase A table are as written; eight arms on the toy network run end to end and score").
- Part 4 (synapse-density literature) was not in this brief.

## Scratch locations

- `/tmp/g7`: plan and code copies at 80c5501.
- `/tmp/g7repo`: `git archive 80c5501`.
- `/tmp/g7old`: `flycns/` at ff816c1.
- `/tmp/g7venv`: Python environment.
- `/tmp/g7probe`: `mk.py` (synthetic arms), `probes.py` (P1–P10), `hill.py`, `v7aprobe.py`, `nan_model.py` (3b demo), `p0eq.py` (3a toy equality), and the synthetic arm folders.
- The clone `/workspace/flycns_ro` working tree is clean. The fetch added only the local remote-tracking ref `origin/gen7/model-code`.
