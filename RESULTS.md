# flycns: results note

*Status v0.14, registration generation 6 (phase A: neither the v-and-g reset nor the MN9_R correction makes the male network viable; the runaway loop sits inside the antennal lobe; M1 is specific to the wiring), 18 October 2026. A working note, not a manuscript. Every number is reproducible
from the scripts named beside it; run `./fly` and use the menu. Where the model disagrees with a
measurement, the model is presumed wrong.*

---

## In one paragraph

The complete male Drosophila central nervous system connectome (Janelia FlyEM MaleCNS v1.0,
176,422 neurons in its table, brain and ventral nerve cord; about 170,000 of them have a connection
of five or more synapses and are simulated) was simulated as a signed leaky integrate-and-fire
network using the model and parameters of Shiu et al. 2024, with the loom stimulus measured from
public calcium imaging and split by the fly's behavioural state. After an audit on 11 October 2026,
the model was frozen and every scored check was registered, with its numbers, before one run (run 12).
It was then refrozen once (generation 3: each giant fiber's sound input calibrated on its own
afferents, the synaptic scale set by its registered blind rule, the giant fiber adaptation refit) and
every check re-registered before run 14 (below).
- **Counts.** 29 of 53 checks pass and 6 are unresolved. Of the 19 independent tests, 5 pass, 11 fail
  and 3 are unresolved.
- **Escape.** The giant fiber escape pathway is the calibration circuit: its spike counts and
  response probability were set, not predicted. Its response depends on the specific wiring: a
  shuffle that keeps each cell's class, neuropil and input strength never reproduces it (a control).
- **Hearing.** With each giant fiber calibrated on its own afferents, sound no longer facilitates the
  escape response: at the near-threshold working point it suppresses it, because polysynaptic
  inhibition outweighs the calibrated coupling. With the ear-to-escape contact as the connectome
  annotates it, sound alone fires the giant fiber, which recordings contradict.
- **Feeding and the visual ON pathway** fail for one measured reason: they work by disinhibition,
  which a network with no background activity cannot express. The flight relay layer stays silent
  for a related reason.
- **The robustness battery** finds no scored result that depends on a transmitter call the
  connectome's own classifier is uncertain about.

(Earlier summaries that described the auditory result as "reproducing published physiology" are
superseded by its registered tests.)

---

## 18 October 2026: generation 6, phase A: neither the reset rule nor the MN9_R correction makes the male network viable; in this model, at w 0.5-0.6, the runaway loop sits inside the antennal lobe (runs 33-36)

**The question.** Phase 1b ended in outcome C: on the male data no synaptic scale is both functional (MN9
responds to sugar) and stable (the network does not keep firing after the drive stops). Phase A asked whether
either of the two cheapest changes rescues it: the reset rule (v-only, as now, against resetting v and g), and a
correction for MN9_R's under-reconstructed input (mirror MN9_L's input onto it). It also re-asked phase 1b's
open specificity question with a larger null, and located the runaway loop with targeted edge cuts.
- **Registered** at `3227975` (registration `registration_v5.json`, git `ff816c1`, model hash `dcb44bf09a88`,
  which covers the 12 simulator files plus `fit/gen6_phaseA.py` and `fit/gen6_phaseA_score.py`). The plan
  `docs/gen6_phaseA_DRAFT.md` is pinned by the commit, not hashed. Phase 1b's model hash is `b4e59cc8dcc2`. The 12
  simulator-file hashes recorded in both registrations are identical, so the simulator is unchanged; a combined
  hash over those 12 alone (`df7e16022378`) is not stored in any registration or stamp and can only be derived
  from them.
- **Run once:** cloud runs 33-36, 23 jobs, 95 arms (`46e7d25`), every arm stamped with the registration.
- **Scored once:** `c1e6e62`. No top-up was named, so none was run.

**Design.** Six cells: c1 (v-only reset, data as is), c2 (v-only, mirror), c3 (v-and-g reset, data), c4
(v-and-g, mirror), plus c2b and c4b (MN9_R input scaled up 15.5x instead of mirrored; reported, never
deciding).
- Each cell runs w_scale 0.4, 0.5, 0.6, 0.8 and 1.0 under sugar and under the blind drive, 10 trials each.
- A cell is **viable** at a w if FUNCTION, FUNCTION-q (MN9 responds in at least half of the trials that do
  not self-sustain), and STABILITY (a), (b) and (c) all pass there.
- B1: if c1 is viable, stop (whatever else is viable); otherwise c2 viable means mirror, c3 reset, c4 both, and
  none means C, each at the smallest viable w. An outcome that adopts the mirror (mirror, both) also needs
  LATERALITY PASS in its cell at its decision w; otherwise it is H (M7).

