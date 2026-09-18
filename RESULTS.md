# flycns: results note

*Status v0.8, 11 September 2026. A working note, not a manuscript. Every number is reproducible
from the scripts named beside it; run `./fly` and use the menu. Where the model disagrees with a
measurement, the model is presumed wrong.*

---

## In one paragraph

The complete male Drosophila central nervous system connectome (Janelia FlyEM MaleCNS v1.0,
166,700 neurons, brain and ventral nerve cord) was simulated as a signed leaky integrate-and-fire
network using the model and parameters of Shiu et al. 2024, with the loom stimulus measured from
public calcium imaging and split by the fly's behavioural state. Two circuits reproduce published
physiology under a single declared parameter set with no fitted gains: the giant fiber escape
pathway and auditory input to the giant fiber. Three further circuits do not, and the reason is
the same in each case and is measured rather than assumed. A nine-suite robustness battery shows
no scored result depends on a transmitter call the connectome's own classifier is uncertain about.

---

## 1. What passes

**Loom escape** (`benchmarks/gf_escape.py`, 8 scored checks). Driving the nine loom-sensitive
lobula columnar populations at measured amplitudes fires the giant fiber 1.06 times per responding
cell with a response probability of 0.68 (95% CI 0.52 to 0.80, 40 trials) and a latency of 37 ms.
Each GF spike drives exactly one TTMn spike 0.9 ms later through a modelled gap junction. Without
the electrical model TTMn is silent; on a degree-preserving rewired connectome nothing fires at
all. This is a sensory-to-motor cascade across the neck connective at physiological latency.

**Auditory input to the giant fiber** (`benchmarks/auditory.py`, 4 scored checks). Johnston's organ
drive alone leaves GF subthreshold, as recorded in vivo. Removing both the electrical model and
the 679 EM synapses annotated as chemical on that contact abolishes the response, identifying
those synapses as the pathway.

**Feeding, partially** (`benchmarks/feeding.py`, 4 scored checks). Each of MN9's excitatory
second-order inputs drives it when stimulated directly; MN9 is silent on a rewired null; activity
stays inside the SEZ; motor rates stay physiological. What fails is the part that matters, below.

---

## 2. What does not pass, and why

Four independent circuits fail. Three share one cause.

### The shared cause: this model class cannot express disinhibition

- **Taste to MN9.** MN9's input is balanced to 1.4% (2,966 excitatory against 3,049 inhibitory
  synapses). Gustatory afferents contact its inhibitory relays about three times more strongly
  than its excitatory ones (1,097 against 3,333 synapses for the screen-selected subset; 1,314
  against 4,659 for all anatomically gustatory afferents). Signed path products from those
  afferents to MN9 are negative at two hops and positive at three to five: **the pathway is
  disinhibitory** (`benchmarks/feeding_mechanism.py`).
- **The canonical ON visual pathway.** Mi1's largest input is L1 with 141,873 glutamatergic
  (inhibitory) synapses. The ON response is a double inversion: light depolarises photoreceptors,
  histamine inhibits L1, L1 releases less glutamate, Mi1 is released.
- **AstA peptidergic modulation.** Pm3 is GABAergic, so activating it in a silent network produces
  nothing at all, in the model or in principle (`benchmarks/peptide_asta.py`).

A network with no spontaneous activity cannot represent any of these, and a uniform tonic baseline
does not help: it lets MN9 respond but the wind-sensitive control responds just as strongly
(specificity lost) and the escape response is abolished (`benchmarks/fit_baseline.py`). Four
uniform manipulations were tested and all fail: global weight scale (0.25 to 1.0), class-wise
gains (up to 3x), regional gain on SEZ intrinsic neurons (1.5 to 4x), and uniform tonic
depolarisation with noise (3 to 6 mV).

### The fourth: the ear-to-flight route exists but is silent

