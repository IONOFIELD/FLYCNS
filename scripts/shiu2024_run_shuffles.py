"""
Reference S6 runner (Gen 5, phase 1): Shiu et al. 2024's OWN code runs the same 100 weight shuffles as flycns's
A1 (fit/shiu2024_phase1.py), so the wiring control S6 can be checked on the reference itself. Registered in the
phase-1 A1 definition; run only if A1's S6 fails. Runs in the authors' environment and imports nothing from
flycns (like scripts/shiu2024_run_reference.py, whose package check it reuses).

Per shuffle k (0-99): their create_model() builds the network from their files; the synapse weights, in the
order of their connectivity file, are permuted with numpy default_rng(10000 + k) (A1 permutes the same array,
in the same order, with the same generator); their poi() adds the sugar GRNs' Poisson input at 100 Hz; one run
of their t_run (1 s). Their code sets no seed. Output: <out_dir>/s6.json with the contralateral MN9 rate per
shuffle.

    <shiu-env python> scripts/shiu2024_run_shuffles.py <shiu_repo_dir> <out_dir> [n_proc]
"""
import json
import os
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shiu2024_run_reference import COMP, CON, PINNED, sugar_ids, versions  # noqa: E402

MN9_CONTRA = 720575940660219265
N_SHUFFLES, RATE_HZ, SEED0 = 100, 100, 10000


def one(k, repo, sugar_idx, mn9_idx):
    """One shuffle, in a worker process (their code is imported from their folder)."""
    sys.path.insert(0, str(repo))
    import numpy as np
    from brian2 import Hz, Network
    from model import create_model, default_params, poi
    params = dict(default_params)
    params["r_poi"] = RATE_HZ * Hz
    neu, syn, spk_mon = create_model(str(repo / COMP), str(repo / CON), params)
    w = np.array(syn.w_[:])
    syn.w_[:] = np.random.default_rng(SEED0 + k).permutation(w)
    pois, neu = poi(neu, sugar_idx, [], params)
    net = Network(neu, syn, spk_mon, *pois)
    net.run(duration=params["t_run"])
    i = np.asarray(spk_mon.i[:])
    return float((i == mn9_idx).sum() / float(params["t_run"]))


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    repo, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    n_proc = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    v = versions()
    if v != PINNED:
        raise SystemExit(f"package versions {v} differ from the registered {PINNED}; not run")
    # the inputs must be the registered ones (the A0 registration's sha256 and commit)
    import hashlib
    import subprocess
    ref = json.loads((Path(__file__).resolve().parents[1] / "results/shiu2024_a0/registration_v4.json")
                     .read_text(encoding="utf-8"))["criteria"]["reference"]
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    bad = [] if head == ref["commit"] else [f"commit {head} is not {ref['commit']}"]
    for rel in (COMP, CON, "figures.ipynb", "model.py"):
        if hashlib.sha256((repo / rel).read_bytes()).hexdigest() != ref["sha256"][rel]:
            bad.append(f"{rel} differs from the registration")
    if bad:
        raise SystemExit("reference inputs differ from the registration: " + "; ".join(bad))
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    import pandas as pd
    from joblib import Parallel, delayed
    index = {int(i): n for n, i in enumerate(pd.read_csv(repo / COMP, index_col=0).index)}   # their brian indices
    sugar_idx, mn9_idx = [index[i] for i in sugar_ids(repo)], index[MN9_CONTRA]
    t0 = time.time()
    rates = Parallel(n_jobs=n_proc)(delayed(one)(k, repo, sugar_idx, mn9_idx) for k in range(N_SHUFFLES))
    rec = dict(mn9_contra_hz=rates, shuffles=list(range(N_SHUFFLES)), permutation=f"numpy default_rng({SEED0} + k)",
               rate_hz=RATE_HZ, versions=v, python=platform.python_version(), platform=platform.platform(),
               n_proc=n_proc, wall_s=round(time.time() - t0, 1))
    (out / "s6.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"reference shuffles done in {rec['wall_s']} s: {sum(r >= 51.4 for r in rates)} of {N_SHUFFLES} reach 51.4 Hz")


if __name__ == "__main__":
    main()
