#!/usr/bin/env python3
"""Smoke tests for governance.evidence_ledger, the append-only APEX Evidence
Ledger referenced in CORE_OS_INHERITANCE.md."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.evidence_ledger import read_ledger, record_evidence


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_record_and_read_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = str(Path(tmp) / "evidence_ledger.jsonl")

        record_evidence({"goal": "repair camera service", "gate_passed": True}, ledger_path)
        record_evidence({"goal": "repair camera service, take two", "gate_passed": False}, ledger_path)

        entries = read_ledger(ledger_path)
        assert_true(len(entries) == 2, "both records must be present")
        assert_true(entries[0]["goal"] == "repair camera service", "entries must preserve order")
        assert_true("recorded_at" in entries[0], "every entry must carry a timestamp")


def test_ledger_is_append_only():
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = str(Path(tmp) / "evidence_ledger.jsonl")

        record_evidence({"goal": "first"}, ledger_path)
        first_pass_entries = read_ledger(ledger_path)
        record_evidence({"goal": "second"}, ledger_path)
        second_pass_entries = read_ledger(ledger_path)

        assert_true(len(first_pass_entries) == 1, "first record must be readable immediately")
        assert_true(len(second_pass_entries) == 2, "second record must be appended, not overwrite the first")
        assert_true(second_pass_entries[0]["goal"] == "first", "prior entries must never be mutated")


def test_read_missing_ledger_returns_empty_list():
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = str(Path(tmp) / "does_not_exist.jsonl")
        assert_true(read_ledger(ledger_path) == [], "a missing ledger must read as empty, not error")


if __name__ == "__main__":
    test_record_and_read_round_trip()
    test_ledger_is_append_only()
    test_read_missing_ledger_returns_empty_list()
    print("PASS: evidence_ledger smoke tests")
