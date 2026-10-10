"""
flycns setup (Windows). Started by setup.cmd; safe to run again at any time.

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
  6. the connectome (skipped if already present), annotations, the stimulus audit, and the data
     fingerprint: written to data\\MANIFEST.json the first time, verified every time after
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


def step_environment():
    v = sys.version_info
    say(f"[1/6] Python environment (Python {v.major}.{v.minor})")
    if v < (3, 10):
        sys.exit("  Python 3.10 or newer is required; 3.12 is recommended.")
    if not VENV_PY.exists():
        run([sys.executable, "-m", "venv", ROOT / ".venv"], check=False)
    if not VENV_PY.exists():
        sys.exit("  could not create the .venv folder")
    vpy("-m", "pip", "install", "-q", "--upgrade", "pip")
    vinfo = subprocess.run([VENV_PY, "-c", "import sys; print(sys.version_info >= (3, 12))"],
                           capture_output=True, text=True, encoding="utf-8").stdout.strip()
    pinned = vinfo == "True"
    req = "requirements.lock" if pinned else "requirements.txt"
    if vpy("-m", "pip", "install", "-q", "-r", req) != 0:
        sys.exit(f"  package installation failed ({req}); see the messages above")
    if pinned:
        say("  reference environment: every package pinned (requirements.lock)")
    else:
        say("  NOTE: below Python 3.12 packages are NOT pinned. It works, but for the reference environment\n"
            "        install Python 3.12, delete the .venv folder, and run setup.cmd again.")
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
        say("  compiled engine available (Microsoft C++ compiler found)")
        return
    say("  No C++ compiler: the pure-Python engine will be used. Results are identical, runs are slower.")
    say("  For full speed install the free Microsoft C++ Build Tools (a one-time download of a few GB).")
    if ask_yes("  Install the Build Tools now with winget? (takes 10 to 20 minutes)", default=False):
        ok = winget("Microsoft.VisualStudio.2022.BuildTools",
                    ["--override", "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"])
        say("  installed: the compiled engine is used from the next run" if ok and engine_ok()
            else "  not confirmed yet; restart the computer and run setup.cmd again to check")


def step_check():
    say("[4/6] regression test on the toy graph (no account needed; about 10 to 20 minutes)")
    code = vpy("tests/regression.py")
    say("install works. For the real connectome run:  .\\setup.cmd" if code == 0 else
        "the regression test failed: send Claude the lines above")
    sys.exit(code)


def step_token():
    say("[5/6] neuPrint token")
    if W.neuprint_token():
        say(f"  found ({W.TOKEN_FILE})")
        return
    if QUIET:
        sys.exit(f"  no token at {W.TOKEN_FILE}; run .\\setup.cmd once by hand to save it")
    say("  The connectome is downloaded from neuPrint, which needs a free personal token:")
    say("    1. open https://neuprint.janelia.org and log in with Google")
    say("    2. click your account (top right), then Account, and copy the token")
    import getpass
    tok = getpass.getpass("  paste the token here (it will not be shown) and press Enter: ")
    if len("".join(tok.split())) < 40:
        sys.exit("  that does not look like a token; run setup.cmd again")
    say(f"  saved to {W.save_token(tok)}")


def step_data():
    W.load_token_into_env()
    say("[6/6] connectome, annotations and fingerprint")
    if (ROOT / "data/neurons.parquet").exists() and (ROOT / "data/edges.parquet").exists():
        say("  connectome already present, skipping the download")
    elif vpy("scripts/fetch_malecns.py") != 0:
        sys.exit("  the connectome download failed; see above")
    for script in ("scripts/fetch_annotations.py", "scripts/fetch_dimorphism.py"):
        if vpy(script) != 0:
            sys.exit(f"  {script} failed; see above")
    if vpy("fit/audit_stimuli.py", "data") != 0:
        sys.exit("  the stimulus audit failed; see above")
    if (ROOT / "data/MANIFEST.json").exists():
        if vpy("-m", "flycns.integrity", "verify", "data") != 0:
            sys.exit("  The downloaded tables differ from the ones the committed results were produced on.\n"
                     "  Registered tests refuse to run until this is resolved; most likely neuPrint updated the\n"
                     "  dataset. Review what changed before rewriting the manifest.")
    else:
        vpy("-m", "flycns.integrity", "write", "data")
        say("  first fetch on this checkout: the fingerprint above now pins these tables")
    say("\nready. Run  .\\fly.cmd  for the menu.")


if __name__ == "__main__":
    step_environment()
    step_git()
    step_engine()
    if "--check" in ARGS:
        step_check()
    step_token()
    step_data()
