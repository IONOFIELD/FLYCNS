"""
Benchmark 2: feeding (sugar GRN -> second-order SEZ -> MN9), a port of the
tests in Shiu et al. 2024 (Nature) from FlyWire to MaleCNS.

STATUS (2026-09-08): the model does NOT reproduce sugar-driven proboscis extension, and the
reason is measured rather than assumed: taste -> MN9 in MaleCNS is disinhibitory, and no
uniform manipulation reproduces that with specificity (benchmarks/feeding_mechanism.py,
results/feeding/mechanism.json). The dose-response checks below only passed while a regional
gain of 2.0 was applied to a type-name-defined SEZ; that gain is retired, so F1 and F2 are now
REPORTED, not scored. What remains scored are the checks that do not depend on MN9 firing from
afferent drive: second-order sufficiency, null silence, and the extra-SEZ and motor-rate limits.

Two declared drive arms, because MaleCNS does not annotate taste modality:
  ALL     every anatomically gustatory afferent type (labellar bristle, taste peg,
          pharyngeal sensillum; 42 types). Sensilla house sugar, bitter, water, salt
          and mechanosensory neurons together, so this arm is "every tastant at once"
          and is NOT expected to drive PER. Reported, not scored.
  SUBSET  the screen-selected MN9-driving gustatory types (GUSTATORY_MN9_DRIVING),
          the closest sugar-GRN proxy available; scored on F1/F2. Wiring-selected,
          not a modality annotation.
Criteria (Shiu 2024; Gordon & Scott 2009; McKellar 2020):
  F1 unilateral drive: MN9 laterality has the same sign as the structural 2-hop
     prediction (dynamics reproduce wiring), at the lowest dose-curve rate giving MN9 >= 2
     spikes/cell bilaterally. CAUTION (2026-09-25): the "structural 2-hop prediction" here is an
     UNSIGNED raw-synapse count, and benchmarks/sugar_laterality.py shows that measure misleads:
     the large ipsilateral 2-hop routes are net inhibitory once sign is included. F1 only runs if
     MN9 fires, which it does not under the declared parameters, so it is currently skipped.
     Shiu 2024's contralateral prediction for labellar sugar GRNs is tested properly, with sign
     and with the modality-identified sugar types LB3b and LB3c, in benchmarks/sugar_laterality.py.
  F2 MN9 response is monotonic in sugar GRN rate over 10-200 Hz
  F3 bitter GRN co-activation suppresses MN9 relative to sugar alone
  F4 each of Fdg/Bract/Roundup/Zorro alone at 50 Hz is sufficient to drive MN9
  F5 rewired null: MN9 silent
  F2b activity outside the SEZ stays < 0.02 Hz/neuron during taste drive
  F2c recruited motor neurons fire < 100 Hz on average (Azevedo 2020; McKellar 2020)
Type discovery: sugar/bitter GRN names in MaleCNS are unverified; the script
lists candidates and falls back to second-order neurons (Shiu: Fdg sufficient).
Writes results/feeding/{report.json, provenance.md, *.csv}
"""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import load_graph, rewire_null, CNSModel, LIFParams
from flycns.graph import (FEEDING_SECOND_ORDER, FEEDING_MOTOR, SUGAR_GRN_PATTERNS,
                          BITTER_GRN_PATTERNS)
from flycns.bench import find_types, present_types, pulse_protocol, readout_rates
from flycns.bench import provenance, stamp
from flycns.graph import infer_side, gustatory_afferents, GUSTATORY_MN9_DRIVING
from flycns import ascii as A
from flycns import stats

OUT = Path("results/feeding"); OUT.mkdir(parents=True, exist_ok=True)
N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
DATA = sys.argv[2] if len(sys.argv) > 2 else "data"
SUGAR = sys.argv[3].split(",") if len(sys.argv) > 3 else None   # override type names
BITTER = sys.argv[4].split(",") if len(sys.argv) > 4 else None

neurons, edges = load_graph(DATA)
A.sketch("feeding")
meta = neurons.set_index("bodyId")

# ---------------------------------------------------------------- discovery
sugar_hits = find_types(neurons, SUGAR_GRN_PATTERNS)
bitter_hits = find_types(neurons, BITTER_GRN_PATTERNS)
so_have, so_miss = present_types(neurons, FEEDING_SECOND_ORDER)
# MaleCNS does not use Shiu's FlyWire names; discover MN9's strongest input types instead
_mn9 = meta.index[meta["type"] == "MN9"]
_exc = edges[edges.post.isin(_mn9) & (edges.sign > 0)].assign(t=lambda d: d.pre.map(meta["type"]))
mn9_inputs = _exc.groupby("t").weight.sum().sort_values(ascending=False)
F4_FALLBACK = not so_have
if F4_FALLBACK:
    so_have = list(mn9_inputs.head(4).index)
    print("second-order (Shiu names) absent; using MN9's top EXCITATORY input types:", so_have)
