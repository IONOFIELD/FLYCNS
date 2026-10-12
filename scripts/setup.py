"""
flycns setup. Started by setup.cmd on Windows, or run directly (python3 scripts/setup.py) on Linux and
macOS; safe to run again at any time.

  .\\setup.cmd --check     environment, then the regression test on the toy graph (no account)
  .\\setup.cmd             environment, then the connectome and its fingerprint (asks for the token once)
  .\\setup.cmd --refresh   as above without questions (used by scripts\\canonical_rerun.py)

Steps:
  1. .venv with every package pinned (requirements.lock) on Python 3.12 or newer; on 3.10 and 3.11
     the newest compatible packages (requirements.txt), with a notice
  2. git (needed so every result can be traced to a commit); offers to install it with winget
  3. the simulation engine: compiled if the Microsoft C++ Build Tools are present, otherwise the
     pure-Python engine (same results, slower); offers to install the Build Tools with winget
  4. --check: the regression test, then stop
  5. the neuPrint token: asked once, saved to %USERPROFILE%\\.neuprint_token
  6. the connectome (skipped if already present), annotations, each neuron's neuropil membership
     (the anatomical SEZ), the stimulus audit, and the data fingerprint: written to
     data\\MANIFEST.json the first time, verified every time after
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ["PYTHONUTF8"] = "1"
ARGS = set(sys.argv[1:])
QUIET = "--refresh" in ARGS or not sys.stdin.isatty()     # never prompt in CI or unattended runs
VENV_PY = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
# the commands this script tells the user to run, as spelled on this platform
SETUP = ".\\setup.cmd" if os.name == "nt" else "python3 scripts/setup.py"
MENU = ".\\fly.cmd" if os.name == "nt" else ".venv/bin/python fly.py"
# The lock installs from ready-made Windows builds only, except these pure-Python packages that are
# published only as source (they build without a compiler). CI installs with the same flags.
SOURCE_OK = "asciitree"
WHEELS_ONLY = ["--only-binary=:all:", f"--no-binary={SOURCE_OK}"]


def _windows_helpers():
    """flycns/windows.py loaded on its own: this script runs before the packages that the flycns
    package needs are installed, and windows.py uses only the standard library."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("flycns_windows", ROOT / "flycns" / "windows.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


W = _windows_helpers()
W.console()


def say(msg=""):
    print(msg, flush=True)


def ask_yes(question, default=True):
    if QUIET:
        return False
    hint = "[Y/n]" if default else "[y/N]"
    ans = input(f"{question} {hint} ").strip().lower()
    return default if not ans else ans.startswith("y")


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], **kw).returncode


def vpy(*args, **kw):
    return run([VENV_PY, *args], **kw)


def winget(package_id, extra=()):
    if not shutil.which("winget"):
        say("  winget is not available on this computer; install it from the Microsoft Store (App Installer).")
        return False
    return run(["winget", "install", "-e", "--id", package_id, *extra]) == 0


def venv_python_version():
    """major.minor of the Python the existing .venv was built with, or None."""
    cfg = ROOT / ".venv" / "pyvenv.cfg"
    if not cfg.exists():
        return None
    for line in cfg.read_text(encoding="utf-8").splitlines():
        key, _, val = line.partition("=")
        if key.strip() in ("version", "version_info"):
            return ".".join(val.strip().split(".")[:2])
    return None


def step_environment():
    v = sys.version_info
    here = f"{v.major}.{v.minor}"
    say(f"[1/6] Python environment (Python {here})")
    if v < (3, 10):
        sys.exit("  Python 3.10 or newer is required; 3.12 is recommended.")
    built = venv_python_version()
    if built and built != here:
        # an environment built with another Python would keep failing the same way after an upgrade
        say(f"  the .venv folder was built with Python {built}; rebuilding it with Python {here}")
        shutil.rmtree(ROOT / ".venv", ignore_errors=True)
    if not VENV_PY.exists():
        run([sys.executable, "-m", "venv", ROOT / ".venv"], check=False)
    if not VENV_PY.exists():
        sys.exit("  could not create the .venv folder (if it still exists, close other flycns windows and delete it)")
    if subprocess.run([VENV_PY, "-m", "pip", "--version"], capture_output=True).returncode != 0:
        vpy("-m", "ensurepip", "--upgrade")              # an environment made without pip gets it back
    if vpy("-m", "pip", "install", "-q", "--upgrade", "pip") != 0:
        sys.exit("  pip does not work in the .venv folder; delete the folder and run setup.cmd again")
    if v >= (3, 12):
        # ready-made Windows builds only: a missing one fails here, in seconds, with a clear way out,
        # instead of a long compile that needs the C++ Build Tools
        if vpy("-m", "pip", "install", "-q", *WHEELS_ONLY, "-r", "requirements.lock") != 0:
            sys.exit(f"  A pinned package has no ready-made Windows build for Python {here}.\n"
                     "  Install Python 3.12 (winget install -e --id Python.Python.3.12), then run setup.cmd again.")
        say("  reference environment: every package pinned (requirements.lock)")
    else:
        if vpy("-m", "pip", "install", "-q", "-r", "requirements.txt") != 0:
            sys.exit("  package installation failed (requirements.txt); see the messages above")
        say("  NOTE: below Python 3.12 packages are NOT pinned. It works, but for the reference environment\n"
            "        install Python 3.12 and run setup.cmd again (the .venv folder is rebuilt automatically).")
    for d in ("data", "results"):
        (ROOT / d).mkdir(exist_ok=True)