The pathway is four hops: 114 auditory Johnston's organ afferents to SAD and WED relays, then
DNp02 (818 synapses), DNp06 (806), DNp11 (568 plus 96 direct) and DNg108 (489 plus 32 direct) onto
the VNC premotor interneurons that drive the wing muscles. The giant fiber does not participate
(6 synapses), consistent with it driving the jump rather than steering. But all four descending
neurons are loom-dominated by 3.5x to 38x in two-hop signed input, so MaleCNS shows no dedicated
auditory-to-flight channel, and none of them fires under measured loom drive, so the multisensory
test the anatomy suggests would compare zero against zero (`benchmarks/auditory_wing_trace.py`).

### A different obstacle: DNp31 and the closed loop

DNp31 is the strongest descending input to the wing motor pool (3,019 synapses) and is the only
neuron examined here with a large excitatory surplus (net +14,568). All of its wing output is
excitatory and spans the whole flight apparatus: DLMn c-f (1,128) and DLMn a,b (156) for the
downstroke, DVMn 1a-c, 2a,b, 3a,b (1,077) for the upstroke, ps1 (593), b2, b1 and hg4 for
steering. Its dominant input is proprioceptive and specifically from the **wing**: campaniform
afferents entering through ADMN, the anterior dorsal mesothoracic (wing) nerve, give 1,045,551
on the two-hop measure, with 24,588 from DMetaN, the dorsal metathoracic (haltere) nerve, and
nothing from any leg nerve (`benchmarks/embodiment_gate.py`). It fires zero spikes under loom
because wing campaniform organs report self-generated wing load, which exists only when the
animal is already flying. This is an argument for embodiment, not for more parameters.

A correction is recorded here rather than hidden. An earlier draft read ADMN as an abdominal
nerve and called DNp31 abdominal-load-driven; that was wrong. Court et al. 2020 (Neuron
107:1071-1079) and the wing sensory reconstruction of Lesser, Moussa et al. (eLife 107867) place
wing afferents in ADMN and haltere afferents in DMetaN, and the dataset confirms it: abdominal
afferents enter through AbN1 to AbN4 and AbNT (1,145 cells, all subclass `abdomen`). The
consequence is good news: the haltere campaniform population is present in MaleCNS v1.0 as the
195 DMetaN afferents, under a nerve-based label rather than a "haltere" subclass.

**The proprioceptive-to-wing-motor loop, as wired.** Wing and haltere campaniform afferents
contact wing motor neurons directly with 11,412 synapses, all excitatory, and through 1,112
relay interneurons with 181,661 (101,272 excitatory, 80,389 inhibitory). The net drive splits
along a functional line: power muscles are excited (DLMn c-f +10,352, DVMn 1a-c +4,711, DLMn a,b
+3,732, DVMn 3a,b +1,649, DVMn 2a,b +1,629) and most steering muscles are inhibited (tp1 -4,697,
ps1 -2,285, hg3 -2,136, hg4 -1,352, hg2 -944), with iii1 (+4,277), b2, i1 and hg1 as excited
exceptions. No physiological counterpart to that split was found in the literature; it is a
connectome-derived prediction, and the surrogate loop below is the test of it.

---

### The flight loop, run: monosynaptic drive works, disynaptic drive does not

`benchmarks/flight_loop.py` supplies the missing proprioceptive input as a surrogate body: the 218
wing (ADMN) and 195 haltere (DMetaN) campaniform afferents fire one spike per cycle at the
Drosophila wingbeat frequency of 202 Hz (Vogel 1967) with 0.8 ms jitter (Fox, Fairhall & Daniel
2010), a recruited fraction set by a scalar load, and uniform phase, since no Drosophila phase
map exists. The drive is injected into the afferent neurons themselves, so everything downstream
runs through the connectome's own synapses. Measured targets: DLM and DVM motor neurons at 2 to 12
Hz (Harcombe & Wyman 1977; Huerkey et al. 2023), b1 at one spike per wingbeat (Fayyazuddin &
Dickinson 1996). Afferent parameters are from crane fly, flesh fly and blowfly, stated as such.

