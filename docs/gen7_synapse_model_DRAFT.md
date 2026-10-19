# Generation 7: change of synapse model (DRAFT plan, not registered)

Status: DRAFT, 18 October 2026. Not registered. Pre-registration for generation 7 happens in its own
registration, committed before any generation-7 run; until then this plan may be revised. **Its trigger has
fired:** phase A ended in outcome C (scored `c1e6e62`; no deciding cell viable; reproduced on Windows and by an
independent blind recompute), the registered trigger in `docs/gen6_phaseA_DRAFT.md` ("the next phase is a change
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
- **H7d (both):** conductance-based + STD gives a viable w where neither alone does.
- **H7e (AL presynaptic GABA_B):** a slow divisive depression of ORN -> PN efficacy driven by AL local-neuron
  activity removes the AL tail (A4-style reading), on top of the best of H7a-H7d.
- **H7f (AL gap junctions):** eLN-PN and sister PN-PN coupling restores the fly's main eLN -> PN route; reported
  for its effect on the AL tail and on cut (i)'s reading from phase A, not a viability arm.

"Viable", FUNCTION, FUNCTION-q, STABILITY (a), (b), (c), LATERALITY, the self-sustained rule, the sugar and
blind drives, the sweep protocol and the grid are **reused unchanged** from phase A's registered criteria.
Only the synapse model and its declared parameters change.

## Design (staged, with stop rules fixed in advance)

**Stage 1, the 2 x 2 core:** {current-based, conductance-based} x {no STD, STD}, everything else at the gen-6
settings (or phase A's adopted settings, if any), each swept over the w grid under sugar and blind drives.
Cell (current, no STD) replicates phase A's cell 1 (positive control for the replication).

**Stage 2, inside the conductance-based arms only:** E_i sweep {-55, -65, -75} mV x tau_i {5, 10} ms. Run only
the conductance-based arms of stage 1 that are not already viable.

**Stage 3, AL mechanisms (H7e, H7f):** on the best stage-1/2 arm, add AL presynaptic GABA_B; then AL gap
junctions. Scored with phase A's A4 readings (W*, "stops it").

**Stop rules:** a stage runs only if the previous stage leaves no viable deciding arm, except stage 3, which runs
in any case as mechanism reporting. Adoption follows phase A's B1 logic (smallest viable w, top-up rule,
LATERALITY -> H), with a fixed preference order fixed now: the simplest viable arm wins (fewest added
mechanisms; ties: current-based before conductance-based).

**Weight conversion (fixed in advance, so arm differences are not a rescaling):** a conductance per synapse
g_syn = w_syn_mV / (V_cal - E_syn), with V_cal = v_rest (-52 mV), so that one synapse gives the same initial
PSP at rest as in the current model (Cavallari et al. 2014 matching rule). With E_e = 0 mV and E_i = -65 mV this
gives an inhibitory conductance 4x the excitatory per synapse, by construction rather than by fit.

## Parameters (measured / modelled / assumed)

| parameter | value | status | source |
|---|---|---|---|
| E_e (nicotinic ACh) | 0 mV (sensitivity -10, +10) | measured in culture only: +8.9 +/- 1.7 mV (pupal), "0 mV" (embryonic); VERIFIED | Su & O'Dowd 2003; Lee et al. 2003 |
| E_i (GABA_A / GluCl / HisCl) | **-65 mV primary**, sweep -55 / -65 / -75 (open choice 1: add -45) | **assumed**: no adult in vivo measurement exists for any inhibitory transmitter. VERIFIED values are from cultured developing neurons only, GABA -37 +/- 3 (pupal) and -41.5 +/- 2.1 mV (embryonic; calculated E_Cl -45), and developing neurons tend to have high E_Cl. Larval VNC GABA -56 +/- 3 and glutamate (GluCl) -55 +/- 2 mV are UNVERIFIED (excerpt only; full text blocked). In vivo whole-cell values are pipette-imposed | Su & O'Dowd 2003; Lee et al. 2003; Rohrbough & Broadie 2002 (excerpt); models -70 (Nagel 2015; Huang 2018) |
| tau_e | 5 ms (sweep 2-5) | modelled: mEPSC half-decay about 2.1-2.5 ms in PNs in vivo; KC 5.2 ms in situ | Kazama & Wilson 2008; Gu & O'Dowd 2006 |
| tau_i (GABA_A) | 5 ms primary, 10 ms in stage 2 | measured in culture only (3.3-5.4 ms); no in vivo AL IPSC kinetics | Su & O'Dowd 2003; Lee et al. 2003 |
| STD | **primary: decrement U 0.22 (retained f 0.78), recovery tau_D 893 ms**; sensitivity U 0.28, tau_D 2.4 s. Model as in the sources: A -> f*A per spike, tau_D dA/dt = 1 - A. (The earlier placeholder U 0.3, tau_D 0.8 s was outside the measured range and is replaced.) Scope: H7c-in / H7c-all | primary (proposed; Jayson confirms): fit to evoked ORN -> PN EPSCs at 10 Hz, n = 19 PNs, in vivo, female (Nagel 2015 Fig 1c legend; VERIFIED by Grok; the legend is not in the PubMed text extract, whose own values, f 0.77 / tau 1006 ms for the fast component, do match). Sensitivity: Kazama & Wilson 2009 fit (alpha 0.72, tau 2.4 s; VERIFIED). On any synapse other than ORN -> PN / ORN -> LN: **assumed** (no data). Huang needed tau_D > 125 ms | Nagel 2015; Kazama & Wilson 2009; Nagel & Wilson 2016 (ORN -> LN f 0.75, tau 1566 ms); Huang 2018 |
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
- **V7a, primary: the ORN -> PN input-output curve.** Driving one glomerulus's ORNs at a set of rates, PN rate
  follows PN = R_max * ORN^1.5 / (ORN^1.5 + sigma^1.5) with R_max 165 spikes/s and sigma 12 spikes/s (Olsen,
  Bhandawat & Wilson 2010, Eq 1, fitted; VERIFIED). Near threshold PN rate is about 3x ORN rate (Jeanne & Wilson
  2015; VERIFIED). Direct (spike rates, same cell types). Caveats: the curve includes ORN -> PN depression, and it
  comes from the same lab as the STD values, so it is not fully independent of the primary STD parameters; and
  the glomeruli, the ORN rates and the tolerance must be fixed in the registration (open choice 6).
- **V7b, ordinal: MN9.** No MN9 firing rate has been recorded; the only measurement is calcium (Gordon & Scott
  2009). So only orderings are testable: sucrose > water (about 48% vs 2% dF/F); sucrose plus caffeine or
  denatonium is not different from water; 1 M sucrose gives about twice the 100 mM response; both MN9 somata
  respond (bilateral). Shiu et al. 2024's MN9 rates are model outputs, not data, and are not a target.
- **Not targets, and why:** spontaneous PN rate (1-9 spikes/s, Jeanne & Wilson 2015; Kazama & Wilson 2009)
  needs background activity the model does not have (basal rate 0 Hz, as Shiu); adding spontaneous ORN drive
  (about 1.5 Hz measured) would be a further model change. Whole-CNS rate: no fly whole-brain spike-rate
  measurement exists. **STABILITY (c)'s 1 Hz bar is therefore a judgment, not a measured value**, and is
  reported as such.

## Open choices for Jayson (before anything is registered)

1. Primary E_i: -65 mV (shunting-leaning, between larval VNC and the -70 used by fly models) or -70 mV (matches
   Nagel and Huang). New (18 Oct): the only VERIFIED fly values are -37 to -42 mV, in cultured developing
   neurons; the larval -55/-56 mV values are UNVERIFIED. Whether to extend the stage-2 sweep to include -45 mV, so
   the bracket covers the verified value as well as the model convention.
2. Whether stage 1 is a full 2 x 2 or STD alone first (cheaper; Huang predicts it is the decisive arm).
3. Whether the AL mechanisms (stage 3) run in gen 7 or wait for a viable core model.
4. Whether to fold the `"unclear"` fallback fix into the same freeze (declared and measured separately) or
   leave it for its own generation. **Size (18 October, read-only script on the pinned data, floor 5):**
   9,793 cells have consensusNt "unclear"; their predictedNt is unclear for 8,673, an amine for 404 (stay
   dropped), and signable for 716 (ACh 329, Glu 320, GABA 53, histamine 14). The fix adds 20,428 edges and
   253,733 synapses (about 0.3% of the signed graph): 111,043 excitatory, 142,690 inhibitory. AL -> AL goes from
   2,282,863 exc / 420,718 inh to 2,292,250 / 469,396 (inhibition +12%; excitatory share 84.4% -> 83.0%), so it
   does not by itself remove the AL loop. Caveat: these cells are signed from their per-cell prediction because
   the type-level consensus was unclear, the lower-confidence label. Recommendation: fold into the freeze,
   declared and measured as its own arm.
5. STD scope: whether H7c runs as H7c-in and H7c-all (two arms; separates weaker drive from limited recurrence),
   or H7c-all only (cheaper; cannot tell the two apart).
6. Validation: the glomeruli, ORN rates and tolerance for V7a; whether V7a/V7b are reported only or join
   viability.

## Not in this plan

Neuropeptides, neuromodulators (amines stay dropped), non-spiking neurons, dendritic compartments, temperature
correction (every in vivo kinetic value is at an unstated, presumably room, temperature).
