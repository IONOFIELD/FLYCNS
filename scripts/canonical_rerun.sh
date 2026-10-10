#!/usr/bin/env bash
# One command, on the computer that holds the connectome (macOS or Linux Terminal, not PowerShell):
#   1. update the code and the environment, refresh annotations (./setup.sh)
#   2. pin the input data: commit data/MANIFEST.json the first time it is written
#   3. rerun the core suite canonically, so its reports carry the integrity stamp
#   4. run the registered stricter null (benchmarks/null_strict.py)
#   5. commit the results and push them
# About 1 to 1.5 hours. On a Mac it keeps the computer awake until it finishes.
# Safe to run again after an interruption: leftover result files are set aside (git stash, recoverable)
# and a data-pin commit from the earlier run is replayed on top of the latest code.
#
#   scripts/canonical_rerun.sh            (also menu option 51)
#
# The whole script is one function, read completely before anything runs, because step 1 can replace
# this very file; after updating, it restarts from the new copy. Helper variables are deliberately not
# named FLYCNS_*, which would be stamped into every report as a settings override.
set -euo pipefail

main () {
  cd "$(dirname "$0")/.."

  # keep a Mac awake for the whole run
  if [ -z "${_CANON_AWAKE:-}" ] && command -v caffeinate >/dev/null 2>&1; then
    export _CANON_AWAKE=1
    exec caffeinate -i "$0" "$@"
  fi

  if [ -z "${_CANON_UPDATED:-}" ]; then
    echo "[1/5] update code"
    # result files left by an interrupted run would block the pull; they are regenerated below, so
    # set them aside (recoverable) rather than discard them. Code changes are never touched.
    if [ -n "$(git status --porcelain --untracked-files=no -- results)" ]; then
      git stash push -q -m "canonical_rerun $(date +%F_%H%M): local result files set aside" -- results
      echo "  set aside uncommitted result files from an earlier run (recover: git stash list, git stash pop)"
    fi
    git pull --rebase -q || stop "git pull failed (uncommitted code changes, or a conflict)."
    export _CANON_UPDATED=1
    exec "$0" "$@"            # restart from the updated copy of this script
  fi

  echo "[1/5] environment and annotations"
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
  git push -q || stop "push failed; everything is committed locally, so just run: git push"

  echo
  sed -n '3,5p' results/SUITE.md
  echo
  echo "done: results pushed to GitHub."
}

stop () { echo; echo "STOPPED: $*"; echo "Nothing was pushed. Send Claude the lines above."; exit 1; }

main "$@"
exit
