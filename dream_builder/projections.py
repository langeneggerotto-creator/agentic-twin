from . import store
from .llm_client import chat
from .util import as_text, extract_json_object, plan_summary, resource_summary

PROJECTION_SYSTEM_PROMPT = (
    "You are a practical estimator and metrics coach. Given a person's goal, "
    "their plan, and any resources/costs already found for it, produce a "
    "realistic time and cost projection, plus lead and lag measures to "
    "track progress. State the assumptions behind your estimates plainly "
    "(e.g. hours per week assumed) rather than hiding them — ranges are "
    "fine and expected, this is an estimate, not a promise. "
    "Lead measures are things the person directly controls day-to-day that "
    "predict progress (frequency of an input behavior); lag measures are "
    "the outcomes that confirm the goal is actually being reached. Be "
    "specific to this goal, not generic productivity advice. "
    "time_estimate and cost_estimate must each be a single plain string "
    "(e.g. a range with the assumption baked in), never a nested object.\n\n"
    "Respond with ONLY a JSON object, no other text, in this exact shape:\n"
    '{"time_estimate": "...", "cost_estimate": "...", '
    '"lead_measures": ["..."], "lag_measures": ["..."]}'
)


def project_dream(dream):
    messages = [
        {"role": "system", "content": PROJECTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Goal: {dream['title']}\nDetails: {dream['description']}\n\n"
                f"Plan:\n{plan_summary(dream)}\n\n"
                f"Resources found so far:\n{resource_summary(dream)}"
            ),
        },
    ]
    raw = chat(messages)
    try:
        data = extract_json_object(raw)
    except ValueError:
        # LLM output is occasionally malformed JSON; one retry clears most
        # of those without making callers deal with the failure themselves.
        raw = chat(messages)
        data = extract_json_object(raw)
    projection = {
        "time_estimate": as_text(data.get("time_estimate", "")),
        "cost_estimate": as_text(data.get("cost_estimate", "")),
        "lead_measures": [as_text(m) for m in (data.get("lead_measures") or [])],
        "lag_measures": [as_text(m) for m in (data.get("lag_measures") or [])],
        "generated_at": store.now(),
    }
    dream["projection"] = projection
    store.update_dream(dream)
    return projection
