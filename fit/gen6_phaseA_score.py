"""
Score generation 6, phase A (fit/gen6_phaseA.py) exactly as docs/gen6_phaseA_DRAFT.md defines it.

    python fit/gen6_phaseA_score.py            score the registered arms (results/gen6_phaseA/arms/) -> phaseA.json
    python fit/gen6_phaseA_score.py --smoke    score whatever smoke arms exist (results/gen6_phaseA/smoke/); never
                                               a result, written to smoke/phaseA.json

This file is hashed into phase A's registration (fit/gen6_phaseA.py registers both), so a threshold changed here is a
changed registration. Every verdict is PASS, FAIL or UNRESOLVED; UNRESOLVED is never read as PASS.

B1   Viable(cell): a grid w at which FUNCTION (screen), FUNCTION-q, STABILITY (a), (b), (c) all PASS, plus LATERALITY
     for c2 and c4 (M7); the decision w is the smallest such w. The outcome table over c1-c4 is B1's. A candidate w
     (no component FAILs, at least one UNRESOLVED) asks for ONE top-up of the arm(s) whose component is UNRESOLVED;
     the top-up trials are pooled only for an arm this rule names; after that, UNRESOLVED counts as not passing.
A3   M4: PASS iff #(real > draw) >= 95 of 100 and the null is alive; FAIL iff real <= null median; else UNRESOLVED.
A4   M1/M2/M9: W* from cell 1's blind arms (at least 5 of 10 self-sustained); a cut stops it if at some w in W* its
     arm has STABILITY (b) 0 self-sustained and (c) PASS.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns import registry, stats  # noqa: E402

SMOKE = "--smoke" in sys.argv[1:]
if SMOKE:   # smoke scoring reads the design only; no registration is read or written
    __name_for_import = "gen6_phaseA_design"
else:
    __name_for_import = "gen6_phaseA"           # importing under this name registers and checks the model
_spec = importlib.util.spec_from_file_location(__name_for_import, ROOT / "fit" / "gen6_phaseA.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

T = A.CRITERIA["thresholds"]       # every bar comes from the registered criteria (one place, hashed)
RESPONDS, RATE_BAR, FRAC_BAR, LI_BAR = T["responds_hz"], T["rate_bar_hz"], T["fraction_bar"], T["li_bar"]
FQ_MIN, FQ_NEED, WSTAR_MIN, NULL_PASS = (T["function_q_min_trials"], T["function_q_need"],
                                         T["wstar_min_self_sustained"], T["null_pass_draws"])
VNC_STEMS = ("LegNp", "Ov", "mVAC", "WTct", "HTct", "NTct", "IntTct", "LTct", "ANm")
AL_LH = ("AL(L)", "AL(R)", "LH(L)", "LH(R)")
DIR = A.OUT / ("smoke" if SMOKE else "arms")


def load(name, required=True):
    f = DIR / f"{name}.json"
    if not f.exists():
        if required and not SMOKE:
            raise SystemExit(f"[score] arm {name} has no result ({f.relative_to(ROOT)})")
        return None
    rec = json.loads(f.read_text(encoding="utf-8"))
    if not SMOKE:
        st = rec.get("registration") or {}
        if st.get("model_hash") != A.REG["model"]["hash"] or not st.get("matches"):
            raise SystemExit(f"[score] arm {name} was not run under this registration ({st})")
        if rec.get("reduced"):
            raise SystemExit(f"[score] arm {name} is a smoke run, not a result")
        if json.loads(json.dumps(rec["spec"])) != json.loads(json.dumps(A.ARMS[name])):
            raise SystemExit(f"[score] arm {name} was run with another specification than the registered one")
    return rec


def col(trials, key):
    return np.array([t[key] for t in trials], dtype=float)


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
                    f"n >= {FQ_MIN}; the verdict uses the point fraction (m9)")
    if why:
        rec["note"] = why
    return rec


def count_zero(trials, label):
    n = int(sum(t["self_sustained"] for t in trials))
    return dict(estimate=n, of=len(trials), verdict="PASS" if n == 0 else "FAIL",
                rule=f"{label}: 0 self-sustained trials")


def stability_c(bl):
    r = below(col(bl, "cns_rate_hz"), RATE_BAR, "blind: whole-CNS rate, Hz")
    f = below(col(bl, "fraction_active"), FRAC_BAR, "blind: fraction active")
    return stats.combine([r, f], note="STABILITY (c): both intervals wholly below 1 Hz and 10%")


def li_summary(trials, min_spikes=0):
    v = [t["mn9_li"] for t in trials if t.get("mn9_li") is not None and t.get("mn9_spikes", 0) >= min_spikes]
    return dict(median=float(np.median(v)) if v else None, n_defined=len(v), n_trials=len(trials))


def laterality(su):
    s = li_summary(su)
    vd = "UNRESOLVED" if s["median"] is None else ("PASS" if s["median"] < LI_BAR else "FAIL")
    return dict(**s, bar=LI_BAR, verdict=vd, rule="median sugar LI over trials where defined, below 0.8",
                sensitivity_min5_spikes=li_summary(su, 5))


def modes(n_active):
    """m3: bimodal iff max > 2 x min; split at the largest gap."""
    x = sorted(int(v) for v in n_active)
    if len(x) < 2 or x[-1] <= T["bimodal_factor"] * max(1, x[0]):
        return dict(bimodal=False, median=float(np.median(x)) if x else None)
    gaps = np.diff(x)
    cut = int(np.argmax(gaps)) + 1
    lo, hi = x[:cut], x[cut:]
    return dict(bimodal=True, low_mode=dict(n=len(lo), median=float(np.median(lo))),
                high_mode=dict(n=len(hi), median=float(np.median(hi))))


def group_v2(label):
    return "VNC" if (str(label).split("(")[0] in VNC_STEMS or label == "VNC-unspecified") else str(label)


def tail_groups(trials, sizes):
    """Pooled over the self-sustained trials: tail spikes per v2 group, and rates from summed counts."""
    ss = [t for t in trials if t["self_sustained"] and "tail_by_neuropil" in t]
    if not ss or not sizes:
        return None
    gs = {}
    for k, n in sizes.get("neuropil", {}).items():
        gs[group_v2(k)] = gs.get(group_v2(k), 0) + n
    tot = {}
    for t in ss:
        for k, v in t["tail_by_neuropil"].items():
            tot[group_v2(k)] = tot.get(group_v2(k), 0) + v[0]
    S = sum(tot.values())
    top = sorted(tot.items(), key=lambda kv: -kv[1])[:8]
    sec = (A.TAIL_MS // 2) / 1000.0
    return dict(n_self_sustained=len(ss), total_tail_spikes=int(S),
                top={g: dict(share=(v / S) if S else None, rate_hz=(v / gs[g] / sec / len(ss)) if gs.get(g) else None)
                     for g, v in top})


def arm_summary(rec):
    tr = rec["trials"]
    return dict(trials=len(tr), self_sustained=int(sum(t["self_sustained"] for t in tr)),
                cns_rate_hz=list(stats.bootstrap(col(tr, "cns_rate_hz"))),
                fraction_active=list(stats.bootstrap(col(tr, "fraction_active"))),
                n_active_modes=modes([t["n_active"] for t in tr]),
                tail_groups=tail_groups(tr, rec.get("group_sizes")))


# ------------------------------------------------------------------------------------------------ B1
def cell_at(cell, w, topups):
    """Every component for one cell at one w, with top-up trials pooled where the rule named that arm."""
    name = lambda d: f"{cell}_{d}_{A._w(w)}"         # noqa: E731
    su, bl = load(name("sugar"), required=True), load(name("blind"), required=True)
    if su is None or bl is None:
        return None
    S, B = list(su["trials"]), list(bl["trials"])
    used = []
    for d, lst in (("sugar", S), ("blind", B)):
        if name(d) in topups:
            t = load(name(d) + "_topup", required=False)
            if t is not None:
                lst.extend(t["trials"])
                used.append(name(d) + "_topup")
    comp = dict(function=function_screen(S), function_q=function_q(S), stability_a=count_zero(S, "sugar"),
                stability_b=count_zero(B, "blind"), stability_c=stability_c(B))
    lat = laterality(S)       # M7: decides H for an outcome that adopts the mirror; not a viability component
    vs = [c["verdict"] for c in comp.values()]
    status = "viable" if all(v == "PASS" for v in vs) else ("fails" if "FAIL" in vs else "candidate")
    need = []
    if status == "candidate":
        for k, c in comp.items():
            if c["verdict"] == "UNRESOLVED":
                need.append(name("blind") if k == "stability_c" else name("sugar"))
    report = dict(w_scale=w, status=status, components=comp, topups_used=used,
                  laterality=lat,
                  mn9_per_cell_mean_hz=[float(np.mean([t["mn9_per_cell_hz"][i] for t in S]))
                                        for i in range(len(S[0]["mn9_per_cell_hz"]))] if S and S[0]["mn9_per_cell_hz"] else None,
                  mn9_cells=S[0]["mn9_cells"] if S else None, sugar=arm_summary(dict(su, trials=S)),
                  blind=arm_summary(dict(bl, trials=B)))
    return report, sorted(set(need))


def b1(results):
    """B1 with M7. Returns (decision, why, adopted cell, its decision w)."""
    V = {c: results[c]["viable"] for c in A.DECIDING}
    w_of = {c: results[c]["decision_w"] for c in A.DECIDING}
    tail = " " + A.CRITERIA["decision"]["provisional"].capitalize() + "."
    if V["c1"]:
        return "V1", ("cell 1 (generation-5 settings) is viable: Phase 1b's outcome C is not replicated; stop for "
                      "review"), "c1", w_of["c1"]
    if V["c2"]:
        dec, cell = "mirror", "c2"
        why = ("cells 2 and 3 both viable: adopt the MN9_R mirror only (a data fix); v-and-g reported (V3)" if V["c3"]
               else "cell 2 viable, cell 3 not: adopt the MN9_R mirror")
    elif V["c3"]:
        return "reset", "cell 3 viable, cell 2 not: adopt the v-and-g reset." + tail, "c3", w_of["c3"]
    elif V["c4"]:
        dec, cell, why = "both", "c4", "only cell 4 viable: adopt the mirror and the v-and-g reset"
    else:
        return "C", ("no deciding cell is viable: the outcome stays C (next: a change of synapse model, in its own "
                     "plan)"), None, None
    w = w_of[cell]
    row = next(r for r in results[cell]["grid"] if r["w_scale"] == w)
    if row["laterality"]["verdict"] != "PASS":
        return "H", (f"{why}, but MN9 stays one-sided in {cell} at w {w} (median LI {row['laterality']['median']}, "
                     f"bar {LI_BAR}): outcome H as amended in rule v2 section 2; no default changes"
                     + ("; v-and-g (cell 3) is viable and reported" if V["c3"] else "")), cell, w
    return dec, why + "." + tail, cell, w


# ------------------------------------------------------------------------------------------------ A3, A4
def a3():
    real = load("A3_real_m1")
    draws = [load(f"A3_null_dc_{j}") for j in range(A.NULL_DRAWS // A.NULL_PER_ARM)]
    if real is None or any(d is None for d in draws):
        return dict(verdict="UNRESOLVED", note="arms missing")
    raw = [t["mn9_hz"] for d in draws for t in d["trials"]]
    nv = [float(x) for x in raw if x is not None and not np.isnan(float(x))]
    ncns = [t["cns_rate_hz"] for d in draws for t in d["trials"]]
    r = float(np.mean(col(real["trials"], "mn9_hz")))
    rc = float(np.median(col(real["trials"], "cns_rate_hz")))
    nc = float(np.median(ncns)) if ncns else float("nan")
    alive = bool(nv) and rc > 0 and nc >= T["alive_fraction"] * rc
    k = int(sum(r > x for x in nv))
    med = float(np.median(nv)) if nv else float("nan")
    if not alive:
        vd, why = "UNRESOLVED", "the null is not active by Phase 1b's alive rule"
    elif k >= NULL_PASS:
        vd, why = "PASS", None
    elif r <= med:
        vd, why = "FAIL", None
    elif len(nv) < NULL_PASS:
        vd, why = "UNRESOLVED", f"only {len(nv)} valid draws, fewer than the {NULL_PASS} needed to pass"
    else:
        vd, why = "UNRESOLVED", None
    rec = dict(real_mn9_hz=r, draws=len(nv), invalid_draws=len(raw) - len(nv), exceeded=k, null_median=med, null_alive=alive,
               real_cns_median=rc, null_cns_median=nc, percentile=stats.percentile_of(r, nv) if nv else None,
               rule=f"PASS iff real > draw (strict) for at least {NULL_PASS} of {A.NULL_DRAWS}; FAIL iff real <= null "
                    "median; else UNRESOLVED; not alive is UNRESOLVED", deviation=A.CRITERIA["deviation"], verdict=vd,
               real_laterality=li_summary(real["trials"]))
    if why:
        rec["note"] = why
    return rec


def a4():
    base = {w: load(f"c1_blind_{A._w(w)}") for w in A.GRID_W}
    wstar = [w for w, r in base.items() if r is not None and sum(t["self_sustained"] for t in r["trials"]) >= WSTAR_MIN]
    out = dict(W_star=wstar, baseline={A._w(w): arm_summary(r) for w, r in base.items() if r is not None})

    def stops(prefix):
        per = {}
        for w in A.GRID_W:
            r = load(f"{prefix}_{A._w(w)}")
            if r is None:
                continue
            b, c = count_zero(r["trials"], "blind"), stability_c(r["trials"])
            per[A._w(w)] = dict(in_W_star=w in wstar, stability_b=b, stability_c=c, summary=arm_summary(r),
                                transform=r.get("transform"), composition=r.get("composition"))
        if not wstar:
            return dict(per_w=per, stops=None, note="W* is empty: not scorable")
        hit = [k for k, v in per.items() if v["in_W_star"] and v["stability_b"]["verdict"] == "PASS"
               and v["stability_c"]["verdict"] == "PASS"]
        return dict(per_w=per, stops=bool(hit), at=hit)
    cuts = {c: stops(f"A4_cut_{c}") for c in A.CUTS}
    out["cuts"] = cuts
    s = {c: cuts[c]["stops"] for c in A.CUTS}
    if None in s.values():
        out["projection_reading"] = out["in_al_reading"] = "not scorable (W* empty)"
    else:
        out["projection_reading"] = ("the AL-LH loop sustains the tail" if s["lh"] else
                                     "the MB route matters" if s["lhmb"] else
                                     "the loop runs inside the AL itself (see the in-AL cuts)")
        out["in_al_reading"] = ("either cut is enough" if s["i"] and s["ii"] else
                                "in the model, ACh-LN chemical output sustains the AL loop (a model-structure finding: "
                                "the fly's eLN -> PN path is electrical)" if s["i"] else
                                "excitatory PN recurrence sustains it" if s["ii"] else
                                "no single cut removes it: mechanism UNRESOLVED")
    out["drives"] = {c: stops(f"A4_drive_{c}") for c in A.COMPOSITIONS}
    sec = {}
    for w in A.GRID_W:          # M9, under drive (c)
        r = load(f"A4_drive_c_{A._w(w)}")
        if r is None:
            continue
        ss = [t for t in r["trials"] if t["self_sustained"] and "tail_by_neuropil" in t]
        if not ss:
            sec[A._w(w)] = dict(scorable=False)
            continue
        tt = sum(sum(v[0] for v in t["tail_by_neuropil"].values()) for t in ss)
        ta = sum(sum(v[0] for k, v in t["tail_by_neuropil"].items() if k in AL_LH) for t in ss)
        dt = sum(sum(v[0] for v in t["drive_by_neuropil"].values()) for t in ss)
        da = sum(sum(v[0] for k, v in t["drive_by_neuropil"].items() if k in AL_LH) for t in ss)
        tsh, dsh = (ta / tt if tt else None), (da / dt if dt else None)
        sec[A._w(w)] = dict(scorable=True, n=len(ss), tail_share=tsh, drive_share=dsh,
                            holds=bool(tsh is not None and dsh is not None and tsh >= T["tail_share_factor"] * dsh))
    out["secondary_drive_c"] = sec
    return out


def main():
    cells, topups_needed = {}, []
    first = {}
    for cell in A.CELLS:            # pass 1: which arms the top-up rule names (main arms only)
        for w in A.GRID_W:
            got = cell_at(cell, w, topups=set())
            if got is None:
                continue
            first[(cell, w)] = got
            if cell in A.DECIDING:      # top-ups only for deciding cells; 2b and 4b never decide
                topups_needed.extend(got[1])
    named = set(topups_needed)
    missing_topups = sorted(a for a in named if load(a + "_topup", required=False) is None)
    for cell in A.CELLS:            # pass 2: pool the top-ups the rule named, where they exist
        rows = []
        for w in A.GRID_W:
            if (cell, w) not in first:
                continue
            rep, _ = cell_at(cell, w, topups=named) if named else first[(cell, w)]
            if rep["status"] == "candidate" and rep["topups_used"]:
                rep["status"] = "not passing (UNRESOLVED after its top-up)"
            rows.append(rep)
        viable = [r["w_scale"] for r in rows if r["status"] == "viable"]
        cells[cell] = dict(deciding=cell in A.DECIDING, grid=rows, viable=bool(viable),
                           decision_w=min(viable) if viable else None)
    decision, why, d_cell, d_w = (b1(cells) if all(c in cells for c in A.DECIDING)
                                  else (None, "deciding cells missing", None, None))
    if missing_topups and decision is not None:
        why += f" (PROVISIONAL: top-ups named by the rule are not yet run: {missing_topups})"
    mirror_only = {}
    for w in A.GRID_W:          # M7: "below 0.8 under mirroring only"
        c1 = next((r for r in cells.get("c1", {}).get("grid", []) if r["w_scale"] == w), None)
        c2 = next((r for r in cells.get("c2", {}).get("grid", []) if r["w_scale"] == w), None)
        if c1 and c2:
            l1, l2 = c1["laterality"]["median"], c2["laterality"]["median"]
            mirror_only[A._w(w)] = dict(c1=l1, c2=l2, mirror_only=bool(l1 is not None and l2 is not None
                                                                         and l2 < LI_BAR and l1 >= LI_BAR))
    A3, A4 = a3(), a4()
    cut_stops = {c: A4["cuts"][c]["stops"] for c in A.CUTS}
    preds = dict(
        Q1=any(r["components"]["stability_b"]["verdict"] == "PASS" and r["components"]["stability_c"]["verdict"] == "PASS"
               for r in cells.get("c3", {}).get("grid", [])),
        Q2=any(r["laterality"]["median"] is not None and r["laterality"]["median"] < LI_BAR
               for r in cells.get("c2", {}).get("grid", [])),
        Q3=A3.get("verdict") == "UNRESOLVED",
        Q4=None if None in cut_stops.values() else (not cut_stops["lh"] and not cut_stops["lhmb"]),
        Q5=decision == "C",
        Q6=None if None in cut_stops.values() else bool(cut_stops["i"] or cut_stops["ii"]))
    report = dict(benchmark=A.LABEL, smoke=SMOKE, criteria=A.CRITERIA, cells=cells, decision=decision, decision_why=why,
                  decision_cell=d_cell, decision_w=d_w,
                  topups_named=sorted(named), topups_missing=missing_topups, laterality_mirror_only=mirror_only,
                  A3=A3, A4=A4, predictions={k: dict(text=A.CRITERIA["predictions"][k][0],
                                                     confidence=A.CRITERIA["predictions"][k][1], held=v)
                                             for k, v in preds.items()},
                  registration=registry.stamp(A.REG) if A.REG else None)
    out = DIR / "phaseA.json" if SMOKE else A.OUT / "phaseA.json"
    out.write_text(json.dumps(report, indent=1, default=float), encoding="utf-8")
    for cell, c in cells.items():
        line = "  ".join(f"{r['w_scale']}:{r['status'][:9]}" for r in c["grid"])
        print(f"  {cell:<4} {'deciding' if c['deciding'] else 'reported'}  viable={c['viable']!s:<5} w*={c['decision_w']}  {line}")
    print(f"B1: {decision} ({d_cell} at w {d_w}): {why}")
    print(f"A3: {A3.get('verdict')} (real {A3.get('real_mn9_hz')}, exceeds {A3.get('exceeded')} of {A3.get('draws')})")
    print(f"A4: W* {A4['W_star']}; cuts stop: {cut_stops}; projection: {A4.get('projection_reading')}; "
          f"in-AL: {A4.get('in_al_reading')}")
    print("predictions held: " + ", ".join(f"{k} {v}" for k, v in preds.items()))
    print(f"-> {out.relative_to(ROOT)}" + ("   (SMOKE: not a result)" if SMOKE else ""))


if __name__ == "__main__":
    main()
