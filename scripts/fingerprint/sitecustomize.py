"""
Spike fingerprints for the identity check (scripts/fingerprint.py). Loaded by Python at start-up only when this
folder is on PYTHONPATH and FPRINT_LOG names a file; otherwise it does nothing.

It wraps flycns.model.CNSModel from outside the model files (so it works on any generation and adding it changes
no registered file) and appends one JSON line per event to FPRINT_LOG:
  net   when a model is built: a hash of every object's full state (neurons, synapses with their weights and
        delays, stimulus sources, monitors), i.e. the network as wired
  run   after every CNSModel.run(): a hash of every neuron group's state (membrane, synaptic and adaptation
        variables, refractory state), of the stimulus sources, of the voltage monitors, and a running hash of
        every spike (which neuron, at which time step)
It only reads state; it draws no random numbers and changes nothing the simulation computes.
"""
import os

_LOG = os.environ.get("FPRINT_LOG")


def _install():
    import hashlib
    import importlib.abc
    import json
    import sys

    seq = {"call": 0, "model": 0}

    def _h(*arrays):
        import numpy as np
        h = hashlib.sha256()
        for name, a in arrays:
            a = np.ascontiguousarray(np.asarray(a))
            h.update(f"{name}|{a.dtype}|{a.shape}|".encode())
            h.update(a.tobytes())
        return h.hexdigest()[:32]

    def _states(obj):
        st = obj.get_states(units=False, format="dict", read_only_variables=True)
        return [(f"{obj.name}.{k}", st[k]) for k in sorted(st)]

    def _write(rec):
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    def _patch(mod):
        from brian2 import NeuronGroup, PoissonGroup, StateMonitor
        _write(dict(kind="proc", argv=[os.path.basename(sys.argv[0])] + sys.argv[1:] if sys.argv else [],
                    env={k: v for k, v in sorted(os.environ.items()) if k.startswith("FLYCNS_")}))
        cls = mod.CNSModel
        init, run = cls.__init__, cls.run

        def __init__(self, *a, **k):
            init(self, *a, **k)
            seq["model"] += 1
            self._fp_model, self._fp_n, self._fp_spk = seq["model"], 0, ""
            objs = sorted(self.net.objects, key=lambda o: o.name)
            parts = [p for o in objs for p in _states(o)]
            _write(dict(kind="net", model=self._fp_model, seq=seq["call"], n_objects=len(objs),
                        objects=[f"{type(o).__name__}:{o.name}" for o in objs], h=_h(*parts)))

        def run_(self, duration_ms):
            run(self, duration_ms)
            seq["call"] += 1
            import numpy as np
            i, t = np.asarray(self.spikes.i[:]), np.asarray(self.spikes.t_[:])
            n = len(i)
            if n < self._fp_n:                       # restored to an earlier state: hash from the start
                self._fp_n, self._fp_spk = 0, ""
            new = _h(("prev", np.frombuffer(self._fp_spk.encode(), dtype=np.uint8)),
                     ("i", i[self._fp_n:n]), ("t", t[self._fp_n:n]))
            self._fp_n, self._fp_spk = n, new
            dyn = sorted((o for o in self.net.objects if isinstance(o, (NeuronGroup, PoissonGroup, StateMonitor))),
                         key=lambda o: o.name)
            _write(dict(kind="run", model=self._fp_model, seq=seq["call"], dur=float(duration_ms),
                        t_ms=round(float(self.net.t_ * 1000), 6), n_spikes=n, spikes=new,
                        state=_h(*[p for o in dyn for p in _states(o)])))

        cls.__init__, cls.run = __init__, run_

    class _Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path, target=None):
            if name != "flycns.model":
                return None
            for f in sys.meta_path:
                if f is self or not hasattr(f, "find_spec"):
                    continue
                spec = f.find_spec(name, path, target)
                if spec is not None:
                    break
            else:
                return None
            orig = spec.loader.exec_module

            def exec_module(module, _orig=orig):
                _orig(module)
                _patch(module)
            spec.loader.exec_module = exec_module
            return spec

    sys.meta_path.insert(0, _Finder())


if _LOG:
    _install()
