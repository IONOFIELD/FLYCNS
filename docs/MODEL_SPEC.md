# Model specification

This file states the model in plain mathematics, independent of any simulator. Software rots, so
someone with only this file, the connectome and a different simulator should be able to rebuild
the model and get the same results. The reference implementation is `flycns/graph.py` (network)
and `flycns/model.py` (dynamics), run in Brian2. Where the two disagree, the code is what produced
the results, and the disagreement is a bug in this file.

Every value below is the default in
`LIFParams` or `flycns/graph.py`. Overrides of any of them through `FLYCNS_*` environment
variables are stamped into each report.

## 1. Network

**Source.** Janelia FlyEM MaleCNS v1.0 (neuprint dataset `male-cns:v1.0`). Two tables:
- **neurons:** `bodyId`, `type`, `superclass`, `somaSide`, and annotations.
- **edges:** `pre`, `post`, `weight` = synapse count, `nt` = the transmitter of the presynaptic neuron: its `consensusNt` where the dataset gives one, otherwise its `predictedNt` (the classifier's call), otherwise unknown. The table also carries a legacy `sign` column that the model never reads (signs come from `SIGN_MAP` below).

Their content is pinned by `data/MANIFEST.json`.

**Connections kept.** Only connections of at least 5 synapses (`MIN_WEIGHT_DEFAULT`).

**Sign.** Each connection takes the sign of its presynaptic transmitter:

| transmitter | sign |
|---|---|
| acetylcholine | +1 |
| GABA, glutamate, histamine | −1 |
| dopamine, octopamine, serotonin | 0 (modulatory; connection removed) |
| unknown | connection removed |

**Neurons simulated.** Every neuron that appears in a kept connection. Neurons with no kept connection are absent. No filter on reconstruction status or cropping is applied, and autapses (a neuron's connections onto itself) are kept as the dataset gives them.

**Electrical synapses.** EM cannot see gap junctions, so they are added from the literature. Each is a one-way pair (pre → post) with a citation (`ELECTRICAL_SYNAPSES`):
- **GF (DNp01) → TTMn and GF → PSI:** spikelet 9 mV, ipsilateral, coupling g = 0.2.
- **JO-B1_a and JO-B1_c → GF:** spikelet calibrated so the population at 150 Hz gives a 3 mV compound potential, with coupling 0.2 / n. Here n is the afferents converging on one GF: the mean count per body side of the sided afferents (both types pooled), plus every unsided afferent. One spikelet value serves both sides, so if the two sides have different counts, the two giant fibers receive slightly different compound potentials (the larger side more). A sided afferent couples only to the giant fiber on its own side; an unsided one, or one with no giant fiber on its side, couples to both. The 3 mV value has no traced source (docs/CALIBRATION.md, "Literature check"); `FLYCNS_JON` and `FLYCNS_JON_MV` give the alternatives (section 10).

The 679 EM "chemical" synapses on the JO→GF contact are removed so the contact is not counted twice.

## 2. Neuron

Each neuron is a leaky integrate-and-fire unit with three state variables: membrane potential v, synaptic drive g, and adaptation a.

```
tau_m · dv/dt = V_rest − v + g + I_gap + g_shunt · (V_rest − v) − a      (this equation is frozen while refractory)
tau_s · dg/dt = −g
tau_a · da/dt = −a

spike when v > V_thresh:   v ← V_reset ;  a ← a + b_adapt ;  refractory for t_ref
```

**Refractoriness, exactly.** Only the voltage equation is frozen while a cell is refractory; `g` and `a` keep integrating. A spikelet that arrives during refractoriness (section 4) still adds to `v`, and because the equation is frozen it is not leaked away: the cell fires as soon as refractoriness ends if `v` is then above threshold. This is load-bearing. A giant fiber doublet 2.2 to 3.1 ms apart delivers its second spikelet while TTMn is refractory, and only this behaviour keeps the relay one-to-one.

| parameter | value | source |
|---|---|---|
| V_rest | −52 mV | Shiu et al. 2024 |
| V_thresh | −45 mV | Shiu et al. 2024 |
| V_reset | −52 mV | Shiu et al. 2024 |
| tau_m | 20 ms | Shiu et al. 2024 |
| tau_s | 5 ms | Shiu et al. 2024 |
| t_ref | 2.2 ms | Shiu et al. 2024 |
| tau_a | 100 ms | declared |
| b_adapt | 0, except GF (DNp01) 10 mV and central-brain motor neurons (superclass cb_motor) 10 mV | docs/CALIBRATION.md |

## 3. Chemical synapse

When presynaptic neuron i spikes, after a delay d_chem = 1.8 ms (Shiu et al. 2024):

```
g_post ← g_post + s_ij · n_ij · w_syn · w_scale
```

- s_ij is the sign.
- n_ij is the synapse count.
- w_syn = 0.275 mV (Shiu et al. 2024).
- w_scale = 0.3 (docs/CALIBRATION.md).

The effective kick is 0.0825 mV per synapse. Class and region gains exist in the code but are all 1.0 in the declared set.

## 4. Electrical synapse

For each declared pair (pre → post):

```
I_gap(post) = Σ_pre  g_gap · (v_pre − v_post)          (continuous; enters the post membrane equation)
on a pre spike, after d_gap = 0.8 ms:  v_post ← v_post + A_spikelet
```

- The spikelet stands in for the action potential, which a LIF unit does not have.
- Coupling acts on the post cell only. The giant-fiber synapses rectify in vivo (Phelan et al. 2008).
- A stimulated source has no membrane. It contributes the spikelet, plus the load of a partner at rest, `g_shunt · (V_rest − v_post)`, where `g_shunt` is the summed `g_gap` of the post cell's stimulated partners. Without that term, replacing a cell by a source would remove its load and change its partner's excitability; this confounded the A2 arms before 10 October 2026.
- **Calibration under load.** A population's spikelet is set to `compound_mV · (1 + G) / (n · rate · tau_m)`, with `G = 0.2` the population's total coupling onto the post cell. The load shortens the post cell's effective time constant to `tau_m / (1 + G)`, so this keeps the calibrated potential exact.

## 5. Stimulus

- A stimulated cell type is **replaced** by independent Poisson spike sources, one per neuron of that type. A replaced neuron receives no input of any kind, chemical or electrical.
- Each source drives the targets of the neuron it replaces through the same synapse rules.
- Rates and protocols are defined per benchmark, in each script header.
- **Loom.** Amplitude per type comes from Turner et al. 2022 (stationary trials). Each trial has a shared lognormal gain (sigma from the same data), scaled by PEAK_HZ = 5 Hz.

## 6. Numerics

- **Integration:** forward Euler, time step 0.1 ms (`FLYCNS_DT_MS` halves it as a numerics check). The peptide pools (off in the declared set) are integrated exactly.
- **Engine:** Brian2, compiled (Cython, with the Microsoft C++ Build Tools) or pure Python (NumPy). Both run the same generated equations and give identical spikes; the unit tests compare them on every CI run, and each report records which ran.
- **Initial state:** all neurons start at V_rest with g = a = 0.
- **Background:** none. There is no tonic background activity and no noise in the declared set.
- **Randomness:** only in Poisson stimulus spikes and nulls, from a fixed seed (`FLYCNS_SEED`, default 0). The auditory benchmark draws its calibration arms on seeds 1000 and up and its two A2 arms on different seeds, so calibration and scoring never share trials. The degree-corrected null draws use seeds 1000 + k, independent of the stimulus seed.

## 7. Null models (`rewire_null`)

| mode | how targets are shuffled | what is kept |
|---|---|---|
| global (default; used by the registered null checks of version 1) | permuted across the whole network | each sender's connection count, synapse counts and sign; each target's in-degree |
| superclass | permuted only among targets of the same superclass | additionally, how many synapses each sender sends to each class of cell |
| superclass_side | as superclass, within the same body side | additionally, body side |
| degree_corrected | permuted only among connections sharing the target's superclass and neuropil (dominant ROI), the connection's sign and its size class (5-9, 10-19, 20-49, 50-99, 100+ synapses) | additionally, each target's input per sign and size class, and its neuropil; the network stays about as active as the real one, so wiring specificity can be scored as a percentile over 20 draws (`benchmarks/null_distribution.py`) |

Self-loops created by the shuffle are dropped in every mode. A shuffle can give a sender the same target twice; such repeats are kept and summed, so the number of distinct partners is not always preserved. Unless a seed is given, the null uses `FLYCNS_SEED`, so the battery's seed replicates draw different nulls.

## 8. Peptide modulation (off in the declared parameter set)

When `peptide_gain_scale > 0`, each declared peptide has one shared level `c`:
- every spike of a source cell, simulated or stimulated, raises it by `1 / n_source`, clipped to [0, 1];
- it decays with that peptide's declared time constant;
- it is copied each step to every receptor-expressing target, where it scales synaptic input as `g += w · (1 + gain · c)`.

A peptide whose source and targets are not both in the network is an error, never silently skipped.

## 10. Declared alternatives (robustness arms; off in the declared parameter set)

| setting | default | alternative |
|---|---|---|
| `FLYCNS_JON` | `electrical` | `em`: the JO → GF contact as EM annotates it (its chemical synapses, transmitter-signed), with no coupling; `em_flip`: the same, sign inverted. The GF → TTMn and GF → PSI relays are kept in every mode. |
| `FLYCNS_JON_MV` | 3 | the JO → GF compound potential, in mV |
| `FLYCNS_GLU_VNC` | `inhibitory` | `excitatory`: glutamate from nerve-cord neurons onto non-motor targets is excitatory |
| `FLYCNS_DT_MS` | 0.1 | the integration time step, in ms |

Any of these, like every `FLYCNS_*` override, is stamped into the report and flagged; a run under one is
never a registered result (`flycns/registry.py`).

## 9. Not in the model

- Neuromodulation: amines are excluded and peptides are off.
- Graded (non-spiking) signalling.
- Spontaneous background activity.
- Dendritic compartments.
- Short-term plasticity.
- A body, except a surrogate drive in the flight benchmarks.

README "Limitations" lists which results fail because of each absence.
