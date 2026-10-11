# Provenance: gf_escape

## Neurotransmitter sign map
{'acetylcholine': 1, 'gaba': -1, 'glutamate': -1, 'histamine': -1, 'dopamine': 0, 'octopamine': 0, 'serotonin': 0}

## Electrical synapses added (invisible to EM)
- DNp01 -> TTMn (ipsilateral, spikelet 9.0): shakB gap junction, 1:1 relay; Tanouye & Wyman 1980; Allen et al. 2006
- DNp01 -> PSI (ipsilateral, spikelet 9.0): shakB gap junction, 1:1 relay; Allen et al. 2006; Phelan et al. 2008
- JO-B1_a -> DNp01 (ipsilateral, spikelet {'compound_mV': 3.0, 'at_hz': 150}): JON->GF mixed synapse modelled as electrical; shakB-dependent (Pezier et al. 2016); mixed (Pezier et al. 2014); 3 mV target untraced; contact set from MaleCNS v1.0
- JO-B1_c -> DNp01 (ipsilateral, spikelet {'compound_mV': 3.0, 'at_hz': 150}): JON->GF mixed synapse modelled as electrical; shakB-dependent (Pezier et al. 2016); mixed (Pezier et al. 2014); 3 mV target untraced; contact set from MaleCNS v1.0

## Intrinsic overrides
- DNp01.b_adapt_mV = 10.0: all-or-none GF response; von Reyn 2014; Ache 2019. Fitted by pre-stated rule (smallest value giving 1-2 spikes/response, <=2 on the strongest gain quartile, P(response) 0.5-1, TTMn relay intact; benchmarks/fit_gf_adapt.py at >=40 trials). 10 mV under the measured stationary loom input (refit 2026-10-10, 40 trials; the strong-quartile constraint holds at 1.95, close to its limit of 2). Earlier 30 mV was fitted under the all-trials input; a 15 mV value came from an undersampled 20-trial fit. 0 mV gives up to 7 spikes per loom.
- superclass:cb_motor.b_adapt_mV = 10.0: sustained MN rates < 100 Hz; Azevedo 2020; McKellar 2020

## Regional gain: SEZ x1.0 (fitted, benchmarks/fit_regional.py), other x1
   SEZ definition: anatomical (roiInfo, 4,606 SEZ-intrinsic neurons)

## Loom tuning: MEASURED (stationary trials, 13 series): Turner, Krieger, Pang & Clandinin 2022, eLife 11:e82587; Dryad doi:10.5061/dryad.h44j0zpp8 (21 flies, extracted 2026-09-09); trial gain sigma 0.357; peak rate 5.0 Hz (free dF/F->rate scale)
{'LC4': 0.52, 'LC6': 0.4008, 'LC9': 0.316, 'LC11': 0.2725, 'LC12': 1.0, 'LC15': 0.59, 'LC16': 0.4908, 'LC17': 0.7778, 'LC18': 0.3764, 'LC21': 0.3853, 'LC26': 0.6906, 'LPLC1': 0.4905, 'LPLC2': 0.8282}

## Checks
- gf_spikes_per_response_1_to_2: PASS
- gf_response_prob_0.5_to_1: PASS
- gf_latency_10_60ms: PASS
- ttmn_one_to_one: PASS
- ttmn_lag_0.5_1.5ms: PASS
- cns_quiet: PASS
- electrical_necessary: PASS
- null_silent: PASS