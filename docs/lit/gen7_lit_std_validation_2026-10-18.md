<!-- Literature review by Grok (read-only), 18 October 2026, committed as received. Paths under /workspace/ are
Grok's own workspace, not this repository. Spot-checked against PubMed full texts on 18 October: Kazama &
Wilson 2009 (alpha 0.72, tau 2.4 s) and Nagel, Hong & Wilson 2015 (f 0.77 / tau 1006 ms; f 0.91 / tau 629 ms;
the slow component fitted to odor-response Vm) all match. -->

# FLYCNS Gen 7 literature: AL short-term depression, reversal potentials, validation targets

Date: 18 Oct 2026 (America/Los_Angeles). Research only: no code, no repo edits, no messages sent.
This file makes no recommendations about parameter values. It reports only what was measured or fitted.

**Tags**
- **VERIFIED**: I read the value or quote in the saved full text, at the location given.
- **VERIFIED-fig**: I read the value off a figure panel by eye (≈, roughly ±10–20 %). The text does not state the number.
- **UNVERIFIED**: I did not check the value against the full text. This covers search-index excerpts, supplements I did not obtain, and papers I could not open.

**Measured / fitted**
- **MEASURED**: a direct experimental measurement.
- **FITTED**: a parameter of a model fitted to data.
- **MODEL**: a simulation output, not data.

**Sources.** Full texts are in `/workspace/flycns/lit/` (`PMCxxxx.txt` plus `.html`/`.xml`; figure images are `*_fig*.jpg/png`). Files new in this pass:
- full texts: PMC4829653 (Nagel & Wilson 2016), PMC2866644 (Olsen 2010), PMC3590906 (Gaudry 2013), PMC5495107 (Hong & Wilson 2015), PMC2838615 (Bhandawat 2007), PMC5488793 (Jeanne & Wilson 2015), PMC2650400 (Gordon & Scott 2009), PMC7316511 (McKellar 2020), PMC3341050 (Manzo 2012), PMC3727048 (Flood 2013 Nature), PMC3789788 (Flood 2013 screen), PMC5315463 (Schwarz 2017), PMC8445619 (Sterne 2021), PMC9292995 (Shiu 2022), PMC3466644 (Yoshihara 2012 JoVE), PMC5967399 (Mann 2017), PMC6395010 (Aimon 2019), PMC10495430 (Schaffer 2023)
- figure images: `kazama2008_fig8.jpg`, `jeanne2015_fig1.jpg`, `gouwens2009_fig7.jpg`, `bhandawat2007_fig1.jpg`, `bhandawat2007_fig3.jpg`, `olsen2010_fig1.jpg`, `gordon2009_fig6.jpg`, `shiu2024_fig1.png`
- Rohrbough & Broadie excerpt: `rohrbough2002_excerpt2_2026-10-18.txt`

**Recording temperature.** None of the in vivo Wilson-lab texts I read gives a recording temperature. They give a rearing temperature of 25 °C. Kazama 2008 and Nagel 2015/2016 were searched for "°C/temperature/room", and the only hits were rearing temperature and drug storage. Temperature is therefore "not stated" in every in vivo row below.

**Saline.** Kazama 2008, Nagel 2015 and Nagel 2016 all use external saline with "1.5 CaCl2, and 4 MgCl2" (mM). VERIFIED in each Methods.

---

## Part 1. Short-term depression in the antennal lobe, and reversal potentials

