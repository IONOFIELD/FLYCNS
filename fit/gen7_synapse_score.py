"""
Score generation 7 (fit/gen7_synapse.py) exactly as docs/gen7_synapse_model_DRAFT.md, D1-D8, defines it.

    python fit/gen7_synapse_score.py            score the registered arms (results/gen7_synapse/arms/) -> gen7.json
    python fit/gen7_synapse_score.py --smoke    score whatever smoke arms exist (results/gen7_synapse/smoke/); never
                                                a result, written to smoke/gen7.json

This file is hashed into generation 7's registration (fit/gen7_synapse.py registers it), so a threshold changed here is
a changed registration. Every component verdict is PASS, FAIL or UNRESOLVED; UNRESOLVED is never read as PASS.

D3   Outcome, in order: R (P0 does not replicate phase A's cell 1) -> F (B viable) -> the first viable of S-in, C,
     CS-in -> C7. Viable(set): a grid w at which FUNCTION (screen), FUNCTION-q, STABILITY (a), (b), (c) and, in a
     conductance arm, NUMERICS all PASS; the decision w is the smallest such w. LATERALITY is reported only.
     A candidate w (no FAIL, at least one UNRESOLVED) in a decision set (B, S-in, C, CS-in) names ONE top-up of BOTH
     drives, where it could change that set's viability or decision w (name_topups); the trials are pooled; after
     it UNRESOLVED counts as not passing. While a top-up that can change the outcome is missing, or the candidate's
     dt 0.05 ms repeat (with as many trials as its verdict rests on) is missing or differs, the outcome is not final.
D4   Hypothesis verdicts: held, not held, undetermined.
D6   Numerics guard, the dt repeat of the candidate, the ORN-under-sugar check, cell counts.
D7   V7a (report-only), the AL/LH share of the blind tail, by-mode summaries.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns import registry, stats  # noqa: E402

# Imported (the unit tests, the arms script's selftest) or run with --smoke: the design only, no registration is read
# or written. Run as a script without --smoke: importing the arms script under its own name registers and checks.
SMOKE = "--smoke" in sys.argv[1:] or __name__ != "__main__"
_spec = importlib.util.spec_from_file_location("gen7_synapse_design" if SMOKE else "gen7_synapse",
                                               ROOT / "fit" / "gen7_synapse.py")
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

T = G.CRITERIA["inherits"]["thresholds"]      # every bar is phase A's, from the registered criteria (one place, hashed)
RESPONDS, RATE_BAR, FRAC_BAR, LI_BAR = T["responds_hz"], T["rate_bar_hz"], T["fraction_bar"], T["li_bar"]
FQ_MIN, FQ_NEED = T["function_q_min_trials"], T["function_q_need"]
VNC_STEMS = ("LegNp", "Ov", "mVAC", "WTct", "HTct", "NTct", "IntTct", "LTct", "ANm")
AL_LH = ("AL(L)", "AL(R)", "LH(L)", "LH(R)")
NEW_KEYS = ("orn_spikes", "lowest_v_mV")      # the two per-trial fields generation 7 adds to phase A's


def load(D, name, required=True, smoke=SMOKE):
    f = Path(D) / f"{name}.json"
    if not f.exists():
        if required and not smoke:
            raise SystemExit(f"[score] arm {name} has no result ({f})")
        return None
    rec = json.loads(f.read_text(encoding="utf-8"))
    if not smoke:
        st = rec.get("registration") or {}
        if st.get("model_hash") != G.REG["model"]["hash"] or not st.get("matches"):
            raise SystemExit(f"[score] arm {name} was not run under this registration ({st})")
        if rec.get("reduced"):
            raise SystemExit(f"[score] arm {name} is a smoke run, not a result")
        if json.loads(json.dumps(rec["spec"])) != json.loads(json.dumps(G.ARMS[name])):
            raise SystemExit(f"[score] arm {name} was run with another specification than the registered one")
        if len(rec["trials"]) != (G.ARMS[name]["trials"] if G.ARMS[name]["kind"] == "sweep" else
                                  len(G.V7A) * len(G.V7A_RATES) * G.V7A_TRIALS):
            raise SystemExit(f"[score] arm {name} has {len(rec['trials'])} runs, not the registered number")
    return rec


def col(trials, key):
    return np.array([t[key] for t in trials], dtype=float)


# ---------------------------------------------------------------------------------- components (phase A's, unchanged)
def below(values, bar, note):
    """Interval wholly below bar: PASS iff hi < bar; FAIL iff lo >= bar; else UNRESOLVED."""
    e, lo, hi = stats.bootstrap(values)
    vd = "UNRESOLVED" if np.isnan(lo) else ("PASS" if hi < bar else ("FAIL" if lo >= bar else "UNRESOLVED"))
    return dict(estimate=e, ci95=[lo, hi], bar=bar, rule="95% interval wholly below the bar", verdict=vd, note=note)


def function_screen(su):
    e, lo, hi = stats.bootstrap(col(su, "mn9_hz"))
    return stats.scored(e, lo, hi, low=RESPONDS, strict=True, n=len(su),
                        note=f"sugar: MN9 two-cell mean, Hz; interval wholly above {RESPONDS} (lower edge exclusive)")


def function_q(su):
    quiet = [t for t in su if not t["self_sustained"]]
    k = int(sum(t["mn9_hz"] > RESPONDS for t in quiet))
    n = len(quiet)
    lo, hi = stats.wilson(k, n)
    if n < FQ_MIN:
        vd, why = "UNRESOLVED", f"{n} non-self-sustained trials, fewer than {FQ_MIN}"
    else:
        vd, why = ("PASS" if k / n >= FQ_NEED else "FAIL"), None
    rec = dict(estimate=(k / n) if n else None, wilson95=[lo, hi], k=k, n=n, verdict=vd,
               rule=f"fraction of non-self-sustained sugar trials with MN9 > {RESPONDS} Hz; PASS iff >= {FQ_NEED} with "
                    f"n >= {FQ_MIN}; the verdict uses the point fraction")
    if why:
        rec["note"] = why
    return rec


def count_zero(trials, label):
    n = int(sum(t["self_sustained"] for t in trials))
    return dict(estimate=n, of=len(trials), verdict="UNRESOLVED" if not trials else ("PASS" if n == 0 else "FAIL"),
                rule=f"{label}: 0 self-sustained trials (no trials: UNRESOLVED)")


def stability_c(bl):
    r = below(col(bl, "cns_rate_hz"), RATE_BAR, "blind: whole-CNS rate, Hz")
    f = below(col(bl, "fraction_active"), FRAC_BAR, "blind: fraction active")
    return stats.combine([r, f], note="STABILITY (c): both intervals wholly below 1 Hz and 10%")


def numerics(trials, e_inh):
    """D6: conductance arms. FAIL iff any cell's v went below E_i - margin in any trial."""
    lows = [t.get("lowest_v_mV") for t in trials]
    if any(x is None for x in lows):
        raise SystemExit("[score] a conductance arm has a trial without lowest_v_mV; scoring refused")
    x = np.array(lows, dtype=float)
    bar = e_inh - G.NUMERICS_MARGIN_MV
    rule = (f"NUMERICS: lowest_v_mV is not below E_i - {G.NUMERICS_MARGIN_MV} mV in any trial; a value that is not a "
            "number, or no trial, is FAIL")
    if not len(x) or np.isnan(x).any():
        return dict(estimate=None, bar=bar, verdict="FAIL", rule=rule, note="a trial's lowest_v_mV is not a number, or "
                                                                             "there is no trial: fails safe")
    lo = float(x.min())
    return dict(estimate=lo, bar=bar, verdict="FAIL" if lo < bar else "PASS", rule=rule)


