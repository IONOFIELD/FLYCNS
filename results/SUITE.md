# MaleCNS v1.0 LIF benchmark suite

**35/48 checks pass under ONE parameter set** (same LIFParams for every circuit).

**By role:** independent 9/18 | control 10/10 | robustness 3/4 | structural 3/5 | calibrated 6/7 (1 unresolved) | construction 4/4

**Uncertainty:** 16 of 48 scored checks carry a 95% interval or a per-draw or null score (flycns/stats.py); 1 are UNRESOLVED (the interval crosses a band edge) and count as not passing. A PASS means the whole interval lies inside the band.

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
| a2_registered | A2R_facilitation | PASS | point, no interval | construction | STALE |
| a2_robustness | RA2_facilitation_at_every_near_threshold_gain | PASS | point, no interval | robustness | STALE |
| auditory | A1_jo_alone_mostly_subthreshold | PASS | 0.05 [0.0138, 0.165] in [-inf, 0.3]; wilson | calibrated | - |
| auditory | A2_jo_effect_on_near_threshold_loom_REPORTED | SKIP | - | reported | - |
| auditory | A3_declared_pairs_carry_jo_drive | PASS | -; all of 2 parts | control | - |
| auditory | A4_null_silent | PASS | -; all of 2 parts | control | - |
| auditory | A5_cns_quiet | PASS | 0.00659; point | calibrated | - |
| dnp13_control | D1_dnp13_reachable | PASS | point, no interval | control | STALE |
| dnp13_control | D2_pc1_1b_sine_choice | FAIL | point, no interval | independent | STALE |
| feeding | F2b_extra_SEZ_quiet | PASS | 0.000348 [0.000323, 0.000372] in [-inf, 0.02] | calibrated | - |
| feeding | F2c_motor_rate_physiological | PASS | 4.17 [3.75, 5.56] in (0, 100] | construction | - |
| feeding | F2_dose_response_REPORTED | SKIP | - | reported | - |
| feeding | F1_laterality_matches_wiring | SKIP | - | reported | - |
| feeding | F1_shiu_contralateral_bias | SKIP | - | reported | - |
| feeding | F3_bitter_suppresses | SKIP | - | reported | - |
| feeding | F4_second_order_sufficient | SKIP | - | reported | - |
| feeding | F5_null_silent | SKIP | - | reported | - |
| feeding_by_modality | F2_sugar_ratio_exceeds_bitter | PASS | point, no interval | structural | STALE |
| feeding_by_modality | F3_sugar_drives_mn9_at_100hz | FAIL | point, no interval | independent | STALE |
| feeding_by_modality | F4_bitter_below_sugar_at_100hz | FAIL | point, no interval | independent | STALE |
| flight_loop | L1a_DVMn_2_to_12_hz | PASS | point, no interval | calibrated | STALE |
| flight_loop | L1b_DLMn_cf_2_to_12_hz | FAIL | point, no interval | independent | STALE |
| flight_loop | L2_b1_0.5_to_1.2_spikes_per_wingbeat | PASS | point, no interval | independent | STALE |
| flight_loop | L3_leg_mn_not_entrained | PASS | point, no interval | independent | STALE |
| flight_loop | L4_steering_specific_vs_null | PASS | point, no interval | control | STALE |
| flight_loop | L5_DLMn_cf_2_to_12_hz_with_DNg02 | FAIL | point, no interval | independent | STALE |
| flight_loop | L6_DVMn_still_in_band_with_DNg02 | FAIL | point, no interval | independent | STALE |
| flight_snpp16 | N1_snpp16_sufficient_dvmn_in_band | FAIL | point, no interval | independent | STALE |
| flight_snpp16 | N2_snpp16_necessary_dvmn_below_2hz | FAIL | point, no interval | independent | STALE |
| flight_snpp16_graded | G1_graded | FAIL | point, no interval | independent | STALE |
| flight_snpp16_graded | G2_in_band_window | PASS | point, no interval | independent | STALE |
| flight_snpp16_graded | G3_selective_at_k_star | PASS | point, no interval | independent | STALE |
| flight_snpp16_graded | G4_wiring_specific_at_k_star | PASS | point, no interval | control | STALE |
| flight_snpp16_graded | G5_reliable_at_k_star | PASS | point, no interval | independent | STALE |
| flight_snpp16_robustness | R1_survives_transmitter_uncertainty | PASS | point, no interval | robustness | STALE |
| flight_snpp16_robustness | R2_selectivity_holds_across_cord_params | FAIL | point, no interval | robustness | STALE |
| flight_snpp16_robustness | R3_replicates_with_fresh_draws | PASS | point, no interval | robustness | STALE |
| gf_escape | gf_spikes_per_response_1_to_2 | PASS | 1.46 [1.15, 1.85] in [1, 2] | calibrated | - |
| gf_escape | gf_response_prob_0.5_to_1 | UNRESOLVED | 0.575 [0.422, 0.715] in [0.5, 1]; wilson | calibrated | - |
| gf_escape | gf_latency_10_60ms | PASS | 39.7 [35.3, 44.2] in [10, 60] | independent | - |
| gf_escape | ttmn_one_to_one | PASS | 1 [1, 1] in [0.8, 1.2]; bootstrap (ratio of sums) | construction | - |
| gf_escape | ttmn_lag_0.5_1.5ms | PASS | 0.9 [0.9, 0.9] in [0.5, 1.5] | construction | - |
| gf_escape | cns_quiet | PASS | 0.00385; point | calibrated | - |
| gf_escape | electrical_necessary | PASS | -0.0713 [-0.104, -0.0437] in [-inf, 0]; bootstrap (two independent arms) | control | - |
| gf_escape | null_silent | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | - |
| gustatory_signed_map | S1_valence_signed_on_proboscis | PASS | point, no interval | structural | STALE |
| gustatory_signed_map | S2_per_type_sign_agreement | FAIL | point, no interval | structural | STALE |
| gustatory_signed_map | S3_LB2_dominates_pharyngeal_pumping | FAIL | point, no interval | structural | STALE |
| null_strict | S1_escape_null_silent_superclass | PASS | 0 [0, 0.0876] in [-inf, 0.1]; wilson | control | - |
| null_strict | S2_pc1_null_silent_superclass | PASS | 0 [0, 0] in [-inf, 0.1] | control | - |
| pc1_song | P1_pc1_14a_pulse_over_sine | PASS | point, no interval | independent | STALE |
| pc1_song | P2_pc1_13_14_pulse_over_sine | PASS | point, no interval | independent | STALE |
| pc1_song | P3_14a_exceeds_15_16_on_pulse | PASS | point, no interval | independent | STALE |
| pc1_song | P4_null_silent | PASS | point, no interval | control | STALE |
| sugar_laterality | L1_sugar_contralateral_bias | PASS | point, no interval | structural | STALE |

