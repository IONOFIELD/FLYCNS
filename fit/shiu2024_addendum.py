"""
Phase-1 addendum (Gen 5), registered 12 October 2026 before any A1 or M1 code or data exists. It adds two
settings the phase-1 pre-registration (results/shiu2024_a0/, preregistered_phase1) left open. That
registration is not changed; the phase-1 benchmark carries it and this addendum, both unchanged.

1. A1 integration. The phase-1 plan the user approved lists eight Shiu-compatible settings for A1, the eighth
   being exact integration (Brian2 method 'linear', as in Shiu et al.'s model.py). The registered a1_settings
   omitted it (an omission, found before any A1 code existed). A1 therefore uses exact integration. flycns's
   Euler method becomes one more ladder step, Le, reported and not scored like L1-L6; L6 ("all together", every
   setting at its flycns value) includes Euler, since Euler is flycns's value.

2. M1 connection floor. M1 is registered as "MaleCNS under the A1 settings", which include a floor of 1 synapse.
   The MaleCNS data hold no connection below 5 synapses (scripts/fetch_malecns.py asks neuPrint for weight >= 5),
   so M1 runs at a floor of 5, with every other A1 setting (exact integration included). This is a deviation,
   logged in docs/CALIBRATION.md. How it is read: if M1 does not respond, the floor is a candidate cause only if
   L3 (A1 with a floor of 5, on FlyWire) loses MN9; in that case a MaleCNS fetch down to 1 synapse comes first,
   before any conclusion of "wiring or annotation".

3. Stated for completeness (no change): in M1, neurons whose transmitter is unknown keep flycns's handling (their
   outputs are dropped), since the registration names only the amines as excitatory; the number of such neurons
   is reported with M1.

    FLYCNS_REGISTER_ONLY=1 python fit/shiu2024_addendum.py     write the registration (then commit it)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flycns import registry  # noqa: E402

LABEL = "shiu2024_phase1_addendum"

CRITERIA = dict(
    adds_to="results/shiu2024_a0/ preregistered_phase1 (unchanged)",
    a1_integration=dict(value="exact (Brian2 method 'linear', as Shiu et al.'s model.py)",
                        why=("the approved phase-1 plan lists it as A1 setting 8; the registered a1_settings "
                             "omitted it; found before any A1 code existed"),
                        ladder="Le: A1 with Euler integration (flycns's value), reported and not scored; L6 "
                               "(all settings at their flycns values) includes Euler"),
    m1_connection_floor=dict(value=5,
                             why=("the MaleCNS data hold no connection below 5 synapses "
                                  "(scripts/fetch_malecns.py queries weight >= 5)"),
                             other_settings="every other A1 setting, exact integration included",
                             reading=("if M1 does not respond and L3 (A1 at floor 5) loses MN9, a MaleCNS fetch "
                                      "down to 1 synapse comes before any conclusion of 'wiring or annotation'")),
    m1_unknown_transmitter="flycns's handling (outputs dropped); the count of such neurons is reported with M1",
    decision_rule="unchanged",
)

REG = registry.register(LABEL, CRITERIA, scripts=[__file__])     # exits here under FLYCNS_REGISTER_ONLY
