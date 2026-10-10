"""flycns: connectome-constrained LIF simulation of the Drosophila MaleCNS with physiological benchmarks."""
from .windows import console as _console
_console()   # UTF-8 output and colour in the Windows console, before anything prints
from .graph import load_graph, rewire_null, ELECTRICAL_SYNAPSES, SIGN_MAP
from .model import CNSModel, LIFParams
from .protocols import loom_protocol
