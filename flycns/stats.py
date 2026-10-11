"""
Uncertainty for scored checks (audit 2026-10-11, gap 8).

A point estimate inside a band is not evidence that the model is inside the band: a hit rate of 0.575
from 40 trials has a 95% interval of 0.42 to 0.71, which straddles a 0.5 floor. Every scored readout
therefore carries a 95% interval, and a check has three outcomes:

  PASS        the whole interval lies inside the band
  FAIL        the whole interval lies outside the band
  UNRESOLVED  the interval crosses a band edge: more trials are needed before the check says anything

Intervals: Wilson for proportions (k of n); a percentile bootstrap over trials for means, ratios and
anything else computed per trial (2,000 resamples, fixed seed, so a rerun gives the same interval).
A readout with no trial structure (one number from one run), or graph arithmetic over the fixed
connectome (no sampling at all), is scored on its point value and marked "point" so the report says so.
Readouts repeated over seeds are scored per draw (stats.per_draw), never on the mean of the draws.

Every report keeps its "checks" (the point verdicts, as before) and adds "uncertainty": one record per
scored check, {estimate, ci95, band, method, verdict}. benchmarks/summarize.py counts the verdicts.
"""
import math

import numpy as np

Z95 = 1.959963984540054
N_BOOT = 2000


def wilson(k, n, z=Z95):
    """Wilson score interval for k successes in n trials. (0, 1) when n is 0."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, mid - half), min(1.0, mid + half)


def bootstrap(values, stat=np.mean, n_boot=N_BOOT, seed=0):
    """Percentile bootstrap 95% interval of stat over the rows of values (1-D, or 2-D with one row per
    trial for ratios). NaN rows are dropped first. Returns (estimate, lo, hi); (nan, nan, nan) if empty."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v).any(axis=1)] if v.ndim == 2 else v[~np.isnan(v)]
    if len(v) == 0:
        return float("nan"), float("nan"), float("nan")
    est = float(stat(v))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), (n_boot, len(v)))
    boots = np.array([stat(v[i]) for i in idx], dtype=float)
    boots = boots[~np.isnan(boots)]
    if len(boots) == 0:
        return est, float("nan"), float("nan")
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return est, float(lo), float(hi)


def ratio_of_sums(rows):
    """For 2-D rows (numerator, denominator) per trial: sum(num) / sum(den)."""
    d = rows[:, 1].sum()
    return rows[:, 0].sum() / d if d else float("nan")


def verdict(lo, hi, low=-math.inf, high=math.inf, strict=False):
    """PASS if [lo, hi] lies inside [low, high]; FAIL if it lies wholly outside; else UNRESOLVED.
    strict: the lower edge is exclusive ("A exceeds B" scored on the difference with low=0): PASS needs
    lo > low and FAIL needs hi <= low. A NaN interval (no data) is UNRESOLVED."""
    if lo is None or hi is None or math.isnan(lo) or math.isnan(hi):
        return "UNRESOLVED"
    inside_low = lo > low if strict else lo >= low
    below = hi <= low if strict else hi < low
    if inside_low and hi <= high:
        return "PASS"
    if below or lo > high:
        return "FAIL"
    return "UNRESOLVED"


def _num(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def scored(estimate, lo, hi, low=-math.inf, high=math.inf, method="bootstrap", n=None, strict=False, note=None):
    """One check's record: the estimate, its 95% interval, the band and the three-way verdict.
    method: "wilson" (a proportion), "bootstrap" (resampled over trials) or a short description."""
    rec = dict(estimate=_num(estimate), ci95=[_num(lo), _num(hi)],
               band=[None if math.isinf(low) else low, None if math.isinf(high) else high],
               method=method, verdict=verdict(lo, hi, low, high, strict))
    if strict:
        rec["band_lower_exclusive"] = True
    if n is not None:
        rec["n"] = int(n)
    if note:
        rec["note"] = note
    return rec


def proportion(k, n, low=-math.inf, high=math.inf, note=None):
    """A rate scored with its Wilson interval."""
    lo, hi = wilson(k, n)
    return scored(k / n if n else float("nan"), lo, hi, low, high, method="wilson", n=n, note=note)


def point(value, ok, method="point", note=None):
    """A readout with no sampling uncertainty (graph arithmetic over the fixed connectome) or no trial
    structure to resample: PASS or FAIL on the point value, and labelled as such in the summary."""
    rec = dict(estimate=_num(value) if not isinstance(value, bool) else value, ci95=None, band=None,
               method=method, verdict="PASS" if ok else "FAIL")
    if note:
        rec["note"] = note
    return rec


def per_draw(values, low=-math.inf, high=math.inf, need=0.8, note=None):
    """A readout repeated over independent draws (seeds): PASS if at least `need` of the draws are in band,
    FAIL if at most 1 - need are, else UNRESOLVED. Scored per draw, never on the mean of the draws."""
    v = [x for x in values if x is not None and not (isinstance(x, float) and math.isnan(x))]
    k = sum(low <= x <= high for x in v)
    n = len(v)
    need_k, fail_k = math.ceil(need * n - 1e-9), math.floor((1 - need) * n + 1e-9)
    vd = "UNRESOLVED" if n == 0 else ("PASS" if k >= need_k else ("FAIL" if k <= fail_k else "UNRESOLVED"))
    rec = dict(estimate=k / n if n else None, ci95=None, band=[None if math.isinf(low) else low,
               None if math.isinf(high) else high], method=f"per-draw ({k} of {n} in band; pass needs {need_k})",
               draws=[float(x) for x in v], n=n, verdict=vd)
    if note:
        rec["note"] = note
    return rec


def null_percentile(real, null_values, null_alive=True, note=None):
    """Wiring specificity against a null distribution. PASS if the real readout exceeds every null draw
    (one-sided p < 1/(n+1)); FAIL if it does not exceed the null median; else UNRESOLVED. A null that
    cannot fire at all (null_alive False) cannot test anything: UNRESOLVED."""
    nv = [float(x) for x in null_values if x is not None and not math.isnan(x)]
    pct = percentile_of(real, nv)
    if not null_alive:
        vd, why = "UNRESOLVED", "the null network is silent, so it cannot test wiring specificity"
    elif not nv:
        vd, why = "UNRESOLVED", "no null draws"
    elif real > max(nv):
        vd, why = "PASS", None
    elif real <= float(np.median(nv)):
        vd, why = "FAIL", None
    else:
        vd, why = "UNRESOLVED", None
    rec = dict(estimate=_num(real), ci95=None, band=None, method=f"null percentile over {len(nv)} draws",
               percentile=pct, null_draws=nv, null_alive=bool(null_alive), verdict=vd)
    if why or note:
        rec["note"] = "; ".join(x for x in (why, note) if x)
    return rec


def percentile_of(real, null_values):
    """Fraction of null draws strictly below the real value, plus half the ties (a mid-rank percentile)."""
    nv = np.asarray(null_values, dtype=float)
    nv = nv[~np.isnan(nv)]
    if len(nv) == 0:
        return float("nan")
    return float(((nv < real).sum() + 0.5 * (nv == real).sum()) / len(nv))
