"""
Unit checks for the machinery every result depends on: data fingerprints, the data manifest, the
null models, the connection threshold, provenance stamping, the settings banner, the clean-tree
guard on registered tests, and the check-role table. Self-contained: builds its own tiny tables,
needs no connectome and no network. Run by tests/regression.py, or alone:

    python tests/unit.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _tables(seed=0):
    rng = np.random.default_rng(seed)
    n = pd.DataFrame(dict(bodyId=np.arange(100, 160), type=[f"T{i % 6}" for i in range(60)],
                          superclass=["sensory"] * 10 + ["central"] * 30 + ["motor"] * 20,
                          somaSide=["L", "R"] * 30))
    pre = rng.choice(n.bodyId[:40], 400)                           # sensory and central senders
    post = rng.choice(n.bodyId[10:], 400)                          # central and motor targets
    e = pd.DataFrame(dict(pre=pre, post=post, weight=rng.integers(1, 30, 400),
                          nt=rng.choice(["acetylcholine", "gaba", "glutamate"], 400)))
    e = e[e.pre != e.post].drop_duplicates(["pre", "post"]).reset_index(drop=True)
    return n, e


def t_fingerprint_invariance(tmp):
    from flycns.integrity import table_fingerprint
    _, e = _tables()
    a = tmp / "a.parquet"; e.to_parquet(a, index=False)
    b = tmp / "b.parquet"; e.sample(frac=1, random_state=1)[list(reversed(e.columns))].to_parquet(b, index=False)
    c = tmp / "c.parquet"; e2 = e.copy(); e2.loc[0, "weight"] += 1; e2.to_parquet(c, index=False)
    fa, fb, fc = (table_fingerprint(p) for p in (a, b, c))
    ok = fa["digest"] == fb["digest"] and fa["digest"] != fc["digest"] and fa["sums"] == fb["sums"]
    return ok, "row and column order ignored; a one-synapse change detected" if ok else f"{fa} | {fb} | {fc}"


def t_manifest_roundtrip(tmp):
    from flycns.integrity import write_manifest, verify_data
    d = tmp / "data"; d.mkdir()
    n, e = _tables()
    n.to_parquet(d / "neurons.parquet", index=False); e.to_parquet(d / "edges.parquet", index=False)
    if verify_data(d)["status"] != "no-manifest":
        return False, "missing manifest not reported"
    write_manifest(d)
    if verify_data(d)["status"] != "match":
        return False, "fresh manifest does not match its own data"
    e.loc[3, "nt"] = "gaba" if e.loc[3, "nt"] != "gaba" else "acetylcholine"
    e.to_parquet(d / "edges.parquet", index=False)
    v = verify_data(d)
    ok = v["status"] == "mismatch" and any("edges.parquet" in p for p in v["problems"]) \
        and not any("neurons.parquet" in p for p in v["problems"])
    return ok, "one changed transmitter call flagged in edges only" if ok else str(v)


def t_null_global_unchanged():
    """The default null must be bit-identical to the original implementation (registered tests use it)."""
    from flycns.graph import rewire_null
    _, e = _tables()
    rng = np.random.default_rng(7)
    legacy = e.copy(); legacy["post"] = rng.permutation(legacy["post"].values)
    legacy = legacy[legacy["pre"] != legacy["post"]].reset_index(drop=True)
    new = rewire_null(e, seed=7, mode="global")
    ok = legacy.equals(new.drop(columns=[], errors="ignore"))
    return ok, "identical to the pre-2026-10-10 null" if ok else "global null changed"


def t_null_superclass():
    from flycns.graph import rewire_null
    n, e = _tables()
    sc = n.set_index("bodyId")["superclass"]
    e = e[e.pre.map(sc) == "sensory"].reset_index(drop=True)   # senders outside every target class: no self-loops possible
    out = rewire_null(e, seed=3, mode="superclass", neurons=n)
    key = lambda df: df.assign(c=df.post.map(sc)).groupby(["pre", "c"]).weight.sum()
    same_class = key(e).equals(key(out))
    same_indeg = e.groupby("post").size().sort_index().equals(out.groupby("post").size().sort_index())
    moved = (out.post.values != e.post.values).mean()
    ok = same_class and same_indeg and moved > 0.3 and len(out) == len(e)
    return ok, f"per-sender synapses to each class and every in-degree kept; {moved:.0%} of targets moved"


def t_min_weight_and_provenance(tmp):
    from flycns import graph, integrity
    d = tmp / "mw"; d.mkdir()
    n, e = _tables()
    n.to_parquet(d / "neurons.parquet", index=False); e.to_parquet(d / "edges.parquet", index=False)
    os.environ["FLYCNS_MIN_WEIGHT"] = "20"
    integrity._ANNOUNCED = True      # the banner is tested separately; keep this test's output quiet
    try:
        _, e20 = graph.load_graph(str(d))
    finally:
        del os.environ["FLYCNS_MIN_WEIGHT"]
    _, e5 = graph.load_graph(str(d))
    rec = integrity.provenance_record()
    ok = (len(e20) < len(e5) and (e20.weight >= 20).all() and rec["graph"]["min_weight"] == 5
          and set(rec["data"]["digests"]) == {"neurons.parquet", "edges.parquet"})
    return ok, f"{len(e5)} edges at 5, {len(e20)} at 20; report stamped with data digests" if ok else str(rec)


def t_settings_banner():
    code = "from flycns.integrity import announce_overrides as a; a(); a()"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "FLYCNS_WSCALE": "0.9"})
    ok = "FLYCNS_WSCALE=0.9" in r.stderr and r.stderr.count("SETTINGS OVERRIDDEN") == 1
    return ok, "override announced once per process" if ok else r.stderr[-300:]


def t_clean_tree_guard(tmp):
    """A registered test must refuse uncommitted code, and run on committed code."""
    if not shutil.which("git"):
        return True, "git not installed; guard not exercised"
    repo = tmp / "repo"
    shutil.copytree(ROOT / "flycns", repo / "flycns", ignore=shutil.ignore_patterns("__pycache__"))
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    env = {k: v for k, v in os.environ.items() if k != "FLYCNS_ALLOW_DIRTY"}
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*g, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*g, "commit", "-qm", "x"], cwd=repo, check=True)
    probe = ["-c", "from flycns.integrity import require_clean; require_clean('probe'); print('RAN')"]
    clean = subprocess.run([sys.executable, *probe], cwd=repo, capture_output=True, text=True, env=env)
    with open(repo / "flycns" / "model.py", "a") as f:
        f.write("\n# edit\n")
    dirty = subprocess.run([sys.executable, *probe], cwd=repo, capture_output=True, text=True, env=env)
    allowed = subprocess.run([sys.executable, *probe], cwd=repo, capture_output=True, text=True,
                             env={**env, "FLYCNS_ALLOW_DIRTY": "1"})
    ok = ("RAN" in clean.stdout and dirty.returncode != 0 and "refuses to run" in dirty.stderr
          and "RAN" in allowed.stdout and "UNCOMMITTED" in allowed.stderr)
    return ok, "runs when committed, refuses an edited model.py, override is loud" if ok else \
        f"clean={clean.stdout!r} {clean.stderr[-200:]!r} dirty={dirty.returncode} {dirty.stderr[-200:]!r}"


def t_every_check_has_a_role():
    """Every check in the committed reports has a role, including checks those reports left unscored
    (some are scored only under some conditions). tests/regression.py adds the complement: every
    check the toy suite scores, which exercises branches the real data skips, must have a role too."""
    from flycns.calibration import role
    missing = set()
    for rep in sorted((ROOT / "results").glob("*/report.json")):
        r = json.loads(rep.read_text())
        for k in (r.get("checks") or {}):
            if role(r.get("benchmark", rep.parent.name), k)[0] == "unclassified":
                missing.add(f"{rep.parent.name}:{k}")
    return not missing, "every check in the committed reports is classified" if not missing else \
        f"classify in flycns/calibration.py: {sorted(missing)}"


def run_all():
    out = []
    tmp = Path(tempfile.mkdtemp(prefix="flycns_unit_"))
    try:
        for name, fn in [("fingerprint ignores order, catches edits", lambda: t_fingerprint_invariance(tmp)),
                         ("manifest write / verify / mismatch", lambda: t_manifest_roundtrip(tmp)),
                         ("global null unchanged", t_null_global_unchanged),
                         ("superclass null keeps class structure", t_null_superclass),
                         ("min_weight override + provenance", lambda: t_min_weight_and_provenance(tmp)),
                         ("settings banner", t_settings_banner),
                         ("registered tests refuse dirty code", lambda: t_clean_tree_guard(tmp)),
                         ("every scored check has a role", t_every_check_has_a_role)]:
            try:
                ok, msg = fn()
            except Exception as ex:  # a crashing check is a failing check
                ok, msg = False, f"{type(ex).__name__}: {ex}"[:300]
            out.append((f"unit: {name}", bool(ok), msg))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


if __name__ == "__main__":
    res = run_all()
    for label, ok, msg in res:
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<48} {msg}")
    sys.exit(0 if all(ok for _, ok, _ in res) else 1)
