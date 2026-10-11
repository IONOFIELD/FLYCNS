# MaleCNS v1.0 LIF benchmark suite  [seed2]

**14/14 checks pass, but NOT all under the declared parameter set:** see the flags column.

**By role:** independent 1/1 | control 4/4 | calibrated 6/6 | construction 3/3

Only *independent* checks test the model; *calibrated* and *construction* checks were made to pass by a declared parameter (docs/CALIBRATION.md). *control* checks show the machinery is not trivial.

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
  "seed": 2,
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
| benchmark | check | result | role | flags |
|---|---|---|---|---|
| auditory | A1_jo_alone_mostly_subthreshold | PASS | calibrated | PERTURBED |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | reported | PERTURBED |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | control | PERTURBED |
| auditory | A4_null_silent | PASS | control | PERTURBED |
| auditory | A5_cns_quiet | PASS | calibrated | PERTURBED |
| feeding | F2b_extra_SEZ_quiet | PASS | calibrated | PERTURBED |
| feeding | F2c_motor_rate_physiological | PASS | construction | PERTURBED |
| feeding | F2_dose_response_REPORTED | SKIP | reported | PERTURBED |
| feeding | F1_laterality_matches_wiring | SKIP | reported | PERTURBED |
| feeding | F1_shiu_contralateral_bias | SKIP | reported | PERTURBED |
| feeding | F3_bitter_suppresses | SKIP | reported | PERTURBED |
| feeding | F4_second_order_sufficient | SKIP | reported | PERTURBED |
| feeding | F5_null_silent | SKIP | reported | PERTURBED |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | calibrated | PERTURBED, STALE |
| gf_escape | gf_response_prob_0.5_to_1 | PASS | calibrated | PERTURBED, STALE |
| gf_escape | gf_latency_10_60ms | PASS | independent | PERTURBED, STALE |
| gf_escape | ttmn_one_to_one | PASS | construction | PERTURBED, STALE |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | construction | PERTURBED, STALE |
| gf_escape | cns_quiet | PASS | calibrated | PERTURBED, STALE |
| gf_escape | electrical_necessary | PASS | control | PERTURBED, STALE |
| gf_escape | null_silent | PASS | control | PERTURBED, STALE |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = over an hour older than the newest report; UNSTAMPED = written before integrity stamping, rerun to stamp.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

**WARNING: reports more than an hour older than the newest are included: gf_escape. Rerun the suite (menu 4, `scripts/run_all.py`) before quoting this table.**

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| auditory | 2026-10-11T01:57:27 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SEED': '2'} |
| feeding | 2026-10-11T02:08:50 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SEED': '2'} |
| gf_escape | 2026-10-11T01:08:43 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SEED': '2'} |

## Citation check: 42/50 tags resolve in REFERENCES.md
Unresolved: Before 2026, Burrows 1998, CORRECTION 2026, Korff & Dickinson 2022, Newcombe 1998, Pezier & Blagburn 2013, Pezier et al. 2014, Pezier et al. 2016
