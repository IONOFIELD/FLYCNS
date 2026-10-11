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
| **w_scale = 0.3** (global synaptic scale; 0.275 mV × 0.3 = 0.0825 mV per synapse) | `flycns/model.py` | A sweep (`scripts/legacy/sweep.py`, `data/sweep_results.csv`) over 1.0, 0.5 and 0.25, looking for low population rate (under about 1 Hz), few active cells (under 10%), and giant fiber firing far more under loom than under sound. The committed grid does not contain 0.3. `scripts/legacy/gf_physio.py` records the reasoning as roughly a 3× reduction, because the raw value is too strong once the nerve cord is included. No other record of the derivation exists. | escape `cns_quiet`, auditory `A5_cns_quiet` and feeding `F2b_extra_SEZ_quiet` are **calibrated**. The selection also looked at GF/TTMn firing, so the escape circuit is not held out from it. **Re-selected blind, 11 October 2026** (`fit/select_wscale.py`, criterion registered before the run): under a random 10% of the sensory neurons no benchmark drives, at 20 Hz, the network stays quiet (rate < 1 Hz, < 10% active) for every w_scale from 0.15 to 0.4 (0.3: 0.007 Hz, 0.06% active) and runs away between 0.4 and 0.5 (2.5 Hz, 3.7% active at 0.5). The registered rule, "the largest quiet value", picks 0.4, at the edge of that transition. 0.3 satisfies the two quietness conditions but is **not** what the registered rule selects. It is kept anyway, because adopting 0.4 would place the model at the edge of a runaway transition and would require refitting the loom rate scale, the GF adaptation and the A2 working point. This departs from the registered rule; it is a decision taken after seeing the result, recorded as such, and gap 6 stays open. The selection's registration and report are committed in `results/select_wscale/`. |
| **PEAK_HZ = 5.0** (dF/F to spike-rate scale of the loom stimulus) | `flycns/protocols.py` | Anchored so the giant fiber fires 1 to 2 spikes with P(response) ≥ 0.5 (von Reyn et al. 2014). No recording links glomerulus dF/F to spike rate, so this is the stimulus's one free scale. | escape `gf_spikes_per_response_1_to_2` and `gf_response_prob_0.5_to_1` are **calibrated** |
| **GF adaptation b_adapt = 10 mV** (30 mV before 10 October 2026) | `flycns/graph.py` INTRINSIC_OVERRIDES | `benchmarks/fit_gf_adapt.py`: the smallest value giving 1 to 2 spikes per response, ≤ 2 on the strongest gain quartile, P(response) 0.5 to 1, and an intact TTMn relay | same two escape checks (**calibrated**) |
| **GF→TTMn, GF→PSI spikelet 9 mV, delay 0.8 ms** | `flycns/graph.py` ELECTRICAL_SYNAPSES, `model.py` | Physiological constraint: a 1:1 relay at about 0.8 ms (Tanouye & Wyman 1980). The spikelet is set just above the 7 mV distance from rest to threshold. | escape `ttmn_one_to_one` and `ttmn_lag_0.5_1.5ms` hold **by construction** |
| **JON→GF compound potential 3 mV at 150 Hz** | `flycns/graph.py` | Chosen to keep sound alone subthreshold, as recorded. **The 3 mV value has not been traced to a source figure.** | auditory `A1_jo_alone_mostly_subthreshold` is **calibrated** |
| **G_GAP_RELAY = 0.2** (ohmic coupling, as a fraction of leak) | `flycns/graph.py` | Set by hand for a 1:1 relay pair and shared across population pairs | none scored directly |
| **cb_motor adaptation 10 mV** | `flycns/graph.py` INTRINSIC_OVERRIDES | Keeps sustained motor rates under 100 Hz (Azevedo et al. 2020, McKellar et al. 2020) | feeding `F2c_motor_rate_physiological` holds **by construction** |
| **flight afferent load 0.25** | `benchmarks/flight_loop.py` | The smallest load putting mean DVMn 1a-c in 2 to 12 Hz | flight `L1a_DVMn_2_to_12_hz` is **calibrated** |
| **A2 working point** (loom gain per run; 0.8 in the 11 October 2026 rerun) | `benchmarks/auditory.py` | Pre-registered protocol: the largest loom gain leaving loom-alone GF response ≤ 0.3, with at least 2 mV depolarisation. It sets "near threshold". It does not target facilitation. The earlier gain fits (`benchmarks/fit_gains.py`, `benchmarks/fit_regional.py`) did score an A2 facilitation criterion while selecting gains; no parameter moved. Since 11 October 2026 (later) the calibration arms draw seeds disjoint from the scored arms (BASE_SEED + 1000 + gain index), and the two scored arms draw different seeds; before, the calibration arm at the chosen gain was bit-identical to the scored loom-alone arm. | `A2R_facilitation` is **construction** (see below). The report now also gives the facilitation that summation alone predicts, and the residual beyond it. |
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
- **w_scale.** `fit/select_wscale.py` re-selects the global scale on the benchmark-blind criterion
  below, registered before it runs. Its answer is a recommendation; adopting a different value would
  move every calibrated value after it.

## Turning calibrated checks into tests

- **PEAK_HZ:** anchor it to recorded LC4/LPLC2 spike rates instead of to the giant fiber's output. Escape spikes per response and response probability then become tests. This needs a published spike-rate measurement for loom in those cell types.
- **w_scale:** choose it on a criterion blind to every benchmark, such as population rate and fraction active under broad sensory drive that excludes all benchmark input types. Then rerun the suite. Register the criterion before running.
- **3 mV:** trace it to a figure or replace it, then report A1 as a test of that number.