**The mirror, as run** (`results/gen6_phaseA/preflight.json`): MN9_R's input rises from 364 to 5,651 synapses
(MN9_L's own), 2,805 excitatory and 2,846 inhibitory, spread over 100 same-type partners on the opposite side.
Three partners with no opposite-side match stay on their original target. No cell lost its last connection.

**B1: outcome C. No deciding cell is viable at any w.** Each cell fails the same way: where the network is
quiet, MN9 is silent; where MN9 responds, the network runs away.

| cell | w 0.4 | w 0.5 | w 0.6 | w 0.8 | w 1.0 |
|---|---|---|---|---|---|
| c1 v-only, data | MN9 0; stable | MN9 0; blind 7/10 self-sustained | MN9 1.05 Hz; FUNCTION-q fails (3 of 8); blind 10/10 | MN9 6.75 Hz; 10/10 and 10/10 | MN9 55 Hz; 10/10 and 10/10 |
| c2 v-only, mirror | MN9 0; stable | MN9 0; blind 7/10 | MN9 2.05 Hz; blind 10/10 | MN9 12.3 Hz; 10/10 and 10/10 | MN9 66 Hz; 10/10 and 10/10 |
| c3 v-and-g, data | MN9 0; blind 9/10 | MN9 0; blind 10/10 | MN9 1.25 Hz; blind 10/10 | MN9 12.9 Hz; blind 10/10 | MN9 12.7 Hz; 10/10 and 10/10 |
| c4 v-and-g, mirror | MN9 0; blind 9/10 | MN9 0; blind 10/10 | MN9 1.65 Hz; blind 10/10 | MN9 22.6 Hz; blind 10/10 | MN9 24.4 Hz; 10/10 and 10/10 |

"10/10 and 10/10" means sugar and blind trials both self-sustain. The blind whole-CNS rate (STABILITY (c), bar
1 Hz) fails at every w of 0.6 and up, in every cell.
- **The v-and-g reset lowers the rates at w 0.6 and above** (blind 1.2-2.3 Hz against 2.9-7.0 Hz under v-only)
  **but does not stop the reverberation.** At w 0.4 it raises them (blind 0.47 Hz against 0.014 Hz), and the blind
  drive self-sustains in 9 of 10 trials there, where v-only self-sustains in none.
- **c2b and c4b** behave like c2 and c4 and are also not viable.

**The mirror removes the one-sidedness; it is not the bottleneck.**

| w | 0.6 | 0.8 | 1.0 |
|---|---|---|---|
| c1 median sugar LI | 1.00 | 0.88 | 0.87 |
| c2 median sugar LI | 0.31 | 0.13 | 0.07 |

At w 0.4 and 0.5, MN9 is silent and LI is undefined. LI does not enter viability. M7 makes it decide outcome H
only for an outcome that adopts the mirror, and none does.

**A3: the male MN9 response is specific to the wiring. PASS.** Real wiring: MN9 23.98 Hz (30 trials, Shiu's
settings, as phase 1b's M1). It beats all 100 degree-corrected rewiring draws (null median 0 Hz; null networks
alive, whole-CNS median 1.49 Hz against 0.39 Hz real); the bar was 95 of 100, set in advance. Phase 1b's MS2
(19 of 20) is not re-scored and stays UNRESOLVED as registered; A3 is a separate test of the same question. A3's
bar differs from MS2's and was proposed after MS2 came out; the registration records that (M4).

**A4: in this model, at w 0.5-0.6, the runaway loop lives inside the antennal lobe, and either in-AL cut is
enough.** Baseline: c1 blind;
W* (the w at which it self-sustains in at least 5 of 10) = 0.5, 0.6, 0.8, 1.0. A cut "stops it" at a w in W*
if the cut arm then has no self-sustained trial and passes STABILITY (c).

| arm | synapses removed | stops it at |
|---|---|---|
| cut LH: AL PN outputs to the lateral horn | 413,873 | no w |
| cut LH + MB: also to the mushroom body | 801,529 | no w |
| cut (i): cholinergic AL local-neuron outputs | 588,606 | w 0.5, 0.6 |
| cut (ii): cholinergic AL PN outputs onto AL PNs and LNs | 473,474 | w 0.5, 0.6 |
| drive (b): photoreceptors removed from the blind drive | (drive change) | no w |
| drive (c): also ORNs and HRNs removed (non-olfactory) | (drive change) | no w; it reduces the tail (w 0.5: 1/10; 0.6: 6/10) |

- **Projection cuts do not stop it** at any w: the LH and MB are downstream, not needed for the loop. They do
  lower the rate (at w 1.0, 6.98 Hz baseline; 6.77 Hz with the LH cut; 4.96 Hz with LH + MB).
- **Either in-AL cut ends it at moderate w:** 0 of 10 self-sustained trials and a stable rate at 0.5 and 0.6.
  Neither holds at w 0.8 and above, where something beyond these two excitatory sources sustains it.
- **M9 does not hold** (it asks for the AL + LH share of the tail to be at least twice its share of the
  activity during the drive). "Drive share" here is the share of network spikes during the drive, not of
  sensory input. Under drive (c) the two shares are about equal at every scorable w (0.606 vs 0.607 at w 0.5,
  from a single self-sustained trial; 0.556 vs 0.546 at 0.6; 0.442 vs 0.444 at 0.8; 0.344 vs 0.346 at 1.0). They
  are about equal under the full blind drive too (c1: 0.609 vs 0.601 at 0.5; 0.343 vs 0.343 at 1.0). So the tail
  is distributed across neuropils much as the activity during the drive is; M9 does not locate it further.

**Predictions logged before the run** (`fit/gen6_phaseA.py`, CRITERIA):

| | prediction | confidence | outcome |
|---|---|---|---|
| Q1 | the v-and-g reset alone makes the blind drive stable at some w | moderate | wrong |
| Q2 | the MN9_R correction brings laterality below 0.8 | high | right under readings (a) and (b); undetermined under (c) (below) |
| Q3 | A3 stays UNRESOLVED at 100 draws | moderate | wrong: PASS |
| Q4 | the AL tail persists after both projection cuts | high | right |
| Q5 | no cell is viable; the outcome stays C | moderate | right |
| Q6 | at least one in-AL cut stops it | moderate | right (both do) |

**Q2 depends on how the rule is read**, and the scorer's code is not changed after the fact.
- **(a) Registered code:** c2 median LI below 0.8 at any w. Held at w 0.6, 0.8 and 1.0.
- **(b) M7's wording:** c2 below 0.8 and c1 at least 0.8 at the same w. Also held at 0.6, 0.8 and 1.0
  (`laterality_mirror_only` in `phaseA.json`).
- **(c) Reading (b) at c2's decision w:** undetermined, because B1 = C leaves c2 without a decision w.

The registered verdict, held, stands; (c) has no answer on this data.

**Independent checks.**
- **Blind recompute:** an independent scorer, written from the registered text, recomputed every score.
  - Its own comparison checks 18 fields per cell and w (540 over 6 cells x 5 w), plus viable and decision w per
    cell; all match, as do B1, A3, A4 and Q1, Q3-Q6. Separately, the 480 per-cell values printed in its report
    were compared against `phaseA.json`: 0 differences. (The commit title of `aec0089` says "480/480"; the
    comparison it describes is the 540-field one above.)
  - Its only difference is reading (c) of Q2 above.
  - It logs 28 points where the registered text left it a choice.
  - **Blindness, as far as the record shows:** the scorer was frozen at 09:52 PT (sha256 `eb0a106b…`). The arms
    were public on GitHub from 09:03 PT, before the freeze, so that the scorer was written without looking at
    them rests on the session record, the same caveat as phase 1b. Its FINAL output (18:18 PT) predates its first
    reading of `phaseA.json` (18:22 PT).
- **Reproduction:** not claimed here. An earlier draft of this note said every arm was rerun on Windows; no
  committed record supports that, so the line was removed.

**What phase A does not show.**
- **No electrical synapses in the AL.** The connectome annotates chemical synapses only: FlyWire and the
  hemibrain state that electrical synapses could not be detected; the MaleCNS paper does not mention them; Shiu
  et al. 2024 ignore them for that reason. The model's only electrical coupling is four hand-declared contacts in
  the giant-fibre circuit (`flycns/graph.py`, `ELECTRICAL_SYNAPSES`), none in the AL.
  - In the fly, excitatory AL local neurons depolarise PNs largely through electrical coupling (Yaksi & Wilson
    2010, Fig. 4; PN-PN sister coupling is also electrical, Fig. 6).
  - This model has no electrical path in the AL, and every cholinergic LN output it carries is chemical.
  - So cut (i) shows what sustains the loop **in this model**: chemical output that, in the fly, is mostly not
    how these cells excite PNs. It is a finding about the model's structure, not about fly biology.
- **The cell-type lists** behind the cuts come from the public MaleCNS Cell Type Explorer (reiserlab
  `celltype-explorer-drosophila-male-cns` @ `789cc6c`, `types.html` sha256 `3213642…`): ALPN 180 types (682
  cells), ALLN 79 (399), Kenyon_Cell 15 (4,064). Two earlier extractions were wrong: the first read truncated
  names from the card text and skipped quoted links; the second (177 / 76 / 14) skipped 469 cards without a
  name link. Both were corrected before registering, and the final list was checked against an independent
  extraction.
- **A4 runs under the v-only reset only.** Since no reset was adopted, it describes the current model.

**Next.** Outcome C points to the synapse model (`docs/gen7_synapse_model_DRAFT.md` on branch `gen7/synapse-model-draft`, not registered).
- **The plan:** current against conductance-based synapses, each with and without short-term depression.
- **Prior evidence:** in a published whole-brain spiking model, conductance-based synapses alone did not stop
  runaway activity; short-term depression with recovery slower than 125 ms cut how often it occurred to 50% or
  less, but did not eliminate it (Huang et al. 2018, *Front. Neuroinform.*, doi 10.3389/fninf.2018.00099).
- **Also planned:** sign the `"unclear"`-transmitter cells from their per-cell prediction at the freeze. Across
  the CNS this re-signs 716 cells and adds 253,733 synapses (about 0.3% of the signed graph). In the AL, 477
  cells lose their outputs to the drop (235,340 AL -> AL synapses); the fix restores 58,065 of those (about a
  quarter), and AL -> AL inhibition rises 12%.

---

## 18 October 2026: generation 5, phase 1b: w_scale settles the male zero; no synaptic scale is both functional and stable (runs 29-32)

**The question.** Phase 1 showed that w_scale 0.4, the value the blind rule picked for quietness, silences
the only circuit with ground truth (sugar -> MN9) on the female brain. Phase 1b asked three things on the
male data: is w_scale the one setting that silences MN9 there too; is the male MN9 response (M1) specific to
the real wiring; and is there any synaptic scale at which the male network responds to sugar without running
away? Registered at `6e50cba` (criteria `1710398`, model `b4e59cc8dcc2`), run once (cloud runs 29-32, 13 jobs,
50 arms), scored once (`e38e5d4`). The generation-6 decision rule (`docs/gen6_rule.md`) and its amendments
(`docs/gen6_rule_v2.md`, `d808f5b`) were committed before scoring. The result branches existed 12 to 67
minutes before the amendments were committed; that the amendments were written without reading results rests
on the session record, which git cannot show. An independent reviewer recomputed every number below from the
raw arm files and found no differences.

**Registered checks** (`results/shiu2024_phase1b/phase1b.json`):

| check | result | 95% interval | verdict |
|---|---|---|---|
| ML0: M1 replicated (male, Shiu's settings) | MN9 22.8 Hz | 21.0 to 24.7 | PASS |
| ML4: w_scale 0.4 alone | MN9 0 Hz, 0 of 30 trials | 0 to 0 | PASS (silent) |
| every other single setting (reset, stimulation, adaptation, Euler, amines dropped) | 13.8 / 24.1 / 11.9 / 24.7 / 21.6 Hz | each above 0.5 | PASS (5 of 5) |
| MS1: beats the weight-permutation null | the null network is silent (0.010 vs 1.237 Hz) | | UNRESOLVED |
| MS2: beats the degree-corrected rewiring null | beats 19 of 20 draws; one draw 28.0 Hz | | UNRESOLVED |

**w_scale alone accounts for the male MN9 zero, as on the female.** Specificity is undecided: the weight
permutation silences the whole network and so cannot test anything, and against the rewiring null the real
wiring is above the null median but not above every draw. MN9 does not track network activity in either the
real or the null networks (equally active null draws give 0 Hz), so this is a genuine open question, not a
near pass. It stays UNRESOLVED; the registered bar is not lowered after the fact.

**The male MN9 response is one cell, and the dataset explains why.** Laterality (|L - R| / (L + R)) is 1.0 in
all 30 trials: cell 10331 (left) fires 45.6 Hz, cell 16949 (right) 0.07 Hz, under a symmetric drive (17 + 17
LB3b/c cells). On FlyWire both cells fire (laterality 0.14 to 0.18). The MaleCNS Cell Type Explorer lists
6,358 input synapses for MN9_L and 633 for MN9_R; the MaleCNS paper notes segmentation issues for some motor
neurons. This was written into the amendments before scoring. A reconstruction artefact is the likely cause;
it is not verified.

**No synaptic scale is both functional and stable** (`results/gen6_screen/screen_v2.json`,
`fit/gen6_screen_v2.py`; flycns settings, male data):

| w_scale | MN9 under sugar (FUNCTION) | sugar trials self-sustained | blind-drive trials self-sustained | blind-drive rate, Hz |
|---|---|---|---|---|
| 0.4 | 0 Hz (fail) | 0 of 10 | 1 of 10 | 0.01 to 0.32 |
| 0.5 | 0.05 Hz (fail) | 0 of 10 | 8 of 10 | 1.15 to 2.27 |
| 0.6 | 1.45 Hz, 0.60 to 2.45 (pass) | 3 of 10 | 10 of 10 | 2.66 to 3.20 |
| 0.8 | 7.45 Hz (pass) | 10 of 10 | 10 of 10 | 4.71 to 4.98 |
| 1.0 | 45.6 Hz (pass) | 10 of 10 | 10 of 10 | 6.73 to 6.96 |

"Self-sustained": activity in the last 250 ms after the drive stops is at least 10% of the rate during it.
MN9 responds only where the network also reverberates: at 0.6 the pass comes from the three runaway trials.
The current default, 0.4, is itself not stable (one blind-drive trial self-sustains, not borderline). The
reverberation is not concentrated in one region (the largest share is the right antennal lobe, 16%), so the
rule's outcome is **C**: no scale works, and the next step is the reset rule, then, if needed, a different
synapse model. Shiu's own settings on the male data run away too (from 0.4 under the blind drive); FlyWire
never self-sustains up to 1.0 under either drive. **The instability belongs to the male data, not to flycns's
options.**

**Two observations, registered as hypotheses for the next phase, not claims:**
- The blind-drive reverberation sits in the antennal lobe and lateral horn (about 55% of the tail) although
  only 17% of the drive enters the antennal lobe. The lateral horn is fed forward from the antennal lobe
  (excitatory and inhibitory projection neurons), with no known excitatory return, so the likelier reading is
  activity that sustains itself inside the antennal lobe and is relayed on. Under sugar the tail sits in the
  ventral nerve cord (89%).
- 38% of the blind drive is photoreceptors, which are histaminergic and inhibitory: the quietness rule that
  chose 0.4 in generation 3 was scored under a drive more than a third inhibitory.

**Predictions logged before the run:** w_scale 0.4 silences male MN9 (correct); the v-only reset runs away
above 100 Hz (wrong: MN9 13.8 Hz, though the whole-CNS rate rises about six-fold); M1 beats both nulls
(unresolved); Outcome B in the nerve cord (wrong: outcome C); laterality at least 0.8 (correct, 1.0).

**Next** (`docs/gen6_phaseA_DRAFT.md`): the reset rule crossed with an MN9_R input correction, scored on
stability; a 100-draw rewiring null with its bar set in advance; a non-olfactory blind drive; and a FUNCTION
criterion that requires MN9 to respond without the network running away.

---

## 12 October 2026: generation 5, phase 1: set to Shiu et al.'s choices, flycns reproduces their model (run 22)

**The question.** flycns finds no sugar -> MN9 response in the male CNS (check F3), where Shiu et al. 2024's
model of the female brain finds a strong one. Is that the simulator or the wiring? Phase 1 ran a positive
control: the flycns simulator, set to Shiu et al.'s choices, on their own FlyWire v630 data (A1), then the
male CNS under the same choices (M1). Everything was registered before it ran: the pre-registration
(`results/shiu2024_a0/`), an addendum (`results/shiu2024_phase1_addendum/`: exact integration for A1; M1
at a connection floor of 5, the MaleCNS data's floor), two point-by-point checks against the authors'
archived output (S4b, S5b) and the phase-1 registration (`results/shiu2024_phase1/registration_v5.json`,
commit `65ce101`). Shiu et al.'s own code was first run here on their data (A0): it reproduces its
published output (67.10 vs 67.03 Hz).

**Generation 5 changes no default.** The options (`flycns.model.SimOptions`, `load_graph(amines=...)`) are
off unless phase 1 sets them. The identity check proves it: every job of the rerun, reduced to a few
trials and fingerprinted on the generation-4 and generation-5 code (cloud runs 20 and 21), gave identical
networks, neuron states, spikes and exit codes in 55 of 55 jobs (7,591 fingerprints).

**A1 passes: on all seven counted checks** (`results/shiu2024_phase1/phase1.json`):

| check | result | 95% interval | band |
|---|---|---|---|
| S1 contralateral MN9, sugar 100 Hz | 68.33 Hz vs published 67.03 (+1.30) | -1.67 to +4.20 | +/-6.7 |
| S2 fires in >= 29 of 30 trials | 30 of 30 | | |
| S3 contra - ipsi; ipsi vs published | +17.9; +1.77 | 15.8 to 19.9; -0.57 to +4.07 | > 0; +/-4.86 |
| S4b dose curve, 50/100/150/200 Hz | 17.5/68.3/82.6/94.5 vs 19.4/65.7/83.7/93.2 | every point inside | +/-6.7 each |
| S5 bitter suppression; minus rho | 63.9 Hz; 0.955 | 62.0 to 65.9; 0.944 to 0.963 | > 0 |
| S5b bitter curve, 0-200 Hz (8 points) | every point within 1.9 Hz of the published | every point inside | +/-6.7 each |
| S6 shuffled weights reaching 51.4 Hz | 0 of 100 | | <= 5 |

S4 (MN9 at 100 Hz as a share of the maximum, band 0.7-0.9) does not count: the reference's own output is
UNRESOLVED on it (0.705), and so is A1 (0.723, 0.700 to 0.745; under other bootstrap seeds it passes about
three times in four). How "A1 passes" is defined (only checks the reference itself passes count; three
outcomes; one extension if unresolved) was chosen after A0 and after S4's behaviour on the reference was
known, but before any A1 run; read plainly, the pre-registration would have made A1 UNRESOLVED (through S4)
and called for its extension, not FAILED it. No extension and no reference shuffle run were needed.

An independent review re-derived every check from the arm files with its own code, and tested the A1
configuration against Shiu et al.'s `model.py` directly on a 400-neuron network: identical spikes (3,706
of 3,706 under Poisson drive, 3,255 of 3,255 after the same weight permutation); switching flycns to
Euler, or to its own reset, breaks the match.

**M1: the male CNS drives MN9 under the same choices.** LB3b and LB3c at 100 Hz, connection floor 5, amines
excitatory: MN9 21.5 Hz (19.8 to 23.2), every one of 30 trials. The registered rule therefore reads: **the
male MN9 zero is caused by flycns's settings, not by the wiring.** Caveats: the response is one cell
(42.8 Hz; the other MN9 0.13 Hz); at w_scale 1.0 the male network is broadly active (about 7,600 neurons
per trial, 4.4%, against 358 on FlyWire) and no specificity control for M1 was registered, so "responds"
does not yet show a sugar-specific drive; and M1 differs from flycns's own F3 run in settings the ladder
does not test (amines, electrical synapses, a 1 s rather than a 200 ms pulse).

**The ladder (female brain, reported, not scored):** from A1, one setting at a time back to flycns's value,
sugar 100 Hz, contralateral MN9:

| switched to flycns's value | MN9 (Hz) | vs A1 |
|---|---|---|
| none (A1) | 68.3 | |
| synaptic scale 0.4 (L4) | **0.0** | -68.3 (0 of 30 trials fire) |
| all of them (L6) | **0.0** | -68.3 |
| motor adaptation (L5) | 37.9 | -30.4 |
| connection floor 5 (L3) | 61.8 | -6.5 |
| stimulus as source cells (L2) | 67.7 | -0.6 |
| Euler integration (Le) | 66.9 | -1.4 |
| reset of v only, g carries over (L1) | 231.8 | +163.5 |

The synaptic scale alone silences MN9 on the female brain. That it is what silences it on the male brain
is the obvious next test (the same ladder on MaleCNS); phase 1 does not show it. The scale is not a
measured value: 0.4 was chosen by a benchmark-blind rule because the male network runs away near 0.5
(docs/CALIBRATION.md).

---

## 12 October 2026: generation 4, a hygiene refreeze; every number of run 14 reproduced (run 18)

**What changed** (docs/CALIBRATION.md, "Generation 4, phase 0"): no parameter. The input data were re-pinned
without the legacy `sign` column (the fetch's own sign table, which the model never read; one
transmitter-to-sign table remains, `flycns/graph.py` SIGN_MAP); `flycns/integrity.py` joined the hashed
model files; two pieces of frozen text were corrected (a rationale string in `flycns/graph.py`, which is
printed into `results/gf_escape/provenance.md`, and the `flycns/registry.py` docstring); the suite table
now lists per-draw values. The model was frozen at `7851c7c`; 20 `registration_v4.json` files were
committed at `bd631a2` before any result. Run 18 ran at `bd631a2`: the same 55 run jobs as run 14, plus
the plan, data and transmitter jobs (58 in all; run 14's "56" counted its output branches).

**Result: every number of generation 3 reproduces.** Compared file by file with run 14: all 88 JSON
result files are numerically identical (only provenance, registration stamps and run times differ); the six
grid tables differ only in their wall-time column; the HDF5 exports are byte-identical; logs and summaries
differ only in times, commits and the re-pinned data hashes, plus the one corrected line of
`results/gf_escape/provenance.md`; all 61 rows of the suite table give the same verdict and role. 29 of
53 checks pass, 6 unresolved; independent 5 of 19. Every collected file is the one its cloud job wrote,
except `results/SUITE.md`, which was regenerated from all of them after collection
(`benchmarks/summarize.py`; rerunning it reproduces the committed file). An independent check confirmed
each of these points from the files themselves. Every scored report says `registration.matches: true`; 111 of 111 result files carry the stamp
of `bd631a2`. (The robustness battery's reports are perturbations by design and are not registered
results, as before.)

**One plumbing fault, no data lost.** The core job ran 109 minutes and was marked failed at its last
step: its own push of the results branch failed, and the script discarded git's message, so the cause
is still unknown. The workflow's backup step then pushed the results commit with the console log added
on top; the results are identical. The script now shows git's message, retries once, and checks with
a dry-run push, before any long run, that the remote would accept results from this checkout (sign-in and
write access; refusals the server makes only on receipt cannot be seen in advance).

---

## 12 October 2026: generation 3, the model refrozen and every test re-registered (run 14)

**What changed, and why** (docs/CALIBRATION.md, "Refrozen 11 October 2026"):
- **Each giant fiber's sound input is calibrated on its own afferents.** The model couples 21 JO-B1
  afferents to the left giant fiber and 6 to the right (by inferred soma side; EM cannot see gap
  junctions). One shared spikelet gave about 4.3
  and 1.5 mV in steady state (run 12 measured peaks of 3.65 and 0.73 mV against a 3 mV target). Now
  `fit/check_jon_calibration.py` measures, with only the coupling acting, plateaus of 2.72 and 2.78 mV
  against the 2.76 mV a 60 ms pulse can reach: PASS on both.
- **w_scale 0.3 → 0.4**, the value the registered benchmark-blind rule selects; the rule, rerun at the
  new code, gives the same grid and the same answer. This closes audit gap 6. It is not a measured
  value: a measured per-synapse PSP (ORN → PN) is about 12 times the model's (CALIBRATION.md).
- **GF adaptation 10 → 45 mV**, refit by its unchanged rule. The strongest-gain quartile sits exactly
  at its limit of 2.0 spikes.
- **Registration generation 3.** The model was frozen at `a94769d`; 20 `registration_v3.json` files,
  each naming the `registration.json` it supersedes, were committed at `47eb98e` before any result.
  The version 2 files are unchanged. Run 14 (56 jobs) ran at `47eb98e`: every scored report says
  `registration.matches: true`, and 111 of 111 result files carry its stamp.

**Headline: 29 of 53 checks pass, 6 unresolved, all scored as registered. Independent: 5 of 19 pass,
11 fail, 3 unresolved.**

| role | run 12 (0.3) | run 14 (generation 3) |
|---|---|---|
| independent | 6 / 19 (4 unresolved) | **5 / 19** (3 unresolved) |
| calibrated | 5 / 7 (1 unresolved) | 6 / 7 (1 unresolved) |
| control | 12 / 14 (2 unresolved) | 12 / 14 (2 unresolved) |
| robustness | 2 / 4 (1 unresolved) | 0 / 4 |
| structural | 3 / 5 | 3 / 5 |
| construction | 4 / 4 | 3 / 4 |

**Verdicts that changed** (everything else kept its verdict):

| check | role | run 12 | run 14 |
|---|---|---|---|
| A2R_facilitation | construction | PASS +0.333 (+0.216 to +0.438) | **FAIL −0.133 (−0.237 to −0.026)** |
| RA2 facilitation at every near-threshold gain | robustness | PASS | FAIL (only 2 gains qualify as near threshold, 3 required; at both, 0.4 and 0.5, the difference spans 0: UNRESOLVED) |
| G5 SNpp16 reliable at k* | independent | PASS (4 of 5 draws) | **FAIL (1 of 5 draws)** |
| L2 b1 spikes per wingbeat | independent | UNRESOLVED (3 of 5) | FAIL (0 of 5) |
| R1 flight survives transmitter uncertainty | robustness | PASS | FAIL |
| R3 flight replicates with fresh draws | robustness | UNRESOLVED | FAIL |
| L1a DVMn 2 to 12 Hz | calibrated | FAIL | UNRESOLVED (2 of 5) |
| GF response probability 0.5 to 1 | calibrated | UNRESOLVED | PASS 0.80 (0.65 to 0.90) |

**What the registered tests found.**
- **Sound now suppresses the escape response at the working point (A2R FAIL).** Loom alone fires the
  giant fiber on 0.30 of 120 trials; loom plus sound on 0.17. The working point is loom gain 0.6,
  chosen by the registered rule on disjoint calibration seeds.
  - The cause is measured, not inferred: with the whole network on, sound alone gives each giant fiber
    an early bump (+2.5 and +1.5 mV) that turns into deep inhibition by the end of the pulse (−9.6 and
    −20.8 mV; `results/checks/jon_calibration.json`, network arm). Polysynaptic inhibition, not the
    calibrated coupling, dominates the giant fiber under sound.
  - This reverses a correction on the record ("sound suppresses" was withdrawn in September when 120
    trials per arm showed facilitation). Both were outcomes of the model as it then stood. Which of the
    three changes removed run 12's facilitation is not isolated: the calibration defect (the left giant
    fiber got about 4.3 mV), w_scale 0.3 and the 10 mV adaptation all changed together. The one arm
    that bears on it, the 40-trial w_scale 0.30 battery arm under the new calibration and 45 mV, gives
    0.25 → 0.25.
  - A2R2 (beyond summation): FAIL, residual −0.69 (−0.78 to −0.54). Adding each fiber's sound-alone
    peak (1.51 and 2.46 mV) to its loom-alone peak predicts 0.86; the model gives 0.17.
  - The registered sweep (`a2_robustness`, 100 trials per arm, declared model) shows the suppression
    grows with loom strength and is resolved wherever the loom is not near threshold: −0.14 (−0.25 to
    −0.02) at gain 0.6, −0.22 (−0.34 to −0.09) at 0.7, −0.39 (−0.50 to −0.26) at 0.8. At the two
    near-threshold gains it is unresolved (+0.04 at 0.4, −0.03 at 0.5).
  - The 40-trial battery arms are too small to resolve it and vary in sign: 0.25 → 0.25 at w_scale
    0.30, 0.125 → 0.15 at 0.35, 0.275 → 0.15 at 0.40 (canonical), 0.075 → 0.10 at 0.45, 0.20 → 0.125
    and 0.05 → 0.075 for seeds 1 and 2.
- **The ear-to-escape contact as EM annotates it still fires the giant fiber on sound alone (C1
  FAIL),** 40 of 40 sound-alone trials (95% interval 0.91 to 1.0); its facilitation part passes, +0.89
  (+0.82 to +0.94) over 120 trials per arm. The sign-inverted contact suppresses (C2 PASS, control).
- **The SNpp16 upstroke result weakens.** Its registered rule now picks a working point of 3 cells
  (k* = 3; it was 5). There it is still selective (G3 PASS) and wiring-specific (G4, control), but it
  reaches the 2 to 12 Hz band in only 1 of 5 draws (G5 FAIL). 5 cells would be in band in 5 of 5 draws,
  but the registered rule picks the smallest size whose mean over the draws is in band (2.5 Hz at 3). R1 fails because its registered size, 7 cells, now
  overshoots the band on the unflipped graph too (1 of 5 draws in band, flipped or not; selectivity
  holds under the flip), so it no longer tests transmitter uncertainty; it does not show that the result
  depends on a transmitter call. R3 (fresh draws) fails. G5 held at 0.3; it does not at 0.4.
- **Unchanged:** escape latency 36.7 ms (32.3 to 41.4; independent PASS), the escape wiring control
  (real 0.80 against a null median of 0.10 over 20 draws), song P3, taste (F3, F4 still fail: no MN9
  response at 100 Hz), the stricter nulls, and the compiled and pure-Python engines (4,340 identical
  spikes).

**Weight-scale battery** (core suite, 40 trials, run under overrides, so not registered):

| w_scale | checks | GF P(response) | spikes per response | A2 loom → loom + sound |
|---|---|---|---|---|
| 0.30 | 13/14 | 0.625 (UNRESOLVED) | 1.04 | 0.25 → 0.25 |
| 0.35 | 14/14 | 0.70 | 1.30 | 0.125 → 0.15 |
| **0.40** (declared, canonical run) | 14/14 | 0.80 | 1.59 | 0.275 → 0.15 |
| 0.45 | 14/15 | 0.875 | 2.09 (UNRESOLVED) | 0.075 → 0.10 |

The adaptation was fitted at 0.4, so the escape numbers drift either side of it, as expected. Under
the benchmarks' own drive the network did not run away even at 0.45 (whole-CNS rate 0.008 Hz).

## 11 October 2026, night: the model frozen, every test registered, one run (audit phases 4 and 5, run 12)

**Registered before the run.** The model was frozen at commit `4c39a8f`. All 20 version-2
registrations were then written (`FLYCNS_REGISTER_ONLY=1`) and committed (`b7eba83`) before any
result existed under this model. Each registration records:
- the criteria, with their numbers;
- the content hash of every model file and of the benchmark's own script;
- the declared values;
- the package versions.

Run 12 (57 jobs) ran at `b7eba83`. Every scored report says `registration.matches: true`. A run
refuses to score if:
- anything registered has changed;
- the registration is not committed;
- the clone is shallow;
- a check is scored with a band other than its registered one.

**Headline: 32 of 53 checks pass, 8 unresolved, all scored as registered. Independent: 6 of 19 pass, 9 fail, 4 unresolved.**

| role | run 10 | run 12 |
|---|---|---|
| independent | 6 / 18 | **6 / 19** (4 unresolved) |
| calibrated | 5 / 7 | 5 / 7 (1 unresolved) |
| control | 11 / 13 | 12 / 14 (2 unresolved) |
| robustness | 2 / 4 | 2 / 4 (1 unresolved) |
| structural | 3 / 5 | 3 / 5 |
| construction | 4 / 4 | 4 / 4 |

The counts changed because A2R2 and C1 were added (independent), C2 was added (control), and flight L6
is now reported rather than scored (it was identical to L5 as coded).

**Every number that did not depend on a phase-4 change is identical to run 10.** That covers escape,
song, taste, flight, the null distributions and the stricter null. The A2 family moved, as intended:
its calibration and scoring arms now use disjoint seeds.

**What the new registered tests found.**
- **A2R: sound facilitates the giant fiber** at the near-threshold working point (construction).
  - The response probability rises from 0.175 to 0.508. The difference is +0.333, with 95% interval
    +0.216 to +0.438; it was +0.358 when the arms shared a seed.
  - The working point is still a loom gain of 0.8, now chosen on calibration trials disjoint from the
    scored ones.
- **A2R2: none of that facilitation goes beyond summation. FAIL** (independent).
  - Adding each giant fiber's own measured sound potential to its loom-alone peak predicts a response
    on every trial (1.0). The model responds on 0.508.
  - The residual is −0.49 (−0.58 to −0.39). Summing two peaks that do not coincide in time
    over-predicts summation, so this baseline is generous.
  - Because that baseline over-predicts, the shortfall does not show that the facilitation is
    sub-additive. It shows only that there is no evidence of facilitation beyond summation.
- **The two giant fibers do not receive the same sound potential.**
  - The declared calibration aims at 3 mV per giant fiber. The measured peaks are 3.65 mV on one side
    and 0.73 mV on the other, because the JON afferents are unequally sided and one spikelet value
    serves both sides.
  - The audit flagged this asymmetry (MODEL_SPEC). It is a defect of the frozen model. Fixing it means
    calibrating each giant fiber on its own afferents, which needs a new registration.
- **C1: with the JON→GF contact as EM annotates it, sound alone fires the giant fiber on every trial.**
  FAIL (independent).
  - Sound alone fires it on 40 of 40 trials (95% interval 0.91 to 1.0), against the literature's
    "sound alone is subthreshold" (Pézier et al. 2016).
  - The 679 chemical synapses, at the declared synaptic scale, are far stronger than any reported sound
    response. That part was known before registration and is recorded as not blind.
  - The calibrated 3 mV coupling is, if anything, the weaker and more realistic representation.
- **C2: the sign-inverted contact suppresses rather than facilitates.** PASS (control): −0.133
  (−0.206 to −0.075).
- **RA2: facilitation at every near-threshold gain holds with independent seeds.** PASS (robustness):
  +0.13 to +0.32 across loom gains 0.4 to 0.8, every interval above 0.

**Robustness arms added in phase 4** (battery, 14 checks each, run under overrides, so not registered):

| variant | result |
|---|---|
| half time step (0.05 ms) | 13/14, same as canonical. TTMn lag 0.85 ms (0.90 at 0.1 ms; 0.8 ms delay plus one step, as expected); GF response probability identical (0.575); spikes per response 1.57 (1.46); A2 facilitation holds |
| nerve-cord glutamate excitatory | 13/14, bit-identical to canonical. None of the 83,382 flipped connections carries activity in these protocols, so the variant does not test them; it shows only that nothing scored here runs through nerve-cord glutamate |
| JON→GF as EM annotates it | 12/14: sound alone fires the giant fiber (A1 fails), and the declared electrical pairs no longer carry the drive (A3 fails, by definition) |

**w_scale, re-selected blind** (`fit/select_wscale.py`; registered and committed in
`results/select_wscale/`). This run reproduced the selection exactly:
- the network is quiet from 0.15 to 0.4 (0.007 Hz at 0.3);
- it runs away between 0.4 and 0.5 (2.5 Hz);
- the registered rule picks 0.4.

0.3 is kept. That departs from the registered rule, and audit gap 6 stays open (docs/CALIBRATION.md).

---

## 11 October 2026, evening: audit phase 3, uncertainty on every check (run 10)

**What changed.** Every scored check now carries a 95% interval, a per-draw score over seeds, or a
null percentile (`flycns/stats.py`). It has three outcomes:
- **PASS:** the whole interval lies inside the band.
- **FAIL:** the interval lies wholly outside.
- **UNRESOLVED:** the interval crosses an edge. UNRESOLVED does not count as a pass.

Seed replicates are scored draw by draw, never on their mean. Checks that cannot fail as designed
are UNRESOLVED, with the reason stated. A new null, *degree-corrected*, permutes connection targets
only within the target's class, neuropil, the connection's sign and its size. It keeps convergence,
so it can fire; each null circuit is compared with 20 draws of it.

**Run 10** (51 jobs at `a4eef18`). Every number the earlier reports held is identical to run 8. Only
the verdicts changed.

**Headline: 31 of 51 checks pass, 8 unresolved** (36 of 48 before, with three null checks added).

| role | run 8 | run 10 |
|---|---|---|
| independent | 9 / 18 | **6 / 18** (4 unresolved) |
| calibrated | 7 / 7 | 5 / 7 (1 unresolved) |
| robustness | 3 / 4 | 2 / 4 (1 unresolved) |
| control | 10 / 10 | 11 / 13 (2 unresolved) |
| structural | 3 / 5 | 3 / 5 |
| construction | 4 / 4 | 4 / 4 |

**Six earlier passes no longer pass:**
- **Escape response probability** (calibrated) is UNRESOLVED. The point is 0.575, but its interval,
  0.42 to 0.72, crosses the 0.5 floor.
- **Flight L1a** (calibrated) FAILS. DVMn is in the 2–12 Hz band in only 1 of the 5 recruitment
  seeds; the mean of the five sat in the band.
- **Flight L2** (independent) is UNRESOLVED: b1 is in band in 3 of 5 seeds; 4 are needed.
- **Song P1 and P2** (independent) are UNRESOLVED. pMP2 passes its band, but "pMP2 above DNp13"
  cannot fail: DNp13 fires in no pulse of any arm.
- **SNpp16 R3** (robustness) is UNRESOLVED: k = 5 and k = 6 are each in band in 3 of 5 draws.

**A null that can fire.** The degree-corrected null keeps the network active (whole-CNS rate within a
factor of about 1 of the real network for escape), unlike the global null (2e-6 Hz).

| circuit | real | null median (max of 20) | percentile | null active | verdict |
|---|---|---|---|---|---|
| escape: GF response probability | 0.575 | 0.05 (0.30) | 1.00 | yes, 0.0043 vs 0.0039 Hz | **PASS** |
| song: pMP2 spikes per pulse | 7.73 | 3.80 (11.1) | 0.88 | no, 0.0008 vs 0.0118 Hz | UNRESOLVED |
| JON → GF chemical: GF depolarisation, mV | 3.64 | 2.08 (3.96) | 0.95 | yes, 0.0012 vs 0.0039 Hz | UNRESOLVED |

- **Escape: wiring-specific.** With the whole network as active as the real one, no null draw drives
  the giant fiber as often as the real wiring.
- **Song: not tested.** The real pMP2 response lies inside the null spread. That null is not active,
  so the check cannot test wiring.
- **JON → GF: unresolved.** One null draw exceeds the real depolarisation.

**Robustness battery under the new verdicts** (12 perturbations of escape, auditory and feeding; 14
checks each):
- **Independent check:** the one independent check the battery scores (giant fiber latency) passes
  under all 12 perturbations.
- **Calibrated checks:** 1 or 2 of the 6 are unresolved under most perturbations (response
  probability, as in the canonical run). Under the ±0.05 weight-scale changes, one calibrated check
  fails outright.
- **Superclass null:** auditory A4 fails, as before.

**Also corrected by the audit, not by this run.**
- **R1 is not vacuous.** The audit said the targeted sign flip touches no connection on the SNpp16 path.
  On the path as the robustness script defines it (driven cells, readouts and the campaniform relay
  layer: 2,120 cells, 50,286 connections), it flips 87 connections; 16 of them lie among the driven
  and readout cells alone. R1 passes.
- **The global null's "silent" checks stay as registered**, but their records note that the global
  and superclass nulls are almost silent, so the degree-corrected comparison is the informative one.

---

## 11 October 2026, later: audit phases 1 and 2 (run 8)

**What changed.** The guards and tests the audit asked for (README, "Integrity"; full list in the
pull request):
- registrations are guarded;
- every pinned table is rehashed from its bytes before a registered run;
- menu 51 refuses settings overrides;
- the toy suite compares 2,224 numbers with a committed golden file;
- 18 new unit tests (34 in all).

Roles changed for six checks. A2R facilitation is now *construction*. Five checks that are graph
arithmetic with no simulation are now *structural*: gustatory S1-S3, sugar laterality L1 and
feeding-by-modality F2. No model equation, parameter, stimulus or criterion changed.

**Not closed by this change** (found by an independent check before merge; scheduled for phases 3
and 5):
- A registered test whose `criteria.json` is deleted in a commit can still register afresh.
- Pass thresholds still sit in the scoring code, outside the registered text, so editing a
  threshold is not refused.
- `FLYCNS_ALLOW_DIRTY` waives the guards and is not flagged in the summary.
- Cloud runs use a shallow checkout, so the registration-history check is skipped there.
- Unregistered runs still trust the writable fingerprint cache.

**Run 8.** All 48 cloud jobs reran at commit `d72fe77`, and all 93 result files carry its stamp.
- **Unchanged.** The 70 result JSON files hold 5,643 numbers and verdicts. All but 12 are
  identical to run 6, to the last digit; the 12 are the feeding mechanism, changed as intended.
  36 of 48 checks pass. By role, independent checks pass 9 of 18 and structural 3 of 5. These were
  13 of 24 independent before the relabel; no outcome changed.
- **Changed: the feeding mechanism, as intended.** Its path products are no longer NaN. They now
  come from the graph the model simulates, with histamine signed and the weight floor applied:

  | hop | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|
  | signed taste-to-MN9 influence | -0.0035 | +0.0032 | +0.0065 | +0.0025 |

  That is inhibitory at two hops and excitatory at three to five: the disinhibition the note has
  claimed. These values, and MN9's input balance (net -83 synapses, -1.4%; afferents onto its
  inhibitory inputs 3 times more than onto its excitatory ones, ratio 0.33), equal the September
  file exactly. Only run 6, which read the stale column, had NaN and slightly different balances.
- **New: both engines on the real connectome.** The compiled and pure-Python engines gave
  identical spikes on 10 looms: 2,547 spikes each, exact equality (`fit/check_engines.py`,
  x86-64 Windows). Until now this had been shown only on the toy and on synthetic networks.
- **Pinned: the transmitter table.** `edges_nt.parquet` (6,287,789 rows, read by the registered
  flight robustness check R1) is now in `data/MANIFEST.json`. The other three tables re-fetched
  byte-identical.

---

## 11 October 2026: every pending result rerun on the real connectome

**How.** The audit marked a list of results "rerun pending". Every one of them was rerun on
GitHub's Windows machines (`.github/workflows/rerun.yml`), one machine per run. So were the seven
benchmarks never rerun under integrity stamping: pc1 song, DNp13 control, feeding by modality,
gustatory map, sugar laterality, SNpp16 and SNpp16 graded. The final run (run 5) reran everything
at one commit.
- **Data.** Four files are pinned in `data/MANIFEST.json`:
  - the connectome from neuPrint: neurons (176,422) and edges (6,287,789);
  - each neuron's neuropil membership, which defines the anatomical SEZ: 174,802 neurons;
  - since run 8, the per-synapse transmitter table (`edges_nt.parquet`) used by the targeted sign flip.

  Every rerun (runs 2 to 5) fetched them again, and setup refuses data that differ from the pin.
  Every run passed that check.
- **Code.** Every result file in `results/` (93 files) was produced at commit `d72fe77` on
  committed code, by run 8 of `rerun.yml`, and carries its stamp. Results that can't carry a stamp
  inside them (CSV, HDF5) have it beside them. The only exception is the Turner 2022 extraction,
  which is a model input hashed into every report. `results/SUITE.md` keeps the inventory. Runs 5,
  6 and 8 gave identical reports (run 8 differs only in the corrected feeding mechanism).
- **Engine.** Every stamped simulation used the compiled engine, on Windows. Wrapper and
  static-analysis scripts record "not used".

**Result: every report in `results/SUITE.md` now carries a clean stamp. None is stale, unstamped,
dirty or perturbed.** 36 of 48 scored checks pass under one parameter set; the independent checks
pass 13 of 24 (9 of 18 after the relabel of run 8, above).

The reruns are deterministic. Run 5 reproduced the earlier runs to the last digit in every
benchmark: run 2, and run 3 for the seven benchmarks below. The only exceptions are the readouts
that use the SEZ, which changed as intended (below). The seven
benchmarks rerun for stamping reproduced their earlier pass and fail pattern exactly:
- pc1 song: 4 of 4;
- DNp13: 1 of 2;
- feeding by modality: 1 of 3;
- gustatory map: 1 of 3;
- sugar laterality: 1 of 1;
- SNpp16: 0 of 2;
- SNpp16 graded: 4 of 5, k* = 5.

**Calibration, re-checked under the stationary loom input** (docs/CALIBRATION.md):

| value | before | now | how |
|---|---|---|---|
| PEAK_HZ | 5.0 | **5.0, holds** | GF 1 to 2 spikes per response, P(response) 0.575 |
| GF adaptation | 30 mV | **10 mV** | the fit's own rule (smallest value meeting all four constraints) |
| A2 working point | gain 0.6 | **gain 0.8** | re-derived by the registered rule in the run |

The GF adaptation fit is close at 10 mV: the strongest-quartile check gives 1.95 against a limit
of 2, and 5 mV fails it at 2.3.

**What the reruns found** (old values are those committed before the audit):

| result | before | now |
|---|---|---|
| Escape (calibrated) | quoted as P 0.68, 1.06 spikes, 37 ms; the committed report (a perturbed run) gave 0.65, 1.19, 38.7 ms | P 0.575 (0.42 to 0.71), 1.46 spikes, 39.7 ms; all 8 checks pass |
| A2R, sound facilitates a near-threshold loom (registered) | 0.042 to 0.450, +0.41 | **0.175 to 0.533, +0.358 (95% CI +0.240 to +0.463): PASS** |
| RA2, facilitation across working points (registered) | PASS | **PASS at all five gains**, +0.20 to +0.40 |
| Stricter null, superclass-preserving (registered; first committed run) | not run | **PASS**: escape and pC1 song both silent on it |
| Flight robustness R1, targeted transmitter inversion | PASS, untouched | **PASS, still untouched**: 1.6% of signed weight flipped, yet the k = 7 draws are identical to the unperturbed ones. No uncertain neuron lies on this circuit, so R1 cannot fail here. |
| Flight robustness R2, cord parameters | FAIL (uninformative) | **FAIL, now informative** (below) |
| Flight robustness R3, fresh draws | PASS (reused draws) | **PASS**: k* = 5 again, k = 7 in band in 4 of 5 |
| Flight loop | 4 of 7 | 4 of 7, the same checks |
| Flight sensitivity | DLMn c-f below 2 Hz at every setting | DLMn c-f below 2 Hz at every setting (at most 0.82 Hz, at tau_m 5 ms) |
| Feeding | 4 scored, all pass | 2 scored, both pass; F4 and F5 reported, as the audit decided |
| AstA on Mi1 (reported, never scored) | "Mi1 stays silent" (the peptide never acted) | **the peptide acts**: Mi1 0.0002 to 0.0375 spikes per flash; knockdown returns it to 0.0001 |
| DNp31 and ear-to-wing traces | | structural findings unchanged; under loom drive DNp31 and the wing motor pool stay silent |

**The A2 artefact.** The audit found that the two A2 arms differed in more than sound. In
loom-alone trials the ear afferents loaded the giant fiber; in loom-plus-sound trials they did
not. With that removed, the registered test gives +0.358, and its interval lies well above zero.
The registered result stands.

The two runs cannot be compared directly: the input, the adaptation and the working point also
changed between them. At the original gain of 0.6, however, the rerun sweep gives +0.40 against
the original +0.408. Whatever the artefact contributed, the effect did not depend on it.

**R2 is now a real failure.** With the wing afferents excluded from the relay layer, the selectivity
of SNpp16 for the upstroke muscles fails at three of seven cord settings:
- tau_m 5 ms: DLMn c-f 20 Hz, steering 3.5 Hz;
- tau_m 10 ms: steering 2.7 Hz;
- threshold gap 4 mV: steering 3.3 Hz.

The claim holds under the declared cord parameters. It depends on them; it is not robust across
them.

**Robustness battery** (12 runs, 14 scored checks each: escape, auditory, feeding; `results/overnight/`):

| run | checks | fails |
|---|---|---|
| seed 1, seed 2 | 14/14 | |
| random sign flip 5% (seed 0) | 13/14 | escape response probability 0.475 (calibrated) |
| random sign flip 5% (seed 1) | 14/14 | |
| random sign flip 10% | 13/14 | escape response probability 0.375 (calibrated) |
| targeted sign flip (classifier-uncertain neurons) | 14/14 | |
| weight scale 0.25 | 13/14 | escape response probability 0.275 (calibrated) |
| weight scale 0.35, 0.40 | 13/14 each | escape spikes per response 2.48, 3.50 (calibrated) |
| connection threshold 10, 20 synapses (first run) | 14/14 each | |
| stricter null (superclass) | 13/14 | auditory null control A4: 0.56 mV against a 0.5 mV limit |

Every failure is a **calibrated** escape check or a control. No independent check fails anywhere
in the battery. Two things changed from the September battery (16/16 almost everywhere):
- With adaptation at 10 mV instead of 30, the giant fiber's spike count and response probability
  are more sensitive to the weight scale and to random sign flips. The calibration has less
  margin.
- The superclass-preserving shuffle leaves enough ear-to-giant-fiber chemical structure for a
  0.56 mV depolarisation. A4 is the weakest control.

**The SEZ trio** (`roi_membership`, `check_modulators`, `fit_regional`). Membership needs no
volume download: it is one neuPrint query. Only the 3D meshes need the volumes. Run 2 had no
membership table, so feeding F2b silently fell back to the type-name SEZ. Setup now fetches the
table and the manifest pins it. With the anatomical SEZ (primary ROIs only, 4,606 SEZ-intrinsic
neurons):
- **Feeding F2b (calibrated).** The rate outside the SEZ is 0.00035 Hz against a 0.02 Hz limit:
  pass. Under the name rule it was 0.0025 Hz.
- **check_modulators.** There is still no dopaminergic or octopaminergic SEZ modulator. No such
  cell has more than half its synapses in the SEZ; one dopaminergic and two octopaminergic cells
  now pass 20%, against none before the nested-ROI fix. Serotonin keeps its 10 SEZ cells. None of
  the 900 output-dominated midline SEZ bodies is predicted dopaminergic (862 before).
- **fit_regional** (the retired SEZ gain). No SEZ gain from 1.5 to 2.5 lets taste drive MN9, as
  before. The fit's quick escape check (GF hit at least 0.8) now fails at every gain (0.67). The
  previous grid ran with 15 mV adaptation, the all-trials input and the name-based SEZ, so the
  cause is not isolated. The regional gain stays retired at 1.0.

**The diagnostics outside the suite, rerun and stamped (run 6):**
- **Cord sweep.** The pattern is unchanged under the current calibration: escape holds at every
  setting except a 10 mV threshold gap, where the relay fails (TTMn/GF 0.23, lag 24.4 ms).
- **Gain fit.** It now also passes its A2 check (score 7 of 8, against 6). Feeding (F1) still fails
  at every gain.
- **Afferent screens.** No taste afferent drives MN9 with a quiet CNS at any weight scale, as
  before.
- **Feeding mechanism. A defect:** its signed path products (M3) came out as NaN. The script reads
  the stale `sign` column stored in the edge table, not the model's signs. The audit of 11 October
  flagged exactly this. Fixed in run 8 (above): the script now reads the graph the model uses.
- **Embodiment gate and baseline fit:** unchanged.

**Fixed along the way:**
- **Registered tests could not be rerun.** A registered test compared its saved criteria with its
  code without converting to JSON. A tuple in code never equals the list it was saved as, so the
  flight robustness battery refused every rerun.
- **The targeted sign flip could run unperturbed.** Without its transmitter table it printed a line
  and ran the plain network under the perturbation's name.
- **The battery summary mixed in other benchmarks.** It counted every benchmark in `results/`,
  not just the three it reran.
- **STALE misfired on parallel runs.** It now means the model code changed since a report.
- **The cloud rerun had no anatomical SEZ.** See "The SEZ trio" above.
- **Two misleading log lines.** Registered tests printed the current commit as the registration
  commit. Flight runs warned about "no outgoing edges" when they had no stimulus types to warn
  about. The SNpp16 graded report's `registration` field also recorded the run's commit (fcff151);
  since run 6 it records the true registration (fae9fdb, 25 September), as its `criteria.json` does.
- **The citation check missed three references** (Namiki et al. 2022, Sasaki & Burrows 1998,
  Newcombe 1998). It also raised false alarms on dates and on accents (Pezier, Pézier). It now
  resolves all 48 tags.

---

## 10 October 2026: calibration ledger and run integrity

**Escape reclassified as the calibration circuit.** An outside review traced three chosen values to
the escape readouts:
- the global weight scale, chosen by a sweep that looked at giant fiber firing;
- the loom rate scale, anchored so the giant fiber fires 1 to 2 spikes;
- the giant fiber's adaptation, fitted to the same targets.

The escape spike-count and response-probability checks are therefore **calibrated**. TTMn one-to-one and lag hold **by construction**. The independent part of escape is its latency, plus two controls. Every check now carries a role (`flycns/calibration.py`), and `results/SUITE.md` counts independent checks separately. The held-out results are the circuits nothing was fitted to: A2 facilitation, pC1 song, the signed taste map, sugar laterality, feeding by modality, flight (except L1a) and SNpp16.

**Committed escape and feeding reports were left in a perturbed state.** The robustness battery wrote into the canonical result folders and did not restore them. The committed `results/gf_escape/report.json` and `results/feeding/report.json` therefore came from the targeted sign-inversion run (seed 0, 11 September), not a canonical run. The battery also copied every benchmark's report into one folder under one name, so each tag kept only the last report. Both are fixed: the battery snapshots and restores the canonical folders, and it keeps one report per benchmark. The escape numbers quoted in this note were recorded from runs before the battery. The committed perturbed report shows 0.65 response probability and 1.19 spikes per response, against 0.68 and 1.06 here. Rerun the core suite (menu 4, `scripts/run_all.py`) to replace both reports with canonical ones that carry the new integrity stamp, and to confirm the quoted numbers.

**Run integrity.** Reports now record:
- whether the code matched the stamped commit;
- a content fingerprint of the input tables;
- every settings override.

Registered tests refuse uncommitted code and data that differ from `data/MANIFEST.json`. See README, "Integrity".

**Windows only (10 October 2026, later).** The project now runs on Windows alone:
- `setup.cmd` and `fly.cmd` replace the bash scripts, and the remaining scripts are Python.
- Every text file is read and written as UTF-8.
- The simulation engine is compiled when the Microsoft C++ Build Tools are present and pure Python otherwise. The two engines gave identical spikes on every comparison: the toy graph, and a 60,000-neuron synthetic network with 204,135 spikes. The pure-Python engine is about 4 times slower.
- CI runs on Windows only.

No model equation, parameter or criterion changed.

**New robustness axes, not yet run on the full connectome:**
- the connection-size threshold (10 and 20 synapses, against the default 5; the fetch keeps nothing below 5, so a looser threshold is impossible and is refused);
- a stricter null that shuffles wiring only within cell class (`benchmarks/null_strict.py`, registered; it also runs in the battery).

---

## 10 October 2026, later: full audit (four independent code reviews plus a run of every script)

Each finding below was confirmed against the code, the committed reports, or a test, and then fixed.
The fixes change no registered criterion. Several change what a rerun will measure, so the
affected committed results are marked **rerun pending** and must not be quoted until they are rerun.

**Update, 11 October 2026:** all of them have been rerun; see the section above.

**Affecting committed results**
- **Loom input was all-trials, not stationary.** The committed data file had no per-state split, so every loom-driven result used all-trials amplitudes. The documentation said stationary. Missing states are now an error, and the file now has the split. **Rerun pending:**
  - escape;
  - auditory, A2R and RA2;
  - DNp31 and the auditory-wing trace;
  - the battery.

  The calibrated values must be re-checked first: PEAK_HZ, GF adaptation and the A2 working point.
- **The A2 arms differed in more than sound.** With the ear afferents simulated (loom alone), their gap junctions loaded the giant fiber. As stimulus sources (loom plus sound), the load vanished, making the giant fiber more excitable. Part of the reported facilitation (4% to 45%) may therefore be this artefact. Reviewers estimated about 0.1 to 0.15 of the difference, an estimate not yet measured. The model now keeps a source's load (`g_shunt`), and a unit test fails if the stimulus choice changes a partner's excitability. **A2R and RA2: rerun pending.** The registered result stands as recorded, with this caveat.
- **The AstA experiment never modulated.** A stimulated peptide source was skipped, and the report shows `peptide_applied: []`. The conclusion "Mi1 stays silent under AstA" is therefore withdrawn. Peptides now act from stimulated sources, a skipped peptide is an error, and the all-to-all wiring is replaced by one shared level. **peptide_asta: rerun pending.**
- **Flight robustness R2 varied the stimulus, not only the relays.** The "relay" superclasses included the driven wing afferents (vnc_sensory). At a 10 mV threshold gap the afferents themselves barely fired, so R2's failure there is uninformative. Sensory superclasses are now excluded, in sensitivity_flight as well. **R2 and sensitivity_flight: rerun pending.**
- **Flight robustness R1 was vacuous.** No flipped edge reached the active circuit: its draws are bit-identical to graded k=7. Separately, the targeted inversion flagged cells by transmitter identity rather than sign, so a glutamate cell whose T-bars say GABA was flipped to excitatory. Agreement is now by sign (`fit/synapse_nt.py`). **R1 and the targeted battery suite: rerun pending, after rerunning menu 24.**
- **Flight robustness R3 reused the original phase draws.** The registered text promises fresh draws; they are now drawn. **R3: rerun pending.**
- **sensitivity_flight ran at the outdated anchor 0.35.** It now uses 0.25. The committed flight_loop report also predates the multi-draw rule. **flight_loop and sensitivity_flight: rerun pending.**
- **Feeding scoring.**
  - F2b and F2c rates are now taken during the drive only. Before, F2b was diluted about 2.5x and F2c divided by 250 ms instead of 200.
  - F2b now uses the anatomical SEZ.
  - F5 (a null that cannot fail when the real network is also silent) and F4 (in fallback mode, MN9's own strongest inputs) are now reported, not scored.
  - A tie in F1 no longer counts as a match.

  **feeding: rerun pending.**
- **The SEZ membership double-counted nested ROIs** (a cell entirely in AMMC scored 0.67). It now uses primary ROIs only. **roi_membership, check_modulators and fit_regional: rerun pending (menu 25).** The SEZ gain is 1.0, so no scored result depended on this.
- **The cord-invariance claim was wrong.** See "Cord parameters" below, now corrected.

**Robustness of the tool**
- **Data and engine.**
  - Data fingerprints now agree across pandas 2 and 3 (checked).
  - Optional derived tables no longer block other copies.
  - The loom input file is guarded like code.
  - A failed `git status` no longer counts as clean.
- **Scripts and batteries.**
  - Every loom report now records which loom input it used.
  - Settings equal to their defaults are no longer flagged as perturbed.
  - Staleness is judged from each report's write stamp, not file times.
  - A2 scores only the report its own run wrote.
  - The battery files only successful reports and runs feeding at the canonical trial count.
  - Every restore of canonical results is exact.
  - Jittered spike trains can no longer crash a run.
  - Thresholds below the data's floor are refused.
  - The stimulus audit now covers every benchmark.
- **Maintainer flow.** Menu 51 now:
  - checks git's identity before the long run;
  - verifies every commit and push;
  - never leaves a half-finished rebase.
- **Setup.**
  - It rebuilds an environment made with another Python.
  - It installs the lock from ready-made Windows wheels only. pykdtree 1.4.3 replaces a Mac-only pin.
  - It never refetches over pinned data.
- **Smaller fixes.** The launchers no longer load the simulator, so Windows does not lock its files during updates. Downloads resume past a completed file.
- **CI.**
  - It runs a script directly under Windows' default encoding.
  - It checks that compiled jobs really compiled.
  - It runs menu 51 end to end against a stand-in for GitHub.
  - The toy graph now exercises the gap junction, AstA and bitter paths it was missing.

---

## 1. What passes

**Loom escape** (`benchmarks/gf_escape.py`, 8 scored checks). Driving the 13 loom-sensitive
visual projection types (2,526 cells) at measured amplitudes fires the giant fiber 1.46 times per responding
cell with a response probability of 0.575 (95% CI 0.42 to 0.71, 40 trials) and a latency of 39.7 ms
(rerun 11 October 2026 at `fcff151`, adaptation 10 mV; quoted earlier as 1.06, 0.68 and 37 ms,
values no committed report confirms).
Each GF spike drives exactly one TTMn spike 0.9 ms later through a modelled gap junction. Without
the electrical model TTMn is silent. On a degree-preserving rewired connectome neither the giant
fiber nor TTMn fires (population rate 4e-7 Hz). This is a sensory-to-motor cascade across the neck connective at physiological latency.

**Auditory input to the giant fiber** (`benchmarks/auditory.py`, 4 scored checks). Johnston's organ
drive alone leaves GF subthreshold, as recorded in vivo. Removing both the electrical model and
the 679 EM synapses annotated as chemical on that contact abolishes the response, identifying
those synapses as the pathway.

**Sound facilitates the giant fiber's response to a near-threshold loom** (`benchmarks/a2_registered.py`;
criterion registered at `cbc0cc5`, committed to GitHub before any result in `4b3d746`, results
`c097e41`). Tootoonian et al. 2012 (J Neurosci 32:787-798, Fig. 2D) showed that sound together with an
input subthreshold on its own produces a full GF spike. At a working point calibrated per run (the
largest loom gain leaving GF hit rate at or below 0.3 with at least 2 mV depolarisation), with 120
trials per arm. The rerun of 11 October 2026 (`fcff151`; stationary input, adaptation 10 mV, the
ear afferents' load on the giant fiber kept in both arms) chose gain 0.8:

| condition | GF responses | probability (95% CI) |
|---|---|---|
| loom alone | 21 / 120 | 0.175 (0.117 to 0.253) |
| loom + sound | 64 / 120 | 0.533 (0.444 to 0.620) |
| difference | | **+0.358 (+0.240 to +0.463)** |

The original registered run (`c097e41`, gain 0.6) gave 5/120 against 54/120, +0.408 (+0.308 to
+0.501). The runs differ in input, adaptation and working point, so the two differences cannot
be compared directly. At the same gain of 0.6 the rerun sweep gives +0.40 (below).

**A2R: PASS.** The interval lies entirely above zero, so the model reproduces the facilitation. Sound
alone stays subthreshold (A1), a near-threshold loom rarely fires the giant fiber, and together they
fire it on more than half of trials. This resolves a question the project had carried as "unresolved"
since its first week; the earlier inconclusive readings came from too few trials and from an interval
function that was wrong until it was corrected and verified. Caveat: the calibrated working point
moves with the loom input and the adaptation (0.6 in the original run, 0.8 in the rerun), and one
run does not show how the effect varies across working points. That caveat was then tested:

**Facilitation is robust across working points** (`benchmarks/a2_robustness.py`; registered at
`cc8d759`). The same protocol at five fixed loom gains, 100 trials per arm, with "near threshold"
defined in advance as loom-alone response at most 0.3. Rerun 11 October 2026 (`fcff151`):

| loom gain | loom alone | loom + sound | difference (95% CI) | regime |
|---|---|---|---|---|
| 0.4 | 0 / 100 | 20 / 100 | +0.20 (+0.12 to +0.29) | near threshold |
| 0.5 | 0 / 100 | 32 / 100 | +0.32 (+0.23 to +0.42) | near threshold |
| 0.6 | 0 / 100 | 40 / 100 | +0.40 (+0.30 to +0.50) | near threshold |
| 0.7 | 10 / 100 | 50 / 100 | +0.40 (+0.28 to +0.51) | near threshold |
| 0.8 | 18 / 100 | 56 / 100 | +0.38 (+0.25 to +0.49) | near threshold |

**RA2: PASS.** Facilitation at all five gains, every one of them near threshold now. Three
observations:

- **Sound makes a loom that never fires the giant fiber fire it.** At gains 0.4 to 0.6 the loom
  alone gives 0 of 100; with sound, 20, 32 and 40 of 100. This is Tootoonian et al.'s result in
  its purest form (an input subthreshold on its own produces a spike when paired with sound),
  shown across a range rather than at one point.
- **The effect rises, then levels off** from gain 0.6 (+0.40, +0.40, +0.38). The September sweep
  peaked at 0.6 and fell to +0.27 at 0.8, where the loom alone already fired 36 of 100. With the
  ear afferents' load now kept in both arms (and the stationary input and 10 mV adaptation), the
  loom alone fires less from gain 0.6 up (0, 10 and 18 of 100, against 3, 16 and 36), and the
  drop is not reached inside the grid.
- **It replicates.** At gain 0.8 the sweep gives 0.180 to 0.560, against 0.175 to 0.533 in the
  registered 120-trial run.

**Feeding, partially** (`benchmarks/feeding.py`, 2 scored checks since the audit). Activity stays
inside the SEZ and motor rates stay physiological. Each of MN9's excitatory second-order inputs
drives it when stimulated directly, and MN9 is silent on a rewired null. Both are now reported,
not scored, because the audit found they could not fail (F4 in fallback mode, F5). What fails is
the part that matters, below.

---

## 2. What does not pass, and why

Four independent circuits fail. Three share one cause.

### The shared cause: this model class cannot express disinhibition

- **Taste to MN9.** MN9's input is balanced to 1.4% (2,966 excitatory against 3,049 inhibitory
  synapses). Gustatory afferents contact its inhibitory relays about three times more strongly
  than its excitatory ones (1,097 against 3,333 synapses for the screen-selected subset; 1,314
  against 4,659 for all anatomically gustatory afferents). Signed path products from those
  afferents to MN9 are negative at two hops and positive at three to five: **the pathway is
  disinhibitory** (`benchmarks/feeding_mechanism.py`).
- **The canonical ON visual pathway.** Mi1's largest input is L1 with 141,873 glutamatergic
  (inhibitory) synapses. The ON response is a double inversion: light depolarises photoreceptors,
  histamine inhibits L1, L1 releases less glutamate, Mi1 is released.
- **AstA peptidergic modulation.** Pm3 is GABAergic, so in a silent network its fast synapses
  have nothing to suppress. The peptide is represented but unscored: AstA raises Mi1's flash
  response from near zero (0.0002) to 0.04 spikes per flash (`benchmarks/peptide_asta.py`),
  far below the graded change Krieger 2023 reports. (Correction, 11 October 2026: this line said
  the peptide produced "nothing at all, in the model or in principle".)

A network with no spontaneous activity cannot represent any of these, and a uniform tonic baseline
does not help: it lets MN9 respond but the wind-sensitive control responds just as strongly
(specificity lost) and the escape response is abolished (`benchmarks/fit_baseline.py`). Four
uniform manipulations were tested and all fail: global weight scale (0.25 to 1.0), class-wise
gains (up to 3x), regional gain on SEZ intrinsic neurons (1.5 to 4x), and uniform tonic
depolarisation with noise (3 to 6 mV).

### The fourth: the ear-to-flight route exists but is silent

The pathway is four hops: 114 auditory Johnston's organ afferents to SAD and WED relays, then
DNp02 (818 synapses), DNp06 (806), DNp11 (568 plus 96 direct) and DNg108 (489 plus 32 direct) onto
the VNC premotor interneurons that drive the wing muscles. The giant fiber does not participate
(6 synapses), consistent with it driving the jump rather than steering. But all four descending
neurons are loom-dominated by 3.5x to 38x in two-hop signed input, so MaleCNS shows no dedicated
auditory-to-flight channel, and none of them fires under measured loom drive, so the multisensory
test the anatomy suggests would compare zero against zero (`benchmarks/auditory_wing_trace.py`).

### A different obstacle: DNp31 and the closed loop

DNp31 is the strongest descending input to the wing motor pool (3,019 synapses) and is the only
neuron examined here with a large excitatory surplus (net +14,568). All of its wing output is
excitatory and spans the whole flight apparatus: DLMn c-f (1,128) and DLMn a,b (156) for the
downstroke, DVMn 1a-c, 2a,b, 3a,b (1,077) for the upstroke, ps1 (593), b2, b1 and hg4 for
steering. Its dominant input is proprioceptive and specifically from the **wing**: campaniform
afferents entering through ADMN, the anterior dorsal mesothoracic (wing) nerve, give 1,045,551
on the two-hop measure, with 24,588 from DMetaN, the dorsal metathoracic (haltere) nerve, and
nothing from any leg nerve (`benchmarks/embodiment_gate.py`). It fires zero spikes under loom
because wing campaniform organs report self-generated wing load, which exists only when the
animal is already flying. This is an argument for embodiment, not for more parameters.

A correction is recorded here rather than hidden. An earlier draft read ADMN as an abdominal
nerve and called DNp31 abdominal-load-driven; that was wrong. Court et al. 2020 (Neuron
107:1071-1079) and the wing sensory reconstruction of Lesser, Moussa et al. (eLife 107867) place
wing afferents in ADMN and haltere afferents in DMetaN, and the dataset confirms it: abdominal
afferents enter through AbN1 to AbN4 and AbNT (1,145 cells, all subclass `abdomen`). The
consequence is good news: the haltere campaniform population is present in MaleCNS v1.0 as the
195 DMetaN afferents, under a nerve-based label rather than a "haltere" subclass.

**The proprioceptive-to-wing-motor loop, as wired.** Wing and haltere campaniform afferents
contact wing motor neurons directly with 11,412 synapses, all excitatory, and through 1,112
relay interneurons with 181,661 (101,272 excitatory, 80,389 inhibitory). The net drive splits
along a functional line: power muscles are excited (DLMn c-f +10,352, DVMn 1a-c +4,711, DLMn a,b
+3,732, DVMn 3a,b +1,649, DVMn 2a,b +1,629) and most steering muscles are inhibited (tp1 -4,697,
ps1 -2,285, hg3 -2,136, hg4 -1,352, hg2 -944), with iii1 (+4,277), b2, i1 and hg1 as excited
exceptions. No physiological counterpart to that split was found in the literature; it is a
connectome-derived prediction, and the surrogate loop below is the test of it.

---

### The flight loop, run: monosynaptic drive works, disynaptic drive does not

> **Re-measured across recruitment draws (23 Sept 2026).** An earlier version of this section
> quoted single random draws. DVMn 1a-c's proprioceptive drive is concentrated in a few
> afferents, so which ones a given load recruits decides whether it fires. Across five draws:
>
> | load | DVMn 1a-c mean +/- SD | range across draws | DLMn c-f |
> |---|---|---|---|
> | 0.25 (anchor) | 6.8 +/- 6.2 Hz | 0 to 15.2 | 0 |
> | 0.35 | 9.2 +/- 9.7 Hz | 0 to 25.9 | 0 |
> | 0.40 | 18.9 +/- 7.6 Hz | 11.2 to 31.7 | 0 |
> | 1.00 (all recruited) | 83.6 +/- 0.2 Hz | 83.5 to 83.9 | 0 |
>
> So DVMn is in band **on average** at the anchor but no single run reliably puts it there; only
> at full recruitment, where nothing is left to chance, is it stable, and there it is seven times
> over band. The anchor moved from 0.35 to 0.25 under the same rule applied to the mean. Everything
> else survived the draws: DLMn c-f silent at every load in every draw; steering wiring-specific in
> every draw (null 0); b1 at the anchor 105 Hz, 0.52 spikes per wingbeat; and stage 2 unchanged
> (the 100 Hz command that brings DLMn c-f to 12.5 Hz drives DVMn to 40.5 Hz). DLM's silence was
> also confirmed independently of the draw: it stays below 2 Hz across the whole relay-layer
> parameter sweep (`benchmarks/sensitivity_flight.py`).
>
> **The variance names a cell type, and the named type is selective, not necessary.** One wing
> campaniform type, **SNpp16** (13 cells, ADMN), carries 664 of DVMn 1a-c's 1,017 afferent
> synapses, 65%. `benchmarks/flight_snpp16.py` drove identified sets deterministically, all cells
> firing once per wingbeat, three phase seeds each. The two pre-stated checks **both failed**:
>
> | arm | DVMn 1a-c | steering | b1 | DLMn c-f |
> |---|---|---|---|---|
> | SNpp16 alone (13 cells) | 33.6 Hz | 0 | 0 | 0 |
> | every other afferent (400) | 14.9 Hz | 71.5 | 263 | 0 |
> | all 413 afferents | 83.5 Hz | 65.5 | 261 | 0 |
> | SNpp16 alone, rewired null | 0 | 0 | 0 | 0 |
>
> N1 (SNpp16 alone puts DVMn in the 2-12 Hz band) failed: it drives DVMn three times over band.
> N2 (withholding SNpp16 drops DVMn below 2 Hz) failed: the other afferents still give 14.9 Hz. So
> the necessity prediction was wrong. What the arms show instead, reported and not scored: SNpp16
> is a **selective** driver, reaching DVMn and nothing else in the flight system, through its real
> wiring (the rewired null gives zero); and inputs to DVMn sum **supralinearly**, 83.5 Hz together
> against 48.5 for the two parts, which is why random recruitment swung so widely. The criteria
> were not rewritten after the fact; a graded-recruitment test with criteria stated in advance
> would be the way to score the selectivity claim. That test has now been run.
>
> **Graded test, criteria registered before the run** (`benchmarks/flight_snpp16_graded.py`;
> criteria registered at `fae9fdb` and committed in `11dcc6a` before any result existed; final results in `0eb3416`;
> `64d665b` holds an intermediate state). k of the 13 SNpp16 cells were recruited, k = 1 to 13,
> five draws each randomising which cells fire and their phase. Result: **four of five criteria
> pass.**
>
> | k | DVMn 1a-c mean | draws in band | steering | b1 | DLMn c-f |
> |---|---|---|---|---|---|
> | 1-2 | 0.0 Hz | 0/5 | 0 | 0 | 0 |
> | 3 | 1.2 Hz | 1/5 | 0 | 0 | 0 |
> | 4 | 0.0 Hz | 0/5 | 0.14 | 0 | 0 |
> | **5 (k*)** | **3.9 Hz** | **4/5** | 0.12 | 0 | 0 |
> | 6 | 4.5 Hz | 4/5 | 0.18 | 0 | 0 |
> | 7 | 7.4 Hz | 5/5 | 0 | 0 | 0 |
> | 8 | 9.0 Hz | 5/5 | 0 | 0 | 0 |
> | 9-13 | 14.7 to 33.6 Hz | above band | 0 | 0 | 0 |
>
> - **G1 graded: FAIL.** The mean at k=4 falls below k=3 by more than the 0.5 Hz tolerance.
>   SNpp16's cells contribute unequally, so at small k which cells fire matters more than how
>   many. The criterion was fixed in advance and stands.
> - **G2 in-band window: pass** (k=5 to 8). **G3 selective at k*: pass**, and at every k: with
>   all 13 cells driving DVMn to 33.6 Hz, steering never exceeds 0.2 Hz and b1 and DLMn stay at
>   zero. **G4 wiring-specific: pass** (rewired null 0 Hz). **G5 reliable: pass** (4/5 at k*,
>   5/5 at k=7 and 8).
>
> Reported, not scored. SNpp07 (12 cells; an earlier note here called it 5, which was the number
> among DVMn's top 20 contributors) is **not** selective: alone it gives DVMn 3.5 Hz but also
> drives steering at 1.6 Hz. Supralinearity is strong at physiological rates: SNpp16 at k*=5 plus
> SNpp07 gives 28.7 Hz against 7.4 for the parts, 3.9 times the sum (1.7 at full recruitment).
>
> **Claim, scored and specific:** one named wing campaniform type, SNpp16, drives the DVM motor
> neurons without recruiting any steering muscle, reliably from about seven of its thirteen cells,
> through its actual wiring. Prediction: activating SNpp16 in a flying fly should raise DVM motor
> neuron activity without engaging the direct steering muscles.
>
> **Robustness battery, criteria registered before the run** (`benchmarks/flight_snpp16_robustness.py`;
> registered at `77e0cc5`, results `1225b21`). Two of three pass, and the failure qualifies the claim:
>
> - **R1 transmitter uncertainty: pass.** With 132,680 edges inverted (110,462 since the audit judges disagreement by sign; every neuron whose own
>   synapses disagree with its label), k=7 gives exactly the unperturbed draws (10.3, 7.2, 6.1,
>   6.7, 6.7 Hz). None of the uncertain calls lie on SNpp16's path to DVMn.
> - **R3 fresh draws: pass.** k* is 5 again, k=7 is in band in 4 of 5, and the curve is
>   monotone this time, so the k=4 dip that failed G1 was a property of those particular draws.
>   G1 remains a recorded failure because it was scored on the original draws.
> - **R2 relay-layer parameters: FAIL.** Selectivity holds at the declared relay values and at
>   every slower or less excitable setting, but leaks at three of seven: tau_m 5 ms (steering
>   3.5 Hz, and DLMn c-f fires at 23.6 Hz), tau_m 10 ms (steering 2.7 Hz), and a 4 mV threshold
>   gap (steering 3.3 Hz). b1 stays at zero throughout. DVMn's in-band rate is also fragile,
>   falling to zero at a 10 mV gap or a 5 ms refractory period.
>
> **The claim, as it now stands:** SNpp16 drives the DVM motor neurons selectively **under the
> declared relay parameters**; the selectivity does not survive faster or more excitable relay
> neurons, and because those parameters are inherited from central-brain values rather than
> measured, the claim is conditional on them. Its independence from transmitter uncertainty and
> from the particular cell draws is established.



`benchmarks/flight_loop.py` supplies the missing proprioceptive input as a surrogate body: the 218
wing (ADMN) and 195 haltere (DMetaN) campaniform afferents fire one spike per cycle at the
Drosophila wingbeat frequency of 202 Hz (Vogel 1967) with 0.8 ms jitter (Fox, Fairhall & Daniel
2010), a recruited fraction set by a scalar load, and uniform phase, since no Drosophila phase
map exists. The drive is injected into the afferent neurons themselves, so everything downstream
runs through the connectome's own synapses. Measured targets: DLM and DVM motor neurons at 2 to 12
Hz (Harcombe & Wyman 1977; Hürkey et al. 2023), b1 at one spike per wingbeat (Fayyazuddin &
Dickinson 1996). Afferent parameters are from crane fly, flesh fly and blowfly, stated as such.

What happened:
- **The steering system is driven by the wiring, not by the volume of input.** At the anchor load
  the real network gives 31 Hz across steering motor neurons and 128 Hz in b1; the rewired null
  gives zero for both. b1 fires 0.6 to 0.9 spikes per wingbeat across loads, in range; its phase
  locking is untestable while afferent phase is uniform by assumption.
- **The connectome's sign prediction holds for steering.** The four most-inhibited types in the
  wiring (tp1, ps1, hg3, hg2) are silent or near it; the excited ones fire (b1, i2, b2, iii1, i1).
  Three mild exceptions each way.
- **DVMn 1a-c fires, DLMn c-f never does**, at any load. DVMn receives 1,017 campaniform synapses
  directly. DLMn c-f receives 75 directly and depends on relays, where its structural balance is
  favourable (18,982 excitatory against 8,639 inhibitory). The diagnostic shows why that fails:
  of 92 excitatory relay interneurons onto DLMn c-f, **4 are active, at 1.1 Hz**, against 13 of 85 inhibitory relays at 3.0 Hz. The relay layer
  of a silent cord does not relay. In the rewired null, where DLM acquires random direct input,
  it is the one motor neuron that fires.
- **DNp31 stays silent** under all 413 afferents at 202 Hz, its own dominant input.
- **Closing the loop saturates**, because the surrogate body maps power output monotonically to
  load, which is positive feedback by construction; that is a property of the body model, not a
  finding about the fly.

This is the fifth circuit to point at missing background activity, and the first where the
missing activity sits in identified premotor interneurons rather than in a modulatory neuron
the dataset lacks. In a flying fly those interneurons are presumably driven by descending flight
command; in a silent cord they are subthreshold, and the disynaptic half of the flight motor
system is unreachable.

### Stage 2: the descending flight command, and a structural advantage the dynamics cannot use

DNg02 is the descending population whose activation drives the indirect flight muscle motor
neurons (Namiki et al. 2022, Curr Biol 32:1189-1196). In MaleCNS v1.0 it is 29 cholinergic cells
across seven subtypes (DNg02_a to _g), and delivering it matters: an earlier run selected it by
the exact name "DNg02", which matches nothing, so those arms ran without the command (commit
ce8b9d2, corrected in cbbdba7; an empty stimulus set now aborts the run). With the command
delivered to 1,327 connections and the proprioceptive loop at its anchor, mean power output rises
with command rate (2.9, 4.0, 6.6, 25.6 Hz at 10, 25, 50, 100 Hz), so DNg02 does drive the power
system. But the two power pools separate:

| DNg02 rate | DLMn c-f | DVMn 1a-c |
|---|---|---|
| 10 Hz | 0.0 Hz | 11.7 Hz (in band) |
| 25 Hz | 0.0 Hz | 15.9 Hz |
| 50 Hz | 0.1 Hz | 23.2 Hz |
| 100 Hz | 14.4 Hz | 50.8 Hz |

**No command rate places both the downstroke (DLM) and upstroke (DVM) power motor neurons in the
measured 2 to 12 Hz range together**, whereas in the fly both fire in that range during flight.
Lowering proprioceptive load does not rescue it: the 100 Hz command alone contributes about 41 Hz
to DVMn. A joint sweep of load and command against these two targets was not run, because two
free parameters fitted to two criteria will find a point by construction and predict nothing.

The wiring predicts the opposite of what the model does. Per cell, DLMn c-f receives 1,841 units
of net DNg02-derived drive and DVMn 1a-c 902, so the connectome gives DLM about twice the
descending command. The difference is where it sits: DLM's is almost entirely disynaptic (15,616
synapses through DNg02's targets against 423 direct), DVMn is already held near threshold by 1,017
direct proprioceptive synapses. In a cord with no background activity the relay layer stays
subthreshold until the command is very strong, so a two-to-one structural advantage becomes the
weakest firing in the pool. This is the sixth circuit to point at missing background activity and
the most precisely localised: the gap is a named relay layer with a measured advantage that the
dynamics cannot use. The DLM gap junctions described by Hürkey et al. 2023 would pool the five
DLM motor neurons but add no net drive, so they are not a fix for this.

### Feeding re-tested with taste afferents split by modality (registered)

The feeding drive used above mixed modalities. Tastekin, de Haan Vicente et al. 2026 (Cell
189:5527-5551, Fig. 2) type the MaleCNS labellar GRNs and assign them by driver-line anatomy:
LB1a-d bitter, LB3a water, LB3b and LB3c sugar, LB3d aversive high salt / heavy metal. Our
"sugar proxy" contained LB3a-d plus pharyngeal and taste-peg types. `benchmarks/feeding_by_modality.py`
re-tested the mechanism by modality, criteria registered at `4cfae84` before any result (results
`98f2c29`). All five labellar types are cholinergic in MaleCNS.

| group | onto MN9 excitatory / inhibitory relays | ratio | signed 2-hop | MN9 at 100 Hz |
|---|---|---|---|---|
| sugar (LB3b, LB3c; 34 cells) | 77 / 114 | 0.68 | ~0 | 0 |
| bitter (LB1a-d; 38) | 0 / 6 | 0.00 | ~0 | 0 |
| water (LB3a; 17) | 58 / 0 | 58 | ~0 | - |
| aversive salt (LB3d; 26) | 119 / 43 | 2.77 | ~0 | - |
| old mixed proxy (140) | 1,097 / 3,333 | 0.33 | -0.0035 | 0 |

**F1 verdict by the registered rule: STRENGTHEN.** Sugar alone still targets MN9's inhibitory
relays more than its excitatory ones and its two-hop product is not positive, and MN9 stays silent
to sugar at 50 and 100 Hz. F2 passes (sugar's ratio exceeds bitter's). F3 and F4 fail: nothing
drives MN9, so the dynamics show no valence.

**But the mechanism we published needs rewording.** The strong 3:1 inhibitory bias came mostly
from the non-labellar afferents in the old proxy. Its four labellar types together (sugar, water,
salt) put 254 synapses on MN9's excitatory relays and 157 on inhibitory; the pharyngeal and
taste-peg types (aPhM2a, aPhM5, PhG1c, claw_tpGRN) put 843 against 3,176, a ratio of 0.27. For
sugar specifically the pathway is only weakly inhibition-biased at two hops (its two-hop product
rounds to zero) and relies on excitation arriving at three hops and beyond, which a network with
no background activity also cannot deliver. So the feeding negative holds, but its cause for
sugar is attenuation across hops more than the strong disinhibition the mixed drive suggested.

Two further observations. Bitter barely touches MN9's relays (6 synapses), whereas the companion
paper's unsigned analysis finds bitter and sugar reach proboscis motor neurons comparably. And
LB3d is classified cholinergic in MaleCNS, so this model has the aversive-salt type exciting MN9's
relays (ratio 2.77); the companion paper matches LB3d to glutamatergic driver lines and proposes
it inhibits attractive circuits. If that is correct, the transmitter call for LB3d is wrong and
the model signs it backwards: a specific discrepancy between the connectome's prediction and the
molecular evidence.

### A signed sensory-to-motor map for taste (registered)

The companion gustatory paper computes influence from every taste neuron type to the feeding motor
neurons but states that its metric ignores synaptic sign. `benchmarks/gustatory_signed_map.py`
computes the same kind of map with sign, and an unsigned version built identically, for 64 GRN
types against 10 feeding motor neuron types (criteria registered at `2239201`, results `316eb61`).
Measure: input-normalised path products, cumulative over hops 1 to 5.

| labellar group | MN9 | MN6 | MN11D | MN11V | CEM |
|---|---|---|---|---|---|
| LB3a-c (water, sugar) | +5.2e-3 | -1.4e-4 | +4.8e-3 | +2.7e-4 | +7.8e-3 |
| LB3d (aversive salt) | +4.3e-3 | +1.1e-4 | +2.7e-3 | +7.2e-4 | +2.4e-3 |
| LB4 | +2.1e-4 | -5.2e-5 | +1.4e-3 | +1.1e-3 | +5.1e-3 |
| LB2 | -2.6e-4 | +1.9e-4 | +3.7e-4 | +7.7e-4 | **+9.0e-3** |
| LB1e | -1.3e-3 | -7.0e-4 | +4.9e-5 | +8.0e-4 | +2.7e-3 |
| LB1a-d (bitter) | -2.7e-4 | -2.4e-3 | -8.5e-4 | +1.6e-3 | -1.2e-2 |

- **S1, valence has a sign: PASS.** On the proboscis-extension motor neurons (MN9, MN6) the
  appetitive types have net positive influence (+8.5e-4) and bitter net negative (-3.3e-4).
- **S2, per-type sign agreement on MN9: FAIL** (4 of 7; 5 required). All three appetitive types
  agree. Of the bitter types only LB1c is negative; LB1a (+4e-6) and LB1d (+1.5e-5) are
  effectively zero and LB1b is exactly zero. The failure is absence, not wrong sign: bitter taste
  barely reaches MN9 within five signed hops, consistent with bitter putting only 6 synapses on
  MN9's relays.
- **S3, LB2 dominates pharyngeal pumping: FAIL.** With sign, LB2 ranks fourth on MN11D and MN11V,
  behind the appetitive types. The companion paper's unsigned prediction for pumping does not
  survive sign. LB2's influence instead concentrates on CEM, the crop-entry motor neuron, where it
  is the largest positive value in the table; that half of the paper's claim is supported.

**Reported, not scored.**

- **Sign reverses the unsigned picture for more than half of the strongest inputs.** Of the 15
  gustatory types with the largest unsigned influence on MN9, 8 are net inhibitory once sign is
  included: every pharyngeal type in the list (aPhM1, aPhM2a, aPhM2b, aPhM3, aPhM4) plus LB1c,
  LB1e and LgAG1. An unsigned map would rank these among MN9's strongest drivers; with sign they
  push against it. This is a quantified instance of the limitation the companion paper states in
  its own discussion, and it agrees with the modality re-test above, which found the pharyngeal
  afferents strongly inhibition-biased.
- **The LB3d transmitter call flips its predicted role.** Signed as MaleCNS classifies it
  (cholinergic), LB3d pushes the proboscis motor neurons positive (+2.2e-3), like an appetitive
  type. Signed as the companion paper's driver-line match suggests (glutamatergic), it pushes them
  negative (-1.8e-3), like an aversive one. The classifier-versus-molecular discrepancy therefore
  decides whether this model treats aversive salt as promoting or suppressing feeding.
- **Sign does not always change the answer.** The visual companion paper (Cell 189:5552-5570)
  predicted ON/OFF selectivity for 54 cell types from L1 versus L2 effective weight (45 of 54
  correct) and reports that adding negative weights for inhibitory neurons did not systematically
  improve it; its methods state the signed predictions were about as accurate as the unsigned ones.
  So a signed ON/OFF classifier would repeat a published test, and was not built. Sign changed the
  answer for taste, feeding laterality and song here; for that visual classification it did not.

### Laterality: Shiu's contralateral prediction holds for sugar, and only with sign (registered)

Shiu et al. 2024 predicted that labellar sugar neurons on one side drive the opposite MN9 more
strongly. This project had recorded that as untestable for lack of a sugar annotation; with LB3b and
LB3c identified as sugar-sensing (Tastekin et al. 2026), `benchmarks/sugar_laterality.py` tests it
structurally (criterion registered at `27d36e2`, results `96308aa`). Only explicit sides are used
(annotated side, else the instance suffix); all 34 sugar cells have one. The criterion required both
sides positive and the contralateral value at least 10% above the ipsilateral one.

| drive | measure | from left: contra / ipsi | from right: contra / ipsi |
|---|---|---|---|
| sugar (LB3b, LB3c) | signed | **3.35** | **1.73** |
| sugar | unsigned | 1.14 | 0.88 |
| old mixed proxy | signed | 5.91 | 1.34 |
| old mixed proxy | unsigned | 1.02 | 0.91 |

**L1: PASS.** Sugar favours the contralateral MN9 on both sides. Unsigned, the same neurons show no
consistent bias, so the prediction becomes visible only when synaptic sign is included.

**Where the bias comes from.** Sugar has no short route to MN9: at two hops its signed influence is
at most 1e-5 on either side. Its whole influence arrives at three to five hops, and is contralateral
at each. This agrees with the modality re-test above, which found sugar reaches MN9 only through
longer paths.

**This overturns an earlier result.** Earlier versions of this project reported that unilateral
gustatory drive produced ipsilateral MN9 output, matching a 73 to 1 ipsilateral structural bias.
That bias was an unsigned count of raw synapses over two hops, on the mixed drive. The signed
per-hop breakdown shows why it misled: in the mixed drive the two-hop routes are net INHIBITORY on
both sides (from the left, -1.4e-3 ipsilateral against -3.2e-4 contralateral), so the large
ipsilateral routes counted as "drive" mostly suppress MN9. The dynamic run that appeared to confirm
it used the SEZ regional gain later retired as a naming artefact. The claim is withdrawn (section 7).

### Courtship song: a male-specific circuit the model reproduces (registered)

The male pC1/pC1x neurons were activated line by line while song was recorded (Current Biology
36:4697-4716, 2026, Fig. 5): pC1_13 and pC1_14 enhance pulse and suppress sine, pC1_14a alone is
necessary and sufficient for pulse, pC1_15 with pC1_16 suppress both. The song command neurons are
pMP2 (pulse), DNp13 (sine) and pIP10 (both). The authors traced two- and three-synapse paths, split
by transmitter, and concluded that many phenotypes cannot be explained by chemical synaptic
connections and transmitter predictions alone. `benchmarks/pc1_song.py` asked whether a signed,
spiking simulation does better (criteria registered at `981a20f`, results `8a9ca3f`). Suppression
phenotypes were declared untestable in advance: with no background activity there is no song-neuron
firing to suppress.

| drive (100 Hz) | cells | pMP2 (pulse) | DNp13 (sine) | pIP10 (both) | static signed pMP2 / DNp13 |
|---|---|---|---|---|---|
| pC1_14a | 6 | **8.15** | 0.00 | 5.70 | +1.3e-1 / +9.3e-3 |
| pC1_13a, 14a, 14b | 10 | **11.05** | 0.00 | 6.75 | +1.8e-1 / +1.4e-2 |
| pC1_15a-c, 16 | 20 | 0.00 | 0.00 | 1.45 | **-2.9e-2 / -1.5e-2** |
| P1a (12b, 4a, 4b), reported | 12 | 0.00 | 0.00 | 0.00 | +2.1e-3 / +8.9e-3 |
| pC1_17a-b, reported | 8 | 0.00 | 0.00 | 0.30 | +9.7e-4 / +1.0e-2 |
| pC1_14a, rewired null | 6 | 0.00 | 0.00 | 0.00 | - |

Units: spikes per cell per 200 ms pulse.

**All four criteria pass.** P1: pC1_14a drives pMP2 far above the 0.5 criterion and above DNp13.
P2: the pC1_13/14 combination does the same. P3: pC1_14a drives pMP2 more than pC1_15/16, which
leave it silent. P4: on shuffled wiring pC1_14a drives nothing. This is the first male-specific
circuit in the project, and one of only two circuits (with escape) where the model reproduces a
recorded phenotype from wiring alone.

**Sign recovers the phenotypes statically too.** The four-hop signed path products already point
the right way for every tested group, including the one the dynamics cannot test: pC1_15/16 are net
NEGATIVE onto both pMP2 and DNp13, matching the suppression of both songs in the fly. For these
groups, sign and a few more hops are enough; the paper's more pessimistic conclusion was drawn from
two-synapse paths across many more lines.

**Caveat, resolved.** DNp13 fired in no arm of this test, so "pulse over sine" could have meant only
that the sine neuron was unreachable. A registered positive control settled it (below): DNp13 is
reachable, so pC1_14a's pulse-over-sine is genuine selectivity. The claim still covers the five
groups tested, not the paper's 48 pC1/pC1x types.

### The sine-song neuron is reachable, through a separate pathway (registered)

`benchmarks/dnp13_control.py` (registered at `c67b98e`, results `ccfdff2`) asked whether DNp13 can
fire at all. Its decisive arm drives DNp13's strongest excitatory input type, chosen by a fixed rule
from the graph before any simulation. The interpretation of every outcome was written in advance.

| drive (100 Hz) | cells | DNp13 (sine) | pMP2 (pulse) | pIP10 (both) |
|---|---|---|---|---|
| SIP108m, rule-chosen strongest input | 4 | **14.30** | 0.00 | 0.00 |
| pC1_1b | 2 | 0.00 | 0.00 | 0.00 |
| LC10a | 275 | 0.00 | 0.00 | 0.00 |

- **D1, reachability: PASS.** SIP108m drives DNp13 to 14.3 spikes per cell per pulse with pMP2 and
  pIP10 silent. By the pre-written interpretation, pC1_14a's pulse-over-sine is genuine selectivity.
- **D2, pC1_1b drives sine: FAIL.** pC1_1b drives nothing (static signed influence on DNp13 only
  +1.6e-2), and neither do all 275 LC10a cells. The companion paper's link from pC1_1b to DNp13 is
  not reproduced.

**Two opposite selective pathways.** pC1_14a drives the pulse neuron and not the sine neuron;
SIP108m drives the sine neuron and not the pulse neuron. The pulse/sine split is present in the
wiring and survives simulation in both directions.

**A testable prediction: SIP108m (pIP5 class) should promote sine song.** One male-specific type,
SIP108m (4 cells), drives the sine command neuron DNp13 and not the pulse neuron pMP2 in a
rule-chosen control arm. Seven further pIP5-class types are its strongest inputs by wiring but
were not simulated, and novelty has not been checked against the song literature. (Correction,
11 October 2026: this heading said "activating the pIP5 (pIP-e) neurons should promote sine song",
a class-level claim from one simulated type.) The rule found
SIP108m from the wiring; MaleCNS's own sex annotations (`scripts/fetch_dimorphism.py`, properties
`dimorphism`, `fruDsx`, `synonyms`) then identify it and every other strong excitatory input to DNp13:
(The literature names come from MaleCNS's `synonyms` annotation. They have not all been checked
against the papers: pC2l does not appear in Nojima et al. 2021's text, and pIP-e was not found in
Cachero et al. 2010's full text.)

| type | cells | dimorphism | fru/dsx | literature names |
|---|---|---|---|---|
| SIP108m | 4 | male-specific | fru_high, coexpress_high | pIP-e (Cachero 2010), pIP5 (Yu 2010), pC2l (Nojima 2021) |
| PVLP204m, SIP109m | 6, 4 | male-specific | fru_high, coexpress_high | pIP-e / pIP5 / pC2l |
| SIP110m_a, SIP110m_b, AVLP711m | 2, 2, 5 | male-specific | fru_high | pIP-e / pIP5 |
| AVLP713m | 2 | male-specific | coexpress_high | pIP-e / pIP5 / pC2l |
| PVLP214m | 10 | male-specific | fru_low | pIP-e / pIP5 |
| **DNp13** (sine command) | 2 | **sexually dimorphic** | dsx_high | pMN1 (Kimura 2015), DN1 (Ruta 2010) |

All eight of DNp13's strongest m-suffixed excitatory inputs are male-specific, fruitless-positive, and
the same literature class. The sine pathway the model found is therefore built from male-specific
neurons of an already-named class onto a sexually dimorphic command neuron, a prediction only a male
connectome could make. The pulse pathway is sex-specific too: pMP2 and pIP10 are male-specific and
fru-high (pIP10 is P2b in Kimura 2008 and Kohatsu 2011), and pC1_14a is annotated potentially
male-specific. pC1_1b, the input the companion paper links to DNp13 and which drove nothing here, is
male-specific as well.

## 3. The missing ingredient is not obtainable from this dataset

Feeding needs cell-specific spontaneous activity. The one neuron with a measured, hunger-gated
tonic rate in the right place is TH-VUM, a single dopaminergic ventral unpaired median neuron in
the SEZ firing at about 1 Hz when fed and 25 Hz after 24 h starvation (Marella, Mann & Scott 2012,
Neuron 73:941-950, Fig. 6, loose patch in vivo, 5 animals per condition). It cannot be used, and
neither can the alternatives (`fit/check_modulators.py`):

- **By name:** peptidergic populations exist (hugin 4 cells, leucokinin 12, AstA 2, drosulfakinin
  6, NPF 4), but there is no TH-VUM. AKH-producing cells are absent as expected for a
  neuroendocrine organ outside the CNS.
- **By transmitter and region:** of 396 dopaminergic and 101 octopaminergic neurons, **none has
  half of its synapses in SEZ compartments**; they sit in the mushroom body, central complex and
  abdominal neuromere. (Rerun 11 October 2026 over primary ROIs only: one dopaminergic and two
  octopaminergic cells pass 20%. Before the nested-ROI fix none did.) Only serotonin has any SEZ presence (10 cells above 50%). This also
  rules out the SEZ octopaminergic AKHR route.
- **By morphology:** of 1,088 midline bodies with more than half their synapses in the SEZ, 900
  are output-dominated (the nSyb-GFP phenotype Marella describes), and **zero are
  dopamine-predicted** (rerun 11 October 2026; 1,037 and 862 before the nested-ROI fix). Five
  contact MN9's relays at all. The largest contact is 168 synapses (body 331473), against the
  ~6,000 reaching MN9.

The likeliest explanation is a classifier blind spot rather than a missing neuron: Eckstein et al.
2024 (Cell 187:2574-2594) report cell-level accuracy of 96% for GABA and 91% for acetylcholine but
85 to 90% for dopamine, and neurons releasing mainly by volume transmission offer few classical
synapses to classify. A dopaminergic VUM would plausibly sit among the ~1,095 untyped,
transmitter-unclear gnathal bodies. No candidate is promoted on shape alone.

---

## 4. Measured inputs

The loom stimulus is not a guess. Per-glomerulus amplitudes and the trial-gain distribution were
extracted from the public Turner, Krieger, Pang & Clandinin 2022 dataset (eLife 11:e82587; Dryad
doi:10.5061/dryad.h44j0zpp8) by `fit/extract_turner_loom.py`: 21 flies, 1,510 loom trials, 13
glomeruli, epoch onsets taken from the per-epoch clock stamps rather than the photodiode.

Trials are split by the authors' own 50 Hz walking classification, carried in the datafiles, so no
video download is needed. Each state's amplitudes are normalised to that state's own largest
glomerulus (`fit/extract_turner_loom.py`, LC12 = 1.0 in both), so the per-state numbers give the
*shape* of the loom profile in each state, not its size: they cannot say whether loom responses are
larger or smaller when the fly walks, and no such claim is made here. (Corrected 17 October 2026: this
paragraph used to read the walking-vs-stationary differences, e.g. LC6 0.64 against 0.40, as a
locomotor enhancement; that comparison is an artefact of the per-state normalisation. The extractor
does not store absolute per-state amplitudes.) The two states also come largely from different days
and protocols (8 walking and 13 stationary series; the LoomingSpot series are the walking-fly days),
so state is confounded with protocol. The trial-gain sigma is 0.442 walking and 0.357 stationary.
Because the benchmarks simulate a fly that is not walking, the **stationary** profile is the default;
`FLYCNS_LOOM_STATE=walking|all` selects the others. The same wrong claim sits in a comment in
`flycns/protocols.py`, a hashed model file; it is corrected at the generation-6 freeze.

The dF/F-to-rate scale (5 Hz for the strongest glomerulus) is the one remaining free parameter of
the stimulus and is declared as such.

---

## 5. Robustness

**Nine-suite battery (September 2026; superseded).** Each run was a full three-circuit suite at 40
trials. This table predates the October fixes (the input was all-trials, adaptation 30 mV) and is
kept as history. The current battery is in the 11 October section at the top and in
`results/overnight/battery_2026-10_cloud.txt`. For example, wscale035 passes everything here but
fails a calibrated escape check there:

| run | result | failing check |
|---|---|---|
| seed 1 | 16/16 | - |
| seed 2 | 16/16 | - |
| 5% random NT sign inversion (seed 0) | 16/16 | - |
| 5% random NT sign inversion (seed 1) | 16/16 | - |
| 10% random NT sign inversion | 15/16 | GF response probability |
| weight scale 0.25 | 15/16 | GF response probability (under-driven) |
| weight scale 0.35 | 16/16 | - |
| weight scale 0.40 | 16/17 | GF spikes per response (over-driven) |
| **targeted NT inversion** | **all pass, 0 failures** | - |

The targeted arm inverts the sign of every neuron whose own per-T-bar predictions disagree with
the aggregate label used for signing: 132,680 edges, 2.0% of synaptic weight. (Since the audit,
disagreement is judged by sign: 110,462 edges, 1.6%. The 11 October rerun gives the same result.) It
costs nothing anywhere, so **no scored result rests on a transmitter call the classifier is uncertain about**.
That is stronger than surviving an arbitrary 5% flip, which is why both are reported. The weight
scale has a genuine plateau rather than a knife edge: 0.30 and 0.35 both pass and the two failures
sit on opposite sides. The last two rows have 17 checks because the auditory benchmark gained one
mid-battery when it moved to modality-based stimulus selection; escape and feeding are comparable
throughout.

**Transmitter confidence** (`fit/synapse_nt.py`). Over the 173,308 annotated neurons, mean
per-synapse confidence is 0.91; 1.2% of neurons fall below 0.6; neurons whose T-bars disagree with
their aggregate label carry 3.5% of total synaptic weight.

**Cord parameters** (`benchmarks/sensitivity_cord.py`). The sweep covered cord-only membrane time constant
(5 to 40 ms), threshold gap (4 to 10 mV) and refractory period (1 to 5 ms) across 19,912 nerve-cord
neurons. Every escape check passes at every setting except one. At a 10 mV threshold gap, the 9 mV
GF-to-TTMn spikelet is subthreshold, so the one-to-one relay and its lag fail: the TTMn/GF ratio is
0.23 and the lag 24.4 ms (rerun 11 October 2026 under 10 mV adaptation; 0.31 and 24.6 ms before). (Correction, 10 October 2026: this paragraph previously said "every metric
unchanged" and "14,153 neurons", contradicting the committed grid.) The escape result therefore
depends on the cord threshold staying within about 9 mV of rest.

---

**Stimulus-set integrity** (`fit/audit_stimuli.py`, run automatically by `scripts/run_all.py` and
`scripts/overnight.py`). Stimulus neurons are selected by exact type name, and MaleCNS splits many
populations into subtypes, so a correct-looking name can match nothing. That happened once: the
first DNg02 run selected "DNg02", which matches none of the 29 DNg02_a to _g cells, and those arms
ran without their input. The model now raises when a stimulus set matches no neurons and warns
when part of one does not, and every long run audits all sets first.

## 6. The declared parameter set

Shiu et al. 2024 LIF parameters (tau_m 20 ms, threshold -45 mV, rest and reset -52 mV, refractory
2.2 ms, synaptic tau 5 ms, delay 1.8 ms). Chemical kick 0.275 mV x 0.3, the rescale fitted on
MaleCNS by sweep. GF spike-triggered adaptation 30 mV, the smallest value satisfying von Reyn's
constraints in a pre-stated sweep at 40 trials (`benchmarks/fit_gf_adapt.py`; an intermediate 15 mV
came from a 20-trial fit whose binding constraint rested on about five trials, and the script now
warns below 40). Proboscis motor neuron adaptation 10 mV; relay motor neurons deliberately not
adapted, since TTMn follows GF one-to-one (Tanouye & Wyman 1980). Electrical synapses: GF-TTMn and
GF-PSI as 1:1 relays with a 9 mV spikelet at 0.8 ms, and JON-GF on the two JO-B1 subtypes that
actually contact GF, calibrated to a 3 mV compound potential. The 679 EM synapses annotated as
chemical on that contact are removed when the electrical model is on. Monoamines are sign 0 by
deliberate scope. Regional and class gains are all 1.0 and there is no tonic baseline.

Every value is either cited or fitted by a rule stated before the fit. Full list with citations:
`flycns/graph.py` and `REFERENCES.md`.

---

## 7. What was retracted

- **"Unilateral gustatory drive gives ipsilateral MN9 output, matching a 73 to 1 structural
  bias."** Reported in earlier versions and in commit messages from 8 September. The structural
  bias was an unsigned raw-synapse count whose large ipsilateral routes are net inhibitory once sign
  is included, and the dynamic confirmation ran under the since-retired SEZ gain. With sign and the
  identified sugar neurons, the bias is contralateral, as Shiu et al. predicted.
- **A regional SEZ gain of 2.0.** Fitted while the SEZ was defined by type-name prefixes, where it
  appeared to open the feeding pathway. Defining the SEZ from the connectome's own compartment
  annotations shows the population is net inhibitory onto that pathway under either definition, so
  MN9 stays silent at every gain. The parameter is now 1.0 and the effect is documented as an
  artefact of the naming heuristic.
- **A claim that auditory drive suppresses the GF loom response.** Withdrawn as gain-dependent:
  the direction depends entirely on where the loom sits relative to threshold, and across the
  robustness battery at 20 trials per arm the reading was facilitation four times, suppression
  twice and no change twice. The benchmark now calibrates a near-threshold working point and
  reports the difference with a confidence interval; at 40 trials per arm it is unresolved. That
  interval was itself computed wrongly until 25 September 2026 (the Newcombe bounds used crossed
  Wilson limits and an extra factor of 1.96, making each interval roughly twice too wide); the
  method is now verified against Newcombe's 1998 worked example. The registered test at 120 trials
  per arm then resolved it: sound FACILITATES the near-threshold loom response (+0.41, 95% CI +0.31
  to +0.50), directly contradicting the withdrawn suppression claim.
- **"The export is in a format machine-learning decoders can read."** Tested on 25 September 2026
  with the real `temporaldata` loader used by brainsets and POYO+: the files could not be read (no
  object-type attributes). The exporter now builds each session with temporaldata's own classes and
  reloads every file through `Data.from_hdf5` before accepting it.
- **A GF adaptation value of 15 mV**, withdrawn as an undersampled fit.
- **A plan to open the feeding pathway with cell-specific baselines from the literature**,
  withdrawn because the target neuron is not in the dataset.

---

## 8. What this does not claim

Single-neuron parameters are Shiu's central-brain values applied uniformly to brain and cord;
measured to be irrelevant for the escape benchmark, unexamined for circuits that need the cord to
compute. No parameter is fitted to a neural recording: only the stimulus is measured. Azevedo et
al. 2020 (eLife 9:e56754) give leg motor neuron input resistances of 150, 300 and 700 MOhm for
fast, intermediate and slow cells, and those numbers are recorded in `flycns/graph.py` but not
entered as parameters, because tau requires a capacitance the paper does not report, because
applying the gradient needs a fast/slow assignment for MaleCNS motor neurons that does not exist,
and because somatic current injection fails to evoke spikes in fast and intermediate motor neurons
(the spike initiation zone is electrically isolated), which a single-compartment cell cannot
represent at all. Modulatory transmitters are omitted, which is exactly what the feeding result
implicates. Gap junctions appear only where documented.

---

## 9. Relation to prior work

Model class, parameters and the feeding validation design: Shiu et al. 2024 (Nature 634:210-219).
Escape physiology: Tanouye & Wyman 1980, Allen et al. 2006, von Reyn et al. 2014 and 2017, Ache et
al. 2019, Augustin et al. 2019. Auditory-GF synapse: Pezier et al. 2014 and 2016, Yorozu et al. 2009,
Tootoonian et al. 2012, Kamikouchi et al. 2009, Vaughan et al. 2014. Loom tuning: Turner, Krieger,
Pang & Clandinin 2022. Peptidergic modulation: Krieger 2023. Transmitter prediction: Eckstein et
al. 2024.

What is added here: a test harness with numeric pass/fail criteria, null models and ablation arms;
one parameter set across circuits, with every chosen value and the checks it touches listed in
docs/CALIBRATION.md; a spiking sensory-to-motor
cascade across the neck connective on MaleCNS; measured stimulus tuning extracted from public
imaging and split by behavioural state; a perturbation targeted at the connectome's own
uncertainty; and mechanistic accounts of four circuits this model class cannot reproduce. Full
references: `REFERENCES.md`.
