"""
What each scored check is evidence of.

A check that a parameter was tuned to pass is not evidence that the model is right; it only shows
the tuning worked. This table records, for every scored check, which of six roles it plays.
benchmarks/summarize.py prints the role beside every result and counts only INDEPENDENT checks as
tests of the model. The parameters behind the CALIBRATED and CONSTRUCTION entries, and the rule
each was set by, are listed in docs/CALIBRATION.md.

  calibrated    a free parameter was chosen, at least partly, to make this check pass
  construction  guaranteed by a parameter entered from the same measurement the check cites
  independent   not a target of any fit; a genuine test (pre-registered where marked)
  control       a null model, ablation or positive control: shows the machinery is not trivial
  robustness    re-tests a result under perturbation
  structural    a count over the wiring graph with no simulation: evidence about the connectome's
                structure, not about the model's dynamics, so it is not counted as a test of the model

A check missing from this table is reported as UNCLASSIFIED and counted as not independent.
"""

CAL, CON, IND, CTL, ROB, STR = "calibrated", "construction", "independent", "control", "robustness", "structural"

CHECK_ROLES = {
    "gf_escape": {
        "gf_spikes_per_response_1_to_2": (CAL, "GF adaptation b_adapt (fit_gf_adapt.py) and the loom rate scale PEAK_HZ were both set to give 1-2 spikes"),
        "gf_response_prob_0.5_to_1": (CAL, "PEAK_HZ anchored to P(response) >= 0.5; b_adapt fit rule includes P 0.5-1"),
        "gf_latency_10_60ms": (IND, "not a fit target"),
        "ttmn_one_to_one": (CON, "9 mV GF->TTMn spikelet chosen so one GF spike is suprathreshold (1:1 relay, Tanouye & Wyman 1980)"),
        "ttmn_lag_0.5_1.5ms": (CON, "gap-junction delay 0.8 ms entered from Tanouye & Wyman 1980"),
        "cns_quiet": (CAL, "global weight scale w_scale was chosen partly on population rate (scripts/legacy/sweep.py)"),
        "electrical_necessary": (CTL, "ablation of the declared electrical synapses"),
        "null_silent": (CTL, "degree-preserving rewired null"),
    },
    "auditory": {
        "A2_jo_effect_on_near_threshold_loom_REPORTED": (IND, "reported here; scored in a2_registered"),
        "A1_jo_alone_mostly_subthreshold": (CAL, "JON->GF coupling calibrated to a 3 mV subthreshold compound potential (value untraced)"),
        "A3_declared_pairs_carry_jo_drive": (CTL, "ablation of the declared mixed synapse"),
        "A4_null_silent": (CTL, "rewired null; note it removes the declared pathway as A3 does, so it cannot fail where A3 passes"),
        "A5_cns_quiet": (CAL, "w_scale was chosen partly on population rate under auditory drive"),
    },
    "a2_registered": {
        "A2R_facilitation": (CON, "the working-point rule parks loom-alone GF within ~2 mV of threshold and sound adds a hand-set, "
                                  "untraced 3 mV compound potential; in a one-compartment cell summation of the two crosses threshold "
                                  "unless polysynaptic inhibition intervenes. Facilitation was also scored (no parameter moved) during "
                                  "the gain fits (fit_gains.py, fit_regional.py). Pre-registered, but not independent"),
        "A2R2_beyond_summation": (IND, "registered version 2: facilitation beyond what adding the model's own measured "
                                       "sound-alone depolarisation to each loom-alone trial predicts; the part of A2 that "
                                       "is not arithmetic"),
    },
    "a2_robustness": {
        "RA2_facilitation_at_every_near_threshold_gain": (ROB, "pre-registered sweep of A2R (itself construction)"),
    },
    "feeding": {
        "F1_laterality_matches_wiring": (IND, "not a fit target; scored only when MN9 responds to one-sided drive"),
        "F1_shiu_contralateral_bias": (IND, "not applicable to this drive; tested in sugar_laterality"),
        "F2_dose_response_REPORTED": (IND, "reported, not scored"),
        "F3_bitter_suppresses": (IND, "not a fit target; scored only when a bitter GRN type resolves"),
        "F2b_extra_SEZ_quiet": (CAL, "w_scale was chosen partly on population rate"),
        "F2c_motor_rate_physiological": (CON, "cb_motor adaptation (10 mV) entered to keep sustained motor rates under 100 Hz"),
        "F4_second_order_sufficient": (IND, "scored only with Shiu's cell names; with the fallback (MN9's own strongest inputs) it is reported, not scored"),
        "F5_null_silent": (CTL, "rewired null; scored only when the real network responds (MN9 >= 0.5 at 50 Hz)"),
    },
    "feeding_by_modality": {
        "F2_sugar_ratio_exceeds_bitter": (STR, "pre-registered; a ratio of synapse counts, no simulation"),
        "F3_sugar_drives_mn9_at_100hz": (IND, "pre-registered"),
        "F4_bitter_below_sugar_at_100hz": (IND, "pre-registered"),
    },
    "gustatory_signed_map": {
        "S1_valence_signed_on_proboscis": (STR, "pre-registered; signed path products, no simulation"),
        "S2_per_type_sign_agreement": (STR, "pre-registered; signed path products, no simulation"),
        "S3_LB2_dominates_pharyngeal_pumping": (STR, "pre-registered; signed path products, no simulation"),
    },
    "sugar_laterality": {
        "L1_sugar_contralateral_bias": (STR, "pre-registered prediction from Shiu et al. 2024; signed path products, no simulation"),
    },
    "pc1_song": {
        "P1_pc1_14a_pulse_over_sine": (IND, "pre-registered"),
        "P2_pc1_13_14_pulse_over_sine": (IND, "pre-registered"),
        "P3_14a_exceeds_15_16_on_pulse": (IND, "pre-registered"),
        "P4_null_silent": (CTL, "pre-registered rewired null"),
    },
    "dnp13_control": {
        "D1_dnp13_reachable": (CTL, "pre-registered positive control"),
        "D2_pc1_1b_sine_choice": (IND, "pre-registered"),
    },
    "flight_loop": {
        "L1a_DVMn_2_to_12_hz": (CAL, "afferent load anchored by rule to put DVMn 1a-c in 2-12 Hz"),
        "L1b_DLMn_cf_2_to_12_hz": (IND, "not a fit target"),
        "L2_b1_0.5_to_1.2_spikes_per_wingbeat": (IND, "not a fit target"),
        "L3_leg_mn_not_entrained": (IND, "not a fit target"),
        "L4_steering_specific_vs_null": (CTL, "rewired null"),
        "L5_DLMn_cf_2_to_12_hz_with_DNg02": (IND, "not a fit target"),
        "L6_DVMn_still_in_band_with_DNg02": (IND, "not a fit target"),
    },
    "flight_snpp16": {
        "N1_snpp16_sufficient_dvmn_in_band": (IND, "stated before the run"),
        "N2_snpp16_necessary_dvmn_below_2hz": (IND, "stated before the run"),
    },
    "flight_snpp16_graded": {
        "G1_graded": (IND, "pre-registered"),
        "G2_in_band_window": (IND, "pre-registered"),
        "G3_selective_at_k_star": (IND, "pre-registered"),
        "G4_wiring_specific_at_k_star": (CTL, "pre-registered rewired null"),
        "G5_reliable_at_k_star": (IND, "pre-registered"),
    },
    "flight_snpp16_robustness": {
        "R1_survives_transmitter_uncertainty": (ROB, "pre-registered"),
        "R2_selectivity_holds_across_cord_params": (ROB, "pre-registered"),
        "R3_replicates_with_fresh_draws": (ROB, "pre-registered"),
    },
    "null_strict": {
        "S1_escape_null_silent_superclass": (CTL, "pre-registered stricter null"),
        "S2_pc1_null_silent_superclass": (CTL, "pre-registered stricter null"),
    },
    # the JON -> GF contact as EM annotates it (benchmarks/a2_contact.py), registered version 2
    "a2_contact_em": {"C1_em_facilitation": (IND, "registered; no hand-set sound potential: the contact as EM annotates it. "
                                                  "Not blind: the committed reference arm showed this contact firing the "
                                                  "giant fiber on every sound-alone trial before registration, so its "
                                                  "subthreshold part was expected to fail; nothing was tuned either way")},
    "a2_contact_em_flip": {"C2_flip_no_facilitation": (CTL, "registered control: the same contact sign-inverted")},
    # degree-corrected null distribution (benchmarks/null_distribution.py)
    "null_dc_escape": {"N1_escape_gf_wiring_specific": (CTL, "real readout vs 20 degree-corrected null draws")},
    "null_dc_song": {"N2_song_pmp2_wiring_specific": (CTL, "real readout vs 20 degree-corrected null draws")},
    "null_dc_auditory": {"N3_jo_gf_chemical_wiring_specific": (CTL, "real readout vs 20 degree-corrected null draws")},
}


def role(benchmark, check):
    return CHECK_ROLES.get(benchmark, {}).get(check, ("unclassified", "add it to flycns/calibration.py"))
