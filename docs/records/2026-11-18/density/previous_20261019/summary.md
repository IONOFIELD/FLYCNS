# MaleCNS vs FlyWire v783: synapses per cell on the same cell types (exploratory)

Exploratory and read-only. It goes into no score. Nothing tracked was edited, committed or pushed.

**Data.**
- **MaleCNS:** the pinned `data/edges.parquet` and `data/neurons.parquet`, matching `data/MANIFEST.json`. Every edge
  counts, whatever its transmitter.
- **FlyWire v783 connections:** `proofread_connections_783.feather` from Zenodo 10676866. Its MD5 matches Zenodo's.
- **FlyWire cell types:** `flyconnectome/flywire_annotations` at commit a83b277 (2026-09-29, after v3.2.0).

URLs, versions and sha256 are in `sources.json`. No download needed a login.

**Method.**
- **Floor:** both datasets use pairs with at least 5 synapses. FlyWire's table is per pair and neuropil, so it was
  summed per pair first, then floored. MaleCNS's file already stops at 5.
- **Per type:** mean input and mean output synapses per cell, counting every partner, typed or not. The ratio is
  MaleCNS / FlyWire.
- **Groups:**
  - AL PN, AL LN and Kenyon cell use the lists in `data/gen6_phaseA_celltypes.json`.
  - ORN means the type starts with `ORN_`.
  - LH means the type starts with `LH`. This is my rule, because the JSON has no ORN or LH list.
  - Everything else matched is "other brain".

The script is `density.py` and the per-type table is `by_type.csv`. All numbers are in `results.json`.

## In plain words

**Yes, MaleCNS counts about twice as many synapses per cell as FlyWire on the same types.**
- 4,688 type names exist in both datasets.
- The median type has 2.06× the input (IQR 1.52–3.06) and 2.12× the output (IQR 1.61–3.12).
- Pooled over every matched cell, the factors are 1.80× input and 1.88× output.
- Cell counts agree for the median type (ratio 1.00), so this is synapses per cell, not cells per type.

This is a whole-dataset offset. It is most likely mainly methodological (different synapse detectors and thresholds)
plus individual and sex differences. It cannot be read as biology from this alone.

**The antennal lobe gets more input than the rest of the brain, but only moderately. Its cells do not send more
output, and the AL→AL loop sits at the brain-wide factor.**

| group | matched types | input ratio, median (IQR) | output ratio, median (IQR) |
|---|---|---|---|
| ORN | 53 | **3.29** (2.07–6.07) | **3.96** (3.19–5.78) |
| AL PN | 161 of 180 listed | 2.34 (1.83–3.45) | **1.42** (1.23–1.83) |
| AL LN | 60 of 79 listed | 2.74 (2.22–4.00) | 1.85 (1.33–2.13) |
| Kenyon cell | 7 of 15 listed | 3.44 (3.12–4.14) | 4.03 (3.64–4.81) |
| LH | 237 | 1.62 (1.10–2.22) | 2.06 (1.61–2.85) |
| other brain | 4,170 | 2.05 (1.52–3.06) | 2.15 (1.64–3.19) |
| **all matched** | **4,688** | **2.06** (1.52–3.06) | **2.12** (1.61–3.12) |

How each group compares with "other brain" (Mann–Whitney on the per-type ratios):
- **AL PN and AL LN input** is higher than the rest of the brain (p < 0.001). The difference is modest: medians of
  2.3–2.7 against 2.05, with widely overlapping IQRs.
- **AL PN output** is *lower* (1.42, p < 0.001). AL LN output is also lower (1.85, p < 0.001).
- **ORNs** are the clear outlier: about 3–4× on both input and output. ORN input is small in absolute terms, so its
  ratios are noisy; the maximum is 29.8.
- **Kenyon cells** are also about 3.5–4×, but only 7 types match by name (see the caveats).
- **LH** is the least inflated group on input (1.62).

**The AL→AL loop, directly.** These are synapses between cells of the matched AL PN and AL LN types (161 PN and 60 LN
types; 613 PN + 290 LN cells in MaleCNS, 614 + 289 in FlyWire):

