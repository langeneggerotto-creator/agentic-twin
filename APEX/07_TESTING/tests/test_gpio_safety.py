#!/usr/bin/env python3
"""Smoke tests for hardware.gpio_safety -- the simulated-by-default actuator
interface for the Jetson edge node."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hardware.gpio_safety import ApprovalRequiredError, PinState, emergency_stop, set_pin


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_set_pin_denied_without_hardware_control_approval():
    threw = False
    try:
        set_pin(17, True, approved_actions=set())
    except ApprovalRequiredError:
        threw = True
    assert_true(threw, "set_pin must refuse to act without hardware_control approval")


def test_set_pin_denied_with_unrelated_approvals():
    threw = False
    try:
        set_pin(17, True, approved_actions={"production_deployment"})
    except ApprovalRequiredError:
        threw = True
    assert_true(threw, "an unrelated approval must not unlock hardware actuation")


def test_set_pin_succeeds_when_approved():
    state = PinState()
    result = set_pin(17, True, approved_actions={"hardware_control"}, pin_state=state)
    assert_true(result["pin"] == 17 and result["state"] is True, "approved set_pin must report what it did")
    assert_true(state.active_pins[17] is True, "the pin must be tracked as active")


def test_no_real_hardware_is_ever_claimed_in_this_environment():
    state = PinState()
    result = set_pin(17, True, approved_actions={"hardware_control"}, pin_state=state)
    assert_true(result["truth_status"] == "SIMULATED_NO_HARDWARE_PRESENT",
                "without a real Jetson.GPIO import, the result must never claim to be real hardware")


def test_emergency_stop_works_without_any_approval():
    state = PinState()
    set_pin(17, True, approved_actions={"hardware_control"}, pin_state=state)
    result = emergency_stop(state)
    assert_true(result["released_pins"] == [17], "emergency_stop must release every tracked pin")
    assert_true(state.active_pins[17] is False, "the pin must be marked inactive after stop")


if __name__ == "__main__":
    test_set_pin_denied_without_hardware_control_approval()
    test_set_pin_denied_with_unrelated_approvals()
    test_set_pin_succeeds_when_approved()
    test_no_real_hardware_is_ever_claimed_in_this_environment()
    test_emergency_stop_works_without_any_approval()
    print("PASS: gpio_safety smoke tests")
