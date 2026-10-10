"""
Stimulus protocols with provenance.

loom_protocol: population loom after Turner, Krieger, Pang & Clandinin 2022
(eLife 11:e82587). Loom-responsive glomeruli with a shared lognormal trial
gain. TUNING is an ordinal placeholder from their Fig 3A groups until the
authors' per-glomerulus loom dF/F replaces it.
"""
import os
import numpy as np

LOOM_TUNING_ORDINAL = {
    "LC4": 1.0, "LPLC2": 1.0, "LC6": 1.0, "LC16": 0.8,
    "LC26": 0.6, "LPLC1": 0.6, "LC9": 0.5, "LC17": 0.5, "LC12": 0.4,
}
GAIN_SIGMA_DEFAULT = 0.5
TUNING_SOURCE = "ordinal placeholder from Turner et al. 2022 Fig 3A groups"

# Measured values, if fit/extract_turner_loom.py has been run on the Dryad data.
import json
from pathlib import Path
# Behavioural state: loom responses are larger when the fly walks (Turner, Krieger, Pang & Clandinin
# 2022, reproduced by fit/extract_turner_loom.py: every glomerulus except LC12 is relatively larger in
# walking trials, e.g. LC6 0.64 vs 0.40, and the trial-gain sigma is 0.44 vs 0.36). The benchmarks
# simulate a fly that is not walking, so the STATIONARY set is the default; FLYCNS_LOOM_STATE=walking
# or =all selects the others. A requested state that is not in the file is an error, never a silent
# fallback: before 2026-10-10 the committed file had no per-state split, so every loom result
# silently used all trials while the documentation said stationary.
LOOM_STATE = os.environ.get("FLYCNS_LOOM_STATE", "stationary")
LOOM_FILE = Path(__file__).resolve().parents[1] / "data" / "loom_tuning_measured.json"
if LOOM_FILE.exists():
    _m = json.loads(LOOM_FILE.read_text(encoding="utf-8"))
    _byst = _m.get("amplitude_by_state", {})
    if LOOM_STATE == "all":
        _amp, _sig, _n = _m["amplitude"], _m.get("gain_sigma"), _m.get("n_series", "?")
    elif LOOM_STATE in _byst:
        _amp = _byst[LOOM_STATE]
        _sig = (_m.get("gain_sigma_by_state") or {}).get(LOOM_STATE)
        _n = (_m.get("n_series_by_state") or {}).get(LOOM_STATE, "?")
    else:
        raise SystemExit(f"[protocols] loom state {LOOM_STATE!r} is not in {LOOM_FILE.name} "
                         f"(it has: {sorted(_byst) + ['all']}). Re-extract it with menu option 22.")
    LOOM_TUNING = {k: v for k, v in _amp.items() if v > 0.05}
    GAIN_SIGMA_DEFAULT = float(_sig or GAIN_SIGMA_DEFAULT)
    TUNING_SOURCE = (f"MEASURED ({LOOM_STATE} trials, {_n} series): {_m['source']} "
                     f"({_m['n_flies']} flies, extracted {_m['extracted_on']})")
else:
    LOOM_TUNING = dict(LOOM_TUNING_ORDINAL)


# dF/F -> spikes/s scale for the most loom-sensitive type. The one free parameter of the
# loom stimulus; anchored so GF fires 1-2 spikes with P(response) >= 0.5 (von Reyn 2014).
PEAK_HZ_DEFAULT = float(os.environ.get("FLYCNS_PEAK_HZ", "5.0"))


def loom_protocol(model, n_trials=20, peak_hz=None, burst_ms=60, gap_ms=300,
                  gain_sigma=None, seed=None):
    peak_hz = PEAK_HZ_DEFAULT if peak_hz is None else peak_hz
    gain_sigma = GAIN_SIGMA_DEFAULT if gain_sigma is None else gain_sigma
    seed = int(os.environ.get("FLYCNS_SEED", "0")) if seed is None else seed
    """Run n_trials looms; return list of (onset_ms, gain)."""
    rng = np.random.default_rng(seed)
    tuning = model.stim["type"].map(LOOM_TUNING).fillna(0).values
    trials = []
    for _ in range(n_trials):
        model.run(gap_ms)
        gain = rng.lognormal(0, gain_sigma)
        trials.append((model.t_ms, gain))
        model.set_stim_rates(tuning * peak_hz * gain)
        model.run(burst_ms)
        model.set_stim_rates(np.zeros_like(tuning))
    model.run(gap_ms)
    return trials
