# MaleCNS vs FlyWire v783: synapses per cell on identically named types

Pairs with >= 5 synapses in both datasets (FlyWire summed over neuropils per pair first). Matched types: 4,688 (MaleCNS typed 11,751, FlyWire typed 8,846). Ratio = MaleCNS / FlyWire per type.

| group | types | cells MCNS / FW | input ratio median [IQR] | output ratio median [IQR] | input, no VNC partners | output, no VNC partners |
|---|---|---|---|---|---|---|
| ORN | 53 | 2,635 / 2,277 | 3.29 [2.07–6.07] (n=53) | 3.96 [3.19–5.78] (n=53) | 3.29 [2.07–6.07] (n=53) | 3.96 [3.19–5.78] (n=53) |
| AL PN | 161 | 613 / 614 | 2.34 [1.83–3.45] (n=161) | 1.42 [1.23–1.83] (n=161) | 2.34 [1.83–3.45] (n=161) | 1.42 [1.23–1.83] (n=161) |
| AL LN | 60 | 290 / 289 | 2.74 [2.22–4.00] (n=60) | 1.85 [1.33–2.13] (n=60) | 2.74 [2.22–4.00] (n=60) | 1.85 [1.33–2.13] (n=60) |
| Kenyon cell | 7 | 1,882 / 2,618 | 3.44 [3.12–4.14] (n=7) | 4.03 [3.64–4.81] (n=7) | 3.44 [3.12–4.14] (n=7) | 4.03 [3.64–4.81] (n=7) |
| rest of brain | 4407 | 97,429 / 84,081 | 2.03 [1.50–3.01] (n=4400) | 2.15 [1.64–3.17] (n=4368) | 2.02 [1.50–3.00] (n=4400) | 2.12 [1.63–3.02] (n=4368) |
| AL (ORN+PN+LN) | 274 | – | 2.59 [1.94–4.10] (n=274) | 1.74 [1.29–2.37] (n=274) | 2.59 [1.94–4.10] (n=274) | 1.74 [1.29–2.37] (n=274) |
| all matched | 4688 | 102,849 / 89,879 | 2.06 [1.52–3.06] (n=4681) | 2.12 [1.61–3.12] (n=4649) | 2.06 [1.52–3.05] (n=4681) | 2.10 [1.60–3.00] (n=4649) |

## Group vs rest of brain (two-sided Mann–Whitney U on per-type ratios)

| comparison | median group | median rest | p |
|---|---|---|---|
| AL (ORN+PN+LN) vs rest, ratio_in | 2.59 | 2.03 | 9.3e-14 |
| AL (ORN+PN+LN) vs rest, ratio_out | 1.74 | 2.15 | 1.5e-15 |
| ORN vs rest, ratio_in | 3.29 | 2.03 | 1.7e-07 |
| ORN vs rest, ratio_out | 3.96 | 2.15 | 1.2e-14 |
| AL PN vs rest, ratio_in | 2.34 | 2.03 | 1.3e-05 |
| AL PN vs rest, ratio_out | 1.42 | 2.15 | 6.7e-35 |
| AL LN vs rest, ratio_in | 2.74 | 2.03 | 3.1e-05 |
| AL LN vs rest, ratio_out | 1.85 | 2.15 | 1.9e-05 |
| Kenyon cell vs rest, ratio_in | 3.44 | 2.03 | 3.9e-03 |
| Kenyon cell vs rest, ratio_out | 4.03 | 2.15 | 3.1e-03 |

## AL → AL among matched AL types

| | AL cells | pairs | synapses | synapses per cell |
|---|---|---|---|---|
| MaleCNS | 3,538 | 119,088 | 2,348,721 | 664 |
| FlyWire | 3,180 | 51,809 | 874,602 | 275 |

Ratio of AL→AL synapses per cell: 2.41.

| pre → post | MaleCNS syn per post cell | FlyWire syn per post cell |
|---|---|---|
| AL LN->AL LN | 1,587 | 759 |
| AL LN->AL PN | 558 | 291 |
| AL LN->ORN | 47 | 28 |
| AL PN->AL LN | 1,154 | 521 |
| AL PN->AL PN | 157 | 64 |
| AL PN->ORN | 1 | 0 |
| ORN->AL LN | 1,528 | 262 |
| ORN->AL PN | 764 | 236 |
| ORN->ORN | 30 | 0 |

## Whole datasets

```
{
 "MaleCNS": {
  "cells": 176422,
  "pairs_ge5": 6287789,
  "synapses_ge5": 90297299,
  "brain_cells_nonvnc": 155993
 },
 "FlyWire": {
  "annotated_cells": 139248,
  "pairs_all": 15091983,
  "synapses_all": 54492922,
  "pairs_ge5": 2700513,
  "synapses_ge5": 34153566
 }
}
```
