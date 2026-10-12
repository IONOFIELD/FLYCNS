# Calibration ledger

A check that a parameter was tuned to pass is not evidence that the model is right. It only shows
that the tuning worked. This file lists every value in the model that was chosen rather than
taken from a measurement, together with the rule it was chosen by and the checks it therefore
stops from counting as tests.

`flycns/calibration.py` holds the same classification in code. `benchmarks/summarize.py` prints
the role beside every result in `results/SUITE.md` and counts only **independent** checks as tests
of the model. CI fails if a scored check has no role.

| role | meaning |
|---|---|
| calibrated | a free parameter was chosen, at least partly, to make this check pass |
| construction | guaranteed by a parameter entered from the same measurement the check cites |
| independent | not a target of any fit; a genuine test (pre-registered where marked) |
| control | a null model, ablation or positive control; shows the machinery is not trivial |
| robustness | re-tests a result under perturbation |
| structural | a count over the wiring graph with no simulation; evidence about the connectome, not the dynamics |

---

## Chosen values

| value | where | how it was chosen | checks it touches |
|---|---|---|---|
| **w_scale = 0.4** (global synaptic scale; 0.275 mV × 0.4 = 0.11 mV per synapse; 0.3 until 11 October 2026) | `flycns/model.py` | **Chosen by a registered rule blind to every benchmark** (`fit/select_wscale.py`; the script wrote its criterion to `results/select_wscale/criteria.json` before running and refuses to run against different criteria; the file was committed with the first report, 11 October 2026): under a random 10% of the sensory neurons no benchmark drives, at 20 Hz, the largest grid value with whole-CNS rate < 1 Hz and < 10% of neurons active. The network stays quiet from 0.15 to 0.4 (0.4: 0.015 Hz) and runs away between 0.4 and 0.5 (2.5 Hz at 0.5), so the rule picks 0.4. Adopted on 11 October 2026 (registration generation 3) because it is the only value with a derivation anyone can rerun. The earlier 0.3 came from a September sweep over {1.0, 0.5, 0.25} that does not contain 0.3 and partly looked at the giant fiber. **Not a measured constant:** the one measured per-synapse anchor found, ORN → PN (about 5 mV per unitary EPSP, Kazama & Wilson 2008, over about 23 EM synapses, Tobin et al. 2017, so about 0.22 mV per synapse), is about 12 times the model's peak PSP per synapse at 0.4 (0.017 mV; about 17 times at 0.3). Matching it would need w_scale ≈ 5, far into the runaway regime. Shiu et al. 2024's own 0.275 mV was fitted to a behaviour (sugar → MN9), not measured. The global scale therefore stands in for missing biology (per-class input resistance, amines, spontaneous background). **Risk:** 0.4 sits one grid step below the transition; the robustness battery runs the core suite at 0.30, 0.35 and 0.45 so a result that holds only next to the transition shows. | escape `cns_quiet`, auditory `A5_cns_quiet` and feeding `F2b_extra_SEZ_quiet` are **calibrated** (the rule picks the largest quiet value). The rule sees no benchmark circuit, so the escape circuit is no longer part of the choice. |
| **PEAK_HZ = 5.0** (dF/F to spike-rate scale of the loom stimulus) | `flycns/protocols.py` | Anchored so the giant fiber fires 1 to 2 spikes with P(response) ≥ 0.5 (von Reyn et al. 2014). No recording links glomerulus dF/F to spike rate, so this is the stimulus's one free scale. | escape `gf_spikes_per_response_1_to_2` and `gf_response_prob_0.5_to_1` are **calibrated** |
| **GF adaptation b_adapt = 45 mV** (10 mV at w_scale 0.3, 10 October 2026; 30 mV before) | `flycns/graph.py` INTRINSIC_OVERRIDES | `benchmarks/fit_gf_adapt.py`: the smallest value giving 1 to 2 spikes per response, ≤ 2 on the strongest gain quartile, P(response) 0.5 to 1, and an intact TTMn relay | same two escape checks (**calibrated**) |
| **GF→TTMn, GF→PSI spikelet 9 mV, delay 0.8 ms** | `flycns/graph.py` ELECTRICAL_SYNAPSES, `model.py` | Physiological constraint: a 1:1 relay at about 0.8 ms (Tanouye & Wyman 1980). The spikelet is set just above the 7 mV distance from rest to threshold. | escape `ttmn_one_to_one` and `ttmn_lag_0.5_1.5ms` hold **by construction** |
| **JON→GF compound potential 3 mV at 150 Hz** | `flycns/graph.py` | Chosen to keep sound alone subthreshold, as recorded. **The 3 mV value has not been traced to a source figure.** | auditory `A1_jo_alone_mostly_subthreshold` is **calibrated** |
| **G_GAP_RELAY = 0.2** (ohmic coupling, as a fraction of leak) | `flycns/graph.py` | Set by hand for a 1:1 relay pair and shared across population pairs | none scored directly |
| **cb_motor adaptation 10 mV** | `flycns/graph.py` INTRINSIC_OVERRIDES | Keeps sustained motor rates under 100 Hz (Azevedo et al. 2020, McKellar et al. 2020) | feeding `F2c_motor_rate_physiological` holds **by construction** |
| **flight afferent load 0.25** | `benchmarks/flight_loop.py` | The smallest load putting mean DVMn 1a-c in 2 to 12 Hz | flight `L1a_DVMn_2_to_12_hz` is **calibrated** |
| **A2 working point** (loom gain per run; 0.6 in run 14, generation 3; 0.8 in run 12) | `benchmarks/auditory.py` | Pre-registered protocol: the largest loom gain leaving loom-alone GF response ≤ 0.3, with at least 2 mV depolarisation. It sets "near threshold". It does not target facilitation. The earlier gain fits (`benchmarks/fit_gains.py`, `benchmarks/fit_regional.py`) did score an A2 facilitation criterion while selecting gains; no parameter moved. Since 11 October 2026 (later) the calibration arms draw seeds disjoint from the scored arms (BASE_SEED + 1000 + gain index), and the two scored arms draw different seeds; before, the calibration arm at the chosen gain was bit-identical to the scored loom-alone arm. | `A2R_facilitation` is **construction** (see below). The report now also gives the facilitation that summation alone predicts, and the residual beyond it. |
| SEZ regional gain | `flycns/graph.py` | Fitted to 2.0 under an earlier region definition, then **disabled (1.0)** on 2026-09-08 | none |
| peptide modulation, tonic baseline | `flycns/model.py` | **Off** in the declared parameter set | none |

