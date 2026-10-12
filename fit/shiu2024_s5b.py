"""
Registered check S5b (Gen 5, phase 1): quantitative bitter suppression, against the authors' own published
values. Registered separately from S5 (the qualitative test pre-registered in results/shiu2024_a0/), which is
never changed. Scored later by the phase-1 benchmark (A1: flycns in Shiu-compatible settings on FlyWire
v630); this file records the criterion and the reference values before any A1 run exists.

Reference values. Shiu et al. 2024's raw output (Edmond doi:10.17617/3.CZODIW, version 3, MIT; results.zip,
4,499,610,373 bytes, MD5 f6f2e314821fa6a4196214e3b2b14bc4, matching the Edmond file page) was read on the
user's computer by scripts/extract_shiu_archive.py (commit ff2dc9a, unchanged since). It wrote per-trial MN9
spike counts for the 121 Sugar_Bitter files of their Fig 3a and the 21 sugar dose files of Fig 1d, and the
sha256 of each file read: reference-data/shiu2024/ (both files pinned below). The archive's
results/example/sugarR_100Hz.parquet has the same sha256 as the GitHub copy A0 used, so both releases agree.

Published contralateral MN9 at sugar 100 Hz (30 trials each), Hz:
  bitter   0     20    40    60    80    100   120   140   160   180   200
  mean     67.0  57.7  45.3  29.2  11.7  4.0   1.5   0.1   0.2   0.1   0.0

S5b (registered here): sugar GRNs at 100 Hz plus bitter GRNs at 0, 20, 40, 60, 80, 100, 120 and 200 Hz,
30 trials each, A1 settings. At every one of the 8 points, the 95% bootstrap interval of (our contralateral
MN9 mean - the published mean, two samples of 30 trials) lies within +/-6.7 Hz: PASS. Any point wholly
outside: FAIL. Otherwise UNRESOLVED. The margin is 10% of the published sugar-alone rate (67.0 Hz), the
scale S1 uses, applied as an absolute margin at every point: a relative margin would be a fraction of a hertz
where the published curve is near zero, below what 30 trials can resolve. 0, 100 and 200 Hz reuse S5's runs;
20, 40, 60, 80 and 120 Hz are new arms on the published grid.

    FLYCNS_REGISTER_ONLY=1 python fit/shiu2024_s5b.py      write the registration (then commit it)
    python fit/shiu2024_s5b.py                             verify the pinned reference and print it
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import registry  # noqa: E402
from flycns.integrity import require_clean  # noqa: E402

LABEL = "shiu2024_s5b"
ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference-data" / "shiu2024"
PINS = {"shiu_archive_mn9.csv": "076ca67fc5eed1a2f590fe2c84c8b77373337be8f89ed615ec6bc6e5016f8355",
        "shiu_archive_manifest.json": "2e20cbc34f97c267d4ec887ea0d5c03f95f1721fd5d2494a1325955f5bcb427e"}
EXTRACTOR = ROOT / "scripts" / "extract_shiu_archive.py"
BITTER_POINTS = [0, 20, 40, 60, 80, 100, 120, 200]
MARGIN_HZ = 6.7

CRITERIA = dict(
    question="does flycns in Shiu-compatible settings reproduce the authors' published bitter suppression curve?",
    reference=dict(archive="Edmond doi:10.17617/3.CZODIW v3, results.zip", zip_bytes=4499610373,
                   zip_md5="f6f2e314821fa6a4196214e3b2b14bc4", extractor="scripts/extract_shiu_archive.py @ ff2dc9a",
                   files_sha256=PINS, readout="MN9 720575940660219265, contralateral; spikes per 1-s trial, 30 trials"),
    relation_to_S5="separate; S5 (qualitative, pre-registered in results/shiu2024_a0/) is unchanged",
    protocol=dict(settings="A1 (results/shiu2024_a0/ preregistered_phase1.a1_settings)", sugar_hz=100,
                  bitter_hz=BITTER_POINTS, trials_per_point=30,
                  reuse="bitter 0, 100 and 200 Hz are S5's runs; 20, 40, 60, 80 and 120 Hz are new arms"),
    checks={"S5b_bitter_curve_matches_published": dict(
        bands=[[-MARGIN_HZ, MARGIN_HZ]] * len(BITTER_POINTS),
        rule=("at each of the 8 bitter rates, the 95% bootstrap interval (two samples of 30 trials) of our "
              "contralateral MN9 mean minus the published mean lies within +/-6.7 Hz: PASS if all 8 do; FAIL if "
              "any lies wholly outside; UNRESOLVED otherwise"),
        margin_derivation=("10% of the published sugar-alone rate (67.0 Hz), the S1 scale, as an absolute margin "
                           "at every point"))},
)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def published():
    """The published per-trial counts at sugar 100 Hz, by bitter rate (verified against the pins first)."""
    bad = [f"{n}: {sha256(REF / n) if (REF / n).exists() else None} != {h}" for n, h in PINS.items()
           if not (REF / n).exists() or sha256(REF / n) != h]
    if bad:
        raise SystemExit("[shiu2024_s5b] reference files differ from the registration: " + "; ".join(bad))
    import pandas as pd
    d = pd.read_csv(REF / "shiu_archive_mn9.csv")
    d = d[(d.experiment == "sugar_bitter") & (d.sugar_hz == 100)]
    return {b: d[d.bitter_hz == b].sort_values("trial").mn9_contra.to_numpy(dtype=float) for b in BITTER_POINTS}


REG = registry.register(LABEL, CRITERIA, scripts=[__file__, EXTRACTOR])     # exits here under FLYCNS_REGISTER_ONLY
require_clean(LABEL)

if __name__ == "__main__":
    for b, v in published().items():
        print(f"  bitter {b:>3} Hz: published contralateral MN9 {v.mean():6.2f} Hz (SD {v.std(ddof=1):.2f}, n {len(v)})")
