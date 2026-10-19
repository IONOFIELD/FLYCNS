"""Collect a cloud rerun's arm results into the working tree, and check them before anything is scored.

    python scripts/collect_rerun_out.py <label> <run_number> [<run_number> ...]

e.g.  python scripts/collect_rerun_out.py gen6_phaseA 33 34 35 36

Each Actions job pushes its results to rerun-out/<run_number>/<job> (.github/workflows/rerun.yml). This fetches
every such branch for the given runs, copies results/<label>/arms/*.json from each into the working tree, and
reports, per arm: which branch and commit it came from, and whether its registration stamp matches the committed
registration (results/<label>/registration_v*.json: same model hash, matches true, not a reduced/smoke run). It
also prints the last lines of ci-log.txt for any job that produced no arm. It never scores, never commits and
never pushes: the scorer (and its own refusal rules) come after, and the collected files are committed by hand.
An arm found on two branches is a hard stop (a re-run must be resolved by a person, not by order of fetching).
Files are written byte-for-byte as committed (LF line endings, also on Windows). Side effect: the branches are
fetched into refs/remotes/rerun-out-collect/* of this repository; `git update-ref -d` or a prune removes them.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise SystemExit(f"[collect] git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout


def registration(label):
    d = ROOT / "results" / label
    regs = sorted(d.glob("registration_v*.json")) or sorted(d.glob("registration.json"))
    if not regs:
        raise SystemExit(f"[collect] no registration under results/{label}/")
    f = regs[-1]
    if git("ls-files", "--error-unmatch", str(f.relative_to(ROOT)), check=False) == "":
        raise SystemExit(f"[collect] {f.relative_to(ROOT)} is not committed")
    return f, json.loads(f.read_text(encoding="utf-8"))


def main(label, runs):
    reg_file, reg = registration(label)
    want_hash = reg["model"]["hash"]
    print(f"[collect] {label}: registration {reg_file.name}, model {want_hash[:12]}, commit {reg.get('git_commit')}")
    refs = []
    for run in runs:
        out = git("ls-remote", "origin", f"refs/heads/rerun-out/{run}/*")
        refs += [line.split("\t")[1] for line in out.splitlines() if line.strip()]
    if not refs:
        raise SystemExit(f"[collect] no rerun-out branches for runs {runs}")
    arms_dir = ROOT / "results" / label / "arms"
    arms_dir.mkdir(parents=True, exist_ok=True)
    seen, rows, empty = {}, [], []
    for ref in sorted(refs):
        local = "refs/remotes/rerun-out-collect/" + ref[len("refs/heads/"):]
        git("fetch", "-q", "origin", f"+{ref}:{local}")
        sha = git("rev-parse", "--short", local).strip()
        names = [p for p in git("ls-tree", "-r", "--name-only", local, f"results/{label}/arms/").splitlines()
                 if p.endswith(".json")]
        if not names:
            log = git("show", f"{local}:ci-log.txt", check=False)
            empty.append((ref, sha, "\n      ".join(log.strip().splitlines()[-6:]) or "(no ci-log.txt)"))
            continue
        for p in names:
            arm = Path(p).stem
            if arm in seen:
                raise SystemExit(f"[collect] {arm} is on two branches: {seen[arm]} and {ref}; resolve by hand")
            seen[arm] = ref
            text = git("show", f"{local}:{p}")
            rec = json.loads(text)
            st = rec.get("registration") or {}
            ok = st.get("model_hash") == want_hash and bool(st.get("matches")) and not rec.get("reduced")
            (ROOT / p).write_text(text, encoding="utf-8", newline="")   # as committed: LF, not CRLF on Windows
            rows.append((arm, ref.split("/")[-1], sha, len(rec.get("trials", [])), "OK" if ok else
                         f"STAMP MISMATCH (model {str(st.get('model_hash'))[:12]}, matches {st.get('matches')}, "
                         f"reduced {rec.get('reduced')})"))
    for arm, job, sha, n, status in sorted(rows):
        print(f"  {arm:<28} {job:<18} {sha}  trials {n:<4} {status}")
    bad = [r for r in rows if r[4] != "OK"]
    print(f"[collect] {len(rows)} arms written to results/{label}/arms/ from {len(refs)} branches; "
          f"{len(bad)} with a stamp problem; {len(empty)} branches without arms")
    for ref, sha, log in empty:
        print(f"  NO ARMS  {ref} ({sha})\n      {log}")
    return 1 if bad or empty else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1], [int(x) for x in sys.argv[2:]]))