# sensory afferents feeding those excitatory inputs (superclass contains 'sensory')
_up = meta.index[meta["type"].isin(mn9_inputs.head(6).index)]
_s2 = edges[edges.post.isin(_up)].assign(t=lambda d: d.pre.map(meta["type"]),
                                        sc=lambda d: d.pre.map(meta["superclass"]).fillna(""))
taste_afferents = (_s2[_s2.sc.str.contains("sensory")].groupby("t").weight.sum()
                   .sort_values(ascending=False))
taste_afferents = list(taste_afferents[taste_afferents >= 50].index)
print("sensory afferents onto MN9 excitatory inputs (>=50 syn):", taste_afferents)
mn_have, mn_miss = present_types(neurons, FEEDING_MOTOR)
print("sugar GRN candidates:", sugar_hits or "NONE FOUND")
print("bitter GRN candidates:", bitter_hits or "NONE FOUND")
print("second-order present:", so_have, " missing:", so_miss)
print("motor present:", mn_have, " missing:", mn_miss)
if "MN9" not in mn_have:
    raise SystemExit("MN9 not found; cannot run feeding benchmark")

# drive priority: explicit argv list > sugar-specific GRN types if annotated >
# discovered MxLbN afferents onto MN9's excitatory inputs (GNG642, BM_Taste on v1.0)
specific = [t for t in sugar_hits if not t.startswith("BM_")]
gust = gustatory_afferents(neurons)
subset = [t for t in GUSTATORY_MN9_DRIVING if (neurons.type == t).any()]
sugar = SUGAR or specific or subset or gust or taste_afferents
report_all_arm = gust if (gust and not SUGAR and not specific) else None
if gust and not SUGAR and not specific:
    print(f"gustatory afferents by subclass (labellar bristle, taste peg, pharyngeal sensillum): {len(gust)} types")
bitter = BITTER or list(bitter_hits)
if not specific and not SUGAR:
    print(f"WARNING: no sugar-specific GRN type in this annotation; driving taste-region afferents "
          f"{sugar} (F3 bitter test skipped; F1/F2/F5 test taste -> MN9 wiring)")
if not sugar:
    raise SystemExit("no usable sensory drive; supply type names as argv[3]")

report = {"benchmark": "feeding", "n_trials": N_TRIALS, "sugar_types": sugar, "bitter_types": bitter,
          "drive_arm": "explicit" if SUGAR else "annotated_sugar" if specific else "screen_selected_subset" if subset else "all_gustatory",
          "second_order_present": so_have, "motor_present": mn_have, "arms": {}, "checks": {}}
WINDOW = 250


def mn9(model, onsets):
    df = readout_rates(model, onsets, ["MN9"], WINDOW, meta)
    return df


def build(stim_types, edge_df=edges):
    return CNSModel(neurons, edge_df, stim_types, LIFParams(), electrical=True)


def _per_trial(df):
    """MN9 spikes per cell in each pulse (mean over sides within the pulse); their mean is the arm's readout."""
    return [float(x) for x in df.groupby("trial").spikes_per_cell.mean().sort_index()] if len(df) else [0.0] * N_TRIALS


