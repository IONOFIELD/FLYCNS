# FLYCNS synapse-model literature review: conductance-based E/I, GABA_B, AL gap junctions, runaway fixes

Date: 18 Oct 2026. Read-only. No repo edits were made and no messages were sent.

**Tags.**
- **VERIFIED**: I read the claim in the saved source, at the section, figure or table given.
- **VERIFIED-fig**: I read the value off a figure panel by eye (≈, roughly ±10–20 % of the value). The text does not state the number.
- **INFERRED**: my own calculation or interpretation from verified values.
- **CAN'T VERIFY**: I could not read the source. I say what I read instead.

**Where the sources are.** Full texts are in `/workspace/flycns/lit/`. `PMCxxxx.txt` is the extracted text and `.html`/`.xml` is the original. Figure images are `*_fig*.jpg`. The FlyWire/hemibrain/Shiu chemical-only quotes and Yaksi & Wilson 2010's "eLN" quotes were verified earlier and are not repeated here; they are in `phaseA_checklist_2026-10-18.md` §4.

**Temperature.** None of the in vivo Wilson-lab papers I read gives a recording temperature in the text. Fly-rearing temperature (25 °C) is stated. The O'Dowd-lab culture and explant papers say "room temperature". Every in vivo τ below is therefore at an unstated temperature, presumably room temperature (INFERRED).

---

## (a) Parameter table

