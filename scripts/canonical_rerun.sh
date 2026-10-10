#!/usr/bin/env bash
# One command, on the computer that holds the connectome (macOS or Linux Terminal, not PowerShell):
#   1. update the code and the environment, refresh annotations (./setup.sh)
#   2. pin the input data: commit data/MANIFEST.json the first time it is written
#   3. rerun the core suite canonically, so its reports carry the integrity stamp
#   4. run the registered stricter null (benchmarks/null_strict.py)
#   5. commit the results and push them
# About 1 to 1.5 hours. On a Mac it keeps the computer awake until it finishes.
#
#   scripts/canonical_rerun.sh            (also menu option 51)
set -euo pipefail
cd "$(dirname "$0")/.."

# keep a Mac awake for the whole run (variable deliberately not FLYCNS_*, which would be stamped as an override)
if [ -z "${_CANON_AWAKE:-}" ] && command -v caffeinate >/dev/null 2>&1; then
  export _CANON_AWAKE=1
  exec caffeinate -i "$0" "$@"
fi

stop () { echo; echo "STOPPED: $*"; echo "Nothing was pushed. Send Claude the lines above."; exit 1; }

echo "[1/5] update code, environment and annotations"
git pull --ff-only || stop "git pull could not fast-forward (local changes or a diverged branch)."
./setup.sh || stop "setup did not finish (see its message above)."
source .venv/bin/activate

echo "[2/5] pin the input data"
if ! git ls-files --error-unmatch data/MANIFEST.json >/dev/null 2>&1; then
  git add data/MANIFEST.json
  git commit -qm "pin input data: data/MANIFEST.json (male-cns:v1.0, fetched $(date +%F))"
  echo "  committed data/MANIFEST.json"
else
  echo "  already pinned; setup.sh verified the data against it"
fi
python - <<'PY' || stop "code differs from the last commit; registered tests would refuse to run."
import sys
from flycns.integrity import git_state
s = git_state()
if not s["clean"]:
    print("  uncommitted code:", ", ".join(s["dirty_files"][:10]))
sys.exit(0 if s["clean"] else 1)
PY

echo "[3/5] core suite, canonical (about 40 min)"
scripts/run_all.sh 40 data || stop "the core suite did not finish."

echo "[4/5] stricter null, registered"
python benchmarks/null_strict.py data || stop "the stricter null did not finish."

echo "[5/5] commit and push"
python benchmarks/summarize.py > /dev/null
git add -A results
git commit -qm "canonical rerun of the core suite and the registered stricter null, under integrity stamping" \
  || echo "  (no result changes to commit)"
git push || stop "push failed; the results are committed locally, so just run: git push"

echo
sed -n '3,5p' results/SUITE.md
echo
echo "done: results pushed to GitHub."