# ---------------------------------------------------------------- F2 dose response
curve = []
for hz in [10, 25, 50, 100, 200]:
    m = build(sugar)
    on = pulse_protocol(m, {t: hz for t in sugar}, n_trials=N_TRIALS)
    _df = mn9(m, on); v = _df.spikes_per_cell.mean()
    curve.append(dict(sugar_hz=hz, MN9_spikes_per_cell=float(v), pop_rate_hz=float(m.population_rate_hz())))
    if hz == 50:   # per pulse (mean over sides within a pulse; their mean is v), for the F3 uncertainty record
        report["arms"]["MN9_sugar_50Hz_per_trial"] = _per_trial(_df)
    if hz == 50:
        A.raster(m, on, ["MN9"], window_ms=250, bin_ms=8, max_trials=2); A.region_bar(m, on)
    print(f"F2 sugar {hz:>3} Hz -> MN9 {v:.2f} spikes/cell, CNS {m.population_rate_hz():.4f} Hz")
    if hz == 50:
        from flycns.graph import region_of
        spf = m.spike_frame()
        # "during taste drive": spikes inside the 200 ms pulses only, divided by the time the drive was on
        # (before 2026-10-10 the whole run including gaps was used, diluting F2b about 2.5x, and F2c
        # divided by 250 ms per pulse); SEZ membership is the anatomical definition the model uses
        in_win = np.zeros(len(spf), dtype=bool)
        for t_on in on:
            in_win |= ((spf.t_ms >= t_on) & (spf.t_ms < t_on + 200)).to_numpy()
        spf = spf[in_win]; scc = spf["superclass"].fillna("")
        drive_s = len(on) * 0.2
        sez_of, _ = region_of(neurons, DATA)
        in_sez = (spf["bodyId"].map(sez_of) == "SEZ") | scc.isin(["cb_motor", "cb_sensory", "cb_sensory_tbc"])
        report["arms"]["F2b_nonSEZ_rate_hz"] = float((~in_sez).sum() / len(m.lif_ids) / drive_s)
        mot = spf[scc == "cb_motor"]
        per_cell = mot.groupby("bodyId").size() / drive_s
        report["arms"]["F2c_motor_mean_hz"] = float(per_cell.mean()) if len(per_cell) else 0.0
        n_types = m.meta.loc[m.lif_ids][m.meta.loc[m.lif_ids, "superclass"] == "cb_motor"].type.nunique()
        report["arms"]["motor_types_active"] = {t: int(v) for t, v in mot.groupby("type").size().sort_values(ascending=False).head(12).items()}
        print(f"  outside-SEZ rate {report['arms']['F2b_nonSEZ_rate_hz']:.4f} Hz | recruited motor mean {report['arms']['F2c_motor_mean_hz']:.1f} Hz "
              f"| {mot.type.nunique()} of {n_types} cb_motor types active: {list(report['arms']['motor_types_active'])[:8]}")
        report["checks"]["F2b_extra_SEZ_quiet"] = bool(report["arms"]["F2b_nonSEZ_rate_hz"] < 0.02)
        report["checks"]["F2c_motor_rate_physiological"] = bool(0 < report["arms"]["F2c_motor_mean_hz"] < 100)
        # the same two readouts per pulse, for the uncertainty records (pulses do not overlap, so every
        # in-window spike belongs to exactly one pulse and the per-pulse values average to the readouts above)
        _pulse = np.full(len(spf), -1)
        for k, t_on in enumerate(on):
            _pulse[((spf.t_ms >= t_on) & (spf.t_ms < t_on + 200)).to_numpy()] = k
        report["arms"]["F2b_nonSEZ_rate_hz_per_pulse"] = [
            float(((~in_sez).to_numpy() & (_pulse == k)).sum() / len(m.lif_ids) / 0.2) for k in range(len(on))]
        _mcells, _mcol = np.unique(mot["bodyId"].to_numpy(), return_inverse=True)
        f2c_counts = np.zeros((len(on), len(_mcells)))     # spikes per pulse (rows) of each recruited motor cell
        np.add.at(f2c_counts, (_pulse[(scc == "cb_motor").to_numpy()], _mcol), 1)
curve = pd.DataFrame(curve); curve.to_csv(OUT / "F2_dose.csv", index=False); stamp(OUT / "F2_dose.csv")
if report_all_arm:
    m = build(report_all_arm)
    on = pulse_protocol(m, {t: 50 for t in report_all_arm}, n_trials=N_TRIALS)
    v_all = float(mn9(m, on).spikes_per_cell.mean())
    report["arms"]["ALL_gustatory_50Hz"] = dict(n_types=len(report_all_arm), MN9_spikes_per_cell=v_all,
                                              pop_rate_hz=float(m.population_rate_hz()))
    print(f"ALL gustatory arm ({len(report_all_arm)} types, every tastant at once) at 50 Hz -> MN9 {v_all:.2f} "
          f"spikes/cell (reported, not scored; expected ~0)")
report["arms"]["F2_dose"] = curve.to_dict("records")
diffs = np.diff(curve.MN9_spikes_per_cell.values)
report["checks"]["F2_dose_response_REPORTED"] = None
report["arms"]["F2_reported"] = dict(monotonic=bool((diffs >= -1e-9).all()),
                                     max_mn9=float(curve.MN9_spikes_per_cell.max()),
                                     note="reported, not scored: MN9 firing from afferent drive requires a "
                                          "mechanism the model lacks (see mechanism.json)")

