"""
One command for the real-data steps:
  1. update the code, the environment and the annotations (setup, without questions)
  2. pin the input data: commit data\\MANIFEST.json the first time it is written
  3. rerun the core suite canonically, so its reports carry the integrity stamp
  4. run the registered stricter null (benchmarks\\null_strict.py)
  5. commit the results and push them
About 1 to 1.5 hours with the compiled engine. Keeps Windows awake until it finishes.
Safe to run again after an interruption: leftover result files are set aside (git stash, recoverable)
and a data-pin commit from the earlier run is replayed on top of the latest code.

    .\\fly.cmd  then option 51        or        .venv\\Scripts\\python.exe scripts\\canonical_rerun.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from flycns.windows import console, keep_awake  # noqa: E402

console()
PY = sys.executable
UPDATED = "_CANON_UPDATED"     # deliberately not FLYCNS_*, which would be stamped as a settings override


def stop(msg):
    print(f"\nSTOPPED: {msg}\nNothing was pushed. Send Claude the lines above.")
    sys.exit(1)


def git(*args, quiet=False):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not quiet and (r.stdout.strip() or r.stderr.strip()):
        print("  " + (r.stdout + r.stderr).strip().replace("\n", "\n  "))
    return r


def py(*args):
    return subprocess.run([PY, *args]).returncode


def main():
    if not os.environ.get(UPDATED):
        print("[1/5] update code")
        if git("rev-parse", "--is-inside-work-tree", quiet=True).returncode != 0:
            stop("this folder is not a git checkout; clone it with git (see README) so results can be traced.")
        # result files left by an interrupted run would block the pull; they are regenerated below, so
        # set them aside (recoverable) rather than discard them. Code changes are never touched.
        if git("status", "--porcelain", "--untracked-files=no", "--", "results", quiet=True).stdout.strip():
            git("stash", "push", "-q", "-m", "canonical_rerun: local result files set aside", "--", "results")
            print("  set aside uncommitted result files from an earlier run (recover: git stash list, git stash pop)")
        # --rebase: a data-pin commit from an earlier interrupted run is replayed on top of the latest code
        if git("pull", "--rebase", "-q").returncode != 0:
            stop("git pull failed (uncommitted code changes, or a conflict).")
        # restart from the updated copy of this script, so the newest steps run
        sys.exit(subprocess.run([PY, __file__, *sys.argv[1:]], env={**os.environ, UPDATED: "1"}).returncode)

    keep_awake()
    print("[1/5] environment and annotations")
    if py("scripts/setup.py", "--refresh") != 0:
        stop("setup did not finish (see its message above).")

    print("[2/5] pin the input data")
    if git("ls-files", "--error-unmatch", "data/MANIFEST.json", quiet=True).returncode != 0:
        git("add", "data/MANIFEST.json")
        git("commit", "-qm", "pin input data: data/MANIFEST.json (male-cns:v1.0)")
        print("  committed data/MANIFEST.json")
    else:
        print("  already pinned; setup verified the data against it")
    from flycns.integrity import git_state
    st = git_state()
    if not st["clean"]:
        print("  uncommitted code: " + ", ".join(st["dirty_files"][:10]))
        stop("code differs from the last commit; registered tests would refuse to run.")

    print("[3/5] core suite, canonical (about 40 min)")
    if py("scripts/run_all.py", "40", "data") != 0:
        stop("the core suite did not finish.")

    print("[4/5] stricter null, registered")
    if py("benchmarks/null_strict.py", "data") != 0:
        stop("the stricter null did not finish.")

    print("[5/5] commit and push")
    subprocess.run([PY, "benchmarks/summarize.py"], capture_output=True)
    git("add", "-A", "results", quiet=True)
    if git("commit", "-qm", "canonical rerun of the core suite and the registered stricter null, "
                            "under integrity stamping", quiet=True).returncode != 0:
        print("  (no result changes to commit)")
    if git("push", "-q").returncode != 0:
        stop("push failed; everything is committed locally, so just run: git push")
    print()
    for line in (ROOT / "results/SUITE.md").read_text(encoding="utf-8").splitlines()[2:5]:
        print(line)
    print("\ndone: results pushed to GitHub.")


if __name__ == "__main__":
    main()
