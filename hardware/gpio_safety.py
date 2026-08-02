"""Actuator/GPIO interface for the Jetson edge node.

SIMULATED by default. This environment has no physical Jetson attached, so
pretending to drive real GPIO here would violate the Core OS truth
boundary in CORE_OS_INHERITANCE.md: "must not represent [simulation]
outputs as real-world validation unless calibrated and verified against
appropriate external data." Every result this module returns carries an
explicit truth_status so nothing downstream can mistake a simulated pin
write for a real one.

A real backend (Jetson.GPIO) is only ever attempted when that library is
actually importable on the host running this code -- it will not be on
this sandbox, and should only be present when this file is actually
deployed to a Jetson.

set_pin() is gated: hardware_control is both a default forbidden-action
heuristic trigger and a requires_human_approval trigger throughout this
build (governance/gatekeeper.py, agents/dream_builder.py) -- this module
enforces that gate itself, at the point of actuation, rather than trusting
a caller to have already checked. emergency_stop() is deliberately NOT
gated: stopping is always allowed regardless of approval state, only
starting/holding a pin open is restricted.
"""
from dataclasses import dataclass, field

try:
    import Jetson.GPIO as _real_gpio
    HAS_REAL_GPIO = True
except ImportError:
    _real_gpio = None
    HAS_REAL_GPIO = False


class ApprovalRequiredError(PermissionError):
    pass


@dataclass
class PinState:
    active_pins: dict = field(default_factory=dict)  # pin -> bool state


def set_pin(pin: int, state: bool, approved_actions: set, pin_state: PinState = None) -> dict:
    """Set a GPIO pin. Requires "hardware_control" to already be in
    approved_actions (see governance.approvals.approved_actions_for) --
    this is the actuation-time enforcement of the same gate
    enforce_contract applies after the fact to everything else."""
    if "hardware_control" not in (approved_actions or set()):
        raise ApprovalRequiredError(
            "set_pin denied: 'hardware_control' has not been granted -- "
            "see governance/approvals.py grant <contract> hardware_control <approver>"
        )

    pin_state = pin_state if pin_state is not None else PinState()

    if HAS_REAL_GPIO:
        _real_gpio.setup(pin, _real_gpio.OUT)
        _real_gpio.output(pin, _real_gpio.HIGH if state else _real_gpio.LOW)
        truth_status = "OBSERVED_REAL_HARDWARE"
    else:
        truth_status = "SIMULATED_NO_HARDWARE_PRESENT"

    pin_state.active_pins[pin] = state
    return {"pin": pin, "state": state, "truth_status": truth_status}


def emergency_stop(pin_state: PinState) -> dict:
    """Release every tracked pin immediately. Never gated behind approval --
    stopping actuation is always allowed; only starting/holding one open
    requires hardware_control approval via set_pin."""
    released = sorted(pin_state.active_pins)
    for pin in released:
        if HAS_REAL_GPIO:
            _real_gpio.output(pin, _real_gpio.LOW)
        pin_state.active_pins[pin] = False

    return {
        "released_pins": released,
        "truth_status": "OBSERVED_REAL_HARDWARE" if HAS_REAL_GPIO else "SIMULATED_NO_HARDWARE_PRESENT",
    }
