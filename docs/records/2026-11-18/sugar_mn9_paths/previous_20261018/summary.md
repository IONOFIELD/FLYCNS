# Sugar → MN9 paths on the pinned data (exploratory)

Exploratory and read-only. It goes into no score. Nothing tracked was edited, committed or pushed.

**Setup.** Repo at `gen6/phaseA-decisions` c1e6e62. Data are the pinned `data/edges.parquet` (sha256 61f8c2ed…) and
`neurons.parquet` (b60448d9…), and both match `data/MANIFEST.json`. The graph comes from `flycns.graph.load_graph("data")`
with the default floor of 5 synapses, signs from SIGN_MAP and amines dropped. That gives 176,422 neurons and 6,127,738
signed edges; 160,051 unsigned edges are dropped. The sources are every LB3b and LB3c cell, which is phase A's sugar
drive: 34 cells (23 LB3c, 11 LB3b; 17 L, 17 R). The targets are MN9_L 10331 and MN9_R 16949. The mirror is
`fit/gen6_phaseA.py:mirror_mn9`.

**Definitions.**
- A cell is at **hop h** if its shortest directed path to the MN9 cell has h edges.
- **On a sugar path** means: hops from the nearest sugar cell + hops to MN9 ≤ 4.
- **Input at hop h** is the signed synapses on edges from hop-h cells to hop-(h−1) cells, where hop 0 is MN9.
- **Normalised weight** is synapses ÷ the postsynaptic cell's total signed input.
- **Path score** is the product of the normalised weights along the path.

The top-10 search is exact: a best-first search over simple paths of 1–4 hops. Full detail is in `paths.json`.

## In plain words

**Sugar does not reach MN9 directly.** No LB3b or LB3c cell synapses onto either MN9.

**The shortest route is 2 hops, and it is negligible.** For MN9_L, four of its partners take input straight from sugar
cells: GNG089_L (excitatory, 7 synapses) and GNG043_L, GNG043_R and DNge031_L (inhibitory, 5 each). Together they give MN9_L 22 of its
5,651 synapses (0.4%): 7 excitatory and 15 inhibitory, so they push net inhibitory. The best 2-hop path scores
1.2e-5 (LB3b_L → GNG089_L → MN9_L, with only 7 synapses on the last step).

**The real route is 3 hops, and every single chain is weak.** About 94% of MN9_L's input comes from cells that are
exactly two synapses downstream of sugar. So in that sense sugar "reaches" almost everything MN9 hears. But that
two-synapse cone is wide (1,154 cells at hop 2 lie on a sugar path) and nearly balanced:

| hop | MN9_L input on sugar paths, excitatory / inhibitory |
|---|---|
| 1 | +2,805 / −2,846 (net −41) |
| 2 | +85,555 / −82,457 |
| 3 | +12,368 / −9,327 |

The strongest individual chains score about 2–3e-5. A typical one is roughly a 7% share, then a 1% share, then a 6%
share. They run through:
- GNG232 or GNG215 → GNG108
- GNG232 → DNge080
- LB3b → ANXXX462b or GNG197 → DNge062

All of those are excitatory, which makes them the candidate feeding routes. GNG132 → GNG130 is a strong inhibitory
route. Six of MN9_L's top 10 paths are excitatory and four are inhibitory.

**So: sugar reaches MN9 only through 3-hop chains, each weak, with excitation and inhibition close to cancelling in the
wiring.** The wiring alone cannot say which side wins. That depends on the dynamics.

**L and R differ in MN9_R's own input, not in the sugar circuitry upstream of it.**

| | MN9_L | MN9_R as reconstructed | MN9_R mirrored |
|---|---|---|---|
| input synapses | 5,651 | 364 (6%) | 5,651 |
| partners | 93 | 25 | 100 |
| shortest path from sugar | 2 hops | 3 hops | 2 hops |
| partners 1 hop from sugar | 4 | 0 | 4 |

- **As reconstructed**, MN9_R has no partner one hop from sugar. Its strongest chains use the same interneuron types as
  MN9_L's (GNG232/GNG215 → GNG108, GNG232 → DNge080, GNG132 → GNG130, LB3b → DNge062), but they land on MN9_R with far
  fewer synapses: GNG108_L → MN9_R has 25, against 348 for GNG108_R → MN9_L.
- **The normalised scores look higher on R** (best 4.7e-5) only because they divide by MN9_R's small total input. They
  do not mean R is driven more strongly.
- **With the mirror**, MN9_R reproduces MN9_L's picture: shortest path 2 hops; the same 22-synapse, net-inhibitory
  2-hop route (GNG089_R, GNG043); layer counts within a few percent of L's; and top paths of the same types with the
  sides swapped. Eight of its top 10 are excitatory.

**A layout note.** On both sides the heavy GNG108 input comes from the GNG108 on the other side: GNG108_R feeds MN9_L,
and GNG108_L feeds MN9_R.

## Per-hop numbers

| target | hop | cells upstream | on a sugar path | sugar cells at this hop | input on sugar path (exc / inh) | all input at this hop (exc / inh) |
|---|---|---|---|---|---|---|
| MN9_L | 1 | 93 | 93 | 0 | +2,805 / −2,846 | +2,805 / −2,846 |
| | 2 | 2,970 | 1,154 | 13 | +85,555 / −82,457 | +141,571 / −113,228 |
| | 3 | 36,361 | 66 | 21 | +12,368 / −9,327 | +2,297,521 / −1,332,125 |
| | 4 | 92,492 | 0 | 0 | 0 / 0 | +6,892,392 / −3,053,109 |
| MN9_R | 1 | 25 | 25 | 0 | +161 / −203 | +161 / −203 |
| | 2 | 1,011 | 563 | 0 | +34,177 / −33,879 | +43,459 / −39,652 |
| | 3 | 19,747 | 116 | 34 | +22,755 / −7,735 | +973,825 / −556,946 |
| | 4 | 89,632 | 0 | 0 | 0 / 0 | +6,525,835 / −3,327,200 |
| MN9_R mirrored | 1 | 100 | 99 | 0 | +2,805 / −2,838.5 | +2,805 / −2,846 |
| | 2 | 3,032 | 1,147 | 17 | +89,059 / −85,464 | +148,661 / −118,830 |
| | 3 | 35,952 | 60 | 17 | +13,329 / −8,317 | +2,242,872 / −1,292,187 |
| | 4 | 91,537 | 0 | 0 | 0 / 0 | +6,805,591 / −3,014,963 |

Hop 4 has no cell on a sugar path by construction. Every sugar cell is within 3 hops of MN9, so a hop-4 cell would
itself have to be a sugar cell.

## Caveats

This is structure only: synapse counts and transmitter signs, with no dynamics. Unknown-transmitter edges and amines
are dropped, as in the model. The mirror's split weights stay fractional, as `mirror_mn9` writes them. The path score
ranks single chains; it is not a measure of total drive.