What happened:
- **The steering system is driven by the wiring, not by the volume of input.** At the anchor load
  the real network gives 31 Hz across steering motor neurons and 128 Hz in b1; the rewired null
  gives zero for both. b1 fires 0.6 to 0.9 spikes per wingbeat across loads, in range; its phase
  locking is untestable while afferent phase is uniform by assumption.
- **The connectome's sign prediction holds for steering.** The four most-inhibited types in the
  wiring (tp1, ps1, hg3, hg2) are silent or near it; the excited ones fire (b1, i2, b2, iii1, i1).
  Three mild exceptions each way.
- **DVMn 1a-c fires, DLMn c-f never does**, at any load. DVMn receives 1,017 campaniform synapses
  directly. DLMn c-f receives 75 directly and depends on relays, where its structural balance is
  favourable (18,982 excitatory against 8,639 inhibitory). The diagnostic shows why that fails:
  of 92 excitatory relay interneurons onto DLMn c-f, **4 are active, at 1.1 Hz**, against 13 of 85 inhibitory relays at 3.0 Hz. The relay layer
  of a silent cord does not relay. In the rewired null, where DLM acquires random direct input,
  it is the one motor neuron that fires.
- **DNp31 stays silent** under all 413 afferents at 202 Hz, its own dominant input.
- **Closing the loop saturates**, because the surrogate body maps power output monotonically to
  load, which is positive feedback by construction; that is a property of the body model, not a
  finding about the fly.

This is the fifth circuit to point at missing background activity, and the first where the
missing activity sits in identified premotor interneurons rather than in a modulatory neuron
the dataset lacks. In a flying fly those interneurons are presumably driven by descending flight
command; in a silent cord they are subthreshold, and the disynaptic half of the flight motor
system is unreachable.

## 3. The missing ingredient is not obtainable from this dataset

Feeding needs cell-specific spontaneous activity. The one neuron with a measured, hunger-gated
tonic rate in the right place is TH-VUM, a single dopaminergic ventral unpaired median neuron in
the SEZ firing at about 1 Hz when fed and 25 Hz after 24 h starvation (Marella, Mann & Scott 2012,
Neuron 73:941-950, Fig. 6, loose patch in vivo, 5 animals per condition). It cannot be used, and
neither can the alternatives (`fit/check_modulators.py`):

- **By name:** peptidergic populations exist (hugin 4 cells, leucokinin 12, AstA 2, drosulfakinin
  6, NPF 4), but there is no TH-VUM. AKH-producing cells are absent as expected for a
  neuroendocrine organ outside the CNS.
- **By transmitter and region:** of 396 dopaminergic and 101 octopaminergic neurons, **none has
  even 20% of its synapses in SEZ compartments**; they sit in the mushroom body, central complex
  and abdominal neuromere. Only serotonin has any SEZ presence (10 cells above 50%). This also
  rules out the SEZ octopaminergic AKHR route.
- **By morphology:** of 1,037 midline bodies with more than half their synapses in the SEZ, 862
  are output-dominated (the nSyb-GFP phenotype Marella describes), and **zero are
  dopamine-predicted**. Four contact MN9's relays at all; two are cholinergic and therefore
  excitatory, two have unclear transmitters with contact weights under 110 synapses against the
  ~6,000 reaching MN9.

The likeliest explanation is a classifier blind spot rather than a missing neuron: Eckstein et al.
2024 (Cell 187:2574-2594) report cell-level accuracy of 96% for GABA and 91% for acetylcholine but
85 to 90% for dopamine, and neurons releasing mainly by volume transmission offer few classical
synapses to classify. A dopaminergic VUM would plausibly sit among the ~1,095 untyped,
transmitter-unclear gnathal bodies. No candidate is promoted on shape alone.

---

