"""
Registered check S4b (Gen 5, phase 1): the sugar dose curve, point by point, against the authors' own published
values. Registered separately from S4 (pre-registered in results/shiu2024_a0/), which is never changed. Scored
later by the phase-1 benchmark (A1: flycns in Shiu-compatible settings on FlyWire v630); this file records the
criterion and the reference values before any A1 run exists.

Why a second check. S4 asks whether MN9 at 100 Hz is 70-90% of the maximum over 50, 100, 150 and 200 Hz (the
paper: W_syn was chosen so that 100 Hz gives "roughly 80% of maximal MN9 firing"). Scored on the authors' own
Fig 1 output, S4 is UNRESOLVED: 65.70 / 93.23 = 0.705, 95% bootstrap interval 0.686-0.724 (10,000 resamples,
seed 0; their results/example copy of the 100 Hz run gives 0.719, 0.690-0.749). So S4 cannot pass even for a
perfect reproduction; it is kept as registered and reported with that note. S4b asks the question S4 was meant
to ask - is the published dose calibration reproduced - on the same runs.

Reference values: reference-data/shiu2024/ (pinned in fit/shiu2024_s5b.py and again below), extracted from
Shiu et al.'s Edmond results.zip by scripts/extract_shiu_archive.py (ff2dc9a). The CSV has no file column; its
rows are 30 per file in the sorted order of the manifest's file list, which is how each row is traced to its
file here (and checked against the experiment and rates in the row). The Fig 1 files are
results/figure_1/data/sugarR_<f>Hz.parquet; results/example/sugarR_100Hz.parquet (the copy A0 and S1 use) is not
part of the Fig 1 series and is not used here.

Published contralateral MN9, sugar GRNs alone (Fig 1 files, 30 trials each), Hz:
  sugar   50     100    150    200
  mean    19.43  65.70  83.67  93.23

S4b (registered here): A1 settings, sugar GRNs at 50, 100, 150 and 200 Hz, 30 trials each (S4's own runs; no new
arms). At every one of the 4 points, the 95% bootstrap interval of (our contralateral MN9 mean - the published
mean, two samples of 30 trials) lies within +/-6.7 Hz: PASS. Any point wholly outside: FAIL. Otherwise
UNRESOLVED. Margin and rule are S5b's: 10% of the published sugar-alone rate (67.0 Hz), as an absolute margin.

    FLYCNS_REGISTER_ONLY=1 python fit/shiu2024_s4b.py      write the registration (then commit it)
    python fit/shiu2024_s4b.py                             verify the pinned reference and print it
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import registry  # noqa: E402
from flycns.integrity import require_clean  # noqa: E402

LABEL = "shiu2024_s4b"
ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference-data" / "shiu2024"
PINS = {"shiu_archive_mn9.csv": "076ca67fc5eed1a2f590fe2c84c8b77373337be8f89ed615ec6bc6e5016f8355",
        "shiu_archive_manifest.json": "2e20cbc34f97c267d4ec887ea0d5c03f95f1721fd5d2494a1325955f5bcb427e"}
EXTRACTOR = ROOT / "scripts" / "extract_shiu_archive.py"
SUGAR_POINTS = [50, 100, 150, 200]
FIG1 = "results/figure_1/data/sugarR_{}Hz.parquet"
MARGIN_HZ = 6.7

CRITERIA = dict(
    question="does flycns in Shiu-compatible settings reproduce the authors' published sugar dose curve?",
    reference=dict(archive="Edmond doi:10.17617/3.CZODIW v3, results.zip", zip_bytes=4499610373,
                   zip_md5="f6f2e314821fa6a4196214e3b2b14bc4", extractor="scripts/extract_shiu_archive.py @ ff2dc9a",
                   files_sha256=PINS, source_files=[FIG1.format(f) for f in SUGAR_POINTS],
                   readout="MN9 720575940660219265, contralateral; spikes per 1-s trial, 30 trials"),
    relation_to_S4=("separate; S4 (pre-registered in results/shiu2024_a0/) is unchanged and scores UNRESOLVED on "
                    "the authors' own Fig 1 output (0.705, 95% interval 0.686-0.724)"),
    protocol=dict(settings="A1 (results/shiu2024_a0/ preregistered_phase1.a1_settings)", sugar_hz=SUGAR_POINTS,
                  bitter_hz=0, trials_per_point=30, reuse="S4's runs (sugar 50, 100, 150 and 200 Hz); no new arms"),
    checks={"S4b_dose_curve_matches_published": dict(
        bands=[[-MARGIN_HZ, MARGIN_HZ]] * len(SUGAR_POINTS),
        rule=("at each of sugar 50, 100, 150 and 200 Hz, the 95% bootstrap interval (two samples of 30 trials) of "
              "our contralateral MN9 mean minus the published mean lies within +/-6.7 Hz: PASS if all 4 do; FAIL "
              "if any lies wholly outside; UNRESOLVED otherwise"),
        margin_derivation="S5b's: 10% of the published sugar-alone rate (67.0 Hz), as an absolute margin")},
)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def published():
    """The published per-trial counts of the Fig 1 dose files, by sugar rate (verified against the pins first,
    and each block of 30 rows traced to its file through the manifest's sorted file list)."""
    bad = [f"{n}: {sha256(REF / n) if (REF / n).exists() else None} != {h}" for n, h in PINS.items()
           if not (REF / n).exists() or sha256(REF / n) != h]
    if bad:
        raise SystemExit("[shiu2024_s4b] reference files differ from the registration: " + "; ".join(bad))
    import pandas as pd
    names = list(json.loads((REF / "shiu_archive_manifest.json").read_text(encoding="utf-8"))["files"])
    d = pd.read_csv(REF / "shiu_archive_mn9.csv")
    if names != sorted(names) or len(d) != 30 * len(names):
        raise SystemExit("[shiu2024_s4b] the CSV rows cannot be traced to the manifest's files")
    d["source"] = [names[i // 30] for i in range(len(d))]
    for n, g in d.groupby("source"):
        m = re.search(r"sugarR_(\d+)Hz\.parquet$", n)
        if m and not (set(g.experiment) == {"sugar_dose"} and set(g.sugar_hz) == {int(m.group(1))}):
            raise SystemExit(f"[shiu2024_s4b] rows traced to {n} do not match its name")
    return {f: d[d.source == FIG1.format(f)].sort_values("trial").mn9_contra.to_numpy(dtype=float)
            for f in SUGAR_POINTS}


REG = registry.register(LABEL, CRITERIA, scripts=[__file__, EXTRACTOR])     # exits here under FLYCNS_REGISTER_ONLY
require_clean(LABEL)

if __name__ == "__main__":
    for f, v in published().items():
        print(f"  sugar {f:>3} Hz: published contralateral MN9 {v.mean():6.2f} Hz (SD {v.std(ddof=1):.2f}, n {len(v)})")
