# Sugar → MN9 paths (exploratory)

Commit `c1e6e6244570b47ad799bca092fda985ced9a6d4`. data sha256: neurons `b60448d9e2f2…`, edges `61f8c2edbb21…`. Graph: flycns.graph.load_graph('data') defaults (floor 5, amines dropped, unsigned dropped).
Sources: 34 cells {'LB3c': 23, 'LB3b': 11} sides {'L': 17, 'R': 17}. Targets MN9_L 10331, MN9_R 16949. Definitions are in the script's docstring.

## observed graph (170,175 cells, 6,127,738 edges)

### MN9_L (10331): total signed input 5,651; shortest hops from sugar = 2
Direct input: 93 partners, +2,805 / −2,846; from partners on a sugar path: 93 partners, +2,805 / −2,846; straight from sugar cells: 0.

| hop | cells | on sugar path | layer input exc / inh (all) | layer input exc / inh (on sugar path) |
|---|---|---|---|---|
| 1 | 93 | 93 | +2,805 / −2,846 | +2,805 / −2,846 |
| 2 | 2,970 | 1,154 | +141,571 / −113,228 | +85,555 / −82,457 |
| 3 | 36,361 | 66 | +2,297,521 / −1,332,125 | +12,368 / −9,327 |
| 4 | 92,492 | 0 | +6,892,392 / −3,053,109 | +0 / −0 |

| # | score | hops | sign | path (synapses, normalised) |
|---|---|---|---|---|
| 1 | 3.35e-05 | 3 | + | LB3c_R →(87, 0.076) GNG232_R →(46, 0.007) GNG108_R →(348, 0.062) MN9_L |
| 2 | 2.92e-05 | 3 | + | LB3b_R →(56, 0.030) ANXXX462b_R →(27, 0.012) DNge062_R →(464, 0.082) MN9_L |
| 3 | 2.68e-05 | 3 | − | LB3c_L →(69, 0.065) GNG215_L →(54, 0.016) DNge051_L →(142, 0.025, inh) MN9_L |
| 4 | 2.37e-05 | 3 | + | LB3b_L →(49, 0.035) GNG197_L →(73, 0.066) GNG537_L →(58, 0.010) MN9_L |
| 5 | 2.36e-05 | 3 | + | LB3c_R →(87, 0.076) GNG232_R →(65, 0.018) DNge080_R →(96, 0.017) MN9_L |
| 6 | 2.20e-05 | 3 | − | LB3c_L →(39, 0.015) GNG132_L →(71, 0.023) GNG130_L →(357, 0.063, inh) MN9_L |
| 7 | 2.02e-05 | 3 | − | LB3c_L →(52, 0.049) GNG215_L →(54, 0.016) DNge051_L →(142, 0.025, inh) MN9_L |
| 8 | 2.00e-05 | 3 | + | LB3c_L →(77, 0.071) GNG232_L →(54, 0.016) DNge080_L →(101, 0.018) MN9_L |
| 9 | 1.98e-05 | 3 | + | LB3c_L →(41, 0.029) GNG197_L →(73, 0.066) GNG537_L →(58, 0.010) MN9_L |
| 10 | 1.90e-05 | 3 | − | LB3c_L →(49, 0.046) GNG215_L →(54, 0.016) DNge051_L →(142, 0.025, inh) MN9_L |

### MN9_R (16949): total signed input 364; shortest hops from sugar = 3
Direct input: 25 partners, +161 / −203; from partners on a sugar path: 25 partners, +161 / −203; straight from sugar cells: 0.

| hop | cells | on sugar path | layer input exc / inh (all) | layer input exc / inh (on sugar path) |
|---|---|---|---|---|
| 1 | 25 | 25 | +161 / −203 | +161 / −203 |
| 2 | 1,011 | 563 | +43,459 / −39,652 | +34,177 / −33,879 |
| 3 | 19,747 | 116 | +973,825 / −556,946 | +22,755 / −7,735 |
| 4 | 89,632 | 0 | +6,525,835 / −3,327,200 | +0 / −0 |