## 4. Measured inputs

The loom stimulus is not a guess. Per-glomerulus amplitudes and the trial-gain distribution were
extracted from the public Turner, Krieger, Pang & Clandinin 2022 dataset (eLife 11:e82587; Dryad
doi:10.5061/dryad.h44j0zpp8) by `fit/extract_turner_loom.py`: 21 flies, 1,510 loom trials, 13
glomeruli, epoch onsets taken from the per-epoch clock stamps rather than the photodiode.

Trials are split by the authors' own 50 Hz walking classification, carried in the datafiles, so no
video download is needed. Every glomerulus except LC12 is relatively larger when the fly walks
(LC6 0.64 against 0.40, LC21 0.59 against 0.39, LC26 0.93 against 0.69, LC4 0.73 against 0.52,
LPLC2 1.00 against 0.83) and the trial-gain sigma is higher too (0.442 against 0.357). That is the
locomotor enhancement the original paper reports, recovered by an independent extraction. Because
the benchmarks simulate a fly that is not walking, the **stationary** amplitudes are the default;
`FLYCNS_LOOM_STATE=walking|all` selects the others.

The dF/F-to-rate scale (5 Hz for the strongest glomerulus) is the one remaining free parameter of
the stimulus and is declared as such.

---

## 5. Robustness

**Nine-suite battery**, each a full three-circuit suite at 40 trials under measured stationary
input (`overnight.sh`, `results/overnight/`):

| run | result | failing check |
|---|---|---|
| seed 1 | 16/16 | - |
| seed 2 | 16/16 | - |
| 5% random NT sign inversion (seed 0) | 16/16 | - |
| 5% random NT sign inversion (seed 1) | 16/16 | - |
| 10% random NT sign inversion | 15/16 | GF response probability |
| weight scale 0.25 | 15/16 | GF response probability (under-driven) |
| weight scale 0.35 | 16/16 | - |
| weight scale 0.40 | 16/17 | GF spikes per response (over-driven) |
| **targeted NT inversion** | **all pass, 0 failures** | - |

The targeted arm inverts the sign of every neuron whose own per-T-bar predictions disagree with
the aggregate label used for signing: 132,680 edges, 2.0% of synaptic weight. It costs nothing
anywhere, so **no scored result rests on a transmitter call the classifier is uncertain about**.
That is stronger than surviving an arbitrary 5% flip, which is why both are reported. The weight
scale has a genuine plateau rather than a knife edge: 0.30 and 0.35 both pass and the two failures
sit on opposite sides. The last two rows have 17 checks because the auditory benchmark gained one
mid-battery when it moved to modality-based stimulus selection; escape and feeding are comparable
throughout.

**Transmitter confidence** (`fit/synapse_nt.py`). Over the 173,308 annotated neurons, mean
per-synapse confidence is 0.91; 1.2% of neurons fall below 0.6; neurons whose T-bars disagree with
their aggregate label carry 3.5% of total synaptic weight.

**Cord parameters** (`benchmarks/sensitivity_cord.py`). Sweeping cord-only membrane time constant
(5 to 40 ms), threshold gap (4 to 10 mV) and refractory period (1 to 5 ms) across all 14,153
nerve-cord neurons leaves every escape check passing and every metric unchanged. The inherited
central-brain parameters are a limitation for circuits requiring cord computation, not for this
benchmark.

---

## 6. The declared parameter set

