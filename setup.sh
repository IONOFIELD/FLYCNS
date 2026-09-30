#!/usr/bin/env bash
# One command from a fresh clone to a ready model.
#   ./setup.sh --check   install, then run the toy regression suite (no account needed, ~5 min)
#   ./setup.sh           install, then download the connectome and annotations (needs a neuprint token)
set -e
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
command -v "$PY" >/dev/null || { echo "python3 not found; install Python 3.10 or newer"; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "Python 3.10 or newer required (found $("$PY" -V 2>&1))"; exit 1; }
command -v cc >/dev/null || command -v gcc >/dev/null || command -v clang >/dev/null \
  || { echo "a C compiler is required (macOS: xcode-select --install; Linux: sudo apt install build-essential)"; exit 1; }

echo "[1/3] python environment"
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
mkdir -p data results testdata

if [ "${1:-}" = "--check" ]; then
  echo "[2/3] toy regression suite (checks the install; no account needed)"
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
  || python fetch_malecns.py
python fetch_annotations.py
python fetch_dimorphism.py
python fit/audit_stimuli.py data
echo
echo "ready. Run ./fly and choose 4 to run the benchmark suite (~40 min)."
