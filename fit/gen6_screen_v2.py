"""
Generation-6 screen on the Phase 1b sweep, exactly as docs/gen6_rule.md as amended by docs/gen6_rule_v2.md
(d808f5b) defines it. Reads ONLY the raw arm files results/shiu2024_phase1b/arms/sw_male_flycns_*.json.

Not a registered benchmark: it computes no new statistic. It applies the committed rule mechanically, so the
outcome it reports can be reproduced from the repository. The formal generation-6 registration repeats it.

  FUNCTION (screen)  95% bootstrap interval of per-trial mn9_hz (two-cell mean), sugar drive; PASS iff lower > 0.5 Hz
  STABILITY          (a) 0/10 sugar self-sustained, (b) 0/10 blind self-sustained,
                     (c) blind 95% intervals of cns_rate_hz and fraction_active wholly below 1 Hz and 10%
  Outcome B          at the smallest w passing FUNCTION but failing STABILITY: G = top group of tail spikes pooled
                     over the self-sustained trials of BOTH drives (v2 grouping: VNC stems + VNC-unspecified);
                     B holds iff share(G) >= 0.5 and (a), (b), (c) pass with G's cells removed (numerator and
                     denominator; rates from summed spikes and cells, never summed rates)
  LI                 median per-trial MN9 laterality; sensitivity: trials with >= 5 MN9 spikes in the 1 s drive window

Run:  python fit/gen6_screen_v2.py      writes results/gen6_screen/screen_v2.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flycns import stats  # noqa: E402

ARMS = ROOT / "results" / "shiu2024_phase1b" / "arms"
OUT = ROOT / "results" / "gen6_screen"
GRID = ["040", "050", "060", "080", "100"]
STEMS = ("LegNp", "Ov", "mVAC", "WTct", "HTct", "NTct", "IntTct", "LTct", "ANm")
DRIVE_S, HALF_S = 1.0, 0.25          # Phase 1b: 1000 ms drive, last 250 ms of the 500 ms tail


def group(label):
    return "VNC" if (str(label).split("(")[0] in STEMS or label == "VNC-unspecified") else str(label)


def arm(drive, w):
    return json.loads((ARMS / f"sw_male_flycns_{drive}_w{w}.json").read_text(encoding="utf-8"))


def ci(x):
    e, lo, hi = stats.bootstrap(np.asarray(x, dtype=float))
    return [e, lo, hi]


def self_sustained(drive_spikes, tail_spikes, n):
    d, t = drive_spikes / n / DRIVE_S, tail_spikes / n / HALF_S
    return bool(t >= 0.1 * d and t >= 0.01)


def stability(su, bl, drop=None, sizes=None):
    """(a), (b), (c); with drop = a group name, its cells leave numerator and denominator."""
    def rows(a):
        out = []
        for t in a["trials"]:
            if drop is None:
                out.append((t["self_sustained"], t["cns_rate_hz"], t["fraction_active"]))
                continue
            N = sum(sizes.values()) - sizes.get(drop, 0)
            dg = sum(v[0] for k, v in t["drive_by_neuropil"].items() if group(k) == drop)
            tg = sum(v[0] for k, v in t["tail_by_neuropil"].items() if group(k) == drop)
            ag = sum(v[1] for k, v in t["drive_by_neuropil"].items() if group(k) == drop)
            out.append((self_sustained(t["n_spikes"] - dg, t["tail_spikes"] - tg, N),
                        (t["n_spikes"] - dg) / N / DRIVE_S, (t["n_active"] - ag) / N))
        return out
    s, b = rows(su), rows(bl)
    rate, frac = ci([x[1] for x in b]), ci([x[2] for x in b])
    a_n, b_n = sum(x[0] for x in s), sum(x[0] for x in b)
    ok = a_n == 0 and b_n == 0 and rate[2] < 1.0 and frac[2] < 0.10
    return dict(sugar_self_sustained=a_n, blind_self_sustained=b_n, blind_rate_hz=rate, blind_fraction_active=frac,
                passes=bool(ok))


def li(trials, min_spikes=0):
    v = [t["mn9_li"] for t in trials if t.get("mn9_li") is not None and sum(t["mn9_per_cell_hz"]) * DRIVE_S >= min_spikes]
    return dict(median=float(np.median(v)) if v else None, n=len(v))


def main():
    rows, first_func_fail_stab = [], None
    for w in GRID:
        su, bl = arm("sugar", w), arm("blind", w)
        mn9 = ci([t["mn9_hz"] for t in su["trials"]])
        func = bool(mn9[1] > 0.5)
        st = stability(su, bl)
        rows.append(dict(w_scale=int(w) / 100, function=dict(mn9_hz=mn9, passes=func), stability=st,
                         li=li(su["trials"]), li_min5=li(su["trials"], 5)))
        if func and not st["passes"] and first_func_fail_stab is None:
            first_func_fail_stab = w
    window = [r["w_scale"] for r in rows if r["function"]["passes"] and r["stability"]["passes"]]
    B = None
    if first_func_fail_stab:
        su, bl = arm("sugar", first_func_fail_stab), arm("blind", first_func_fail_stab)
        sizes = {}
        for k, n in su["group_sizes"]["neuropil"].items():
            sizes[group(k)] = sizes.get(group(k), 0) + n
        tot = {}
        for a in (su, bl):
            for t in a["trials"]:
                if t["self_sustained"]:
                    for k, v in t["tail_by_neuropil"].items():
                        tot[group(k)] = tot.get(group(k), 0) + v[0]
        S = sum(tot.values())
        G = max(tot, key=tot.get)
        without = stability(su, bl, drop=G, sizes=sizes)
        sugar_only = {}
        for t in su["trials"]:
            if t["self_sustained"]:
                for k, v in t["tail_by_neuropil"].items():
                    sugar_only[group(k)] = sugar_only.get(group(k), 0) + v[0]
        B = dict(w_scale=int(first_func_fail_stab) / 100, group=G, share=tot[G] / S,
                 top_shares={k: v / S for k, v in sorted(tot.items(), key=lambda kv: -kv[1])[:6]},
                 stability_without_group=without, holds=bool(tot[G] / S >= 0.5 and without["passes"]),
                 sugar_only_vnc_share=(sugar_only.get("VNC", 0) / sum(sugar_only.values())) if sugar_only else None)
    func_any = any(r["function"]["passes"] for r in rows)
    if window:
        outcome = "A or H (decided by LATERALITY at the chosen w)"
    elif not func_any:
        outcome = "D"
    elif B and B["holds"]:
        outcome = "B"
    else:
        outcome = "C"
    rep = dict(rule="docs/gen6_rule.md as amended by docs/gen6_rule_v2.md (d808f5b)", family="male_flycns",
               grid=rows, window=window, outcome_b=B, outcome=outcome)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screen_v2.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    for r in rows:
        f, s = r["function"], r["stability"]
        print(f"w {r['w_scale']:.1f}  FUNCTION {'PASS' if f['passes'] else 'fail'} {f['mn9_hz'][0]:6.2f} "
              f"[{f['mn9_hz'][1]:.2f}, {f['mn9_hz'][2]:.2f}]  STABILITY {'PASS' if s['passes'] else 'fail'} "
              f"sugar {s['sugar_self_sustained']}/10 blind {s['blind_self_sustained']}/10  LI {r['li']['median']} (n {r['li']['n']})")
    if B:
        print(f"Outcome B at w {B['w_scale']}: G {B['group']} share {B['share']:.3f}; holds {B['holds']}; "
              f"sugar-only VNC share {B['sugar_only_vnc_share']:.3f}")
    print("OUTCOME:", outcome)


if __name__ == "__main__":
    main()
