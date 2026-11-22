# Published synapse-count ratios and the Shiu 0.275 mV calibration

Refreshed 21 November 2026, America/Los_Angeles, from `/workspace/flycns/gen7_density_lit_2026-11-18.md`. Key quotes were re-checked against the saved full texts in `/workspace/flycns/lit/`. This is not a from-scratch rewrite.

Read-only literature report for FLYCNS gen 7. No repo edits, no messages, no parameter recommendations.

Tags: **VERIFIED** (exact quote + location), **INFERRED**, **UNVERIFIED**.  
Ranks (blocker / should-fix / note) refer only to relevance for whether MaleCNS synapse counts need rescaling relative to Shiu et al. 2024’s FlyWire calibration. They are not implementation instructions.

**Given measurement (not verified here):** MaleCNS v1.0 has about 2.1× the synapses per cell of FlyWire v783 on matched cell types (ORN→LN 5.8×, ORN→PN 3.2×). Those figures are treated as given. No source checked below publishes a matched-cell-type per-cell ratio, or an AL / ORN-specific ratio, that is comparable to those numbers.

---

## Short summary

Shiu et al. 2024 set W_syn = 0.275 mV as a free parameter on FlyWire public materialization **v.630**, chosen so that 100 Hz sugar-GRN drive gave roughly 80% of maximal MN9 firing (VERIFIED: Methods, plus repo `model.py` lines 36–37 and 183 at commit `2a83ad6`, unchanged at HEAD `91bdd1e`). Berg et al. 2026 themselves scale male isomorphic type–type edge weights by 0.79 to match FAFB/FlyWire because “there are generally more synapses in the male CNS,” “mostly for technical reasons” (VERIFIED: *Cell* Results and STAR Methods). Scheffer 2025 (preprint, still v1) estimates human-visible counts in overlapping compartments of MaleCNS / FAFB-Buhmann = 1.26 and MaleCNS / FAFB2-Princeton = 1.45 (text: 1.49), attributing the gap mainly to FIB-SEM versus SS-TEM, after correcting for detector precision/recall and arguing that size and sex do not explain it (VERIFIED). Dorkenwald 2024 states that Buhmann detection, the set Shiu’s v.630 graph used (INFERRED), is weaker on sensory neurons (VERIFIED). None of these published quantities is a matched-cell-type per-cell or ORN→LN / ORN→PN ratio like the given 2.1× / 5.8× / 3.2×. The *Cell* numerals 2.1, 5.8 and 3.2 are other percentages, not density ratios (VERIFIED).

---

## Changes since 18 November 2026

1. **Key quotes re-verified** in the saved texts (Shiu `PMC11446845.txt`; Berg *Cell* `berg2026_cell.txt`; Scheffer 2025 `synapse_detection_efficiency_2025_biorxiv.txt`; Dorkenwald `PMC11446842.xml`; Schlegel `PMC11446831.xml`; Yu, Buhmann, BANC bioRxiv, Scheffer 2020). Locations below match those files. Hyphenation in the *Cell* PDF means some phrases are split across two columns (for example “precision/ recall of 0.82/0.81” at lines 143–144); the wording is unchanged.

2. **No new Scheffer, Yu, Schlegel, or Berg preprint/version** was found in a 21 Nov 2026 search. Scheffer 2025 is still the 19 Oct 2025 bioRxiv posting (10.1101/2025.10.16.682869). Yu 2025 is still the 17 July 2025 bioRxiv posting. Berg *Cell* remains 10.1016/j.cell.2026.08.015 (published 3 Sep 2026).

3. **Figure S7D / S7E images are still not in hand.** cell.com and the Cell supplement URLs again returned Cloudflare 403. EuropePMC lists the *Cell* paper as “Subscription required,” with no PMCID and no open full-text XML. The official analysis repo `flyconnectome/2025malecns` has source data for synapse precision/recall and capture, and the male–female edge table `mcns_fw_edge_comp.feather`, but not the S7 figure images. The 0.79 factor remains **VERIFIED** from STAR Methods text, **UNVERIFIED** as a re-read of the figure itself.

4. **BANC *Nature* 2026 is now quoted** (Bates et al., 8 June 2026, PMC13518251). This paper existed before 18 Nov 2026; the 18 Nov report had only the 31 July 2025 bioRxiv. The journal evaluation numbers differ from the preprint: F-score = 0.83, precision = 0.87, recall = 0.78 on 16 dense cutouts, versus bioRxiv F-score .79, precision .68, recall .95. Completeness is stated as 74% pre / 23% post / 18% both sides, and compared with FAFB 41.9%, hemibrain 35.3%, MANC 44.4%, and maleCNS 40.1% (close to Scheffer 2025 Table 6). Kenyon-cell outgoing links are given as 36.6 in BANC versus “around 200” in FAFB (cleft score threshold >50); the bioRxiv had 139 versus 213. Scheffer 2025 Table 3 still lists the bioRxiv-era BANC pair (recall 0.95, precision 0.68).

