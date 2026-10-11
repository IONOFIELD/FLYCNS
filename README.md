# flycns

[![regression](https://github.com/IONOFIELD/FLYCNS/actions/workflows/regression.yml/badge.svg)](https://github.com/IONOFIELD/FLYCNS/actions/workflows/regression.yml)

A simulation of the male fruit fly's entire nervous system, built from its complete wiring diagram
and checked against recordings from real flies.

## In one minute

Scientists have mapped every neuron and every connection in the male fruit fly's brain and nerve
cord. That map is a wiring diagram, and on its own it does nothing. flycns turns it on: signals run
through the wiring, and the result is checked against what real flies do.

**What it is for.** Experiments in software first. Stimulate a sense, silence a cell type or cut a
pathway, and see what changes. A run costs nothing but computer time, so a lab can test in real
flies only the predictions worth testing.

**Why do it.** A basic question in neuroscience is how much of what a nervous system does follows
from its wiring alone. No human brain can be mapped this way; it is far too large. The fly's is the
largest complete map there is, so it is where that question can be tested. This model answers it
circuit by circuit, including where the wiring alone is not enough.

**What is different.**
- **The whole central nervous system, not only the brain.** Brain and nerve cord, so a signal
  travels from a sense all the way to the motor neurons.
- **The male fly.** Circuits that differ between the sexes, such as courtship song, can be simulated.
- **Scored, not showcased.** For 25 of the 48 scored checks, the pass/fail criteria were committed
  to git before the test ran. Failures stay on the record next to the successes: at present 36 of
  48 checks pass, and of the 18 that count as independent tests of the model, 9 pass and 9 fail
  (`results/SUITE.md`). Checks guaranteed by a chosen value, or that only count over the wiring, are
  labelled as such and not counted as tests.
- **Built to be used and to last.** Every result is traceable to its code, data and settings, and
  automated checks run on every change.

**Headline result.** The model predicts that a sound makes the fly's escape neuron far more likely
to fire for a faint visual threat: from 18% to 53% of trials, with the criteria committed before
the test ran. Tootoonian et al. 2012 showed the same summation in real flies with an injected
current in place of the visual threat; sound plus a faint loom has not been recorded, so the 18%
and 53% are predictions a lab could test. The main caveat: the result is counted as *construction*,
not as an independent test. A rule parks the faint threat about 2 mV below threshold, and sound adds
a hand-set, untraced 3 mV, so in this model class summation is close to guaranteed. An earlier
fitting step also scored facilitation (see `docs/CALIBRATION.md`). Making this a real test means
modelling the sound pathway as the connectome annotates it; that is planned.

## What it is

- A computer model of the male fruit fly's brain and nerve cord, built from the Janelia MaleCNS connectome (2026). Of the 176,422 neurons in the MaleCNS table, the roughly 170,000 with at least one connection of five or more synapses are simulated, wired as the connectome maps them. The exceptions (connections under five synapses dropped, modulatory amine outputs removed, one mixed synapse modelled as electrical) are listed in RESULTS.md.
- Each neuron is a simple spiking unit. The connections come straight from the wiring diagram, including whether each one excites or inhibits.
- A test suite that scores each circuit against published measurements from real flies. The pass/fail criteria are written down before the test runs.

## What it can do

- **Stimulate a sense and watch the response.** Choose sight, sound, taste or the wing's motion sensors, and see which neurons fire and in what order, all the way to the motor neurons. You can watch it in the terminal or in 3D.
- **Test what the wiring alone can explain**, and show exactly where that explanation stops.
- **Make predictions a lab can test.** Each one names cell types and pathways and gives a specific expected result.
- **Show what a connectome uncertainty changes.** The companion paper's driver-line data disagree with the transmitter classifier on one taste neuron type, LB3d; the model shows that call decides whether salt promotes or suppresses feeding.
- **Score other fly models.** The same tests, run on another model, give a comparable score.
- **Export simulated recordings** in the format that brain-decoding machine-learning tools read.

## What it achieves

- **Escape reflex.** A looming shadow fires the giant escape neuron, which drives the jump motor neuron one spike for one spike, 0.9 ms later, as in the fly. This circuit was used to set the model's few tuned values, so it shows the model is set up correctly. It is not a prediction.
- **Sound and sight combined.** The model predicts that a sound makes the escape neuron far more likely to fire for a faint visual threat: 18% becomes 53%. Tootoonian et al. 2012 recorded the same summation with an injected current in place of the visual threat. The test was registered in advance, but it is counted as *construction*, not as an independent test. A rule places the faint threat within about 2 mV of threshold, and sound adds a hand-set 3 mV, so in a one-compartment model summation is close to guaranteed.
- **Courtship song.** The model reproduces which male-only neurons drive pulse song but not sine song, as experiments showed. It also predicts a new pathway for sine song that a lab could test.
- **Taste.** It shows which taste neurons push feeding up and which push it down, once each connection's sign (excite or inhibit) is counted.
- **Traceable.** Every result records the exact code, data and settings that produced it. Failures and corrections stay on the record.

## What it is not

- **Not a whole fly.** There is no body and no behavior, except a stand-in for flight.
- **Not complete.** Neuromodulators (chemicals such as dopamine that change how circuits behave), background activity and non-spiking neurons are missing. Circuits that depend on them fail, and those failures are reported.
- **Not tuned to look good.** The few values that were tuned are listed, and the checks they affect are not counted as tests.

## Install (Windows)

1. Open **PowerShell**: press the Windows key, type `PowerShell`, press Enter.
2. Install git and Python. You only need to do this once, and you can skip either one if you already have it. Paste:

       winget install -e --id Git.Git
       winget install -e --id Python.Python.3.12

3. Close PowerShell and open it again.
4. Download flycns and set it up. Paste:

       git clone https://github.com/IONOFIELD/FLYCNS.git flycns
       cd flycns
       .\setup.cmd

   Setup asks for your **neuPrint token**, a free key for downloading the fly's wiring:
   1. Sign in at [neuprint.janelia.org](https://neuprint.janelia.org) with Google.
   2. Click **Account** and copy the token.
   3. Paste it when setup asks.

   Setup then downloads the data, which takes about 5 minutes.
5. Run it:

       .\fly.cmd

   A menu opens. Type `4` and press Enter to run the main tests (about 40 minutes).

**Next time:** open PowerShell, then type `cd flycns` and `.\fly.cmd`.

- **Check the install without an account:** use `.\setup.cmd --check` in place of `.\setup.cmd`. It runs a self-test on a small practice network.
- **Faster runs:** setup offers to install the free Microsoft C++ Build Tools. Without them everything still works, about 4 times slower, with identical results.
- **Updating:** in the `flycns` folder, run `git pull`, then `.\setup.cmd`.

---

## More detail

### How results are scored

- Each circuit is tested against numbers from published recordings, with pass/fail criteria, null models (the same neurons with shuffled wiring) and ablations.
- Many tests are **pre-registered**: their criteria are committed to git before they run, so a result cannot be tuned after the fact.
- Every check is labelled with **what it is evidence of**. A check that a parameter was tuned to pass is marked *calibrated* and is not counted as a test of the model ([`docs/CALIBRATION.md`](docs/CALIBRATION.md)).
- **For the maintainer:** after an update, menu option **51** does four things. It updates the code, pins the data fingerprint, reruns the core suite and the stricter null, then commits and pushes the results. It keeps Windows awake while it runs, and it is safe to run again after an interruption.
- **Without your own computer:** push any commit to a branch named `rerun/<anything>` and GitHub's Windows machines run every real-data rerun at once: menu 51, the battery, the A2 and flight tests ([`.github/workflows/rerun.yml`](.github/workflows/rerun.yml)). It needs your neuPrint token saved once as the repository secret `NEUPRINT_TOKEN`. Add `--name+name` to the branch name to run only some, for example `rerun/2026-11-01--core+a2`. Each run fetches the connectome once (about 6 minutes) and refuses data that differ from `data/MANIFEST.json`. Each run's results come back on its own `rerun-out/...` branch for review; nothing reaches main unreviewed.

### Where this sits (2026)

| work | what it is | relation to this repository |
|---|---|---|
| Shiu et al. 2024, *Nature* | LIF model of the female adult brain (FlyWire, no nerve cord), with predictions tested by optogenetics | Source of the single-neuron parameters and synaptic weight |
| Lappalainen et al. 2024, *Nature* | Connectome-constrained network of the visual system, trained on a task, predicting responses across many cell types | Shows what fitting to a task adds; this repository fits nothing to its targets except where listed |
| NeuroMechFly v2 (Wang-Chen et al. 2024, *Nature Methods*) | Physics-simulated adult fly body for closed-loop control | The natural body for this model. The nerve cord is already here, so motor neurons could drive it directly |
| Eon Systems, 2026 (announced) | A FlyWire-based whole-brain emulation in a simulated body (company writeup, no peer-reviewed description) | Whole-fly emulation; female, brain-based |
| Jin et al. 2026, arXiv 2602.17997 | The fly connectome as a graph controller, trained by reinforcement learning for locomotion | Connectome as architecture rather than as a fixed circuit |

What this repository adds:
- the **male** central nervous system, **brain and nerve cord**, including sexually dimorphic circuits;
- every result **scored** against criteria written in advance, with null models, ablations and a stated role for each check;
- failures and retractions kept on the record (below).

**Corrections on the record** (details in RESULTS.md):
- An ipsilateral feeding bias (8 September) was an unsigned count; with sign it is contralateral.
- A regional SEZ gain of 2.0 was an artefact of naming the SEZ by cell type; the gain is retired.
- "Sound suppresses the escape response" was withdrawn; at 120 trials per arm sound facilitates it.
- The brainsets export could not be read by the real loader; it is now built and reloaded with it.
- GF adaptation of 15 mV was an undersampled fit (the current value is 10 mV, refit in October 2026).
- Escape is the calibration circuit, not a test. The escape and feeding reports committed in
  September came from a perturbed run.
- The loom input was all-trials, not stationary as documented. Every loom result was rerun.
- The two A2 arms differed in more than sound; with the difference removed the effect holds.
- "Mi1 stays silent under AstA": the peptide never acted. With it acting, Mi1 responds weakly.
- Flight robustness R1 never touched the circuit, R2 varied the stimulus, and R3 reused its draws.
  The fixed R2 now fails informatively.
- Tootoonian et al. 2012 used injected current, not a loom, and A2 was scored during two gain fits.
  A2 is now counted as construction, and five graph-count checks (three passes) as structural.

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
| Every file | Every result file carries the stamp of the run that wrote it, in the file or beside it (`<file>.stamp.json`). `results/SUITE.md` lists any file without a stamp, and flags any stamp whose model code has changed since (STALE). | `flycns/bench.py`, `benchmarks/summarize.py` |
| Data | The fetched tables are fingerprinted by content, so the fingerprint ignores row order and file format. The fingerprint is committed in `data/MANIFEST.json`. The suite and registered tests refuse to run on data that differ, and every report records the fingerprint it ran on. | `flycns/integrity.py`, `scripts/setup.py` |
| Settings | Any `FLYCNS_*` override prints a banner, is stamped into the report, and is flagged PERTURBED in `results/SUITE.md`. The robustness battery restores the canonical results when it finishes. | `flycns/integrity.py`, `scripts/overnight.py` |
| Evidence | Each check has a role: independent, control, robustness, structural, calibrated or construction. Only independent checks count as tests; structural checks count over the wiring without simulating it. CI fails if a check is unclassified. | `flycns/calibration.py`, `docs/CALIBRATION.md` |
| Stimuli | Every stimulus list is checked against the dataset before a long run, so a renamed cell type cannot silently drop an input. | `fit/audit_stimuli.py` |
| Registration | Pre-registered tests refuse to run against changed criteria. | each registered script |
| Environment | Python 3.12 with every package pinned (`requirements.lock`). The engine is compiled when the Microsoft C++ Build Tools are present and pure Python otherwise. Both give identical spikes, and every report records which engine ran. | `requirements.lock`, `flycns/windows.py` |
| Verification | On every push, CI runs on Windows: the unit checks and the whole toy suite in an isolated copy, on Python 3.12 and 3.13 with the pinned packages, on the oldest supported Python, and on the pure-Python engine. Every number the toy suite writes must equal a committed golden file (`tests/toy_expected.json`), so a model change that moves results cannot pass unnoticed; the toy carries every transmitter label, both ear partner types and an anatomical SEZ table. It also runs `setup.cmd` and `fly.cmd` exactly as a user would. A weekly run catches outside breakage. On the real connectome, the cloud rerun checks that both engines give identical spikes (`fit/check_engines.py`). | `tests/`, `.github/workflows/` |

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
| **Visual escape** (loom to giant fiber to jump muscle) | The **calibration circuit**. The loom's rate scale and the giant fiber's adaptation were set to give 1 to 2 spikes per response, and the relay is 1:1 by construction. On that calibration, the giant fiber fires with probability 0.58, and each spike drives the jump motor neuron one-to-one 0.9 ms later. The independent part is the latency (40 ms, inside 10 to 60 ms). The controls: the jump motor neuron does not respond without the electrical synapse, and nothing responds on shuffled wiring, including wiring shuffled within cell class. Holds under other seeds, stricter connection thresholds and inversion of the transmitter calls the classifier is unsure of. Its calibrated response probability falls out of range under random sign flips (2 of 3 runs), and its spike count or response probability under a ±0.05 change in the weight scale. |
| **Hearing to the giant fiber** | Sound alone stays subthreshold through the documented electrical synapse, which is calibrated. **Pre-registered, counted as construction** (the near-threshold working point and the 3 mV sound input make summation close to guaranteed): sound plus a near-threshold loom raises the giant fiber's response probability from 18% to 53% (re-measured October 2026 after the audit). This is the summation Tootoonian et al. 2012 recorded with injected current in place of the loom (the model's test: 120 trials per arm), and it holds at every working point tested (pre-registered sweep, five gains). |
| **Feeding** (taste to proboscis) | Does not reproduce feeding. The reason is measured, and the result holds when taste neurons are split by modality. |
| **Courtship song** (male-specific pC1 neurons to song command neurons) | Pre-registered, 3 of 3 independent checks pass, and the null control passes. Activating pC1_14a drives the pulse-song neuron and not the sine-song neuron, as optogenetics showed; shuffled wiring drives nothing. The companion paper's pC1_1b-to-sine link is not reproduced (registered check, fail). One male-specific type, SIP108m (4 cells, pIP5 class), drives the sine command neuron and not the pulse neuron, in a rule-chosen control arm. Seven further pIP5-class types are its strongest inputs by wiring but were not simulated. This is offered as a testable prediction; its novelty against the song literature has not been checked. |
| **Taste to feeding motor neurons** (signed map) | Counts over the wiring, not simulations (*structural* role). Appetitive taste neurons push proboscis extension up and bitter pushes it down (pre-registered: 1 of 3 checks pass; per-type sign agreement and LB2's dominance of pumping both fail). Of the 15 strongest unsigned influences on the proboscis motor neuron, 8 reverse to inhibitory once synaptic sign is included. Sugar neurons favour the opposite side's proboscis motor neuron, as Shiu et al. 2024 predicted, and this is visible only with sign. |
| **Flight** (wing sensors and command to flight motor neurons) | The afferent load was set so the upstroke motor neurons respond. The downstroke motor neurons, reached mainly through relay neurons, stay silent, which is an independent failure. One wing sensor type, SNpp16, drives the upstroke motor neurons selectively under the declared parameters (pre-registered). That selectivity replicates with fresh random draws but fails with faster cord membranes or a smaller threshold gap (registered robustness test). No classifier-uncertain neuron lies on its path. |

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
  - the connection-size threshold (5, 10 and 20 synapses; the data contain nothing below 5);
  - a stricter null that shuffles wiring only within cell class.
- **Measured input.** The visual stimulus uses amplitudes from the Turner et al. 2022 dataset (21 flies, 1,510 loom trials in all). The model uses the stationary-fly subset (13 of 23 imaging series), to match a simulation with no locomotion.

### Limitations

- **No background activity.** Neurons are silent at rest, so circuits that work by *removing* inhibition cannot be represented. Feeding and the visual ON pathway fail for this reason, and the flight relay layer stays silent for a related one. Peptide modulation is represented but unscored: AstA raises Mi1's flash response from near zero to 0.04 spikes per flash, far below the graded change Krieger 2023 reports.
- **Borrowed single-neuron parameters.** Every neuron uses central-brain values from Shiu et al. 2024. The escape relay survives every tested change to the cord neurons' parameters except one: with a 10 mV gap between rest and threshold it fails (TTMn/GF 0.23, lag 24.4 ms; cord sweep, rerun 11 October 2026). The SNpp16 flight result is sensitive to them.
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

- Berg S, et al., Jefferis GSXE. 2026. Sexual dimorphism in the complete *Drosophila* male central nervous system connectome. *Cell* 189:5504-5526. doi:10.1016/j.cell.2026.08.015
- Tastekin I, de Haan Vicente I, et al. 2026. The complete gustatory connectome of adult *Drosophila* reveals how taste guides feeding, foraging, and social behavior. *Cell* 189:5527-5551. doi:10.1016/j.cell.2026.08.016

The model and the principal physiology it is scored against:

- Shiu PK, Sterne GR, et al. 2024. A *Drosophila* computational brain model reveals sensorimotor processing. *Nature* 634:210-219. doi:10.1038/s41586-024-07763-9
- Turner MH, Krieger A, Pang MM, Clandinin TR 2022. Visual and motor signatures of locomotion dynamically shape a population code for feature detection in *Drosophila*. *eLife* 11:e82587
- von Reyn CR, Breads P, Peek MY, et al. 2014. A spike-timing mechanism for action selection. *Nat Neurosci* 17:962-970
- Tanouye MA, Wyman RJ 1980. Motor outputs of giant nerve fiber in *Drosophila*. *J Neurophysiol* 44:405-421
- Eckstein N, Bates AS, Champion A, et al. 2024. Neurotransmitter classification from electron microscopy images at synaptic sites in *Drosophila melanogaster*. *Cell* 187:2574-2594

Every other source, with the specific number taken from it, is in [`REFERENCES.md`](REFERENCES.md).