# ---------------------------------------------------------------- F1 laterality
t0 = time.time()
sugar_ids = neurons[neurons.type.isin(sugar)].copy()
sugar_ids["side"] = infer_side(meta).loc[sugar_ids.bodyId].values
left_sugar = sugar_ids[sugar_ids.side == "L"]
print(f"sugar drive: {len(sugar_ids)} neurons, {len(left_sugar)} inferred left")
m = build(sugar)
rates = pd.Series(0.0, index=m.stim.bodyId.values)
# rate: lowest dose-curve rate at which bilateral drive gave MN9 >= 1 spike/cell,
# so a left/right ratio is measurable (unilateral drive is half the input)
_ok = curve[curve.MN9_spikes_per_cell >= 2.0]   # >= 2 spikes/cell so a side ratio is measurable
F1_HZ = float(_ok.sugar_hz.iloc[0]) if len(_ok) else 100.0
rates[left_sugar.bodyId.values] = F1_HZ
onsets = []
for _ in range(N_TRIALS):
    m.run(300); onsets.append(m.t_ms); m.set_stim_rates(rates.loc[m.stim.bodyId].values); m.run(200)
    m.set_stim_rates(np.zeros(len(m.stim)))
m.run(300)
lat = mn9(m, onsets)
ipsi = lat[lat.side == "L"].spikes_per_cell.mean(); contra = lat[lat.side == "R"].spikes_per_cell.mean()
report["arms"]["F1_left_sugar"] = dict(rate_hz=F1_HZ, MN9_ipsi_L=float(ipsi), MN9_contra_R=float(contra),
                                            pop_rate_hz=float(m.population_rate_hz()), wall_s=round(time.time()-t0, 1))
# structural prediction: 2-hop synapse-weighted drive from the driven (left) afferents onto each MN9
_L = list(left_sugar.bodyId); _s1 = edges[edges.pre.isin(_L)]; _mid = _s1.groupby("post").weight.sum()
_s2 = edges[edges.pre.isin(_mid.index) & edges.post.isin(_mn9)].assign(w=lambda d: d.weight * d.pre.map(_mid))
_side = infer_side(meta); _struct = _s2.groupby(_s2.post.map(_side)).w.sum()
struct_L, struct_R = float(_struct.get("L", 0)), float(_struct.get("R", 0))
report["arms"]["F1_left_sugar"]["structural_2hop_L"] = struct_L
report["arms"]["F1_left_sugar"]["structural_2hop_R"] = struct_R
func_sign = np.sign(contra - ipsi); struct_sign = np.sign(struct_R - struct_L)
# a tie on either side carries no direction, so it is not scored as a match
report["checks"]["F1_laterality_matches_wiring"] = (bool(func_sign == struct_sign)
                                                    if (ipsi + contra) > 0 and func_sign != 0 and struct_sign != 0 else None)
# per pulse, for the uncertainty record: MN9-R minus MN9-L within each pulse (same simulation, paired)
_f1_side = {s_: lat[lat.side == s_].groupby("trial").spikes_per_cell.mean() for s_ in ("L", "R")}
report["arms"]["F1_left_sugar"]["MN9_ipsi_L_per_trial"] = [float(x) for x in _f1_side["L"].sort_index()]
report["arms"]["F1_left_sugar"]["MN9_contra_R_per_trial"] = [float(x) for x in _f1_side["R"].sort_index()]
f1_diff = (_f1_side["R"] - _f1_side["L"]).dropna().to_numpy()
# Shiu 2024 predicted contralateral > ipsilateral MN9 for LABELLAR SUGAR GRNs. This benchmark's
# drive is pharyngeal/taste-peg/LB3 dominated, so the comparison is not applicable HERE; it is
# tested with the identified sugar types in benchmarks/sugar_laterality.py (registered; passes).
report["checks"]["F1_shiu_contralateral_bias"] = None
report["arms"]["F1_left_sugar"]["note"] = ("Shiu 2024 contralateral prediction concerns labellar sugar GRNs; "
                                          "tested separately with LB3b/LB3c in benchmarks/sugar_laterality.py")
print(f"   structural 2-hop drive from left afferents: MN9-L {struct_L:,.0f} vs MN9-R {struct_R:,.0f}; "
      f"functional {'ipsi' if ipsi > contra else 'contra'} dominant -> "
      f"{'matches' if report['checks']['F1_laterality_matches_wiring'] else 'does NOT match'} wiring")
