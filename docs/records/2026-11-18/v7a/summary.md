# V7a feasibility (MaleCNS, data\neurons.parquet + data\edges.parquet)

Synapse counts use edges with weight >= 5. Side = instance suffix (_L/_R/_unknown); ORNs have no somaSide.
edges.parquet is already floored: min weight 5, so 'all_edges' and 'edges_ge5' below coincide.
ORN→PN = ORN_<glom> onto PN types named <glom>…; ORN→LN = ORN_<glom> onto ALLN types (data\gen6_phaseA_celltypes.json).

| Glomerulus | ORN types (L/R/unk) | PN types (L/R) | ORN→PN syn | PN cells | syn/PN | ORN→LN syn | LN cells |
|---|---|---|---|---|---|---|---|
| DM4 | ORN_DM4 16/15/1 | DM4_adPN 1/1; DM4_vPN 1/1 | 4,801 | 4 | 1200 | 3,953 | 65 |
| DL5 | ORN_DL5 23/19/1 | DL5_adPN 1/1 | 6,944 | 2 | 3472 | 11,830 | 101 |
| VM7d | ORN_VM7d 18/18/0 | VM7d_adPN 3/4 | 10,251 | 7 | 1464 | 10,431 | 89 |
| VM7v | ORN_VM7v 11/14/0 | VM7v_adPN 2/1 | 5,182 | 3 | 1727 | 4,884 | 67 |
| DM1 | ORN_DM1 35/39/0 | DM1_lPN 1/1 | 13,384 | 2 | 6692 | 17,158 | 88 |

## Per PN cell (ORN input from its own glomerulus)

| Glom | Instance | bodyId | ORN syn | from ORN L / R / unk | ORN partners | total input | ORN share |
|---|---|---|---|---|---|---|---|
| DM4 | DM4_adPN_L | 10670 | 2,625 | 1187 / 1438 / 0 | 30 | 7,126 | 0.37 |
| DM4 | DM4_adPN_R | 10613 | 2,156 | 752 / 1378 / 26 | 32 | 7,885 | 0.27 |
| DM4 | DM4_vPN_L | 71476 | 0 | 0 / 0 / 0 | 0 | 186 | 0.00 |
| DM4 | DM4_vPN_R | 73492 | 20 | 12 / 8 / 0 | 3 | 508 | 0.04 |
| DL5 | DL5_adPN_L | 10767 | 3,540 | 2137 / 1278 / 125 | 43 | 7,367 | 0.48 |
| DL5 | DL5_adPN_R | 525105 | 3,404 | 1136 / 2221 / 47 | 42 | 6,871 | 0.50 |
| VM7d | VM7d_adPN_L | 14895 | 1,462 | 994 / 468 / 0 | 36 | 2,674 | 0.55 |
| VM7d | VM7d_adPN_L | 14430 | 1,720 | 1098 / 622 / 0 | 36 | 3,214 | 0.54 |
| VM7d | VM7d_adPN_L | 18834 | 1,457 | 1001 / 456 / 0 | 36 | 2,619 | 0.56 |
| VM7d | VM7d_adPN_R | 13225 | 1,614 | 644 / 970 / 0 | 36 | 3,163 | 0.51 |
| VM7d | VM7d_adPN_R | 511807 | 1,385 | 535 / 850 / 0 | 36 | 2,690 | 0.51 |
| VM7d | VM7d_adPN_R | 527523 | 1,238 | 434 / 804 / 0 | 36 | 2,342 | 0.53 |
| VM7d | VM7d_adPN_R | 18084 | 1,375 | 466 / 909 / 0 | 36 | 2,672 | 0.51 |
| VM7v | VM7v_adPN_L | 13972 | 1,677 | 845 / 832 / 0 | 24 | 3,008 | 0.56 |
| VM7v | VM7v_adPN_L | 16524 | 1,571 | 756 / 815 / 0 | 24 | 2,676 | 0.59 |
| VM7v | VM7v_adPN_R | 13386 | 1,934 | 747 / 1187 / 0 | 23 | 3,845 | 0.50 |
| DM1 | DM1_lPN_L | 10208 | 6,776 | 3454 / 3322 / 0 | 74 | 14,276 | 0.47 |
| DM1 | DM1_lPN_R | 10176 | 6,608 | 2039 / 4569 / 0 | 71 | 14,169 | 0.47 |

## STD-in scope

```
{
 "n_ORN_cells": 2635,
 "n_ORN_types": 53,
 "n_HRN_cells_excluded": 66,
 "ORN_side": {
  "R": 1343,
  "L": 883,
  "unknown": 409
 },
 "all_edges": {
  "edges": 55527,
  "synapses": 937946,
  "onto_ALPN": {
   "edges": 16234,
   "synapses": 469621
  },
  "onto_ALLN": {
   "edges": 39293,
   "synapses": 468325
  },
  "n_ORN_cells_with_edge": 2634,
  "n_target_cells": 809
 },
 "edges_ge5": {
  "edges": 55527,
  "synapses": 937946,
  "onto_ALPN": {
   "edges": 16234,
   "synapses": 469621
  },
  "onto_ALLN": {
   "edges": 39293,
   "synapses": 468325
  },
  "n_ORN_cells_with_edge": 2634,
  "n_target_cells": 809
 }
}
```
