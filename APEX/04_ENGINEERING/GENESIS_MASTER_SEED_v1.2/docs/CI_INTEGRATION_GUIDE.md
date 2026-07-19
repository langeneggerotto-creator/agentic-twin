# APEX Purpose Gate CI Integration Guide v1.2

Run:

```bash
python runtime/purpose_gate_validator.py <module_contract.json>
```

Fail CI when the validator returns `BLOCK`.

## Draft PR Boundary

The workflow can validate a draft PR. It cannot approve, merge, release, deploy, or authorize physical action.
