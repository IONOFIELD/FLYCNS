# MaleCNS v1.0 LIF benchmark suite

**29/53 checks pass under ONE parameter set** (same LIFParams for every circuit).

**By role:** independent 5/19 (3 unresolved) | control 12/14 (2 unresolved) | robustness 0/4 | structural 3/5 | calibrated 6/7 (1 unresolved) | construction 3/4

**Uncertainty:** 53 of 53 scored checks carry a 95% interval or a per-draw or null score (flycns/stats.py); 6 are UNRESOLVED (the interval crosses a band edge) and count as not passing. A PASS means the whole interval lies inside the band.

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
  "w_scale": 0.4,
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
effective chemical kick per synapse: 0.1100 mV (Shiu 2024 unitary 0.275 mV x MaleCNS rescale 0.4)

## Checks
| benchmark | check | result | estimate [95% interval] and band | role | flags |
|---|---|---|---|---|---|
| a2_contact_em | C1_em_facilitation | FAIL | -; all of 2 parts | independent | - |
| a2_contact_em_flip | C2_flip_no_facilitation | PASS | -0.108 [-0.177, -0.0546] in [-inf, 0]; newcombe | control | - |
| a2_registered | A2R_facilitation | FAIL | -0.133 [-0.237, -0.0262] in (0, inf]; newcombe (as registered) | construction | - |
| a2_registered | A2R2_beyond_summation | FAIL | -0.692 [-0.783, -0.542] in (0, inf] | independent | - |
| a2_robustness | RA2_facilitation_at_every_near_threshold_gain | FAIL | -; all of 3 parts | robustness | - |
| auditory | A1_jo_alone_mostly_subthreshold | PASS | 0.025 [0.00443, 0.129] in [-inf, 0.3]; wilson | calibrated | - |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | - | reported | - |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | -; all of 2 parts | control | - |
| auditory | A4_null_silent | PASS | -; all of 2 parts | control | - |
| auditory | A5_cns_quiet | PASS | 0.00873; point | calibrated | - |
| dnp13_control | D1_dnp13_reachable | PASS | 19.6 [18.1, 21] in [0.5, inf] | control | - |
| dnp13_control | D2_pc1_1b_sine_choice | FAIL | -; all of 2 parts | independent | - |
| feeding | F2b_extra_SEZ_quiet | PASS | 0.00104 [0.000921, 0.00113] in [-inf, 0.02] | calibrated | - |
| feeding | F2c_motor_rate_physiological | PASS | 4.29 [4.03, 6.83] in (0, 100] | construction | - |
| feeding | F2_dose_response_REPORTED | SKIP | - | reported | - |
| feeding | F1_laterality_matches_wiring | SKIP | - | reported | - |
| feeding | F1_shiu_contralateral_bias | SKIP | - | reported | - |
| feeding | F3_bitter_suppresses | SKIP | - | reported | - |
| feeding | F4_second_order_sufficient | SKIP | - | reported | - |
| feeding | F5_null_silent | SKIP | - | reported | - |
| feeding_by_modality | F2_sugar_ratio_exceeds_bitter | PASS | 0.675; point | structural | - |
| feeding_by_modality | F3_sugar_drives_mn9_at_100hz | FAIL | 0 [0, 0] in [0.5, inf] | independent | - |
| feeding_by_modality | F4_bitter_below_sugar_at_100hz | FAIL | 0 [0, 0] in (0, inf] | independent | - |
| flight_loop | L1a_DVMn_2_to_12_hz | UNRESOLVED | draws 3.37, 0, 6.65, 0, 0; band [2, 12]; 2 of 5 draws in band, pass needs 4 | calibrated | - |
| flight_loop | L1b_DLMn_cf_2_to_12_hz | FAIL | draws 0, 0, 0, 0, 0; band [2, 12]; 0 of 5 draws in band, pass needs 4 | independent | - |
| flight_loop | L2_b1_0.5_to_1.2_spikes_per_wingbeat | FAIL | draws 49.7, 55.3, 55.5, 87.6, 14.6; band [101, 242]; 0 of 5 draws in band, pass needs 4 | independent | - |
| flight_loop | L3_leg_mn_not_entrained | PASS | draws 0.658, 0.231, 0, 0.137, 0; band [-inf, 20.2]; 5 of 5 draws in band, pass needs 4 | independent | - |
| flight_loop | L4_steering_specific_vs_null | PASS | draws 94.7, 89.7, 62.9, 76.9, 34.3; band [5, inf]; 5 of 5 draws in band, pass needs 4 | control | - |
| flight_loop | L5_DLMn_cf_2_to_12_hz_with_DNg02 | FAIL | -; any of 4 parts | independent | - |
| flight_loop | L6_DVMn_still_in_band_with_DNg02 | SKIP | - | reported | - |
| flight_snpp16 | N1_snpp16_sufficient_dvmn_in_band | FAIL | draws 59.6, 59.6, 59.5; band [2, 12]; 0 of 3 draws in band, pass needs 3 | independent | - |
| flight_snpp16 | N2_snpp16_necessary_dvmn_below_2hz | FAIL | draws 39, 38.5, 38.5; band [-inf, 2]; 0 of 3 draws in band, pass needs 3 | independent | - |
| flight_snpp16_graded | G1_graded | UNRESOLVED | -; all of 12 parts | independent | - |
| flight_snpp16_graded | G2_in_band_window | PASS | -; any of 13 parts | independent | - |
| flight_snpp16_graded | G3_selective_at_k_star | PASS | -; all of 3 parts | independent | - |
| flight_snpp16_graded | G4_wiring_specific_at_k_star | PASS | draws 0, 0, 0, 0, 0; band [-inf, 1]; 5 of 5 draws in band, pass needs 4 | control | - |
| flight_snpp16_graded | G5_reliable_at_k_star | FAIL | draws 0, 1.68, 1.6, 9.34, 0; band [2, 12]; 1 of 5 draws in band, pass needs 4 | independent | - |
| flight_snpp16_robustness | R1_survives_transmitter_uncertainty | FAIL | -; all of 4 parts | robustness | - |
| flight_snpp16_robustness | R2_selectivity_holds_across_cord_params | FAIL | -; all of 7 parts | robustness | - |
| flight_snpp16_robustness | R3_replicates_with_fresh_draws | FAIL | -; all of 2 parts | robustness | - |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | 1.59 [1.39, 1.78] in [1, 2] | calibrated | - |
| gf_escape | gf_response_prob_0.5_to_1 | PASS | 0.8 [0.652, 0.895] in [0.5, 1]; wilson | calibrated | - |
| gf_escape | gf_latency_10_60ms | PASS | 36.7 [32.3, 41.4] in [10, 60] | independent | - |
| gf_escape | ttmn_one_to_one | PASS | 1 [1, 1] in [0.8, 1.2]; bootstrap (ratio of sums) | construction | - |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | 0.9 [0.9, 0.9] in [0.5, 1.5] | construction | - |
| gf_escape | cns_quiet | PASS | 0.00616; point | calibrated | - |
| gf_escape | electrical_necessary | PASS | -0.12 [-0.146, -0.0938] in [-inf, 0]; bootstrap (two independent arms) | control | - |
| gf_escape | null_silent | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | - |
| gustatory_signed_map | S1_valence_signed_on_proboscis | PASS | 0.000849; point | structural | - |
| gustatory_signed_map | S2_per_type_sign_agreement | FAIL | 4; point | structural | - |
| gustatory_signed_map | S3_LB2_dominates_pharyngeal_pumping | FAIL | 0.00057; point | structural | - |
| null_dc_auditory | N3_jo_gf_chemical_wiring_specific | UNRESOLVED | 3.64; null percentile over 20 draws | control | - |
| null_dc_escape | N1_escape_gf_wiring_specific | PASS | 0.8; null percentile over 20 draws | control | - |
| null_dc_song | N2_song_pmp2_wiring_specific | UNRESOLVED | 8.17; null percentile over 20 draws | control | - |
| null_strict | S1_escape_null_silent_superclass | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | - |
| null_strict | S2_pc1_null_silent_superclass | PASS | 0 [0, 0] in [-inf, 0.1] | control | - |
| pc1_song | P1_pc1_14a_pulse_over_sine | UNRESOLVED | -; all of 2 parts | independent | - |
| pc1_song | P2_pc1_13_14_pulse_over_sine | UNRESOLVED | -; all of 2 parts | independent | - |
| pc1_song | P3_14a_exceeds_15_16_on_pulse | PASS | 8.35 [7.6, 9.15] in (0, inf] | independent | - |
| pc1_song | P4_null_silent | PASS | 0 [0, 0] in [-inf, 0.1] | control | - |
| sugar_laterality | L1_sugar_contralateral_bias | PASS | 1.73; point | structural | - |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = the model code has changed since this report (unstamped: over an hour older than the newest); UNSTAMPED = written before integrity stamping, rerun to stamp; UNPINNED = no record of the input tables; ALLOW-DIRTY = run with FLYCNS_ALLOW_DIRTY=1, which waives the integrity guards; UNREGISTERED = not scored under a matching registration of the frozen model (flycns/registry.py); TRIALS a<b = run at fewer trials than the canonical b.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| a2_contact_em | 2026-10-12T19:25:25 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| a2_contact_em_flip | 2026-10-12T19:00:10 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| a2_registered | 2026-10-12T19:52:48 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| a2_robustness | 2026-10-12T21:04:08 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| auditory | 2026-10-12T18:51:51 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| dnp13_control | 2026-10-12T19:42:14 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| feeding | 2026-10-12T19:01:20 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| feeding_by_modality | 2026-10-12T18:24:13 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| flight_loop | 2026-10-12T18:42:45 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| flight_snpp16 | 2026-10-12T19:48:44 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| flight_snpp16_graded | 2026-10-12T19:15:38 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| flight_snpp16_robustness | 2026-10-12T19:33:19 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| gf_escape | 2026-10-12T18:10:47 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| gustatory_signed_map | 2026-10-12T18:28:13 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| null_dc_auditory | 2026-10-12T21:19:16 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| null_dc_escape | 2026-10-12T21:00:35 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| null_dc_song | 2026-10-12T19:33:20 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| null_strict | 2026-10-12T19:25:02 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| pc1_song | 2026-10-12T18:27:48 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| peptide_asta | 2026-10-12T18:31:53 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| select_wscale | 2026-10-12T19:09:19 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |
| sugar_laterality | 2026-10-12T17:56:57 | 65ce101 | 06ea0afb48c414ad / f08e90783d6b6420 | - |

## Citation check: 49/49 tags resolve in REFERENCES.md

## Stamp inventory
138 of 138 result files carry a stamp (commits: 65ce101 x136, a79bcf7 x1, c525b28 x1); 1 flagged, 0 unstamped.
- flagged: results/shiu2024_a0/a0.json (STALE)
- exempt: results/turner2022/ (input extraction from 22 GB of Turner et al. 2022 imaging; its output is a model input, hashed into every report's loom_input stamp)