| synapse | quantity | value (units) | species/sex/age | preparation | measured or fitted | source + figure/table/section | tag |
|---|---|---|---|---|---|---|---|
| ORN→PN | release probability p (multiple-probability fluctuation analysis) | 0.79 ± 0.02 (also N = 51.4 ± 7.8 sites, q = 1.05 ± 0.11 pA), glomeruli DL5 + DM4 | D. melanogaster, female, 2–7 d | in vivo whole-cell V-clamp (−65 mV), antennae removed, antennal-nerve minimal stimulation; 1.5 mM Ca2+ / 4 mM Mg2+; temperature not stated | FITTED (parabolic variance–mean fit to measured uEPSCs) | Kazama & Wilson 2008 Neuron, Fig 5C legend + Results (PMC2429849) | VERIFIED |
| ORN→PN | p (single-probability method, all 4 glomeruli) | "uniform across glomeruli"; no difference by ANOVA, p > 0.36, n = 7, 4, 6, 5 (DM6, VM2, DL5, DM4) | as above | as above | FITTED | Kazama & Wilson 2008 Fig 7C | VERIFIED (the text gives no per-glomerulus p values) |
| ORN→PN | depression during trains (after a 7 Hz, 4 s conditioning train) | uEPSC as % of first in-train EPSC at ≈500 ms: 15 Hz ≈65 %, 20 Hz ≈35 %, 50 Hz ≈0–5 % (reached by ≈100 ms); n = 6 cells, VM2 | female, 2–7 d | in vivo, nerve stimulation | MEASURED | Kazama & Wilson 2008 Fig 8F (`kazama2008_fig8.jpg`) | VERIFIED-fig |
| ORN→PN | presynaptic locus | 1/CV² falls with depression at 7 Hz, "Pearson's r = 0.79, p < 10−4" | as above | as above | MEASURED | Kazama & Wilson 2008 Fig 8G | VERIFIED |
| ORN→PN | recovery τ and paired-pulse ratio | **not reported** in Kazama & Wilson 2008. There are no hits for "paired" or "recover" in the full text. | n/a | n/a | n/a | Kazama & Wilson 2008 full text | VERIFIED (absent) |
| ORN→PN | depression factor α and recovery τ (A → αA per spike, then τ dA/dt = 1 − A) | α = 0.72, τ = 2.4 s; DM4; constant-frequency stimulation "mimicking the mean spontaneous firing rate of DM4 ORNs" | sex/age in Supplementary Methods (not read) | in vivo, antennal-nerve suction electrode | FITTED (least squares on measured EPSCs) | Kazama & Wilson 2009 Nat Neurosci, Methods "Model of synaptic transmission" (PMC2751859); data in Supp Fig 2 (not read) | VERIFIED (parameters); UNVERIFIED (sex, saline, train frequency) |
| ORN→PN | qualitative paired-interval depression | "long inter-pulse interval (30 s), EPSCs are consistently large … A short inter-pulse interval (0.25 s) produces short-term depression" | as above | in vivo | MEASURED (example) | Kazama & Wilson 2009 Fig 5b legend | VERIFIED |
| ORN→PN (total EPSC) | f and τ (A → f·A per spike; recovery τ) | f = 0.78, τ = 893 ms; 10 Hz train, n = 19 PNs / 19 flies, DM6 or VM2 | female, 1–3 d | in vivo whole-cell V-clamp, antennae removed, nerve stimulation; 1.5 Ca / 4 Mg | FITTED | Nagel, Hong & Wilson 2015 Nat Neurosci, Fig 1c legend; Methods Eq 1 (PMC4289142) | VERIFIED |
| ORN→PN fast (IMI-resistant, curare-sensitive) component | f, τ | f = 0.77, τ = 1006 ms (10 Hz) | female, 1–3 d | as above, in imidacloprid | FITTED | Nagel 2015 Results ("For the IMI-resistant component…") | VERIFIED |
| ORN→PN slow (curare-resistant) component | f, τ | f = 0.91, τ = 629 ms (10 Hz) | female, 1–3 d | as above, in curare | FITTED | Nagel 2015 Results | VERIFIED |
| ORN→PN fast component (rate-based model) | r, τ_A, k, τ_g | r = 0.23 spike⁻¹, τ_A = 1006 ms, k = 20 nS/spike, τ_g = 9.3 ms | n/a | model | FITTED (r and τ_A taken from the IMI fit; τ_g from the EPSC shape in IMI) | Nagel 2015 Methods Eq 3–4 | VERIFIED |
| ORN→PN slow component (rate-based model) | r, τ_A, k, τ_g | r = 0.0073 spike⁻¹, τ_A = 33247 ms, k = 1.8 nS/spike, τ_g = 80 ms | n/a | model | FITTED **to PN odor-response membrane potential** (55 % density stimulus), not to evoked EPSCs | Nagel 2015 Methods | VERIFIED |
| ORN→PN | block by both nicotinic drugs | curare + IMI "blocked 70±12% of the evoked current during the 50 Hz stimulus (mean±s.e.m, n=8 PNs from 8 flies)" | female | in vivo | MEASURED | Nagel 2015 Fig 2f legend | VERIFIED |
| ORN→LN (not PN→LN) | f, τ | f = 0.75, τ = 1566 ms; 10 Hz train; n = 9 LNs (PN comparison n = 19) | female, 1–3 d | in vivo whole-cell, antennal-nerve stimulation; 1.5 Ca / 4 Mg | FITTED | Nagel & Wilson 2016 J Neurosci, Fig 6B legend (PMC4829653) | VERIFIED |
| ORN→LN vs ORN→PN | late/peak ratio of odor-evoked synaptic current (last 200 ms of a 2 s pulse ÷ peak) | "significantly higher in PNs than in LNs (p=1.7e-3, t-test)"; LN n = 22, PN n = 9 | female | in vivo V-clamp, −60 mV | MEASURED | Nagel 2015 Fig 5d–f legend | VERIFIED (ratio values not read off the figure) |
| PN→LN | depression τ, f, PPR | **no measurement found** | n/a | n/a | n/a | Nagel 2015/2016, Kazama 2008/2009, Yaksi 2010, Wilson & Laurent 2005, Olsen & Wilson 2008, Hong & Wilson 2015 searched for "depress / paired / recover / facilitat" | VERIFIED (absent in the texts read) |
| LN→PN (and LN→ORN) | depression τ, f, PPR | **no measurement found**. Closest data: (i) inhibition onset "fit with an alpha function with a time constant of about 25 ms" (Nagel 2015 Fig 6); (ii) ChR2-driven LN firing decays while outward current in ChR− LNs "grow[s] slowly" (LN→LN, Nagel 2016 Fig 6D–F); (iii) GABA_A and GABA_B inhibition of ORN→PN EPSCs "associated with an increase in the paired-pulse ratio" (Olsen & Wilson 2008, Supp Fig 7, not read) | female | in vivo | MEASURED (qualitative) | as listed | VERIFIED for (i) and (ii); **UNVERIFIED** for the (iii) numbers |
| eLN→iLN | synapse type | "eLN-to-iLN synapses are largely cholinergic"; Cd2+ reduces depolarizing transmission (n = 6 pairs, p < 0.005); shakB2 abolishes both directions. No dynamics reported. | female, 1–3 d | in vivo dual whole-cell, antennae removed | MEASURED | Yaksi & Wilson 2010 Neuron, Fig 5 + Results (PMC2954501) | VERIFIED (no STD data) |
| ORN→PN, ipsi vs contra | release asymmetry | "each ORN spike releases ~40% more neurotransmitter from the axon branch ipsilateral to the soma"; sEPSCs larger ipsilaterally (n = 15 DM6 pairs, p < 0.05); conduction delay 0.80 ± 0.51 ms. No STD data. | sex not found in main text | in vivo dual whole-cell, one antenna removed | MEASURED | Gaudry et al. 2013 Nature, abstract + Fig 3 (PMC3590906) | VERIFIED |
| ORN→PN | Hong & Wilson 2015 | no depression-model fit found. They state that "vesicular release saturates at high presynaptic firing rates (Kazama and Wilson, 2008)" | female, 2–3 d | in vivo | n/a | Hong & Wilson 2015 Neuron, Discussion (PMC5495107) | VERIFIED (absent) |
| ORN→PN intraglomerular I/O (includes STD and refractoriness) | PN = R_max·ORN^1.5/(ORN^1.5 + σ^1.5) | R_max = 165 spikes/s, σ = 12 spikes/s (the defaults used for all glomeruli in simulations) | sex in Supp Methods (not read) | in vivo | FITTED | Olsen, Bhandawat & Wilson 2010 Neuron, Eq 1 + Methods text (PMC2866644) | VERIFIED (values); UNVERIFIED (sex) |
| **Reversal potentials** | | | | | | | |
| nACh (cholinergic sPSCs) | E_rev | +8.9 ± 1.7 mV (n = 9) | pupal brain neurons | culture, room temperature | MEASURED | Su & O'Dowd 2003 J Neurosci, Results (PMC6740836) | VERIFIED (re-checked) |
| nACh | E_rev | "0 mV, the reversal potential for the cholinergic currents" | embryonic neurons | culture, RT | MEASURED (stated) | Lee, Su & O'Dowd 2003, Results (PMC6740792) | VERIFIED (re-checked) |
| GABA (Rdl) | E_rev | −37 ± 3 mV (n = 4) | pupal neurons | culture, RT | MEASURED | Su & O'Dowd 2003 | VERIFIED (re-checked) |
| GABA (Rdl) | E_rev | −41.5 ± 2.1 mV (n = 5); calculated E_Cl −45 mV; −1.1 ± 2.6 mV in symmetrical Cl | embryonic neurons | culture, RT | MEASURED | Lee, Su & O'Dowd 2003 | VERIFIED (re-checked) |
| GABA | E_rev | −56 ± 3 mV in 6/9 neurons; 3/9 depolarized ≤16 mV | larval VNC (mostly motor) neurons | larval CNS whole-cell ("motor neurons in vivo", Fig 3 title); 2 mM Ca2+ saline | MEASURED | Rohrbough & Broadie 2002 J Neurophysiol, Results + Fig 3B2 | **UNVERIFIED** (search-index excerpt only; the publisher page returns Cloudflare 403 to WebFetch and curl) |
| Glutamate (GluCl) | E_rev | "−55 ± 2 mV; n = 7" ("clearly reversed at −50 to −60 mV"); PTX-blocked (n = 2); responses "especially prolonged (2–5 s)" | larval VNC | as above | MEASURED | Rohrbough & Broadie 2002, Results + Fig 3C2 | **UNVERIFIED** (excerpt only) |
| GluCl, adult AL | E_rev | not reported (no hits for "revers" in Liu & Wilson 2013) | adult | in vivo | n/a | Liu & Wilson 2013 PLoS Biol (PMC3690841) | VERIFIED (absent) |
| GABA, adult PN/LN in vivo | E_rev | not measured physiologically. The pipette "yielded a GABA reversal potential near E Cl" (Supp Fig 1, not read) | female, 3–10 d | in vivo whole-cell (Cl set by pipette) | n/a | Wilson & Laurent 2005 J Neurosci, Methods (PMC6725763) | VERIFIED (quote); UNVERIFIED (Supp Fig 1 value) |