| Parameter | Value (units) | Cell / synapse | Preparation | Source + location | Tag |
|---|---|---|---|---|---|
| **Reversal potentials** | | | | | |
| E_nACh, measured | +8.9 ± 1.7 mV (n=9) | cholinergic synaptic currents, pupal neurons | cultured pupal brain neurons, whole-cell, RT | Su & O'Dowd 2003 J Neurosci, Results (PMC6740836) | VERIFIED |
| E_nACh, stated | ≈0 mV ("the reversal potential for the cholinergic currents") | embryonic neurons | culture, RT | Lee, Su & O'Dowd 2003 J Neurosci, Results (PMC6740792) | VERIFIED |
| E_syn (nACh) used in fly PN models | −10 mV, "close to the measured reversal potential for nicotinic acetylcholine receptors" (cites Hille 1992, not a fly measurement) | ORN→PN | model fitted to in vivo data | Nagel, Hong & Wilson 2015 Nat Neurosci, Methods (PMC4289142); also Gouwens & Wilson 2009 model, Methods (PMC2709801) | VERIFIED |
| E_GABA (Cl), measured | −37 ± 3 mV (n=4), vs calculated E_Cl −45 mV | GABAergic sPSCs | cultured pupal neurons, RT | Su & O'Dowd 2003, Results | VERIFIED |
| E_GABA (Cl), measured | −41.5 ± 2.1 mV (n=5), vs calculated E_Cl −45 mV (24 mM Cl_in / 153 mM Cl_out); −1.1 ± 2.6 mV in symmetric Cl | GABA sPSCs (Rdl-dependent) | cultured embryonic neurons, RT, 5 mV LJP corrected | Lee, Su & O'Dowd 2003, Results | VERIFIED |
| E_GABA, measured | −56 ± 3 mV (6 of 9 neurons); in 3 of 9 neurons GABA depolarized by ≤16 mV and evoked APs | larval VNC (motor) neurons | larval CNS, whole-cell | Rohrbough & Broadie 2002 J Neurophysiol, Results + Fig 3B2 | VERIFIED via a search-index excerpt only. The page is Cloudflare-blocked; the excerpt is saved as `rohrbough2002_excerpt.txt` |
| E_GluCl (glutamate-evoked Cl), measured | reverses "in the range of −50 to −60 mV"; blocked by PTX | larval VNC neurons | larval CNS | Rohrbough & Broadie 2002, Fig 3C2 legend (excerpt) | VERIFIED (excerpt only, as above) |
| E_GluCl, adult central neuron | not reported. Liu & Wilson 2013 (GluClα in PNs and LNs) give no reversal; searches of the text for "revers" and "mV" in that context found nothing | AL PNs / LNs | in vivo | Liu & Wilson 2013 PLoS Biol (PMC3690841) | CAN'T VERIFY (not measured in the source) |
| E_Cl imposed by the pipette in the Wilson & Laurent recordings | ≈ −120 mV (Cl_in ≈1 mM KCl; Cl_out ≈117 mM from 103 NaCl + 3 KCl + 2×1.5 CaCl2 + 2×4 MgCl2) | PNs, LNs | in vivo whole-cell | composition from Wilson & Laurent 2005 J Neurosci, Methods (PMC6725763); the paper says the solution "yielded a GABA reversal potential near E Cl" (supp Fig 1, not read) | INFERRED (my Nernst calculation, 22 °C). This is an artefact of the pipette, not physiology |
| Physiological E_Cl, adult central neuron in vivo (gramicidin or other non-dialysing method) | **no measurement found** | n/a | n/a | WebSearch on 18 Oct 2026 found none | CAN'T VERIFY (absent) |
| Inhibitory reversal used in fly models | −70 mV (Nagel 2015: postsynaptic inhibition "reversed at −70 mV"); −70 mV GABA_A (Huang 2018 Flysim) | PN; whole brain | models | Nagel 2015 Methods; Huang et al. 2018 Methods (PMC6335393) | VERIFIED (model choices, not measurements) |
| **Resting potential / passive** | | | | | |
| PN "true" resting potential | ≈ −55 to −60 mV with ORN input intact; ≈ −65 mV with ORN input removed | DM1 / GH146 PNs | in vivo, after correcting for seal leak | Gouwens & Wilson 2009 J Neurosci, Discussion; Fig 7C,D (−47.8 ± 1.6 → −57.8 ± 1.5 mV, n=12) | VERIFIED |
| PN E_leak used in model | −70 mV ("close to the resting potential of PNs in tetrodotoxin") | PN | model | Nagel 2015 Methods | VERIFIED |
| PN input resistance | 598.0 ± 69.3 MΩ (n=14, antennae removed) | PN | in vivo | Gouwens & Wilson 2009 Results | VERIFIED |
| PN τ_m used in model | 5 ms, with R_m 800 MΩ | PN | model | Nagel 2015 Methods | VERIFIED |
| PN spike threshold | −39 ± 1 mV | PN | in vivo whole-cell | Wilson & Laurent 2005 Results | VERIFIED |
| KC resting potential | −60.9 ± 1.7 mV; R_in ≈ 1 GΩ | Kenyon cells | adult whole brain explant, RT, 5 mV LJP corrected | Gu & O'Dowd 2006 J Neurosci, Results / Table 1 (PMC6674319) | VERIFIED |
| Larval VNC resting potential | −50 to −60 mV | motor neurons | larval CNS | Rohrbough & Broadie 2002 abstract (excerpt) | VERIFIED (excerpt only) |
| FLYCNS / Shiu values, for comparison | V_rest −52 mV, V_th −45 mV, τ_m 20 ms (from R 10 kΩ·cm² × C 2 µF·cm⁻²), τ_syn 5 ms, T_ref 2.2 ms | all neurons | model | Shiu et al. 2024 Nature, Methods "Computational model" (PMC11446845) | VERIFIED. The τ_m = 20 ms product is INFERRED arithmetic |
| **Fast nACh kinetics** | | | | | |
| mEPSC rise / half-decay | rise ≈1.05–1.12 ms; half-decay ≈2.1–2.45 ms; amplitude ≈1.65–1.85 pA | ORN→PN (DM6, VM2, DL5, DM4) | in vivo voltage clamp, V_hold −65 mV, flies reared at 25 °C | Kazama & Wilson 2008 Neuron Fig 6C (PMC2429849; `kazama2008_fig6.jpg`) | VERIFIED-fig |
| Evoked ORN→PN EPSC, fast component | τ_g 9.3 ms; k 20 nS/spike; depression r 0.23, τ_A 1006 ms (curare-sensitive) | ORN→PN | in vivo, model fit | Nagel 2015 Methods | VERIFIED |
| Evoked ORN→PN EPSC, slow component | τ_g 80 ms; k 1.8 nS/spike; r 0.0073, τ_A 33,247 ms (IMI-sensitive) | ORN→PN | in vivo, model fit | Nagel 2015 Methods | VERIFIED |
| Gouwens model synapse | E_syn −10 mV; single site rise 0.01 ms, decay 0.6 ms, gmax 0.1 nS; distributed over 25 branches, rise 0.2 ms, decay 1.1 ms | ORN→PN | compartmental model | Gouwens & Wilson 2009 Methods | VERIFIED |
| mEPSC rise / decay τ | rise 0.43 ± 0.05 ms, decay 1.4 ± 0.1 ms (KC); decay 1.5 ± 0.1 ms (GFP−); decay 1.7 ± 0.21 ms (Cha-Gal4) | cholinergic | cultured pupal neurons, RT | Su & O'Dowd 2003 Table 1 + Results | VERIFIED |
| mEPSC rise / decay τ | rise 1.53 ± 0.09 ms, decay 5.23 ± 0.41 ms, amplitude 4.0 pA (OK107 GFP+); WT decay 6.73 ± 1.43 ms; 201Y GFP− decay 4.45 ms | KCs (cholinergic) | adult brain explant, RT | Gu & O'Dowd 2006 Table 1 | VERIFIED |
| Short-term depression of ORN→PN | f 0.78, τ 893 ms (Fig 1c); IMI-resistant f 0.77, τ 1006 ms; curare-resistant f 0.91, τ 629 ms | ORN→PN | in vivo | Nagel 2015 Fig 1 / Results | VERIFIED |
| **GABA_A (Rdl) kinetics** | | | | | |
| mIPSC rise / decay τ | rise 0.80 ± 0.20 ms, decay 3.7 ± 0.9 ms (KC); decay 3.3 ± 0.5 ms (GFP−) | GABAergic | cultured pupal neurons, RT | Su & O'Dowd 2003 Table 1 | VERIFIED |
| mIPSC rise / decay τ | rise 0.88 ± 0.03 ms, decay 5.4 ± 0.3 ms (WT); Rdl decay 5 ± 0.3 ms. Decay shortens 1.5–2× with time in culture | GABAergic | cultured embryonic neurons, RT | Lee, Su & O'Dowd 2003 Table 1 | VERIFIED |
| In vivo AL GABA_A IPSC kinetics | **not measured** in the papers read | LN→PN, LN→LN | n/a | n/a | CAN'T VERIFY (absent) |
| **GABA_B (AL)** | | | | | |
| Fraction of the PN GABA response that is picrotoxin-resistant | picrotoxin 250 µM "suppressed less than one-half" (≈55 % remained); CGP54626 50 µM blocked the PTX-resistant part "by 97 ± 2%; n = 5" | PN (iontophoretic GABA) | in vivo | Wilson & Laurent 2005 Results, Fig 2B1 (`wilsonlaurent2005_fig2.jpg`) | VERIFIED (text); ≈55 % is VERIFIED-fig |
| GABA_B in LNs | none: PTX blocked 98 ± 3 % (n=6); CGP 101 ± 6 % (n=5); "GABA inhibits LNs solely via a GABA A-type conductance" | LNs | in vivo | Wilson & Laurent 2005 Results | VERIFIED |
| GABA_B time course, postsynaptic in PNs | CGP-sensitive component peaks later than the PTX-sensitive one and lasts ≈1 s or more | PN (iontophoresis) | in vivo | Wilson & Laurent 2005 Fig 2C3 | VERIFIED-fig |
| GABA_B effect on odor responses | CGP: early (0–0.5 s) ≈34→47 Hz, late (1.5–2.5 s) ≈6.6→12.6 Hz. PTX: early ≈48→73 Hz, no late effect. CGP fully blocked slow inhibition in 15/29 cell-odor pairs and shortened it in 10/29 | PN | in vivo | Wilson & Laurent 2005 Fig 3 + Results | VERIFIED (counts); VERIFIED-fig (rates) |
| Presynaptic GABA_B on ORN terminals | odor-evoked lateral inhibition depresses ORN→PN EPSCs to ≈25–30 % of baseline. With CGP alone the minimum is ≈50 % and recovery is complete by ≈1.5 s. CGP + PTX blocks it; PTX alone has no clear effect. "The late phase of inhibition evidently involves only GABA B receptors" | ORN→PN | in vivo | Olsen & Wilson 2008 Nature, Fig 3c,f + text (PMC2824883; `olsen2008_fig3.jpg`) | VERIFIED (quote); VERIFIED-fig (%) |
| Presynaptic inhibition onset | "fit with an alpha function with a time constant of about 25 ms"; "Both antagonists are required to block inhibition in this circuit" (CGP54626 50 µM + PTX 5 µM) | LN→ORN terminal (mainly), smaller on PN dendrites | in vivo | Nagel 2015 Fig 6 + Results | VERIFIED |
| GABA_B gain effect | CGP54626 25 µM raised the PN input-output slope by 105 % (nerve stimulation); odor-specific: cVA/DA1 +153 %, ethyl hexanoate/DM2 +67 %, 2-PE/VA3 +43 %; CO2 (V glomerulus) ORNs lack GABA_BR | ORN→PN | isolated brain, GCaMP, flies reared at 22–25 °C | Root et al. 2008 Neuron, Results (PMC2539065) | VERIFIED |
| **Electrical coupling (coupling coefficient k = ΔV_post/ΔV_pre at the soma)** | | | | | |
| Sister PN–PN (homotypic) | depol ≈0.034, hyperpol ≈0.013; in Cd2+ ≈0.016 / ≈0.011 (mixed chemical + electrical); heterotypic ≈0 | PN pairs, same glomerulus | in vivo dual whole-cell | Kazama & Wilson 2009 Nat Neurosci Fig 7d (PMC2751859; `kazama2009_fig7.jpg`) | VERIFIED-fig |
| Sister PN–PN, shakB dependence | depol ≈0.018, hyperpol ≈0.007 (control), **both abolished in shakB2**; 4 vs 4 pairs, 8 coefficients each, p<0.0005, Mann-Whitney | DA1 PN pairs | in vivo | Yaksi & Wilson 2010 Neuron Fig 6C (PMC2954501; `yaksi2010_fig6.jpg`) | VERIFIED-fig (values); VERIFIED (stats) |
| eLN→PN | depol ≈0.010 (≈0.014 in Cd2+); ≈0.009 control vs ≈0 in shakB2; hyperpol ≈0.003; n = 37 control, 19 shakB2 pairs | eLN→PN | in vivo | Yaksi & Wilson 2010 Fig 4C | VERIFIED-fig |
| PN→eLN | depol ≈0.032 control → ≈0.005 in Cd2+ (mostly chemical); ≈0.018 vs ≈0.016 in shakB2; hyperpol ≈0.005, abolished in shakB2 | PN→eLN | in vivo | Yaksi & Wilson 2010 Fig 4F | VERIFIED-fig |
| Caveat on k | the coefficients "almost certainly underestimate the strength of the connection" (somatic electrodes, electrotonically distant dendrites) | all | n/a | Yaksi & Wilson 2010 Results | VERIFIED |
| Implied junctional conductance | g_c ≈ k / (R_in (1−k)) ≈ 0.005–0.06 nS soma-equivalent (k 0.003–0.034, R_in 0.6 GΩ); as a ratio to leak, g_c/g_L ≈ k/(1−k) ≈ 0.003–0.035 | PN–PN, eLN–PN | n/a | from the rows above + Gouwens R_in | INFERRED (two-cell steady-state approximation; a lower bound) |
| Huang et al. 2010 PN–PN numbers | reciprocal excitation by "dendrodendritic cholinergic synapses and gap junctions"; numbers unread | PN–PN | in vivo | Neuron 2010; ScienceDirect is JS-only and cell.com is behind Cloudflare | CAN'T VERIFY (abstract only, via PubMed/WebSearch) |

