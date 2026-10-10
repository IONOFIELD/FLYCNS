# flycns

[![regression](https://github.com/IONOFIELD/FLYCNS/actions/workflows/regression.yml/badge.svg)](https://github.com/IONOFIELD/FLYCNS/actions/workflows/regression.yml)

A spiking simulation of the complete male fruit fly nervous system, built from its wiring diagram,
tested against published physiology, and built so that every result can be traced to the exact
code, data and settings that produced it.

---

## Quick start

Needs macOS or Linux, Python 3.12 (3.10 or newer works, unpinned), and a C compiler
(macOS: `xcode-select --install`). These are **Terminal** commands. Windows PowerShell and cmd cannot
run them. On Windows, use WSL (Ubuntu) or the Docker route below.

    git clone https://github.com/IONOFIELD/FLYCNS.git flycns && cd flycns
    ./setup.sh --check                          # installs, runs the regression test: no account, ~10 min
    echo "YOUR_TOKEN" > ~/.neuprint_token       # free at neuprint.janelia.org, under Account
    ./setup.sh                                  # downloads the connectome, checks it against data/MANIFEST.json
    ./fly                                       # menu: choose 4 to run the core suite, ~40 min

`--check` alone is enough to confirm everything installs and runs. Rerunning `./setup.sh` is safe;
it skips the download if the connectome is already there.

After an update, **one command** brings everything up to date on the computer that holds the
connectome. It updates the code, pins the data, reruns the core suite and the stricter null, then
commits and pushes. It is safe to run again after an interruption, and it is also menu option **51**.

    git stash; git pull; scripts/canonical_rerun.sh       # about 1 to 1.5 h; keeps a Mac awake

With Docker instead, using the frozen reference environment:

    docker build -t flycns . && docker run --rm flycns          # regression test
    docker run --rm -it -v "$PWD":/flycns flycns ./fly          # the menu, on your own checkout and data

---

## What it is

Every neuron in the male fly's brain and nerve cord is simulated as a simple spiking unit, wired
exactly as the MaleCNS v1.0 connectome (Janelia FlyEM, 2026) says. Stimulate a sense organ and
watch which neurons fire and in what order. The downloaded connectome has 176,422 neurons and 6.1
million signed connections.

What makes it more than a simulation is that it is **scored**:
- Each circuit is tested against numbers from published recordings, with pass/fail criteria, null models (the same neurons with shuffled wiring) and ablations.
- Many tests are **pre-registered**: their criteria are committed to git before they run, so a result cannot be tuned after the fact.
- Every check is labelled with **what it is evidence of**. A check that a parameter was tuned to pass is marked *calibrated* and is not counted as a test of the model ([`docs/CALIBRATION.md`](docs/CALIBRATION.md)).

### What it is not

- **Not a model of how a fly behaves.** There is no body, except a minimal stand-in for flight.
- **Not fitted to neural recordings.** The single-neuron parameters come from published values, and the visual stimulus is measured from real imaging. A few values were chosen to make specific checks pass. They are listed, with their rules, in `docs/CALIBRATION.md`, and those checks are not counted as tests.
- **Not a complete account of the fly.** Neuromodulators, graded (non-spiking) neurons and spontaneous background activity are absent, and several circuits fail for exactly that reason.

### What it can be used for

- **Asking what the wiring alone can explain**, and seeing exactly where it stops.
- **Generating predictions an experimenter can test**: named cell types and pathways with a specific expected result.
- **Checking the connectome itself.** The simulation has exposed annotation issues, including a likely transmitter misclassification.
- **Benchmarking other fly models.** The same tests, run on another model, give a comparable score.

### Where this sits (2026)

| work | what it is | relation to this repository |
|---|---|---|
| Shiu et al. 2024, *Nature* | LIF model of the female adult brain (FlyWire, no nerve cord), with predictions tested by optogenetics | Source of the single-neuron parameters and synaptic weight |
| Lappalainen et al. 2024, *Nature* | Connectome-constrained network of the visual system, trained on a task, predicting responses across many cell types | Shows what fitting to a task adds; this repository fits nothing to its targets except where listed |
| NeuroMechFly v2 (Wang-Chen et al. 2024, *Nature Methods*) | Physics-simulated adult fly body for closed-loop control | The natural body for this model. The nerve cord is already here, so motor neurons could drive it directly |
| Eon Systems, 2026 (announced) | A FlyWire-based whole-brain emulation driving NeuroMechFly | Whole-fly emulation; female, brain-based |
| Jin et al. 2026, arXiv 2602.17997 | The fly connectome as a graph controller, trained by reinforcement learning for locomotion | Connectome as architecture rather than as a fixed circuit |

What this repository adds:
- the **male** central nervous system, **brain and nerve cord**, including sexually dimorphic circuits;
- every result **scored** against criteria written in advance, with null models, ablations and a stated role for each check;
- failures and retractions kept on the record.

---

## The system

### How it is built

    connectome (neuprint)  ->  signed graph  ->  spiking model (Brian2)  ->  benchmarks  ->  scored report
                               flycns/graph.py    flycns/model.py           benchmarks/     results/

- **Signed graph.** Each connection's sign comes from the connectome's predicted transmitter of the sending neuron: acetylcholine excites; GABA, glutamate and histamine inhibit; modulatory amines are left out. A few documented electrical synapses are added, each with a citation.
- **Spiking model.** Leaky integrate-and-fire units with the parameters of Shiu et al. 2024, and one parameter set for every circuit. The full model is written out as plain mathematics, independent of any simulator, in [`docs/MODEL_SPEC.md`](docs/MODEL_SPEC.md).
- **Benchmarks.** Each is a script that drives a stimulus, reads out named neurons, and scores the result against criteria written in its header.

### Integrity: the steel box

Every result has to answer four questions: which code, which data, which settings, and what it is evidence of.

| guard | what it does | where |
|---|---|---|
| Code | Every report records the commit and whether any code differed from it. Registered tests refuse to run on uncommitted code. | `flycns/integrity.py` |
| Data | The fetched tables are fingerprinted by content, so the fingerprint ignores row order and file format. The fingerprint is committed in `data/MANIFEST.json`. The suite and registered tests refuse to run on data that differ, and every report records the fingerprint it ran on. | `flycns/integrity.py`, `setup.sh` |
| Settings | Any `FLYCNS_*` override prints a banner, is stamped into the report, and is flagged PERTURBED in `results/SUITE.md`. The robustness battery restores the canonical results when it finishes. | `flycns/integrity.py`, `scripts/overnight.sh` |
| Evidence | Each check has a role: independent, control, robustness, calibrated or construction. Only independent checks count as tests. CI fails if a check is unclassified. | `flycns/calibration.py`, `docs/CALIBRATION.md` |
| Stimuli | Every stimulus list is checked against the dataset before a long run, so a renamed cell type cannot silently drop an input. | `fit/audit_stimuli.py` |
| Registration | Pre-registered tests refuse to run against changed criteria. | each registered script |
| Environment | Python 3.12 with every package pinned (`requirements.lock`), and a Dockerfile that freezes it. | `requirements.lock`, `Dockerfile` |
| Verification | On every push, CI runs the unit checks and the whole toy suite in an isolated copy on Linux and macOS. It also tests the pinned environment on Python 3.12 and 3.13, the oldest supported Python, and the container. A weekly run catches outside breakage. | `tests/`, `.github/workflows/` |

`python -m flycns.integrity status` (menu **49**) shows all three run states at once: code, settings and data.
The house rules are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

### The menu

| group | options | what they do |
|---|---|---|
| Setup | 1 to 3, 45 | download the connectome, sensory and sex-related annotations; show status |
| Benchmarks | 4 to 7 | run the core suite or one circuit; summary; overnight robustness battery |
| Checks | 28, 35, 36, 46, 49 to 51 | stimulus audit; parameter sensitivity; regression test; integrity status; stricter null; one-command canonical rerun |
| Fits | 8 to 10, 26 | the fits and sweeps behind each declared value |
| Recorded data | 21, 22 | fetch the Turner et al. 2022 imaging data; extract measured loom tuning |
| Connectome detail | 23 to 25 | per-synapse transmitter confidence; neuropil membership |
| Feeding | 27, 31, 40 to 42 | why feeding fails; modulator audit; re-test by taste modality; signed taste map; sugar laterality |
| Social and auditory | 43, 44, 47, 48 | pC1 song; DNp13 positive control; sound-loom facilitation and its robustness sweep |
| Flight | 33, 34, 37 to 39 | surrogate-body flight loop; the SNpp16 tests |
| Traces | 29, 30, 32 | pathway traces that are findings rather than benchmarks |
| Explore | 11 to 16 | stimulate anything and watch; terminal and 3D views of cascades and neurons |
| Export | 20 | simulated sessions as temporaldata files, verified to reload with the loader brainsets and POYO+ use |
| Docs | 17 to 19 | results note, references, provenance of the last run |

### Results at a glance

| circuit | outcome |
|---|---|
| **Visual escape** (loom to giant fiber to jump muscle) | The **calibration circuit**. The loom's rate scale and the giant fiber's adaptation were set to give 1 to 2 spikes per response, and the relay is 1:1 by construction. On that calibration, the giant fiber fires with probability 0.68, and each spike drives the jump motor neuron one-to-one 0.9 ms later. The independent part is the latency (37 ms, inside 10 to 60 ms). The controls are no response without the electrical synapse and none on shuffled wiring. Holds when uncertain transmitter calls are inverted and across nerve-cord parameters. |
| **Hearing to the giant fiber** | Sound alone stays subthreshold through the documented electrical synapse, which is calibrated. **Independent and pre-registered:** sound plus a near-threshold loom raises the giant fiber's response probability from 4% to 45%. This is the facilitation Tootoonian et al. 2012 recorded (120 trials per arm), and it holds at every near-threshold working point tested (pre-registered sweep). |
| **Feeding** (taste to proboscis) | Does not reproduce feeding. The reason is measured, and the result holds when taste neurons are split by modality. |
| **Courtship song** (male-specific pC1 neurons to song command neurons) | Pre-registered, 3 of 3 independent checks pass, and the null control passes. Activating pC1_14a drives the pulse-song neuron and not the sine-song neuron, as optogenetics showed; shuffled wiring drives nothing. A separate pathway of male-specific pIP5 neurons drives the sine neuron and not the pulse neuron, which is a new prediction. Signed paths also predict the song suppression the model cannot simulate. |
| **Taste to feeding motor neurons** (signed map) | Appetitive taste neurons push proboscis extension up and bitter pushes it down (pre-registered pass). Of the 15 strongest unsigned influences on the proboscis motor neuron, 8 reverse to inhibitory once synaptic sign is included. Sugar neurons favour the opposite side's proboscis motor neuron, as Shiu et al. 2024 predicted, and this is visible only with sign. |
| **Flight** (wing sensors and command to flight muscles) | The afferent load was set so the upstroke muscles respond. The downstroke muscles, reached mainly through relay neurons, stay silent, which is an independent failure. One wing sensor type, SNpp16, drives the upstroke muscles selectively under the declared parameters (pre-registered). |

`results/SUITE.md` lists every check with its result, role and flags. Full numbers, every failure
and every retraction are in [`RESULTS.md`](RESULTS.md).

---

## Limitations and verification of values

### How values are verified

- **Every parameter is cited or chosen by a stated rule.** Chosen values, their rules and the checks they touch are in `docs/CALIBRATION.md`. When a value changed, the reason is kept in the code.
- **Pre-registration.** Scored tests on new claims commit their criteria before running. A criteria file stamped with that commit proves the order, and the test refuses to run on uncommitted code. Failures are reported as failures.
- **Robustness.** A twelve-suite battery covers:
  - random seeds;
  - random and targeted transmitter-sign inversion. The targeted inversion flips every neuron whose own synapses disagree with its transmitter label, and no scored result depends on those calls;
  - the connection-strength scale;
  - the connection-size threshold (3, 5 and 10 synapses);
  - a stricter null that shuffles wiring only within cell class.
- **Measured input.** The visual stimulus uses amplitudes extracted from 1,510 recorded trials across 21 flies (Turner et al. 2022). Only the trials in which the fly was not walking are used, to match a simulation with no locomotion.

### Limitations

- **No background activity.** Neurons are silent at rest, so circuits that work by *removing* inhibition cannot be represented. Feeding, the visual ON pathway and peptide modulation fail for this reason, and the flight relay layer stays silent for a related one.
- **Borrowed single-neuron parameters.** Every neuron uses central-brain values from Shiu et al. 2024. The escape result is insensitive to them; the SNpp16 flight result is not.
- **Transmitters come from a classifier.** It is less reliable for modulatory neurons (Eckstein et al. 2024) and appears to misclassify at least one taste neuron type, LB3d. Its call on LB3d decides whether the model treats aversive salt as promoting or suppressing feeding.
- **Spiking only.** Neurons that signal with graded potentials, common in early vision and hearing, are forced to spike.
- **Some drives are cross-species.** Wing and haltere sensor parameters come from larger flies.
- **The escape circuit is calibrated, not predicted.** See above and `docs/CALIBRATION.md`. The held-out results are the circuits nothing was fitted to.
- **One calibration value is untraced.** The ear-to-giant-fiber synapse is mixed electrical and chemical (Pézier et al. 2014). The model represents it as electrical only, tuned to a 3 mV subthreshold potential whose source figure has not yet been confirmed. The checks score subthreshold behaviour, not the number.

---

## Citing and license

Code: BSD 3-Clause ([`LICENSE`](LICENSE)). GitHub's "Cite this repository" button uses
[`CITATION.cff`](CITATION.cff). Please also cite the connectome.

The connectome, and the paper that assigns taste modality to it:

- FlyEM Project Team et al. 2026. Sexual dimorphism in the complete connectome of the *Drosophila* male central nervous system. *Cell*. doi:10.1016/j.cell.2026.08.015
- Tastekin I, de Haan Vicente I, et al. 2026. The complete gustatory connectome of adult *Drosophila* reveals how taste guides feeding, foraging, and social behavior. *Cell* 189:5527-5551. doi:10.1016/j.cell.2026.08.016

The model and the principal physiology it is scored against:

- Shiu PK, Sterne GR, et al. 2024. A *Drosophila* computational brain model reveals sensorimotor processing. *Nature* 634:210-219. doi:10.1038/s41586-024-07763-9
- Turner MH, Krieger A, Pang MM, Clandinin TR 2022. Visual and motor signatures of locomotion dynamically shape a population code for feature detection in *Drosophila*. *eLife* 11:e82587
- von Reyn CR, Breads P, Peek MY, et al. 2014. A spike-timing mechanism for action selection. *Nat Neurosci* 17:962-970
- Tanouye MA, Wyman RJ 1980. Motor outputs of giant nerve fiber in *Drosophila*. *J Neurophysiol* 44:405-421
- Eckstein N, Bates AS, Champion A, et al. 2024. Neurotransmitter classification from electron microscopy images at synaptic sites in *Drosophila melanogaster*. *Cell* 187:2574-2594

Every other source, with the specific number taken from it, is in [`REFERENCES.md`](REFERENCES.md).