### Quote notes, Part 1
- Kazama & Wilson 2008: "Estimated release probability was consistently high, with a mean value of 0.79. The number of release sites was also high, with a mean value of 51." On depression: "All stimulus frequencies produced additional substantial synaptic depression (Figure 8F). As expected, depression was particularly rapid at high stimulus frequencies." Protocol: "we began every trial with a long train of pulses at this frequency [7 spikes/s] … which itself produced some synaptic depression." Fig 8 values are percentages of the first EPSC **after** this conditioning, so they are not depression from rest. Baseline uEPSC was measured at 0.033 Hz: "29.0 ± 2.6 pA (n = 45)", uEPSP "6.19 ± 0.45 mV (n = 23)".
- Kazama & Wilson 2009: "After the arrival of each action potential, A(t) decreased to a fraction α of the previous value (αA(t)) and recovered exponentially with a time constant τ … The parameters α = 0.72 and τ = 2.4 s were obtained from a least-squares regression using these data."
- Nagel 2015, Eq 1: "if s(t)=1, A(t+Δt) = f·A(t); if s(t)=0, A(t+Δt) = A(t) + (1−A(t))Δt/τ". The parameters "were fit to the mean normalized amplitude of EPSCs recorded in PNs in response to electrical stimulation of the antennal nerve at 10 Hz". Note that f is the **retained** fraction, so the per-spike decrement is 1 − f ≈ 0.22. Eq 3 uses r = 1 − f.
- Nagel & Wilson 2016: "Values of f and τ are 0.75 and 1566 ms for LNs; 0.78 and 893 ms for PNs." This is **ORN→LN**, not PN→LN.
- Correction to the prior report (`synapse_model_lit_2026-10-18.md`): its slow-component values (r 0.0073, τ_A 33,247 ms, 80 ms) were fitted to odor-response V_m, not to evoked EPSCs. The paper says: "The parameters of the slow component were fit … to minimize the difference between the predicted PN membrane potential in response to 55% density stimulus and the actual disinhibited response". The other values carried over from that report were re-checked and match.
- Rohrbough & Broadie 2002: I could not reach the full text (journals.physiology.org returns 403 for both the /full/ and /pdf/ URLs). The new excerpt adds the glutamate value "−55 ± 2 mV; n = 7". Pipette [Cl−], junction-potential correction, temperature and larval stage are not known.

