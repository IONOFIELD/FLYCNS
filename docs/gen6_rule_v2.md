# Generation 6 rule, version 2: amendments committed before the Phase 1b results are read

Status: committed 18 October 2026, after the 13 Phase 1b jobs finished (runs 29 to 32, at registration
`6e50cba`) and **before any Phase 1b result file was opened**. No result branch (`rerun-out/29..32/*`) had been
read when this file was written. `docs/gen6_rule.md` stays as it was; this file amends it, and where they differ
this file wins. Nothing here changes the Phase 1b registration, its code or its registered verdicts. These
amendments only govern how the generation-6 rule reads the Phase 1b data.

Sources of the amendments:
- the independent blind code review of `54eee14..1710398` (Grok, 18 October 2026), findings F1 to F9;
- the MaleCNS Cell Type Explorer, which gives MN9 input totals.
Every finding was checked against the code before it was used here.

## 1. Erratum: the two MN9 cells do not receive equal input

`docs/gen6_rule.md` ("Why LATERALITY gates the result") says the connectome paths give the two MN9 cells
roughly equal input. **That is false for MaleCNS v1.0.** The MaleCNS Cell Type Explorer lists:

| cell | input (post) synapses | output (pre) synapses |
|---|---|---|
| MN9_L | 6,358 | 172 |
| MN9_R | 633 | 244 |

MN9_R has about one tenth of MN9_L's input. No published biological left/right MN9 asymmetry was found. Shiu et
al. 2024's model treats each MN9 as favouring contralateral input, symmetrically. The most likely explanation is
incomplete reconstruction of MN9_R's dendrite in the dataset. This is an interpretation, not a verified fact.

**Consequence, stated before the results:** a high MN9 laterality index (LI) on the male data is expected from
this input gap alone, whatever the network dynamics. Prediction P5 (LI ≥ 0.8) is now expected for this reason.

Optional local confirmation, which changes nothing below: input synapses per MN9 at the model's floor of 5,
from `data/edges.parquet`.

## 2. Male MN9 readout: report both cells; the registered two-cell mean decides

- **FUNCTION is unchanged.** It uses the two-cell mean, as registered. If MN9_R is under-reconstructed the
  mean understates the response, so a FUNCTION pass on the mean is conservative and stands as a real pass.
  Switching to MN9_L alone would change a registered statistic after a reason to want a different answer had
  appeared. That is not allowed.
- **Also reported, never deciding:**
  - MN9_L rate and MN9_R rate per trial (`mn9_per_cell_hz` with `mn9_cells` and `mn9_sides`);
  - the max cell;
  - LI;
  - the input-synapse counts of section 1.
- **Outcome H, reinterpreted.** If the chosen w fails LATERALITY (median LI ≥ 0.8) **and** MN9_R has fewer
  than one third of MN9_L's input synapses, the asymmetry is attributed to the reconstruction gap. Then:
  1. w_scale is still not changed in generation 6 on the basis of MN9 (unchanged from H).
  2. The next step is a registered **MN9_R input correction**, not the one-side-at-a-time run. The correction
     is mirroring MN9_L's input partners onto MN9_R, or normalising MN9_R's input weights to MN9_L's total.
     The choice is fixed in its own registration.
  3. FUNCTION and LATERALITY are then re-run on the corrected input.

  If MN9_R's input is not deficient (at least one third of MN9_L's), H keeps its original meaning: hold
  w_scale and run one side at a time.

## 3. Outcome-B grouping: `VNC-unspecified` is VNC

The **VNC** group is every label whose stem is LegNp, Ov, mVAC, WTct, HTct, NTct, IntTct, LTct or ANm, **plus
`VNC-unspecified`**. That label is VNC tissue that MaleCNS left unnamed, not an unassigned cell (finding F1).
Everything else stays as `gen6_rule.md` says:
- the VNC nerves (ProLN, MesoLN, MetaLN, DMetaN, AbN2, AbN3, AbN4, AbNT) stay separate;
- brain, optic-lobe and SEZ labels stay separate;
- `CentralBrain-unspecified`, `Optic-unspecified(L/R)` and `?` stay separate.

The label list was checked against the MANIFEST-matched data on 18 October: 117 labels, 23 VNC neuropils plus
`VNC-unspecified`, and no neck-connective label among dominant ROIs.

**Recomputed, not re-run.** Phase 1b's registered code does not merge `VNC-unspecified`, so phase1b.json's
`tail_groups` uses the old grouping. Generation 6 recomputes Outcome B from the per-label arm data
(`tail_by_neuropil`, `drive_by_neuropil`, `group_sizes`) under this grouping. phase1b.json's `tail_groups` is
reported as computed but does not decide Outcome B.

## 4. Outcome B, fully defined (findings F2, F3 and F4)

At the smallest w that passes FUNCTION (screen) but fails STABILITY, in family `male_flycns`:

1. **One group across both drives.** Pool the tail spikes of every self-sustained trial under the sugar
   **and** the blind drive. The Outcome-B group G is the group (section 3 grouping) with the most pooled tail
   spikes. Its share is G's pooled tail spikes divided by all pooled tail spikes.
2. **Rates come from counts.** Every rate is spikes / cells / seconds, built from summed spikes and summed
   `group_sizes`. Per-label rates are never summed. The `_merge` rate column in Phase 1b's code sums rates and
   is not used (F2).
3. **STABILITY without G, all three parts.** Leave G's cells out of every whole-CNS readout, in both windows,
   numerator and denominator, then recompute:
   - (a) 0 of 10 sugar-drive trials self-sustained;
   - (b) 0 of 10 blind-drive trials self-sustained;
   - (c) under the blind drive, the 95% intervals of whole-CNS rate and fraction active lie wholly below 1 Hz
     and 10%.
   Intervals: `flycns.stats.bootstrap` over trials, 2,000 resamples, seed 0. The fraction active without G is
   (drive active − G's drive active) / (cells − G's cells).
4. **Outcome B holds** if G's share is ≥ 0.5 and (a), (b) and (c) all pass without G.

## 5. Intervals for FUNCTION (screen) and STABILITY (c) (finding F4)

Phase 1b's sweep table reports medians, and its `largest_drive_dependent` column uses the median, so that column
is **not** STABILITY. Generation 6 computes the rule's 95% intervals itself, from the per-trial arm records,
exactly as `gen6_rule.md` defines them.

## 6. Labels and sensitivity (findings F5 and F7)

- The FlyWire sweep `mn9` column is the **contralateral MN9 only**, matching phase 1's A1 statistic. It is
  labelled as such wherever it is reported and is never compared directly with the male two-cell mean.
- LI with few spikes is forced towards 1. As a **reported sensitivity only**, LI is also given restricted to
  trials with at least 5 MN9 spikes in total, together with that count. The LATERALITY decision uses the
  registered definition.

## 7. Known code issues, fixed at the next code change, not now

- F2: the `_merge` rate column.
- F6: the docstring says "ascending", but the FlyWire order is contra then ipsi.
- F8: the FlyWire superclass grouping is degenerate.
- F9: the VNC unit test omits `VNC-unspecified` and the real nerve labels.

None of them changes a registered Phase 1b verdict. The Phase 1b code is frozen with its registration.