5. **Shiu repo evidence now includes file, line, and commit** (the 18 Nov report had the files but not SHA or line numbers). `w_syn` is `model.py` lines 36–37 and 183. Last change to `model.py`: commit `2a83ad611cd9768f8c9723fc613ed27761a5feb5` (9 May 2023, 11:18 AM PDT). Unchanged at default-branch HEAD `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` (14 Sep 2024, 6:47 AM PDT). The “paper used” v630 statement is `Readme.md` lines 54–55, added in `038cf2f3258cc7f91c9dbf28e40464a1669e22f9` and last edited in that same HEAD commit.

6. **Official MaleCNS per-ROI detector and capture tables** were fetched from `flyconnectome/2025malecns` (commit `a2156b0afd74134f05fff8181878cd927b06121c`, 13 May 2026, 11:12 AM PDT; README says the precision/recall *content* did not change for v1.0). These give AL-specific precision/recall and proofreading-capture fractions. They are MaleCNS-only accuracy and completeness, **not** MaleCNS-versus-FlyWire synapse-count ratios, and they do not fill the gap for a published 2.1× / 5.8× / 3.2×-style number.

7. A non-paper web page found in the fresh search (Florian Kämpf, “Fly odour ORN figure”) reports 517 versus 157 output synapses per cell for 53 shared ORN types in MaleCNS v1.0 versus FlyWire 783. That is **not** treated as a published source here.

---

## Ranked findings

### BLOCKER 1 — Shiu’s 0.275 mV is a free parameter fit on FlyWire v.630, not a dataset-independent mV per synapse

**VERIFIED.** Shiu et al. 2024, *Nature*, Methods, “Computational model” (`/workspace/flycns/lit/PMC11446845.txt`, line 70):

> “W syn = 0.275 mV (free parameter; synaptic weight, that is, how much each synapse influences downstream membrane potential)”

Same section (line 73):

> “All parameters are taken from previous *Drosophila* modelling or electrophysiology efforts 18, 19, 61, 62, from the synaptic weights from the Flywire connectome (public materialization v.630) 18, 19, or from the neurotransmitter predictions 3, 63, except for W syn, the single free parameter of the model, which corresponds to how much the downstream membrane potential changes as a result of a single excitatory or inhibitory synapse. We chose W syn such that activation of sugar GRNs at 100 Hz resulted in roughly 80% of maximal MN9 firing 64, 65.”

> “The connection weight, w_j,i, between neuron j and neuron i is the synaptic connectivity weight from the Flywire connectivity multiplied by either 1, if neuron j is excitatory or −1, if neuron j is inhibitory, multiplied by W syn.”

Later in Methods (line 79):

> “All 127,400 proofread neurons from Flywire materialization v.630 are included in the model.”

and (line 81):

> “As in ref. 67, we used a cleft score cutoff of 50”

Main text cites the FlyWire connectome as refs 1 and 21: Dorkenwald et al. 2024 and Buhmann et al. 2021 (Shiu reference list). The “18, 19” after “v.630” are Kakaria & de Bivort 2017 and Churgin et al. in that same list (modelling papers). **VERIFIED** as the cited numbers; the v.630 sentence is therefore oddly pointed at the modelling refs.

**VERIFIED** from `philshiu/Drosophila_brain_model`, default branch `main`, HEAD `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` (14 Sep 2024, 6:47 AM PDT). `model.py` last changed in `2a83ad611cd9768f8c9723fc613ed27761a5feb5` (9 May 2023, 11:18 AM PDT); lines 36–37 and 183 are the same at that commit and at HEAD:

```
# Free parameter
'w_syn' : .275 * mV,
# weight per synapse
# (note: modulated by
# exponential decay)
```

(`model.py` line 37; the comment sits on the same line in the file.)

Line 183:

```
syn.w = df_con.loc[:,
 'Excitatory x Connectivity'
 ].values * params['w_syn']
```

`Readme.md` lines 54–55 (section “Version 783”), commit `91bdd1e` / added in `038cf2f` on 14 Sep 2024:

> “The code is currently set up for the Flywire version 630, which the paper used. To use public version 783, change the config dictionary:”

then `Completeness_783.csv` and `Connectivity_783.parquet` (lines 59–60). `example.ipynb` at the same HEAD still defaults to `2023_03_23_completeness_630_final.csv` and `2023_03_23_connectivity_630_final.parquet`.

**INFERRED.** Together with the 23 March 2023 file dates, Dorkenwald’s statement that FlyWire then used Buhmann synapses (SHOULD-FIX 4), and Yu et al. 2025 posting Princeton synapses only in July 2025, the calibration graph is the Buhmann-detected, cleft-score-filtered FlyWire v.630 connectome.

**INFERRED**, not a recommendation: because W_syn was chosen so that a particular FlyWire v.630 sugar→MN9 circuit reached a firing target, the same millivolts per annotated synapse is not, in the paper, a biophysical constant that can be moved onto a graph with a different synapse density without changing that effective drive. What scale, if any, to use is outside the scope of this file.

