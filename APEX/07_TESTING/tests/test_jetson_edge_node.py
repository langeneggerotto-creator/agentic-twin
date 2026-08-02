#!/usr/bin/env python3
"""Smoke tests for runner.jetson_edge_node and runner.dream_queue_worker --
the file-based queue connecting the Jetson-side monitor to the
control-plane-side router. No real API calls in either half."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.dream_queue_worker import list_pending
from runner.jetson_edge_node import check_service, monitor_and_queue, queue_dream


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_check_service_on_a_nonexistent_unit_is_unknown_not_a_crash():
    status = check_service("definitely-not-a-real-service-xyz")
    assert_true(status in ("unknown", "inactive", "failed"),
                f"a nonexistent unit must resolve to a status string, not raise; got {status!r}")


def test_monitor_and_queue_writes_a_dream_for_an_unhealthy_service():
    with tempfile.TemporaryDirectory() as tmp:
        queued = monitor_and_queue(
            ["definitely-not-a-real-service-xyz"],
            allowed_paths=["src/camera/**"],
            allowed_commands=["systemctl restart definitely-not-a-real-service-xyz"],
            queue_dir=tmp,
        )
        assert_true(len(queued) == 1, "an unhealthy/unknown service must produce exactly one queued dream")
        contract = json.loads(queued[0].read_text())
        assert_true("definitely-not-a-real-service-xyz" in contract["goal"],
                    "the queued dream's goal must name the service it's repairing")
        assert_true(contract["allowed_paths"] == ["src/camera/**"],
                    "the queued dream must carry the scope the monitor was configured with")


def test_dream_queue_worker_sees_what_the_edge_node_queued():
    with tempfile.TemporaryDirectory() as tmp:
        monitor_and_queue(
            ["another-fake-service"], ["src/**"], ["true"], queue_dir=tmp,
        )
        pending = list_pending(tmp)
        assert_true(len(pending) == 1, "the queue worker must see exactly what the edge node wrote")


def test_queue_dream_creates_a_uniquely_named_file():
    with tempfile.TemporaryDirectory() as tmp:
        contract = {"goal": "test dream"}
        path1 = queue_dream(contract, queue_dir=tmp)
        path2 = queue_dream(contract, queue_dir=tmp)
        assert_true(path1 != path2, "two dreams queued in quick succession must not collide on filename")
        assert_true(len(list(Path(tmp).glob("*.json"))) == 2, "both queued files must be present")


if __name__ == "__main__":
    test_check_service_on_a_nonexistent_unit_is_unknown_not_a_crash()
    test_monitor_and_queue_writes_a_dream_for_an_unhealthy_service()
    test_dream_queue_worker_sees_what_the_edge_node_queued()
    test_queue_dream_creates_a_uniquely_named_file()
    print("PASS: jetson_edge_node / dream_queue_worker smoke tests")