Flags: PERTURBED = run under FLYCNS_* overrides (robustness variant); DIRTY = uncommitted code; DATA-MISMATCH = data differ from data/MANIFEST.json; STALE = the model code has changed since this report (unstamped: over an hour older than the newest); UNSTAMPED = written before integrity stamping, rerun to stamp; UNPINNED = no record of the input tables; ALLOW-DIRTY = run with FLYCNS_ALLOW_DIRTY=1, which waives the integrity guards; TRIALS a<b = run at fewer trials than the canonical b.

Declared deviations from the raw connectome: see each results/*/provenance.md and flycns/graph.py.

**WARNING: reports produced by code that has changed since: a2_registered, a2_robustness, dnp13_control, feeding_by_modality, flight_loop, flight_snpp16, flight_snpp16_graded, flight_snpp16_robustness, gustatory_signed_map, pc1_song, peptide_asta, sugar_laterality. Rerun them before quoting this table.**

## Report provenance
| benchmark | written | commit | data (neurons / edges) | env overrides |
|---|---|---|---|---|
| a2_registered | 2026-10-11T14:39:08 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| a2_robustness | 2026-10-11T15:21:36 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| auditory | 2026-10-11T18:08:30 | a4eef18 | 06ea0afb48c414ad / becf568580708ba9 | - |
| dnp13_control | 2026-10-11T13:02:29 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| feeding | 2026-10-11T18:20:02 | a4eef18 | 06ea0afb48c414ad / becf568580708ba9 | - |
| feeding_by_modality | 2026-10-11T13:05:49 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_loop | 2026-10-11T13:58:53 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16 | 2026-10-11T13:04:51 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16_graded | 2026-10-11T13:21:06 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| flight_snpp16_robustness | 2026-10-11T14:29:09 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| gf_escape | 2026-10-11T17:19:59 | a4eef18 | 06ea0afb48c414ad / becf568580708ba9 | - |
| gustatory_signed_map | 2026-10-11T13:41:45 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| null_strict | 2026-10-11T18:49:21 | a4eef18 | 06ea0afb48c414ad / becf568580708ba9 | - |
| pc1_song | 2026-10-11T13:32:02 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| peptide_asta | 2026-10-11T13:32:02 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |
| sugar_laterality | 2026-10-11T13:11:08 | d72fe77 | 06ea0afb48c414ad / becf568580708ba9 | - |

## Citation check: 48/48 tags resolve in REFERENCES.md

## Stamp inventory
93 of 93 result files carry a stamp (commits: d72fe77 x84, a4eef18 x9); 84 flagged, 0 unstamped.
- flagged: results/a2_registered/report.json (STALE)
- flagged: results/a2_robustness/gain_0.4/report.json (STALE)
- flagged: results/a2_robustness/gain_0.5/report.json (STALE)
- flagged: results/a2_robustness/gain_0.6/report.json (STALE)
- flagged: results/a2_robustness/gain_0.7/report.json (STALE)
- flagged: results/a2_robustness/gain_0.8/report.json (STALE)
- flagged: results/a2_robustness/report.json (STALE)
- flagged: results/auditory_wing/trace.json (STALE)
- flagged: results/brainsets/flycns_sim_loom.h5 (STALE)
- flagged: results/brainsets/flycns_sim_sound.h5 (STALE)
- flagged: results/brainsets/flycns_sim_taste.h5 (STALE)
- flagged: results/checks/engines_real.json (STALE)
- flagged: results/checks/modulator_checks.json (STALE)
- flagged: results/dnp13_control/report.json (STALE)
- flagged: results/dnp31/trace.json (STALE)
- flagged: results/embodiment/gate.json (STALE)
- flagged: results/feeding/afferent_influence.csv (STALE)
- flagged: results/feeding/afferent_screen_200Hz_w0.3.csv (STALE)
- flagged: results/feeding/afferent_screen_50Hz_w0.3.csv (STALE)
- flagged: results/feeding/afferent_screen_50Hz_w0.45.csv (STALE)
- flagged: results/feeding/afferent_screen_50Hz_w0.6.csv (STALE)
- flagged: results/feeding/afferent_screen_50Hz_w0.75.csv (STALE)
- flagged: results/feeding/afferent_screen_50Hz_w1.0.csv (STALE)
- flagged: results/feeding/mechanism.json (STALE)
- flagged: results/feeding_by_modality/report.json (STALE)
- flagged: results/fit_baseline/best.json (STALE)
- flagged: results/fit_baseline/grid.csv (STALE)
- flagged: results/fit_gains/best.json (STALE)
- flagged: results/fit_gains/grid.csv (STALE)
- flagged: results/fit_gf_adapt/best.json (STALE)
- flagged: results/fit_gf_adapt/grid.csv (STALE)
- flagged: results/fit_regional/best.json (STALE)
- flagged: results/fit_regional/grid.csv (STALE)
- flagged: results/flight_loop/report.json (STALE)
- flagged: results/flight_snpp16/report.json (STALE)
- flagged: results/flight_snpp16_graded/report.json (STALE)
- flagged: results/flight_snpp16_robustness/report.json (STALE)
- flagged: results/gustatory_signed_map/report.json (STALE)
- flagged: results/gustatory_signed_map/signed.csv (STALE)
- flagged: results/gustatory_signed_map/unsigned.csv (STALE)
- flagged: results/nt_confidence.json (STALE)
- flagged: results/overnight/minweight10/auditory_report.json (STALE)
- flagged: results/overnight/minweight10/feeding_report.json (STALE)
- flagged: results/overnight/minweight10/gf_escape_report.json (STALE)
- flagged: results/overnight/minweight20/auditory_report.json (STALE)
- flagged: results/overnight/minweight20/feeding_report.json (STALE)
- flagged: results/overnight/minweight20/gf_escape_report.json (STALE)
- flagged: results/overnight/null_superclass/auditory_report.json (STALE)
- flagged: results/overnight/null_superclass/feeding_report.json (STALE)
- flagged: results/overnight/null_superclass/gf_escape_report.json (STALE)
- flagged: results/overnight/seed1/auditory_report.json (STALE)
- flagged: results/overnight/seed1/feeding_report.json (STALE)
- flagged: results/overnight/seed1/gf_escape_report.json (STALE)
- flagged: results/overnight/seed2/auditory_report.json (STALE)
- flagged: results/overnight/seed2/feeding_report.json (STALE)
- flagged: results/overnight/seed2/gf_escape_report.json (STALE)
- flagged: results/overnight/signflip05_a/auditory_report.json (STALE)
- flagged: results/overnight/signflip05_a/feeding_report.json (STALE)
- flagged: results/overnight/signflip05_a/gf_escape_report.json (STALE)
- flagged: results/overnight/signflip05_b/auditory_report.json (STALE)
- flagged: results/overnight/signflip05_b/feeding_report.json (STALE)
- flagged: results/overnight/signflip05_b/gf_escape_report.json (STALE)
- flagged: results/overnight/signflip10/auditory_report.json (STALE)
- flagged: results/overnight/signflip10/feeding_report.json (STALE)
- flagged: results/overnight/signflip10/gf_escape_report.json (STALE)
- flagged: results/overnight/signflip_targeted/auditory_report.json (STALE)
- flagged: results/overnight/signflip_targeted/feeding_report.json (STALE)
- flagged: results/overnight/signflip_targeted/gf_escape_report.json (STALE)
- flagged: results/overnight/wscale025/auditory_report.json (STALE)
- flagged: results/overnight/wscale025/feeding_report.json (STALE)
- flagged: results/overnight/wscale025/gf_escape_report.json (STALE)
- flagged: results/overnight/wscale035/auditory_report.json (STALE)
- flagged: results/overnight/wscale035/feeding_report.json (STALE)
- flagged: results/overnight/wscale035/gf_escape_report.json (STALE)
- flagged: results/overnight/wscale040/auditory_report.json (STALE)
- flagged: results/overnight/wscale040/feeding_report.json (STALE)
- flagged: results/overnight/wscale040/gf_escape_report.json (STALE)
- flagged: results/pc1_song/report.json (STALE)
- flagged: results/peptide_asta/report.json (STALE)
- flagged: results/sensitivity_cord/grid.csv (STALE)
- flagged: results/sensitivity_cord/summary.json (STALE)
- flagged: results/sensitivity_flight/grid.csv (STALE)
- flagged: results/sensitivity_flight/summary.json (STALE)
- flagged: results/sugar_laterality/report.json (STALE)
- exempt: results/turner2022/ (input extraction from 22 GB of Turner et al. 2022 imaging; its output is a model input, hashed into every report's loom_input stamp)
