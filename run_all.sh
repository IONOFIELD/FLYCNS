#!/usr/bin/env bash
# One-command repeatable build: all benchmarks, suite summary, 3D cascade.
# Usage: ./run_all.sh [n_trials] [data_dir]
set -e
source .venv/bin/activate 2>/dev/null || true
N=${1:-40}; D=${2:-data}
# refuse to start if any benchmark's stimulus set resolves to no neurons (see fit/audit_stimuli.py)
python fit/audit_stimuli.py "$D" || { echo "stimulus audit failed: fix the lists above before running"; exit 1; }
python benchmarks/gf_escape.py "$N" "$D"
python benchmarks/auditory.py "$N" "$D"
python benchmarks/feeding.py 6 "$D" || echo "feeding benchmark did not complete (see above)"
python benchmarks/summarize.py
python viz/cascade_3d.py "" "$D" || true
echo; echo "suite summary: results/SUITE.md    3D: results/gf_escape/cascade_3d.html"
echo "terminal anatomy animation:  python viz/cascade_ascii.py          (add --path for route only)"
