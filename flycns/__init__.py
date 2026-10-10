"""flycns: connectome-constrained LIF simulation of the Drosophila MaleCNS with physiological benchmarks.

The public names load on first use (PEP 562), so `import flycns.windows` or `flycns.integrity`
stays light: the launchers and setup never load Brian2, NumPy or pandas into their own process,
which on Windows would lock those libraries' files while setup updates them."""
from .windows import console as _console

_console()   # UTF-8 output and colour in the Windows console, before anything prints

_LAZY = {"load_graph": "graph", "rewire_null": "graph", "ELECTRICAL_SYNAPSES": "graph", "SIGN_MAP": "graph",
         "CNSModel": "model", "LIFParams": "model", "loom_protocol": "protocols"}


def __getattr__(name):
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(f".{_LAZY[name]}", __name__), name)
    raise AttributeError(f"module 'flycns' has no attribute {name!r}")
