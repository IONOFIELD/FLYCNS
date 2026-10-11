# MaleCNS v1.0 LIF benchmark suite  [signflip10]

**33/46 checks pass, but NOT all under the declared parameter set:** see the flags column.

**By role:** independent 13/24 | control 8/8 | robustness 3/4 | calibrated 6/7 | construction 3/3

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
| a2_registered | A2R_facilitation | PASS | independent | UNSTAMPED |
| a2_robustness | RA2_facilitation_at_every_near_threshold_gain | PASS | robustness | UNSTAMPED |
| auditory | A1_jo_alone_mostly_subthreshold | PASS | calibrated | PERTURBED |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | reported | PERTURBED |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | control | PERTURBED |
| auditory | A4_null_silent | PASS | control | PERTURBED |
| auditory | A5_cns_quiet | PASS | calibrated | PERTURBED |
| dnp13_control | D1_dnp13_reachable | PASS | control | STALE, UNSTAMPED |
| dnp13_control | D2_pc1_1b_sine_choice | FAIL | independent | STALE, UNSTAMPED |
| feeding | F2b_extra_SEZ_quiet | PASS | calibrated | PERTURBED |
| feeding | F2c_motor_rate_physiological | PASS | construction | PERTURBED |
| feeding | F2_dose_response_REPORTED | SKIP | reported | PERTURBED |
| feeding | F1_laterality_matches_wiring | SKIP | reported | PERTURBED |
| feeding | F1_shiu_contralateral_bias | SKIP | reported | PERTURBED |
| feeding | F3_bitter_suppresses | SKIP | reported | PERTURBED |
| feeding | F4_second_order_sufficient | SKIP | reported | PERTURBED |
| feeding | F5_null_silent | SKIP | reported | PERTURBED |
| feeding_by_modality | F2_sugar_ratio_exceeds_bitter | PASS | independent | STALE, UNSTAMPED |
| feeding_by_modality | F3_sugar_drives_mn9_at_100hz | FAIL | independent | STALE, UNSTAMPED |
| feeding_by_modality | F4_bitter_below_sugar_at_100hz | FAIL | independent | STALE, UNSTAMPED |
| flight_loop | L1a_DVMn_2_to_12_hz | PASS | calibrated | STALE, UNSTAMPED |
| flight_loop | L1b_DLMn_cf_2_to_12_hz | FAIL | independent | STALE, UNSTAMPED |
| flight_loop | L2_b1_0.5_to_1.2_spikes_per_wingbeat | PASS | independent | STALE, UNSTAMPED |
| flight_loop | L3_leg_mn_not_entrained | PASS | independent | STALE, UNSTAMPED |
| flight_loop | L4_steering_specific_vs_null | PASS | control | STALE, UNSTAMPED |
| flight_loop | L5_DLMn_cf_2_to_12_hz_with_DNg02 | FAIL | independent | STALE, UNSTAMPED |
| flight_loop | L6_DVMn_still_in_band_with_DNg02 | FAIL | independent | STALE, UNSTAMPED |
| flight_snpp16 | N1_snpp16_sufficient_dvmn_in_band | FAIL | independent | STALE, UNSTAMPED |
| flight_snpp16 | N2_snpp16_necessary_dvmn_below_2hz | FAIL | independent | STALE, UNSTAMPED |
| flight_snpp16_graded | G1_graded | FAIL | independent | STALE, UNSTAMPED |
| flight_snpp16_graded | G2_in_band_window | PASS | independent | STALE, UNSTAMPED |
| flight_snpp16_graded | G3_selective_at_k_star | PASS | independent | STALE, UNSTAMPED |
| flight_snpp16_graded | G4_wiring_specific_at_k_star | PASS | control | STALE, UNSTAMPED |
| flight_snpp16_graded | G5_reliable_at_k_star | PASS | independent | STALE, UNSTAMPED |
| flight_snpp16_robustness | R1_survives_transmitter_uncertainty | PASS | robustness | STALE, UNSTAMPED |
| flight_snpp16_robustness | R2_selectivity_holds_across_cord_params | FAIL | robustness | STALE, UNSTAMPED |
| flight_snpp16_robustness | R3_replicates_with_fresh_draws | PASS | robustness | STALE, UNSTAMPED |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | calibrated | PERTURBED |
| gf_escape | gf_response_prob_0.5_to_1 | FAIL | calibrated | PERTURBED |
| gf_escape | gf_latency_10_60ms | PASS | independent | PERTURBED |
| gf_escape | ttmn_one_to_one | PASS | construction | PERTURBED |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | construction | PERTURBED |
| gf_escape | cns_quiet | PASS | calibrated | PERTURBED |
| gf_escape | electrical_necessary | PASS | control | PERTURBED |
| gf_escape | null_silent | PASS | control | PERTURBED |
| gustatory_signed_map | S1_valence_signed_on_proboscis | PASS | independent | STALE, UNSTAMPED |
| gustatory_signed_map | S2_per_type_sign_agreement | FAIL | independent | STALE, UNSTAMPED |
| gustatory_signed_map | S3_LB2_dominates_pharyngeal_pumping | FAIL | independent | STALE, UNSTAMPED |
| pc1_song | P1_pc1_14a_pulse_over_sine | PASS | independent | STALE, UNSTAMPED |
| pc1_song | P2_pc1_13_14_pulse_over_sine | PASS | independent | STALE, UNSTAMPED |
| pc1_song | P3_14a_exceeds_15_16_on_pulse | PASS | independent | STALE, UNSTAMPED |
| pc1_song | P4_null_silent | PASS | control | STALE, UNSTAMPED |
| sugar_laterality | L1_sugar_contralateral_bias | PASS | independent | STALE, UNSTAMPED |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = over an hour older than the newest report; UNSTAMPED = written before integrity stamping, rerun to stamp.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

