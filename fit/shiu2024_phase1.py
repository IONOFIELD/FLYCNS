"""
Phase-1 positive control (Gen 5): the flycns simulator in Shiu-compatible settings on Shiu et al. 2024's own
FlyWire v630 data (A1), its weight-shuffle control (S6), the ladder from A1 back to flycns's settings (L1-L6, Le;
reported, not scored) and the male CNS under the same settings (M1).

Criteria, copied unchanged from committed registrations written before any of this existed, and checked
against them at every run:
  results/shiu2024_a0/registration_v4.json                 preregistered_phase1: data, A1 settings, S1-S6, M1,
                                                           ladder, decision rule
  results/shiu2024_phase1_addendum/registration_v4.json    A1 exact integration; M1 at a floor of 5; ladder Le
  results/shiu2024_s4b/registration_v4.json                S4b: the published dose curve, point by point
  results/shiu2024_s5b/registration_v4.json                S5b: the published bitter curve, point by point
This file adds only what those leave to the implementation (arms, seeds, readouts, the shuffle, the meaning of
"A1 passes"), registered with it before any A1 or M1 run.

    python fit/shiu2024_phase1.py parts                       the cloud jobs and their arms
    python fit/shiu2024_phase1.py part <part> [shiu_repo]     run one job's arms, in parallel processes
    python fit/shiu2024_phase1.py arm <arm> [shiu_repo]       run one arm (results/shiu2024_phase1/arms/<arm>.json)
    python fit/shiu2024_phase1.py score [shiu_repo]           score every check from the arms; write phase1.json
    python fit/shiu2024_phase1.py extension <k> <n> [repo]    share k of n of the registered one-time extension
Its report is results/shiu2024_phase1/phase1.json, not report.json: a diagnostic of the simulator against a
reference model, kept out of the model's own scoreboard (benchmarks/summarize.py reads */report.json), as A0's
a0.json is.
shiu_repo defaults to $SHIU_REPO: github.com/philshiu/Drosophila_brain_model at the registered commit.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns import registry, stats  # noqa: E402
from flycns.integrity import require_clean, refuse_overrides  # noqa: E402

LABEL = "shiu2024_phase1"
OUT = ROOT / "results" / LABEL
SOURCES = {"preregistered": "results/shiu2024_a0/registration_v4.json",
           "addendum": "results/shiu2024_phase1_addendum/registration_v4.json",
           "s4b": "results/shiu2024_s4b/registration_v4.json",
           "s5b": "results/shiu2024_s5b/registration_v4.json"}
MN9_CONTRA, MN9_IPSI = 720575940660219265, 720575940645521262
COMP, CON = "2023_03_23_completeness_630_final.csv", "2023_03_23_connectivity_630_final.parquet"
PUBLISHED_100 = "results/example/sugarR_100Hz.parquet"
TRIALS, TRIAL_MS = 30, 1000
T_SHUFFLE = 51.4
BAND_CONTRA, BAND_IPSI, MARGIN = 6.7, 4.86, 6.7


def _source(key):
    rec = json.loads((ROOT / SOURCES[key]).read_text(encoding="utf-8"))
    return dict(file=SOURCES[key], git_commit=rec.get("git_commit"), registered_at=rec.get("registered_at"),
                criteria=rec["criteria"])


SRC = {k: _source(k) for k in SOURCES}
PRE = SRC["preregistered"]["criteria"]["preregistered_phase1"]
REF = SRC["preregistered"]["criteria"]["reference"]          # Shiu repository commit and file sha256

# The settings. A1 = the registered a1_settings plus the addendum's exact integration.
A1 = dict(reset="v_and_g", stimulation="kick", integration="exact", adaptation=False, w_scale=1.0, floor=1)
FLYCNS = dict(reset="v", stimulation="source", integration="euler", adaptation=True, w_scale=0.4, floor=5)
LADDER = {"L1_reset": ["reset"], "L2_stimulation": ["stimulation"], "L3_floor5": ["floor"],
          "L4_wscale04": ["w_scale"], "L5_adaptation": ["adaptation"], "Le_euler": ["integration"],
          "L6_all": ["reset", "stimulation", "floor", "w_scale", "adaptation", "integration"]}


def _arms():
    arms = {}
    seed = 0

    def add(name, **spec):
        nonlocal seed
        seed += 1
        arms[name] = dict(seed=seed, **{"trials": TRIALS, **spec})
    for s in (50, 100, 150, 200):
        add(f"a1_sugar{s}", data="flywire", settings=A1, sugar_hz=s, bitter_hz=0)
    for b in (20, 40, 50, 60, 80, 100, 120, 150, 200):
        add(f"a1_sugar100_bitter{b}", data="flywire", settings=A1, sugar_hz=100, bitter_hz=b)
    for k in range(4):
        add(f"a1_shuffle{k}", data="flywire", settings=A1, sugar_hz=100, bitter_hz=0, kind="shuffle",
            shuffles=list(range(25 * k, 25 * k + 25)), trials=1)
    for name, keys in LADDER.items():
        add(name, data="flywire", settings={**A1, **{k: FLYCNS[k] for k in keys}}, sugar_hz=100, bitter_hz=0)
    add("m1_male", data="malecns", settings={**A1, "floor": 5}, sugar_hz=100, bitter_hz=0)
    return arms


ARMS = _arms()
PARTS = {"p1-dose-a": ["a1_sugar50", "a1_sugar100"], "p1-dose-b": ["a1_sugar150", "a1_sugar200"],
         "p1-bitter-a": ["a1_sugar100_bitter20", "a1_sugar100_bitter40"],
         "p1-bitter-b": ["a1_sugar100_bitter50", "a1_sugar100_bitter60"],
         "p1-bitter-c": ["a1_sugar100_bitter80", "a1_sugar100_bitter100"],
         "p1-bitter-d": ["a1_sugar100_bitter120", "a1_sugar100_bitter150"],
         "p1-bitter-e": ["a1_sugar100_bitter200"],
         "p1-shuffle-a": ["a1_shuffle0", "a1_shuffle1"], "p1-shuffle-b": ["a1_shuffle2", "a1_shuffle3"],
         "p1-ladder-a": ["L1_reset", "L2_stimulation"], "p1-ladder-b": ["L3_floor5", "L4_wscale04"],
         "p1-ladder-c": ["L5_adaptation", "Le_euler"], "p1-ladder-d": ["L6_all"], "p1-m1": ["m1_male"]}
assert sorted(a for p in PARTS.values() for a in p) == sorted(ARMS), "every arm in exactly one part"

S5_RATES = [0, 50, 100, 150, 200]
S4_RATES = [50, 100, 150, 200]
S5B_RATES = [0, 20, 40, 60, 80, 100, 120, 200]


def arm_of(sugar, bitter):
    return f"a1_sugar{sugar}" if not bitter else f"a1_sugar{sugar}_bitter{bitter}"


# The single extension (A1 definition): 30 more trials of an arm, with its own seed, only when needed.
EXT = {f"{a}_ext": dict(ARMS[a], seed=100 + ARMS[a]["seed"], extension_of=a)
       for a in ARMS if ARMS[a].get("kind") != "shuffle"}
ALL_ARMS = {**ARMS, **EXT}
COUNTED = ["S1_sugar_mn9_magnitude", "S2_reliability", "S3_laterality", "S4b_dose_curve_matches_published",
           "S5_bitter_suppression", "S5b_bitter_curve_matches_published", "S6_wiring_control"]
FEEDS = {"S1_sugar_mn9_magnitude": ["a1_sugar100"], "S3_laterality": ["a1_sugar100"],
         "S4b_dose_curve_matches_published": [arm_of(s, 0) for s in S4_RATES],
         "S5_bitter_suppression": [arm_of(100, b) for b in S5_RATES],
         "S5b_bitter_curve_matches_published": [arm_of(100, b) for b in S5B_RATES], "M1_male_mn9": ["m1_male"]}
# for a check made of parts, the arms feeding each part, in the order the parts are scored
PART_FEEDS = {"S3_laterality": [["a1_sugar100"], ["a1_sugar100"]],
              "S4b_dose_curve_matches_published": [[arm_of(s, 0)] for s in S4_RATES],
              "S5_bitter_suppression": [[arm_of(100, 0), arm_of(100, 100)], [arm_of(100, b) for b in S5_RATES]],
              "S5b_bitter_curve_matches_published": [[arm_of(100, b)] for b in S5B_RATES]}
REF_S6 = ROOT / "reference-runs" / "shiu2024_s6" / "s6.json"


CRITERIA = dict(
    question=("does the flycns simulator, set to Shiu et al. 2024's choices, reproduce their model's outputs on "
              "their own FlyWire v630 data (A1); and does the male CNS drive MN9 under the same choices (M1)?"),
    sources=SRC,
    implementation=dict(
        a1_settings=dict(A1, electrical=False, peptides=False, dt_ms=0.1, trial_ms=TRIAL_MS, trials=TRIALS,
                         stim_kick_mV=68.75,
                         note=("flycns.model.SimOptions(reset='v_and_g', stimulation='kick', integration='exact', "
                               "adaptation=False); LIFParams(w_scale=1.0); every connection of the repository "
                               "(floor 1); sign = its Excitatory column; electrical synapses off; peptides off")),
        data=dict(flywire=("the repository's completeness table (every neuron, its root id) and connectivity "
                           "table (pre, post, synapse count, Excitatory sign), verified against the sha256 of "
                           "the A0 registration; sugar and bitter GRNs: the neu_sugar and neu_bitter lists of "
                           "figures.ipynb; the two MN9s are labelled superclass cb_motor (they are the cells "
                           "flycns's motor adaptation would act on; ladder L5); no other cell is labelled"),
                  malecns=("data/ as pinned by data/MANIFEST.json, load_graph(min_weight=5, amines='excitatory'); "
                           "sugar: every LB3b and LB3c cell; MN9: every cell of type MN9")),
        arms=ARMS, parts=PARTS,
        trial=("restore the stored initial state, set the Poisson rates (sugar GRNs, bitter GRNs), run 1000 ms; "
               "spikes counted per neuron; one network per arm, built once; seeds 1, 2, ... in arm order; the "
               "random stream runs on across trials (Brian2 restore keeps it)"),
        shuffle=("S6: per shuffle k (0-99), the signed per-connection weights of the recurrent network are "
                 "permuted among the existing connections (numpy default_rng(10000 + k)), keeping the global "
                 "weight distribution; one 1000 ms trial at sugar 100 Hz; contralateral MN9 rate"),
        readouts=dict(mn9_contra=MN9_CONTRA, mn9_ipsi=MN9_IPSI,
                      m1="mean spikes per MN9 cell per second, per trial"),
        intervals="flycns.stats: percentile bootstrap, 2,000 resamples, seed 0; multi-arm statistics resample "
                  "every arm on its own",
        published=dict(s1_s3=f"{PUBLISHED_100} of the reference repository (as A0)",
                       s4b="the S4b registration's reference values", s5b="the S5b registration's reference values")),
    checks={
        "S1_sugar_mn9_magnitude": dict(band=[-BAND_CONTRA, BAND_CONTRA], arm="a1_sugar100"),
        "S2_reliability": dict(rule="contralateral MN9 fires in >= 29 of 30 trials", arm="a1_sugar100"),
        "S3_laterality": dict(bands=[[0.0, None], [-BAND_IPSI, BAND_IPSI]], arm="a1_sugar100"),
        "S4_calibration_reproduced": dict(band=[0.7, 0.9], arms=[arm_of(s, 0) for s in S4_RATES],
                                          note="the authors' own Fig 1 output also scores UNRESOLVED here (S4b)"),
        "S4b_dose_curve_matches_published": dict(bands=[[-MARGIN, MARGIN]] * 4, arms=[arm_of(s, 0) for s in S4_RATES]),
        "S5_bitter_suppression": dict(
            bands=[[0.0, None], [0.0, None]], arms=[arm_of(100, b) for b in S5_RATES],
            scored_as=("suppression = MN9(sugar 100) - MN9(sugar 100 + bitter 100), and minus the Spearman rho of "
                       "per-trial MN9 against bitter rate (150 trials): both intervals must lie above 0 (lower edge "
                       "exclusive), i.e. the registered 'below 0'; FAIL if either lies wholly at or below it")),
        "S5b_bitter_curve_matches_published": dict(bands=[[-MARGIN, MARGIN]] * 8,
                                                   arms=[arm_of(100, b) for b in S5B_RATES]),
        "S6_wiring_control": dict(rule=f"at most 5 of 100 shuffles reach {T_SHUFFLE} Hz contralateral MN9",
                                  arms=[f"a1_shuffle{k}" for k in range(4)]),
        "M1_male_mn9": dict(band=[0.5, None], arm="m1_male",
                            scored_as="PASS = responds (interval above 0.5 Hz, lower edge exclusive); FAIL = does not"),
    },
    a1_definition=dict(
        counted=COUNTED,
        principle=("reference-calibrated: a check counts towards A1 only if the reference model (Shiu et al.'s own "
                   "code, or its released output) passes it under the same procedure. A check the reference itself "
                   "cannot pass cannot tell the two simulators apart"),
        reference=dict(
            S1_S2_S3="A0 passed all three (reference run 1, results/shiu2024_a0/a0.json)",
            S4=("the reference's own Fig 1 output scores 0.705, 95% interval 0.686-0.724: UNRESOLVED, so S4 does "
                "not count; it is scored and reported"),
            S4b_S5b="the reference's released output is the comparison itself",
            S5=("the reference's released output passes on the rates it has (bitter 0, 100, 200 Hz; 50 and 150 Hz "
                "were not released): suppression 63.0 Hz (61.2 to 64.8), minus rho 0.946 (0.925 to 0.962)"),
            S6=("no released shuffle output. If A1's S6 FAILs, the reference's own code runs the same 100 "
                "shuffles (scripts/shiu2024_run_shuffles.py: the same permutation of the same weight array, in "
                "file order, one 1 s trial each, sugar 100 Hz, its own run settings); S6 then counts only if the "
                "reference passes it")),
        outcome="PASSES if every counted check PASSes; FAILS if any counted check FAILs; UNRESOLVED otherwise",
        extension=("once only, if A1 or M1 is UNRESOLVED: every arm feeding an UNRESOLVED counted check (for a "
                   "check made of parts, the arms feeding its UNRESOLVED parts), and M1's arm if M1 is UNRESOLVED, "
                   "runs 30 more trials as <arm>_ext (seed 100 + the arm's seed); the trials are pooled, every "
                   "check is scored once more on the pooled arms, and that outcome stands. No further extension; "
                   "an outcome still UNRESOLVED means the decision rule does not decide, and the phase stops for "
                   "review. Only if A1 FAILS is M1 not extended (the rule then says: bisect first)"),
        feeds=FEEDS, part_feeds=PART_FEEDS),
    ladder="reported, not scored: each rung's contralateral MN9 at sugar 100 Hz, and its difference from A1's",
    decision_rule=PRE["decision_rule"],
)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def shiu_repo(arg=None):
    repo = Path(arg or os.environ.get("SHIU_REPO") or "")
    if not repo.is_dir():
        raise SystemExit("[phase1] the reference repository is needed: pass its folder or set SHIU_REPO")
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()
    bad = [] if head == REF["commit"] else [f"commit {head or '?'} is not {REF['commit']}"]
    for rel in (COMP, CON, PUBLISHED_100, "figures.ipynb"):
        want, p = REF["sha256"].get(rel), repo / rel
        if want and (not p.exists() or sha256(p) != want):
            bad.append(f"{rel}: sha256 differs from the A0 registration")
    if bad:
        raise SystemExit("[phase1] reference repository differs from the registration: " + "; ".join(bad))
    return repo


def notebook_ids(repo, name):
    """A list literal `name = [...]` from figures.ipynb (the first cell that defines it, as the authors do)."""
    import ast
    nb = json.loads((repo / "figures.ipynb").read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code" and f"{name} = [" in src:
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
                    return [int(x) for x in ast.literal_eval(node.value)]
    raise SystemExit(f"figures.ipynb: no {name} list")


def flywire(repo, floor):
    """The v630 network as flycns tables: neurons (bodyId, type, superclass) and signed edges."""
    import pandas as pd
    from flycns.integrity import LOADED
    ids = pd.read_csv(repo / COMP, index_col=0).index.astype("int64")
    con = pd.read_parquet(repo / CON, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory"])
    sugar, bitter = notebook_ids(repo, "neu_sugar"), notebook_ids(repo, "neu_bitter")
    if (len(sugar), len(bitter)) != (21, 21):
        raise SystemExit(f"[phase1] expected 21 sugar and 21 bitter GRNs, found {len(sugar)} and {len(bitter)}")
    typ = pd.Series("fw", index=ids)
    typ[sugar], typ[bitter] = "fw_sugar_GRN", "fw_bitter_GRN"
    typ[MN9_CONTRA], typ[MN9_IPSI] = "fw_MN9_contra", "fw_MN9_ipsi"
    sc = pd.Series("", index=ids)
    sc[[MN9_CONTRA, MN9_IPSI]] = "cb_motor"
    neurons = pd.DataFrame({"bodyId": ids, "type": typ.values, "superclass": sc.values})
    edges = pd.DataFrame({"pre": con["Presynaptic_ID"].astype("int64"), "post": con["Postsynaptic_ID"].astype("int64"),
                          "weight": con["Connectivity"].astype("int64"), "sign": con["Excitatory"].astype(float)})
    edges = edges[edges["weight"] >= floor].reset_index(drop=True)
    LOADED.clear()          # no MaleCNS tables apply: region lookups fall back to type names (all 'other')
    LOADED.update(data_dir=str(repo), min_weight=int(floor), n_neurons=int(len(neurons)),
                  n_signed_edges=int(len(edges)), n_signed_synapses=int(edges["weight"].sum()), dataset="FlyWire v630")
    return neurons, edges, ["fw_sugar_GRN", "fw_bitter_GRN"]


def run_arm(name, repo):
    from flycns.bench import provenance
    from flycns.model import CNSModel, LIFParams, SimOptions
    spec = ALL_ARMS[name]
    st = spec["settings"]
    opt = SimOptions(reset=st["reset"], stimulation=st["stimulation"], integration=st["integration"],
                     adaptation=st["adaptation"])
    t0 = time.time()
    if spec["data"] == "flywire":
        neurons, edges, stim_types = flywire(repo, st["floor"])
        unknown_nt = None
    else:
        from flycns.graph import load_graph
        from flycns.integrity import LOADED
        neurons, edges = load_graph("data", min_weight=st["floor"], amines="excitatory")
        stim_types = ["LB3b", "LB3c"]
        unknown_nt = dict(edges=LOADED["n_dropped_unsigned_edges"], synapses=LOADED["n_dropped_unsigned_synapses"],
                          silent_presynaptic=LOADED["n_silent_presynaptic"])
    m = CNSModel(neurons, edges, stim_types, LIFParams(w_scale=st["w_scale"], seed=spec["seed"]), electrical=False,
                 options=opt)
    m.store()
    built = time.time() - t0
    stim_type = m.stim["type"].values
    rates = np.where(np.isin(stim_type, ["fw_bitter_GRN"]), float(spec["bitter_hz"]), float(spec["sugar_hz"]))
    if spec["data"] == "flywire":
        idx = dict(contra=int(m.lif_index[MN9_CONTRA]), ipsi=int(m.lif_index[MN9_IPSI]))
        sugar_lif = [m.lif_index[b] for b in m.stim["bodyId"][stim_type == "fw_sugar_GRN"] if b in m.lif_index.index]
    else:
        mn9 = m.readout_index("MN9")
        sugar_lif = [m.lif_index[b] for b in m.stim["bodyId"] if b in m.lif_index.index]
    rec_syn = [o for o in m.net.objects if type(o).__name__ == "Synapses" and o.source is m.G and o.target is m.G
               and "w" in o.variables]
    base_w = np.array(rec_syn[0].w_[:]) if spec.get("kind") == "shuffle" else None
    out = []
    runs = spec.get("shuffles") or list(range(spec["trials"]))
    for k in runs:
        m.restore()
        if base_w is not None:
            rec_syn[0].w_[:] = np.random.default_rng(10000 + k).permutation(base_w)
        m.set_stim_rates(rates)
        m.run(TRIAL_MS)
        counts = np.bincount(np.asarray(m.spikes.i[:]), minlength=len(m.lif_ids)) / (TRIAL_MS / 1000.0)
        row = dict(k=int(k), n_active=int((counts > 0).sum()), n_spikes=int(counts.sum() * TRIAL_MS / 1000.0),
                   grn_mean_hz=float(counts[sugar_lif].mean()) if len(sugar_lif) else None)
        if spec["data"] == "flywire":
            row.update(mn9_contra_hz=float(counts[idx["contra"]]), mn9_ipsi_hz=float(counts[idx["ipsi"]]))
        else:
            row.update(mn9_hz=float(counts[mn9].mean()), mn9_per_cell_hz=[float(x) for x in counts[mn9]])
        out.append(row)
        print(f"[phase1] {name} {len(out)}/{len(runs)} done ({time.time() - t0:.0f} s)", flush=True)
    rec = dict(arm=name, spec=spec, options=opt.__dict__, n_lif=int(len(m.lif_ids)), n_recurrent=int(m.n_chem),
               n_stimulated=int(len(m.stim)), unknown_transmitter=unknown_nt, build_s=round(built, 1),
               wall_s=round(time.time() - t0, 1), trials=out, registration=registry.stamp(REG),
               provenance=provenance())
    (OUT / "arms").mkdir(parents=True, exist_ok=True)
    (OUT / "arms" / f"{name}.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(f"[phase1] {name}: {len(out)} runs in {rec['wall_s']} s -> {OUT / 'arms' / (name + '.json')}")


def run_part(part, repo, parallel=2):
    arms = PARTS[part]
    procs, failed = [], []
    for a in arms:
        while len([p for p in procs if p[1].poll() is None]) >= parallel:
            time.sleep(5)
        log = open(OUT / "arms" / f"{a}.log", "w", encoding="utf-8")
        procs.append((a, subprocess.Popen([sys.executable, __file__, "arm", a, str(repo)], stdout=log,
                                          stderr=subprocess.STDOUT, cwd=ROOT)))
    for a, p in procs:
        if p.wait() != 0:
            failed.append(a)
    for a in arms:
        print(f"--- {a}\n" + "".join((OUT / "arms" / f"{a}.log").read_text(encoding="utf-8").splitlines(True)[-5:]))
    if failed:
        raise SystemExit(f"[phase1] {part}: arms failed: {failed}")


# ------------------------------------------------------------------------------------------------ scoring
def _published(repo):
    import pandas as pd
    d = pd.read_parquet(repo / PUBLISHED_100, columns=["trial", "flywire_id"])
    per = lambda n: d[d.flywire_id == n].groupby("trial").size().reindex(range(TRIALS), fill_value=0).to_numpy(float)  # noqa: E731
    ref = ROOT / "reference-data" / "shiu2024"
    for key in ("s4b", "s5b"):
        for f, want in SRC[key]["criteria"]["reference"]["files_sha256"].items():
            if sha256(ref / f) != want:
                raise SystemExit(f"[phase1] {f} differs from the {key} registration")
    names = list(json.loads((ref / "shiu_archive_manifest.json").read_text(encoding="utf-8"))["files"])
    a = pd.read_csv(ref / "shiu_archive_mn9.csv")
    a["source"] = [names[i // 30] for i in range(len(a))]
    dose = {s: a[a.source == f"results/figure_1/data/sugarR_{s}Hz.parquet"].sort_values("trial").mn9_contra.to_numpy(float)
            for s in S4_RATES}
    sb = a[(a.experiment == "sugar_bitter") & (a.sugar_hz == 100)]
    bitter = {b: sb[sb.bitter_hz == b].sort_values("trial").mn9_contra.to_numpy(float) for b in S5B_RATES}
    return dict(contra=per(MN9_CONTRA), ipsi=per(MN9_IPSI), dose=dose, bitter=bitter)


def _boot_multi(arms, stat, n_boot=stats.N_BOOT, seed=0):
    """Percentile bootstrap of stat(list of arrays), each arm resampled on its own."""
    rng = np.random.default_rng(seed)
    idx = [rng.integers(0, len(a), (n_boot, len(a))) for a in arms]
    boots = np.array([stat([a[ix[b]] for a, ix in zip(arms, idx)]) for b in range(n_boot)], dtype=float)
    boots = boots[~np.isnan(boots)]
    lo, hi = np.percentile(boots, [2.5, 97.5]) if len(boots) else (np.nan, np.nan)
    return float(stat(arms)), float(lo), float(hi)


def _load_arm(name):
    f = OUT / "arms" / f"{name}.json"
    if not f.exists():
        raise SystemExit(f"[phase1] arm {name} has no result ({f.relative_to(ROOT)})")
    rec = json.loads(f.read_text(encoding="utf-8"))
    st = rec["registration"]
    if st.get("model_hash") != REG["model"]["hash"] or not st.get("matches"):
        raise SystemExit(f"[phase1] arm {name} was not run under this registration ({st})")
    if json.loads(json.dumps(rec["spec"])) != json.loads(json.dumps(ALL_ARMS[name])):
        raise SystemExit(f"[phase1] arm {name} was run with another specification than the registered one")
    return rec


def _checks(col, pub):
    """Every scored check from per-trial arrays (col(arm, key)); n is the number of trials actually used."""
    from scipy.stats import spearmanr
    U = {}
    s100c, s100i = col("a1_sugar100", "mn9_contra_hz"), col("a1_sugar100", "mn9_ipsi_hz")
    two = lambda a: f"bootstrap, two samples ({len(a)} and 30 trials)"  # noqa: E731
    e, lo, hi = stats.bootstrap_diff(s100c, pub["contra"])
    U["S1_sugar_mn9_magnitude"] = stats.scored(e, lo, hi, -BAND_CONTRA, BAND_CONTRA, n=len(s100c), method=two(s100c),
                                               note="our contralateral MN9 mean minus the published one, Hz")
    k = int((s100c[:TRIALS] > 0).sum())
    U["S2_reliability"] = stats.point(k, k >= 29, method="count: of the arm's first 30 trials, those with a "
                                                         "contralateral MN9 spike; at least 29 required")
    e1, lo1, hi1 = stats.bootstrap(s100c - s100i)
    e2, lo2, hi2 = stats.bootstrap_diff(s100i, pub["ipsi"])
    U["S3_laterality"] = stats.combine([
        stats.scored(e1, lo1, hi1, low=0.0, strict=True, n=len(s100c), note="contralateral minus ipsilateral, paired, Hz"),
        stats.scored(e2, lo2, hi2, -BAND_IPSI, BAND_IPSI, n=len(s100i), method=two(s100i),
                     note="our ipsilateral MN9 mean minus the published one, Hz")], note="laterality, and the ipsilateral magnitude")
    dose = [col(arm_of(s, 0), "mn9_contra_hz") for s in S4_RATES]

    def ratio(xs):
        top = max(np.mean(x) for x in xs)
        return np.mean(xs[1]) / top if top > 0 else np.nan
    e, lo, hi = _boot_multi(dose, ratio)
    U["S4_calibration_reproduced"] = stats.scored(e, lo, hi, 0.7, 0.9, n=sum(len(x) for x in dose),
                                                  method="bootstrap, each of the 4 arms resampled",
                                                  note="MN9(100 Hz) / max of the MN9 means at 50-200 Hz; does not count "
                                                       "towards A1 (the reference's own output: 0.705, UNRESOLVED)")
    U["S4b_dose_curve_matches_published"] = stats.combine([
        stats.scored(*stats.bootstrap_diff(x, pub["dose"][s]), -MARGIN, MARGIN, n=len(x), method=two(x),
                     note=f"sugar {s} Hz: ours minus published, Hz")
        for s, x in zip(S4_RATES, dose)], note="the published dose curve, point by point")
    bit = [col(arm_of(100, b), "mn9_contra_hz") for b in S5_RATES]
    e1, lo1, hi1 = stats.bootstrap_diff(bit[0], bit[2])

    def neg_rho(xs):
        return -spearmanr(np.concatenate([np.full(len(x), r) for x, r in zip(xs, S5_RATES)]), np.concatenate(xs)).correlation
    e2, lo2, hi2 = _boot_multi(bit, neg_rho)
    U["S5_bitter_suppression"] = stats.combine([
        stats.scored(e1, lo1, hi1, low=0.0, strict=True, n=len(bit[0]) + len(bit[2]), method="bootstrap, two samples",
                     note="suppression: MN9(sugar 100) - MN9(sugar 100 + bitter 100), Hz"),
        stats.scored(e2, lo2, hi2, low=0.0, strict=True, n=sum(len(x) for x in bit),
                     method="bootstrap, each of the 5 arms resampled",
                     note="minus the Spearman rho of per-trial MN9 against bitter rate (0-200 Hz)")],
        note="registered: both intervals below 0, scored here on their negatives (above 0)")
    U["S5b_bitter_curve_matches_published"] = stats.combine([
        stats.scored(*stats.bootstrap_diff(x, pub["bitter"][b]), -MARGIN, MARGIN, n=len(x), method=two(x),
                     note=f"bitter {b} Hz: ours minus published, Hz")
        for b, x in ((b, col(arm_of(100, b), "mn9_contra_hz")) for b in S5B_RATES)],
        note="the published bitter curve, point by point")
    shuf = np.concatenate([col(f"a1_shuffle{k}", "mn9_contra_hz") for k in range(4)])
    n_act = int((shuf >= T_SHUFFLE).sum())
    U["S6_wiring_control"] = stats.point(n_act, n_act <= 5 and len(shuf) == 100,
                                         method=f"count: shuffles reaching {T_SHUFFLE} Hz, of {len(shuf)}; at most 5 allowed")
    m1 = col("m1_male", "mn9_hz")
    e, lo, hi = stats.bootstrap(m1)
    U["M1_male_mn9"] = stats.scored(e, lo, hi, low=0.5, strict=True, n=len(m1),
                                    note="MaleCNS MN9 rate (mean of its cells), Hz; PASS = responds")
    return U


def _reference_s6():
    """The reference's own 100 shuffles, if they were run (only when A1's S6 fails)."""
    if not REF_S6.exists():
        return None
    r = json.loads(REF_S6.read_text(encoding="utf-8"))
    x = np.asarray(r["mn9_contra_hz"], dtype=float)
    k = int((x >= T_SHUFFLE).sum())
    return stats.point(k, k <= 5 and len(x) == 100, method=f"the reference's own code: shuffles reaching {T_SHUFFLE} Hz, "
                                                           f"of {len(x)}; at most 5 allowed")


def _a1(v, ref_s6):
    """The registered A1 definition: counted checks (reference-calibrated), three outcomes."""
    s6_fail = v["S6_wiring_control"] == "FAIL"
    counted = [k for k in COUNTED if not (k == "S6_wiring_control" and ref_s6 is not None and ref_s6["verdict"] == "FAIL")]
    others = [k for k in counted if k != "S6_wiring_control"]
    if any(v[k] == "FAIL" for k in others):
        return "FAILS", counted, False
    if s6_fail and ref_s6 is None:
        return "PENDING", counted, True           # the reference's own shuffles decide whether S6 counts
    if any(v[k] == "FAIL" for k in counted):
        return "FAILS", counted, False
    return ("PASSES" if all(v[k] == "PASS" for k in counted) else "UNRESOLVED"), counted, False


def score(repo):
    from flycns.bench import provenance
    base = {a: _load_arm(a) for a in ARMS}
    ext_file = OUT / "extension.json"
    present_ext = sorted(f.stem for f in (OUT / "arms").glob("*_ext.json"))
    plan = json.loads(ext_file.read_text(encoding="utf-8")) if ext_file.exists() else None
    needed = plan["arms"] if plan else []
    if sorted(f"{a}_ext" for a in needed) != present_ext:
        if not plan:
            raise SystemExit(f"[phase1] extension arms {present_ext} exist but no extension was called for")
        missing = sorted(set(f"{a}_ext" for a in needed) - set(present_ext))
        extra = sorted(set(present_ext) - set(f"{a}_ext" for a in needed))
        raise SystemExit(f"[phase1] the registered extension needs {missing or 'nothing more'}; not called for: {extra or 'none'}")
    ext = {a: _load_arm(f"{a}_ext") for a in needed}

    def col(a, k):
        rows = base[a]["trials"] + (ext[a]["trials"] if a in ext else [])
        return np.array([t[k] for t in rows], dtype=float)
    pub = _published(repo)
    U = _checks(col, pub)
    registry.verify_bands(REG, U)
    v = {k: r["verdict"] for k, r in U.items()}
    ref_s6 = _reference_s6()
    a1, counted, need_ref_s6 = _a1(v, ref_s6)
    m1v = v["M1_male_mn9"]
    stage = "extended" if plan else "first"
    status = "final"
    if stage == "first":
        unresolved = [k for k in counted if v[k] == "UNRESOLVED"] if a1 in ("UNRESOLVED", "PENDING") else []
        if a1 in ("PASSES", "UNRESOLVED", "PENDING") and m1v == "UNRESOLVED":
            unresolved.append("M1_male_mn9")
        arms_needed = set()
        for k in unresolved:
            parts = U[k].get("parts")
            if parts and k in PART_FEEDS:
                arms_needed |= {a for p_, feed in zip(parts, PART_FEEDS[k]) if p_["verdict"] == "UNRESOLVED" for a in feed}
            else:
                arms_needed |= set(FEEDS[k])
        arms_needed = sorted(arms_needed)
        if arms_needed:
            ext_file.write_text(json.dumps(dict(arms=arms_needed, because=unresolved, first_pass=U,
                                                provenance=provenance()), indent=2, default=float), encoding="utf-8")
            status = "extension needed (commit extension.json, then run the p1-ext-* jobs)"
        if need_ref_s6:
            status = ("reference shuffles needed (push reference/<label>--s6)" if not arms_needed else
                      status + "; and the reference shuffles (push reference/<label>--s6)")
    elif need_ref_s6:
        status = "reference shuffles needed (push reference/<label>--s6)"
    if status != "final":
        outcome = f"not decided yet: {status}"
    elif a1 == "FAILS":
        outcome = "A1 fails: flycns differs from Shiu's model beyond the listed settings; bisect first"
    elif a1 == "UNRESOLVED":
        outcome = "A1 is UNRESOLVED after its one extension: the decision rule does not decide; stop for review"
    elif m1v == "PASS":
        outcome = "A1 passes and M1 responds: the male MN9 zero is caused by flycns settings (the ladder names which)"
    elif m1v == "FAIL":
        outcome = ("A1 passes and M1 does not respond: the male zero is wiring or annotation, not the simulator "
                   "(addendum: unless L3 loses MN9, in which case a floor-1 MaleCNS fetch comes first)")
    else:
        outcome = "A1 passes; M1 is UNRESOLVED after its one extension: the rule does not decide; stop for review"
    s100c = col("a1_sugar100", "mn9_contra_hz")
    ladder = {}
    for name in LADDER:
        x = col(name, "mn9_contra_hz")
        e, lo, hi = stats.bootstrap(x)
        d, dlo, dhi = stats.bootstrap_diff(x, s100c)
        ladder[name] = dict(switched=LADDER[name], mn9_contra_hz=[e, lo, hi], minus_a1=[d, dlo, dhi],
                            fired_trials=int((x > 0).sum()), trials=len(x))
    reported = dict(
        a1_sugar100=dict(mn9_contra_hz=float(s100c.mean()), mn9_ipsi_hz=float(col("a1_sugar100", "mn9_ipsi_hz").mean()),
                         published_contra_hz=float(pub["contra"].mean()), published_ipsi_hz=float(pub["ipsi"].mean()),
                         grn_mean_hz=float(np.mean(col("a1_sugar100", "grn_mean_hz"))),
                         neurons_active=float(np.mean(col("a1_sugar100", "n_active")))),
        dose={s: [float(col(arm_of(s, 0), "mn9_contra_hz").mean()), float(pub["dose"][s].mean())] for s in S4_RATES},
        bitter={b: [float(col(arm_of(100, b), "mn9_contra_hz").mean()),
                    float(pub["bitter"][b].mean()) if b in pub["bitter"] else None]
                for b in sorted(set(S5_RATES) | set(S5B_RATES))},
        shuffles_mn9_contra_hz=col("a1_shuffle0", "mn9_contra_hz").tolist() + col("a1_shuffle1", "mn9_contra_hz").tolist()
        + col("a1_shuffle2", "mn9_contra_hz").tolist() + col("a1_shuffle3", "mn9_contra_hz").tolist(),
        reference_s6=ref_s6, m1_mn9_hz=col("m1_male", "mn9_hz").tolist(),
        m1_unknown_transmitter=base["m1_male"]["unknown_transmitter"], ladder=ladder,
        wall_s={a: r["wall_s"] for a, r in {**base, **{f"{a}_ext": r for a, r in ext.items()}}.items()})
    report = dict(benchmark=LABEL, criteria=CRITERIA, stage=stage, status=status, uncertainty=U,
                  checks={k: x == "PASS" for k, x in v.items()}, a1=a1, a1_counted=counted, m1=m1v, outcome=outcome,
                  extension=plan and dict(arms=plan["arms"], because=plan["because"]), reported=reported,
                  registration=registry.stamp(REG), provenance=provenance())
    (OUT / "phase1.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    for k, x in v.items():
        print(f"  {x:<10} {k}" + ("" if k in counted or k == "M1_male_mn9" else "   (reported; does not count towards A1)"))
    print(f"A1 {a1}; M1 {m1v} ({stage} scoring)\n{outcome}")
    for name, r in ladder.items():
        print(f"  {name:<16} MN9 {r['mn9_contra_hz'][0]:6.2f} Hz ({r['mn9_contra_hz'][1]:.2f}-{r['mn9_contra_hz'][2]:.2f}); "
              f"minus A1 {r['minus_a1'][0]:+.2f}")


def run_extension(k, n, repo):
    plan = OUT / "extension.json"
    if not plan.exists():
        raise SystemExit("[phase1] no extension was called for (results/shiu2024_phase1/extension.json is absent)")
    mine = json.loads(plan.read_text(encoding="utf-8"))["arms"][k::n]
    if not mine:
        print(f"[phase1] extension share {k} of {n}: nothing to run")
        return
    PARTS[f"p1-ext-{k}"] = [f"{a}_ext" for a in mine]
    run_part(f"p1-ext-{k}", repo)


REG = registry.register(LABEL, CRITERIA, scripts=[__file__])     # exits here under FLYCNS_REGISTER_ONLY
require_clean(LABEL)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "parts":
        for p, arms in PARTS.items():
            print(f"{p:<14} {', '.join(arms)}")
    elif mode in ("part", "arm", "score", "extension"):
        refuse_overrides(f"phase 1 {mode}")
        repo_arg = {"part": 3, "arm": 3, "score": 2, "extension": 4}[mode]
        repo = shiu_repo(sys.argv[repo_arg] if len(sys.argv) > repo_arg else None)
        (OUT / "arms").mkdir(parents=True, exist_ok=True)
        if mode == "part":
            run_part(sys.argv[2], repo)
        elif mode == "arm":
            run_arm(sys.argv[2], repo)
        elif mode == "extension":
            run_extension(int(sys.argv[2]), int(sys.argv[3]), repo)
        else:
            score(repo)
    else:
        raise SystemExit(__doc__)
