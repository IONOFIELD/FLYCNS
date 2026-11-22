# Phase A re-score record (Windows)

Date: 2026-11-18. Read-only check: nothing committed, the scorer's rewrite of
`results\gen6_phaseA\phaseA.json` was reverted with `git checkout --` after copying.

## Environment

- Commit: `c1e6e6244570b47ad799bca092fda985ced9a6d4` (branch `gen6/phaseA-decisions`, up to date with origin)
- Python: 3.12.10 (tags/v3.12.10:0cc8128, Apr 8 2025) [MSC v.1943 64 bit (AMD64)], `.venv\Scripts\python.exe`
- OS: Windows 11 Home, `Windows-11-10.0.26200-SP0`
- Packages the scorer imports (directly, or via `flycns.registry`/`flycns.stats`): numpy 2.5.3, scipy 1.18.1, pandas 3.0.6, pyarrow 26.0.0
- Full venv: asciitree 0.3.3, Brian2 2.10.1, certifi 2026.7.22, charset-normalizer 3.5.2, colorama 0.4.6,
  contourpy 1.4.0, cycler 0.12.1, Cython 3.1.3, flexcache 0.3, flexparser 0.4, fonttools 4.66.1, fuzzywuzzy 0.18.0,
  h5py 3.16.0, idna 3.20, igraph 1.0.0, Jinja2 3.1.6, kiwisolver 1.5.1, MarkupSafe 3.0.4, matplotlib 3.11.2,
  molesq 0.4.0, morphops 0.2.0, mpmath 1.3.0, narwhals 2.27.1, navis 1.12.0, ncollpyde 0.19.0, networkx 3.7,
  neuprint-python 0.6.4, numpy 2.5.3, packaging 26.3, pandas 3.0.6, pillow 12.3.0, Pint 0.26.1, pip 26.2.1,
  platformdirs 4.12.4, plotly 7.1.0, py-cpuinfo 9.0.0, pyarrow 26.0.0, pykdtree 1.4.3, pynrrd 1.1.3, pyparsing 3.3.3,
  pypng 0.20220715.0, python-dateutil 2.9.0.post0, rdata 1.1.0, requests 2.34.2, scipy 1.18.1, seaborn 0.13.2,
  setuptools 84.0.0, six 1.17.0, skeletor 1.7.1, sympy 1.14.0, temporaldata 0.1.6, texttable 1.7.0, tqdm 4.70.1,
  trimesh 5.1.1, typing_extensions 4.16.0, tzdata 2026.5, ujson 6.0.0, urllib3 2.8.0, xarray 2026.9.0

## How it was run

`.venv\Scripts\python.exe fit\gen6_phaseA_score.py` (no flags, `FLYCNS_ALLOW_DIRTY` not set).

The first attempt was refused by the integrity guard because an untracked code file from an earlier
session, `explore\density\density.py`, counts as uncommitted code. Instead of waiving the guard, that file
was moved out of the repository for the duration of the run and put back afterwards (sha256 unchanged).
The scored run therefore ran on a tree whose only change was untracked non-code files under `explore\`.

Scorer output: B1 = C (no deciding cell viable); A3 PASS (real 23.98, exceeds 100 of 100);
A4 W* [0.5, 0.6, 0.8, 1.0], cuts stop: lh False, lhmb False, i True, ii True; predictions Q1 F, Q2 T, Q3 F, Q4 T, Q5 T, Q6 T.

## Comparison

`compare.py` flattens both JSON documents to leaf paths and compares type and value exactly (no tolerance).

- Leaf values compared: **5,404** (5,404 in each file, same path set)
- Differing paths: **0**
  - Provenance fields (timestamps, git or machine stamps): **0**
  - Results fields: **0**

The record has no per-run timestamp or machine stamp. Its only provenance block, `registration`
(`registration_v5.json`, git_commit `ff816c1`, model_hash `dcb44bf0…dcb8`, registered_at `2026-10-18T08:31:14`,
matches true), is read from the registration and is identical in both files.

### Byte-level difference

The files are not byte-identical, only because of line endings: the committed file uses LF
(9,523 lines, 236,851 bytes); the Windows rerun writes CRLF (9,523 lines, 246,374 bytes). After CRLF→LF the
two are byte-identical. `.gitattributes` has `*.json text eol=lf`, so git treats this as no content change
(`git diff --stat` empty, only a CRLF→LF warning).

## sha256

| File | sha256 |
|---|---|
| `explore\rescore\phaseA_committed.json` | `c761a7160df08cd5072af2f5c08eca8092bcbd8bfcef56dfdc683c195238e99b` |
| `explore\rescore\phaseA_windows.json` | `5850307263939bdeef2d9b4282ee9bb067272a954da577a4bcb7684b1306e0f8` |