---

## Part 2. Validation targets

Rank: **direct** = spikes/s from the same cell type; **indirect** = calcium signal, or a different cell; **behavioral proxy** = PER probability or direction; **none** = model output, or no data.

| target | readout it maps to | value (units) | conditions (stimulus, sex, prep, n) | measured as | source + figure | tag | rank |
|---|---|---|---|---|---|---|---|
| **(a) AL PN** | | | | | | | |
| PN spontaneous rate (DA1) | AL PN rate | mean ≈8.5 spikes/s (bar); individual cells ≈0–29 Hz; n = 44 PNs (cell-attached + whole-cell) | no stimulus; in vivo; sex in Supp (not read) | firing rate | Jeanne & Wilson 2015 Neuron, Fig 1H (`jeanne2015_fig1.jpg`) (PMC5488793) | VERIFIED-fig (value); VERIFIED that "Mean rates are higher in PNs than in ORNs" | direct |
| PN spontaneous rate (various glomeruli) | AL PN rate | "typically 1–5 spikes/sec" | no odor; in vivo whole-cell pairs; sex not read | firing rate | Kazama & Wilson 2009, Results "Modulation of correlated activity" | VERIFIED (quote) | direct |
| PN spontaneous rate, cell-attached vs whole-cell | AL PN rate | cell-attached ≈0–20 spikes/s (most ≲10); rates "generally increased immediately after rupturing the membrane patch"; n = 27 | in vivo, antennae intact | firing rate | Gouwens & Wilson 2009 J Neurosci, Fig 7B (`gouwens2009_fig7.jpg`) | VERIFIED-fig (range); VERIFIED (quote) | direct |
| PN spontaneous and evoked rate, pooled over 7 glomeruli × 18 odors | AL PN rate | baseline ≈0.25 spikes per 50 ms bin (≈5 spikes/s); peak ≈4.4 spikes/bin (≈88 spikes/s), averaged over all odors | 500 ms odor; female, 2–7 d; in vivo whole-cell; n = 843 PN responses | firing rate | Bhandawat et al. 2007 Nat Neurosci, Fig 1b (`bhandawat2007_fig1.jpg`) (PMC2838615) | VERIFIED-fig (conversion to Hz is mine: /0.05 s) | direct |
| PN odor responses per glomerulus (DL1, DM1, DM2, DM3, DM4, VA2, VM2) | AL PN rate | baseline-subtracted peak 100 ms rate per odor, ≈0–260 spikes/s; strongest ≈200–260 (e.g. DM3 isoamyl acetate / 2-octanone ≈250; VA2 2,3-butanedione ≈225); n per bar in Supp Table 2 (not read) | 18 odors, 500 ms; female; in vivo | firing rate (peak − baseline) | Bhandawat 2007 Fig 3a (`bhandawat2007_fig3.jpg`) | VERIFIED-fig; n is UNVERIFIED | direct |
| PN response vs ORN response (DM4, DL5, VM7, DM1) | AL PN rate | saturating I/O: PN plateau ≈150–170 spikes/s; fitted R_max 165, σ 12 spikes/s; 6–12 recordings per point | private odors at several concentrations; in vivo; sex not read | firing rate | Olsen, Bhandawat & Wilson 2010, Fig 1B (`olsen2010_fig1.jpg`) + Eq 1 | VERIFIED (R_max, σ); VERIFIED-fig (plateaus) | direct |
| PN evoked, near threshold (DA1, optogenetic ORN drive) | AL PN rate | peak ≈85 spikes/s (100 ms flash, ≈1.7 ORN spikes per trial); PN rate ≈3× ORN rate; n = 44 PNs | ChR2 in DA1 ORNs; in vivo | firing rate | Jeanne & Wilson 2015 Fig 1C,E | VERIFIED-fig; VERIFIED ("PN spike rates were consistently about three-fold larger than ORN spike rates") | direct |
| PN response with GABA_B / GABA_A blocked | AL PN rate | early (0–0.5 s) ≈34→47 Hz with CGP; ≈48→73 Hz with PTX; late (1.5–2.5 s) ≈6.6→12.6 Hz with CGP | odor; female, 3–10 d; in vivo | firing rate | Wilson & Laurent 2005 Fig 3 | VERIFIED-fig (carried from the prior report, figure not re-read) | direct |
| PN ipsi vs contra rate asymmetry | AL PN rate (laterality) | ipsilateral ≈50 % higher than contralateral (DM6); first spike 2.47 ± 0.70 ms earlier (DM6, n = 16), 1.01 ± 0.41 ms (DM1, n = 6) | unilateral-antenna odor; in vivo dual recording | firing rate / latency | Gaudry 2013, Results + Fig 2c–g | VERIFIED | direct |
| PN responses, Wilson, Turner & Laurent 2004 | AL PN rate | not read (Science; no PMC copy, no repository PDF found) | in vivo whole-cell | firing rate | Science 303:366 | UNVERIFIED | direct (if obtained) |
| "Seki et al. 2010" | (LN, not PN) | Seki, Rybak, Wicher, Sachse & Hansson 2010 J Neurophysiol is about **LNs** (Hansson lab, not Jefferis). The abstract reports class-specific firing (one bursting class, others tonic); no rates in the abstract | in vivo whole-cell | n/a | PubMed abstract, PMID 20505124 | UNVERIFIED (full text not read) | indirect |
| Population (two-photon, all glomeruli) PN data | AL PN rate | not obtained this pass (e.g. Badel et al. 2016 not read) | n/a | calcium | n/a | UNVERIFIED | indirect |
| LN spontaneous rate | AL (LN), whole-CNS anchor | 4.6 ± 2.8 spikes/s (mean ± s.d., n = 45 LNs / 38 flies) | no odor; female; in vivo loose-patch | firing rate | Nagel 2015 Results ("Odors elicit transient activity…") | VERIFIED | indirect (different cell) |
| LN spontaneous rate | as above | 2.3 ± 0.2 spikes/s (n = 12), cell-attached | in vivo; female | firing rate | Wilson & Laurent 2005 Results | VERIFIED | indirect |
| ORN / LHN spontaneous rate (DA1 circuit) | whole-CNS anchor | ORN ≈1.5 Hz, LHN ≈3 Hz (bars); n = 58 ORNs, 25 LHNs | in vivo | firing rate | Jeanne & Wilson 2015 Fig 1H | VERIFIED-fig | indirect |
| **(b) MN9 / proboscis MNs** | | | | | | | |
| MN9 (E49) response to sugar | MN9 Hz | ≈48 % ΔF/F (100 mM sucrose), ≈49 % (200 mM maltose); water ≈2 %; sucrose + 50 mM caffeine or + 1 mM denatonium = not different from water; 6–8 flies per condition. Text: "approximately 50%" | proboscis stimulation; live prep, G-CaMP (confocal), one cell body per fly; sex not stated for imaging | **calcium** | Gordon & Scott 2009 Neuron, Fig 6C + Results (PMC2650400; `gordon2009_fig6.jpg`) | VERIFIED (≈50 % quote); VERIFIED-fig (bars) | indirect (same cell, calcium) |
| MN9 sugar concentration dependence | MN9 Hz | 1 M sucrose ≈90 % vs 100 mM ≈53 % ΔF/F, "almost twice"; n = 10 flies each, p < 0.01 | as above | calcium | Gordon & Scott 2009 Fig 6D | VERIFIED (quote) / VERIFIED-fig | indirect |
| MN9 calcium vs rostrum extension | MN9 Hz / PER | "perfect correlation between rostrum movement and motor neuron activity"; activity reliably detectable only above 10 % ΔF/F (movement artefact); trials with movement ≈28–68 % ΔF/F at 0 mM caffeine; n = 10 trials per condition | 100 mM sucrose + 0–100 mM caffeine | calcium + behavior | Gordon & Scott 2009 Fig 6E + Methods | VERIFIED / VERIFIED-fig | indirect |
| MN9 time course | MN9 latency | no latency value. Example trace: rise to ≈60 % within a few s of stimulus onset, then decay (G-CaMP1). JoVE: "a sharp increase in fluorescence followed by a restoration phase of several seconds"; imaged at 4 Hz with GCaMP3 | proboscis 100 mM sucrose | calcium | Gordon & Scott 2009 Fig 6B; Yoshihara 2012 JoVE Fig 9 (PMC3466644) | VERIFIED (qualitative); no number | indirect |
| MN9 laterality (anatomy and silencing) | MN9 Hz (left/right) | MN9 is a bilateral pair; unilateral TNT silencing gave "sidedness … extension of the proboscis downward and to one side" in 57 flies; bilateral silencing gave complete block (11 flies). Both somata respond in Fig 6A (by eye). MN9 innervates muscle 9 ipsilaterally | proboscis sucrose; behavior + anatomy | behavior / anatomy | Gordon & Scott 2009 Fig 4 + Results; Schwarz et al. 2017 eLife, Discussion ("MN9 … ipsilateral innervation of muscle 9") | VERIFIED | behavioral proxy |
| PER direction with unilateral input | MN9 laterality | "presentation of food to gustatory receptors on one side of the body leads to proboscis extension on that side"; single Fdg activation → PE toward the GFP+ Fdg side; unilateral Fdg ablation → PE away from the ablated side | starved flies; behavior | behavior | Flood et al. 2013 Nature, Results (PMC3727048) | VERIFIED | behavioral proxy |
| Shiu 2024 MN9 "validation" | MN9 Hz | **No measured MN9 rate.** Model predictions only (Fig 1c): contralateral > ipsilateral MN9; ≈0 Hz up to 40 Hz GRN input; at 100 Hz GRN ≈63 (contra) vs ≈46 (ipsi) Hz; at 180 Hz ≈91 vs ≈62 Hz. Compared against: behavior (direction of PER, refs Flood 2013 and Yetman & Pollack 1987), cell-type sufficiency/necessity from Shiu 2022, and "Across 164 predictions … 91% were consistent with our empirical results" (84 % excluding the optogenetic split-GAL4 set) | in silico | MODEL | Shiu et al. 2024 Nature, Fig 1c (`shiu2024_fig1.png`) + Results + Discussion (PMC11446845) | VERIFIED (quotes); VERIFIED-fig (predicted Hz) | none (model) |
| Shiu 2024 caveat | — | "absolute firing rate predictions are unlikely to be accurate"; "we assume that increased MN9 firing rates correspond with increased rostrum lifting probability" | — | — | Shiu 2024 Results | VERIFIED | — |
| MN9 activation, fed vs starved | PER | MN9 activation "elicited the same proboscis extension rate in food-deprived and fed flies" (n = 50) | CsChrimson; behavior | PER probability | Shiu et al. 2022 eLife, Fig 4C (PMC9292995) | VERIFIED | behavioral proxy |
| McKellar 2020 MN9 | MN9 | CsChrimson activation of mn9 "elicited proboscis extension"; TNT silencing "prevented the movement of both the rostrum and haustellum during natural feeding". No imaging or ephys of mn9 | behavior | joint angles | McKellar et al. 2020 eLife, Results (PMC7316511) | VERIFIED | behavioral proxy |
| PER motor sequence | MN9 timing | sequence: rostrum (MN9) → haustellum → labella extension → spreading; 4/93 deviations (n = 14 flies). Times are relative to rostrum lift (set to 0), so there is no stimulus-to-MN9 latency | leg sucrose; starved; behavior | behavior | Schwarz et al. 2017 eLife, Fig 1G + Results (PMC5315463) | VERIFIED | behavioral proxy |
| MN11/MN12 (pump MNs) | MN9 (different MN) | peak %ΔF/F larger and longer for sucrose (n = 10–13 flies per bar); values only in the figure, not read | proboscis stimulation; 24 h starved | calcium | Manzo et al. 2012 PNAS, Fig 5 (PMC3341050) | VERIFIED (qualitative); values UNVERIFIED | indirect |
| Sterne 2021; Pospisil 2024 | MN9 | no MN9 measurements (Sterne: "MN9" 0 hits; Pospisil: "MN9/proboscis/sugar" 0 hits) | — | — | PMC8445619; PMC11446844 | VERIFIED (absent) | none |
| MN9 spike-rate electrophysiology | MN9 Hz | **none found** (WebSearch 18 Oct 2026) | — | — | — | — | — |
| **(c) Whole brain / CNS** | | | | | | | |
| Whole-brain spontaneous activity | whole-CNS rate | no spike rates; pan-neuronal GCaMP6m ΔF/F in 61 atlas ROIs, imaged "in the absence of sensory stimuli" | female, 5 d, nSyb-Gal4; head-fixed, dissected; two-photon | calcium | Mann, Gallen & Clandinin 2017 Curr Biol, Methods + Fig 2 (PMC5967399) | VERIFIED | indirect |
| Near-whole-brain activity vs behavior | whole-CNS rate | no spike rates; light-field imaging up to 100 Hz (GCaMP6) / 200 Hz (ArcLight); activity maps for walking/grooming/odor/light | nSyb/Cha/GMR57C10 drivers; sex not found in text | calcium / voltage | Aimon et al. 2019 PLoS Biol, Results + Fig 2 (PMC6395010) | VERIFIED | indirect |
| Dorsal-brain cellular activity vs behavior | whole-CNS rate | no spike rates; "41% of cells had small time constants (τ < 4 seconds) … 31% of all cells have τ greater than 20 seconds"; front/back grooming: 3.0 % / 2.1 % of cells with τ < 4 s and weight > 0.02; 16 flies | nls-GCaMP6s, nSyb; SCAPE; dorsal third of central brain; KCs excluded | calcium | Schaffer et al. 2023 Nat Commun, Results + Fig 2–3 (PMC10495430) | VERIFIED | indirect |
| Fly whole-brain spike-rate estimate | whole-CNS rate | **none found** | — | — | WebSearch 18 Oct 2026 | — | none |
| Shiu model baseline | whole-CNS rate | "assume a basal firing rate of 0 Hz" | model | MODEL | Shiu 2024 Methods (carried from the prior report) | VERIFIED (earlier) | none |

