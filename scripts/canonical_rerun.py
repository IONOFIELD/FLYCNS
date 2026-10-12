"""
One command for the real-data steps:
  1. update the code, the environment and the annotations (setup, without questions)
  2. pin the input data: commit data\\MANIFEST.json the first time it is written
  3. rerun the core suite canonically, so its reports carry the integrity stamp
  4. run the registered stricter null (benchmarks\\null_strict.py)
  5. commit the results to a NEW review branch and push that branch (scripts/review_branch.py): your
     own branch is never pushed; the results reach main through a pull request
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
from review_branch import (close_review_branch, confirm_remote, open_review_branch,  # noqa: E402
                           pull_request_url, push_review)

console()
PY = sys.executable
UPDATED = "_CANON_UPDATED"     # deliberately not FLYCNS_*, which would be stamped as a settings override


def stop(msg):
    print(f"\nSTOPPED: {msg}\nNothing was pushed. Copy the lines above when you ask for help "
          f"(for example in a GitHub issue).")
    sys.exit(1)


def git(*args, quiet=False):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not quiet and (r.stdout.strip() or r.stderr.strip()):
        print("  " + (r.stdout + r.stderr).strip().replace("\n", "\n  "))
    return r


def py(*args):
    return subprocess.run([PY, *args]).returncode


def commit(message, *paths):
    """Commit the given paths; True if a commit was made. Nothing staged is not an error; a refused
    commit is (git needs user.name and user.email, which a fresh Git for Windows does not have)."""
    git("add", "-A", "--", *paths, quiet=True)
    if git("diff", "--cached", "--quiet", "--", *paths, quiet=True).returncode == 0:
        return False
    r = git("commit", "-qm", message, "--", *paths)
    if r.returncode != 0:
        stop("git refused the commit (see its message above).")
    return True


CANONICAL_REPORTS = ["gf_escape", "auditory", "feeding", "null_strict"]


def main():
    from flycns.integrity import refuse_overrides
    refuse_overrides("menu 51")     # before an hour of simulation, not after
    if not os.environ.get(UPDATED):
        print("[1/5] update code")
        if git("rev-parse", "--is-inside-work-tree", quiet=True).returncode != 0:
            stop("this folder is not a git checkout; clone it with git (see README) so results can be traced.")
        # checked before 1.5 hours of simulation, not after: git cannot commit without an identity
        if not (git("config", "user.name", quiet=True).stdout.strip() and git("config", "user.email", quiet=True).stdout.strip()):
            stop('git does not know who you are yet. Run these two lines once, then choose 51 again:\n'
                 '  git config --global user.name "Your Name"\n'
                 '  git config --global user.email "you@example.com"')
        # where the results will go, checked before 1.5 hours of simulation, not after
        url, why = confirm_remote()
        if why:
            stop(why)
        print(f"  results will go to a new review branch on {url}; your branch is not pushed")
        # result files left by an interrupted run would block the pull; they are regenerated below, so
        # set them aside (recoverable) rather than discard them. Code changes are never touched.
        if git("status", "--porcelain", "--untracked-files=no", "--", "results", quiet=True).stdout.strip():
            git("stash", "push", "-q", "-m", "canonical_rerun: local result files set aside", "--", "results")
            print("  set aside uncommitted result files from an earlier run (recover: git stash list, git stash pop)")
        # --rebase: a data-pin commit from an earlier interrupted run is replayed on top of the latest code
        if git("pull", "--rebase", "-q").returncode != 0:
            gitdir = Path(git("rev-parse", "--git-dir", quiet=True).stdout.strip())
            if (gitdir / "rebase-merge").exists() or (gitdir / "rebase-apply").exists():
                git("rebase", "--abort", quiet=True)      # never leave the folder half-rebased
                stop("the update conflicts with a local commit; the folder is back as it was.")
            stop("git pull failed (uncommitted code changes, or no connection).")
        # restart from the updated copy of this script, so the newest steps run
        sys.exit(subprocess.run([PY, __file__, *sys.argv[1:]], env={**os.environ, UPDATED: "1"}).returncode)

    keep_awake()
    print("[1/5] environment and annotations")
    if py("scripts/setup.py", "--refresh") != 0:
        stop("setup did not finish (see its message above).")

    print("[2/5] pin the input data")
    if git("ls-files", "--error-unmatch", "data/MANIFEST.json", quiet=True).returncode != 0:
        commit("pin input data: data/MANIFEST.json (male-cns:v1.0)", "data/MANIFEST.json")
        print("  committed data/MANIFEST.json")
    else:
        print("  already pinned; setup verified the data against it")
    from flycns.integrity import git_state
    st = git_state()
    if not st["clean"]:
        print("  uncommitted code: " + ", ".join(st["dirty_files"][:10]))
        stop("code differs from the last commit; registered tests would refuse to run.")

    import time
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    print("[3/5] core suite, canonical (about 40 min)")
    if py("scripts/run_all.py", "40", "data") != 0:
        stop("the core suite did not finish.")

    print("[4/5] stricter null, registered")
    if py("benchmarks/null_strict.py", "data") != 0:
        stop("the stricter null did not finish.")

    print("[5/5] commit to a review branch and push it")
    refuse_overrides("menu 51")
    url, why = confirm_remote()
    if why:
        stop(why)
    # every canonical report must come from this run: a benchmark that failed leaves its old report behind
    import json
    old = [b for b in CANONICAL_REPORTS
           if json.loads((ROOT / "results" / b / "report.json").read_text(encoding="utf-8"))
           .get("provenance", {}).get("written_at", "") < started]
    if old:
        stop(f"these reports were not rewritten by this run: {', '.join(old)} (see the messages above).")
    if py("benchmarks/summarize.py") != 0:
        stop("the suite summary failed.")
    headline = (ROOT / "results/SUITE.md").read_text(encoding="utf-8").splitlines()[2:5]
    branch, back = open_review_branch("canonical-rerun")
    made = commit("canonical rerun of the core suite and the registered stricter null, under integrity stamping",
                  "results")
    pushed = made and push_review(branch)
    if not close_review_branch(back):
        print(f"  NOTE: could not switch back to {back}; you are on {branch}")
    elif back and not made:
        git("branch", "-D", branch, quiet=True)          # nothing was committed: no review branch is left
    print()
    for line in headline:
        print(line)
    if not made:
        print("\ndone: no result changes, nothing to review.")
    elif not pushed:
        stop(f"push failed; the results are committed on the local branch {branch}. "
             f"Push it with: git push -u origin {branch}")
    else:
        pr = pull_request_url(branch)
        print(f"\ndone: results pushed to the review branch {branch} (your branch was not pushed).")
        if pr:
            print(f"open the pull request to review and merge them: {pr}")


if __name__ == "__main__":
    main()
