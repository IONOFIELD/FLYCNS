"""
Where menu 51 (scripts/canonical_rerun.py) and the robustness battery (scripts/overnight.py) put the
results they commit: a NEW review branch, never the branch you work on. A result reaches main only
through a pull request that someone has looked at.

  confirm_remote()        before any long run: the remote exists, answers and would accept the push
                          (a dry run); says where results go
  open_review_branch()    switch to review/<label>-<time> (or stay on a branch that already is one:
                          review/* here, rerun-out/* in the cloud rerun)
  push_review()           push that branch, and only that branch (git's message shown on failure; one retry)
  close_review_branch()   switch back to the branch you were on

Your own branch is never pushed and never gets the result commits. After a run, open the pull request
the script prints, merge it, and update (menu option 51 updates first; or `git pull`).
"""
import re
import subprocess
import time

REMOTE = "origin"
REVIEW_PREFIXES = ("review/", "rerun-out/")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def _why(r):
    """git's own message, on one line (it says why a push or a fetch was refused)."""
    return " ".join((r.stderr or r.stdout or "no message").split())[:300]


def confirm_remote(remote=REMOTE):
    """(url, None) if the remote is configured, answers and accepts a push from here, else (None, why).
    Checked before a long run, so an hour of simulation never ends in a push that cannot happen. The push
    check is a dry run (nothing is sent) to a new review branch name: it needs the same sign-in and write
    access as the real push at the end."""
    r = git("remote", "get-url", remote)
    url = r.stdout.strip()
    if r.returncode != 0 or not url:
        return None, f"this checkout has no git remote named {remote!r}; results would have nowhere to go"
    r = git("ls-remote", "--heads", remote)
    if r.returncode != 0:
        return None, f"the remote {remote} ({url}) does not answer: {_why(r)}"
    r = git("push", "--dry-run", "-q", remote, "HEAD:refs/heads/review/push-check")
    if r.returncode != 0:
        return None, f"the remote {remote} ({url}) answers but would refuse the results: {_why(r)}"
    return url, None


def current_branch():
    """The checked-out branch name, or None when HEAD is detached."""
    r = git("symbolic-ref", "-q", "--short", "HEAD")
    return r.stdout.strip() or None if r.returncode == 0 else None


def is_review_branch(name):
    return bool(name) and name.startswith(REVIEW_PREFIXES)


def open_review_branch(label):
    """Switch to a new review branch for this run's results. Returns (review_branch, back), where `back` is
    what close_review_branch() returns to: the branch (or detached commit) you were on, or None when the
    current branch already is a review branch and nothing was switched."""
    cur = current_branch()
    if is_review_branch(cur):
        return cur, None
    back = cur or git("rev-parse", "HEAD").stdout.strip()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-") or "results"
    name = f"review/{safe}-{time.strftime('%Y%m%d-%H%M%S')}"
    r = git("switch", "-q", "-c", name)
    if r.returncode != 0:
        raise SystemExit(f"could not create the review branch {name}: {(r.stderr or r.stdout).strip()}")
    return name, back


def push_review(branch, remote=REMOTE, retry_after_s=15):
    """Push the review branch (never any other). True on success. A failed push prints git's own message
    and is tried once more (a connection that drops for a moment should not cost the run)."""
    if not is_review_branch(branch):
        raise ValueError(f"refusing to push {branch!r}: results go to a review branch only")
    for attempt in (1, 2):
        r = git("push", "-q", "-u", remote, f"HEAD:refs/heads/{branch}")
        if r.returncode == 0:
            return True
        print(f"  push of {branch} failed (attempt {attempt} of 2): {_why(r)}", flush=True)
        if attempt == 1:
            time.sleep(retry_after_s)
    return False


def close_review_branch(back):
    """Return to the branch (or commit) the run started on. True if back there (or nothing to do)."""
    if not back:
        return True
    cmd = ["switch", "-q", back] if not re.fullmatch(r"[0-9a-f]{40}", back) else ["switch", "-q", "--detach", back]
    return git(*cmd).returncode == 0


def pull_request_url(branch, remote=REMOTE):
    """The page to open a pull request from `branch`, when the remote is on GitHub; else None."""
    url = git("remote", "get-url", remote).stdout.strip()
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"https://github.com/{m.group(1)}/{m.group(2)}/compare/{branch}?expand=1" if m else None
