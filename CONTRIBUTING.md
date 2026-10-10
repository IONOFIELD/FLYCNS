# Rules of the house

These rules keep a result traceable to the exact code, data and settings that produced it, for as
long as the repository exists. CI enforces the ones marked **(CI)**. The code refuses to run when
the ones marked **(guard)** are broken.

## Parameters
1. Every value in the model is either cited to a measurement or chosen by a stated rule. A chosen value goes in `docs/CALIBRATION.md`, with the rule and the checks it touches. When a value changes, the reason stays in the code beside it.
2. Every scored check has a role in `flycns/calibration.py`: calibrated, construction, independent, control or robustness. **(CI)** Only independent checks count as tests of the model.

## Claims
3. A new claim is **registered**. Its criteria are written in the script and committed before the first run. The script writes `results/<name>/criteria.json`, stamped with the commit, and refuses to run if the criteria later differ. Follow the pattern in `benchmarks/pc1_song.py`.
4. A registered test runs only on committed code. **(guard)** `FLYCNS_ALLOW_DIRTY=1` overrides this for throwaway runs, and the report is stamped dirty.
5. Never edit the criteria of a registered test. Write a new registered test instead. Report failures as failures, and keep retractions in `RESULTS.md`.

## Data
6. The input tables are pinned by `data/MANIFEST.json`. Registered tests and the suite refuse to run on data that differ from it. **(guard)** If the connectome is deliberately refetched:
   - review what changed with `python -m flycns.integrity verify`;
   - rewrite the manifest with `python -m flycns.integrity write`;
   - commit it on its own, with the reason in the commit message;
   - rerun the suite.

## Settings
7. Robustness variants run through `FLYCNS_*` environment variables. Each one is announced in a banner, stamped into the report, and flagged PERTURBED in `results/SUITE.md`. The battery (`scripts/overnight.sh`) restores the canonical results when it finishes.

## Verification
8. `python tests/regression.py` must pass. Run it on a fresh clone, because local state hides missing files. **(CI)** It runs on every push, on Linux and macOS, with the pinned reference environment and with the oldest supported Python.
9. Dependencies change only through `requirements.lock`, regenerated with:
   `uv pip compile requirements.txt --universal --python-version 3.12 -o requirements.lock`
   Then let CI confirm the new lock on every platform before merging.