---

## (b) Per-topic notes and key quotes

### 1. Conductance-based parameters

- **Excitatory reversal.** Fly measurements are in culture only: +8.9 mV (Su & O'Dowd 2003) and "0 mV" (Lee et al. 2003). Wilson-lab models use −10 mV and cite Hille, not fly data. Nagel 2015 Methods: "E syn to −10 mV, which is close to the measured reversal potential for nicotinic acetylcholine receptors". Any value from −10 to +10 mV is defensible. The choice matters little: from rest (≈−55 mV) the driving force changes by <30 %. INFERRED.
- **Chloride reversal is the real hole.** Every adult in vivo recording I found used whole-cell dialysis, so the pipette imposed E_Cl. In Wilson & Laurent 2005 that was ≈−120 mV (INFERRED). Culture values (−37 to −45 mV) are also set by the pipette Cl (24 mM). The only non-culture value is from larval VNC: "currents that clearly reversed at negative holding potentials (−56 ± 3 mV) in six of nine neurons" (Rohrbough & Broadie 2002, excerpt). This puts E_Cl near rest, so inhibition there acts mainly by shunting and can even be depolarizing in some cells ("In three of nine neurons, GABA elicited depolarizing responses"). For glutamate (GluCl) the same paper says "reverse in the range of −50 to −60 mV". Liu & Wilson 2013 established GluClα-mediated glutamatergic inhibition of PNs and LNs, but I found no reversal potential or kinetics in the text.
- **Rest.** Gouwens & Wilson 2009: "true resting potential ... approximately −55 to −60 mV when spontaneous synaptic input from ORNs is intact and approximately −65 mV when input from ORNs is removed." FLYCNS's −52 mV (from Shiu) sits at the depolarized edge of this range.
- **Kinetics.** These are fast, roughly AMPA-like, plus a slow tail.
  - Fast nACh: mEPSC decay ≈1.4–1.7 ms in culture; ≈5–7 ms in KCs in situ; half-decay ≈2.1–2.5 ms in PNs in vivo.
  - Evoked ORN→PN EPSC: Kazama & Wilson 2008 found the evoked EPSCs "had two decay phases". Nagel fits τ_g 9.3 ms (fast, curare-sensitive) and 80 ms (slow, IMI-sensitive), with strong depression (τ_rec ≈1 s).
  - GABA_A mIPSC decay is ≈3.3–5.4 ms (culture), i.e. **inhibition decays about 2–3× slower than excitation in the same preparation** (Su & O'Dowd Table 1: 1.4 vs 3.7 ms in KCs). VERIFIED values; the ratio is INFERRED.
  - FLYCNS's shared τ_syn = 5 ms comes from Shiu ref 61 (Jürgensen et al. 2021, a neuromorphic larva model), not from a fly measurement. VERIFIED for the citation.

### 2. GABA_B in the AL

- It is present presynaptically on ORN terminals and postsynaptically on PNs, and it is absent from LNs.
- Wilson & Laurent 2005: "GABA inhibits LNs solely via a GABA A-type conductance". The effect of CGP54626 is "attributable at least in part to postsynaptic GABA B receptors".
- Olsen & Wilson 2008: lateral inhibition is mostly presynaptic, through both receptor types on the same terminal, and "The late phase of inhibition evidently involves only GABA B receptors". Pertussis toxin in ORNs makes inhibition briefer and CGP-insensitive.
- Nagel 2015: inhibition "acts primarily on ORN axon terminals, with a smaller effect on PN dendrites". The onset is an alpha function with τ ≈ 25 ms, and "Both antagonists are required to block inhibition in this circuit".
- Time course: the GABA_B component lasts ≈1–2 s (Olsen Fig 3c,f; Wilson & Laurent Fig 2C3, Fig 3 late window). VERIFIED-fig.
- Gain: Root 2008 found that blocking GABA_B roughly doubles PN input-output slope (+105 %). The effect varies by glomerulus (cVA/DA1 +153 % … VA3 +43 %; none for CO2/V).
- **Relevance to FLYCNS (INFERRED).** The main AL brake in vivo is a slow, divisive presynaptic depression of ORN→PN release. A point-neuron model with fast subtractive inhibition has neither the presynaptic site nor the 1–2 s time scale. The nearest single-variable equivalent is a slow GABA_B-like inhibitory conductance from LNs. Placing it on the ORN→PN synaptic efficacy is better still: multiply w(ORN→PN) by (1 − s_GABAB).

### 3. eLN–PN and PN–PN coupling

- All values are soma-measured coefficients k ≈ 0.003–0.034, read from figures (table above).
- shakB2 abolishes:
  - sister PN–PN coupling (both directions of polarization; Yaksi Fig 6C);
  - eLN→PN depolarizing coupling;
  - PN→eLN hyperpolarizing coupling.
- PN→eLN depolarization is largely Cd2+-sensitive, i.e. chemical (Yaksi Fig 4F).
- Kazama & Wilson 2009 describe sister-PN coupling as mixed chemical/electrical. Heterotypic PN pairs are uncoupled.
- These ks are lower bounds (Yaksi quote above). Expressed as a fraction of leak conductance they give g_gap/g_L ≈ 0.003–0.035 (INFERRED). That is weak per pair, but eLNs contact many PNs.
- Huang 2010 numbers: CAN'T VERIFY.

### 4. Large-scale fly models and their synapse choices

- **Shiu et al. 2024 (whole-brain LIF, FlyWire).** "dv/dt=(g−(v−V_rest))/T_mbr; dg/dt=−g/τ" with g += w at each spike. One τ = 5 ms, sign set by predicted transmitter, no reversal potentials. "does not account for gap junctions"; "assume a basal firing rate of 0 Hz ... inhibitory connections to an inactive neuron have no effect". (Methods, PMC11446845.) VERIFIED.
- **Kakaria & de Bivort 2017 (fly central complex).** Current-based: "I PSC is the amplitude of a PSC (5 nA ...); excitatory and inhibitory PSCs were assumed to have the same magnitude but opposite sign". PSC half-life 5 ms. Raising excitatory drive produced "seizure" modes (modes 11–15). (PMC5306390.) VERIFIED.
- **Lappalainen et al. 2024 (visual system).** Non-spiking: "passive leaky linear non-spiking voltage dynamics"; synapse = α·σ·N·f(V_pre), threshold-linear, σ = ±1 by transmitter (ACh +; GABA, Glu, His −). Per-type τ is trained (initialized at 50 ms). No reversal potentials. The model "cannot ... account for ... electrical synapses, nonlinear chemical synapses and neuromodulation". (PMC11525180.) VERIFIED.
- **Pospisil et al. 2024 (effectome).** Linear model with W "scaled to have a maximum eigenvalue of 1 ... if it was too large the dynamics would be unstable". The Extended Data conductance model uses every reversal at 0 mV and τ = 10 ms. Reversal potentials etc. "can all corrupt proportionality". (PMC11446844.) VERIFIED.
- **Huang et al. 2018 (Flysim, FlyCircuit whole brain, 20,089 neurons).** Conductance-based LIF: V_rev 0 mV (AMPA/NMDA/ACh), −70 mV (GABA_A); V_rest −70, V_th −45, reset −55, τ_m 16 ms. See topic 5. (PMC6335393.) VERIFIED.
- **Gouwens & Wilson 2009; Nagel et al. 2015.** Single-circuit conductance models (table above).

### 5. Runaway / reverberation and the fixes used

- **Huang et al. 2018, fly, conductance-based.** Seizure-like activity occurred anyway.
  - Raising the I/E factor from 0.1 to 100 "moderately prolonged the onset of the seizure-like events, but did not completely eliminate them"; "once the seizure-like activity occurred, it never stopped".
  - The fix was **short-term depression**: dD/dt = (1−D)/τ_D − D(1−p_v)δ. With τ_D > 125 ms, seizure prevalence fell to ≤50 % in the reconstructed brain (Fig 7, τ_D 125–600 ms). STD did not stabilize a degree-preserving randomized brain even at τ_D = 1000 ms.
  - They also hit a GABA driving-force artefact: strong inhibition pushed V below V_rev, so GABA became depolarizing. They capped dV_max = V_th − V_rev. VERIFIED.
  - **This is the most important caution: conductance-based synapses alone did not prevent runaway in a whole fly-brain LIF.**
- **Billeh et al. 2019/2020 (mouse V1, ~230k neurons).** Two variants.
  - Biophysical: conductance-based Exp2Syn, reversals 0 / −70 mV, τ1/τ2 I→E 2.7/15, I→I 0.2/8, E→I 0.1/0.5, E→E 1/3 ms.
  - GLIF: "postsynaptic current-based" with τ_syn E→E 5.5, I→E 8.5, E→I 2.8, I→I 5.8 ms.
  - Both were grid-search tuned layer by layer "to ... avoid runaway excitation or epileptic-like activity". Only the biophysical variant is conductance-based ("weights in the GLIF model are current based while they are conductance based for the biophysical model"). The point that carries over is **per-pathway τ with slower inhibition onto E**, not COBA itself. VERIFIED (bioRxiv PDF, `billeh2019_biorxiv.txt`).
- **Brunel 2000 (delta current synapses).** "In the high νext, g < 4 region, only a very high-frequency (near saturation) stationary state can be found (H state)", at a rate "close to the saturation frequency, 1/τrp". FLYCNS's AL→AL is 84 % excitatory by synapse count. That corresponds to g < 4 unless inhibitory weights are much larger (INFERRED). VERIFIED (quote).
- **Vogels & Abbott 2005.** COBA with E_ex 0, E_inh −80, τ_ex 5, τ_inh 10 ms: "driving-force effects cause EPSPs to shrink and IPSPs to grow with increased depolarization ... This provides a stabilization mechanism ... buffering protects the network against excessively low or high firing rates". VERIFIED.
- **Kuhn et al. 2004.** τ_eff = C/G_tot. "shunting effect provided by the increased membrane conductance always dominates for high enough input rates". VERIFIED.
- **Cavallari et al. 2014.** COBA vs CUBA. Current-based neurons "cannot undergo such transitions" into the high-conductance state. The two are matched with g_syn = J/(⟨V⟩ − V_syn). Taus: GABA 0.25/5, AMPA→I 0.2/1, AMPA→E 0.4/2 ms. VERIFIED.
- **Why CUBA with a shared τ runs away but COBA saturates.** INFERRED synthesis of the quotes above.
  1. In CUBA a PSP is independent of V. Summed excitation can push V arbitrarily far above threshold, so rates are limited only by refractoriness (Brunel's H state). In COBA, excitation can drive V only toward E_exc. EPSPs shrink as V rises, and total conductance shortens τ_eff (Kuhn), which caps temporal summation.
  2. CUBA inhibition is subtractive and fixed in size. COBA inhibition grows with depolarization (Vogels & Abbott) and divides through shunting, so feedback strengthens exactly when activity is high.
  3. With a shared 5 ms τ, inhibition has the same window as excitation and arrives one synaptic delay later, so it cannot catch up with recurrent excitation. Measured fly kinetics show inhibition 2–3× slower (GABA_A) and 200× slower (GABA_B), and Billeh uses slower I→E. Longer inhibition integrates over more excitatory events.
  4. **However**, Huang 2018 shows that COBA alone is not sufficient in a fly connectome. Presynaptic depression (STD, or the presynaptic GABA_B on ORNs) was what stopped persistent seizures. And Rohrbough's E_Cl near rest suggests real fly inhibition is largely shunting.

---

## (c) What is not measured, with suggested defaults

| Unknown | Suggested default | Why |
|---|---|---|
| Physiological E_Cl (GABA_A/Rdl and GluCl) in adult central neurons | −65 mV (sweep −55 to −75) | Larval VNC −56 ± 3 mV (Rohrbough). Fly models use −70 (Nagel, Huang). −65 sits just below the PN rest range and gives mainly shunting inhibition. Avoid −120 mV (a pipette artefact). Pre-register the sweep; this is the single most consequential parameter. |
| E_nACh in adult neurons in vivo | 0 mV (sensitivity −10 / +10) | Culture: 0 and +8.9 mV. Models: −10 mV. |
| E_His (HisCl, photoreceptor/visual outputs) | same as E_Cl | Histamine gates Cl channels in flies (Lappalainen treats His as hyperpolarizing). No reversal read: CAN'T VERIFY. |
| GluCl kinetics (rise/decay) | same as GABA_A (rise 0.5 ms, decay 5 ms) | Not reported in Liu & Wilson 2013 or any source read. |
| In vivo GABA_A IPSC decay (LN→PN, LN→LN) | 5 ms (sweep 3–10) | Only culture values exist (3.3–5.4 ms, RT). |
| nACh decay for non-AL cell types (LH, MB output, VNC) | 2–5 ms fast | PN half-decay ≈2.1–2.5 ms in vivo; KC 5.2 ms in situ. No LH/VNC data read. |
| Slow nACh component outside ORN→PN | omit | Nagel's 80 ms IMI-sensitive component is measured only at ORN→PN. |
| GABA_B: postsynaptic magnitude per synapse, and presence outside the AL | AL only: presynaptic on ORN→PN (divisive, onset τ ≈ 25 ms, decay ≈ 1 s); optional weak postsynaptic PN term (τ_rise ≈ 50–100 ms, τ_decay ≈ 500–1000 ms); no GABA_B on LNs | Wilson & Laurent, Olsen, Nagel, Root. No data read for other neuropils. |
| eLN→PN / PN–PN junctional conductance | g_gap/g_L = 0.01–0.03 for sister PNs and eLN–PN, applied only to these pairs | Coupling coefficients 0.003–0.034, which are underestimates (Yaksi). Huang 2010 is unread. |
| Which LNs are electrically coupled (eLN identity in MaleCNS) | use Yaksi's "eLN" definition mapped to cholinergic LN types; flag as INFERRED | The connectome has no gap junctions (verified earlier). |
| Recording temperature of all in vivo kinetics | treat all τ as ≈22 °C values | Not stated in any in vivo text read. |
| LN-specific excitatory kinetics | same fast nACh, plus stronger STD than PNs | Nagel Fig 5: excitation onto LNs is more transient and depresses more. |
| STD parameters network-wide | U ≈ 0.2–0.5, τ_D ≈ 0.5–1 s, at least for ORN→PN and AL→AL | Nagel (τ_A ≈ 1 s at ORN→PN); Huang 2018 (τ_D > 125 ms needed). |

---

## (d) Prompt for Claude

```
You are drafting (not implementing) a PRE-REGISTERED synapse-model change for FLYCNS, a Brian2 LIF model
of the MaleCNS v1.0 connectome. Read /workspace/flycns/synapse_model_lit_2026-10-18.md first; cite only
values tagged VERIFIED / VERIFIED-fig there, and label every default from section (c) as an assumption.

Current model (src/main/flycns/model.py, the local checkout only, which I did not re-check against origin): dv/dt = (v_rest + I_base - v + g + I_gap + g_shunt*(v_rest-v) - a)/tau_m;
dg/dt = -g/tau_syn, a single current-like g in volts, tau_syn 5 ms shared by E and I, no reversal potentials,
no GABA_B, gap junctions only for the documented GF/TTMn/PSI/JO-B1 list. Phase 1b ended in outcome C (no
synaptic scale both functional and stable); blind-drive reverberation sits in the AL (AL->AL 84% excitatory).

IMPORTANT: model.py, graph.py, calibration.py, stats.py etc. are in registry.MODEL_FILES and are hashed. Any
of these changes alters the model hash, so it must be a NEW GENERATION (new label, new registration, fresh
calibration), never a patch to gen5/gen6 phase A. Write the plan as a draft doc only; no code, no commits.

Draft, with hypotheses, arms, primary/secondary outcomes and stop rules fixed in advance:
1. Conductance-based E/I: I_syn = g_e(E_e - v) + g_i(E_i - v), with separate tau_e (fast nACh, ~2-5 ms)
   and tau_i (GABA_A/GluCl, ~5 ms; sweep 3-10). E_e = 0 mV. E_i = -65 mV primary, with a pre-registered
   sweep {-55,-65,-75}. Fix the weight conversion in advance, e.g. g = w/(<V> - E_syn) at the calibration V
   (Cavallari 2014), so arm differences are not just a rescaling.
2. Optional slow GABA_B (AL only): presynaptic divisive depression of ORN->PN weights driven by LN activity
   (onset ~25 ms, decay ~1 s), and optionally a weak postsynaptic PN conductance; none on LNs.
3. Optional gap junctions: I_gap += g_gap(v_j - v_i) for sister PN-PN and eLN-PN pairs only, g_gap/g_L
   0.01-0.03 (from coupling coefficients that are lower bounds).
4. Candidate control arm: short-term depression (tau_D 0.5-1 s), because Huang et al. 2018 found conductance
   synapses + more inhibition did NOT stop seizure-like runaway in a fly whole-brain LIF but STD did.
Specify the factorial (or staged) design, a priori stability criterion (e.g. self_sustained tail_hz) and
functional criteria reused unchanged from phase 1b, the multiple-comparison handling, and what result would
falsify "driving-force saturation is sufficient". Mark every parameter as measured / modelled / assumed.
```

---

### Sources read in full (saved in `/workspace/flycns/lit/`)
- Wilson & Laurent 2005 (PMC6725763)
- Olsen & Wilson 2008 (PMC2824883)
- Kazama & Wilson 2008 (PMC2429849)
- Kazama & Wilson 2009 (PMC2751859)
- Gouwens & Wilson 2009 (PMC2709801)
- Root et al. 2008 (PMC2539065)
- Yaksi & Wilson 2010 (PMC2954501)
- Liu & Wilson 2013 (PMC3690841)
- Nagel, Hong & Wilson 2015 (PMC4289142)
- Su & O'Dowd 2003 (PMC6740836)
- Lee, Su & O'Dowd 2003 (PMC6740792)
- Gu & O'Dowd 2006 (PMC6674319)
- Shiu et al. 2024 (PMC11446845)
- Pospisil et al. 2024 (PMC11446844)
- Lappalainen et al. 2024 (PMC11525180)
- Kakaria & de Bivort 2017 (PMC5306390)
- Huang et al. 2018 (PMC6335393)
- Cavallari et al. 2014 (PMC3943173)
- Kuhn et al. 2004 (PMC6729484)
- Vogels & Abbott 2005 (PMC6725859)
- Billeh et al. 2019 bioRxiv (`billeh2019_biorxiv.pdf`)
- Brunel 2000 (`brunel2000.pdf`)

### Partial or unread
- Rohrbough & Broadie 2002: search-index excerpt only (`rohrbough2002_excerpt.txt`).
- Huang et al. 2010 Neuron: abstract only, CAN'T VERIFY.
- Wilson & Laurent 2005 supplementary figures: not read.
- Olsen & Wilson 2008 Supp Fig 5: not read; known only from the main-text mention.
