# flycns

A spiking simulation of the complete male fruit fly nervous system, built from its wiring diagram
and tested against published physiology.

---

## Install

macOS or Linux, Python 3.10 or newer, and a few gigabytes of free disk.

    git clone https://github.com/IONOFIELD/FLYCNS.git flycns && cd flycns
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    echo "PASTE_YOUR_NEUPRINT_TOKEN" > ~/.neuprint_token     # neuprint.janelia.org -> Account
    ./fly

`./fly` opens the menu. The first time, choose **1** (download the connectome, about 5 minutes),
**2** (sensory annotations), then **4** (run the benchmark suite, about 40 minutes). To launch from
anywhere, add `alias flycns=~/flycns/fly` to your shell profile.

---

## What it is

Every neuron in the male fly's brain and nerve cord, wired exactly as the MaleCNS v1.0 connectome
(Janelia FlyEM, 2026) says, simulated as a simple spiking unit. Stimulate a sense organ and watch
which neurons fire and in what order. The downloaded connectome has 176,422 neurons and 6.1 million
signed connections.

What makes it more than a simulation is that it is **scored**. Each circuit is tested against
numbers from published recordings, with pass/fail criteria, null models (the same neurons with
shuffled wiring) and ablations. Many tests are pre-registered: their criteria are committed to git
before they run, so a result cannot be tuned after the fact.

### What it is not

- **Not a model of how a fly behaves.** There is no body, except a minimal stand-in for flight.
- **Not fitted to neural recordings.** The single-neuron parameters come from published values; only
  the stimulus is measured from real data.
- **Not a complete account of the fly.** Neuromodulators, graded (non-spiking) neurons and
  spontaneous background activity are absent, and several circuits fail for exactly that reason.

### What it can be used for

- **Asking what the wiring alone can explain**, and seeing exactly where it stops.
- **Generating predictions an experimenter can test**: named cell types and pathways with a
  specific expected result.
- **Checking the connectome itself.** The simulation has exposed annotation issues, including a
  likely transmitter misclassification.
- **Benchmarking other fly models.** The same tests, run on another model, give a comparable score.

---

## The system

### How it is built

    connectome (neuprint)  ->  signed graph  ->  spiking model (Brian2)  ->  benchmarks  ->  scored report
                               flycns/graph.py    flycns/model.py           benchmarks/     results/

- **Signed graph.** Each connection's sign comes from the connectome's predicted transmitter of the
  sending neuron: acetylcholine excites, GABA, glutamate and histamine inhibit, modulatory amines are
  left out. A few documented electrical synapses are added, each with a citation.
- **Spiking model.** Leaky integrate-and-fire units with the parameters of Shiu et al. 2024. One
  parameter set is used for every circuit, and there are no fitted gains.
- **Benchmarks.** Each is a script that drives a stimulus, reads out named neurons, and scores the
  result against criteria written in its header.
- **Guards.** Every stimulus list is checked against the dataset before a long run starts, reports
  record the commit and settings that produced them, and pre-registered tests refuse to run against
  changed criteria.

### The menu

| group | options | what they do |
|---|---|---|
| Setup | 1 to 3 | download the connectome and annotations; show status |
| Benchmarks | 4 to 7 | run the suite or one circuit; summary; overnight robustness battery |
| Checks | 28, 35, 36 | audit every stimulus set; test sensitivity to inherited parameters |
| Fits | 8 to 10, 26 | the fits and sweeps behind each declared value |
| Recorded data | 21, 22 | fetch the Turner et al. 2022 imaging data; extract measured loom tuning |
| Connectome detail | 23 to 25 | per-synapse transmitter confidence; neuropil membership |
| Feeding | 27, 31, 40, 41 | why feeding fails; modulator audit; re-test by taste modality; signed taste map |
| Flight | 33, 34, 37 to 39 | surrogate-body flight loop; the SNpp16 tests |
| Traces | 29, 30, 32 | pathway traces that are findings rather than benchmarks |
| Explore | 11 to 16 | stimulate anything and watch; terminal and 3D views of cascades and neurons |
| Export | 20 | simulated sessions in a format machine-learning decoders can read |
| Docs | 17 to 19 | results note, references, provenance of the last run |

### Results at a glance

