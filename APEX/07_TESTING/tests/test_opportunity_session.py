#!/usr/bin/env python3
"""Smoke tests for the opportunity_session scoring pipeline."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents import opportunity_analyst
from governance.gatekeeper import enforce_claims_safety
from runner import opportunity_session

DATA_PATH = ROOT / "vault" / "business_opportunities.json"


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_opportunities_load_and_score():
    opportunities = opportunity_analyst.load_opportunities(str(DATA_PATH))
    ranked = opportunity_analyst.rank_opportunities(opportunities)

    assert_true(len(ranked) == len(opportunities["business_opportunities"]),
                "ranking must include every opportunity")
    scores = [op["match_score"] for op in ranked]
    assert_true(scores == sorted(scores, reverse=True), "opportunities must be sorted by match_score desc")
    assert_true(all(0 <= s <= 100 for s in scores), "match_score must be within 0-100")


def test_zero_effort_option_scores_well_on_effort_axis():
    opportunities = opportunity_analyst.load_opportunities(str(DATA_PATH))
    idle = next(op for op in opportunities["business_opportunities"] if op["id"] == "idle-asset-monetization")
    assert_true(idle["effort_score"] == 1, "idle asset monetization should be the lowest-effort baseline")


def test_educational_tracks_present():
    opportunities = opportunity_analyst.load_opportunities(str(DATA_PATH))
    tracks = opportunity_analyst.educational_tracks(opportunities)
    assert_true(len(tracks) >= 3, "educational tracks should offer several adjacent skill areas")
    for track in tracks:
        assert_true(track["resources"], f"educational track {track['id']} must list resources")


def test_report_passes_claims_safety_gate():
    report = opportunity_session.run_opportunity_session()
    assert_true("Top Match" in report, "report must surface a top match section")
    violations = enforce_claims_safety(report)
    assert_true(violations == [], f"generated report must not contain overpromising claims: {violations}")


if __name__ == "__main__":
    test_opportunities_load_and_score()
    test_zero_effort_option_scores_well_on_effort_axis()
    test_educational_tracks_present()
    test_report_passes_claims_safety_gate()
    print("PASS: opportunity_session smoke tests")