def li_summary(trials, min_spikes=0):
    v = [t["mn9_li"] for t in trials if t.get("mn9_li") is not None and t.get("mn9_spikes", 0) >= min_spikes]
    return dict(median=float(np.median(v)) if v else None, n_defined=len(v), n_trials=len(trials))


def laterality(su):
    s = li_summary(su)
    vd = "UNRESOLVED" if s["median"] is None else ("PASS" if s["median"] < LI_BAR else "FAIL")
    return dict(**s, bar=LI_BAR, verdict=vd, rule="median sugar LI over trials where defined, below 0.8; reported, gates "
                                                  "nothing in generation 7", sensitivity_min5_spikes=li_summary(su, 5))


def modes(n_active):
    x = sorted(int(v) for v in n_active)
    if len(x) < 2 or x[-1] <= T["bimodal_factor"] * max(1, x[0]):
        return dict(bimodal=False, median=float(np.median(x)) if x else None)
    cut = int(np.argmax(np.diff(x))) + 1
    lo, hi = x[:cut], x[cut:]
    return dict(bimodal=True, low_mode=dict(n=len(lo), median=float(np.median(lo))),
                high_mode=dict(n=len(hi), median=float(np.median(hi))))


def group_v2(label):
    return "VNC" if (str(label).split("(")[0] in VNC_STEMS or label == "VNC-unspecified") else str(label)


