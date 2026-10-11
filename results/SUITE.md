# MaleCNS v1.0 LIF benchmark suite

**36/48 checks pass under ONE parameter set** (same LIFParams for every circuit).

**By role:** independent 13/24 | control 10/10 | robustness 3/4 | calibrated 7/7 | construction 3/3

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
  "seed": 0,
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
| a2_registered | A2R_facilitation | PASS | independent | - |
| a2_robustness | RA2_facilitation_at_every_near_threshold_gain | PASS | robustness | - |
| auditory | A1_jo_alone_mostly_subthreshold | PASS | calibrated | - |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | reported | - |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | control | - |
| auditory | A4_null_silent | PASS | control | - |
| auditory | A5_cns_quiet | PASS | calibrated | - |
| dnp13_control | D1_dnp13_reachable | PASS | control | - |
| dnp13_control | D2_pc1_1b_sine_choice | FAIL | independent | - |
| feeding | F2b_extra_SEZ_quiet | PASS | calibrated | - |
| feeding | F2c_motor_rate_physiological | PASS | construction | - |
| feeding | F2_dose_response_REPORTED | SKIP | reported | - |
| feeding | F1_laterality_matches_wiring | SKIP | reported | - |
| feeding | F1_shiu_contralateral_bias | SKIP | reported | - |
| feeding | F3_bitter_suppresses | SKIP | reported | - |
| feeding | F4_second_order_sufficient | SKIP | reported | - |
| feeding | F5_null_silent | SKIP | reported | - |
| feeding_by_modality | F2_sugar_ratio_exceeds_bitter | PASS | independent | - |
| feeding_by_modality | F3_sugar_drives_mn9_at_100hz | FAIL | independent | - |
| feeding_by_modality | F4_bitter_below_sugar_at_100hz | FAIL | independent | - |
| flight_loop | L1a_DVMn_2_to_12_hz | PASS | calibrated | - |
| flight_loop | L1b_DLMn_cf_2_to_12_hz | FAIL | independent | - |
| flight_loop | L2_b1_0.5_to_1.2_spikes_per_wingbeat | PASS | independent | - |
| flight_loop | L3_leg_mn_not_entrained | PASS | independent | - |
| flight_loop | L4_steering_specific_vs_null | PASS | control | - |
| flight_loop | L5_DLMn_cf_2_to_12_hz_with_DNg02 | FAIL | independent | - |
| flight_loop | L6_DVMn_still_in_band_with_DNg02 | FAIL | independent | - |
| flight_snpp16 | N1_snpp16_sufficient_dvmn_in_band | FAIL | independent | - |
| flight_snpp16 | N2_snpp16_necessary_dvmn_below_2hz | FAIL | independent | - |
| flight_snpp16_graded | G1_graded | FAIL | independent | - |
| flight_snpp16_graded | G2_in_band_window | PASS | independent | - |
| flight_snpp16_graded | G3_selective_at_k_star | PASS | independent | - |
| flight_snpp16_graded | G4_wiring_specific_at_k_star | PASS | control | - |
| flight_snpp16_graded | G5_reliable_at_k_star | PASS | independent | - |
| flight_snpp16_robustness | R1_survives_transmitter_uncertainty | PASS | robustness | - |
| flight_snpp16_robustness | R2_selectivity_holds_across_cord_params | FAIL | robustness | - |
| flight_snpp16_robustness | R3_replicates_with_fresh_draws | PASS | robustness | - |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | calibrated | - |
| gf_escape | gf_response_prob_0.5_to_1 | PASS | calibrated | - |
| gf_escape | gf_latency_10_60ms | PASS | independent | - |
| gf_escape | ttmn_one_to_one | PASS | construction | - |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | construction | - |
| gf_escape | cns_quiet | PASS | calibrated | - |
| gf_escape | electrical_necessary | PASS | control | - |
| gf_escape | null_silent | PASS | control | - |
| gustatory_signed_map | S1_valence_signed_on_proboscis | PASS | independent | - |
| gustatory_signed_map | S2_per_type_sign_agreement | FAIL | independent | - |
| gustatory_signed_map | S3_LB2_dominates_pharyngeal_pumping | FAIL | independent | - |
| null_strict | S1_escape_null_silent_superclass | PASS | control | - |
| null_strict | S2_pc1_null_silent_superclass | PASS | control | - |
| pc1_song | P1_pc1_14a_pulse_over_sine | PASS | independent | - |
| pc1_song | P2_pc1_13_14_pulse_over_sine | PASS | independent | - |
| pc1_song | P3_14a_exceeds_15_16_on_pulse | PASS | independent | - |
| pc1_song | P4_null_silent | PASS | control | - |
| sugar_laterality | L1_sugar_contralateral_bias | PASS | independent | - |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = the model code has changed since this report (unstamped: over an hour older than the newest); UNSTAMPED = written before integrity stamping, rerun to stamp.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| a2_registered | 2026-10-11T02:02:23 | 45126da | - | - |
| a2_robustness | 2026-10-11T02:48:05 | 45126da | - | - |
| auditory | 2026-10-11T02:00:14 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | - |
| dnp13_control | 2026-10-11T03:08:16 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |
| feeding | 2026-10-11T02:11:31 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | - |
| feeding_by_modality | 2026-10-11T03:07:39 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_loop | 2026-10-11T01:36:21 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16 | 2026-10-11T03:10:35 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16_graded | 2026-10-11T03:51:10 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16_robustness | 2026-10-11T01:58:49 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | - |
| gf_escape | 2026-10-11T01:11:58 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | - |
| gustatory_signed_map | 2026-10-11T03:01:18 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |
| null_strict | 2026-10-11T02:41:06 | 45126da | - | - |
| pc1_song | 2026-10-11T03:20:57 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |
| peptide_asta | 2026-10-11T01:00:36 | 45126da | 06ea0afb48c414ad / becf568580708ba9 | - |
| sugar_laterality | 2026-10-11T03:01:10 | b33610d | 06ea0afb48c414ad / becf568580708ba9 | - |

## Citation check: 48/48 tags resolve in REFERENCES.md