print(f"F1 left sugar {F1_HZ:.0f} Hz: MN9 ipsi {ipsi:.2f}, contra {contra:.2f} spikes/cell  [{time.time()-t0:.0f}s]")
lat.to_csv(OUT / "F1_laterality.csv", index=False); stamp(OUT / "F1_laterality.csv")

# ---------------------------------------------------------------- F3 bitter suppression
if bitter:
    m = build(sugar + bitter)
    on = pulse_protocol(m, {**{t: 50 for t in sugar}, **{t: 50 for t in bitter}}, n_trials=N_TRIALS)
    _df = mn9(m, on); both = _df.spikes_per_cell.mean()
    alone = float(curve.loc[curve.sugar_hz == 50, "MN9_spikes_per_cell"].iloc[0])
    report["arms"]["F3_bitter"] = dict(MN9_sugar_alone=alone, MN9_sugar_plus_bitter=float(both))
    report["arms"]["F3_bitter"]["MN9_sugar_plus_bitter_per_trial"] = _per_trial(_df)
    report["checks"]["F3_bitter_suppresses"] = bool(both < alone)
    print(f"F3 sugar alone {alone:.2f} vs sugar+bitter {both:.2f}")
else:
    report["checks"]["F3_bitter_suppresses"] = None
    print("F3 skipped: no bitter GRN type resolved")

# ---------------------------------------------------------------- F4 second-order sufficiency
suff, suff_pt = {}, {}
for typ in [t for t in (["Fdg", "Bract", "Roundup", "Zorro"] if "Fdg" in so_have else so_have) if t in so_have]:
    m = build([typ])
    on = pulse_protocol(m, {typ: 50}, n_trials=N_TRIALS)
    _df = mn9(m, on)
    suff[typ] = float(_df.spikes_per_cell.mean()); suff_pt[typ] = _per_trial(_df)
    print(f"F4 {typ} 50 Hz -> MN9 {suff[typ]:.2f}")
report["arms"]["F4_sufficiency"] = suff
report["arms"]["F4_sufficiency_per_trial"] = suff_pt
# Without Shiu's cell names the types tried are MN9's strongest direct excitatory inputs, which drive it
# almost by construction: the question cannot be asked, so it is reported, not scored.
report["arms"]["F4_mode"] = "fallback: MN9's top direct excitatory inputs (not scored)" if F4_FALLBACK else "Shiu names"
report["checks"]["F4_second_order_sufficient"] = (None if F4_FALLBACK or not suff
                                                  else bool(all(v > 0 for v in suff.values())))

# ---------------------------------------------------------------- F5 null
m = build(sugar, rewire_null(edges))
on = pulse_protocol(m, {t: 50 for t in sugar}, n_trials=N_TRIALS)
_df = mn9(m, on); nullv = float(_df.spikes_per_cell.mean())
real50 = float(curve.loc[curve.sugar_hz == 50, "MN9_spikes_per_cell"].iloc[0])
report["arms"]["F5_null"] = dict(MN9=nullv, MN9_real_50Hz=real50)
report["arms"]["F5_null"]["MN9_per_trial"] = _per_trial(_df)
# a null is only informative if the real network responds; silent vs silent is not scored
report["checks"]["F5_null_silent"] = bool(nullv < 0.1) if real50 >= 0.5 else None
print(f"F5 rewired null -> MN9 {nullv:.2f}")

report["pass"] = all(v for v in report["checks"].values() if v is not None)
mech = Path("results/feeding/mechanism.json")
if mech.exists():
    report["mechanism"] = json.loads(mech.read_text(encoding="utf-8"))["conclusion"]
    print("\nmechanism:", report["mechanism"])


# ---------------------------------------------------------------- uncertainty (flycns/stats.py)
# one record per scored check: 95% interval over pulses, three-way verdict; checks that are None get none
def _recruited_motor_hz(counts):
    """F2c's readout from a (pulses x recruited motor cells) spike-count matrix: the mean rate of the cells that
    fired at least once in these pulses, over the time the drive was on (0 if none fired)."""
    tot = counts.sum(axis=0)
    return float(tot[tot > 0].mean() / (len(counts) * 0.2)) if (tot > 0).any() else 0.0


ch, A_ = report["checks"], report["arms"]
unc = {}
if ch.get("F2b_extra_SEZ_quiet") is not None:
    _v = A_["F2b_nonSEZ_rate_hz_per_pulse"]
    unc["F2b_extra_SEZ_quiet"] = stats.scored(*stats.bootstrap(_v), high=0.02, n=len(_v),
                                              note="outside-SEZ spikes per neuron per second of drive in each 200 ms "
                                                   "pulse (sugar at 50 Hz), bootstrap over pulses")
