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
    ok = ("RAN" in first.stdout and edited.returncode != 0 and committed_edit.returncode != 0
          and "changed after it was committed" in committed_edit.stderr
          and rewritten.returncode != 0 and "deleted and written again" in rewritten.stderr)
    return ok, "an edited, re-committed or deleted-and-rewritten registration is refused" if ok else \
        f"first={first.stdout!r} edited={edited.returncode} committed={committed_edit.stderr[-160:]!r} rewritten={rewritten.stderr[-160:]!r}"


def t_fingerprint_cache_cannot_vouch(tmp):
    """Registered tests rehash from content: a tampered fingerprint cache cannot make data 'match', and a
    changed file is never served from the cache."""
    from flycns import integrity
    d = tmp / "fp"; d.mkdir()
    n, e = _tables()
    e.to_parquet(d / "edges.parquet", index=False)
    true = integrity.fingerprints(d)["edges.parquet"]["digest"]
    cf = d / integrity.CACHE
    cache = json.loads(cf.read_text(encoding="utf-8"))
    cf.write_text(json.dumps({k: {**v, "digest": "0" * 64} for k, v in cache.items()}), encoding="utf-8")
    trusted = integrity.fingerprints(d)["edges.parquet"]["digest"]
    fresh = integrity.fingerprints(d, fresh=True)["edges.parquet"]["digest"]
    e2 = e.copy(); e2.loc[0, "weight"] += 1
    e2.to_parquet(d / "edges.parquet", index=False)
    changed = integrity.fingerprints(d)["edges.parquet"]["digest"]
    ok = trusted == "0" * 64 and fresh == true and changed not in (true, "0" * 64)
    return ok, "fresh rehash ignores a tampered cache; a changed file is rehashed" if ok else f"{trusted[:8]} {fresh[:8]} {changed[:8]}"


def t_refuse_overrides():
    """Menu 51 refuses a model setting left in the environment, and allows engine plumbing."""
    code = "from flycns.integrity import refuse_overrides; refuse_overrides('menu 51'); print('RAN')"
    base = {k: v for k, v in os.environ.items() if not k.startswith("FLYCNS_")}
    bad = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                         errors="replace", env={**base, "FLYCNS_WSCALE": "0.5"})
    fine = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env={**base, "FLYCNS_WSCALE": "0.3", "FLYCNS_CODEGEN": "numpy"})
    ok = bad.returncode != 0 and "FLYCNS_WSCALE=0.5" in bad.stderr and "RAN" in fine.stdout
    return ok, "an override is refused; a default value and the engine choice are not" if ok else f"{bad.stderr[-160:]!r} {fine.stdout!r}"


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
        and np.allclose(a.t_ms.values, b.t_ms.values)
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
    for label, stim in (("source simulated", ["L3", "L5"]), ("source stimulated", ["L3", "L5", "Pm3"])):
        m = CNSModel(neurons, edges, stim, LIFParams(peptide_gain_scale=1.0), electrical=False)
        rates = np.where(m.stim["type"].isin(["Pm3", "L3", "L5"]), 100.0, 0.0)
        m.set_stim_rates(rates)
        m.run(300)
        tgt = np.flatnonzero(np.asarray(m.G.pep_gain) > 0)
        out[label] = (len(m.peptides_applied), float(np.asarray(m.G.pep)[tgt].max()) if len(tgt) else 0.0)
    ok = out["source stimulated"][0] == 1 and out["source stimulated"][1] > 0
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
                         ("peptide acts from a stimulated source", t_peptide_reaches_targets)]:
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
