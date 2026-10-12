"""
Input guards for the menu (fly.py), kept here so they can be tested without starting the menu.

  benchmark_script(name)   menu option 5: only a script that exists directly in benchmarks/, named
                           with letters, digits and underscores (no paths, no other folders)
  safe_extract(zip, dest)  menu option 21: unpack a downloaded archive only inside dest; an entry with an
                           absolute path, a drive letter, a '..' step or a link is refused, not unpacked
"""
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def benchmark_script(name, root=ROOT):
    """The path of benchmarks/<name>.py if `name` is a plain benchmark name and that file exists; else None."""
    name = (name or "").strip()
    if name.endswith(".py"):
        name = name[:-3]
    if not _NAME.match(name):
        return None
    p = Path(root) / "benchmarks" / f"{name}.py"
    return p if p.is_file() and p.parent.resolve() == (Path(root) / "benchmarks").resolve() else None


def unsafe_member(info, dest):
    """Why a zip entry may not be unpacked into dest, or None if it may."""
    n = info.filename
    if not n or "\x00" in n:
        return "empty or invalid name"
    if PurePosixPath(n).is_absolute() or PureWindowsPath(n).is_absolute() or PureWindowsPath(n).drive or n.startswith(("/", "\\")):
        return "absolute path"
    parts = re.split(r"[\\/]+", n)
    if any(p == ".." for p in parts):
        return "'..' in path"
    if stat.S_ISLNK(info.external_attr >> 16):
        return "symbolic link"
    target = (Path(dest) / n).resolve()
    if not target.is_relative_to(Path(dest).resolve()):
        return "outside the destination"
    return None


def safe_extract(zip_path, dest):
    """Unpack only the entries that stay inside dest. Returns (n_extracted, [(name, why) refused])."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    refused, n = [], 0
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            why = unsafe_member(info, dest)
            if why:
                refused.append((info.filename, why))
                continue
            z.extract(info, dest)
            n += 1
    return n, refused