### Ranking of Part 2 targets by how directly they map onto the readouts

1. **AL PN rate: direct.** The best-specified values are:
   - spontaneous: Jeanne & Wilson 2015 Fig 1H (DA1, n = 44); Kazama & Wilson 2009 "1–5 spikes/sec"; Bhandawat 2007 Fig 1b (≈5 spikes/s pooled); Gouwens 2009 Fig 7B. These disagree by a factor of about 2. Whole-cell recording raises the rate (Gouwens).
   - per-glomerulus odor-evoked: Bhandawat 2007 Fig 3a.
   - I/O saturation: Olsen 2010 (R_max 165 spikes/s, fitted).
2. **MN9 Hz: indirect at best.** The only measured MN9 signal is calcium (Gordon & Scott 2009, ≈50 % ΔF/F at 100 mM sucrose; ≈2× at 1 M). No firing rate or latency is reported. Laterality data are behavioral (Gordon & Scott unilateral silencing; Flood 2013 PER toward the stimulated side). Shiu 2024's MN9 Hz values are model outputs, not data.
3. **Whole-CNS rate: indirect only.** There are no fly whole-brain spike-rate measurements. The whole-brain papers give calcium signals (Mann 2017, Aimon 2019, Schaffer 2023). The only spike-rate anchors are single cell classes: PN ≈1–9 Hz, LN 2.3–4.6 Hz, ORN ≈1.5 Hz, LHN ≈3 Hz (spontaneous).