def tail_groups(trials, sizes):
    ss = [t for t in trials if t["self_sustained"] and "tail_by_neuropil" in t]
    if not ss or not sizes:
        return None
    gs, tot = {}, {}
    for k, n in sizes.get("neuropil", {}).items():
        gs[group_v2(k)] = gs.get(group_v2(k), 0) + n
    for t in ss:
        for k, v in t["tail_by_neuropil"].items():
            tot[group_v2(k)] = tot.get(group_v2(k), 0) + v[0]
    S = sum(tot.values())
    sec = (G.PA.TAIL_MS // 2) / 1000.0
    return dict(n_self_sustained=len(ss), total_tail_spikes=int(S),
                top={g: dict(share=(v / S) if S else None, rate_hz=(v / gs[g] / sec / len(ss)) if gs.get(g) else None)
                     for g, v in sorted(tot.items(), key=lambda kv: -kv[1])[:8]})


def al_share(trials):
    """Phase A's M9 measure: among self-sustained trials, the AL and LH share of the tail and of the drive spikes."""
    ss = [t for t in trials if t["self_sustained"] and "tail_by_neuropil" in t]
    if not ss:
        return dict(scorable=False)
    tt = sum(sum(v[0] for v in t["tail_by_neuropil"].values()) for t in ss)
    ta = sum(sum(v[0] for k, v in t["tail_by_neuropil"].items() if k in AL_LH) for t in ss)
    dt = sum(sum(v[0] for v in t["drive_by_neuropil"].values()) for t in ss)
    da = sum(sum(v[0] for k, v in t["drive_by_neuropil"].items() if k in AL_LH) for t in ss)
    return dict(scorable=True, n=len(ss), tail_share=(ta / tt if tt else None), drive_share=(da / dt if dt else None))


def arm_summary(rec, trials):
    return dict(trials=len(trials), self_sustained=int(sum(t["self_sustained"] for t in trials)),
                cns_rate_hz=list(stats.bootstrap(col(trials, "cns_rate_hz"))),
                fraction_active=list(stats.bootstrap(col(trials, "fraction_active"))),
                n_active_modes=modes([t["n_active"] for t in trials]),
                tail_groups=tail_groups(trials, rec.get("group_sizes")),
                orn_spikes_mean=float(np.mean([t.get("orn_spikes", 0) for t in trials])) if trials else None,
                n_lif=rec.get("n_lif"), n_std_syn=rec.get("n_std_syn"))


# ---------------------------------------------------------------------------------- viability
def copied(a, b):
    """True if two arms' trial rows are identical although the arm is not silent. Arms with different seeds or
    time steps cannot give identical rows unless nothing spikes; this is flagged, not refused (D10, F13)."""
    same = json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)
    return bool(same and any(t.get("n_spikes", 0) for t in a))


def components(s, S, B):
    comp = dict(function=function_screen(S), function_q=function_q(S), stability_a=count_zero(S, "sugar"),
                stability_b=count_zero(B, "blind"), stability_c=stability_c(B))
    if G.SETS[s]["synapse"] == "conductance":
        comp["numerics"] = numerics(S + B, G.settings_of(s)["e_inh_mV"])
    return comp


def set_at(D, s, w, pool, smoke=SMOKE):
    """Every component for one arm set at one w; pool: add the top-up trials of both drives (D1, D3)."""
    name = lambda d: f"{s}_{d}_{G._w(w)}"         # noqa: E731
    su, bl = load(D, name("sugar"), smoke=smoke), load(D, name("blind"), smoke=smoke)
    if su is None or bl is None:
        return None
    S, B, used, dup = list(su["trials"]), list(bl["trials"]), [], []
    if pool:
        ts, tb = (load(D, name(d) + "_topup", required=False, smoke=smoke) for d in ("sugar", "blind"))
        if (ts is None) != (tb is None):
            raise SystemExit(f"[score] {s} at w {w}: the top-up of only one drive exists; a top-up counts only if "
                             "both drives were run (D1). Scoring refused")
        if ts is not None:
            # (a top-up's rows are not compared with the main arm's: two silent arms have identical rows by right.
            #  That a top-up is a new run is checked in load(): its specification, with its own seed, must be the
            #  registered one.)
            S, B, used = S + list(ts["trials"]), B + list(tb["trials"]), [name("sugar") + "_topup", name("blind") + "_topup"]
            dup = [name(d) + "_topup" for d, t, m in (("sugar", ts, su), ("blind", tb, bl)) if copied(t["trials"], m["trials"])]
    comp = components(s, S, B)
    vs = [c["verdict"] for c in comp.values()]
    status = "viable" if all(v == "PASS" for v in vs) else ("fails" if "FAIL" in vs else "candidate")
    if status == "candidate" and used:
        status = "not passing (UNRESOLVED after its top-up)"
    need = [name("sugar"), name("blind")] if status == "candidate" and s in G.DECISION else []
    per = S[0].get("mn9_per_cell_hz") if S else None
    return dict(w_scale=w, status=status, components=comp, topups_used=used, identical_rows=dup, laterality=laterality(S),
                mn9_per_cell_mean_hz=[float(np.mean([t["mn9_per_cell_hz"][i] for t in S])) for i in range(len(per))] if per else None,
                mn9_cells=S[0].get("mn9_cells") if S else None, sugar=arm_summary(su, S), blind=arm_summary(bl, B),
                blind_al_lh_share=al_share(B)), need


