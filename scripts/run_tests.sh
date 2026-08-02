#!/usr/bin/env bash
# The single canonical way to test the MVP -- run this locally, and CI
# (.github/workflows/twin.yml) runs the exact same list. No API keys or
# hardware required: every test here is a pure-function test or a scripted
# integration test against a real isolated temp git repo.
#
# This deliberately lists files by name rather than globbing
# APEX/07_TESTING/tests/*.py: that directory also holds pre-existing,
# unrelated APEX prototype tests (test_python_intent_v03.py,
# test_python_intent_v04.py, test_ras2_adapter_v01.py) with a known,
# pre-existing dataclass-loading bug unrelated to anything below. Globbing
# would make this suite red for reasons that have nothing to do with the
# MVP. If you fix that bug, add those files back explicitly -- don't switch
# this back to a glob.
set -u

TESTS=(
  APEX/07_TESTING/tests/test_contract_gate.py
  APEX/07_TESTING/tests/test_approvals.py
  APEX/07_TESTING/tests/test_evidence_ledger.py
  APEX/07_TESTING/tests/test_report.py
  APEX/07_TESTING/tests/test_apex_bridge.py
  APEX/07_TESTING/tests/test_dream_builder.py
  APEX/07_TESTING/tests/test_claude_code_delegate.py
  APEX/07_TESTING/tests/test_claude_code_delegate_integration.py
  APEX/07_TESTING/tests/test_openai_provider.py
  APEX/07_TESTING/tests/test_openai_provider_integration.py
  APEX/07_TESTING/tests/test_provider_router.py
  APEX/07_TESTING/tests/test_jetson_edge_node.py
  APEX/07_TESTING/tests/test_gpio_safety.py
  APEX/07_TESTING/tests/test_opportunity_session.py
)

fail=0
for f in "${TESTS[@]}"; do
  echo "=== $f ==="
  python3 "$f" || fail=1
done

echo ""
if [ "$fail" -eq 0 ]; then
  echo "ALL PASS (${#TESTS[@]} suites)"
else
  echo "FAILED -- see above"
fi
exit $fail