Refs 64 and 65 are Dahanukar et al., *Neuron*, and Inagaki et al., *Cell*. **VERIFIED** as the cited sources. The “80%” figure is Shiu’s stated calibration target, not a number re-read from those two papers.

---

### BLOCKER 2 — The MaleCNS paper itself scales male edge weights down to match FAFB/FlyWire

**VERIFIED.** Berg et al. 2026, *Cell* 189: 5504–5526, Results (`berg2026_cell.txt` lines 707–720), citing Schlegel et al. 2024 as ref. 30:

> “Because synapse counts differ systematically across datasets (mostly for technical reasons30), we scaled male connection strengths down to match the female (Figure S7D; see STAR Methods).”

In the same stretch, different noise floors (`berg2026_cell.txt` line 687 / 699–702):

> “by labeling weak edges (<11 synapses for male CNS, <8 for FAFB/FlyWire) (Figure S7E; see STAR Methods) as noisy. While this removes 80% of connections, most synapses (∼90%) belong to strong connections that are reliably observed within and across datasets.”

**VERIFIED.** STAR Methods, “Definition of dimorphic edges” (*Cell* e11; `berg2026_cell.txt` lines 2391–2392):

> “To align connection weights between the male and female datasets, we modeled the systematic differences between them using a simple principal component analysis (PCA), using only edges between isomorphic types. To make this more robust, we first removed outliers by computing a Mahalanobis-like distance in the 2D (weight in male versus female) space using median centering and MAD scaling, then excluded points with distance > 3.0. A PCA on the remaining data yielded a scaling factor of 0.79 which we applied to all male CNS edge weights for cross-dataset comparisons (i.e. there are generally more synapses in the male CNS; see Figure S7D).”

**VERIFIED**, same Methods stretch on the 90% persistence thresholds:

> “To achieve a 90% probability of an isomorphic edge in the male also being present in the female dataset, it needs to consist of >10 synapses. In the opposite direction, that threshold is >7 synapses – likely due to the generally stronger edges in the male CNS.”

**INFERRED** (arithmetic only): applying 0.79 to male weights is the same statement as “male isomorphic type–type edges are, on the PCA axis they used, about 1/0.79 ≈ 1.27 times the female FAFB/FlyWire edges,” after outlier removal. The paper never writes “1.27×.” This factor is **not** the given 2.1× per-cell figure, and it is **not** an ORN→LN or ORN→PN number.

**UNVERIFIED:** the images of Figure S7D and S7E (still not retrieved; see Changes). The 0.79 factor and the caption-level claim are in the STAR Methods text.

The bioRxiv preprint (10.1101/2025.10.09.680999, version 2, 30 Oct 2025) still has no “0.79” or “scaling factor of 0.79” in the extracted text. **VERIFIED** as absent there. The published *Cell* STAR Methods is the source for 0.79.

Berg’s female comparison uses FlyWire **v783**, not Shiu’s v.630. **VERIFIED**, STAR Methods, “Typing in the central brain and the ventral nerve cord” (`berg2026_cell.txt` line 2162):

> “Neurons were principally typed by cross-matching to the FAFB/FlyWire29,30,74 (v783), the hemibrain31 (v1.2.1) and the male adult nerve cord (MANC, v1.2.3).”

---

### SHOULD-FIX 3 — Scheffer 2025 compares human-visible synapse counts across MaleCNS, FlyWire, hemibrain, BANC and MANC, and states reasons

**VERIFIED.** Scheffer, L.K. (2025), “Synapse Detection Efficiency in EM *Drosophila* Connectomics,” bioRxiv 10.1101/2025.10.16.682869, 19 Oct 2025, still the only version found on 21 Nov 2026. Preprint, “not certified by peer review.” Quotes re-checked in `synapse_detection_efficiency_2025_biorxiv.txt`.

Abstract (line 37):

> “We find that in almost all known cases where a volume has been reconstructed by both techniques, isotropic FIB-SEM reconstructions show more human-visible synapses than microtome sliced reconstructions, typically by more than 40%. This strongly suggests, but does not conclusively prove, that synapses are easier to see in isotropic FIB-SEM data.”

Stated reasons, with location:

