"""
A0 runner (Gen 5, phase 1): Shiu et al. 2024's OWN code on its OWN released data, unmodified, in the
package versions of its authors' environment. It runs in a separate Python environment and imports
nothing from flycns. The registered check, its criteria and its scoring are in fit/shiu2024_reference.py,
which also verifies every input file by sha256 before this runs.

    <shiu-env python> scripts/shiu2024_run_reference.py <shiu_repo_dir> <out_dir> [n_proc]

Writes <out_dir>/A0_sugarR_100Hz.parquet (their run_exp output format: one row per spike) and
<out_dir>/A0_meta.json (package versions, platform, engine, wall time, the stimulated ids).
"""
import ast
import json
import os
import platform
import sys
import time
from pathlib import Path

# the versions of the authors' environment_full.yml (installed from PyPI; their file pins conda builds)
PINNED = {"brian2": "2.5.1", "numpy": "1.22.3", "pandas": "1.4.3", "pyarrow": "11.0.0", "scipy": "1.8.1",
          "joblib": "1.2.0", "Cython": "0.29.33", "sympy": "1.12", "Jinja2": "2.11.3"}
EXP = "A0_sugarR_100Hz"
RATE_HZ = 100
COMP = "2023_03_23_completeness_630_final.csv"
CON = "2023_03_23_connectivity_630_final.parquet"


def versions():
    import importlib.metadata as md
    out = {}
    for k in PINNED:
        try:
            out[k] = md.version(k)
        except md.PackageNotFoundError:
            out[k] = None
    return out


def sugar_ids(repo):
    """The labellar sugar GRNs exactly as the authors list them: the first `neu_sugar = [...]` in
    figures.ipynb (its Figure 1 cell), read as a Python literal."""
    nb = json.loads((repo / "figures.ipynb").read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code" and "neu_sugar = [" in src:
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "neu_sugar" for t in node.targets):
                    return [int(x) for x in ast.literal_eval(node.value)]
    raise SystemExit("figures.ipynb: no neu_sugar list found")


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    repo, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    n_proc = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    v = versions()
    if v != PINNED:
        raise SystemExit(f"package versions {v} differ from the registered {PINNED}; A0 not run")
    ids = sugar_ids(repo)
    if len(ids) != 21:
        raise SystemExit(f"expected 21 sugar GRNs, found {len(ids)}")
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(repo)                          # their code is run from its own folder, as their notebooks do
    sys.path.insert(0, str(repo))
    from brian2 import Hz, prefs           # noqa: E402
    from model import default_params, run_exp   # noqa: E402  (their model.py, unmodified)
    try:
        from brian2.codegen.runtime.cython_rt import CythonCodeObject
        cython_ok = bool(CythonCodeObject.is_available())
    except Exception as e:                 # recorded, not fatal: their code runs on either engine
        cython_ok = f"unknown ({e})"
    params = dict(default_params)
    params["r_poi"] = RATE_HZ * Hz
    if params["n_run"] != 30:
        raise SystemExit(f"their default n_run is {params['n_run']}, not 30")
    t0 = time.time()
    run_exp(exp_name=EXP, neu_exc=ids, path_res=str(out), path_comp=str(repo / COMP), path_con=str(repo / CON),
            params=params, n_proc=n_proc, force_overwrite=True)
    meta = dict(exp_name=EXP, rate_hz=RATE_HZ, n_run=int(params["n_run"]), t_run_s=float(params["t_run"]),
                sugar_ids=ids, versions=v, python=platform.python_version(), platform=platform.platform(),
                cpu_count=os.cpu_count(), n_proc=n_proc, codegen_target=str(prefs.codegen.target),
                cython_available=cython_ok, wall_s=round(time.time() - t0, 1))
    (out / "A0_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"A0 done in {meta['wall_s']} s: {out / (EXP + '.parquet')}")


if __name__ == "__main__":
    main()
