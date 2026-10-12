"""
flycns launcher: one menu for setup, benchmarks, fits, exploration and visualization.

    .\fly.cmd          (runs this file in the project's environment)
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "scripts"))
from flycns.windows import console, load_token_into_env, open_path, open_text, TOKEN_FILE  # noqa: E402
from menu_guard import benchmark_script, safe_extract  # noqa: E402

console()
load_token_into_env()        # so the fetch scripts see the token saved by setup.cmd
STATE = ROOT / ".flycns_state.json"
state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"cell": "DNp01"}

def save():
    STATE.write_text(json.dumps(state), encoding="utf-8")

def run(*cmd, env=None):
    e = dict(os.environ); e.update(env or {})
    try:
        subprocess.run([sys.executable, *cmd] if (cmd[0].endswith(".py") or cmd[0] == "-m") else list(cmd), env=e)
    except KeyboardInterrupt:
        print("\n(interrupted)")

def status():
    have = lambda p: "yes" if Path(p).exists() else "no "
    t = os.environ.get("NEUPRINT_TOKEN", "")
    tok = "set" if (len(t) > 40 and "<" not in t and "token" not in t.lower()) else \
          f"NOT SET. Run setup.cmd, which asks for it once and saves it to {TOKEN_FILE}"
    suite = ""
    if Path("results/SUITE.md").exists():
        for line in Path("results/SUITE.md").read_text(encoding="utf-8").splitlines():
            if "checks pass" in line:
                suite = line.strip("* "); break
    print(f"""
  data/neurons.parquet {have('data/neurons.parquet')}   data/edges.parquet {have('data/edges.parquet')}   annotations {have('data/neurons.parquet') if 'subclass' in _cols() else 'no '}
  neuprint token: {tok}
  last suite: {suite or 'none run'}
  selected cell for neuron view: {state['cell']}""")

def _cols():
    # in a child process: the menu itself never loads compiled libraries, which on Windows would lock
    # their files while menu 51 or setup updates the environment
    r = subprocess.run([sys.executable, "-c", "import pyarrow.parquet as pq; "
                        "print(','.join(pq.read_schema('data/neurons.parquet').names))"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip().split(",") if r.returncode == 0 else []

def ask(prompt, default=""):
    v = input(f"{prompt}{' [' + default + ']' if default else ''}> ").strip()
    return v or default

MENU = """
  flycns  ::  benchmarked spiking simulation of the Drosophila CNS (MaleCNS v1.0)
  ------------------------------------------------------------------------------
  SETUP          1  fetch connectome (neurons + edges, ~5 min)
                 2  fetch sensory annotations (subclass, entry nerve)
                45  fetch sex-related annotations (dimorphism, fruitless, doublesex)
                 3  status
  BENCHMARKS     4  run core suite (3 circuits, ~40 min)      5  run one benchmark
                 6  show suite summary                        7  robustness battery (overnight)
  CHECKS        35  audit every stimulus set against the dataset (seconds; run before long jobs)
                46  regression test: unit checks + whole toy suite in an isolated copy (~10 min)
                49  integrity: code committed? settings overridden? data match data/MANIFEST.json?
                50  stricter null: escape and pC1 controls on a superclass-preserving shuffle (registered)
                51  canonical rerun: update, pin data, core suite, stricter null; results to a review branch (~1.5 h)
                28  cord parameter sensitivity (do brain values distort the nerve cord?)
                36  flight sensitivity: does DLM's silence depend on the relay layer's parameters?
  FITS           8  GF adaptation sweep       9  SEZ regional gain sweep      10  afferent screen
                26  tonic baseline sweep
  RECORDED DATA 21  get Turner 2022 glomerulus data (Dryad, browser)   22  extract measured loom tuning
  CONNECTOME+   23  fetch per-synapse neurotransmitter probabilities (2.7 GB)
                24  neurotransmitter confidence per edge      25  neuropil ROI membership / meshes
  FEEDING       27  why feeding fails: measured mechanism
                31  is there an aminergic modulator in the SEZ? (dataset audit)
                40  feeding re-test by taste modality (Tastekin et al. 2026), registered
                41  signed sensory-to-motor map: every GRN type x every feeding MN (registered)
                42  sugar laterality: does one-sided sugar favour the opposite MN9? (registered)
  SOCIAL        43  pC1 song: can the dynamic model explain what static paths could not? (registered)
  AUDITORY      47  A2 facilitation at 120 trials per arm, scored against Tootoonian 2012 (registered)
                48  A2 robustness: facilitation across near-threshold working points (registered)
                44  DNp13 positive control: is the sine-song neuron reachable at all? (registered)
  FLIGHT        33  gate: are the wing and haltere afferents identifiable and do they form a loop
                34  flight loop: phase-locked campaniform drive at 202 Hz (surrogate body)
                37  SNpp16: is DVMn's drive carried by one named wing campaniform type?
                38  SNpp16 graded test (criteria registered before the run)
                39  SNpp16 robustness battery: transmitter uncertainty, cord parameters, fresh draws
  TRACES        29  AstA: separate Pm3's synaptic and peptidergic effects (exploratory)
                30  ear to wing motor pathway (structural finding, not a benchmark)
                32  DNp31: the strongest descending drive to the wing muscles
  EXPLORE       11  interactive: pick a sensory group, stimulate, watch the cascade
                12  whole-CNS cascade (braille, terminal)     13  same, with synapse sites
                14  single neuron view  (current: {cell})     15  choose cell for neuron view
                16  3D cascade (html, opens in browser)
  EXPORT        20  simulated sessions in brainsets/POYO+ layout (HDF5 with connectome unit features)
  DOCS          17  results note      18  references      19  provenance of last run
                 q  quit