- **Imaging modality (FIB-SEM vs SS-TEM / microtome).** Abstract, as quoted; Analysis: “This leaves imaging techology as a suspect.” Also: “The most parsimonious explanation of synapse count differences is the greater ability of FIB-SEM to see synapses, in particular those in the direction perpendicular to the cutting plane (see Appendix 2).”
- **Detector precision/recall.** Section “Comparing synapse counts”: software “can vary considerably in effectiveness.” Visible count is defined as `human visible = #detected ∗ precision/recall` (line 191). Table 3 lists the precision/recall he used (including BANC 0.95 / 0.68, which is the **bioRxiv-era** BANC pair; the *Nature* BANC paper now reports 0.87 / 0.78 — see Changes item 4 and NOTE 8).
- **Buhmann versus Princeton (FAFB vs FAFB2).** Introduction: “In 2025, a new set of synapses for the FAFB data set was released. This set uses the segmentation as an aid to finding synapses, and features much better synapse recall, but somewhat less precision (Yu et al. 2025).” After correction, visible totals are 190.1M (FAFB) versus 162.2M (FAFB2); Table 4 gives FAFB2/FAFB = 0.87 in overlapping regions.
- **Proofreading completeness** is deliberately set aside for the main ratios (“We look at raw synapse counts to avoid any dependence on proofreading”) and is reported separately in Table 6: FAFB 41.90%; FAFB2 40.95%; hemibrain 35.25%; CNS 40.10%; MANC 44.43%; BANC 13.67% (16.02% without optic lobes). MaleCNS and FAFB connection-completion are close.
- **Sample size.** Section 2 and Table 5: “Altogether, although size differences cannot be ignored, they are not enough to account for the difference in synapse count.”
- **Sex.** Analysis: “Is the difference the result of sexual dimorphism? This seems unlikely, as both nerve cords and brains of both sexes have been imaged with both SS-TEM and FIBSEM, and in every case the FIBSEM shows more synapses.” Figure 4 caption: Mi1 in female FIB19 is “much more consistent with CNS (same imaging, different sexes) than it is with FAFB (same sex, different imaging).”
- **Sample preparation.** Considered and down-weighted: 1C versus 7C “were prepared identically”; “The FIBSEM reconstruction showed roughly 1.5x more synapses.” “We conclude that while sample preparation differences likely contribute … they are a small contributor compared to other effects.”

Table 4, overlapping regions only, read as (column dataset) / (row dataset), consistent with the text “The global average is 1.49” for FAFB2 versus male CNS (line 258) and with FAFB2/FAFB = 0.87 lining up with 162.2/190.1. MaleCNS (CNS) column:

| Versus (row) | CNS / that dataset (Table 4) |
|--------------|------------------------------|
| BANC         | 1.95 |
| FANC         | 1.45 |
| FAFB (Buhmann) | 1.26 |
| FAFB2 (Princeton) | 1.45 (text: 1.49) |
| HBI (hemibrain, fully internal compartments) | 1.34 |
| MANC         | 1.18 |

Analysis: “The ratios ranging from 0.89 (from one since superceded synapse detection) to 1.95, with a mean of 1.44 (geometric mean of 1.49).”

On analyses of strong paths (quoted as what the paper says, not as a recommendation):

> “Strong paths remain strong paths, and while their absolute strength is unknown, for many analyses a constant scale factor has little effect.”

Scheffer 2025 has no “ORN”, “antennal”, or “glomerul” in the extracted text. It does not publish matched-cell-type per-cell ratios.

**INFERRED:** the given 2.1× (synapses per cell, matched types, MaleCNS v1.0 vs FlyWire v783) is not the same measurement as Scheffer’s 1.26 or 1.45–1.49 compartment ratios. Table 6 completion rates do not by themselves explain a 2.1× per-cell gap.

**UNVERIFIED** from Scheffer et al. 2020 itself: Table 3’s 0.80/0.80 for hemibrain, MANC and CNS are labelled “Published statistics.” Berg *Cell* reports MaleCNS 0.82/0.81, not 0.80/0.80 (SHOULD-FIX 7). Scheffer 2020 Figure 5 reports per-region detector precision/recall and says human proofreaders typically achieve 0.9 (T-bars) and 0.8 (PSDs).

---

### SHOULD-FIX 4 — FlyWire’s Buhmann detector, the set Shiu used, is known to be weaker on sensory neurons

**VERIFIED.** Dorkenwald et al. 2024, *Nature* 634: 124–138, Discussion (`PMC11446842.xml`):

> “The automated synapse detection currently used by FlyWire was performed by Buhmann et al. 7 in an independent effort. By combining the FlyWire brain reconstruction with these synapses, the resulting connectome inherits the limitations from both. In the case of the synapse detection, users should be aware that the ground truth was limited to a few neuropils. As a result, synapse detection performance is lower for some cell types, and we are aware that sensory neurons are particularly affected. FlyWire’s reconstruction is compatible with any synapse prediction method and improved synapse prediction will be made available in the future.”

Same paper, opening results: the whole brain “contains … around 130 million synapses. This equates to 7.4 synapses per µm³.”

Same paper, Methods, “Synaptic connections”:

> “We imported the automatically predicted synapses from Buhmann et al. 7, which we combined with the synapse segmentations by Heinrich et al. 118 to assign scores to all synapses to improve precision. … The dataset published by Buhmann et al. contained ~244 million synapses. We removed synapses … (2) It had a score ≤50. Additionally, we removed duplicate synapse annotations … within a distance of 100 nm … After filtering, we were left with ~130 million synapses.”

Shiu’s “cleft score cutoff of 50” matches this score filter. **INFERRED** as the same filter, not independently re-derived.

This is the published reason a **global** MaleCNS / FlyWire ratio can understate the gap on ORN edges. The given 5.8× (ORN→LN) and 3.2× (ORN→PN) are not contradicted or confirmed by a published AL-specific MaleCNS-versus-FlyWire count table; none was found.

---

