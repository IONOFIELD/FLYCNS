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


def t_targeted_flip_needs_its_table(tmp):
    """A perturbation whose input is missing must stop, never run unperturbed under its label."""
    from flycns import graph, integrity
    d = tmp / "tf"; d.mkdir()
    n, e = _tables()
    n.to_parquet(d / "neurons.parquet", index=False); e.to_parquet(d / "edges.parquet", index=False)
    os.environ["FLYCNS_SIGNFLIP_TARGETED"] = "1"
    integrity._ANNOUNCED = True
    try:
        graph.load_graph(str(d))
        return False, "ran without edges_nt.parquet"
    except SystemExit as ex:
        return "edges_nt.parquet" in str(ex), "refused: no transmitter table"
    finally:
        del os.environ["FLYCNS_SIGNFLIP_TARGETED"]



def t_signs_come_from_one_map(tmp):
    """Every transmitter label, mixed case and missing labels, signed only by graph.SIGN_MAP; any sign
    column already in the file is ignored; dropped edges and silent senders are counted; and no other
    file carries its own transmitter-to-sign table."""
    import re
    from flycns import graph, integrity
    d = tmp / "sg"; d.mkdir()
    n, e = _tables()
    labels = ["Acetylcholine", "GABA", "glutamate", "Histamine", "dopamine", "OCTOPAMINE", "serotonin", None]
    e["nt"] = [labels[i % len(labels)] for i in range(len(e))]
    e["sign"] = 1.0                                   # a stale on-disk column, as the fetch writes
    n.to_parquet(d / "neurons.parquet", index=False); e.to_parquet(d / "edges.parquet", index=False)
    integrity._ANNOUNCED = True
    _, g = graph.load_graph(str(d))
    e = e[e.weight >= graph.MIN_WEIGHT_DEFAULT]       # the default connection-size floor applies first
    want = e["nt"].str.lower().map(graph.SIGN_MAP)
    kept = e[want.notna() & (want != 0)].reset_index(drop=True)
    right = ((g["sign"] == g["nt"].str.lower().map(graph.SIGN_MAP)).all()
             and set(zip(g.pre, g.post)) == set(zip(kept.pre, kept.post)))
    counted = integrity.LOADED["n_dropped_unsigned_edges"] == len(e) - len(kept)
    stray = []
    for f in list((ROOT / "flycns").glob("*.py")) + list((ROOT / "benchmarks").glob("*.py")) + \
            list((ROOT / "fit").glob("*.py")) + list((ROOT / "viz").glob("*.py")):
        if f.name != "graph.py" and re.search(r'["\']glutamate["\']\s*:\s*-1', f.read_text(encoding="utf-8")):
            stray.append(str(f.relative_to(ROOT)))
    ok = right and counted and not stray
    return ok, (f"{len(g)} of {len(e)} edges signed by SIGN_MAP (7 labels, mixed case, missing); stale column "
                f"ignored; {len(e) - len(kept)} dropped and counted" if ok else
                f"signs right {right}, counted {counted}, other sign tables in {stray}")


def t_one_membrane_time_constant():
    """The compound-potential calibration uses graph.TAU_M_S; it must equal the model's membrane tau."""
    from flycns.graph import TAU_M_S
    from flycns.model import LIFParams
    ok = abs(TAU_M_S * 1000 - LIFParams().tau_m_ms) < 1e-12
    return ok, f"TAU_M_S {TAU_M_S * 1000} ms == LIFParams.tau_m_ms {LIFParams().tau_m_ms} ms"

def t_registered_criteria_rerun(tmp):
    """A registered test must be rerunnable: criteria saved as JSON match the code (tuples become
    lists), a changed criterion does not, and every registered test uses this comparison."""
    from flycns.integrity import criteria_differ
    crit = dict(band=(2.0, 12.0), k=7, R1="text")
    f = tmp / "criteria.json"
    f.write_text(json.dumps(dict(criteria=crit)), encoding="utf-8")
    same = not criteria_differ(f, crit)
    changed = criteria_differ(f, {**crit, "k": 8})
    raw = [p.name for p in (ROOT / "benchmarks").glob("*.py")
           if "CRITERIA = dict(" in p.read_text(encoding="utf-8")
           and "criteria_differ(crit_f, CRITERIA)" not in p.read_text(encoding="utf-8")]
    ok = same and changed and not raw
    return ok, "saved criteria match their code; a changed criterion is refused" if ok else f"{same} {changed} {raw}"