"""

while True:
    print(MENU.format(cell=state["cell"]))
    c = ask("select").lower()
    if c in ("q", "quit", ""):
        break
    elif c == "1": run("scripts/fetch_malecns.py")
    elif c == "2": run("scripts/fetch_annotations.py")
    elif c == "45": run("scripts/fetch_dimorphism.py")
    elif c == "3": status()
    elif c == "4": run("scripts/run_all.py", ask("trials", "40"))
    elif c == "5":
        b = ask("benchmark (gf_escape / auditory / feeding, or another name in benchmarks)", "gf_escape")
        script = benchmark_script(b)
        if script is None:
            print(f"  {b!r} is not a benchmark: give a script name from the benchmarks folder, without a path")
        else:
            run(str(script.relative_to(ROOT)), ask("trials", "40"))
            if script.stem == "gf_escape": state["cell"] = "DNp01"; save()
            if script.stem == "feeding": state["cell"] = "MN9"; save()
    elif c == "6":
        run("benchmarks/summarize.py")
    elif c == "7":
        print("  the robustness suites, several hours; keeps Windows awake; each is committed to a new review branch,\n"
              "  which is pushed (your own branch is not), and you are switched back at the end")
        if ask("start now? (y/n)", "n").lower() == "y": run("scripts/overnight.py")
    elif c == "8": run("benchmarks/fit_gf_adapt.py", ask("trials (40 or more)", "40"))
    elif c == "9": run("benchmarks/fit_regional.py", ask("trials", "6"))
    elif c == "10":
        run("benchmarks/screen_afferents.py", ask("trials", "3"), "data", ask("rate Hz", "50"), ask("w_scale", "0.4"))
    elif c == "11":
        print("  SEZ gain: 1.0 is the declared model. The regional gain of 2.0 is retired (an artefact of naming the\n"
              "  SEZ by cell type, 8 September 2026); other values are for exploration only")
        run("viz/explore.py", "--sez", ask("SEZ gain", "1.0"))
    elif c == "12":
        run("viz/cascade_ascii.py", *([] if ask("layout: landscape / portrait", "landscape") == "landscape" else ["--portrait"]))
    elif c == "13":
        if not Path("results/gf_escape/cascade_sites.parquet").exists():
            print("  fetching synapse sites for the cascade neurons (needs token)..."); run("viz/fetch_cascade_synapses.py")
        run("viz/cascade_ascii.py", "--synapses")
    elif c == "14":
        flags = []
        v = ask("view: dorsal / side / front", "dorsal")
        if v != "dorsal": flags.append(f"--{v}")
        if ask("show synapses? (y/n)", "y").lower() == "y": flags.append("--synapses")
        if ask("mark synapses onto top partner? (y/n)", "n").lower() == "y": flags.append("--partners")
        run("viz/neuron_ascii.py", state["cell"], *flags)
    elif c == "15":
        state["cell"] = ask("cell type or bodyId (e.g. DNp01, TTMn, MN9, LC4, 10001)", state["cell"]); save()
    elif c == "16":
        run("viz/cascade_3d.py")
        if Path("results/gf_escape/cascade_3d.html").exists(): open_path(ROOT / "results/gf_escape/cascade_3d.html")
    elif c == "20": run("scripts/export_brainsets.py", ask("trials per session", "40"))
    elif c == "21":
        dest = ROOT / "data" / "turner2022"; dest.mkdir(parents=True, exist_ok=True)
        need = ["README.rtf", "template_brain.zip", "datafiles.zip"]
        dl = Path.home() / "Downloads"
        if not all((dest / n).exists() or (dl / n).exists() for n in need):
            print("""
  Dryad blocks scripted downloads, so this one is by hand, once:
    1. the page opening now: click README.rtf, template_brain.zip (0.7 GB) and datafiles.zip (22 GB)
       (skip behavior_tracking, anatomical_brains, transforms and mean_brain)
    2. when all three are in your Downloads folder, choose 21 again: they are moved and unpacked for you""")
            open_path("https://doi.org/10.5061/dryad.h44j0zpp8")
        else:
            for n in need:
                if (dl / n).exists() and not (dest / n).exists():
                    shutil.move(str(dl / n), str(dest / n)); print(f"  moved {n}")
            for z in ("template_brain.zip", "datafiles.zip"):
                print(f"  unpacking {z} ...")
                n, refused = safe_extract(dest / z, dest)
                for name, why in refused[:10]:
                    print(f"    refused {name!r}: {why}")
                if refused:
                    print(f"    {len(refused)} entr{'y' if len(refused) == 1 else 'ies'} refused; {n} unpacked")
            print(f"  ready in {dest}. Next: option 22 extracts the loom tuning.")
    elif c == "22":
        if subprocess.run([sys.executable, "-m", "pip", "show", "visanalysis"], capture_output=True).returncode != 0:
            run("-m", "pip", "install", "-q", "git+https://github.com/ClandininLab/visanalysis")
        run("fit/extract_turner_loom.py", "data/turner2022")
        if Path("results/turner2022/loom_tuning.json").exists() and ask("activate measured tuning for benchmarks? (y/n)", "y") == "y":
            shutil.copy("results/turner2022/loom_tuning.json", "data/loom_tuning_measured.json"); print("  activated")
    elif c == "23": run("scripts/fetch_bulk.py", ask("target: synapse-nt / annotations / connectome / all", "synapse-nt"))
    elif c == "24": run("fit/synapse_nt.py")
    elif c == "25":
        run("fit/roi_membership.py")
        if ask("also build neuropil meshes for the 3D view? (large download) (y/n)", "n") == "y":
            run("-m", "pip", "install", "-q", "cloud-volume", "trimesh", "scikit-image")
            run("fit/roi_membership.py", "--meshes")
    elif c == "26": run("benchmarks/fit_baseline.py", ask("trials", "6"))
    elif c == "27": run("benchmarks/feeding_mechanism.py")
    elif c == "28": run("benchmarks/sensitivity_cord.py", ask("trials", "20"))
    elif c == "29": run("benchmarks/peptide_asta.py", ask("trials", "10"))
    elif c == "30": run("benchmarks/auditory_wing_trace.py")
    elif c == "32": run("benchmarks/dnp31_trace.py")
    elif c == "33": run("benchmarks/embodiment_gate.py")
    elif c == "35": run("fit/audit_stimuli.py")
    elif c == "46": run("tests/regression.py")
    elif c == "49": run("-m", "flycns.integrity", "status", "data")
    elif c == "50": run("benchmarks/null_strict.py")
    elif c == "51": run("scripts/canonical_rerun.py")
    elif c == "36": run("benchmarks/sensitivity_flight.py", ask("wingbeat cycles per arm", "400"))
    elif c == "37": run("benchmarks/flight_snpp16.py", ask("wingbeat cycles per arm", "400"))
    elif c == "38": run("benchmarks/flight_snpp16_graded.py", ask("wingbeat cycles per arm", "400"))
    elif c == "39": run("benchmarks/flight_snpp16_robustness.py", ask("wingbeat cycles per arm", "400"))
    elif c == "40": run("benchmarks/feeding_by_modality.py", ask("trials", "6"))
    elif c == "41": run("benchmarks/gustatory_signed_map.py")
    elif c == "42": run("benchmarks/sugar_laterality.py")
    elif c == "43": run("benchmarks/pc1_song.py", ask("trials", "10"))
    elif c == "47": run("benchmarks/a2_registered.py", ask("trials per arm", "120"))
    elif c == "48": run("benchmarks/a2_robustness.py", ask("trials per arm", "100"))
    elif c == "44": run("benchmarks/dnp13_control.py", ask("trials", "10"))
    elif c == "34": run("benchmarks/flight_loop.py", ask("wingbeat cycles per arm", "400"))
    elif c == "31": run("fit/check_modulators.py")
    elif c == "17": open_text(ROOT / "RESULTS.md")
    elif c == "18": open_text(ROOT / "REFERENCES.md")
    elif c == "19":
        for p in Path("results").glob("*/provenance.md"): print(f"\n--- {p}\n" + p.read_text(encoding="utf-8"))
    else:
        print("  unknown option")
    input("\n  enter to return to menu...")