### SHOULD-FIX 5 — v783 and the later “Princeton” synapses are not the graph Shiu calibrated on

**VERIFIED.** Yu et al. (2025), bioRxiv 10.1101/2025.07.11.664377, 17 July 2025 (still v1 on 21 Nov 2026):

> “Overall the Princeton method has detected more synapses compared to Buhmann (76,944,499 vs 54,492,922) and these also make up more connected neuron pairs (22,285,323 vs 15,091,983).”

(The universe of those counts is not equated in the text with Dorkenwald’s ~130 million or Scheffer’s 130.1M / 187.9M; they are not merged here.)

Yu abstract: up to a 0.23 F-score increase in challenging areas, “maintaining performance in control regions.” Body: “Princeton synapses show a significant increase in recall for every volume analyzed (Figure 3).” Target regions listed include “Antennal Lobe.” Control regions include calyx, lateral horn, ellipsoid body, and protocerebral bridge.

Availability: the “Connections Princeton No Threshold” CSV is “from FlyWire FAFB Full Brain snapshot v783”; “The connectome with Princeton synapses is also available for exploration in Codex (default since July 2025).”

**INFERRED:** Shiu (October 2024) and the v.630 files (March 2023) predate Princeton synapses becoming the Codex default (July 2025). v783 in Yu is the **root-ID snapshot** onto which Princeton synapses were later mapped, not the connectivity table Shiu fit. The README still says the paper used version 630.

---

### SHOULD-FIX 6 — Schlegel 2024 compares FlyWire with hemibrain, not MaleCNS, and does not publish a single density ratio

**VERIFIED.** Schlegel et al. 2024, *Nature* 634: 139–152, “Connectivity stereotypy” (`PMC11446831.xml`):

> “Synapse counts were also largely consistent within cell types, both within and across brains. To enable a fair comparison, the FlyWire synapse cloud was restricted to the smaller hemibrain volume. Although this does not correct for other potential confounds such as differences in the synaptic completion rates or synapse detection, pre- and post-synapse counts per cell type were highly correlated, both within brains (Pearson R = 0.99; P < 0.001) and across brains (Pearson R = 0.92 and 0.76 for pre- and post-synapses, respectively; P < 0.001; Fig. 4a,b and Extended Data Fig. 4k,l).”

> “Weights of individual edges are highly correlated within (Pearson R = 0.97, P < 0.001) and across (Pearson R = 0.8, P < 0.001) brains.”

> “any edge of more than ten synapses in any hemisphere can be reproducibly (>90% of the time, rounded) found in the other two hemispheres. Although only 16% of all edges meet this threshold, they comprise around 79% of all synapses.”

> “We also analysed normalized edge weights expressed as the fraction of the input onto each downstream neuron; this accounts for the small difference in synaptic completion rate between FlyWire and the hemibrain.”

> “edges greater than 2.6% edge weight (or 31 synapses) can be considered to be strong.”

Their technical-noise model uses “the precision (0.72) and recall (0.77) rates reported previously 46,” ref. 46 = Buhmann et al. 2021.

Scheffer 2025 on Schlegel Extended Data Figure 2(e): three regions that appeared to have fewer hemibrain synapses than FAFB (CAN(R), EPA(L), LO(R)) “are all truncated in the hemibrain sample but not in FAFB.” **VERIFIED** as Scheffer’s reading. The Extended Data figure image was not re-opened.

**UNVERIFIED:** a secondary wording that “a 30-synapse hemibrain edge averaged 29 synapses in FlyWire.” That sentence is still not in the Schlegel XML. The paper reports correlations and persistence thresholds, not that average.

Berg et al. 2026 cite this paper as the “technical reasons” for systematic synapse-count differences (BLOCKER 2).

---

### SHOULD-FIX 7 — Berg et al. do not publish 2.1×, 5.8× or 3.2× as synapse-density ratios

**VERIFIED** from the *Cell* 2026 full text (`berg2026_cell.txt`). The numerals 2.1, 5.8 and 3.2 appear as other percentages:

- “Of the remaining 2.1%, some remain unmatched due to limitations of previous partial datasets.”
- “Ignoring noisy edges, 5.8% of connections in the male central brain (and 1.2% in the female) are dimorphic.”
- “11% of all isomorphic cell types in the male (3.2% in females) have more than 5% dimorphic in- or outputs.”

The published MaleCNS-versus-female scaling statement is the 0.79 factor and “generally more synapses in the male CNS” (BLOCKER 2). There is no AL / ORN→PN / ORN→LN count ratio in the extracted text.

MaleCNS synapse detection, Results (`berg2026_cell.txt` lines 142–144):

> “46 million presynapses connected to 312 million postsynapses were detected with a precision/recall of 0.82/0.81 (Figure S1I; STAR Methods).”

STAR Methods, “EM Volume Synapse Identification”:

> “Two separate networks for presynaptic T-bar detection and postsynaptic partner detection from that reconstruction were further fine-tuned with additional training ground-truth synapse data collected in the brain and VNC regions of the full CNS sample. … synapses were densely labeled in 114 cubes of 300 × 300 × 300 voxels, spanning 81 ROIs. … the subvolumes contained 2,303 annotated T-bars and 16,870 annotated postsynaptic partners.”

> “initially selected validation cubes in the lamina (LA) showed poor recall … some presynapses in the lamina having a differing morphology, which was not well-represented in the original training set.”

> “There is some variation in accuracy across ROIs, but performance is largely clustered, and generally above 0.8 recall for T-bars alone and 0.7 recall for synapses.”

Imaging: 8 × 8 × 8 nm eFIB-SEM. Proofread connectome: “124.2M synaptic connections”; “40.1%” of connections have both sides proofread; “94% pre- and 42% postsynaptic completion rates.”

---

### NOTE 8 — Precision / recall, completeness, and BANC (updated)

All **VERIFIED** from the cited location, except where marked.

**Buhmann et al. 2019/2021** (`buhmann2019_biorxiv.txt`): 244 million putative partners; “between 92% and 96% of edges linking connected neurons are correctly classified as weakly connected (less than five synapses) and strongly connected (at least five synapses)”; “f-scores of 0.73, 0.68, 0.66 and 0.59 for the four different brain areas.” Dorkenwald Methods names those evaluation regions as “calyx, lateral horn, ellipsoid body and protocerebral bridge.” Schlegel uses precision 0.72 and recall 0.77; Scheffer 2025 Table 3 lists FAFB (Buhmann) recall 0.65 and precision 0.95. **VERIFIED** that the headline pairs differ; they were not reconciled here.

**Scheffer et al. 2020, eLife**, Figure 5 caption: human proofreaders “typically achieve 0.9 precision/recall on T-bars and 0.8 precision/recall on PSDs.” “64 million PSDs and 9.5 million T-bars.” Figure 15: median connection precision 88%.

**Bates et al. 2025 bioRxiv** (10.1101/2025.07.31.667571), as in the 18 Nov report:

> “F-score: .79, precision: .68, recall: .95; Fig. 1b,c, Extended Data Fig. 1c).”

Methods then: 218,460,852 synaptic links; Kenyon-cell outgoing 139 versus FAFB 213 (cleft score threshold > 50); possible under-detection of “axo-axonic connections between sensory neurons.”

**Bates et al. 2026 *Nature*** (10.1038/s41586-026-10735-w, 8 June 2026, PMC13518251; text saved as `bates2026_banc_nature_PMC13518251.txt`). Main text:

> “To automatically identify synapses in the BANC dataset, we trained two CNNs 35 to predict presynaptic and postsynaptic locations with high accuracy (F-score = 0.83, precision = 0.87, recall = 0.78; Extended Data Fig. 2b). Overall, 74% of detected presynaptic links and 23% of postsynaptic links have been attached to identified (proofread and/or cell typed) cells; 18% of synapses have identified cells on both sides (Fig. 1c and Extended Data Fig. 2c,d). A comparison of the normalized synaptic count between all pairs of cross-matched, identified cell types in the CNS revealed strong concordance between the BANC and other adult fly connectomes”

Methods, evaluation (16 cutouts of 2 × 2 × 0.7 µm³, two experts, dense review): F-score, precision and recall “for the individual cutouts and for the dataset as a whole (using the total number of synapses in each category summed across all 16 cutouts).”

Methods, “Synapse detection”: two-step method pretrained on FAFB, “tuned … with an additional 721 (about 21% new) labels from the BANC dataset.” File `synapses_v2` “lists 218,460,852 synaptic links … of which 74% of presynaptic ends and 23% of postsynaptic ends are connected to a proofread neuron. … Overall, 18% of synaptic links have an identified neuron on both sides. For other densely reconstructed datasets, this number is 41.9% for FAFB, 35.3% for hemibrain, 44.4% for MANC and 40.1% for connections within the neuropils of maleCNS.”

> “the average number of outgoing connections for Kenyon cells (36.6 synaptic links) is substantially smaller than in FAFB (around 200 synaptic links, cleft score threshold >50). Axo-axonic connections between peripheral sensory neurons may also be underdetected.”

A later `synapses_v3` with 259,409,001 links, “made with more BANC-centric training data,” is mentioned and “reported in ref. 31”; that table was not opened here.

The BANC-versus-other comparison in both versions is **normalized**, so those sentences are not raw count ratios. The Kenyon-cell outgoing comparison is BANC versus FAFB, not MaleCNS versus FlyWire, and not ORN.

**MANC.** Scheffer 2025 Table 3 lists 74.5M detected and 0.80/0.80 as “published statistics.” The Takemura / Marin papers were still not fetched as full text, so those 0.80/0.80 figures remain **UNVERIFIED** against the MANC papers themselves. Bates *Nature* 2026 quotes MANC connection completeness as 44.4% (VERIFIED as Bates’s statement; matches Scheffer Table 6).

---

### NOTE 9 — What is, and is not, published on AL / ORN synapses and on matched-cell-type per-cell ratios

Published and **VERIFIED**:

