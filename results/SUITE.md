# MaleCNS v1.0 LIF benchmark suite

**32/53 checks pass under ONE parameter set** (same LIFParams for every circuit).

**By role:** independent 6/19 (4 unresolved) | control 12/14 (2 unresolved) | robustness 2/4 (1 unresolved) | structural 3/5 | calibrated 5/7 (1 unresolved) | construction 4/4

**Uncertainty:** 53 of 53 scored checks carry a 95% interval or a per-draw or null score (flycns/stats.py); 8 are UNRESOLVED (the interval crosses a band edge) and count as not passing. A PASS means the whole interval lies inside the band.

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
| benchmark | check | result | estimate [95% interval] and band | role | flags |
|---|---|---|---|---|---|
| a2_contact_em | C1_em_facilitation | FAIL | -; all of 2 parts | independent | - |
| a2_contact_em_flip | C2_flip_no_facilitation | PASS | -0.133 [-0.206, -0.0749] in [-inf, 0]; newcombe | control | - |
| a2_registered | A2R_facilitation | PASS | 0.333 [0.216, 0.438] in (0, inf]; newcombe (as registered) | construction | - |
| a2_registered | A2R2_beyond_summation | FAIL | -0.492 [-0.575, -0.391] in (0, inf] | independent | - |
| a2_robustness | RA2_facilitation_at_every_near_threshold_gain | PASS | -; all of 6 parts | robustness | - |
| auditory | A1_jo_alone_mostly_subthreshold | PASS | 0.05 [0.0138, 0.165] in [-inf, 0.3]; wilson | calibrated | - |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | - | reported | - |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | -; all of 2 parts | control | - |
| auditory | A4_null_silent | PASS | -; all of 2 parts | control | - |
| auditory | A5_cns_quiet | PASS | 0.00633; point | calibrated | - |
| dnp13_control | D1_dnp13_reachable | PASS | 14.3 [13.2, 15.4] in [0.5, inf] | control | - |
| dnp13_control | D2_pc1_1b_sine_choice | FAIL | -; all of 2 parts | independent | - |
| feeding | F2b_extra_SEZ_quiet | PASS | 0.000348 [0.000323, 0.000372] in [-inf, 0.02] | calibrated | - |
| feeding | F2c_motor_rate_physiological | PASS | 4.17 [3.75, 5.56] in (0, 100] | construction | - |
| feeding | F2_dose_response_REPORTED | SKIP | - | reported | - |
| feeding | F1_laterality_matches_wiring | SKIP | - | reported | - |
| feeding | F1_shiu_contralateral_bias | SKIP | - | reported | - |
| feeding | F3_bitter_suppresses | SKIP | - | reported | - |
| feeding | F4_second_order_sufficient | SKIP | - | reported | - |
| feeding | F5_null_silent | SKIP | - | reported | - |
| feeding_by_modality | F2_sugar_ratio_exceeds_bitter | PASS | 0.675; point | structural | - |
| feeding_by_modality | F3_sugar_drives_mn9_at_100hz | FAIL | 0 [0, 0] in [0.5, inf] | independent | - |
| feeding_by_modality | F4_bitter_below_sugar_at_100hz | FAIL | 0 [0, 0] in (0, inf] | independent | - |
| flight_loop | L1a_DVMn_2_to_12_hz | FAIL | 0.2 in [2, 12]; per-draw (1 of 5 in band; pass needs 4) | calibrated | - |
| flight_loop | L1b_DLMn_cf_2_to_12_hz | FAIL | 0 in [2, 12]; per-draw (0 of 5 in band; pass needs 4) | independent | - |
| flight_loop | L2_b1_0.5_to_1.2_spikes_per_wingbeat | UNRESOLVED | 0.6 in [101, 242]; per-draw (3 of 5 in band; pass needs 4) | independent | - |
| flight_loop | L3_leg_mn_not_entrained | PASS | 1 in [-inf, 20.2]; per-draw (5 of 5 in band; pass needs 4) | independent | - |
| flight_loop | L4_steering_specific_vs_null | PASS | 1 in [5, inf]; per-draw (5 of 5 in band; pass needs 4) | control | - |
| flight_loop | L5_DLMn_cf_2_to_12_hz_with_DNg02 | FAIL | -; any of 4 parts | independent | - |
| flight_loop | L6_DVMn_still_in_band_with_DNg02 | SKIP | - | reported | - |
| flight_snpp16 | N1_snpp16_sufficient_dvmn_in_band | FAIL | 0 in [2, 12]; per-draw (0 of 3 in band; pass needs 3) | independent | - |
| flight_snpp16 | N2_snpp16_necessary_dvmn_below_2hz | FAIL | 0 in [-inf, 2]; per-draw (0 of 3 in band; pass needs 3) | independent | - |
| flight_snpp16_graded | G1_graded | UNRESOLVED | -; all of 12 parts | independent | - |
| flight_snpp16_graded | G2_in_band_window | PASS | -; any of 13 parts | independent | - |
| flight_snpp16_graded | G3_selective_at_k_star | PASS | -; all of 3 parts | independent | - |
| flight_snpp16_graded | G4_wiring_specific_at_k_star | PASS | 1 in [-inf, 1]; per-draw (5 of 5 in band; pass needs 4) | control | - |
| flight_snpp16_graded | G5_reliable_at_k_star | PASS | 0.8 in [2, 12]; per-draw (4 of 5 in band; pass needs 4) | independent | - |
| flight_snpp16_robustness | R1_survives_transmitter_uncertainty | PASS | -; all of 4 parts | robustness | - |
| flight_snpp16_robustness | R2_selectivity_holds_across_cord_params | FAIL | -; all of 7 parts | robustness | - |
| flight_snpp16_robustness | R3_replicates_with_fresh_draws | UNRESOLVED | -; all of 2 parts | robustness | - |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | 1.46 [1.15, 1.85] in [1, 2] | calibrated | - |
| gf_escape | gf_response_prob_0.5_to_1 | UNRESOLVED | 0.575 [0.422, 0.715] in [0.5, 1]; wilson | calibrated | - |
| gf_escape | gf_latency_10_60ms | PASS | 39.7 [35.3, 44.2] in [10, 60] | independent | - |
| gf_escape | ttmn_one_to_one | PASS | 1 [1, 1] in [0.8, 1.2]; bootstrap (ratio of sums) | construction | - |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | 0.9 [0.9, 0.9] in [0.5, 1.5] | construction | - |
| gf_escape | cns_quiet | PASS | 0.00385; point | calibrated | - |
| gf_escape | electrical_necessary | PASS | -0.0713 [-0.104, -0.0437] in [-inf, 0]; bootstrap (two independent arms) | control | - |
| gf_escape | null_silent | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | - |
| gustatory_signed_map | S1_valence_signed_on_proboscis | PASS | 0.000849; point | structural | - |
| gustatory_signed_map | S2_per_type_sign_agreement | FAIL | 4; point | structural | - |
| gustatory_signed_map | S3_LB2_dominates_pharyngeal_pumping | FAIL | 0.00057; point | structural | - |
| null_dc_auditory | N3_jo_gf_chemical_wiring_specific | UNRESOLVED | 3.64; null percentile over 20 draws | control | - |
| null_dc_escape | N1_escape_gf_wiring_specific | PASS | 0.575; null percentile over 20 draws | control | - |
| null_dc_song | N2_song_pmp2_wiring_specific | UNRESOLVED | 7.73; null percentile over 20 draws | control | - |
| null_strict | S1_escape_null_silent_superclass | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | - |
| null_strict | S2_pc1_null_silent_superclass | PASS | 0 [0, 0] in [-inf, 0.1] | control | - |
| pc1_song | P1_pc1_14a_pulse_over_sine | UNRESOLVED | -; all of 2 parts | independent | - |
| pc1_song | P2_pc1_13_14_pulse_over_sine | UNRESOLVED | -; all of 2 parts | independent | - |
| pc1_song | P3_14a_exceeds_15_16_on_pulse | PASS | 8.15 [7.5, 8.85] in (0, inf] | independent | - |
| pc1_song | P4_null_silent | PASS | 0 [0, 0] in [-inf, 0.1] | control | - |
| sugar_laterality | L1_sugar_contralateral_bias | PASS | 1.73; point | structural | - |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = the model code has changed since this report (unstamped: over an hour older than the newest); UNSTAMPED = written before integrity stamping, rerun to stamp; UNPINNED = no record of the input tables; ALLOW-DIRTY = run with FLYCNS_ALLOW_DIRTY=1, which waives the integrity guards; UNREGISTERED = not scored under a matching registration of the frozen model (flycns/registry.py); TRIALS a<b = run at fewer trials than the canonical b.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| a2_contact_em | 2026-10-11T20:53:31 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| a2_contact_em_flip | 2026-10-11T20:32:31 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| a2_registered | 2026-10-11T20:55:21 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| a2_robustness | 2026-10-11T22:48:03 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| auditory | 2026-10-11T21:01:58 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| dnp13_control | 2026-10-11T21:28:50 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| feeding | 2026-10-11T21:13:31 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| feeding_by_modality | 2026-10-11T20:01:09 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_loop | 2026-10-11T20:56:16 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16 | 2026-10-11T21:07:32 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16_graded | 2026-10-11T20:40:44 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16_robustness | 2026-10-11T21:01:12 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| gf_escape | 2026-10-11T20:13:21 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| gustatory_signed_map | 2026-10-11T20:22:50 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| null_dc_auditory | 2026-10-11T22:13:45 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| null_dc_escape | 2026-10-11T21:33:40 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| null_dc_song | 2026-10-11T21:30:50 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| null_strict | 2026-10-11T21:43:01 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| pc1_song | 2026-10-11T20:09:12 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| peptide_asta | 2026-10-11T20:01:50 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| select_wscale | 2026-10-11T20:28:00 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |
| sugar_laterality | 2026-10-11T21:03:10 | b7eba83 | 06ea0afb48c414ad / becf568580708ba9 | - |

## Citation check: 49/49 tags resolve in REFERENCES.md

## Stamp inventory
110 of 110 result files carry a stamp (commits: b7eba83 x108, d72fe77 x2); 2 flagged, 0 unstamped.
- flagged: results/fit_gains/best.json (STALE)
- flagged: results/fit_gains/grid.csv (STALE)
- exempt: results/turner2022/ (input extraction from 22 GB of Turner et al. 2022 imaging; its output is a model input, hashed into every report's loom_input stamp)