def name_topups(first):
    """D3: which candidate w get a top-up, from the main arms alone. first: (set, w) -> (row, both arm names).
    In a decision set, a candidate w is named only below that set's smallest viable w: above it, the top-up could
    change neither whether the set is viable nor its decision w. Going through the outcome order (B, S-in, C,
    CS-in): up to and including the first set that is already viable, a named top-up can change the outcome
    ('blocking': the outcome is PROVISIONAL until it is run). After that set, the outcome cannot change; a later
    set is named only if it has no viable w, because its hypothesis verdict still rests on the top-up ('for the
    hypothesis')."""
    blocking, extra, decided = [], [], False
    for s in G.DECISION:
        rows = [first[(s, w)] for w in G.GRID_W if (s, w) in first]
        viable = [r["w_scale"] for r, _ in rows if r["status"] == "viable"]
        below = [need for r, need in rows if r["status"] == "candidate" and (not viable or r["w_scale"] < min(viable))]
        if not decided:
            blocking += [a for need in below for a in need]
        elif not viable:
            extra += [a for need in below for a in need]
        decided = decided or bool(viable)
    return blocking, extra


def state(grid):
    """D4: viable | not viable | undetermined, for one arm set's rows."""
    if any(r["status"] == "viable" for r in grid):
        return "viable"
    if not grid or any(r["status"] == "candidate" for r in grid):
        return "undetermined"
    return "not viable"


def p0_replication(sets, D_phaseA=None):
    """D3.1: P0's table against EXPECT_C1; and (reported) its trial rows against phase A's cell-1 arm files."""
    grid = {G._w(r["w_scale"]): r for r in sets.get("p0", {}).get("grid", [])}
    got = {k: dict({c: r["components"][c]["verdict"] for c in G.COMPONENTS},
                   self_sustained=[r["sugar"]["self_sustained"], r["blind"]["self_sustained"]]) for k, r in grid.items()}
    diff = {k: dict(expected=v, got=got.get(k)) for k, v in G.EXPECT_C1.items() if got.get(k) != v}
    return dict(replicates=not diff, differences=diff, table=got)


def p0_rows(D, smoke=SMOKE):
    """Reported: are P0's trial rows identical to phase A's cell-1 arms (same seeds, default code path)?"""
    ref = ROOT / "results" / "gen6_phaseA" / "arms"
    out = {}
    for d in G.DRIVES:
        for w in G.GRID_W:
            a, f = load(D, f"p0_{d}_{G._w(w)}", required=False, smoke=smoke), ref / f"c1_{d}_{G._w(w)}.json"
            if a is None or not f.exists():
                continue
            old = json.loads(f.read_text(encoding="utf-8"))["trials"]
            new = [{k: v for k, v in t.items() if k not in NEW_KEYS} for t in a["trials"]]
            out[f"{d}_{G._w(w)}"] = bool(json.loads(json.dumps(new, default=float)) == old)
    return dict(compared=len(out), identical=sum(out.values()), per_arm=out,
                note="reported, not a criterion: identical rows are expected on the same platform and packages")


