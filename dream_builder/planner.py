from . import store
from .llm_client import chat
from .util import extract_json_array

PLAN_SYSTEM_PROMPT = (
    "You are a practical planning assistant. Given a person's goal, break it "
    "into a concrete, ordered list of action steps that a real person could "
    "actually do. Be specific and realistic — no vague advice like 'believe "
    "in yourself'. If a step genuinely requires looking up current "
    "information (prices, listings, current events, contacts), mark "
    "needs_internet true for that step.\n\n"
    "Respond with ONLY a JSON array, no other text, in this exact shape:\n"
    '[{"step": "...", "needs_internet": false}, ...]'
)


def build_plan(dream):
    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Goal: {dream['title']}\nDetails: {dream['description']}",
        },
    ]
    raw = chat(messages)
    steps = extract_json_array(raw)
    dream["plan"] = [
        {
            "step": s["step"],
            "needs_internet": bool(s.get("needs_internet", False)),
            "done": False,
            "notes": "",
        }
        for s in steps
    ]
    dream["status"] = "in_progress"
    store.update_dream(dream)
    return dream