- Dorkenwald 2024: “sensory neurons are particularly affected” by Buhmann detection (SHOULD-FIX 4).
- Yu 2025: Antennal Lobe was a “challenging” evaluation region for Princeton versus Buhmann; no MaleCNS comparison in that paper (SHOULD-FIX 5).
- Bates 2026 *Nature*: possible under-detection of axo-axonic connections between peripheral sensory neurons; Kenyon-cell outgoing 36.6 versus FAFB ~200 (NOTE 8).
- Berg 2026: lamina T-bars needed a special detector; AL is discussed as a region of relatively high postsynaptic completeness / downstream capture, not as a MaleCNS-versus-FlyWire density ratio.

**Official MaleCNS per-ROI source data** (not a cross-dataset ratio). `flyconnectome/2025malecns` README:

> “The precision and recall of pre-synapse (t-bar) predictions based on validation data collected in 81 neuropil compartments. This is the source data for the upper plot in Fig 1i of Berg et al. (2025).”

> “The precision and recall of predicted pre-to-post synaptic connections … source data for the lower plot in Fig 1i …”

(The *Cell* paper’s corresponding panel is Figure S1I.) Files, fetched 21 Nov 2026, commit `a2156b0` (13 May 2026, 11:12 AM PDT):

| ROI | T-bar recall | T-bar precision | Connection recall | Connection precision |
|-----|--------------|-----------------|-------------------|----------------------|
| AL(L) | 0.944 | 0.814 | 0.975 | 0.966 |
| AL(R) | 0.885 | 0.840 | 0.905 | 0.950 |

From `male-cns-v1.0-traced-synapse-capture-by-roi.csv` (source data for Fig. 1D / Fig. S9g in the repo’s 2025 numbering):

| ROI | PreSyn | PostSyn | pre traced | post traced | both-sides conn |
|-----|--------|---------|------------|-------------|-----------------|
| AL(L) | 626,980 | 3,310,043 | 0.867 | 0.550 | 0.485 |
| AL(R) | 656,660 | 3,438,694 | 0.920 | 0.600 | 0.556 |

**VERIFIED** as the CSV values and as MaleCNS-only detector accuracy and proofreading capture. They are **not** comparable to the given 2.1× / 5.8× / 3.2×, which are cross-dataset synapse counts on matched types.

**UNVERIFIED / not found in the published papers and preprints below:** a matched-cell-type per-cell synapse-count ratio, or an ORN→PN or ORN→LN ratio, between MaleCNS and FlyWire, hemibrain, BANC or MANC. The given 2.1×, 5.8× and 3.2× remain the user’s measurement.

---

## Compact comparison (published quantities only)

Quantities are not interchangeable. Empty cells were not found as a single published number.

| Comparison | Published quantity | Value | Source | Tag |
|---|---|---|---|---|
| Shiu calibration graph | FlyWire public materialization | v.630, 127,400 proofread neurons | Shiu 2024 Methods | VERIFIED |
| Shiu W_syn | Free parameter, mV per synapse | 0.275 mV, set so 100 Hz sugar GRNs give ~80% max MN9 | Shiu 2024 Methods; `model.py` L37, L183, commit `2a83ad6` / HEAD `91bdd1e` | VERIFIED |
| Shiu synapse filter | Cleft / Heinrich score | cutoff 50 | Shiu 2024 Methods; Dorkenwald Methods | VERIFIED |
| Shiu synapse detector | — | Buhmann et al. 2021 (inferred from citations, date, and Dorkenwald) | — | INFERRED |
| MaleCNS vs FAFB/FlyWire, isomorphic type–type edges | PCA scale applied to **male** weights | 0.79 (“generally more synapses in the male CNS”) | Berg 2026 STAR Methods; Fig. S7D (figure image unread) | VERIFIED (text) |
| MaleCNS vs FAFB/FlyWire, noise floor | Synapses / edge | <11 male vs <8 female called noisy | Berg 2026 Results | VERIFIED |
| MaleCNS vs FAFB (Buhmann), overlapping compartments | Human-visible count ratio, CNS/FAFB | 1.26 | Scheffer 2025 Table 4 | VERIFIED |
| MaleCNS vs FAFB2 (Princeton), overlapping compartments | Same | 1.45 (text: global average 1.49) | Scheffer 2025 Table 4 and Fig. 3 text | VERIFIED |
| MaleCNS vs hemibrain (internal compartments) | Same | 1.34 | Scheffer 2025 Table 4 | VERIFIED |
| MaleCNS vs BANC, overlapping compartments | Same | 1.95 | Scheffer 2025 Table 4 | VERIFIED |
| MaleCNS vs MANC, overlapping compartments | Same | 1.18 | Scheffer 2025 Table 4 | VERIFIED |
| FIB-SEM vs SS-TEM, “typically” | Human-visible | “more than 40%”; ratios 0.89–1.95, mean 1.44, geomean 1.49 | Scheffer 2025 Abstract and Analysis | VERIFIED |
| FlyWire vs hemibrain, per cell type | Pearson R (not a ratio) | pre 0.92, post 0.76 across brains, FlyWire cloud clipped to hemibrain volume | Schlegel 2024 | VERIFIED |
| Princeton vs Buhmann (Yu’s comparison set) | Detected synapses | 76,944,499 vs 54,492,922 | Yu 2025 | VERIFIED |
| MaleCNS detector P/R | Prec. / recall | 0.82 / 0.81 overall; AL T-bar 0.944/0.814 (L) and 0.885/0.840 (R) | Berg 2026; `2025malecns` CSVs | VERIFIED |
| FlyWire Buhmann raw vs filtered | Synapse count | ~244M → ~130M after unassigned, score ≤50, and 100 nm duplicates | Dorkenwald 2024 Methods | VERIFIED |
| BANC detector P/R (bioRxiv) | F / prec. / recall | 0.79 / 0.68 / 0.95 | Bates 2025 bioRxiv | VERIFIED |
| BANC detector P/R (*Nature*) | F / prec. / recall | 0.83 / 0.87 / 0.78 | Bates 2026 *Nature* | VERIFIED |
| Given 2.1× / 5.8× / 3.2× | Per-cell, matched types, MaleCNS v1.0 vs FlyWire v783 | not a published table in the papers below | — | not verified here |