def decide(states, w_of, replicated, missing_topups):
    """D3. states: arm set -> viable | not viable | undetermined; w_of: arm set -> smallest viable w."""
    if not replicated:
        return dict(code="R", candidate=None, w=None, final=False,
                    why="P0 does not replicate phase A's cell 1: stop for review; nothing is adopted")
    if states["b"] == "viable":
        code, cand, why = "F", "b", "the fix alone (B) is viable"
    else:
        cand = next((s for s in G.ORDER if states[s] == "viable"), None)
        code = cand if cand else "C7"
        why = (f"{cand} is the first viable arm set in the order S-in, C, CS-in" if cand else
               "no decision arm set is viable; generation 8 takes the antennal-lobe mechanisms")
    w = w_of.get(cand) if cand else None
    final = not missing_topups
    if cand:
        why += f"; the candidate is {cand} at w {w}. " + G.CRITERIA["decision"]["provisional"].capitalize()
    if missing_topups:
        why += f" (PROVISIONAL: top-ups that can change the outcome are not yet run: {missing_topups})"
    return dict(code=code, candidate=cand, w=w, final=final, why=why)


def finalize(outcome, dt, states):
    """D6: a candidate is final only after its dt 0.05 ms repeat has run and agrees. Until then, and if the repeat
    differs (numerics-sensitive), the outcome is not final and the candidate's arm set is 'undetermined' for the
    hypothesis verdicts. Returns (outcome, states)."""
    if outcome.get("candidate") is None:
        return outcome, states
    s = outcome["candidate"]
    if not dt.get("done"):
        return (dict(outcome, final=False, why=outcome["why"] + f" (PROVISIONAL: the dt 0.05 ms repeat is not yet run: "
                                                                 f"{dt.get('parts_to_run')})"),
                dict(states, **{s: "undetermined"}))
    if dt.get("numerics_sensitive"):
        return (dict(outcome, final=False, numerics_sensitive=True,
                     why=outcome["why"] + f" (NOT FINAL: the candidate is numerics-sensitive; components "
                                          f"{dt['differs']} differ at dt 0.05 ms. Stop for review)"),
                dict(states, **{s: "undetermined"}))
    return outcome, states


def hypotheses(states, outcome, replicated):
    """D4. Each: held | not held | undetermined, beside the registered prediction."""
    V, N = "viable", "not viable"

    def simple(s):
        return {V: "held", N: "not held"}.get(states.get(s, "undetermined"), "undetermined")

    def any_of(ss):
        st = [states.get(s, "undetermined") for s in ss]
        return "held" if V in st else ("not held" if all(x == N for x in st) else "undetermined")
    c, ti, sin, csin = (states.get(k, "undetermined") for k in ("c", "cti10", "sin", "csin"))
    h7b = ("held" if ti == V and c == N else "not held" if ti == N or c == V else "undetermined")
    h7d = ("held" if csin == V and c == N and sin == N else
           "not held" if csin == N or c == V or sin == V else "undetermined")
    got = {"H7-P": "held" if replicated else "not held", "H7-F": simple("b"), "H7a": simple("c"), "H7b": h7b,
           "H7c-in": simple("sin"), "H7d": h7d, "H7c-al": any_of(("sal", "csal")), "H7c-all": any_of(("sall", "csall")),
           "overall": ("undetermined" if not outcome["final"] else "held" if outcome["code"] == "C7" else "not held")}
    if not replicated:
        got = {k: (v if k == "H7-P" else "undetermined") for k, v in got.items()}
    about = {"H7-P": ["p0"], "H7-F": ["b"], "H7a": ["c"], "H7b": ["cti10", "c"], "H7c-in": ["sin"],
             "H7d": ["csin", "c", "sin"], "H7c-al": ["sal", "csal"], "H7c-all": ["sall", "csall"], "overall": list(G.DECISION)}
    return {k: dict(text=G.CRITERIA["hypotheses"][k][0], predicted=G.CRITERIA["hypotheses"][k][1],
                    confidence=G.CRITERIA["hypotheses"][k][2], verdict=v, arm_sets=about[k],
                    arm_set_states={a: states.get(a, "undetermined") for a in about[k]},
                    prediction_correct=None if v == "undetermined" else bool(v == G.CRITERIA["hypotheses"][k][1]))
            for k, v in got.items()}