**WARNING: reports more than an hour older than the newest are included: dnp13_control, feeding_by_modality, flight_loop, flight_snpp16, flight_snpp16_graded, flight_snpp16_robustness, gustatory_signed_map, pc1_song, peptide_asta, sugar_laterality. Rerun the suite (menu 4, `scripts/run_all.py`) before quoting this table.**

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| a2_registered | unstamped |  | - | - |
| a2_robustness | unstamped |  | - | - |
| auditory | 2026-10-11T00:12:04 | d313cfa | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SIGNFLIP': '0.1'} |
| dnp13_control | 2026-09-26T22:15:58 | c67b98e | - | - |
| feeding | 2026-10-11T00:23:28 | d313cfa | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SIGNFLIP': '0.1'} |
| feeding_by_modality | 2026-09-26T18:54:44 | 4cfae84 | - | - |
| flight_loop | 2026-09-24T21:19:46 | ce8b9d2 | - | - |
| flight_snpp16 | 2026-09-25T13:57:00 | b1e9e41 | - | - |
| flight_snpp16_graded | 2026-09-25T15:05:22 | 64d665b | - | - |
| flight_snpp16_robustness | 2026-09-26T12:17:55 | 77e0cc5 | - | - |
| gf_escape | 2026-10-10T23:23:45 | d313cfa | 06ea0afb48c414ad / becf568580708ba9 | {'FLYCNS_SIGNFLIP': '0.1'} |
| gustatory_signed_map | 2026-09-26T19:06:17 | 2239201 | - | - |
| pc1_song | 2026-09-26T19:47:23 | 981a20f | - | - |
| peptide_asta | 2026-09-09T15:43:57 | 00a6afb | - | - |
| sugar_laterality | 2026-09-26T19:20:29 | 27d36e2 | - | - |

## Citation check: 42/50 tags resolve in REFERENCES.md
Unresolved: Before 2026, Burrows 1998, CORRECTION 2026, Korff & Dickinson 2022, Newcombe 1998, Pezier & Blagburn 2013, Pezier et al. 2014, Pezier et al. 2016
