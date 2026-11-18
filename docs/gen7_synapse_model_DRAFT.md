# Generation 7: change of synapse model (DRAFT plan, not registered)

Status: DRAFT, 18 October 2026. Not registered. Pre-registration for generation 7 happens in its own
registration, committed before any generation-7 run; until then this plan may be revised. **Its trigger has
fired:** phase A ended in outcome C (scored `c1e6e62`; no deciding cell viable; confirmed by an independent
blind recompute), the registered trigger in `docs/gen6_phaseA_DRAFT.md` ("the next phase is a change
of synapse model (conductance-based), in its own plan"). Phase A adopted neither the reset nor the MN9_R
mirror, so the gen-6 settings (v-only reset, MN9_R as in the data) are the baseline below.
Sources: `docs/lit/synapse_model_lit_2026-10-18.md` (Grok, read-only literature review, 22 sources read in full)
and `docs/lit/gen7_lit_std_validation_2026-10-18.md` (Grok, second pass: STD, reversal potentials, validation
targets; spot-checked against PubMed full texts). Every value is tagged VERIFIED / VERIFIED-fig / INFERRED /
UNVERIFIED there. Only VERIFIED or VERIFIED-fig values are cited as measurements below; everything else is
labelled an assumption.

## Why this is a new generation

The synapse equations live in `flycns/model.py`, a hashed model file (`registry.MODEL_FILES`). Any change here
changes the simulator-model hash (`df7e16022378` for generations 5 and 6), so it is a refreeze: a new
`registry.VERSION` (6), new registrations for every benchmark that is rerun, and a refit of every calibration
chosen under the current synapse model (`docs/CALIBRATION.md`; the list is fixed in the gen-7 registration
before any refit). The two pending gen-6-freeze items ride along and are declared separately so their effect
can be read alone: the `"unclear"` transmitter fallback (`scripts/fetch_malecns.py` / `load_graph`) and the
`flycns/protocols.py` loom comment.

## What the current model is (and why it can run away)

`flycns/model.py`: `dv/dt = (v_rest + I_base - v + g + I_gap + g_shunt(v_rest - v) - a)/tau_m`,
`dg/dt = -g/tau_syn`, one current-like `g` (volts), `tau_syn` 5 ms shared by excitation and inhibition, no
reversal potentials, no slow inhibition, no short-term plasticity; gap junctions only for the declared
giant-fibre pairs. v_rest -52 mV, threshold -45 mV, tau_m 20 ms (Shiu et al. 2024). Phase 1b: outcome C; the
blind-drive tail sits inside the antennal lobe (AL -> AL 84% excitatory by synapse count; LH net inhibitory).

Three properties of this model each allow runaway (literature synthesis, INFERRED from VERIFIED quotes):
1. Current-based synapses: a PSP does not depend on v, so summed excitation is limited only by refractoriness
   (Brunel 2000, the "H state" near 1/tau_rp at g < 4).
2. Inhibition is subtractive and as fast as excitation (shared 5 ms). In the fly it is 2-3x slower for
   GABA_A (mIPSC decay 3.3-5.4 ms vs mEPSC 1.4-1.7 ms in the same culture preparation, Su & O'Dowd 2003;
   Lee et al. 2003) and about 200x slower for GABA_B (about 1-2 s, Wilson & Laurent 2005; Olsen & Wilson 2008).
3. No short-term depression, although ORN -> PN depresses strongly: release probability about 0.79 (Kazama &
   Wilson 2008), each spike leaves 72-78% of the next response, and recovery takes 0.9-2.4 s (Nagel et al. 2015;
   Kazama & Wilson 2009). ORN -> LN depresses similarly (f 0.75, tau 1.57 s; Nagel & Wilson 2016).

**The caution that shapes this plan (VERIFIED in the full text, Huang et al. 2018, Front Neuroinform,
doi:10.3389/fninf.2018.00099):** in a conductance-based LIF of the whole fly brain (FlyCircuit; reversals 0 and
-70 mV), raising the inhibition/excitation factor up to 100 "did not completely eliminate" seizure-like
activity, and "once the seizure-like activity occurred, it never stopped". Short-term depression in every
synapse brought prevalence to 50% or lower for recovery tau > 125 ms, but did not stabilise a randomized
brain. So conductance-based synapses alone are not expected to be enough; STD is an arm in its own right, not
a control.

## Hypotheses (registered as a set; each is a separate verdict)

- **H7a (driving force):** conductance-based synapses alone (E_e 0 mV, E_i at the primary value) give at
  least one w that is functional and stable. *Prediction: FAILS* (Huang 2018). Falsified if no w passes
  STABILITY at any E_i in the sweep.
- **H7b (slow inhibition):** separate time constants with tau_i > tau_e, on top of H7a, give a viable w.
- **H7c (short-term depression):** STD on every chemical synapse, on the CURRENT synapse model, gives a viable
  w. Tests whether depression alone is the missing mechanism, independent of conductances.
  - **The extrapolation, declared:** depression is measured only on the input synapses (ORN -> PN, ORN -> LN).
    No measurement exists for PN -> LN, LN -> PN or PN -> PN (searched; absent in every text read), the
    recurrent synapses phase A's cuts (i) and (ii) show sustain the loop. STD on them uses the ORN -> PN values
    as an assumption.
  - **The confound, designed out:** STD on the input alone could "stabilise" the network by weakening the drive,
    not by limiting recurrence. H7c is therefore split (open choice 5): **H7c-in**, STD on sensory-afferent
    synapses only; **H7c-all**, STD on every chemical synapse. If only H7c-all is viable, depression of the
    recurrent synapses is the operative mechanism (in the model; the extrapolation above applies).
  - **Scope, decided (Jayson, 18 Oct): H7c-in is primary and means the measured synapses only**, no
    extrapolation: presynaptic type starting `ORN_` (not `HRN_`) onto a postsynaptic type in the ALPN or ALLN
    list (`data/gen6_phaseA_celltypes.json`). These are exactly the ORN -> PN and ORN -> LN classes with
    measured depression. Gustatory, hygrosensory, other sensory and all central synapses stay undepressed in
    H7c-in. Consequence, stated in advance: the model has no spontaneous activity, so under the sugar drive
    (no ORN driven) ORN synapses act only if ORNs fire through recurrent input; the number of ORN spikes per
    sugar trial is reported. Otherwise H7c-in's sugar arms equal the no-STD arms', and H7c-in acts only on the
    blind drive's olfactory share. H7c-all stays as the secondary, explicitly extrapolating arm,
    reported, so the two readings above can be told apart.
- **H7d (both):** conductance-based + STD gives a viable w where neither alone does.
- **H7e (AL presynaptic GABA_B), deferred to generation 8 (decided 18 Oct):** a slow divisive depression of ORN -> PN efficacy driven by AL local-neuron
  activity removes the AL tail (A4-style reading), on top of the best of H7a-H7d.
- **H7f (AL gap junctions), deferred to generation 8 (decided 18 Oct):** eLN-PN and sister PN-PN coupling restores the fly's main eLN -> PN route; reported
  for its effect on the AL tail and on cut (i)'s reading from phase A, not a viability arm.

"Viable", FUNCTION, FUNCTION-q, STABILITY (a), (b), (c), LATERALITY, the self-sustained rule, the sugar and
blind drives, the sweep protocol and the grid are **reused unchanged** from phase A's registered criteria.
Only the synapse model and its declared parameters change.

## Design (staged, with stop rules fixed in advance)

**Stage 1, the core, all under one registration (decided 18 Oct):** {current-based, conductance-based} x
{no STD, STD-in, STD-all}, everything else at the gen-6 settings (v-only reset, MN9_R as in the data), each swept
over the w grid under sugar and blind drives. No arm of stage 1 is gated on another: all six run, and every
verdict is registered in advance. Prediction written now (from Huang 2018): conductance-based without STD fails;
an STD arm is the first viable one, if any is.
- **Baselines for the `"unclear"` fix (decided: fold it in):** cell (current, no STD) runs twice, without the
  fix (replicates phase A's cell 1; positive control) and with it (isolates the fix). Every other stage-1 arm
  runs with the fix, so its difference from the with-fix baseline is the synapse change alone.

**Stage 2, inside the conductance-based arms only:** E_i sweep {-55, -70, -80} mV x tau_i {5, 10} ms. Run only
the conductance-based arms of stage 1 that are not already viable.

**Stage 3, AL mechanisms (H7e, H7f): not in generation 7** (decided 18 Oct). Adding them here would mix a
second change into the synapse comparison. They move to generation 8, on gen 7's outcome.

**Stop rules:** stage 2 runs only if stage 1 leaves no viable deciding arm. Adoption follows phase A's B1 logic
(smallest viable w, top-up rule, LATERALITY -> H), with a preference order fixed now: the simplest viable arm
wins (fewest added mechanisms; ties: current-based before conductance-based, STD-in before STD-all, because
STD-in uses measured synapses only).

**Weight conversion (fixed in advance, so arm differences are not a rescaling):** a conductance per synapse
g_syn = w_syn_mV / (V_cal - E_syn), with V_cal = v_rest (-52 mV), so that one synapse gives the same initial
PSP at rest as in the current model (Cavallari et al. 2014 matching rule). With E_e = 0 mV and E_i = -70 mV this
gives an inhibitory conductance about 2.9x the excitatory per synapse (52 / 18), by construction rather than by
fit. Across the E_i sweep the PSP at rest is matched; what differs is how inhibition scales as a cell
depolarizes, which is the variable under test.

## Parameters (measured / modelled / assumed)

| parameter | value | status | source |
|---|---|---|---|
| E_e (nicotinic ACh) | 0 mV (sensitivity -10, +10) | measured in culture only: +8.9 +/- 1.7 mV (pupal), "0 mV" (embryonic); VERIFIED | Su & O'Dowd 2003; Lee et al. 2003 |
| E_i (GABA_A / GluCl / HisCl) | **-70 mV primary, sweep -55 / -70 / -80** (decided 18 Oct). No -45 arm: at or above threshold (-45) inhibition depolarizes from rest (-52), a different question (depolarizing GABA), left for its own test. -70 is chosen for comparability, not from adult data: it is the value of Huang et al. 2018, whose result H7a's prediction rests on, and of Nagel et al. 2015's AL model. The culture values below sit above threshold in this model and cannot be used as they are | **assumed**: no adult in vivo measurement exists for any inhibitory transmitter. VERIFIED values are from cultured developing neurons only, GABA -37 +/- 3 (pupal) and -41.5 +/- 2.1 mV (embryonic; calculated E_Cl -45), and developing neurons tend to have high E_Cl. Larval VNC GABA -56 +/- 3 and glutamate (GluCl) -55 +/- 2 mV are UNVERIFIED (excerpt only; full text blocked). In vivo whole-cell values are pipette-imposed | Su & O'Dowd 2003; Lee et al. 2003; Rohrbough & Broadie 2002 (excerpt); models -70 (Nagel 2015; Huang 2018) |
| tau_e | 5 ms (sweep 2-5) | modelled: mEPSC half-decay about 2.1-2.5 ms in PNs in vivo; KC 5.2 ms in situ | Kazama & Wilson 2008; Gu & O'Dowd 2006 |
| tau_i (GABA_A) | 5 ms primary, 10 ms in stage 2 | measured in culture only (3.3-5.4 ms); no in vivo AL IPSC kinetics | Su & O'Dowd 2003; Lee et al. 2003 |
| STD | **primary: decrement U 0.22 (retained f 0.78), recovery tau_D 893 ms**; sensitivity U 0.28, tau_D 2.4 s. Model as in the sources: A -> f*A per spike, tau_D dA/dt = 1 - A. (The earlier placeholder U 0.3, tau_D 0.8 s was outside the measured range and is replaced.) Scope: H7c-in = ORN_ -> ALPN/ALLN only (primary); H7c-all = every chemical synapse (secondary, extrapolated) | primary: fit to evoked ORN -> PN EPSCs at 10 Hz, n = 19 PNs from 19 flies, DM6 or VM2, in vivo, female (Nagel 2015 Fig 1c legend, quoted verbatim in `docs/lit/v7a_nagel_check_2026-10-18.md`; VERIFIED). Sensitivity conditions: DM4, 4 Hz minimal stimulation of one ORN axon, n = 3, female 2-5 d (Kazama & Wilson 2009 Supp Fig 2; VERIFIED). **Implementation, fixed now:** the synaptic weight is scaled by A (w_eff = w x A, A = 1 at rest), exactly as in both papers, with no Tsodyks-Markram U factor on the amplitude and no facilitation. So the first PSP after rest equals the current model's, and only the train dynamics change. U = 1 - f is a depletion fraction, not a release probability (measured p is 0.79, Kazama & Wilson 2008). Sensitivity: Kazama & Wilson 2009 fit (alpha 0.72, tau 2.4 s; VERIFIED). On any synapse other than ORN -> PN / ORN -> LN: **assumed** (no data). Huang needed tau_D > 125 ms | Nagel 2015; Kazama & Wilson 2009; Nagel & Wilson 2016 (ORN -> LN f 0.75, tau 1566 ms); Huang 2018 |
| GABA_B (AL, presynaptic) | divisive on ORN -> PN efficacy, onset alpha tau 25 ms, decay 1 s, driven by AL LN spikes; none on LNs | modelled from in vivo pharmacology | Olsen & Wilson 2008; Nagel 2015; Wilson & Laurent 2005; Root et al. 2008 |
| AL gap junctions | g_gap / g_L 0.02 for sister PN-PN and eLN-PN (eLN = cholinergic ALLN types, INFERRED mapping) | modelled from coupling coefficients 0.003-0.034, which are lower bounds | Yaksi & Wilson 2010; Kazama & Wilson 2009 |
| v_rest, threshold, tau_m | unchanged (-52, -45 mV, 20 ms) | modelled (Shiu); PN rest in vivo -55 to -60 mV is noted, not adopted, so only the synapse model changes | Gouwens & Wilson 2009 |

Two numerics risks are designed out in advance: the GABA driving-force artefact Huang 2018 hit (v pushed below
E_i makes inhibition depolarizing) is avoided because conductances cannot drive v past E_i; it is checked by
asserting v >= E_i - 1 mV in a smoke run. Integration stays Euler at dt 0.1 ms with the existing dt 0.05 ms
numerics check.

## Validation against measured data (new in gen 7; criterion fixed in the registration, before any run)

Phase A's criteria test the model against itself (function, stability, laterality). Gen 7 adds one check against
recorded physiology, scored but not part of viability (open choice 6 decides whether it should be). Targets,
from `docs/lit/gen7_lit_std_validation_2026-10-18.md`, ranked by how directly they map onto a model readout:
- **V7a, primary, report-only in generation 7 (decided 18 Oct): the ORN -> PN input-output curve.** Driving one glomerulus's ORNs at a set of rates, PN rate
  follows PN = R_max * ORN^1.5 / (ORN^1.5 + sigma^1.5), **fitted per glomerulus** (Olsen, Bhandawat & Wilson
  2010, Methods; VERIFIED): R_max 170, 167, 163, 144 and sigma 16.3, 11.8, 12.4, 44.8 spikes/s for DM4, DL5, VM7
  and DM1. (165 / 12 are the paper's simulation defaults, not a fit, and are not used.) DM1's large sigma comes
  from GABA (it reverts with picrotoxin + CGP54626); the model has inhibition, so the control fit is the
  comparison. Measured input range: baseline-subtracted ORN rate about 0-125 spikes/s over a 500 ms odor; points
  are means of 6-12 recordings; ORNs and PNs were recorded separately. No goodness of fit or residual scatter is
  reported for these fits, so the tolerance cannot be taken from the paper; the only empirical scatter scale is
  Bhandawat et al. 2007 / Kazama & Wilson 2008 Fig 9A (VM2: PN about 64-118 Hz around a plateau of about 90 Hz,
  VERIFIED-fig). Near threshold PN rate is about 3x ORN rate (Jeanne & Wilson
  2015, DA1, ChR2 near threshold, ORN about 2-22 Hz, **recorded in males**; VERIFIED). Direct (spike rates, same cell types). Caveats: the curve includes ORN -> PN depression, and it
  comes from the same lab as the STD values, so it is not fully independent of the primary STD parameters; and
  the glomeruli, the ORN rates and the tolerance must be fixed in the registration. Glomeruli: DM4, DL5, VM7 and
  DM1, the four in Olsen et al. 2010 Fig 1B (VERIFIED-fig). It joins viability in a later generation, once a
  tolerance has been fixed in advance and seen once.
- **V7b, ordinal: MN9.** No MN9 firing rate has been recorded; the only measurement is calcium (Gordon & Scott
  2009). So only orderings are testable: sucrose > water (about 48% vs 2% dF/F); sucrose plus caffeine or
  denatonium is not different from water; 1 M sucrose gives about twice the 100 mM response; both MN9 somata
  respond (bilateral). Shiu et al. 2024's MN9 rates are model outputs, not data, and are not a target.
- **Not targets, and why:** spontaneous PN rate (1-9 spikes/s, Jeanne & Wilson 2015; Kazama & Wilson 2009)
  needs background activity the model does not have (basal rate 0 Hz, as Shiu); adding spontaneous ORN drive
  (about 1.5 Hz measured) would be a further model change. Whole-CNS rate: no fly whole-brain spike-rate
  measurement exists. **STABILITY (c)'s 1 Hz bar is therefore a judgment, not a measured value**, and is
  reported as such.

## Decided (Jayson, 18 October), and what is still open

**Decided:**
1. E_i primary -70 mV, sweep -55 / -70 / -80 mV, no -45 mV arm.
2. Stage 1 as one full registration (no gating inside it): 2 synapse models x 3 STD settings.
3. Stage 3 (AL GABA_B, AL gap junctions) deferred to generation 8.
4. The `"unclear"` fix is folded in, with paired current/no-STD baselines (with and without the fix). Size
   (18 October, read-only script on the pinned data, floor 5): 9,793 cells have consensusNt "unclear"; their
   predictedNt is unclear for 8,673, an amine for 404 (stay dropped), and signable for 716 (ACh 329, Glu 320,
   GABA 53, histamine 14). The fix adds 20,428 edges and 253,733 synapses (about 0.3% of the signed graph):
   111,043 excitatory, 142,690 inhibitory. AL -> AL goes from 2,282,863 exc / 420,718 inh to 2,292,250 /
   469,396 (inhibition +12%; excitatory share 84.4% -> 83.0%). Caveat: these cells are signed from their per-cell
   prediction because the type-level consensus was unclear, the lower-confidence label.
5. STD scope: H7c-in (ORN_ -> ALPN/ALLN, the measured synapses only) primary; H7c-all secondary.
6. V7a report-only in generation 7, on DM4 / DL5 / VM7 / DM1.

**Decided (Jayson, 18 Nov):**
- V7a tolerance, report-only: per glomerulus, fit the model's own R_max and sigma (exponent fixed at 1.5, as
  Olsen) to its PN rate against the driven ORN rate; "consistent" if R_max is within +/-25% and sigma within a
  factor of 2 of Olsen's fitted values for that glomerulus. The model's PN rate at each driven ORN rate is also
  reported next to Olsen's Fig 1B points (VERIFIED-fig), with no verdict attached.

**Proposed (Claude, 18 Nov; Jayson to confirm):**
- V7a drive: ORN rates 5, 10, 20, 40, 80 and 120 spikes/s (inside Olsen's measured range of about 0-125), each
  as a 500 ms Poisson drive of every cell of the ORN type, PN rate over the same 500 ms, as in the paper.

**Still open (fix before registering):**
- Anything the pre-registration audit (Grok, requested 18 Nov) finds.
- (Resolved 18 Oct: the STD primary's figure legend is quoted verbatim; f 0.78 / 893 ms stays.)
- Code (18 Nov, branch `gen7/model-code`, not registered): `SimOptions.synapse`, `SimOptions.std`,
  `load_graph(unclear=...)`, all off by default; the arms script and scorer are not written yet.
- V7a model mapping, from `docs/lit/v7a_mn9r_check_2026-11-13.md` (MaleCNS Explorer @ 789cc6c and the v1.0
  release tables; VERIFIED there). Drive every cell of the ORN type at the target rate (the real ORN count,
  both sides) and read the listed PN type:

  | Olsen 2010 | ORN type (cells) | PN read (cells) | not read, reported |
  |---|---|---|---|
  | DM4 | `ORN_DM4` (32) | `DM4_adPN` (2) | `DM4_vPN` (2): GABAergic, driven mainly by DM4_adPN |
  | DL5 | `ORN_DL5` (43) | `DL5_adPN` (2) | |
  | VM7 | `ORN_VM7d` (36) (open: see below) | `VM7d_adPN` (7) | `ORN_VM7v` (25) -> `VM7v_adPN` (3) |
  | DM1 | `ORN_DM1` (74) | `DM1_lPN` (2) | |

  - **VM7 is split in MaleCNS** (VM7d, VM7v); Olsen et al. 2010 report one "VM7", driven with 2-butanone.
    **Decided (Jayson, 18 Nov): VM7d is the comparison, VM7v is reported**, on the reading that Olsen's VM7 is the
    Or42a glomerulus (VM7d = Or42a from the hemibrain table, not re-verified; INFERRED).
  - Only cholinergic uniglomerular PNs are read: Olsen's curve is for excitatory PNs. `DM4_vPN` is GABAergic.
  - Known impurities, stated, not corrected: ORN_DL2v supplies 5.3% of DM4_adPN's input; multiglomerular PNs
    that take the same ORN input are not read; 1 body each of ORN_DM4 and ORN_DL5 has no side; 2, 1, 2 and 2
    ORN bodies (DM4, DL5, VM7v, DM1) are labelled "RT Hard to trace".

## Not in this plan

AL presynaptic GABA_B and AL gap junctions (generation 8). Neuropeptides, neuromodulators (amines stay dropped), non-spiking neurons, dendritic compartments, temperature
correction (every in vivo kinetic value is at an unstated, presumably room, temperature).

## Definitions fixed before registering (these win over anything above)

Written 18 November 2026 in answer to the pre-registration audit (`docs/lit/gen7_prereg_audit_2026-11-18.md`,
74 findings, 14 blockers; finding numbers in brackets). Where this section and the text above disagree, this
section is the plan. Items marked **(proposed)** are Claude's and wait for Jayson's yes; everything else follows
from decisions already made.

### D1. What is inherited, pinned [F7, F13, F25, F27, F28]
- Criteria: FUNCTION (screen), FUNCTION-q, STABILITY (a), (b), (c), LATERALITY, the self-sustained rule, the
  sugar and blind drives, the sweep protocol (10 trials, 1,000 ms drive, 500 ms tail, restore between trials),
  the grid w 0.4 / 0.5 / 0.6 / 0.8 / 1.0 and the thresholds (responds 0.5 Hz, rate bar 1.0 Hz, fraction bar
  0.10, li bar 0.8), exactly as in `results/gen6_phaseA/registration_v5.json` (git `ff816c1`).
- Intervals: percentile bootstrap over trials, 2,000 resamples, seed 0 (`docs/gen6_rule.md`), also for pooled
  top-ups.
- Cell types: `data/gen6_phaseA_celltypes.json`, sha256 `ea8bad7d...`, from the MaleCNS Cell Type Explorer @
  `789cc6c`. ORN types are taken from `neurons.parquet`'s `type` column by exact name. Connectome: MaleCNS v1.0,
  as pinned by `data/MANIFEST.json`.
- Scorer readings: those of `fit/gen6_phaseA_score.py`, with the two points the blind scorer read differently
  fixed here: a top-up counts only if both drives of that (arm, w) were topped up, otherwise scoring is refused;
  while a named top-up is missing the outcome is PROVISIONAL, never final.
- The refreeze is compared against the simulator hash `df7e16022378` (generations 5 and 6).

### D2. Arms [F1, F3, F4, F11, F15, F26, F46]
Every arm is a sweep: 5 w x {sugar, blind} x 10 trials, v-only reset, MN9_R as in the data.

| arm | synapse | STD | "unclear" fix | role |
|---|---|---|---|---|
| P0 | current | none | off | positive control: replicates phase A's c1 |
| B | current | none | on | baseline for every comparison |
| S-in | current | in | on | **deciding** |
| C | conductance | none | on | **deciding** |
| CS-in | conductance | in | on | **deciding** |
| S-al, CS-al | current / conductance | AL | on | reported **(proposed)** |
| S-all, CS-all | current / conductance | all | on | reported **(proposed: never adopted)** |
| sensitivity | C and CS-in at E_i -55, at E_i -80, and at tau_i 10 ms; S-in and CS-in at f 0.72 / tau 2.4 s | | on | reported **(proposed: always run, never adopted)** |

- **STD scopes.** "in": presynaptic type starts `ORN_`, postsynaptic type in the ALPN or ALLN list (the two
  synapse classes with measured depression). "AL" **(proposed)**: presynaptic type starts `ORN_` or is in the
  ALPN or ALLN list, postsynaptic type in the ALPN or ALLN list; it adds the antennal-lobe recurrent synapses
  phase A's cuts point to, and nothing else. "all": every chemical synapse. "AL" and "all" extrapolate the
  ORN -> PN values to synapses with no measurement; that is why they are reported and cannot be adopted.
- **Replaces stages 1 and 2 above.** There is no conditional stage: every arm in the table runs under one
  registration. The E_i and tau_i variants are sensitivity arms, so H7a can be scored at every E_i. E_e +/-10 mV
  and tau_e 2 ms are **not run** in generation 7.
- 17 arm sets, 170 sweep arms (phase A had 60 sweep arms and 35 others).

### D3. Outcome, in this order [F1, F2, F3, F8, F60, F61, F62]
1. **R (stop for review).** P0's per-w component verdicts and self-sustained counts differ from phase A's c1
   (`results/gen6_phaseA/phaseA.json`). P0 uses phase A's seeds and the default code path, so they should be
   identical. Nothing is adopted.
2. **F (the fix alone).** B is viable. Candidate: the fix, at B's smallest viable w.
3. Otherwise the first viable arm in the order **S-in, C, CS-in** is the candidate, at its own smallest viable
   w. The order is by arm first, then by w within the arm.
4. **C7 (none).** No deciding arm is viable. The reported arms then say where a mechanism would have to act:
   whether S-al / CS-al or S-all / CS-all are viable is stated, with the label "extrapolated". Generation 8
   takes the antennal-lobe mechanisms (H7e, H7f), in its own plan.
- "Viable" is phase A's: FUNCTION, FUNCTION-q and STABILITY (a), (b), (c) all PASS at the same w.
- **LATERALITY is reported for every arm and gates nothing** in generation 7: no arm adopts the MN9_R
  correction, and MN9_R is labelled "RT Hard to trace" in the release.
- A candidate is **provisional**. It becomes the model's default only after a confirm step in its own
  registration (fresh seeds, both nulls, a specificity test as phase A's A3) and after the calibrations listed in
  `docs/CALIBRATION.md` are refit under it. **No calibration is refit before or during generation 7** [F10, F22,
  F45]: every arm uses the generation-6 values, and the grid w is `w_scale` itself.
- Top-ups: as phase A (an UNRESOLVED component at a w that could become a deciding arm's decision w names 10
  more trials of both drives at that (arm, w)); deciding arms only.

### D4. Hypotheses, verdicts and predictions [F54-F58, F19]
Verdicts are *held*, *not held*, or *undetermined* (a named top-up is missing, or outcome R).

| | claim | scored on | prediction **(proposed)** | confidence |
|---|---|---|---|---|
| H7-P | P0 replicates phase A's c1 | D3.1 | held | high |
| H7-F | the fix alone gives a viable w | B | not held | high |
| H7a | conductance-based synapses alone give a viable w | C (primary); the E_i variants are reported beside it | not held | moderate |
| H7b | slower inhibition (tau_i 10 ms) gives a viable w where 5 ms does not | C at tau_i 10 vs C | not held | moderate |
| H7c-in | depression of the ORN input synapses alone gives a viable w | S-in | not held | high |
| H7d | conductance-based with input depression gives a viable w where neither C nor S-in does | CS-in, C, S-in | not held | moderate |
| H7c-al | (reported) depression of the antennal-lobe synapses gives a viable w | S-al, CS-al | held for at least one | low |
| H7c-all | (reported) depression of every synapse gives a viable w | S-all, CS-all | held for at least one | low |
| overall | the outcome | D3 | C7 | moderate |

Why S-in is predicted to fail: under the sugar drive no ORN is driven, and phase A placed the loop in the
antennal lobe's own recurrent synapses, which S-in does not touch. The arm is still the primary one, because it
is the only depression arm that uses measured synapses only.
- "H7c" alone has no verdict; H7c-in, H7c-al and H7c-all do.
- This is an uncorrected screen, as phase A's M6 [F18].

### D5. The synapse model, as implemented [F9, F14, F47-F52]
(`flycns/model.py` on `gen7/model-code`; unit test "gen-7 synapse options".)
- Weights. The kick per connection is w_mV = n_synapses x 0.275 mV x w x gain, signed. Current-based: g += w_mV.
  Conductance-based: ge += w_mV / (E_e - V_rest) for w_mV > 0, gi += |w_mV| / (V_rest - E_i) for w_mV < 0 (both
  positive). ge decays with tau_syn (5 ms), gi with tau_i.
- The stimulus sources' synapses follow the same rule as the recurrent ones. Electrical coupling is unchanged.
- Depression is per connection (pre -> post pair), on recurrent and stimulus-source synapses alike. A spike is
  delivered with w x A, **then** A -> f x A; A recovers to 1 with tau_D. A is advanced at delivery; every
  chemical synapse has the same delay, so the values equal those at the spike. The per-trial restore returns A
  to 1.
- **What co-varies, stated:** across E_i the PSP at rest is matched, so the inhibitory conductance per synapse
  is 17.3x, 2.9x and 1.9x the excitatory at E_i -55, -70 and -80 (shunting changes with E_i). At tau_i 10 ms
  the peak is matched and the inhibitory charge is about doubled. Any depression lowers the mean weight as well
  as changing its dynamics. S-all and CS-all also depress the sugar -> MN9 pathway. So each arm's component
  verdicts (FUNCTION, FUNCTION-q, STABILITY a, b, c) are reported separately, and a non-viable arm is read by
  which component failed.
- The self-sustained test is read as in phase A in every arm; with tau_D 893 ms, A has not recovered by the
  end of the 500 ms tail. That is the model under test, not a correction to make.

### D6. Fail-safes [F16, F17, F51, F63, F64, F65]
- A missing or crashed arm refuses scoring. A deciding arm cannot PASS on missing data.
- Numerics: every conductance arm records the lowest v reached by any cell. Below E_i - 1 mV, the arm's
  STABILITY is FAIL (flag NUMERICS). The candidate's sweep at its decision w is repeated at dt 0.05 ms; if a
  component verdict differs, the candidate is flagged numerics-sensitive and stays provisional.
- The fix is applied in `load_graph` to the pinned edges (already at the 5-synapse floor). The simulated cell
  count is recorded with and without it; each arm's rates use its own cell count.
- Per sugar trial of S-in and CS-in, the number of spikes of `ORN_` cells is recorded (mean per w reported). If
  it is zero, S-in's sugar arms must equal B's exactly; that is checked and reported.
- Seeds: 6000 + index(drive, w), phase A's, in every sweep arm, so all arms are paired with each other and with
  phase A. Top-ups 7000 + index. V7a 9000 + index.
- Process, as phase A: the arms script and the scorer are hashed into the registration; toy-data smoke tests; a
  preflight on the pinned data committed before registering (it also reproduces the fix's sizes, which until
  then rest on an uncommitted script [F44]); an independent blind recompute before the write-up.

### D7. Validation [F5, F6, F42, F69-F74]
- **V7a, report-only.** Arms B, S-in, C, CS-in, S-all, CS-all, at each grid w. For each glomerulus in the
  mapping table above: every simulated cell of the ORN type becomes a Poisson source at 5, 10, 20, 40, 80 and
  120 spikes/s **(proposed)** for 500 ms, 2 trials; the readout is the mean rate of the PN type's cells over the
  same 500 ms, mean of the trials (the model's rate before the drive is 0). R_max and sigma are fitted with the
  exponent fixed at 1.5. "Consistent" per glomerulus: R_max within +/-25% and sigma within a factor of 2 of
  Olsen's fit. Reported: the count of consistent glomeruli per (arm, w), the fits, and the rates beside Olsen's
  points. No verdict enters the outcome. The driven count is the simulated count; side-unknown ORNs are driven
  with the rest.
- **V7b is not run in generation 7 (proposed).** The model has no water, bitter or concentration stimulus, and
  a mapping from sugar concentration to receptor-neuron rate would be an assumption. The bilateral item cannot
  be read while MN9_R is under-reconstructed.
- Also reported per arm, with no verdict: the antennal-lobe share of the blind tail (phase A's M9 measure) and
  the by-mode summaries of phase A [F67, F68].

### D8. Corrections to the text above [F29-F44]
- V7a's numbers come from `docs/lit/v7a_nagel_check_2026-10-18.md`; the "165 / 12, fitted" lines in
  `gen7_lit_std_validation_2026-10-18.md` are superseded.
- "ORNs and PNs were recorded separately" is INFERRED (the supplement was not obtained). "No goodness of fit is
  reported" holds for the main text; the supplement was not read.
- "Recovery takes 0.9-2.4 s" means recovery time constants of 0.9-2.4 s.
- mIPSC decay 3.3-5.4 ms spans two culture preparations; only Su & O'Dowd 2003 measured both mEPSC and mIPSC.
- "No MN9 firing rate has been recorded" and "no whole-brain spike rate exists" are search results ("none
  found"), not established absences. The 1.5 Hz ORN rate is DA1's.