| circuit | outcome |
|---|---|
| **Visual escape** (loom to giant fiber to jump muscle) | Passes 8 of 8. The giant fiber fires 1.06 spikes per response with probability 0.68, and each spike drives the jump motor neuron one-to-one 0.9 ms later. Holds when uncertain transmitter calls are inverted and across nerve-cord parameters. |
| **Hearing to the giant fiber** | Passes 4 of 4. Sound alone stays subthreshold, as recorded, through the documented electrical synapse. |
| **Feeding** (taste to proboscis) | Does not reproduce feeding. The reason is measured, and the result holds when taste neurons are split by modality. |
| **Flight** (wing sensors and command to flight muscles) | The upstroke muscles respond; the downstroke muscles, reached mainly through relay neurons, stay silent. One wing sensor type, SNpp16, drives the upstroke muscles selectively under the declared parameters (pre-registered). |

Full numbers, every failure, and every retraction are in [`RESULTS.md`](RESULTS.md).

---

## Limitations and verification of values

### How values are verified

- **Every parameter is cited or fitted by a stated rule.** Fitted values record the rule and the
  sweep that produced them, and when a value changed, the reason is kept in the code.
- **Pre-registration.** Scored tests on new claims commit their criteria before running, and a
  criteria file stamped with that commit proves the order. Failures are reported as failures.
- **Robustness.** A nine-suite battery covers random seeds, random and targeted transmitter-sign
  inversion, and the connection-strength scale. The targeted inversion flips every neuron whose own
  synapses disagree with its transmitter label, and no scored result depends on those calls.
- **Measured input.** The visual stimulus uses amplitudes extracted from 1,510 recorded trials across
  21 flies (Turner et al. 2022), taken from the trials in which the fly was not walking, to match a
  simulation with no locomotion.

### Limitations

- **No background activity.** Neurons are silent at rest, so circuits that work by *removing*
  inhibition cannot be represented. Feeding, the visual ON pathway and peptide modulation fail for
  this reason, and the flight relay layer stays silent for a related one.
- **Borrowed single-neuron parameters.** Every neuron uses central-brain values from Shiu et al.
  2024. The escape result is insensitive to them; the SNpp16 flight result is not.
- **Transmitters come from a classifier**, which is less reliable for modulatory neurons (Eckstein
  et al. 2024) and appears to misclassify at least one taste neuron type.
- **Spiking only.** Neurons that signal with graded potentials, common in early vision and hearing,
  are forced to spike.
- **Some drives are cross-species.** Wing and haltere sensor parameters come from larger flies.
- **One calibration value is untraced.** The ear-to-giant-fiber synapse is mixed electrical and
  chemical (Pézier et al. 2014); the model represents it as electrical only, tuned to a 3 mV
  subthreshold potential whose source figure has not yet been confirmed. The checks score
  subthreshold behaviour, not the number.

---

## Citations

The connectome, and the paper that assigns taste modality to it:

- FlyEM Project Team et al. 2026. Sexual dimorphism in the complete connectome of the *Drosophila*
  male central nervous system. *Cell*. doi:10.1016/j.cell.2026.08.015
- Tastekin I, de Haan Vicente I, et al. 2026. The complete gustatory connectome of adult *Drosophila*
  reveals how taste guides feeding, foraging, and social behavior. *Cell* 189:5527-5551.
  doi:10.1016/j.cell.2026.08.016

The model and the principal physiology it is scored against:

- Shiu PK, Sterne GR, et al. 2024. A *Drosophila* computational brain model reveals sensorimotor
  processing. *Nature* 634:210-219. doi:10.1038/s41586-024-07763-9
- Turner MH, Krieger A, Pang MM, Clandinin TR 2022. Visual and motor signatures of locomotion
  dynamically shape a population code for feature detection in *Drosophila*. *eLife* 11:e82587
- von Reyn CR, Breads P, Peek MY, et al. 2014. A spike-timing mechanism for action selection.
  *Nat Neurosci* 17:962-970
- Tanouye MA, Wyman RJ 1980. Motor outputs of giant nerve fiber in *Drosophila*. *J Neurophysiol*
  44:405-421
- Eckstein N, Bates AS, Champion A, et al. 2024. Neurotransmitter classification from electron
  microscopy images at synaptic sites in *Drosophila melanogaster*. *Cell* 187:2574-2594

Every other source, with the specific number taken from it, is in
[`REFERENCES.md`](REFERENCES.md).