---

## UNVERIFIED items (not checked against the full text)
1. Rohrbough & Broadie 2002: all values (GABA −56 ± 3 mV; glutamate −55 ± 2 mV; resting −50 to −60 mV). These come from search-index excerpts only, and the publisher page is Cloudflare-blocked. Pipette Cl, temperature and stage are unknown.
2. Kazama & Wilson 2009: sex, saline and stimulation frequency for the α = 0.72 / τ = 2.4 s fit (Supplementary Methods and Supp Fig 2 not obtained).
3. Olsen & Wilson 2008 Supp Fig 7: paired-pulse-ratio values under GABA_A/GABA_B inhibition (only the main-text statement was read).
4. Wilson & Laurent 2005 Supp Fig 1: the GABA reversal value set by the pipette.
5. Olsen 2010 and Jeanne & Wilson 2015: sex and age (in supplements, not read).
6. Bhandawat 2007: n per glomerulus–odor bar (Supp Table 2) and spontaneous rates per glomerulus (not in the main text).
7. Wilson, Turner & Laurent 2004 Science: not read at all.
8. Seki et al. 2010: abstract only. It is an LN paper, not a PN paper.
9. Manzo 2012 MN11/MN12 ΔF/F values (figure not read).
10. Gordon & Scott 2009: sex of the imaged flies (not stated in the imaging Methods; the PER screen used females).
11. Gaudry 2013: sex (in Supplementary Methods).
12. Recording temperature for every in vivo row: not stated in any text read.
13. A "≈28 ms rostrum-lift latency" appeared in a WebSearch synthesis. It is not in Schwarz 2017, where times are relative to rostrum lift. Treat it as unsupported.
14. Population PN two-photon data (e.g. Badel et al. 2016) and Turner et al. 2008 J Neurophysiol PN/KC baseline rates: not obtained.