**Loom input, corrected 10 October 2026.** The documentation said the loom stimulus used the
stationary-trial amplitudes. In fact the committed data file had no per-state split, so the code
silently used all trials (LC4 0.595 instead of 0.52, sigma 0.369 instead of 0.357). The file now
carries the split and a missing state is an error. Every value chosen on loom-driven readouts was
therefore re-checked under the stationary input, on 10 October 2026, on GitHub's Windows machines
(`.github/workflows/rerun.yml`; the fit gave the same grid in every run; `results/fit_gf_adapt/`):
- **GF adaptation: refit to 10 mV** (was 30). By the fit's rule, 10 mV is now the smallest value
  that meets all four constraints. It gives 1.46 spikes per response, 1.95 on the strongest gain
  quartile (limit 2, so close), P(response) 0.575 and a 1:1 TTMn relay. At 5 mV the strong
  quartile gives 2.3 spikes.
- **PEAK_HZ: holds at 5.0.** At the fitted adaptation, the giant fiber fires 1 to 2 spikes per
  response with P(response) 0.575, which is within its anchor (P ≥ 0.5).
- **A2 working point:** re-derived by the registered rule inside every A2 run, with the values
  above.

**JON→GF calibration under load.** The spikelet now includes the factor `(1 + 0.2)` for the
gap-junction load the afferents put on the giant fiber (docs/MODEL_SPEC.md §4). The 3 mV target is
unchanged and is now met in every configuration. Before, it was met only when the afferents were
stimulus sources.