def t_settings_banner():
    code = "from flycns.integrity import announce_overrides as a; a(); a()"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
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
    clean = subprocess.run([sys.executable, *probe], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    with open(repo / "flycns" / "model.py", "a", encoding="utf-8") as f:
        f.write("\n# edit\n")
    dirty = subprocess.run([sys.executable, *probe], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    allowed = subprocess.run([sys.executable, *probe], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
                             env={**env, "FLYCNS_ALLOW_DIRTY": "1"})
    ok = ("RAN" in clean.stdout and dirty.returncode != 0 and "refuses to run" in dirty.stderr
          and "RAN" in allowed.stdout and "UNCOMMITTED" in allowed.stderr)
    return ok, "runs when committed, refuses an edited model.py, override is loud" if ok else \
        f"clean={clean.stdout!r} {clean.stderr[-200:]!r} dirty={dirty.returncode} {dirty.stderr[-200:]!r}"


def t_registration_guard(tmp):
    """A committed registration may not be edited, or deleted and written again: either is refused."""
    if not shutil.which("git"):
        return True, "git not installed; guard not exercised"
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    env = {k: v for k, v in os.environ.items() if k != "FLYCNS_ALLOW_DIRTY"}
    probe = ["-c", "from flycns.integrity import require_clean; require_clean('probe'); print('RAN')"]

    def repo(name):
        r = tmp / name
        shutil.copytree(ROOT / "flycns", r / "flycns", ignore=shutil.ignore_patterns("__pycache__"))
        (r / "results" / "probe").mkdir(parents=True)
        (r / "results" / "probe" / "criteria.json").write_text('{"criteria": {"k": 1}}', encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=r, check=True)
        subprocess.run([*g, "add", "-A"], cwd=r, check=True)
        subprocess.run([*g, "commit", "-qm", "register"], cwd=r, check=True)
        return r

    def run(r):
        return subprocess.run([sys.executable, *probe], cwd=r, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env)
    a = repo("reg_a")
    first = run(a)
    (a / "results" / "probe" / "criteria.json").write_text('{"criteria": {"k": 2}}', encoding="utf-8")
    edited = run(a)
    subprocess.run([*g, "commit", "-qam", "edit"], cwd=a, check=True)
    committed_edit = run(a)
    b = repo("reg_b")
    subprocess.run([*g, "rm", "-q", "results/probe/criteria.json"], cwd=b, check=True)
    subprocess.run([*g, "commit", "-qm", "delete"], cwd=b, check=True)
    (b / "results" / "probe").mkdir(parents=True, exist_ok=True)
    (b / "results" / "probe" / "criteria.json").write_text('{"criteria": {"k": 3}}', encoding="utf-8")
    subprocess.run([*g, "add", "-A"], cwd=b, check=True)
    subprocess.run([*g, "commit", "-qm", "rewrite"], cwd=b, check=True)
    rewritten = run(b)
    # the audit's recipe: delete the registration in a commit and rerun, so the test registers afresh
    c = repo("reg_c")
    subprocess.run([*g, "rm", "-q", "results/probe/criteria.json"], cwd=c, check=True)
    subprocess.run([*g, "commit", "-qm", "delete"], cwd=c, check=True)
    deleted = run(c)
    ok = ("RAN" in first.stdout and edited.returncode != 0 and committed_edit.returncode != 0
          and "changed after it was committed" in committed_edit.stderr
          and rewritten.returncode != 0 and "deleted and written again" in rewritten.stderr
          and deleted.returncode != 0 and "registered and then deleted" in deleted.stderr)
    return ok, "an edited, re-committed, deleted, or deleted-and-rewritten registration is refused" if ok else \
        (f"first={first.stdout!r} edited={edited.returncode} committed={committed_edit.stderr[-160:]!r} "
         f"rewritten={rewritten.stderr[-160:]!r} deleted={deleted.returncode} {deleted.stderr[-160:]!r}")


def t_fingerprint_cache_cannot_vouch(tmp):
    """Data are checked from the files themselves. A forged cache file changes nothing; the pinned file
    is recognised by the sha256 of its bytes; an edited table is caught; the same rows written to
    different bytes still match on content."""
    from flycns import integrity
    d = tmp / "fp"; d.mkdir()
    n, e = _tables()
    e.to_parquet(d / "edges.parquet", index=False)
    man = integrity.write_manifest(d)
    pinned_sha = man["files"]["edges.parquet"].get("sha256")
    (d / integrity.CACHE).write_text(json.dumps({"edges.parquet": {"digest": "0" * 64}}), encoding="utf-8")
    first = integrity.verify_data(d)["status"]
    forged_ignored = integrity.fingerprints(d)["edges.parquet"]["digest"] == man["files"]["edges.parquet"]["digest"]
    e2 = e.copy(); e2.loc[0, "weight"] += 1
    e2.to_parquet(d / "edges.parquet", index=False)
    edited = integrity.verify_data(d)["status"]
    e.sample(frac=1.0, random_state=1).to_parquet(d / "edges.parquet", index=False, compression="gzip")
    rewritten = integrity.verify_data(d)["status"]
    ok = bool(pinned_sha) and first == "match" and forged_ignored and edited == "mismatch" and rewritten == "match"
    return ok, ("pinned bytes recognised; a forged cache is ignored; an edit is caught; the same rows in other "
                "bytes still match" if ok else f"sha {bool(pinned_sha)} first {first} forged_ignored {forged_ignored} "
                f"edited {edited} rewritten {rewritten}")


def t_refuse_overrides():
    """Menu 51 refuses a model setting left in the environment, and allows engine plumbing."""
    code = "from flycns.integrity import refuse_overrides; refuse_overrides('menu 51'); print('RAN')"
    base = {k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_")}
    bad = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                         errors="replace", env={**base, "FLYCNS_WSCALE": "0.5"})
    fine = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env={**base, "FLYCNS_WSCALE": "0.3", "FLYCNS_CODEGEN": "numpy"})
    waived = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", env={**base, "FLYCNS_ALLOW_DIRTY": "1"})
    ok = (bad.returncode != 0 and "FLYCNS_WSCALE=0.5" in bad.stderr and "RAN" in fine.stdout
          and waived.returncode != 0 and "FLYCNS_ALLOW_DIRTY=1" in waived.stderr)
    return ok, ("an override is refused, and so is waiving the guards; a default value and the engine choice are not"
                if ok else f"{bad.stderr[-160:]!r} {fine.stdout!r} {waived.stderr[-160:]!r}")


def t_every_check_has_a_role():
    """Every check in the committed reports has a role, including checks those reports left unscored
    (some are scored only under some conditions). tests/regression.py adds the complement: every
    check the toy suite scores, which exercises branches the real data skips, must have a role too."""
    from flycns.calibration import role
    missing = set()
    for rep in sorted((ROOT / "results").glob("*/report.json")):
        r = json.loads(rep.read_text(encoding="utf-8"))
        for k in (r.get("checks") or {}):
            if role(r.get("benchmark", rep.parent.name), k)[0] == "unclassified":
                missing.add(f"{rep.parent.name}:{k}")
    return not missing, "every check in the committed reports is classified" if not missing else \
        f"classify in flycns/calibration.py: {sorted(missing)}"


def t_engines_identical():
    """The compiled and pure-Python engines must produce the same spikes (the fallback on a Windows
    machine without the C++ Build Tools must not change any result)."""
    import tempfile as _tf
    from flycns import CNSModel, LIFParams, loom_protocol, load_graph
    from flycns.protocols import LOOM_TUNING
    from flycns.windows import codegen_target
    d = Path(_tf.mkdtemp(prefix="flycns_engine_"))
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts/make_testdata.py")], cwd=d, capture_output=True, check=True)
        neurons, edges = load_graph(str(d / "testdata"))
        engines = ["numpy"] + (["cython"] if codegen_target() == "cython" else [])
        spikes = {}
        for eng in engines:
            m = CNSModel(neurons, edges, list(LOOM_TUNING), LIFParams(), electrical=True, codegen=eng)
            loom_protocol(m, n_trials=4, peak_hz=15.0)   # strong drive: enough spikes to compare
            spikes[eng] = m.spike_frame().sort_values(["t_ms", "bodyId"]).reset_index(drop=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    expect = os.environ.get("FLYCNS_EXPECT_ENGINE", "")
    if expect and expect != codegen_target():      # CI: a "compiled" job must really have compiled
        return False, f"expected the {expect} engine, but {codegen_target()} is in use"
    if len(engines) == 1:
        return True, f"pure-Python engine only here ({len(spikes['numpy'])} spikes); the compiled comparison runs in CI"
    a, b = spikes["cython"], spikes["numpy"]
    ok = len(a) > 0 and len(a) == len(b) and (a.bodyId.values == b.bodyId.values).all() \
        and np.array_equal(a.t_ms.values, b.t_ms.values)
    return ok, f"compiled and pure-Python engines: {len(a)} identical spikes" if ok else \
        f"engines differ: {len(a)} vs {len(b)} spikes"


def _toy_graph():
    """The toy graph, built once per process in a temporary folder."""
    if "toy" not in _CACHE:
        import tempfile as _tf
        d = Path(_tf.mkdtemp(prefix="flycns_toy_"))
        subprocess.run([sys.executable, str(ROOT / "scripts/make_testdata.py")], cwd=d, capture_output=True, check=True)
        from flycns import load_graph
        _CACHE["toy"] = load_graph(str(d / "testdata"))
        shutil.rmtree(d, ignore_errors=True)
    return _CACHE["toy"]


_CACHE = {}


def t_stimulus_choice_keeps_excitability():
    """Turning an electrically coupled cell into a stimulus source must not change how excitable its
    partner is. Four cells: an ear afferent (JO-B1_a) coupled by a declared gap junction to the giant
    fiber (DNp01), a driver and a dummy. The giant fiber starts 5 mV above rest and relaxes; with the
    afferent simulated (at rest) or a silent source, the relaxation must be identical. Before
    2026-10-10 the source version lost the gap-junction load and relaxed more slowly, which made the
    giant fiber more excitable and confounded the A2 arms."""
    from brian2 import mV
    from flycns import CNSModel, LIFParams
    neurons = pd.DataFrame(dict(bodyId=[1, 2, 3, 4], type=["JO-B1_a", "DNp01", "LC4", "dummy"],
                                superclass=["cb_sensory", "descending_neuron", "visual_projection", "cb_intrinsic"],
                                somaSide=["L"] * 4))
    edges = pd.DataFrame(dict(pre=[3, 1], post=[2, 4], weight=[10, 5], nt=["acetylcholine"] * 2, sign=[1.0, 1.0]))
    final = {}
    for label, stim in (("afferent simulated", ["LC4"]), ("afferent a silent source", ["LC4", "JO-B1_a"])):
        m = CNSModel(neurons, edges, stim, LIFParams(), electrical=True, monitor_types=("DNp01",))
        gf = m.readout_index("DNp01")
        m.G.v[gf] = -47 * mV
        m.run(10)
        final[label] = float(np.asarray(m.vmon.v / mV)[0, -1])
    a, b = final.values()
    ok = abs(a - b) < 1e-6
    return ok, f"giant fiber after 10 ms: {a:.4f} vs {b:.4f} mV" + ("" if ok else ": the stimulus choice changed it")


def t_peptide_reaches_targets():
    """Peptide modulation must act whether its source cell type is simulated or a stimulus (before
    2026-10-10 a stimulated source was silently skipped, so the AstA experiment never modulated)."""
    from flycns import CNSModel, LIFParams
    neurons, edges = _toy_graph()
    out = {}
    # simulated arm: L2 drives the simulated Pm3 source through its chain; stimulated arm: Pm3 is driven
    for label, stim in (("source simulated", ["L3", "L5", "L2"]), ("source stimulated", ["L3", "L5", "Pm3"])):
        m = CNSModel(neurons, edges, stim, LIFParams(peptide_gain_scale=1.0), electrical=False)
        rates = np.where(m.stim["type"].isin(["Pm3", "L3", "L5", "L2"]), 100.0, 0.0)
        m.set_stim_rates(rates)
        m.run(300)
        tgt = np.flatnonzero(np.asarray(m.G.pep_gain) > 0)
        out[label] = (len(m.peptides_applied), float(np.asarray(m.G.pep)[tgt].max()) if len(tgt) else 0.0)
    ok = all(n == 1 and v > 0 for n, v in out.values())
    return ok, "; ".join(f"{k}: {n} peptide wired, peak level {v:.2f}" for k, (n, v) in out.items())


def t_all_sources_parse():
    """Every Python file parses on THIS interpreter. CI runs the oldest supported Python (3.10), so
    syntax that only newer versions accept (e.g. reusing the quote inside an f-string, 3.12+) fails here."""
    import ast as _ast
    bad = []
    for f in sorted(ROOT.rglob("*.py")):
        if any(p in f.parts for p in (".venv", ".git", "__pycache__")):
            continue
        try:
            _ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError as e:
            bad.append(f"{f.relative_to(ROOT)}:{e.lineno}")
    return not bad, (f"every file parses on Python {sys.version.split()[0]}" if not bad else f"syntax errors: {bad}")


def t_text_io_is_utf8():
    """Every text read or write names its encoding. On Windows the default is cp1252, which breaks
    on characters this repository uses (é, —, ×, braille in the terminal views)."""
    from flycns.windows import unencoded_text_io
    bad = []
    for f in sorted(ROOT.rglob("*.py")):
        if any(p in f.parts for p in (".venv", ".git", "__pycache__")):
            continue
        bad += [f"{f.relative_to(ROOT)}:{line}" for line, _, _ in unencoded_text_io(f.read_text(encoding="utf-8"))]
    return not bad, "every text read/write is explicitly UTF-8" if not bad else f"add encoding='utf-8': {bad[:8]}"


def t_token_file_formats(tmp):
    """The token is read whether the file was saved as UTF-8, UTF-8 with BOM, or the UTF-16 that
    PowerShell 5 writes for `echo token > file`."""
    from flycns import windows as W
    saved_file, saved_env = W.TOKEN_FILE, os.environ.pop("NEUPRINT_TOKEN", None)
    tok = "eyJhbGciOiJIUzI1NiJ9." + "x" * 60
    try:
        results = []
        for enc in ("utf-8", "utf-8-sig", "utf-16"):
            W.TOKEN_FILE = tmp / f"tok_{enc}"
            W.TOKEN_FILE.write_bytes((tok + "\r\n").encode(enc))
            results.append(W.neuprint_token() == tok)
    finally:
        W.TOKEN_FILE = saved_file
        if saved_env is not None:
            os.environ["NEUPRINT_TOKEN"] = saved_env
    return all(results), "UTF-8, UTF-8 with BOM and PowerShell UTF-16 all read" if all(results) else str(results)


# ------------------------------------------------------------------ audit 2026-10-11, section 4
def t_sign_flips_are_exact(tmp):
    """The random flip inverts about the requested fraction; the targeted flip inverts exactly the edges
    whose sender's T-bars mostly disagree with its label (nt_agree < 0.5), no more and no fewer."""
    from flycns import graph, integrity
    d = tmp / "fl"; d.mkdir()
    rng = np.random.default_rng(3)
    n = pd.DataFrame(dict(bodyId=np.arange(1, 401), type="T", superclass="central", somaSide="L"))
    pairs = {(int(a), int(b)) for a, b in rng.integers(1, 401, (9000, 2)) if a != b}
    e = pd.DataFrame(sorted(pairs), columns=["pre", "post"])
    e["weight"] = rng.integers(5, 30, len(e)); e["nt"] = rng.choice(["acetylcholine", "gaba"], len(e))
    n.to_parquet(d / "neurons.parquet", index=False); e.to_parquet(d / "edges.parquet", index=False)
    nt = e[["pre", "post"]].copy(); nt["nt_agree"] = rng.random(len(e))
    nt.to_parquet(d / "edges_nt.parquet", index=False)
    integrity._ANNOUNCED = True
    _, base = graph.load_graph(str(d))
    os.environ["FLYCNS_SIGNFLIP"] = "0.2"
    try:
        _, rnd = graph.load_graph(str(d))
    finally:
        del os.environ["FLYCNS_SIGNFLIP"]
    frac = float((rnd["sign"] != base["sign"]).mean())
    os.environ["FLYCNS_SIGNFLIP_TARGETED"] = "1"
    try:
        _, tgt = graph.load_graph(str(d))
    finally:
        del os.environ["FLYCNS_SIGNFLIP_TARGETED"]
    m = base.merge(nt, on=["pre", "post"]).set_index(["pre", "post"])
    flipped = (tgt.set_index(["pre", "post"])["sign"] != m["sign"])
    exact = bool((flipped == (m["nt_agree"] < 0.5)).all())
    ok = abs(frac - 0.2) < 0.02 and exact
    return ok, (f"random flip {frac:.3f} of {len(base):,} edges at 0.2; targeted flip = exactly the "
                f"{int(flipped.sum()):,} edges with nt_agree < 0.5" if ok else f"random {frac:.3f}, exact {exact}")


_SEED_RUN = """
import sys, json, hashlib, numpy as np
sys.path.insert(0, sys.argv[1])
from flycns import CNSModel, LIFParams, load_graph
neurons, edges = load_graph(sys.argv[2])
m = CNSModel(neurons, edges, ["LC4", "LPLC2"], LIFParams(), electrical=True)
m.set_stim_rates(np.full(len(m.stim), 40.0))
m.run(150)
f = m.spike_frame().sort_values(["t_ms", "bodyId"])
print(json.dumps(dict(seed=LIFParams().seed, n=len(f),
                      h=hashlib.sha256(f[["t_ms", "bodyId"]].to_numpy().tobytes()).hexdigest())))
"""


def t_seed_reaches_the_model(tmp):
    """FLYCNS_SEED set before the run reaches LIFParams and the random input: the same seed in two separate
    processes gives the same spikes, a different seed gives different ones."""
    d = tmp / "sd"; d.mkdir()
    subprocess.run([sys.executable, str(ROOT / "scripts/make_testdata.py")], cwd=d, capture_output=True, check=True)
    base = {k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_") or k == "FLYCNS_CODEGEN"}
    out = []
    for seed in ("0", "0", "7"):
        r = subprocess.run([sys.executable, "-c", _SEED_RUN, str(ROOT), str(d / "testdata")], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**base, "FLYCNS_SEED": seed})
        if r.returncode != 0:
            return False, r.stderr.strip()[-200:]
        out.append(json.loads(r.stdout.strip().splitlines()[-1]))
    a, b, c = out
    ok = a["n"] > 0 and a["h"] == b["h"] and a["h"] != c["h"] and (a["seed"], c["seed"]) == (0, 7)
    return ok, (f"seed 0 twice: {a['n']} identical spikes; seed 7: different ({c['n']} spikes); LIFParams.seed follows"
                if ok else str(out))


DATA_TABLE_NAMES = {"neurons.parquet", "edges.parquet", "roi_membership.parquet", "edges_nt.parquet"}
RESULT_TABLE_NAMES = {"cascade_links.parquet", "cascade_sites.parquet", "spikes_real.parquet"}   # written under results/


def t_manifest_pins_every_input_table():
    """Every parquet table the code reads is either pinned in data/MANIFEST.json or a result the code
    itself writes under results/. A new input table must be pinned before any result can rest on it."""
    import re
    names = set()
    for top in ("benchmarks", "fit", "scripts", "flycns", "viz"):
        for f in (ROOT / top).rglob("*.py"):
            if "legacy" not in f.parts:
                names |= set(re.findall(r"([A-Za-z0-9_]+\.parquet)", f.read_text(encoding="utf-8")))
    names.discard("pyarrow.parquet")
    unknown = names - DATA_TABLE_NAMES - RESULT_TABLE_NAMES
    mf = ROOT / "data/MANIFEST.json"
    pinned = set(json.loads(mf.read_text(encoding="utf-8"))["files"]) if mf.exists() else set()
    unpinned = sorted(DATA_TABLE_NAMES - pinned)
    ok = not unknown and not unpinned
    return ok, (f"all {len(DATA_TABLE_NAMES)} input tables pinned ({', '.join(sorted(DATA_TABLE_NAMES))})" if ok else
                f"unclassified tables {sorted(unknown)}; not pinned in data/MANIFEST.json: {unpinned}")


def _registered_benchmarks():
    return sorted(f for f in (ROOT / "benchmarks").glob("*.py")
                  if "CRITERIA" in f.read_text(encoding="utf-8") and "criteria.json" in f.read_text(encoding="utf-8"))


def t_registered_tests_guard_themselves():
    """Every pre-registered benchmark checks its code is committed and its data are pinned before it
    runs, and refuses criteria that differ from its registration."""
    bad = []
    for f in _registered_benchmarks():
        s = f.read_text(encoding="utf-8")
        miss = [c for c in ("require_clean(", "require_data(", "criteria_differ(") if c not in s]
        if miss:
            bad.append(f"{f.name}: {miss}")
    n = len(_registered_benchmarks())
    return n >= 10 and not bad, (f"{n} registered benchmarks call require_clean, require_data and criteria_differ"
                                 if not bad else f"missing guards: {bad}")


def t_registrations_never_changed():
    """Each committed registration (results/*/criteria.json) was committed once, never changed or deleted,
    and the file on disk is the committed one. Needs the full git history (skipped in a shallow clone)."""
    def git(*a):
        r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout
    code, shallow = git("rev-parse", "--is-shallow-repository")
    if code != 0:
        return True, "SKIPPED: not a git checkout"
    if shallow.strip() == "true":
        return True, "SKIPPED: shallow clone (no history to check)"
    bad, n = [], 0
    # every registration ever added, including any later deleted (a deleted one could register afresh)
    _, added = git("log", "--diff-filter=A", "--name-only", "--format=", "--", "results/*/criteria.json")
    ever = sorted({ROOT / x for x in added.split()} | set((ROOT / "results").glob("*/criteria.json")))
    for f in ever:
        rel = f.relative_to(ROOT).as_posix()
        if not f.exists():
            bad.append(f"{rel}: registered and later deleted")
            continue
        _, log = git("log", "--format=%H", "--", rel)
        commits = log.split()
        if not commits:
            continue                                    # not committed yet: a new registration in progress
        n += 1
        _, deleted = git("log", "--format=%h", "--diff-filter=D", "--", rel)
        _, first = git("show", f"{commits[-1]}:{rel}")
        if len(commits) != 1 or deleted.split() or first != f.read_text(encoding="utf-8"):
            bad.append(f"{rel}: {len(commits)} commits, deleted in {deleted.split() or 'none'}, "
                       f"on disk {'matches' if first == f.read_text(encoding='utf-8') else 'differs from'} the registration")
    return n > 0 and not bad, f"{n} registrations: one commit each, unchanged on disk" if not bad else "; ".join(bad)


def t_summary_counts_and_flags(tmp):
    """summarize.py on four made-up reports: the headline counts equal the PASS and FAIL rows, the role
    tallies sum to the headline, and every flag is raised where it should be and nowhere else."""
    w = tmp / "sm"; (w / "results").mkdir(parents=True)
    good = dict(written_at="2026-10-11T12:00:00", git_commit="", git_dirty=False, env={},
                data=dict(dir="data", digests={"neurons.parquet": "a", "edges.parquet": "b"}, manifest="match"))
    reps = {
        "gf_escape": dict(n_trials=40, provenance=good,
                          checks={"gf_spikes_per_response_1_to_2": True, "gf_response_prob_0.5_to_1": False}),
        "auditory": dict(n_trials=10, provenance={**good, "env": {"FLYCNS_WSCALE": "0.5", "FLYCNS_ALLOW_DIRTY": "1"},
                                                  "git_dirty": True, "allow_dirty": True,
                                                  "data": {**good["data"], "manifest": "mismatch"}},
                         checks={"A1_jo_alone_mostly_subthreshold": True, "A2_jo_effect_on_near_threshold_loom_REPORTED": None},
                         # in band on its point value, but the interval crosses the edge: not a pass
                         uncertainty={"A1_jo_alone_mostly_subthreshold": dict(
                             estimate=0.1, ci95=[0.02, 0.4], band=[0, 0.3], method="wilson", verdict="UNRESOLVED")}),
        "pc1_song": dict(provenance={**good, "written_at": "2026-10-11T09:00:00", "data": None},
                         checks={"P1_pc1_14a_pulse_over_sine": True}),
        "sugar_laterality": dict(checks={"L1_sugar_contralateral_bias": False}),
    }
    for b, r in reps.items():
        (w / "results" / b).mkdir()
        (w / "results" / b / "report.json").write_text(json.dumps({"benchmark": b, **r}), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "benchmarks/summarize.py")], cwd=w, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env={k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_")})
    if r.returncode != 0:
        return False, r.stderr.strip()[-200:]
    md = (w / "results/SUITE.md").read_text(encoding="utf-8")
    import re
    checks = md.split("## Checks")[1].split("\n## ")[0]
    rows = [l.split("|")[1:-1] for l in checks.splitlines() if l.startswith("| ") and l.count("|") == 7
            and not l.startswith("| benchmark")]
    rows = {(c[0].strip(), c[1].strip()): (c[2].strip(), c[4].strip(), c[5].strip()) for c in rows}
    n_pass = sum(v[0] == "PASS" for v in rows.values()); n_scored = sum(v[0] in ("PASS", "FAIL", "UNRESOLVED") for v in rows.values())
    head = re.search(r"\*\*(\d+)/(\d+) checks pass", md)
    tallies = re.findall(r"(\w+) (\d+)/(\d+)", md.split("**By role:**")[1].splitlines()[0])
    want = {"gf_escape": set(), "auditory": {"PERTURBED", "DIRTY", "ALLOW-DIRTY", "DATA-MISMATCH", "TRIALS 10<40"},
            "pc1_song": {"UNPINNED", "STALE"}, "sugar_laterality": {"UNSTAMPED"}}
    got = {b: {x.strip() for x in v[2].split(",") if x.strip() not in ("-", "")} for (b, _), v in rows.items()}
    flags_ok = all(got[b] == want[b] for b in want)
    unresolved_ok = rows[("auditory", "A1_jo_alone_mostly_subthreshold")][0] == "UNRESOLVED" and "1 are UNRESOLVED" in md
    ok = (head and (int(head[1]), int(head[2])) == (n_pass, n_scored) == (2, 5)
          and sum(int(t[2]) for t in tallies) == n_scored and sum(int(t[1]) for t in tallies) == n_pass
          and "NOT all under the declared parameter set" in md and flags_ok and unresolved_ok)
    return ok, ("headline 2/5 equals the rows (an in-band point with an interval across the edge is UNRESOLVED, "
                "not a pass); role tallies sum to it; all eight flags exactly where expected" if ok else
                f"head {head and head.group(0)}, rows {n_pass}/{n_scored}, tallies {tallies}, flags {got}, "
                f"unresolved {unresolved_ok}")


def t_side_inference_precedence():
    """somaSide first, then the instance suffix, then soma position against the midline, else unknown."""
    from flycns.graph import infer_side
    meta = pd.DataFrame(dict(somaSide=["R", None, None, None, "L", None, "M"],
                             instance=["x_L", "x_R", None, "x", None, None, None],
                             x=[0.0, 0.0, -5.0, 5.0, -1.0, np.nan, 9.0]))
    got = [None if pd.isna(x) else x for x in infer_side(meta)]
    want = ["R", "R", "L", "R", "L", None, "R"]
    return got == want, f"{got}" + ("" if got == want else f" (want {want})")


def t_electrical_pairs_by_side():
    """An ipsilateral electrical synapse joins each sided partner to the post cell(s) on its own side only;
    an unsided partner, or one with no post cell on its side, reaches every post cell. The compound
    calibration counts the mean population per side."""
    from flycns.graph import electrical_pairs
    rows = [dict(bodyId=1, type="DNp01", somaSide="L"), dict(bodyId=2, type="DNp01", somaSide="R")]
    rows += [dict(bodyId=10 + i, type="JO-B1_a", somaSide="L") for i in range(4)]
    rows += [dict(bodyId=20 + i, type="JO-B1_c", somaSide="R") for i in range(2)]
    rows += [dict(bodyId=30, type="JO-B1_a", somaSide=None)]
    rows += [dict(bodyId=40, type="TTMn", somaSide="L")]                     # no right TTMn
    rows += [dict(bodyId=3, type="PSI", somaSide="L"), dict(bodyId=4, type="PSI", somaSide="R")]
    n = pd.DataFrame(rows)
    p = electrical_pairs(n)
    jo = p[p.post_type == "DNp01"]
    by_pre = jo.groupby("pre")["post"].apply(set).to_dict()
    side_ok = all(by_pre[b] == {1} for b in range(10, 14)) and all(by_pre[b] == {2} for b in (20, 21)) \
        and by_pre[30] == {1, 2}
    ttmn = p[p.post_type == "TTMn"].groupby("pre")["post"].apply(set).to_dict()
    fallback_ok = ttmn == {1: {40}, 2: {40}}
    # n_conv = mean per side (4 left, 2 right -> 3) + 1 unsided = 4; spikelet = 3 mV*1.2/(4*150 Hz*20 ms)
    spk = jo.spikelet_mV.iloc[0]
    calib_ok = abs(spk - 3.0 * 1.2 / (4 * 150 * 0.020)) < 1e-9
    ok = side_ok and fallback_ok and calib_ok
    return ok, (f"sided partners stay on their side, unsided reach both, no same-side post falls back to all; "
                f"spikelet {spk:.3f} mV for n_conv 4" if ok else f"sides {by_pre}, TTMn {ttmn}, spikelet {spk}")


def t_compound_potential_hits_its_target():
    """Ear afferents on one side, all firing at 150 Hz (Poisson), depolarise their giant fiber by the
    declared 3 mV compound potential, within 10%."""
    from brian2 import mV
    from flycns import CNSModel, LIFParams
    k = 8
    rows = [dict(bodyId=1, type="DNp01", superclass="descending_neuron", somaSide="L")]
    rows += [dict(bodyId=10 + i, type="JO-B1_a", superclass="cb_sensory", somaSide="L") for i in range(k)]
    rows += [dict(bodyId=99, type="dummy", superclass="central", somaSide="L")]
    neurons = pd.DataFrame(rows)
    edges = pd.DataFrame(dict(pre=[99], post=[1], weight=[5], nt=["acetylcholine"], sign=[1.0]))
    m = CNSModel(neurons, edges, ["JO-B1_a"], LIFParams(), electrical=True, monitor_types=("DNp01",))
    m.set_stim_rates(np.full(len(m.stim), 150.0))
    m.run(1500)
    v = np.asarray(m.vmon.v / mV)[0]
    dep = float(v[len(v) // 3:].mean() - LIFParams().v_rest_mV)
    ok = abs(dep - 3.0) <= 0.3
    return ok, f"{k} afferents at 150 Hz: giant fiber {dep:.2f} mV above rest (target 3.0 +/- 0.3)"


def t_audit_refuses_missing_partner(tmp):
    """The stimulus audit fails when a declared electrical partner type is absent from the data."""
    d = tmp / "au"; d.mkdir()
    subprocess.run([sys.executable, str(ROOT / "scripts/make_testdata.py")], cwd=d, capture_output=True, check=True)
    run = lambda: subprocess.run([sys.executable, str(ROOT / "fit/audit_stimuli.py"), str(d / "testdata")],  # noqa: E731
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
    full = run()
    n = pd.read_parquet(d / "testdata/neurons.parquet")
    n[n.type != "JO-B1_c"].to_parquet(d / "testdata/neurons.parquet", index=False)
    cut = run()
    ok = full.returncode == 0 and cut.returncode != 0 and "MISSING" in cut.stdout
    return ok, "complete toy passes; without JO-B1_c the audit fails" if ok else \
        f"full exit {full.returncode}, cut exit {cut.returncode}: {cut.stdout[-200:]}"


def t_preserved_restores_exactly(tmp):
    """Results put under preserved() come back byte for byte after an error and after Ctrl+C, and a path
    that did not exist before is removed."""
    from flycns.integrity import preserved
    d = tmp / "pv"; (d / "res").mkdir(parents=True)
    (d / "res/a.json").write_text('{"x": 1}', encoding="utf-8"); (d / "one.txt").write_bytes(b"\x00\x01")
    before = {p.relative_to(d).as_posix(): p.read_bytes() for p in d.rglob("*") if p.is_file()}
    results = []
    for exc in (RuntimeError("boom"), KeyboardInterrupt()):
        try:
            with preserved(d / "res", d / "one.txt", d / "new"):
                (d / "res/a.json").write_text('{"x": 2}', encoding="utf-8"); (d / "res/b.json").write_text("{}", encoding="utf-8")
                (d / "one.txt").unlink(); (d / "new").mkdir(); (d / "new/z").write_text("z", encoding="utf-8")
                raise exc
        except (RuntimeError, KeyboardInterrupt):
            pass
        after = {p.relative_to(d).as_posix(): p.read_bytes() for p in d.rglob("*") if p.is_file()}
        results.append(after == before and not (d / "new").exists())
    return all(results), "restored exactly after an error and after Ctrl+C" if all(results) else str(results)


def t_null_side_mode_and_default_table():
    """The superclass_side null keeps every target's class, side and in-degree; without an explicit neuron
    table it uses the one the last load_graph read, giving the same result as passing it."""
    from collections import Counter
    from flycns import graph
    from flycns.graph import infer_side, rewire_null
    n, e = _tables()
    e = e[e.pre.isin(n.bodyId[:10])].reset_index(drop=True)   # senders never receive: no self-loop can form,
    a = rewire_null(e, seed=5, mode="superclass_side", neurons=n)   # so rows stay aligned with the input
    meta = n.set_index("bodyId"); grp = meta["superclass"] + "|" + infer_side(meta).fillna("?")
    groups_ok = len(a) == len(e) and (grp[e.post].values == grp[a.post].values).all()
    degree_ok = Counter(e.post) == Counter(a.post) and not a.post.equals(e.post)
    saved = graph._LAST.get("neurons")
    try:
        graph._LAST["neurons"] = n
        default_ok = rewire_null(e, seed=5, mode="superclass_side").equals(a)
    finally:
        graph._LAST["neurons"] = saved
    ok = groups_ok and degree_ok and default_ok
    return ok, (f"{len(e)} edges shuffled; every target keeps class, side and in-degree; the default table is the "
                f"last one loaded" if ok else f"groups {groups_ok}, degree {degree_ok}, default {default_ok}")


def t_every_named_script_exists():
    """Every script the menu, the suite runners and the cloud workflow name exists in the repository."""
    import re
    srcs = ["fly.py", "scripts/run_all.py", "scripts/overnight.py", "scripts/canonical_rerun.py",
            ".github/workflows/rerun.yml", ".github/workflows/regression.yml", "tests/regression.py"]
    named, missing = set(), []
    for s in srcs:
        t = (ROOT / s).read_text(encoding="utf-8").replace("\\\\", "/").replace("\\", "/")
        for m in re.findall(r"((?:benchmarks|fit|scripts|viz|tests)/[A-Za-z0-9_/]+\.py)", t):
            named.add(m)
    missing = sorted(m for m in named if not (ROOT / m).exists())
    return not missing and len(named) > 20, (f"all {len(named)} named scripts exist" if not missing else f"missing: {missing}")



def t_stats_rules():
    """flycns/stats.py: Wilson limits, the three-way verdict at each band edge, per-draw scoring, the
    null percentile (a silent null scores nothing) and a reproducible bootstrap."""
    from flycns import stats as S
    lo, hi = S.wilson(23, 40)
    cases = [S.verdict(0.42, 0.71, 0.5, 1.0) == "UNRESOLVED", S.verdict(0.55, 0.9, 0.5, 1.0) == "PASS",
             S.verdict(0.1, 0.4, 0.5, 1.0) == "FAIL", S.verdict(0.0, 0.2, 0, strict=True) == "UNRESOLVED",
             S.verdict(-0.2, 0.0, 0, strict=True) == "FAIL", S.verdict(float("nan"), 1, 0, 1) == "UNRESOLVED",
             S.per_draw([6.48, 0, 0, 12.12, 15.23], 2, 12)["verdict"] == "FAIL",
             S.per_draw([3, 4, 5, 6, 30], 2, 12)["verdict"] == "PASS",
             S.per_draw([3, 4, 30, 40, 5], 2, 12)["verdict"] == "UNRESOLVED",
             S.null_percentile(0.6, [0.0] * 20)["verdict"] == "PASS",
             S.null_percentile(0.6, [0.0] * 20, null_alive=False)["verdict"] == "UNRESOLVED",
             S.null_percentile(0.3, [0.0] * 10 + [0.5] * 10)["verdict"] == "UNRESOLVED",
             S.null_percentile(0.0, [0.0] * 20)["verdict"] == "FAIL",
             S.bootstrap([1, 2, 3, 4, 9]) == S.bootstrap([1, 2, 3, 4, 9]),
             abs(lo - 0.4220) < 1e-4 and abs(hi - 0.7149) < 1e-4]
    return all(cases), (f"Wilson 23/40 = {lo:.4f}-{hi:.4f}; all {len(cases)} verdict rules hold" if all(cases)
                        else f"failing cases: {[i for i, c in enumerate(cases) if not c]}")


def t_degree_corrected_null(tmp):
    """The degree-corrected null keeps, for every cell, its incoming connections per sign and size class,
    its class and its neuropil; every sender keeps its outgoing rows; and it actually moves targets."""
    from collections import Counter
    from flycns.graph import WEIGHT_BINS, rewire_null
    rng = np.random.default_rng(4)
    n = pd.DataFrame(dict(bodyId=np.arange(600), superclass=rng.choice(["a", "b"], 600), type="t", somaSide="L"))
    e = pd.DataFrame(dict(pre=rng.integers(0, 60, 20000), post=rng.integers(60, 600, 20000),
                          weight=rng.integers(5, 300, 20000)))
    e["sign"] = rng.choice([1.0, -1.0], len(e))
    d = tmp / "dc"; d.mkdir()
    roi = pd.DataFrame(dict(bodyId=n.bodyId, dominant_roi=rng.choice(["GNG", "SMP(R)", "LAL(L)"], 600)))
    roi.to_parquet(d / "roi_membership.parquet", index=False)
    a = rewire_null(e, seed=2, mode="degree_corrected", neurons=n, data_dir=str(d))
    key = lambda x: Counter(zip(x.post, np.sign(x.sign), np.digitize(x.weight, WEIGHT_BINS)))  # noqa: E731
    grp = (n.set_index("bodyId")["superclass"] + "|" + roi.set_index("bodyId")["dominant_roi"])
    ok = (key(a) == key(e) and len(a) == len(e) and (a.pre.values == e.pre.values).all()
          and (grp[a.post].values == grp[e.post].values).all() and (a.post.values != e.post.values).mean() > 0.5
          and a.attrs.get("neuropil_source") == "roi_membership.parquet")
    return ok, (f"{len(e):,} connections: every cell keeps its input per sign and size, class and neuropil; "
                f"{(a.post.values != e.post.values).mean():.0%} of targets moved" if ok else str(a.attrs))


def t_jon_contact_modes():
    """The JON -> GF contact: declared as calibrated coupling (EM chemical synapses removed); as EM
    annotates it (chemical kept, no coupling); sign-inverted; and the compound potential is settable."""
    from flycns.graph import drop_mixed_chemical, electrical_pairs
    rows = [dict(bodyId=1, type="DNp01", somaSide="L"), dict(bodyId=2, type="TTMn", somaSide="L")]
    rows += [dict(bodyId=10 + i, type="JO-B1_a", somaSide="L") for i in range(4)]
    n = pd.DataFrame(rows)
    e = pd.DataFrame(dict(pre=[10, 11, 2], post=[1, 1, 1], weight=[20, 20, 9], sign=[1.0, 1.0, 1.0]))
    out = {}
    saved = {k: os.environ.pop(k, None) for k in ("FLYCNS_JON", "FLYCNS_JON_MV")}
    try:
        for mode, mv in (("electrical", None), ("em", None), ("em_flip", None), ("electrical", "1.5")):
            os.environ["FLYCNS_JON"] = mode
            if mv:
                os.environ["FLYCNS_JON_MV"] = mv
            p = electrical_pairs(n)
            jo = p[p.pre_type == "JO-B1_a"]
            d = drop_mixed_chemical(e, n)
            jon = d[d.pre.isin([10, 11])]
            out[(mode, mv)] = (len(jo), float(jo.spikelet_mV.iloc[0]) if len(jo) else None,
                               len(jon), float(jon.sign.sum()) if len(jon) else 0.0, len(p[p.pre_type == "DNp01"]))
            os.environ.pop("FLYCNS_JON_MV", None)
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    dec, em, flip, low = out[("electrical", None)], out[("em", None)], out[("em_flip", None)], out[("electrical", "1.5")]
    ok = (dec[0] == 4 and dec[2] == 0 and em[0] == 0 and em[2] == 2 and em[3] == 2.0 and flip[3] == -2.0
          and all(x[4] == 1 for x in out.values()) and abs(low[1] / dec[1] - 0.5) < 1e-9)
    return ok, ("declared: coupling, EM synapses removed; em: chemical kept, no coupling; em_flip: sign inverted; "
                "the GF -> TTMn relay stays in every mode; 1.5 mV halves the spikelet" if ok else str(out))


def t_vnc_glutamate_option(tmp):
    """FLYCNS_GLU_VNC=excitatory makes glutamate from nerve-cord neurons excitatory onto non-motor targets
    only; the declared model keeps it inhibitory everywhere."""
    from flycns import graph, integrity
    d = tmp / "glu"; d.mkdir()
    n = pd.DataFrame(dict(bodyId=[1, 2, 3, 4], type=["a", "b", "c", "d"], somaSide="L",
                          superclass=["vnc_intrinsic", "vnc_intrinsic", "vnc_motor", "cb_intrinsic"]))
    e = pd.DataFrame(dict(pre=[1, 1, 4, 1], post=[2, 3, 2, 4], weight=[5, 10, 10, 10],
                          nt=["glutamate", "glutamate", "glutamate", "gaba"]))
    n.to_parquet(d / "neurons.parquet", index=False); e.to_parquet(d / "edges.parquet", index=False)
    integrity._ANNOUNCED = True
    _, base = graph.load_graph(str(d))
    os.environ["FLYCNS_GLU_VNC"] = "excitatory"
    try:
        _, alt = graph.load_graph(str(d))
    finally:
        del os.environ["FLYCNS_GLU_VNC"]
    s = alt.set_index(["pre", "post"])["sign"]
    ok = ((base["sign"] == -1).all() and s[(1, 2)] == 1 and s[(1, 3)] == -1 and s[(4, 2)] == -1 and s[(1, 4)] == -1
          and integrity.LOADED["n_glu_vnc_flipped"] == 1)
    return ok, ("only nerve-cord glutamate onto a non-motor target turns excitatory (1 of 4 edges)" if ok
                else str(alt[["pre", "post", "nt", "sign"]].to_dict("records")))

def run_all():
    out = []
    tmp = Path(tempfile.mkdtemp(prefix="flycns_unit_"))
    try:
        for name, fn in [("fingerprint ignores order, catches edits", lambda: t_fingerprint_invariance(tmp)),
                         ("manifest write / verify / mismatch", lambda: t_manifest_roundtrip(tmp)),
                         ("global null unchanged", t_null_global_unchanged),
                         ("superclass null keeps class structure", t_null_superclass),
                         ("min_weight override + provenance", lambda: t_min_weight_and_provenance(tmp)),
                         ("targeted flip refuses without its table", lambda: t_targeted_flip_needs_its_table(tmp)),
                         ("signs come from one map", lambda: t_signs_come_from_one_map(tmp)),
                         ("one membrane time constant", t_one_membrane_time_constant),
                         ("registered tests can be rerun", lambda: t_registered_criteria_rerun(tmp)),
                         ("settings banner", t_settings_banner),
                         ("registered tests refuse dirty code", lambda: t_clean_tree_guard(tmp)),
                         ("registrations cannot be edited or rewritten", lambda: t_registration_guard(tmp)),
                         ("fingerprint cache cannot vouch for data", lambda: t_fingerprint_cache_cannot_vouch(tmp)),
                         ("menu 51 refuses environment overrides", t_refuse_overrides),
                         ("every scored check has a role", t_every_check_has_a_role),
                         ("every file parses on this Python", t_all_sources_parse),
                         ("text I/O is explicitly UTF-8", t_text_io_is_utf8),
                         ("token read in every Windows format", lambda: t_token_file_formats(tmp)),
                         ("both engines give identical spikes", t_engines_identical),
                         ("stimulus choice keeps excitability", t_stimulus_choice_keeps_excitability),
                         ("peptide acts from a stimulated source", t_peptide_reaches_targets),
                         ("sign flips invert exactly what they say", lambda: t_sign_flips_are_exact(tmp)),
                         ("the seed reaches the model", lambda: t_seed_reaches_the_model(tmp)),
                         ("the manifest pins every input table", t_manifest_pins_every_input_table),
                         ("registered tests guard themselves", t_registered_tests_guard_themselves),
                         ("registrations were never changed", t_registrations_never_changed),
                         ("summary counts and flags", lambda: t_summary_counts_and_flags(tmp)),
                         ("side inference precedence", t_side_inference_precedence),
                         ("electrical synapses respect sides", t_electrical_pairs_by_side),
                         ("compound potential hits its target", t_compound_potential_hits_its_target),
                         ("audit refuses a missing partner", lambda: t_audit_refuses_missing_partner(tmp)),
                         ("preserved() restores exactly", lambda: t_preserved_restores_exactly(tmp)),
                         ("side null and its default table", t_null_side_mode_and_default_table),
                         ("every named script exists", t_every_named_script_exists),
                         ("uncertainty rules", t_stats_rules),
                         ("degree-corrected null invariants", lambda: t_degree_corrected_null(tmp)),
                         ("JON -> GF contact modes", t_jon_contact_modes),
                         ("nerve-cord glutamate option", lambda: t_vnc_glutamate_option(tmp))]:
            try:
                ok, msg = fn()
            except (Exception, SystemExit) as ex:  # a crashing or exiting check is a failing check
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