def step_git():
    say("[2/6] git")
    if shutil.which("git"):
        say("  found")
        return
    say("  git is not installed. It is needed so every result can be traced to the exact code.")
    if ask_yes("  Install git now with winget?") and winget("Git.Git"):
        say("  git installed. Close this window, open a new PowerShell in this folder, and run setup.cmd again.")
        sys.exit(1)
    say("  continuing without git: registered tests will refuse to run until git is installed.")


def engine_ok():
    probe = ("import sys\nfrom brian2.codegen.runtime.cython_rt import CythonCodeObject\n"
             "sys.exit(0 if CythonCodeObject.is_available() else 1)")
    return subprocess.run([VENV_PY, "-c", probe], capture_output=True).returncode == 0


def step_engine():
    say("[3/6] simulation engine")
    if engine_ok():
        say("  compiled engine available (a working C++ compiler was found)")
        return
    say("  No C++ compiler: the pure-Python engine will be used. Results are identical, runs are slower.")
    if os.name != "nt":
        say("  For full speed install a C++ compiler: g++ on Linux (e.g. sudo apt install g++), or the Xcode\n"
            "  command line tools on macOS (xcode-select --install); then run scripts/setup.py again.")
        return
    say("  For full speed install the free Microsoft C++ Build Tools (a one-time download of a few GB).")
    if ask_yes("  Install the Build Tools now with winget? (takes 10 to 20 minutes)", default=False):
        ok = winget("Microsoft.VisualStudio.2022.BuildTools",
                    ["--override", "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"])
        say("  installed: the compiled engine is used from the next run" if ok and engine_ok()
            else "  not confirmed yet; restart the computer and run setup.cmd again to check")


def step_check():
    say("[4/6] regression test on the toy graph (no account needed; about 10 to 20 minutes)")
    code = vpy("tests/regression.py")
    say(f"install works. For the real connectome run:  {SETUP}" if code == 0 else
        "the regression test failed: copy the lines above when you ask for help (for example in a GitHub issue)")
    sys.exit(code)


def step_token():
    say("[5/6] neuPrint token")
    if W.neuprint_token():
        where = "the NEUPRINT_TOKEN environment variable" if os.environ.get("NEUPRINT_TOKEN", "").strip() else W.TOKEN_FILE
        say(f"  found ({where})")
        if W.TOKEN_FILE.exists():
            ok, why = W.restrict_token_file()     # a file saved before this check existed may be readable by others
            if not ok:
                say(f"  WARNING: could not restrict {W.TOKEN_FILE} to your user only: {why}")
        return
    if QUIET:
        sys.exit(f"  no token at {W.TOKEN_FILE}; run {SETUP} once by hand to save it")
    say("  The connectome is downloaded from neuPrint, which needs a free personal token:")
    say("    1. open https://neuprint.janelia.org and log in with Google")
    say("    2. click your account (top right), then Account, and copy the token")
    import getpass
    tok = getpass.getpass("  paste the token here (it will not be shown) and press Enter: ")
    if len("".join(tok.split())) < 40:
        sys.exit(f"  that does not look like a token; run {SETUP} again")
    say(f"  saved to {W.save_token(tok)}")


def data_pinned():
    """True if the connectome is present and matches the committed fingerprint: nothing to fetch, and
    no reason to rewrite the tables (an annotation refresh would overwrite them before checking)."""
    have = all((ROOT / "data" / n).exists() for n in ("neurons.parquet", "edges.parquet"))
    return have and (ROOT / "data/MANIFEST.json").exists() and \
        subprocess.run([VENV_PY, "-m", "flycns.integrity", "verify", "data"], capture_output=True).returncode == 0


def step_data():
    W.load_token_into_env()
    say("[6/6] connectome, annotations and fingerprint")
    manifest = (ROOT / "data/MANIFEST.json").exists()
    present = (ROOT / "data/neurons.parquet").exists() and (ROOT / "data/edges.parquet").exists()
    if present and manifest:
        # present but not matching: never refetch over it; say what differs and stop
        vpy("-m", "flycns.integrity", "verify", "data")
        sys.exit("  The tables here differ from the ones the committed results were produced on (see above).\n"
                 "  Registered tests refuse to run until this is resolved. Copy the lines above when you ask for help.")
    if not present and vpy("scripts/fetch_malecns.py") != 0:
        sys.exit("  the connectome download failed; see above")
    for script in ("scripts/fetch_annotations.py", "scripts/fetch_dimorphism.py", "fit/roi_membership.py"):
        if vpy(script) != 0:
            sys.exit(f"  {script} failed; see above")
    if vpy("fit/audit_stimuli.py", "data") != 0:
        sys.exit("  the stimulus audit failed; see above")
    if manifest:
        if vpy("-m", "flycns.integrity", "verify", "data") != 0:
            sys.exit("  The downloaded tables differ from the ones the committed results were produced on.\n"
                     "  Registered tests refuse to run until this is resolved; most likely neuPrint updated the\n"
                     "  dataset. Keep the lines above and change nothing until the difference is understood.")
    else:
        vpy("-m", "flycns.integrity", "write", "data")
        say("  first fetch on this checkout: the fingerprint above now pins these tables")
    say(f"\nready. Run  {MENU}  for the menu.")


if __name__ == "__main__":
    step_environment()
    step_git()
    step_engine()
    if "--check" in ARGS:
        step_check()
    if data_pinned():
        say("[5/6] data: present and matching data\\MANIFEST.json, nothing to fetch")
        if not (ROOT / "data/roi_membership.parquet").exists():
            say("  NOTE: no data\\roi_membership.parquet, so the SEZ is defined by cell-type name, not anatomy.\n"
                "        The committed results use the anatomical SEZ: run menu 25 once to match them.")
        say(f"\nready. Run  {MENU}  for the menu.")
        sys.exit(0)
    step_token()
    step_data()