| | MaleCNS | FlyWire | ratio |
|---|---|---|---|
| total AL→AL synapses | 1,233,400 | 588,268 | 2.10 |
| **per cell (PN + LN)** | **1,366** | **651** | **2.10** |
| PN→PN per cell | 107 | 44 | 2.44 |
| PN→LN per cell | 371 | 167 | 2.22 |
| LN→PN per cell | 379 | 198 | 1.91 |
| LN→LN per cell | 510 | 243 | 2.10 |

- **The loop is at the brain-wide factor.** At 2.10× per cell it matches the whole-brain median (2.06 in, 2.12 out).
  The AL loop is not denser than the rest of MaleCNS relative to FlyWire. It carries the same roughly twofold offset.
- **Location of the PN→PN synapses:** in FlyWire, 98% of these AL-group synapses sit in the AL neuropil (577,394 of
  588,268). The exception is PN→PN: 29,156 of 39,499 are in the AL. Of the other 10,343, 7,600 are in the LH and 815 in the calyx.
  MaleCNS's edge table has no per-synapse neuropil, so its PN→PN cannot be split the same way. If MaleCNS's PN→PN is
  also partly outside the AL, the in-AL PN→PN ratio could be anywhere from 2.4 to 3.3.

## Caveats

**Name matching**
- **Exact string matching only.** Of 11,751 MaleCNS types and 8,846 FlyWire types, 4,688 names match exactly.
  Nothing was matched through synonyms or `hemibrain_type`, so types named differently are left out. That includes
  most Kenyon cells: FlyWire `KCab` or `KCapbp-*` against MaleCNS `KCab-c/m/s` or `KCa'b'-m`.
- **Unmatched AL types:**
  - 19 of 180 AL PN, for example `M_lvPNm30`, `M_vPNml68`, `VM6_lvPN`, `VP1m+VP2_lvPN2` and `CB1296_a`.
  - 19 of 79 AL LN, for example `v2LN34A–F`, `lLN2R_a`, `LN60` and `vLN28`.
  - 8 of 15 KC types.
  - The full lists are in `results.json`.
- **The same name need not mean the same cells.**
  - 503 matched types have cell counts that differ by more than 1.5×. Examples: `Tm6` has 1,526 cells in MaleCNS
    against 1 in FlyWire; `KCa'b'-ap1` 199 against 1; `FS3` 2 against 68.
  - Restricted to the 4,185 count-consistent types, nothing changes: all-matched medians are 2.04 in and 2.10 out;
    AL PN 2.34 / 1.42; AL LN 2.73 / 1.86; ORN 3.29 / 3.96; KC 3.69 / 4.19 (4 types); LH 1.60 / 2.05.
- **What eased the matching.** FlyWire annotations v3.x were revised against MaleCNS v0.9 (Berg et al. 2026), which is
  why so many names line up. The pinned MaleCNS data is v1.0, so a few renames since v0.9 may be missing.

**Floor and synapse counting**
- **The floor is not neutral between datasets.** At about twice the counts, more MaleCNS pairs clear 5 synapses, so a
  common floor somewhat inflates the ratio. FlyWire's floor keeps 34.2 M of its 54.5 M proofread synapses (63%).
  MaleCNS's file has no pairs below 5, so no symmetric no-floor comparison is possible from it.
- **The synapse definitions differ.** FlyEM and Buhmann et al. use different detection and partner assignment, so the
  global factor is largely method. Only *relative* differences between groups say anything about the AL. Even those
  can reflect how each detector behaves in dense neuropils (the AL glomeruli, the calyx).

**Coverage and sampling**
- **Partner coverage differs.** MaleCNS counts partners anywhere in the CNS, including the nerve cord. FlyWire has the
  brain only, and neck-crossing neurons are truncated there. This matters for descending and ascending types, not the
  AL.
- **Peripheral truncation.** ORN and other sensory axons are cut at the edge of each volume. Absolute ORN numbers depend
  on how much nerve each volume holds.
- **Two animals.** Each dataset is one animal, male and female. Sex, individual and side differences are mixed into
  every ratio.
- **Zero-input types.** A few "other brain" types have zero FlyWire input or output (6 input, 37 output). Their ratios
  are undefined and left out.