---

## What could not be accessed

- **Cell Figure S7D and S7E images**, and the rest of the *Cell* supplement: cell.com still Cloudflare 403; EuropePMC has no open full text. The 0.79 factor is from STAR Methods text, not from a re-read of the figure.
- **Codex / neuPrint / FlyWire materializations** as live databases. Version statements are from papers and the Shiu GitHub repo only. The `mcns_fw_edge_comp.feather` male–female edge table in `2025malecns` was listed but not opened or re-analysed (it is source data for Berg’s dimorphism statistics, not a published per-cell ratio).
- **Buhmann et al. 2021 Nature Methods official PDF / PMC full XML**: still unavailable; quotes remain from the 2019 bioRxiv PDF plus Dorkenwald.
- **MANC (Takemura et al. / Marin et al.) full text**: still not fetched. MANC 0.80/0.80 is only as listed in Scheffer 2025 Table 3 (UNVERIFIED against the MANC papers).
- **Schlegel Extended Data figures as images** (ED Fig. 2e, 4k,l, 6). Slope or offset of FlyWire versus hemibrain synapse counts, if present only in those plots, remains UNVERIFIED.
- **Huang et al. 2018**, cited by Scheffer 2020 for the hemibrain T-bar/PSD networks: not re-fetched.
- A published **matched-cell-type per-cell** or **ORN / antennal-lobe** MaleCNS-versus-FlyWire synapse-count table: not found.
- The BANC *Nature* PDF itself failed to download from PMC (HTML interstitial); quotes are from the PMC HTML full text.

---

## Sources on disk under `/workspace/flycns/lit/`

Unchanged from 18 Nov 2026 unless noted:

- Berg et al. 2026 *Cell*: `berg2026_cell_iris.pdf`, `berg2026_cell.txt`
- Berg et al. bioRxiv v2: `berg_biorxiv_v2_PMC12636603.pdf`, `.txt`, `berg.html`
- Scheffer 2025 bioRxiv: `synapse_detection_efficiency_2025_biorxiv.pdf`, `.txt`
- Yu et al. 2025 bioRxiv: `yu2025_princeton_synapses_biorxiv.pdf`, `.txt`
- Bates et al. 2025 BANC bioRxiv: `bates2025_banc_biorxiv.pdf`, `.txt`
- **New:** Bates et al. 2026 BANC *Nature* PMC HTML text: `bates2026_banc_nature_PMC13518251.txt`
- **New:** `malecns_supp_2026-11-21/` (README + three official CSVs from `flyconnectome/2025malecns`)
- Buhmann et al. 2019 bioRxiv: `buhmann2019_biorxiv.pdf`, `.txt`
- Shiu repo README: `shiu2024_repo_Readme.md`; paper at `PMC11446845.txt` / `.xml`
- Dorkenwald 2024 `PMC11446842.xml`; Schlegel 2024 `PMC11446831.xml`; Scheffer 2020 `PMC7546738.xml`

Primary papers: Shiu et al. 2024 *Nature* 10.1038/s41586-024-07763-9; Dorkenwald et al. 2024 *Nature* 10.1038/s41586-024-07558-y; Schlegel et al. 2024 *Nature* 10.1038/s41586-024-07686-5; Buhmann et al. 2021 *Nat. Methods* 10.1038/s41592-021-01183-7; Scheffer et al. 2020 *eLife* 10.7554/eLife.57443; Berg et al. 2026 *Cell* 10.1016/j.cell.2026.08.015; Yu et al. 2025 bioRxiv 10.1101/2025.07.11.664377; Scheffer 2025 bioRxiv 10.1101/2025.10.16.682869; Bates et al. 2025 bioRxiv 10.1101/2025.07.31.667571; Bates et al. 2026 *Nature* 10.1038/s41586-026-10735-w.
