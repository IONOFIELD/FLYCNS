# MaleCNS v1.0 LIF benchmark suite  [seed1]

**13/14 checks pass, but NOT all as registered under the declared parameter set:** see the flags column.

**By role:** independent 1/1 | control 4/4 | calibrated 5/6 (1 unresolved) | construction 3/3

**Uncertainty:** 14 of 14 scored checks carry a 95% interval or a per-draw or null score (flycns/stats.py); 1 are UNRESOLVED (the interval crosses a band edge) and count as not passing. A PASS means the whole interval lies inside the band.

Only *independent* checks test the model; *calibrated* and *construction* checks were made to pass by a declared parameter (docs/CALIBRATION.md). *control* checks show the machinery is not trivial. *structural* checks count over the wiring with no simulation.

## Parameters
```
{
  "v_rest_mV": -52.0,
  "v_thresh_mV": -45.0,
  "v_reset_mV": -52.0,
  "tau_m_ms": 20.0,
  "tau_syn_ms": 5.0,
  "refractory_ms": 2.2,
  "w_syn_mV": 0.275,
  "w_scale": 0.3,
  "tau_adapt_ms": 100.0,
  "gap_delay_ms": 0.8,
  "chem_delay_ms": 1.8,
  "dt_ms": 0.1,
  "seed": 1,
  "class_gains": {
    "sensory": 1.0,
    "relay": 1.0,
    "local": 1.0
  },
  "region_gains": {
    "SEZ": 1.0,
    "other": 1.0
  },
  "superclass_params": {},
  "peptide_gain_scale": 0.0,
  "peptide_exclude": [],
  "baseline_depol_mV": 0.0,
  "baseline_noise_mV": 0.0
}
```
effective chemical kick per synapse: 0.0825 mV (Shiu 2024 unitary 0.275 mV x MaleCNS rescale 0.3)

## Checks
| benchmark | check | result | estimate [95% interval] and band | role | flags |
|---|---|---|---|---|---|
| auditory | A1_jo_alone_mostly_subthreshold | PASS | 0 [0, 0.0876] in [-inf, 0.3]; wilson | calibrated | PERTURBED, UNREGISTERED |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | - | reported | PERTURBED, UNREGISTERED |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | -; all of 2 parts | control | PERTURBED, UNREGISTERED |
| auditory | A4_null_silent | PASS | -; all of 2 parts | control | PERTURBED, UNREGISTERED |
| auditory | A5_cns_quiet | PASS | 0.00661; point | calibrated | PERTURBED, UNREGISTERED |
| feeding | F2b_extra_SEZ_quiet | PASS | 0.000377 [0.000333, 0.000421] in [-inf, 0.02] | calibrated | PERTURBED, UNREGISTERED |
| feeding | F2c_motor_rate_physiological | PASS | 5.42 [4.17, 6.25] in (0, 100] | construction | PERTURBED, UNREGISTERED |
| feeding | F2_dose_response_REPORTED | SKIP | - | reported | PERTURBED, UNREGISTERED |
| feeding | F1_laterality_matches_wiring | SKIP | - | reported | PERTURBED, UNREGISTERED |
| feeding | F1_shiu_contralateral_bias | SKIP | - | reported | PERTURBED, UNREGISTERED |
| feeding | F3_bitter_suppresses | SKIP | - | reported | PERTURBED, UNREGISTERED |
| feeding | F4_second_order_sufficient | SKIP | - | reported | PERTURBED, UNREGISTERED |
| feeding | F5_null_silent | SKIP | - | reported | PERTURBED, UNREGISTERED |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | 1.56 [1.23, 1.98] in [1, 2] | calibrated | PERTURBED, UNREGISTERED |
| gf_escape | gf_response_prob_0.5_to_1 | UNRESOLVED | 0.65 [0.495, 0.779] in [0.5, 1]; wilson | calibrated | PERTURBED, UNREGISTERED |
| gf_escape | gf_latency_10_60ms | PASS | 40.7 [35.3, 46.1] in [10, 60] | independent | PERTURBED, UNREGISTERED |
| gf_escape | ttmn_one_to_one | PASS | 1 [1, 1] in [0.8, 1.2]; bootstrap (ratio of sums) | construction | PERTURBED, UNREGISTERED |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | 0.9 [0.9, 0.9] in [0.5, 1.5] | construction | PERTURBED, UNREGISTERED |
| gf_escape | cns_quiet | PASS | 0.00421; point | calibrated | PERTURBED, UNREGISTERED |
| gf_escape | electrical_necessary | PASS | -0.0875 [-0.124, -0.0563] in [-inf, 0]; bootstrap (two independent arms) | control | PERTURBED, UNREGISTERED |
| gf_escape | null_silent | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | PERTURBED, UNREGISTERED |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = the model code has changed since this report (unstamped: over an hour older than the newest); UNSTAMPED = written before integrity stamping, rerun to stamp; UNPINNED = no record of the input tables; ALLOW-DIRTY = run with FLYCNS_ALLOW_DIRTY=1, which waives the integrity guards; UNREGISTERED = not scored under a matching registration of the frozen model (flycns/registry.py); TRIALS a<b = run at fewer trials than the canonical b.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| auditory | 2026-10-11T22:10:20 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SEED': '1'} |
| feeding | 2026-10-11T22:22:06 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SEED': '1'} |
| gf_escape | 2026-10-11T21:20:27 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SEED': '1'} |

## Citation check: 49/49 tags resolve in REFERENCES.md