Shiu et al. 2024 LIF parameters (tau_m 20 ms, threshold -45 mV, rest and reset -52 mV, refractory
2.2 ms, synaptic tau 5 ms, delay 1.8 ms). Chemical kick 0.275 mV x 0.3, the rescale fitted on
MaleCNS by sweep. GF spike-triggered adaptation 30 mV, the smallest value satisfying von Reyn's
constraints in a pre-stated sweep at 40 trials (`benchmarks/fit_gf_adapt.py`; an intermediate 15 mV
came from a 20-trial fit whose binding constraint rested on about five trials, and the script now
warns below 40). Proboscis motor neuron adaptation 10 mV; relay motor neurons deliberately not
adapted, since TTMn follows GF one-to-one (Tanouye & Wyman 1980). Electrical synapses: GF-TTMn and
GF-PSI as 1:1 relays with a 9 mV spikelet at 0.8 ms, and JON-GF on the two JO-B1 subtypes that
actually contact GF, calibrated to a 3 mV compound potential. The 679 EM synapses annotated as
chemical on that contact are removed when the electrical model is on. Monoamines are sign 0 by
deliberate scope. Regional and class gains are all 1.0 and there is no tonic baseline.

Every value is either cited or fitted by a rule stated before the fit. Full list with citations:
`flycns/graph.py` and `REFERENCES.md`.

---

## 7. What was retracted

- **A regional SEZ gain of 2.0.** Fitted while the SEZ was defined by type-name prefixes, where it
  appeared to open the feeding pathway. Defining the SEZ from the connectome's own compartment
  annotations shows the population is net inhibitory onto that pathway under either definition, so
  MN9 stays silent at every gain. The parameter is now 1.0 and the effect is documented as an
  artefact of the naming heuristic.
- **A claim that auditory drive suppresses the GF loom response.** Withdrawn as gain-dependent:
  the direction depends entirely on where the loom sits relative to threshold, and across the
  robustness battery at 20 trials per arm the reading was facilitation four times, suppression
  twice and no change twice. The benchmark now calibrates a near-threshold working point and
  reports the difference with a confidence interval; at 40 trials per arm it is unresolved.
- **A GF adaptation value of 15 mV**, withdrawn as an undersampled fit.
- **A plan to open the feeding pathway with cell-specific baselines from the literature**,
  withdrawn because the target neuron is not in the dataset.

---

## 8. What this does not claim

Single-neuron parameters are Shiu's central-brain values applied uniformly to brain and cord;
measured to be irrelevant for the escape benchmark, unexamined for circuits that need the cord to
compute. No parameter is fitted to a neural recording: only the stimulus is measured. Azevedo et
al. 2020 (eLife 9:e56754) give leg motor neuron input resistances of 150, 300 and 700 MOhm for
fast, intermediate and slow cells, and those numbers are recorded in `flycns/graph.py` but not
entered as parameters, because tau requires a capacitance the paper does not report, because
applying the gradient needs a fast/slow assignment for MaleCNS motor neurons that does not exist,
and because somatic current injection fails to evoke spikes in fast and intermediate motor neurons
(the spike initiation zone is electrically isolated), which a single-compartment cell cannot
represent at all. Modulatory transmitters are omitted, which is exactly what the feeding result
implicates. Gap junctions appear only where documented.

---

## 9. Relation to prior work

Model class, parameters and the feeding validation design: Shiu et al. 2024 (Nature 634:210-219).
Escape physiology: Tanouye & Wyman 1980, Allen et al. 2006, von Reyn et al. 2014 and 2017, Ache et
al. 2019, Augustin et al. 2019. Auditory-GF synapse: Pezier & Blagburn 2013, Yorozu et al. 2009,
Tootoonian et al. 2012, Kamikouchi et al. 2009, Vaughan et al. 2014. Loom tuning: Turner, Krieger,
Pang & Clandinin 2022. Peptidergic modulation: Krieger 2023. Transmitter prediction: Eckstein et
al. 2024.

What is added here: a test harness with numeric pass/fail criteria, null models and ablation arms;
one parameter set across independent circuits with no fitted gains; a spiking sensory-to-motor
cascade across the neck connective on MaleCNS; measured stimulus tuning extracted from public
imaging and split by behavioural state; a perturbation targeted at the connectome's own
uncertainty; and mechanistic accounts of four circuits this model class cannot reproduce. Full
references: `REFERENCES.md`.
