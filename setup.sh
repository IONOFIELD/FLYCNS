#!/usr/bin/env bash
# One command from a fresh clone to a ready model.
#   ./setup.sh --check   install, then run the regression test on the toy graph (no account, ~10 min)
#   ./setup.sh           install, then download the connectome and annotations (needs a neuprint token)
#
# Environment: Python 3.12 or newer installs the REFERENCE environment, every package pinned in
# requirements.lock (the exact set CI tests). Python 3.10 or 3.11 installs the newest compatible
# versions from requirements.txt instead; that works, but reports from it are not bit-for-bit
# reproducible and say so (every report records the library versions it ran with).
set -e
cd "$(dirname "$0")"

PY=${PYTHON:-}
if [ -z "$PY" ]; then
  for c in python3.12 python3.13 python3; do command -v "$c" >/dev/null && { PY=$c; break; }; done
fi
[ -n "$PY" ] || { echo "python3 not found; install Python 3.12 (or 3.10 or newer)"; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "Python 3.10 or newer required (found $("$PY" -V 2>&1)); 3.12 recommended"; exit 1; }
command -v cc >/dev/null || command -v gcc >/dev/null || command -v clang >/dev/null \
  || { echo "a C compiler is required (macOS: xcode-select --install; Linux: sudo apt install build-essential)"; exit 1; }

echo "[1/3] python environment ($("$PY" -V 2>&1))"
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
if python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
  pip install -q -r requirements.lock
  echo "  reference environment: every package pinned (requirements.lock)"
else
  pip install -q -r requirements.txt
  echo "  NOTE: Python $(python -V 2>&1 | cut -d' ' -f2) is below 3.12, so packages are NOT pinned."
  echo "        It works, but for the reference environment install Python 3.12 and rerun after: rm -rf .venv"
fi
mkdir -p data results

if [ "${1:-}" = "--check" ]; then
  echo "[2/3] regression test on the toy graph (checks the install; no account needed)"
  python tests/regression.py
  echo "install works. For the real connectome: put your neuprint token in ~/.neuprint_token, then ./setup.sh"
  exit 0
fi

echo "[2/3] neuprint token"
if [ ! -s ~/.neuprint_token ]; then
  echo "  no token at ~/.neuprint_token"
  echo "  get a free one at https://neuprint.janelia.org (log in, then Account), then:"
  echo "    echo 'YOUR_TOKEN' > ~/.neuprint_token && ./setup.sh"
  exit 1
fi
export NEUPRINT_TOKEN="$(tr -d '[:space:]' < ~/.neuprint_token)"

echo "[3/3] connectome and annotations"
[ -s data/neurons.parquet ] && [ -s data/edges.parquet ] && echo "  connectome already present, skipping download" \
  || python scripts/fetch_malecns.py
python scripts/fetch_annotations.py
python scripts/fetch_dimorphism.py
python fit/audit_stimuli.py data

echo
if [ -f data/MANIFEST.json ]; then
  echo "checking the data against the committed fingerprint (data/MANIFEST.json)"
  if ! python -m flycns.integrity verify data; then
    echo
    echo "  The downloaded tables differ from the ones the committed results were produced on."
    echo "  Registered tests will refuse to run until this is resolved. Most likely the dataset was"
    echo "  updated on neuprint. Review what changed before rewriting the manifest."
    exit 1
  fi
else
  python -m flycns.integrity write data
  echo "  First fetch on this checkout: the fingerprint above pins these tables. Commit it so every"
  echo "  later fetch, on any machine, is checked against it:  git add data/MANIFEST.json && git commit"
fi
echo
echo "ready. Run ./fly and choose 4 to run the benchmark suite (~40 min)."
