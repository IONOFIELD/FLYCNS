#!/usr/bin/env bash
# Robustness battery: seed replicates, transmitter sign inversion (random and targeted), connection
# weight scale, connection-size threshold, and a stricter (superclass-preserving) null.
# Each run = the three-benchmark core suite (~25 min).
#
# Results go to results/overnight/<tag>/ : SUITE.md plus one <benchmark>_report.json per benchmark.
# The CANONICAL results (results/<benchmark>/, results/SUITE.md) are snapshotted before the battery
# and restored afterwards, even if it is interrupted, so a perturbed run can never be left standing
# as the headline result. (Before 2026-10-10 the battery overwrote them, and copied every
# report.json into one folder, so only the last one survived.)
#
# Usage:  caffeinate -i scripts/overnight.sh 2>&1 | tee overnight.log
set -u
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
mkdir -p results/overnight
python fit/audit_stimuli.py data || { echo "stimulus audit failed; battery not started"; exit 1; }
python -m flycns.integrity verify data || { echo "data differ from data/MANIFEST.json; battery not started"; exit 1; }

BENCHES="gf_escape auditory feeding"
SNAP=$(mktemp -d)
for b in $BENCHES; do [ -d "results/$b" ] && cp -a "results/$b" "$SNAP/"; done
[ -f results/SUITE.md ] && cp results/SUITE.md "$SNAP/"
restore () {
  for b in $BENCHES; do
    if [ -d "$SNAP/$b" ]; then rm -rf "results/$b"; cp -a "$SNAP/$b" "results/$b"; fi
  done
  [ -f "$SNAP/SUITE.md" ] && cp "$SNAP/SUITE.md" results/SUITE.md
  rm -rf "$SNAP"
  echo "canonical results restored"
}
trap restore EXIT

run () {   # run TAG SEED SIGNFLIP WSCALE   (extra settings: export before calling, unset after)
  local tag=$1; export FLYCNS_SEED=$2 FLYCNS_SIGNFLIP=$3 FLYCNS_WSCALE=$4 FLYCNS_RUN_TAG=$tag
  echo "=== $(date '+%H:%M') start $tag (seed $2, signflip $3, wscale $4${FLYCNS_MIN_WEIGHT:+, min_weight $FLYCNS_MIN_WEIGHT}${FLYCNS_NULL:+, null $FLYCNS_NULL})"
  mkdir -p "results/overnight/$tag"
  for b in $BENCHES; do
    python benchmarks/$b.py 40 data > "results/overnight/${tag}_${b}.log" 2>&1 || echo "  $b errored (see log)"
    [ -f "results/$b/report.json" ] && cp "results/$b/report.json" "results/overnight/$tag/${b}_report.json"
  done
  python benchmarks/summarize.py > /dev/null 2>&1
  cp results/SUITE.md "results/overnight/$tag/SUITE.md"
  grep -m1 "checks pass" results/SUITE.md
  git add -A results/overnight >/dev/null 2>&1 && git commit -qm "overnight: $tag $(grep -m1 -o '[0-9]*/[0-9]* checks pass' results/SUITE.md)" >/dev/null 2>&1 && git push -q 2>/dev/null
  echo "=== $(date '+%H:%M') done  $tag"
}
run seed1        1 0    0.3
run seed2        2 0    0.3
run signflip05_a 0 0.05 0.3
run signflip05_b 1 0.05 0.3
run signflip10   0 0.10 0.3
run wscale025    0 0    0.25
run wscale035    0 0    0.35
run wscale040    0 0    0.40
# targeted perturbation: only the neurons the transmitter classifier is unsure about
export FLYCNS_SIGNFLIP_TARGETED=1; run signflip_targeted 0 0 0.3; unset FLYCNS_SIGNFLIP_TARGETED
# connection-size threshold (default 5 synapses): looser and stricter inclusion of connections
export FLYCNS_MIN_WEIGHT=3;  run minweight3  0 0 0.3; unset FLYCNS_MIN_WEIGHT
export FLYCNS_MIN_WEIGHT=10; run minweight10 0 0 0.3; unset FLYCNS_MIN_WEIGHT
# stricter null: shuffle targets only within the same superclass (flycns/graph.py rewire_null)
export FLYCNS_NULL=superclass; run null_superclass 0 0 0.3; unset FLYCNS_NULL
unset FLYCNS_SEED FLYCNS_SIGNFLIP FLYCNS_WSCALE FLYCNS_RUN_TAG
echo; echo "SUMMARY"; for d in results/overnight/*/; do printf "%-18s %s\n" "$(basename $d)" "$(grep -m1 -o '[0-9]*/[0-9]* checks pass' $d/SUITE.md 2>/dev/null)"; done