**Refrozen 11 October 2026 (registration generation 3).** Two changes, then every value chosen on a
loom-driven readout re-derived by its own rule, on GitHub's Windows machines (cloud run 13, commit
77d3726):
- **JON→GF calibrated per giant fiber.** The model couples 21 JO-B1_a and JO-B1_c afferents to the left
  giant fiber and 6 to the right. EM cannot see gap junctions: the model couples every cell of the two
  types to the giant fiber on its inferred soma side, not only the 19 cells with EM chemical contacts
  onto DNp01. One spikelet from the mean count per side gave
  the left about 4.3 mV and the right about 1.5 mV in steady state from the coupling alone (run 12
  measured peaks of 3.65 and 0.73 mV in the full network). Each giant fiber now gets its own spikelet (0.057 and 0.2 mV) and the same 0.2 coupling
  load. `fit/check_jon_calibration.py` measures, with only the coupling acting, a plateau of 2.72 and
  2.78 mV against the 2.76 mV a 60 ms pulse can reach (PASS on both). With the chemical network on, the
  same sound drive gives an early peak of 2.5 and 1.5 mV and then a plateau of −9.6 and −20.8 mV by the end
  of the pulse: polysynaptic inhibition, not the coupling, dominates the giant fiber under sound at
  w_scale 0.4 (`results/checks/jon_calibration.json`, network arm; reported, not scored).
- **w_scale 0.3 → 0.4** (table above). The blind selection, rerun at the new code, gives the same grid
  and the same answer (`results/select_wscale/`, agrees_with_declared true).
- **GF adaptation: refit to 45 mV** by the fit's unchanged rule (`results/fit_gf_adapt/`): 1.59 spikes
  per response, exactly 2.0 on the strongest gain quartile (its limit), P(response) 0.80, 1:1 TTMn
  relay. 30 mV gives 2.75 on the strong quartile. The stronger synapses drive the giant fiber harder,
  and the adaptation absorbs it; the fit sits at its constraint edge.
- **PEAK_HZ: holds at 5.0** (P(response) 0.80 ≥ 0.5, 1 to 2 spikes per response at the fitted
  adaptation).