| # | score | hops | sign | path (synapses, normalised) |
|---|---|---|---|---|
| 1 | 4.72e-05 | 3 | + | LB3c_L →(77, 0.071) GNG232_L →(50, 0.010) GNG108_L →(25, 0.069) MN9_R |
| 2 | 3.99e-05 | 3 | + | LB3c_L →(77, 0.071) GNG232_L →(54, 0.016) DNge080_L →(13, 0.036) MN9_R |
| 3 | 3.43e-05 | 3 | + | LB3c_R →(87, 0.076) GNG232_R →(65, 0.018) DNge080_R →(9, 0.025) MN9_R |
| 4 | 2.92e-05 | 3 | − | LB3c_R →(51, 0.016) GNG132_R →(73, 0.020) GNG130_R →(34, 0.093, inh) MN9_R |
| 5 | 2.86e-05 | 3 | + | LB3c_L →(69, 0.065) GNG215_L →(33, 0.006) GNG108_L →(25, 0.069) MN9_R |
| 6 | 2.80e-05 | 3 | − | LB3c_R →(49, 0.015) GNG132_R →(73, 0.020) GNG130_R →(34, 0.093, inh) MN9_R |
| 7 | 2.52e-05 | 3 | − | LB3c_R →(44, 0.014) GNG132_R →(73, 0.020) GNG130_R →(34, 0.093, inh) MN9_R |
| 8 | 2.20e-05 | 3 | + | LB3b_L →(54, 0.031) ANXXX462b_L →(17, 0.008) DNge062_L →(31, 0.085) MN9_R |
| 9 | 2.18e-05 | 3 | + | LB3b_L →(49, 0.035) GNG197_L →(15, 0.007) DNge062_L →(31, 0.085) MN9_R |
| 10 | 2.17e-05 | 3 | − | LB3c_R →(38, 0.012) GNG132_R →(73, 0.020) GNG130_R →(34, 0.093, inh) MN9_R |

## mirrored graph (170,175 cells, 6,127,813 edges)

### MN9_L (10331): total signed input 5,651; shortest hops from sugar = 2
Direct input: 93 partners, +2,805 / −2,846; from partners on a sugar path: 93 partners, +2,805 / −2,846; straight from sugar cells: 0.

| hop | cells | on sugar path | layer input exc / inh (all) | layer input exc / inh (on sugar path) |
|---|---|---|---|---|
| 1 | 93 | 93 | +2,805 / −2,846 | +2,805 / −2,846 |
| 2 | 2,978 | 1,156 | +141,854 / −113,803 | +85,814 / −82,890 |
| 3 | 36,367 | 66 | +2,299,286 / −1,331,309 | +12,368 / −9,327 |
| 4 | 92,479 | 0 | +6,889,828 / −3,052,584 | +0 / −0 |

| # | score | hops | sign | path (synapses, normalised) |
|---|---|---|---|---|
| 1 | 3.35e-05 | 3 | + | LB3c_R →(87, 0.076) GNG232_R →(46, 0.007) GNG108_R →(348, 0.062) MN9_L |
| 2 | 2.92e-05 | 3 | + | LB3b_R →(56, 0.030) ANXXX462b_R →(27, 0.012) DNge062_R →(464, 0.082) MN9_L |
| 3 | 2.68e-05 | 3 | − | LB3c_L →(69, 0.065) GNG215_L →(54, 0.016) DNge051_L →(142, 0.025, inh) MN9_L |
| 4 | 2.37e-05 | 3 | + | LB3b_L →(49, 0.035) GNG197_L →(73, 0.066) GNG537_L →(58, 0.010) MN9_L |
| 5 | 2.36e-05 | 3 | + | LB3c_R →(87, 0.076) GNG232_R →(65, 0.018) DNge080_R →(96, 0.017) MN9_L |
| 6 | 2.20e-05 | 3 | − | LB3c_L →(39, 0.015) GNG132_L →(71, 0.023) GNG130_L →(357, 0.063, inh) MN9_L |
| 7 | 2.02e-05 | 3 | − | LB3c_L →(52, 0.049) GNG215_L →(54, 0.016) DNge051_L →(142, 0.025, inh) MN9_L |
| 8 | 2.00e-05 | 3 | + | LB3c_L →(77, 0.071) GNG232_L →(54, 0.016) DNge080_L →(101, 0.018) MN9_L |
| 9 | 1.98e-05 | 3 | + | LB3c_L →(41, 0.029) GNG197_L →(73, 0.066) GNG537_L →(58, 0.010) MN9_L |
| 10 | 1.90e-05 | 3 | − | LB3c_L →(49, 0.046) GNG215_L →(54, 0.016) DNge051_L →(142, 0.025, inh) MN9_L |

