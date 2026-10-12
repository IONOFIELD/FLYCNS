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
- **Scored, not showcased.** Every one of the 53 scored checks was registered against a frozen model,
  and its registration committed, before the run that scored it: the criteria with their numbers,
  and a hash of every model file. Each check carries a 95% interval, a score per random draw, or a
  percentile against shuffled wiring; checks that only count over the wiring are scored on their
  value. A check passes only if its whole interval, or the required share of draws, lies inside its
  band. Failures stay on the record next to the successes: at present 29 of
  53 checks pass and 6 are unresolved. Of the 19 that count as independent tests of the model,
  5 pass, 11 fail and 3 are unresolved (`results/SUITE.md`). Checks guaranteed by a chosen value, or
  that only count over the wiring, are labelled as such and not counted as tests.
- **Built to be used and to last.** Every result is traceable to its code, data and settings, and
  automated checks run on every change.

**Headline result, after the refrozen model's registered rerun (generation 3, 12 October 2026).** The
result that used to lead this page does not survive. With each escape neuron's sound input
calibrated on its own ear afferents (before, one side got several times the other's), a sound
makes the escape neuron LESS likely to fire for a faint visual threat (from 30% to 17% of trials): the
network's polysynaptic inhibition outweighs the calibrated ear contact. Across the robustness
registered sweep the suppression grows with the strength of the visual threat (up to 80% → 41% of
trials) and is unresolved only right at threshold, where the facilitation used to be. With the ear-to-escape contact modelled as the connectome annotates it, sound alone
fires the escape neuron on every trial, which recordings do not show. (That outcome could be seen in an
earlier reference run before the test was registered, so it is not a blind prediction.)

One result holds as registered, and a second in part:
- **Escape needs its specific wiring.** This is a control, not a test of a prediction. Shuffle the
  connectome while keeping each cell's class, neuropil and input strength, and the network stays as
  active as the real one. Yet in 20 such shuffles the escape neuron never responds as often as with
  the real wiring.
- **One wing sensor selectively drives the upstroke motor neurons,** at a working point chosen by a
  pre-registered rule from the same sweep (SNpp16, G3). This one now holds only in part: at the rule's
  working point it reaches the 2 to 12 Hz band in only 1 of 5 random draws (was 4 of 5; reliability
  test G5 fails), and it fails its fresh-draw replication. Its registered transmitter-uncertainty test
  fails too, but because its fixed size now overshoots the band with or without the flips, not
  because of a transmitter call. It still fails with faster nerve-cord membranes, as before.

Most independent checks fail or are unresolved (`results/SUITE.md`, RESULTS.md).

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
- **Sound and sight combined.** Not reproduced. Tootoonian et al. 2012 recorded summation of a sound input with an injected current in place of a visual threat; the model was expected to show it (counted as *construction*: a rule places the faint threat near threshold and sound adds a hand-set potential). With each escape neuron's hand-set sound input now calibrated on its own afferents (the earlier calibration gave them 3.7 and 0.7 mV against 3 mV intended), a sound makes the escape neuron less likely to fire for a faint visual threat: 30% becomes 17% (120 trials per arm). Sound alone gives a small early depolarisation and then deep inhibition through the network, which outweighs the hand-set input. With the ear-to-escape contact as the connectome annotates it, sound alone fires the escape neuron on every trial, which recordings do not show (an outcome visible in an earlier reference run before that test was registered).
- **Courtship song.** Activating the male-only pC1_14a neurons drives the pulse-song command neuron, as optogenetics showed, and more than other pC1 groups do. Whether they drive pulse *rather than* sine song cannot be tested here: the sine command neuron fires in no condition at all (unresolved). The companion paper's pC1_1b-to-sine link is not reproduced (registered check, fail). One male-specific type, SIP108m (4 cells, pIP5 class), drives the sine command neuron and not the pulse neuron in a rule-chosen control arm: a testable prediction, not yet checked for novelty.
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

## Install (Linux and macOS)

The Windows files (`setup.cmd`, `fly.cmd`) are thin launchers; the work is done by `scripts/setup.py` and
`fly.py`, which run on Linux and macOS too. **Tested on Linux** (Python 3.13, 12 October 2026: a fresh
clone passes `python3 scripts/setup.py --check`, the whole toy regression, 87 of 87). **Not yet tested on
macOS.** You need git, Python 3.10 to 3.13, and for the faster compiled engine a C++ compiler (`g++` on
Linux, e.g. `sudo apt install g++`; `xcode-select --install` on macOS). Without one, the pure-Python
engine runs with identical results, about 4 times slower.

    git clone https://github.com/IONOFIELD/FLYCNS.git flycns
    cd flycns
    python3 scripts/setup.py --check      # environment and self-test on the practice network, no account
    python3 scripts/setup.py              # asks for the neuPrint token once, then downloads the data
    .venv/bin/python fly.py               # the menu

- The token is saved to `~/.neuprint_token`, readable by your user only (mode 0600); or set the
  `NEUPRINT_TOKEN` environment variable instead.
- **Updating:** `git pull`, then `python3 scripts/setup.py`.
- Keeping the computer awake during long runs is Windows-only; on Linux and macOS use your system's own
  setting (for example `caffeinate` on macOS) for menu options 7 and 51.

---

## More detail

### How results are scored

- Each circuit is tested against numbers from published recordings, with pass/fail criteria, null models (the same neurons with shuffled wiring) and ablations.
- Many tests are **pre-registered**: their criteria are committed to git before they run, so a result cannot be tuned after the fact.
- Every check is labelled with **what it is evidence of**. A check that a parameter was tuned to pass is marked *calibrated* and is not counted as a test of the model ([`docs/CALIBRATION.md`](docs/CALIBRATION.md)).
- **For the maintainer:** after an update, menu option **51** does four things. It updates the code, pins the data fingerprint, reruns the core suite and the stricter null, then commits the results to a new `review/...` branch and pushes that branch only; your own branch is never pushed, and the results reach `main` through a pull request. It checks the git remote before it starts, keeps Windows awake while it runs, and is safe to run again after an interruption. The robustness battery (menu 7) does the same.
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
- "Sound suppresses the escape response" was withdrawn in September (at 120 trials per arm sound
  facilitated it), and is back under generation 3: the facilitation rested on the calibration defect.
- The brainsets export could not be read by the real loader; it is now built and reloaded with it.
- GF adaptation of 15 mV was an undersampled fit (10 mV at w_scale 0.3; 45 mV since the generation 3 refit).
- The two escape neurons got different sound inputs (3.65 and 0.73 mV for a 3 mV target): one value
  served both sides. Each is now calibrated on its own afferents (generation 3).
- The synaptic scale 0.3 had no recoverable derivation; it is now 0.4, the value a registered rule
  blind to every benchmark selects. Neither is measured (docs/CALIBRATION.md).
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
| Data | The fetched tables are fingerprinted by content, so the fingerprint ignores row order and file format. The fingerprint and each file's sha256 are committed in `data/MANIFEST.json`. Every check reads the files themselves, never a cache. The suite and registered tests refuse to run on data that differ, and every report records the fingerprint it ran on. | `flycns/integrity.py`, `scripts/setup.py` |
| Settings | Any `FLYCNS_*` override prints a banner, is stamped into the report, and is flagged PERTURBED in `results/SUITE.md`. `FLYCNS_ALLOW_DIRTY=1`, which waives the guards, is flagged ALLOW-DIRTY. The one-command canonical rerun (menu 51) refuses both. The robustness battery restores the canonical results when it finishes. | `flycns/integrity.py`, `scripts/overnight.py` |
| Evidence | Each check has a role: independent, control, robustness, structural, calibrated or construction. Only independent checks count as tests; structural checks count over the wiring without simulating it. CI fails if a check is unclassified. | `flycns/calibration.py`, `docs/CALIBRATION.md` |
| Stimuli | Every stimulus list is checked against the dataset before a long run, so a renamed cell type cannot silently drop an input. | `fit/audit_stimuli.py` |
| Registration | Every benchmark that scores a check is registered against a frozen model (version 2). The registration records the criteria with their numbers, and the content hash of every model file and of the benchmark's own script, where its thresholds live. A run refuses to score if any of these changed, and every check must be scored with exactly its registered band. A changed model needs a new registration that names the one it supersedes. Registrations are written before any result (`FLYCNS_REGISTER_ONLY=1`) and must be committed before the run they govern; a run never registers itself. They may never be edited, or deleted and written again. A run under a settings override or other package versions runs but is marked not registered. Reports not scored under a matching registration are flagged UNREGISTERED, and the headline then does not claim a registered result. | `flycns/registry.py`, each benchmark |
| Uncertainty | Every scored check carries a 95% interval (Wilson or bootstrap over trials), a per-draw score over seeds, or a null percentile. PASS means the whole interval lies inside the band; an interval across an edge is UNRESOLVED and does not count as a pass. | `flycns/stats.py` |
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
| **Visual escape** (loom to giant fiber to jump muscle) | The **calibration circuit**. The loom's rate scale and the giant fiber's adaptation were set to give 1 to 2 spikes per response, and the relay is 1:1 by construction. On that calibration, the giant fiber fires with probability 0.80 (95% interval 0.65 to 0.90), and each spike drives the jump motor neuron one-to-one 0.9 ms later. The independent part is the latency (37 ms, 95% interval 32 to 41, inside 10 to 60 ms). The controls: the jump motor neuron does not respond without the electrical synapse, and nothing responds on shuffled wiring, including wiring shuffled within cell class. On a shuffle that keeps each cell's class, neuropil and input per sign and size, the network stays as active as the real one, yet no draw of 20 drives the giant fiber as often (0.55 at most, against 0.80): the response depends on the specific wiring. Holds under other seeds, stricter connection thresholds, random sign flips and inversion of the transmitter calls the classifier is unsure of (the spike count is unresolved for seed 2). Under a weight scale of 0.30 the response probability is unresolved (0.63), and at 0.45 the spike count is (2.09): the adaptation was fitted at 0.4. |
| **Hearing to the giant fiber** | Sound alone stays subthreshold through the documented electrical synapse, which is calibrated, now on each giant fiber's own afferents (2.72 and 2.78 mV measured against 2.76; before, 3.7 and 0.7). **Pre-registered, counted as construction:** sound plus a near-threshold loom was expected to raise the giant fiber's response probability, as Tootoonian et al. 2012 recorded with injected current in place of the loom. It lowers it, from 30% to 17% (−0.13, 95% interval −0.24 to −0.03; 120 trials per arm; fail), and the registered sweep shows the suppression growing with loom strength (−0.14, −0.22, −0.39 at gains 0.6 to 0.8, each resolved) and unresolved only at the two near-threshold gains. Sound alone depolarises the giant fibers early (+2.5 and +1.5 mV) and then inhibits them deeply through the network (−9.6 and −20.8 mV by the end of a 60 ms tone). With the contact as EM annotates it, sound alone fires the giant fiber on every trial (C1; visible in an earlier reference run before registration, so not blind). |
| **Feeding** (taste to proboscis) | Does not reproduce feeding. The reason is measured, and the result holds when taste neurons are split by modality. |
| **Courtship song** (male-specific pC1 neurons to song command neurons) | Pre-registered. Activating pC1_14a drives the pulse-song neuron, as optogenetics showed, and more than the pC1_15/16 groups do (independent, pass). That it drives the pulse neuron *and not the sine neuron* cannot be tested here: the sine neuron fires in no arm at all, so the two checks that compare them are unresolved. Globally shuffled wiring drives nothing; a shuffle that keeps class, neuropil, sign and size leaves the pulse response inside the null's spread, but that null is not active enough to test wiring (unresolved). The companion paper's pC1_1b-to-sine link is not reproduced (registered check, fail). One male-specific type, SIP108m (4 cells, pIP5 class), drives the sine command neuron and not the pulse neuron, in a rule-chosen control arm. Seven further pIP5-class types are its strongest inputs by wiring but were not simulated. This is offered as a testable prediction; its novelty against the song literature has not been checked. |
| **Taste to feeding motor neurons** (signed map) | Counts over the wiring, not simulations (*structural* role). Appetitive taste neurons push proboscis extension up and bitter pushes it down (pre-registered: 1 of 3 checks pass; per-type sign agreement and LB2's dominance of pumping both fail). Of the 15 strongest unsigned influences on the proboscis motor neuron, 8 reverse to inhibitory once synaptic sign is included. Sugar neurons favour the opposite side's proboscis motor neuron, as Shiu et al. 2024 predicted, and this is visible only with sign. |
| **Flight** (wing sensors and command to flight motor neurons) | The afferent load was set so the upstroke motor neurons respond on average; scored seed by seed, they are in band in 2 of 5 recruitment draws (calibrated check, unresolved). The downstroke motor neurons, reached mainly through relay neurons, stay silent, which is an independent failure. One wing sensor type, SNpp16, drives the upstroke motor neurons selectively at the working point its pre-registered rule picks (3 of the 13 cells), but reaches the band there in only 1 of 5 draws (reliability test fails; 5 cells would be in band in 5 of 5). Its fresh-draw replication fails. Its transmitter-uncertainty test fails because the registered 7-cell size now overshoots the band with or without inverting the 87 uncertain connections; selectivity holds under the inversion. It fails with faster cord membranes or a smaller threshold gap (registered robustness tests). With all 13 SNpp16 cells firing every wingbeat, the upstroke neurons are driven above the band (independent, fail), and withholding SNpp16 alone does not silence them (independent, fail). |

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
- **Borrowed single-neuron parameters.** Every neuron uses central-brain values from Shiu et al. 2024. The escape relay survives every tested change to the cord neurons' parameters except one: with a 10 mV gap between rest and threshold it fails (TTMn/GF 0.30, lag 23.4 ms; cord sweep, run 14). The SNpp16 flight result is sensitive to them.
- **Transmitters come from a classifier.** It is less reliable for modulatory neurons (Eckstein et al. 2024). The companion paper's driver-line data disagree with the classifier on one taste neuron type, LB3d, and the model shows that this call decides whether aversive salt promotes or suppresses feeding.
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