- **A2 working point, flight afferent load:** re-derived by their registered rules inside every run.
- **Errata in frozen code comments** (left as they are, because any edit to model code changes the
  generation-3 registrations' hashes; to be corrected with the next model change): the
  `INTRINSIC_OVERRIDES` note in `flycns/graph.py` says 0 mV adaptation gives "up to 10 spikes per
  loom"; 9.7 is the strongest-quartile mean and the maximum is 15. The `flycns/registry.py` docstring
  dates version 2 to `b7eba83`, the commit of its registrations; the frozen model was `4c39a8f`.

Values that are **measured, not chosen**:
- **Single-neuron parameters:** Shiu et al. 2024.
- **Loom tuning amplitudes and trial-gain sigma:** extracted from Turner et al. 2022 imaging, stationary trials.
- **Transmitter signs:** the connectome's own classifier.
- **Electrical-synapse list:** each entry cited.

## What this means for the headline results

**The escape circuit is the calibration circuit.** Its eight checks break down as follows:
- **Calibrated:** spikes per response, response probability, CNS quiet.
- **By construction:** TTMn one-to-one, TTMn lag.
- **Independent:** GF latency (10 to 60 ms).
- **Controls:** the electrical ablation and the rewired null.

The escape result shows that one declared parameter set can be calibrated to reproduce the
escape relay with sensible latency and no runaway activity. It is not an out-of-sample prediction.

The **held-out tests** are the circuits no value above was fitted to:
- the pC1 song phenotypes (`pc1_song`) and the DNp13 control (`dnp13_control`)
- feeding by modality, the simulated checks (`feeding_by_modality` F3, F4)
- the flight checks other than L1a
- the SNpp16 tests
- **sound-loom facilitation beyond summation** (`a2_registered`, A2R2, registered version 2): it
  scores only the facilitation that adding the model's own measured sound-alone depolarisation to
  each loom-alone trial does not predict
- **sound-loom facilitation with the contact as EM annotates it** (`a2_contact_em`, C1), with one
  caveat recorded in its registration: the committed reference arm had already shown the EM-annotated
  contact firing the giant fiber on every sound-alone trial, so C1's "sound alone stays subthreshold"
  part is not a blind prediction. It is kept so C1 cannot pass on sound firing the giant fiber by itself.

Not counted as tests, though pre-registered:
- **Sound-loom facilitation** (`a2_registered`, A2R) is **construction**. The working-point rule parks
  the loom-alone giant fiber about 2 mV below threshold, and the sound input is a hand-set, untraced
  3 mV compound potential. In a one-compartment cell, summation of the two crosses threshold unless
  polysynaptic inhibition intervenes. Facilitation was also scored, with no parameter moving, during
  the gain fits (`fit_gains.py`, `fit_regional.py`). The tests of it are A2R2 and C1 (above).
- **The sign-inverted contact** (`a2_contact_em_flip`, C2) is a **control**: inhibitory input cannot
  facilitate in this model, so it is expected to pass by construction.
- **The signed taste map, sugar laterality and the feeding-by-modality synapse ratio** are
  **structural**: they count over the wiring with no simulation.

Most of these are pre-registered. Their passes and their failures are the model's real record.

## Literature check (11 October 2026)

A search for the measurements that would anchor the hand-set values (sources in REFERENCES.md,
"Physiology checked against hand-set values") found:
- **3 mV sound potential: no source.** No paper reports the giant fiber's depolarisation to sound in
  mV. Lehnert et al. 2013 recorded currents (voltage clamp); Tootoonian et al. 2012 recorded voltage
  but give no amplitude in the text; the Pézier and Jezzini papers inferred GF spikes from muscle
  recordings. What the literature does support is qualitative: sound alone is subthreshold and
  reaches threshold only with other input. The value stays a declared free parameter. The model can
  now run the contact as EM annotates it (`FLYCNS_JON=em`), sign-inverted (`em_flip`), or at another
  compound potential (`FLYCNS_JON_MV`), so the A2 result can be tested without it (phase 5 registers
  these arms).
- **Loom rate scale (PEAK_HZ): no source.** No electrophysiology of LC4 or LPLC2 spike rates was
  found; LPLC2 data are calcium imaging (Klapoetke et al. 2017). Ache et al. 2019 model the GF input
  as angular velocity (LC4) plus a Gaussian of angular size (LPLC2). PEAK_HZ stays the stimulus's
  one free scale; escape spikes per response and response probability stay calibrated.
- **Nerve-cord glutamate.** Inhibition onto motor neurons is moderately supported (larval
  pharmacology, Rohrbough & Broadie 2002, Kohsaka et al. 2014; adult GluClα expression, Lesser et
  al. 2024). Between nerve-cord interneurons it is an untested inference. A battery variant makes
  that glutamate excitatory (`FLYCNS_GLU_VNC=excitatory`).
- **Membrane parameters.** Motor neurons span about 100–700 MΩ input resistance by size class
  (Azevedo et al. 2020; Herrera-Valdez et al. 2013); the only central τ_m found is about 16 ms
  (Hafez et al. 2023), close to the model's 20 ms. Too sparse to set per-class values.
- **Numerics.** A battery variant halves the time step (`FLYCNS_DT_MS=0.05`): the TTMn lag should
  move from 0.9 to 0.85 ms (0.8 ms delay plus one step), and nothing else should change.
- **w_scale.** `fit/select_wscale.py` selects the global scale on a benchmark-blind criterion,
  registered before it ran. Its answer, 0.4, is the declared value since 11 October 2026 (registration
  generation 3); the giant fiber adaptation was refit under it, and the loom scale, the flight load and
  the A2 working point re-derive themselves by their own rules in every run.

## Turning calibrated checks into tests

- **PEAK_HZ:** anchor it to recorded LC4/LPLC2 spike rates instead of to the giant fiber's output. Escape spikes per response and response probability then become tests. This needs a published spike-rate measurement for loom in those cell types.
- **w_scale:** done (11 October 2026): chosen on a registered criterion blind to every benchmark (`fit/select_wscale.py`). It is still a calibration, not a measurement: a measured per-synapse PSP is about 12 times the model's (see the table).
- **3 mV:** trace it to a figure or replace it, then report A1 as a test of that number.