### MN9_R (16949): total signed input 5,651; shortest hops from sugar = 2
Direct input: 100 partners, +2,805 / −2,846; from partners on a sugar path: 99 partners, +2,805 / −2,838; straight from sugar cells: 0.

| hop | cells | on sugar path | layer input exc / inh (all) | layer input exc / inh (on sugar path) |
|---|---|---|---|---|
| 1 | 100 | 99 | +2,805 / −2,846 | +2,805 / −2,838 |
| 2 | 3,032 | 1,147 | +148,661 / −118,830 | +89,059 / −85,464 |
| 3 | 35,952 | 60 | +2,242,872 / −1,292,187 | +13,329 / −8,317 |
| 4 | 91,537 | 0 | +6,805,591 / −3,014,963 | +0 / −0 |

| # | score | hops | sign | path (synapses, normalised) |
|---|---|---|---|---|
| 1 | 4.23e-05 | 3 | + | LB3c_L →(77, 0.071) GNG232_L →(50, 0.010) GNG108_L →(348, 0.062) MN9_R |
| 2 | 2.56e-05 | 3 | + | LB3c_L →(69, 0.065) GNG215_L →(33, 0.006) GNG108_L →(348, 0.062) MN9_R |
| 3 | 2.48e-05 | 3 | + | LB3c_R →(87, 0.076) GNG232_R →(65, 0.018) DNge080_R →(101, 0.018) MN9_R |
| 4 | 2.12e-05 | 3 | + | LB3b_L →(54, 0.031) ANXXX462b_L →(17, 0.008) DNge062_L →(464, 0.082) MN9_R |
| 5 | 2.10e-05 | 3 | + | LB3b_L →(49, 0.035) GNG197_L →(15, 0.007) DNge062_L →(464, 0.082) MN9_R |
| 6 | 1.97e-05 | 3 | − | LB3c_R →(51, 0.016) GNG132_R →(73, 0.020) GNG130_R →(357, 0.063, inh) MN9_R |
| 7 | 1.93e-05 | 3 | + | LB3c_L →(52, 0.049) GNG215_L →(33, 0.006) GNG108_L →(348, 0.062) MN9_R |
| 8 | 1.90e-05 | 3 | + | LB3c_L →(77, 0.071) GNG232_L →(54, 0.016) DNge080_L →(96, 0.017) MN9_R |
| 9 | 1.90e-05 | 3 | − | LB3c_R →(49, 0.015) GNG132_R →(73, 0.020) GNG130_R →(357, 0.063, inh) MN9_R |
| 10 | 1.87e-05 | 3 | + | LB3c_R →(34, 0.031) GNG232_L →(50, 0.010) GNG108_L →(348, 0.062) MN9_R |

## Mirror log

```
{
 "partners": 93.0,
 "weight_in": 5651.0,
 "kept": 3.0,
 "kept_w": 71.0,
 "split_partners": 5.0,
 "below_floor_edges": 11.0,
 "below_floor_w": 21.0,
 "sign_mismatch_w": 0.0,
 "no_signed_output_w": 2.5,
 "mn9_swap": 1.0,
 "opposite_not_in_network": 0.0,
 "removed_partners": 25.0,
 "removed_w": 364.0,
 "new_partners": 100.0,
 "weight_out": 5651.0,
 "weight_out_exc": 2805.0,
 "weight_out_inh": 2846.0,
 "weight_in_exc": 2805.0,
 "weight_in_inh": 2846.0,
 "no_signed_output_cells": 1.0,
 "placeholders": 0.0,
 "placeholder_ids": [],
 "cells_before": 170175.0,
 "cells_after": 170175.0
}
```
