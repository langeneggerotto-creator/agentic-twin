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


def chat_json_array(chat_fn, messages):
    """Call chat_fn(messages) and parse a JSON array from the result,
    retrying once on failure. The model occasionally returns malformed
    JSON or an outright refusal ("I can't help with this request.")
    instead of the requested array — one retry clears most transient
    cases; a real refusal still propagates as ValueError so callers (and
    the web/CLI error handlers) can surface it clearly instead of it
    failing silently or crashing uninformatively."""
    raw = chat_fn(messages)
    try:
        return extract_json_array(raw)
    except ValueError:
        raw = chat_fn(messages)
        return extract_json_array(raw)


def chat_json_object(chat_fn, messages):
    """Object-returning counterpart to chat_json_array — see its docstring."""
    raw = chat_fn(messages)
    try:
        return extract_json_object(raw)
    except ValueError:
        raw = chat_fn(messages)
        return extract_json_object(raw)


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
