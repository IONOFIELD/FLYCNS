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

> **Re-measured across recruitment draws (23 Sept 2026).** An earlier version of this section
> quoted single random draws. DVMn 1a-c's proprioceptive drive is concentrated in a few
> afferents, so which ones a given load recruits decides whether it fires. Across five draws:
>
> | load | DVMn 1a-c mean +/- SD | range across draws | DLMn c-f |
> |---|---|---|---|
> | 0.25 (anchor) | 6.8 +/- 6.2 Hz | 0 to 15.2 | 0 |
> | 0.35 | 9.2 +/- 9.7 Hz | 0 to 25.9 | 0 |
> | 0.40 | 18.9 +/- 7.6 Hz | 11.2 to 31.7 | 0 |
> | 1.00 (all recruited) | 83.6 +/- 0.2 Hz | 83.5 to 83.9 | 0 |
>
> So DVMn is in band **on average** at the anchor but no single run reliably puts it there; only
> at full recruitment, where nothing is left to chance, is it stable, and there it is seven times
> over band. The anchor moved from 0.35 to 0.25 under the same rule applied to the mean. Everything
> else survived the draws: DLMn c-f silent at every load in every draw; steering wiring-specific in
> every draw (null 0); b1 at the anchor 105 Hz, 0.52 spikes per wingbeat; and stage 2 unchanged
> (the 100 Hz command that brings DLMn c-f to 12.5 Hz drives DVMn to 40.5 Hz). DLM's silence was
> also confirmed independently of the draw: it stays below 2 Hz across the whole relay-layer
> parameter sweep (`benchmarks/sensitivity_flight.py`).
>
> **The variance names a cell type, and the named type is selective, not necessary.** One wing
> campaniform type, **SNpp16** (13 cells, ADMN), carries 664 of DVMn 1a-c's 1,017 afferent
> synapses, 65%. `benchmarks/flight_snpp16.py` drove identified sets deterministically, all cells
> firing once per wingbeat, three phase seeds each. The two pre-stated checks **both failed**:
>
> | arm | DVMn 1a-c | steering | b1 | DLMn c-f |
> |---|---|---|---|---|
> | SNpp16 alone (13 cells) | 33.6 Hz | 0 | 0 | 0 |
> | every other afferent (400) | 14.9 Hz | 71.5 | 263 | 0 |
> | all 413 afferents | 83.5 Hz | 65.5 | 261 | 0 |
> | SNpp16 alone, rewired null | 0 | 0 | 0 | 0 |
>
> N1 (SNpp16 alone puts DVMn in the 2-12 Hz band) failed: it drives DVMn three times over band.
> N2 (withholding SNpp16 drops DVMn below 2 Hz) failed: the other afferents still give 14.9 Hz. So
> the necessity prediction was wrong. What the arms show instead, reported and not scored: SNpp16
> is a **selective** driver, reaching DVMn and nothing else in the flight system, through its real
> wiring (the rewired null gives zero); and inputs to DVMn sum **supralinearly**, 83.5 Hz together
> against 48.5 for the two parts, which is why random recruitment swung so widely. The criteria
> were not rewritten after the fact; a graded-recruitment test with criteria stated in advance
> would be the way to score the selectivity claim. That test has now been run.
>
> **Graded test, criteria registered before the run** (`benchmarks/flight_snpp16_graded.py`;
> criteria committed in `11dcc6a` before any result existed; final results in `0eb3416`;
> `64d665b` holds an intermediate state). k of the 13 SNpp16 cells were recruited, k = 1 to 13,
> five draws each randomising which cells fire and their phase. Result: **four of five criteria
> pass.**
>
> | k | DVMn 1a-c mean | draws in band | steering | b1 | DLMn c-f |
> |---|---|---|---|---|---|
> | 1-2 | 0.0 Hz | 0/5 | 0 | 0 | 0 |
> | 3 | 1.2 Hz | 1/5 | 0 | 0 | 0 |
> | 4 | 0.0 Hz | 0/5 | 0.14 | 0 | 0 |
> | **5 (k*)** | **3.9 Hz** | **4/5** | 0.12 | 0 | 0 |
> | 6 | 4.5 Hz | 4/5 | 0.18 | 0 | 0 |
> | 7 | 7.4 Hz | 5/5 | 0 | 0 | 0 |
> | 8 | 9.0 Hz | 5/5 | 0 | 0 | 0 |
> | 9-13 | 14.7 to 33.6 Hz | above band | 0 | 0 | 0 |
>
> - **G1 graded: FAIL.** The mean at k=4 falls below k=3 by more than the 0.5 Hz tolerance.
>   SNpp16's cells contribute unequally, so at small k which cells fire matters more than how
>   many. The criterion was fixed in advance and stands.
> - **G2 in-band window: pass** (k=5 to 8). **G3 selective at k*: pass**, and at every k: with
>   all 13 cells driving DVMn to 33.6 Hz, steering never exceeds 0.2 Hz and b1 and DLMn stay at
>   zero. **G4 wiring-specific: pass** (rewired null 0 Hz). **G5 reliable: pass** (4/5 at k*,
>   5/5 at k=7 and 8).
>
> Reported, not scored. SNpp07 (12 cells; an earlier note here called it 5, which was the number
> among DVMn's top 20 contributors) is **not** selective: alone it gives DVMn 3.5 Hz but also
> drives steering at 1.6 Hz. Supralinearity is strong at physiological rates: SNpp16 at k*=5 plus
> SNpp07 gives 28.7 Hz against 7.4 for the parts, 3.9 times the sum (1.7 at full recruitment).
>
> **Claim, scored and specific:** one named wing campaniform type, SNpp16, drives the DVM motor
> neurons without recruiting any steering muscle, reliably from about seven of its thirteen cells,
> through its actual wiring. Prediction: activating SNpp16 in a flying fly should raise DVM motor
> neuron activity without engaging the direct steering muscles.
>
> **Robustness battery, criteria registered before the run** (`benchmarks/flight_snpp16_robustness.py`;
> registered at `77e0cc5`, results `1225b21`). Two of three pass, and the failure qualifies the claim:
>
> - **R1 transmitter uncertainty: pass.** With 132,680 edges inverted (every neuron whose own
>   synapses disagree with its label), k=7 gives exactly the unperturbed draws (10.3, 7.2, 6.1,
>   6.7, 6.7 Hz). None of the uncertain calls lie on SNpp16's path to DVMn.
> - **R3 fresh draws: pass.** k* is 5 again, k=7 is in band in 4 of 5, and the curve is
>   monotone this time, so the k=4 dip that failed G1 was a property of those particular draws.
>   G1 remains a recorded failure because it was scored on the original draws.
> - **R2 relay-layer parameters: FAIL.** Selectivity holds at the declared relay values and at
>   every slower or less excitable setting, but leaks at three of seven: tau_m 5 ms (steering
>   3.5 Hz, and DLMn c-f fires at 23.6 Hz), tau_m 10 ms (steering 2.7 Hz), and a 4 mV threshold
>   gap (steering 3.3 Hz). b1 stays at zero throughout. DVMn's in-band rate is also fragile,
>   falling to zero at a 10 mV gap or a 5 ms refractory period.
>
> **The claim, as it now stands:** SNpp16 drives the DVM motor neurons selectively **under the
> declared relay parameters**; the selectivity does not survive faster or more excitable relay
> neurons, and because those parameters are inherited from central-brain values rather than
> measured, the claim is conditional on them. Its independence from transmitter uncertainty and
> from the particular cell draws is established.



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

### Stage 2: the descending flight command, and a structural advantage the dynamics cannot use

DNg02 is the descending population whose activation drives the indirect flight muscle motor
neurons (Namiki et al. 2022, Curr Biol 32:1189-1196). In MaleCNS v1.0 it is 29 cholinergic cells
across seven subtypes (DNg02_a to _g), and delivering it matters: an earlier run selected it by
the exact name "DNg02", which matches nothing, so those arms ran without the command (commit
ce8b9d2, corrected in cbbdba7; an empty stimulus set now aborts the run). With the command
delivered to 1,327 connections and the proprioceptive loop at its anchor, mean power output rises
with command rate (2.9, 4.0, 6.6, 25.6 Hz at 10, 25, 50, 100 Hz), so DNg02 does drive the power
system. But the two power pools separate:

| DNg02 rate | DLMn c-f | DVMn 1a-c |
|---|---|---|
| 10 Hz | 0.0 Hz | 11.7 Hz (in band) |
| 25 Hz | 0.0 Hz | 15.9 Hz |
| 50 Hz | 0.1 Hz | 23.2 Hz |
| 100 Hz | 14.4 Hz | 50.8 Hz |

**No command rate places both the downstroke (DLM) and upstroke (DVM) power motor neurons in the
measured 2 to 12 Hz range together**, whereas in the fly both fire in that range during flight.
Lowering proprioceptive load does not rescue it: the 100 Hz command alone contributes about 41 Hz
to DVMn. A joint sweep of load and command against these two targets was not run, because two
free parameters fitted to two criteria will find a point by construction and predict nothing.

The wiring predicts the opposite of what the model does. Per cell, DLMn c-f receives 1,841 units
of net DNg02-derived drive and DVMn 1a-c 902, so the connectome gives DLM about twice the
descending command. The difference is where it sits: DLM's is almost entirely disynaptic (15,616
synapses through DNg02's targets against 423 direct), DVMn is already held near threshold by 1,017
direct proprioceptive synapses. In a cord with no background activity the relay layer stays
subthreshold until the command is very strong, so a two-to-one structural advantage becomes the
weakest firing in the pool. This is the sixth circuit to point at missing background activity and
the most precisely localised: the gap is a named relay layer with a measured advantage that the
dynamics cannot use. The DLM gap junctions described by Huerkey et al. 2023 would pool the five
DLM motor neurons but add no net drive, so they are not a fix for this.

### Feeding re-tested with taste afferents split by modality (registered)

The feeding drive used above mixed modalities. Tastekin, de Haan Vicente et al. 2026 (Cell
189:5527-5551, Fig. 2) type the MaleCNS labellar GRNs and assign them by driver-line anatomy:
LB1a-d bitter, LB3a water, LB3b and LB3c sugar, LB3d aversive high salt / heavy metal. Our
"sugar proxy" contained LB3a-d plus pharyngeal and taste-peg types. `benchmarks/feeding_by_modality.py`
re-tested the mechanism by modality, criteria registered at `4cfae84` before any result (results
`98f2c29`). All five labellar types are cholinergic in MaleCNS.

| group | onto MN9 excitatory / inhibitory relays | ratio | signed 2-hop | MN9 at 100 Hz |
|---|---|---|---|---|
| sugar (LB3b, LB3c; 34 cells) | 77 / 114 | 0.68 | ~0 | 0 |
| bitter (LB1a-d; 38) | 0 / 6 | 0.00 | ~0 | 0 |
| water (LB3a; 17) | 58 / 0 | 58 | ~0 | - |
| aversive salt (LB3d; 26) | 119 / 43 | 2.77 | ~0 | - |
| old mixed proxy (140) | 1,097 / 3,333 | 0.33 | -0.0035 | 0 |

**F1 verdict by the registered rule: STRENGTHEN.** Sugar alone still targets MN9's inhibitory
relays more than its excitatory ones and its two-hop product is not positive, and MN9 stays silent
to sugar at 50 and 100 Hz. F2 passes (sugar's ratio exceeds bitter's). F3 and F4 fail: nothing
drives MN9, so the dynamics show no valence.

**But the mechanism we published needs rewording.** The strong 3:1 inhibitory bias came mostly
from the non-labellar afferents in the old proxy. Its four labellar types together (sugar, water,
salt) put 254 synapses on MN9's excitatory relays and 157 on inhibitory; the pharyngeal and
taste-peg types (aPhM2a, aPhM5, PhG1c, claw_tpGRN) put 843 against 3,176, a ratio of 0.27. For
sugar specifically the pathway is only weakly inhibition-biased at two hops (its two-hop product
rounds to zero) and relies on excitation arriving at three hops and beyond, which a network with
no background activity also cannot deliver. So the feeding negative holds, but its cause for
sugar is attenuation across hops more than the strong disinhibition the mixed drive suggested.

Two further observations. Bitter barely touches MN9's relays (6 synapses), whereas the companion
paper's unsigned analysis finds bitter and sugar reach proboscis motor neurons comparably. And
LB3d is classified cholinergic in MaleCNS, so this model has the aversive-salt type exciting MN9's
relays (ratio 2.77); the companion paper matches LB3d to glutamatergic driver lines and proposes
it inhibits attractive circuits. If that is correct, the transmitter call for LB3d is wrong and
the model signs it backwards: a specific discrepancy between the connectome's prediction and the
molecular evidence.

### A signed sensory-to-motor map for taste (registered)

The companion gustatory paper computes influence from every taste neuron type to the feeding motor
neurons but states that its metric ignores synaptic sign. `benchmarks/gustatory_signed_map.py`
computes the same kind of map with sign, and an unsigned version built identically, for 64 GRN
types against 10 feeding motor neuron types (criteria registered at `2239201`, results `316eb61`).
Measure: input-normalised path products, cumulative over hops 1 to 5.

| labellar group | MN9 | MN6 | MN11D | MN11V | CEM |
|---|---|---|---|---|---|
| LB3a-c (water, sugar) | +5.2e-3 | -1.4e-4 | +4.8e-3 | +2.7e-4 | +7.8e-3 |
| LB3d (aversive salt) | +4.3e-3 | +1.1e-4 | +2.7e-3 | +7.2e-4 | +2.4e-3 |
| LB4 | +2.1e-4 | -5.2e-5 | +1.4e-3 | +1.1e-3 | +5.1e-3 |
| LB2 | -2.6e-4 | +1.9e-4 | +3.7e-4 | +7.7e-4 | **+9.0e-3** |
| LB1e | -1.3e-3 | -7.0e-4 | +4.9e-5 | +8.0e-4 | +2.7e-3 |
| LB1a-d (bitter) | -2.7e-4 | -2.4e-3 | -8.5e-4 | +1.6e-3 | -1.2e-2 |

- **S1, valence has a sign: PASS.** On the proboscis-extension motor neurons (MN9, MN6) the
  appetitive types have net positive influence (+8.5e-4) and bitter net negative (-3.3e-4).
- **S2, per-type sign agreement on MN9: FAIL** (4 of 7; 5 required). All three appetitive types
  agree. Of the bitter types only LB1c is negative; LB1a (+4e-6) and LB1d (+1.5e-5) are
  effectively zero and LB1b is exactly zero. The failure is absence, not wrong sign: bitter taste
  barely reaches MN9 within five signed hops, consistent with bitter putting only 6 synapses on
  MN9's relays.
- **S3, LB2 dominates pharyngeal pumping: FAIL.** With sign, LB2 ranks fourth on MN11D and MN11V,
  behind the appetitive types. The companion paper's unsigned prediction for pumping does not
  survive sign. LB2's influence instead concentrates on CEM, the crop-entry motor neuron, where it
  is the largest positive value in the table; that half of the paper's claim is supported.

**Reported, not scored.**

- **Sign reverses the unsigned picture for more than half of the strongest inputs.** Of the 15
  gustatory types with the largest unsigned influence on MN9, 8 are net inhibitory once sign is
  included: every pharyngeal type in the list (aPhM1, aPhM2a, aPhM2b, aPhM3, aPhM4) plus LB1c,
  LB1e and LgAG1. An unsigned map would rank these among MN9's strongest drivers; with sign they
  push against it. This is a quantified instance of the limitation the companion paper states in
  its own discussion, and it agrees with the modality re-test above, which found the pharyngeal
  afferents strongly inhibition-biased.
- **The LB3d transmitter call flips its predicted role.** Signed as MaleCNS classifies it
  (cholinergic), LB3d pushes the proboscis motor neurons positive (+2.2e-3), like an appetitive
  type. Signed as the companion paper's driver-line match suggests (glutamatergic), it pushes them
  negative (-1.8e-3), like an aversive one. The classifier-versus-molecular discrepancy therefore
  decides whether this model treats aversive salt as promoting or suppressing feeding.

### Laterality: Shiu's contralateral prediction holds for sugar, and only with sign (registered)

Shiu et al. 2024 predicted that labellar sugar neurons on one side drive the opposite MN9 more
strongly. This project had recorded that as untestable for lack of a sugar annotation; with LB3b and
LB3c identified as sugar-sensing (Tastekin et al. 2026), `benchmarks/sugar_laterality.py` tests it
structurally (criterion registered at `27d36e2`, results `96308aa`). Only explicit sides are used
(annotated side, else the instance suffix); all 34 sugar cells have one. The criterion required both
sides positive and the contralateral value at least 10% above the ipsilateral one.

| drive | measure | from left: contra / ipsi | from right: contra / ipsi |
|---|---|---|---|
| sugar (LB3b, LB3c) | signed | **3.35** | **1.73** |
| sugar | unsigned | 1.14 | 0.88 |
| old mixed proxy | signed | 5.91 | 1.34 |
| old mixed proxy | unsigned | 1.02 | 0.91 |

**L1: PASS.** Sugar favours the contralateral MN9 on both sides. Unsigned, the same neurons show no
consistent bias, so the prediction becomes visible only when synaptic sign is included.

**Where the bias comes from.** Sugar has no short route to MN9: at two hops its signed influence is
at most 1e-5 on either side. Its whole influence arrives at three to five hops, and is contralateral
at each. This agrees with the modality re-test above, which found sugar reaches MN9 only through
longer paths.

**This overturns an earlier result.** Earlier versions of this project reported that unilateral
gustatory drive produced ipsilateral MN9 output, matching a 73 to 1 ipsilateral structural bias.
That bias was an unsigned count of raw synapses over two hops, on the mixed drive. The signed
per-hop breakdown shows why it misled: in the mixed drive the two-hop routes are net INHIBITORY on
both sides (from the left, -1.4e-3 ipsilateral against -3.2e-4 contralateral), so the large
ipsilateral routes counted as "drive" mostly suppress MN9. The dynamic run that appeared to confirm
it used the SEZ regional gain later retired as a naming artefact. The claim is withdrawn (section 7).

### Courtship song: a male-specific circuit the model reproduces (registered)

The male pC1/pC1x neurons were activated line by line while song was recorded (Current Biology
36:4697-4716, 2026, Fig. 5): pC1_13 and pC1_14 enhance pulse and suppress sine, pC1_14a alone is
necessary and sufficient for pulse, pC1_15 with pC1_16 suppress both. The song command neurons are
pMP2 (pulse), DNp13 (sine) and pIP10 (both). The authors traced two- and three-synapse paths, split
by transmitter, and concluded that many phenotypes cannot be explained by chemical synaptic
connections and transmitter predictions alone. `benchmarks/pc1_song.py` asked whether a signed,
spiking simulation does better (criteria registered at `981a20f`, results `8a9ca3f`). Suppression
phenotypes were declared untestable in advance: with no background activity there is no song-neuron
firing to suppress.

| drive (100 Hz) | cells | pMP2 (pulse) | DNp13 (sine) | pIP10 (both) | static signed pMP2 / DNp13 |
|---|---|---|---|---|---|
| pC1_14a | 6 | **8.15** | 0.00 | 5.70 | +1.3e-1 / +9.3e-3 |
| pC1_13a, 14a, 14b | 10 | **11.05** | 0.00 | 6.75 | +1.8e-1 / +1.4e-2 |
| pC1_15a-c, 16 | 20 | 0.00 | 0.00 | 1.45 | **-2.9e-2 / -1.5e-2** |
| P1a (12b, 4a, 4b), reported | 12 | 0.00 | 0.00 | 0.00 | +2.1e-3 / +8.9e-3 |
| pC1_17a-b, reported | 8 | 0.00 | 0.00 | 0.30 | +9.7e-4 / +1.0e-2 |
| pC1_14a, rewired null | 6 | 0.00 | 0.00 | 0.00 | - |

Units: spikes per cell per 200 ms pulse.

**All four criteria pass.** P1: pC1_14a drives pMP2 far above the 0.5 criterion and above DNp13.
P2: the pC1_13/14 combination does the same. P3: pC1_14a drives pMP2 more than pC1_15/16, which
leave it silent. P4: on shuffled wiring pC1_14a drives nothing. This is the first male-specific
circuit in the project, and one of only two circuits (with escape) where the model reproduces a
recorded phenotype from wiring alone.

**Sign recovers the phenotypes statically too.** The four-hop signed path products already point
the right way for every tested group, including the one the dynamics cannot test: pC1_15/16 are net
NEGATIVE onto both pMP2 and DNp13, matching the suppression of both songs in the fly. For these
groups, sign and a few more hops are enough; the paper's more pessimistic conclusion was drawn from
two-synapse paths across many more lines.

**Caveat, resolved.** DNp13 fired in no arm of this test, so "pulse over sine" could have meant only
that the sine neuron was unreachable. A registered positive control settled it (below): DNp13 is
reachable, so pC1_14a's pulse-over-sine is genuine selectivity. The claim still covers the five
groups tested, not the paper's 48 pC1/pC1x types.

### The sine-song neuron is reachable, through a separate pathway (registered)

`benchmarks/dnp13_control.py` (registered at `c67b98e`, results `ccfdff2`) asked whether DNp13 can
fire at all. Its decisive arm drives DNp13's strongest excitatory input type, chosen by a fixed rule
from the graph before any simulation. The interpretation of every outcome was written in advance.

| drive (100 Hz) | cells | DNp13 (sine) | pMP2 (pulse) | pIP10 (both) |
|---|---|---|---|---|
| SIP108m, rule-chosen strongest input | 4 | **14.30** | 0.00 | 0.00 |
| pC1_1b | 2 | 0.00 | 0.00 | 0.00 |
| LC10a | 275 | 0.00 | 0.00 | 0.00 |

- **D1, reachability: PASS.** SIP108m drives DNp13 to 14.3 spikes per cell per pulse with pMP2 and
  pIP10 silent. By the pre-written interpretation, pC1_14a's pulse-over-sine is genuine selectivity.
- **D2, pC1_1b drives sine: FAIL.** pC1_1b drives nothing (static signed influence on DNp13 only
  +1.6e-2), and neither do all 275 LC10a cells. The companion paper's link from pC1_1b to DNp13 is
  not reproduced.

**Two opposite selective pathways.** pC1_14a drives the pulse neuron and not the sine neuron;
SIP108m drives the sine neuron and not the pulse neuron. The pulse/sine split is present in the
wiring and survives simulation in both directions.

**A new prediction: activating SIP108m should promote sine song.** It was not proposed in the
companion paper; the rule found it from the wiring. SIP108m is 4 cholinergic central-brain neurons,
two per side. DNp13 receives 9,101 excitatory against 7,307 inhibitory synapses, and eight of its ten
strongest excitatory input types carry the "m" suffix (SIP108m, PVLP204m, SIP109m, SIP110m_a and _b,
AVLP713m, PVLP214m, AVLP711m). Whether that suffix marks male-specific types, and therefore whether
the sine pathway is sexually dimorphic, is not established here: the local data carries no
dimorphism annotation.

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

**Stimulus-set integrity** (`fit/audit_stimuli.py`, run automatically by `run_all.sh` and
`overnight.sh`). Stimulus neurons are selected by exact type name, and MaleCNS splits many
populations into subtypes, so a correct-looking name can match nothing. That happened once: the
first DNg02 run selected "DNg02", which matches none of the 29 DNg02_a to _g cells, and those arms
ran without their input. The model now raises when a stimulus set matches no neurons and warns
when part of one does not, and every long run audits all sets first.

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

- **"Unilateral gustatory drive gives ipsilateral MN9 output, matching a 73 to 1 structural
  bias."** Reported in earlier versions and in commit messages from 8 September. The structural
  bias was an unsigned raw-synapse count whose large ipsilateral routes are net inhibitory once sign
  is included, and the dynamic confirmation ran under the since-retired SEZ gain. With sign and the
  identified sugar neurons, the bias is contralateral, as Shiu et al. predicted.
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
