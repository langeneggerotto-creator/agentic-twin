#!/usr/bin/env bash
# PostToolUse hook: after Write/Edit touches dream_builder/*.py, run its
# test suite and report pass/fail back into the session automatically.
set -euo pipefail

input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty')

case "$file_path" in
  */dream_builder/*.py|dream_builder/*.py)
    ;;
  *)
    exit 0
    ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}"

if output=$(python -m pytest dream_builder/tests -q 2>&1); then
  status="PASS"
else
  status="FAIL"
fi

summary="dream_builder tests: $status ($file_path)"

jq -n \
  --arg msg "$summary" \
  --arg out "$output" \
  '{
    systemMessage: $msg,
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: ($msg + "\n" + $out)
    }
  }'