# ---------------------------------------------------------------------------------- D6, D7
def orn_check(D, smoke=SMOKE):
    """D6: where S-in's (CS-in's) sugar arm has no ORN spike, its trials must equal B's (C's), field by field."""
    out = {}
    for s, ref in (("sin", "b"), ("csin", "c")):
        for w in G.GRID_W:
            a = load(D, f"{s}_sugar_{G._w(w)}", required=False, smoke=smoke)
            b = load(D, f"{ref}_sugar_{G._w(w)}", required=False, smoke=smoke)
            if a is None or b is None:
                continue
            if any("orn_spikes" not in t for t in a["trials"]):
                raise SystemExit(f"[score] {s}_sugar_{G._w(w)}: a trial has no orn_spikes; scoring refused")
            n = int(sum(t["orn_spikes"] for t in a["trials"]))
            rec = dict(orn_spikes_total=n, orn_spikes_mean=n / len(a["trials"]), compared_with=ref)
            if n == 0:
                same = json.dumps(a["trials"], sort_keys=True, default=float) == json.dumps(b["trials"], sort_keys=True, default=float)
                rec["equals_reference"] = bool(same)
                if not same:
                    pairs = list(zip(a["trials"], b["trials"]))
                    rec["differing_fields"] = sorted({k for x, y in pairs for k in set(x) | set(y) if x.get(k) != y.get(k)})
                    rec["trials_differing"] = int(sum(x != y for x, y in pairs)) + abs(len(a["trials"]) - len(b["trials"]))
            out[f"{s}_{G._w(w)}"] = rec
    flags = sorted(k for k, v in out.items() if v.get("equals_reference") is False)
    return dict(per_arm=out, unexpected_differences=flags,
                rule="no ORN spike under sugar means no depressing synapse delivers: the arm must equal its reference")


def v7a(D, smoke=SMOKE):
    """D7, report-only. Every compared glomerulus counts; one whose record is incomplete is 'missing' (a registered
    arm with an incomplete record refuses scoring), never dropped from the count."""
    arms, low = {}, []
    n_compared = sum(1 for v in G.V7A.values() if v["compared"])
    for s in G.V7A_SETS:
        for w in G.GRID_W:
            name = f"v7a_{s}_{G._w(w)}"
            rec = load(D, name, smoke=smoke)
            if rec is None:
                continue
            per, missing = {}, []
            for g, ref in G.V7A.items():
                y = [[t["pn_hz"] for t in rec["trials"] if t["glomerulus"] == g and t["orn_hz"] == r] for r in G.V7A_RATES]
                if not smoke and any(len(v) != G.V7A_TRIALS for v in y):
                    raise SystemExit(f"[score] {name}: glomerulus {g} has {[len(v) for v in y]} runs per rate, not "
                                     f"{G.V7A_TRIALS}; scoring refused")
                if not all(y):
                    missing.append(g)
                    continue
                mean = [float(np.mean(v)) for v in y]
                fit = G.hill_fit(G.V7A_RATES, mean)
                per[g] = dict(orn_hz=G.V7A_RATES, pn_hz=mean,
                              olsen_fit_hz=[float(x) for x in G.hill(G.V7A_RATES, ref["r_max"], ref["sigma"])],
                              fit=fit, rms_residual_hz=float(np.sqrt(fit["sse"] / len(G.V7A_RATES))),
                              monotone=bool(all(b >= a for a, b in zip(mean, mean[1:]))),
                              olsen=dict(r_max=ref["r_max"], sigma=ref["sigma"]), compared=ref["compared"],
                              consistent=G.v7a_consistent(fit, g), cells=rec.get("v7a_cells", {}).get(g))
            rec_low = None
            if G.SETS[s]["synapse"] == "conductance":
                lows = [t.get("lowest_v_mV") for t in rec["trials"]]
                rec_low = (None if not lows or any(x is None or x != x for x in lows) else float(min(lows)))
                if rec_low is None or rec_low < G.settings_of(s)["e_inh_mV"] - G.NUMERICS_MARGIN_MV:
                    low.append(name)
            arms[name] = dict(set=s, w_scale=w, glomeruli=per, missing=missing, compared=n_compared,
                              consistent=int(sum(v["consistent"] for v in per.values() if v["compared"])),
                              lowest_v_mV=rec_low)
    return dict(status=G.CRITERIA["validation"]["v7a"]["status"], arms=arms, numerics_low=sorted(low),
                consistent_by_arm={k: f"{v['consistent']} of {v['compared']}" + (f" ({len(v['missing'])} missing)" if v["missing"] else "")
                                   for k, v in arms.items()})


