"""
Registered reference check A0 (Gen 5, phase 1, step 1): does Shiu et al. 2024's OWN code, run here on its
own released data, reproduce the sugar -> MN9 output its authors released with it?

Why first. Phase 1 asks whether the flycns simulator reproduces Shiu et al. 2024 (Nature 634:210,
doi:10.1038/s41586-024-07763-9) as a positive control. Before flycns is compared with the published model,
the published model itself must replicate in our environment; otherwise a later difference could not be
attributed. Decision of 12 October 2026: run A0 first and stop; A1 (flycns in Shiu-compatible settings)
and M1 (the male CNS) are built only after A0 is reported.

Reference: github.com/philshiu/Drosophila_brain_model at commit 91bdd1e (MIT licence). FlyWire public
materialization v630 (127,400 neurons, 14,687,178 connections), the authors' code (model.py, run_exp,
unmodified), the cell IDs (figures.ipynb) and the output they released with the code,
results/example/sugarR_100Hz.parquet: sugar GRNs at 100 Hz, 30 trials of 1 s, contralateral MN9 67.03 Hz
(trial SD 6.71), ipsilateral MN9 48.63 Hz. Every file is pinned by sha256 (PINS) and verified before use.

Environment: Python 3.10 with the package versions of the authors' environment_full.yml (brian2 2.5.1,
numpy 1.22.3, pandas 1.4.3, pyarrow 11.0.0, scipy 1.8.1, joblib 1.2.0, Cython 0.29.33, sympy 1.12,
Jinja2 2.11.3), installed from PyPI because their file pins conda 'defaults' Windows builds; on a GitHub
Windows runner, as their environment file is a Windows one. scripts/shiu2024_run_reference.py runs their
code there and refuses any other version. Their code sets no random seed, so trials are not bit-identical
to theirs: the comparison is statistical, against their 30 released trials.

Checks (registered before the run):
  A0_S1  contralateral MN9: the 95% bootstrap interval of (our mean - their mean), two samples of 30 trials,
         lies within +/-6.7 Hz (10% of their 67.03 Hz)
  A0_S2  contralateral MN9 fires (at least one spike) in at least 29 of 30 trials (the paper: "robust
         activation of MN9 in 100% of simulations" at 100 Hz)
  A0_S3  BOTH: contralateral minus ipsilateral (paired per trial) lies above 0, AND our ipsilateral mean is
         within +/-4.86 Hz (10% of their 48.63 Hz) of theirs (two samples)

Also pre-registered here (PREREGISTERED), before any phase-1 simulation and before any archived figure
value has been seen: the phase-1 checks S1-S6 and M1, the A1 settings and the decision rule, as reviewed on
12 October 2026. The phase-1 benchmark scores them later; its registration must carry them unchanged.

Run (cloud, .github/workflows/reference.yml):
  python fit/shiu2024_reference.py check <shiu_repo>             pinned commit and file hashes; registration
  python fit/shiu2024_reference.py score <shiu_repo> <out_dir>   score A0, write results/shiu2024_a0/a0.json
  FLYCNS_REGISTER_ONLY=1 python fit/shiu2024_reference.py         write the registration (then commit it)
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import registry, stats  # noqa: E402
from flycns.bench import provenance  # noqa: E402
from flycns.integrity import require_clean  # noqa: E402

LABEL = "shiu2024_a0"
OUT = Path("results") / LABEL
REPO_URL = "https://github.com/philshiu/Drosophila_brain_model"
COMMIT = "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
PINS = {
    "2023_03_23_completeness_630_final.csv": "e6b71e17671a9bdb05f55e4bc6774640a1418cb7a05125e0fc994ad40f9bfdfb",
    "2023_03_23_connectivity_630_final.parquet": "94db8c650533bc36ffa3223f2e62325d5648b8d6bd31c3a4e1c804628c7557b3",
    "results/example/sugarR_100Hz.parquet": "93722ec03c3faa5a85790d77ed16bdd7f1e38a7c847ed0bc3af3dc2e4d0c3d34",
    "model.py": "fc45837d7122c6ce2a7f3f2f23c515992e4b232aadb919efabb72337fac88e4e",
    "utils.py": "f378cf0b464f2ac5e1daf3609ba25fd51c7e34f294846281707ffe006c3e9ef1",
    "figures.ipynb": "33cd73c0b4b4a291c51b7bab639c4fa28978e49e111ff0d6adbca5687addb84c",
    "environment_full.yml": "402fcef4968c99397b0e908b3323ab9e6ef86af5583e46e6427f96f3d1091adf",
}
MN9_CONTRA, MN9_IPSI = 720575940660219265, 720575940645521262   # contralateral to the stimulated GRNs
N_TRIALS, T_RUN_S = 30, 1.0
PUBLISHED = dict(contra_mean_hz=67.03, contra_sd_hz=6.71, ipsi_mean_hz=48.63, grn_mean_hz=99.0,
                 neurons_active=404, file="results/example/sugarR_100Hz.parquet")
BAND_CONTRA = 6.7                    # 10% of 67.03 Hz, rounded
BAND_IPSI = 4.86                     # 10% of 48.63 Hz, rounded
RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "shiu2024_run_reference.py"

# Phase-1 checks, pre-registered now (reviewed 12 October 2026). Scored by the phase-1 benchmark later.
PREREGISTERED = dict(
    data=("FlyWire v630 from the pinned reference repository (PINS); sugar, bitter and MN9 ids from its "
          "figures.ipynb; the per-neuron sign is the repository's Excitatory column (Shiu's rule: GABA and "
          "glutamate inhibitory; acetylcholine and the amines excitatory), mapped onto graph.SIGN_MAP labels"),
    a1_settings=dict(reset="v and g reset at a spike; g frozen while refractory",
                     stimulation="stimulated cells stay in the network; Poisson input of 250 x w_syn per event, refractory 0",
                     min_weight=1, w_scale=1.0, amines="excitatory (the repository's sign column)",
                     adaptation="none", electrical=False, peptides=False, dt_ms=0.1, trial_ms=1000, trials=30),
    checks=dict(
        S1_sugar_mn9_magnitude=("sugar GRNs (21 ids) at 100 Hz, 30 trials: the 95% bootstrap interval of (our "
                                "contralateral MN9 mean - the published 30 trials' mean) lies within +/-6.7 Hz"),
        S2_reliability="contralateral MN9 fires (>= 1 spike) in at least 29 of 30 trials",
        S3_laterality=("BOTH: contralateral minus ipsilateral (paired per trial) above 0, AND ipsilateral within "
                       "+/-4.86 Hz of the published 48.63 Hz (two samples)"),
        S4_calibration_reproduced=("MN9 at 100 Hz divided by the maximum of the MN9 means at 50, 100, 150 and "
                                   "200 Hz (30 trials each), 95% bootstrap interval within [0.7, 0.9] (the paper: "
                                   "W_syn chosen so that 100 Hz gives 'roughly 80% of maximal MN9 firing')"),
        S5_bitter_suppression=("sugar GRNs at 100 Hz plus bitter GRNs (21 ids, figures.ipynb) at 0, 50, 100, 150 "
                               "and 200 Hz, 30 trials each. PASS if BOTH: the 95% bootstrap interval of "
                               "MN9(sugar 100 + bitter 100) - MN9(sugar 100 + bitter 0) lies below 0, AND the 95% "
                               "bootstrap interval of the Spearman rank correlation between bitter rate and "
                               "per-trial contralateral MN9 rate (150 trials) lies below 0. FAIL if either "
                               "interval lies wholly at or above 0; UNRESOLVED otherwise. Qualitative, from the "
                               "paper's text. If the authors' archived Fig 3a values become available, a "
                               "quantitative S5b is registered separately before it is scored; S5 is never changed"),
        S6_wiring_control=("100 weight shuffles keeping the global weight distribution (as the paper), 1 trial "
                           "each, sugar at 100 Hz. A shuffle 'activates MN9' if its contralateral MN9 rate reaches "
                           "T = 51.4 Hz. Derivation: T is the 1st percentile of a normal fit to the 30 released "
                           "real-wiring trials (mean 67.03, SD 6.71 Hz; their minimum is 53 Hz), i.e. a rate the "
                           "real wiring reaches in 99% of trials. PASS if at most 5 of 100 shuffles activate MN9 "
                           "(the paper: 1 of 100; if the true probability were 1%, 6 or more of 100 would occur "
                           "with probability below 0.001); FAIL otherwise"),
        M1_male_mn9=("MaleCNS under the A1 settings, the sugar set and MN9 readout of flycns check F3 (LB3b and "
                     "LB3c at 100 Hz), 30 trials: MN9 'responds' if the 95% bootstrap interval of its rate lies "
                     "above 0.5 Hz (the F3 band)"),
    ),
    ladder=("L1-L6, reported and not scored: from A1, one setting switched to its flycns value at a time "
            "(reset, stimulation, connection floor 5, w_scale 0.4, motor adaptation), then all together"),
    decision_rule=("A0 fails: the reference does not reproduce here; stop. A0 passes and A1 fails: flycns "
                   "differs beyond the listed settings; bisect first. A1 passes and M1 responds: the male MN9 "
                   "zero is caused by flycns settings (the ladder names which). A1 passes and M1 does not "
                   "respond: the male zero is wiring or annotation, not the simulator"),
)

CRITERIA = dict(
    question=("does Shiu et al. 2024's own code, on its own released data and in its own package versions, "
              "reproduce its released sugar -> MN9 output when run here?"),
    reference=dict(repository=REPO_URL, commit=COMMIT, licence="MIT", sha256=PINS, published=PUBLISHED),
    environment=dict(python="3.10", packages="scripts/shiu2024_run_reference.py PINNED (environment_full.yml "
                     "versions, from PyPI)", runner="GitHub windows-latest", seeds="none (their code sets none)"),
    protocol=dict(stimulus="the 21 sugar GRNs of figures.ipynb (first neu_sugar list) at 100 Hz (their r_poi)",
                  trials=N_TRIALS, trial_s=T_RUN_S, code="their run_exp, unmodified, n_proc = all cores",
                  readout="spikes per trial of MN9 720575940660219265 (contralateral) and 720575940645521262"),
    checks={
        "A0_S1_mn9_contra_magnitude": dict(band=[-BAND_CONTRA, BAND_CONTRA], rule=(
            "the 95% percentile-bootstrap interval (flycns.stats.bootstrap_diff, seed 0) of our contralateral MN9 "
            "mean minus the published 30 trials' mean lies within +/-6.7 Hz: PASS; wholly outside: FAIL; else "
            "UNRESOLVED")),
        "A0_S2_mn9_reliability": dict(rule="contralateral MN9 fires in at least 29 of 30 trials (a count, no interval)"),
        "A0_S3_laterality": dict(bands=[[0.0, None], [-BAND_IPSI, BAND_IPSI]], rule=(
            "BOTH parts: contralateral minus ipsilateral per trial, 95% bootstrap interval above 0; our ipsilateral "
            "mean minus the published one, 95% bootstrap interval within +/-4.86 Hz")),
    },
    reported=["GRN mean rate (published 99.0 Hz)", "neurons active (published 404)", "package versions and engine"],
    decision="A0 passes only if all three checks PASS; then phase 1 continues with A1 and M1 after review",
    preregistered_phase1=PREREGISTERED,
)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_reference(repo):
    """The reference repository is the registered commit and every pinned file is byte-identical."""
    repo = Path(repo)
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()
    bad = [] if head == COMMIT else [f"commit {head or '?'} is not the registered {COMMIT}"]
    for rel, want in PINS.items():
        p = repo / rel
        got = sha256(p) if p.exists() else None
        if got != want:
            bad.append(f"{rel}: sha256 {got} != registered {want}")
    if bad:
        raise SystemExit("[shiu2024_a0] reference inputs differ from the registration:\n  " + "\n  ".join(bad))
    print(f"[shiu2024_a0] reference verified: {COMMIT[:7]}, {len(PINS)} files byte-identical to the registration")


def per_trial(parquet, neuron):
    import pandas as pd
    d = pd.read_parquet(parquet, columns=["trial", "flywire_id"])
    n_trials = int(d["trial"].max()) + 1 if len(d) else 0
    counts = d[d.flywire_id == neuron].groupby("trial").size().reindex(range(max(n_trials, N_TRIALS)), fill_value=0)
    return counts.to_numpy(dtype=float) / T_RUN_S, d


REG = registry.register(LABEL, CRITERIA, scripts=[__file__, RUNNER])     # exits here under FLYCNS_REGISTER_ONLY
require_clean(LABEL)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "check" and len(sys.argv) > 2:
        verify_reference(sys.argv[2])
    elif mode == "score" and len(sys.argv) > 3:
        repo, out_dir = Path(sys.argv[2]), Path(sys.argv[3])
        verify_reference(repo)
        ours_parquet = out_dir / "A0_sugarR_100Hz.parquet"
        meta = json.loads((out_dir / "A0_meta.json").read_text(encoding="utf-8"))
        oc, od = per_trial(ours_parquet, MN9_CONTRA)
        oi, _ = per_trial(ours_parquet, MN9_IPSI)
        tc, td = per_trial(repo / PUBLISHED["file"], MN9_CONTRA)
        ti, _ = per_trial(repo / PUBLISHED["file"], MN9_IPSI)
        if len(oc) != N_TRIALS or int(od["trial"].nunique()) > N_TRIALS:
            raise SystemExit(f"[shiu2024_a0] expected {N_TRIALS} trials, found {len(oc)}")
        e, lo, hi = stats.bootstrap_diff(oc, tc)
        s1 = stats.scored(e, lo, hi, low=-BAND_CONTRA, high=BAND_CONTRA, method="bootstrap, two samples of 30 trials",
                          n=N_TRIALS, note="our contralateral MN9 mean minus the published one, Hz")
        k = int((oc > 0).sum())
        s2 = stats.point(k, k >= 29, method="count: trials with a contralateral MN9 spike, of 30; at least 29 required")
        e1, lo1, hi1 = stats.bootstrap(oc - oi)
        e2, lo2, hi2 = stats.bootstrap_diff(oi, ti)
        s3 = stats.combine([stats.scored(e1, lo1, hi1, low=0.0, strict=True, n=N_TRIALS,
                                         note="contralateral minus ipsilateral MN9, paired per trial, Hz"),
                            stats.scored(e2, lo2, hi2, low=-BAND_IPSI, high=BAND_IPSI, n=N_TRIALS,
                                         method="bootstrap, two samples of 30 trials",
                                         note="our ipsilateral MN9 mean minus the published one, Hz")],
                           note="laterality, and the ipsilateral magnitude")
        uncertainty = {"A0_S1_mn9_contra_magnitude": s1, "A0_S2_mn9_reliability": s2, "A0_S3_laterality": s3}
        registry.verify_bands(REG, uncertainty)
        sugar = set(meta["sugar_ids"])
        grn = lambda d: float(d[d.flywire_id.isin(sugar)].groupby("flywire_id").size().mean() / N_TRIALS / T_RUN_S)  # noqa: E731
        reported = dict(
            mn9_contra_hz=dict(ours=float(np.mean(oc)), ours_sd=float(np.std(oc, ddof=1)), published=float(np.mean(tc)),
                               published_sd=float(np.std(tc, ddof=1)), ours_per_trial=oc.tolist()),
            mn9_ipsi_hz=dict(ours=float(np.mean(oi)), published=float(np.mean(ti)), ours_per_trial=oi.tolist()),
            sugar_grn_mean_hz=dict(ours=grn(od), published=grn(td)),
            neurons_active=dict(ours=int(od.flywire_id.nunique()), published=int(td.flywire_id.nunique())),
            spikes_per_trial=dict(ours=len(od) / N_TRIALS, published=len(td) / N_TRIALS),
            run=meta)
        verdicts = {k: v["verdict"] for k, v in uncertainty.items()}
        report = dict(benchmark=LABEL, criteria=CRITERIA, checks={k: v == "PASS" for k, v in verdicts.items()},
                      uncertainty=uncertainty, reported=reported,
                      a0_passes=all(v == "PASS" for v in verdicts.values()),
                      registration=registry.stamp(REG), provenance=provenance())
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "a0.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
        print(f"contralateral MN9: ours {np.mean(oc):.2f} Hz vs published {np.mean(tc):.2f} Hz "
              f"(difference {e:+.2f}, 95% CI {lo:+.2f} to {hi:+.2f}); ipsilateral ours {np.mean(oi):.2f} vs "
              f"{np.mean(ti):.2f}; fired in {k}/30 trials")
        for name, v in verdicts.items():
            print(f"  {v:<10} {name}")
        print("A0 " + ("PASSES: the published model replicates here" if report["a0_passes"] else
                       "does NOT pass: stop and report before building A1/M1"))
    else:
        raise SystemExit(__doc__)
