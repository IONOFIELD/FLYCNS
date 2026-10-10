"""
Windows platform layer. flycns runs on Windows; this module is the one place that knows it.

  console()            UTF-8 output and colour in the Windows console, also when output is piped
  codegen_target()     the simulation engine: compiled ("cython", needs the free Microsoft C++
                       Build Tools) when a compiler works, else pure-Python ("numpy", slower,
                       same equations). FLYCNS_CODEGEN=cython|numpy forces one.
  neuprint_token()     the neuPrint token from NEUPRINT_TOKEN or %USERPROFILE%\\.neuprint_token,
                       read robustly (a file written by PowerShell's `echo > file` is UTF-16)
  keep_awake()         stop Windows sleeping during a long run (released when the process exits)
  open_path(p)         open a file or URL with its default Windows app
  unencoded_text_io()  finds text file I/O without an explicit encoding (used by the tests: on
                       Windows such I/O defaults to cp1252 and breaks on characters like é or —)
"""
import ast
import os
import sys
from pathlib import Path

TOKEN_FILE = Path.home() / ".neuprint_token"
_DONE = {}


def console():
    """Make stdout/stderr UTF-8 (with replacement, never crashing on a glyph) and enable ANSI
    colour in the Windows console. Child processes inherit UTF-8 mode. Idempotent."""
    if _DONE.get("console"):
        return
    _DONE["console"] = True
    os.environ.setdefault("PYTHONUTF8", "1")        # children start in UTF-8 mode
    for stream in (sys.stdout, sys.stderr):
        try:
            if (stream.encoding or "").lower().replace("-", "") != "utf8":
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if os.name == "nt":
        try:   # ENABLE_VIRTUAL_TERMINAL_PROCESSING so \033[...m colour codes render
            import ctypes
            k32 = ctypes.windll.kernel32
            for handle_id in (-11, -12):            # stdout, stderr
                h = k32.GetStdHandle(handle_id)
                mode = ctypes.c_uint32()
                if k32.GetConsoleMode(h, ctypes.byref(mode)):
                    k32.SetConsoleMode(h, mode.value | 0x0004)
        except Exception:
            pass


def codegen_target():
    """'cython' (compiled, fast) if a C++ compiler works, else 'numpy' (pure Python, slower).
    Both run the same equations; tests/unit.py checks they give identical spikes."""
    if "codegen" in _DONE:
        return _DONE["codegen"]
    forced = os.environ.get("FLYCNS_CODEGEN", "").strip().lower()
    if forced in ("cython", "numpy"):
        target = forced
    else:
        try:
            from brian2.codegen.runtime.cython_rt import CythonCodeObject
            target = "cython" if CythonCodeObject.is_available() else "numpy"
        except Exception:
            target = "numpy"
        if target == "numpy":
            print("[engine] no working C++ compiler found: using the pure-Python engine (same results, slower).\n"
                  "         For full speed install the free Microsoft C++ Build Tools: run setup.cmd again.",
                  file=sys.stderr, flush=True)
    _DONE["codegen"] = target
    return target


def neuprint_token():
    """Token from NEUPRINT_TOKEN, else from the token file. Handles UTF-8, UTF-8 with BOM and the
    UTF-16 that PowerShell 5's `echo x > file` writes. Returns '' if none."""
    tok = os.environ.get("NEUPRINT_TOKEN", "").strip()
    if tok:
        return tok
    if not TOKEN_FILE.exists():
        return ""
    raw = TOKEN_FILE.read_bytes()
    for enc in ("utf-16", "utf-8-sig") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else ("utf-8-sig", "utf-16"):
        try:
            return "".join(raw.decode(enc).split())
        except UnicodeDecodeError:
            continue
    return ""


def save_token(token):
    TOKEN_FILE.write_text("".join(token.split()), encoding="utf-8")
    return TOKEN_FILE


def load_token_into_env():
    """So every child process (the fetch scripts) sees the token without the user exporting it."""
    tok = neuprint_token()
    if tok:
        os.environ["NEUPRINT_TOKEN"] = tok
    return bool(tok)


def keep_awake():
    """Ask Windows not to sleep while this process runs (ES_CONTINUOUS | ES_SYSTEM_REQUIRED).
    Released automatically when the process exits. No-op elsewhere."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001))
    except Exception:
        return False


def open_path(target):
    """Open a file with its default Windows app, or a URL in the default browser."""
    target = str(target)
    if target.startswith(("http://", "https://")):
        import webbrowser
        webbrowser.open(target)
    elif os.name == "nt":
        os.startfile(target)                        # noqa: S606  (Windows only)
    else:
        import webbrowser
        webbrowser.open(Path(target).resolve().as_uri())


def open_text(path):
    """Open a text or Markdown file for reading: Notepad on Windows, which always exists."""
    if os.name == "nt":
        import subprocess
        subprocess.Popen(["notepad.exe", str(path)])
    else:
        open_path(path)


def _binary_mode(node):
    """True if an open() mode is certainly binary: a constant with 'b', or a conditional whose
    branches are both binary ("ab" if resume else "wb")."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and "b" in node.value
    if isinstance(node, ast.IfExp):
        return _binary_mode(node.body) and _binary_mode(node.orelse)
    return False


def unencoded_text_io(source):
    """(end_line, end_col_byte, has_args) for every text-mode read_text/write_text/open call
    in `source` with no encoding= argument."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or any(k.arg == "encoding" for k in node.keywords):
            continue
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in ("read_text", "write_text"):
            pass                                                    # always text mode
        elif isinstance(f, ast.Name) and f.id == "open":            # builtin open(path, mode)
            mode = node.args[1] if len(node.args) >= 2 else next(
                (k.value for k in node.keywords if k.arg == "mode"), None)
            if _binary_mode(mode):
                continue                                            # binary: no encoding
        else:
            continue
        hits.append((node.end_lineno, node.end_col_offset, bool(node.args or node.keywords)))
    return hits