def dt_check(D, outcome, sets, smoke=SMOKE):
    """D6: the candidate at its decision w, repeated at dt 0.05 ms with as many trials as its verdict rests on: the
    two main arms, and the two top-up arms too when the decision w was reached with a top-up. The repeat's
    component verdicts are compared with the candidate's (all PASS)."""
    s, w = outcome["candidate"], outcome["w"]
    if s is None:
        return dict(needed=False)
    row = next(r for r in sets[s]["grid"] if r["w_scale"] == w)
    pooled = bool(row["topups_used"])
    base = {d: f"{s}_{d}_{G._w(w)}" for d in G.DRIVES}
    want = {f"g7-dt-{s}-{G._w(w)}": [base[d] + "_dt005" for d in G.DRIVES]}
    if pooled:
        want[f"g7-dtt-{s}-{G._w(w)}"] = [base[d] + "_dt005_topup" for d in G.DRIVES]
    got = {a: load(D, a, required=False, smoke=smoke) for arms in want.values() for a in arms}
    todo = sorted(p for p, arms in want.items() if any(got[a] is None for a in arms))
    if todo:
        return dict(needed=True, done=False, pooled=pooled, parts=sorted(want), parts_to_run=todo,
                    note=f"run {', '.join(todo)}; until then the candidate is unchecked at dt 0.05 ms")
    trials = {d: [t for a in arms_of for t in got[a]["trials"]]
              for d, arms_of in ((d, [base[d] + "_dt005"] + ([base[d] + "_dt005_topup"] if pooled else [])) for d in G.DRIVES)}
    c = components(s, trials["sugar"], trials["blind"])
    a = {k: v["verdict"] for k, v in row["components"].items()}
    b = {k: v["verdict"] for k, v in c.items()}
    dup = []
    for name, rec in got.items():
        main = load(D, name.replace("_dt005", ""), required=False, smoke=smoke)
        if main is not None and copied(rec["trials"], main["trials"]):
            dup.append(name)
    return dict(needed=True, done=True, pooled=pooled, parts=sorted(want), parts_to_run=[],
                trials_per_drive=len(trials["sugar"]), candidate=a, dt005=b, differs=sorted(k for k in a if a[k] != b[k]),
                numerics_sensitive=bool(a != b), identical_rows=sorted(dup),
                note="the repeat is also a new draw of the Poisson input, because the input is drawn per time step")


