# Tracing-status audit

Total input = `post` column of data\neurons.parquet (all postsynaptic sites); `ge5` = summed weight of incoming
edges in data\edges.parquet (connections of >= 5 synapses). Pair = a type with exactly one L and one R cell (side
from somaSide, else instance suffix). Flag: max/min input > 3, or either cell's status not `Traced`.

## Status, all cells

| status | cells |
|---|---|
| Traced | 165,122 |
| Orphan | 6,464 |
| <missing> | 4,214 |
| Anchor | 611 |
| Assign | 11 |

## Benchmark cells: 17 sets, 106 types, 21,625 cells

| status | cells |
|---|---|
| Traced | 21,624 |
| <missing> | 1 |

## Flagged one-to-one pairs (2 of 19)

| type | L bodyId | R bodyId | L status | R status | L input | R input | max/min | ge5 L | ge5 R | ge5 max/min | sets |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MN9 | 10331 | 16949 | Traced | Traced | 6,358 | 633 | 10.04 | 5,743 | 386 | 14.88 | feeding / MN9 readout; taste benchmarks / feeding motor neurons |
| MN11V | 49829 | 492462351 | Traced | Traced | 1,907 | 373 | 5.11 | 1,624 | 207 | 7.85 | taste benchmarks / feeding motor neurons |

## Multi-cell types with side-mean input ratio > 3 (11)

| type | n L | n R | mean L | mean R | max/min | non-Traced |
|---|---|---|---|---|---|---|
| JO-unclear | 7 | 95 | 107 | 3 | 33.61 | 0 |
| MN11D | 1 | 2 | 546 | 12032 | 22.04 | 0 |
| JO-B-unclear | 2 | 11 | 0 | 9 | 18.91 | 0 |
| JO-A2 | 11 | 2 | 196 | 16 | 12.25 | 0 |
| JO-B1_b | 7 | 5 | 141 | 16 | 8.71 | 0 |
| JO-B1_a | 12 | 5 | 217 | 35 | 6.27 | 0 |
| JO-B4_b | 9 | 3 | 103 | 18 | 5.64 | 0 |
| JO-A1 | 4 | 4 | 100 | 19 | 5.32 | 0 |
| JO-B3 | 10 | 2 | 141 | 27 | 5.22 | 0 |
| JO-EV5 | 13 | 10 | 221 | 62 | 3.56 | 0 |
| JO-CM | 16 | 14 | 104 | 34 | 3.05 | 0 |

## Non-Traced benchmark cells (1), by type and status

| type | status | cells |
|---|---|---|
| L4 | <missing> | 1 |

Within-type outliers (cell input > 3x off its type+side median, groups of >= 3): 475 cells, see within_type_outliers.csv.

Files: status_table.csv, cells.csv (every benchmark cell), pairs.csv, types_by_side.csv, non_traced_cells.csv, within_type_outliers.csv, status_audit.json.