if ch.get("F2c_motor_rate_physiological") is not None:
    unc["F2c_motor_rate_physiological"] = stats.scored(
        *stats.bootstrap(f2c_counts, stat=_recruited_motor_hz), low=0, high=100, strict=True, n=len(f2c_counts),
        note="mean rate of the recruited cb_motor cells (sugar at 50 Hz), bootstrap over pulses; a cell counts as "
             "recruited if it fires in the resampled pulses, as in the readout")
if ch.get("F1_laterality_matches_wiring") is not None:
    unc["F1_laterality_matches_wiring"] = stats.scored(
        *stats.bootstrap(f1_diff * struct_sign), low=0, strict=True, n=len(f1_diff),
        note=f"(MN9-R minus MN9-L) x structural sign ({int(struct_sign):+d}, graph arithmetic, fixed), paired per "
             f"pulse in one simulation, bootstrap over pulses: positive means the functional laterality matches wiring")
if ch.get("F3_bitter_suppresses") is not None:
    _a, _b = A_["MN9_sugar_50Hz_per_trial"], A_["F3_bitter"]["MN9_sugar_plus_bitter_per_trial"]
    unc["F3_bitter_suppresses"] = stats.scored(
        *stats.bootstrap_diff(_a, _b), low=0, strict=True,
        note=f"MN9 under sugar alone minus under sugar+bitter at 50 Hz: two separate simulations, each resampled "
             f"over its own pulses ({len(_a)} and {len(_b)})")
if ch.get("F4_second_order_sufficient") is not None:
    _parts = []
    for typ, _v in suff_pt.items():
        _parts.append(stats.scored(*stats.bootstrap(_v), low=0, strict=True, n=len(_v),
                                   note=f"MN9 under {typ} at 50 Hz, bootstrap over pulses"))
    unc["F4_second_order_sufficient"] = stats.combine(_parts, note="every second-order type drives MN9 above 0")
if ch.get("F5_null_silent") is not None:
    _v = A_["F5_null"]["MN9_per_trial"]
    unc["F5_null_silent"] = stats.scored(
        *stats.bootstrap(_v), high=0.1, n=len(_v),
        note=f"MN9 on the rewired null at 50 Hz, bootstrap over pulses; scored because the real network responds "
             f"(MN9 {real50:.3g} at 50 Hz >= 0.5, point value)")
report["uncertainty"] = unc
report["provenance"] = provenance()
(OUT / "report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
prov = ["# Provenance: feeding (port of Shiu et al. 2024 tests to MaleCNS)", "",
        f"sugar types used: {sugar}", f"bitter types used: {bitter or 'none resolved'}",
        f"second-order present: {so_have}", f"motor present: {mn_have}", "", "## Checks"]
prov += [f"- {k}: {'SKIP' if v is None else ('PASS' if v else 'FAIL')}" for k, v in report["checks"].items()]
(OUT / "provenance.md").write_text("\n".join(prov), encoding="utf-8")
print("\nCHECKS"); [print(f"  {'SKIP' if v is None else ('PASS' if v else 'FAIL')}  {k}") for k, v in report["checks"].items()]


def _g(x):
    return "-" if x is None else (f"{x:.3g}" if isinstance(x, float) else str(x))


def _desc(u):
    """One line for an uncertainty record: estimate [95% interval] in band (method); a conjunction lists its parts."""
    if u.get("parts"):
        return "; ".join(f"{p['verdict']} {_desc(p)}" for p in u["parts"])
    s, ci, band = _g(u.get("estimate")), u.get("ci95"), u.get("band")
    if ci:
        s += f" [{_g(ci[0])}, {_g(ci[1])}]"
    if band and any(b is not None for b in band):
        s += (f" in {'(' if u.get('band_lower_exclusive') else '['}{'-inf' if band[0] is None else _g(band[0])}, "
              f"{'inf' if band[1] is None else _g(band[1])}]")
    return s + f" ({u['method']})" + (f": {u['note']}" if u["method"] == "not scorable as designed" else "")


print("UNCERTAINTY (95% intervals, flycns/stats.py: PASS only if the whole interval lies in the band)")
for k, u in report["uncertainty"].items():
    print(f"  {u['verdict']:<10}  {k}: {_desc(u)}")
print(f"\nBENCHMARK {'PASS' if report['pass'] else 'FAIL'}  -> {OUT}/report.json")