# ---------------------------------------------------------------------------------- score
def score(D=None, smoke=SMOKE):
    D = Path(D) if D is not None else G.OUT / ("smoke" if smoke else "arms")
    first = {}
    for s in G.SETS:                      # pass 1: the main arms alone
        for w in G.GRID_W:
            got = set_at(D, s, w, pool=False, smoke=smoke)
            if got is not None:
                first[(s, w)] = got
    blocking, extra = name_topups(first)  # which top-ups the rule names
    named = sorted(set(blocking + extra))
    have = lambda a: (D / f"{a}_topup.json").exists()          # noqa: E731
    missing = [a for a in named if not have(a)]
    sets = {}
    for s in G.SETS:                      # pass 2: pool the named top-ups that exist
        rows = []
        for w in G.GRID_W:
            if (s, w) not in first:
                continue
            pooled = f"{s}_sugar_{G._w(w)}" in named and (have(f"{s}_sugar_{G._w(w)}") or have(f"{s}_blind_{G._w(w)}"))
            rows.append(set_at(D, s, w, pool=True, smoke=smoke)[0] if pooled else first[(s, w)][0])
        viable = [r["w_scale"] for r in rows if r["status"] == "viable"]
        sets[s] = dict(role=G.SETS[s]["role"], settings=G.settings_of(s), grid=rows, state=state(rows),
                       viable=bool(viable), decision_w=min(viable) if viable else None,
                       not_passing={G._w(r["w_scale"]): {k: c["verdict"] for k, c in r["components"].items()
                                                         if c["verdict"] != "PASS"} for r in rows})
    # which still-missing top-ups hold the outcome, judged again on the pooled rows (a row is still a candidate
    # only where its top-up is missing): a top-up that made an earlier set viable releases the later ones
    second = {(s, r["w_scale"]): (r, [f"{s}_sugar_{G._w(r['w_scale'])}", f"{s}_blind_{G._w(r['w_scale'])}"])
              for s in G.DECISION if s in sets for r in sets[s]["grid"]}
    missing_blocking = sorted(set(name_topups(second)[0]) & set(missing))
    p0 = p0_replication(sets)
    states = {s: v["state"] for s, v in sets.items()}
    complete = all(s in sets and len(sets[s]["grid"]) == len(G.GRID_W) for s in G.SETS)
    if complete:
        outcome = decide(states, {s: v["decision_w"] for s, v in sets.items()}, p0["replicates"], missing_blocking)
    else:
        outcome = dict(code=None, candidate=None, w=None, final=False, why="arms missing (smoke): no outcome")
        if smoke and "p0" in sets and not p0["replicates"]:
            outcome = dict(outcome, code="R", why="P0 does not replicate phase A's cell 1 (smoke data: expected)")
    dt = dt_check(D, outcome, sets, smoke=smoke)
    outcome, states_h = finalize(outcome, dt, states)
    label = {"reported": "extrapolated: never adopted", "sensitivity": "sensitivity: never adopted"}
    outcome["not_adoptable_but_viable"] = {s: dict(decision_w=v["decision_w"], label=label[v["role"]])
                                           for s, v in sets.items() if v["viable"] and v["role"] in label}
    orn = orn_check(D, smoke=smoke)
    val = v7a(D, smoke=smoke)
    flags = []
    if val["numerics_low"]:
        flags.append(f"V7a (report-only): lowest v below E_i - {G.NUMERICS_MARGIN_MV} mV, or not recorded, in {val['numerics_low']}")
    if orn["unexpected_differences"]:
        flags.append(f"ORN-under-sugar check: arms differ from their reference although no ORN fired: {orn['unexpected_differences']}")
    if dt.get("numerics_sensitive"):
        flags.append(f"the candidate is numerics-sensitive: components {dt['differs']} differ at dt 0.05 ms")
    if dt.get("needed") and not dt.get("done"):
        flags.append(dt["note"])
    dup = sorted(a for v in sets.values() for r in v["grid"] for a in r["identical_rows"]) + list(dt.get("identical_rows") or [])
    if dup:
        flags.append(f"rows identical to the main arm's although the arm is not silent (a copy, not a new run?): {dup}")
    num = sorted(f"{s}_{G._w(r['w_scale'])}" for s, v in sets.items() for r in v["grid"]
                 if r["components"].get("numerics", {}).get("verdict") == "FAIL")
    if num:
        flags.append(f"NUMERICS FAIL (v below E_i - {G.NUMERICS_MARGIN_MV} mV): {num}")
    counts = {s: dict(n_lif_sugar=v["grid"][0]["sugar"]["n_lif"], n_lif_blind=v["grid"][0]["blind"]["n_lif"],
                      n_std_syn_sugar=v["grid"][0]["sugar"]["n_std_syn"], n_std_syn_blind=v["grid"][0]["blind"]["n_std_syn"])
              for s, v in sets.items() if v["grid"]}
    report = dict(benchmark=G.LABEL, smoke=bool(smoke), criteria=G.CRITERIA, outcome=outcome, flags=flags,
                  p0_replication=p0, p0_rows=p0_rows(D, smoke=smoke), sets=sets,
                  topups_named=[a + "_topup" for a in named], topups_missing=[a + "_topup" for a in missing],
                  topups_blocking_missing=[a + "_topup" for a in missing_blocking],
                  topups_for_hypothesis_only=[a + "_topup" for a in sorted(set(extra))],
                  topup_parts=sorted({f"g7-topup-{a.split('_')[0]}-{a.split('_')[2]}" for a in missing}),
                  dt_parts=dt.get("parts_to_run") or [],
                  hypotheses=hypotheses(states_h, outcome, p0["replicates"]) if complete else None,
                  dt_check=dt, orn_check=orn, cell_counts=counts, v7a=val,
                  registration=registry.stamp(G.REG) if G.REG else None)
    return report


def main():
    report = score()
    out = (G.OUT / "smoke" / "gen7.json") if SMOKE else G.OUT / "gen7.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, default=float) + "\n", encoding="utf-8")
    for s, c in report["sets"].items():
        line = "  ".join(f"{r['w_scale']}:{r['status'][:9]}" for r in c["grid"])
        print(f"  {s:<9} {c['role']:<11} {c['state']:<12} w*={c['decision_w']}  {line}")
    o = report["outcome"]
    print(f"P0 replicates phase A's cell 1: {report['p0_replication']['replicates']}"
          f" (rows identical in {report['p0_rows']['identical']} of {report['p0_rows']['compared']} arms)")
    print(f"outcome: {o['code']}{'' if o['final'] else ' (not final)'}: {o['why']}")
    for f in report["flags"]:
        print(f"FLAG: {f}")
    if report["topup_parts"]:
        print(f"top-ups to run: {', '.join(report['topup_parts'])}")
    if report["dt_parts"]:
        print(f"dt repeat to run: {', '.join(report['dt_parts'])}")
    if report["hypotheses"]:
        print("hypotheses: " + ", ".join(f"{k} {v['verdict']}" for k, v in report["hypotheses"].items()))
    print("V7a consistent glomeruli: " + ", ".join(f"{k} {v}" for k, v in report["v7a"]["consistent_by_arm"].items()))
    print(f"-> {out.relative_to(ROOT)}" + ("   (SMOKE: not a result)" if SMOKE else ""))


if __name__ == "__main__":
    main()
