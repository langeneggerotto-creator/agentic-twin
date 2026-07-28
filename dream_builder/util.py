import json
import re


def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in model output:\n{text}")
    return json.loads(match.group(0))


def extract_json_object(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output:\n{text}")
    return json.loads(match.group(0))


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "project"


def as_text(value):
    """LLMs occasionally ignore a "must be a plain string" instruction and
    return a nested object/list instead — flatten it into something
    readable rather than showing raw Python repr."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "; ".join(f"{k}: {as_text(v)}" for k, v in value.items())
    if isinstance(value, list):
        return "; ".join(as_text(v) for v in value)
    return str(value)


def plan_summary(dream):
    plan = dream.get("plan") or []
    if not plan:
        return "(no plan yet)"
    return "\n".join(f"- {s['step']}" for s in plan)


def resource_summary(dream):
    resources = dream.get("resources") or []
    if not resources:
        return "(no resources gathered yet — estimate from general knowledge)"
    return "\n".join(f"- {r['resource']}: {r['recommendation']}" for r in resources)
