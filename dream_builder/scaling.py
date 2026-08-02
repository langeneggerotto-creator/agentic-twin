from . import store
from .llm_client import chat
from .util import as_text, chat_json_object, plan_summary, resource_summary

SCALING_SYSTEM_PROMPT = (
    "You help someone think through how to fund and scale their goal — "
    "whether it's a money-making venture, a product, a service, a charity, "
    "or an outreach effort. Given the goal, its plan, resources, and any "
    "existing cost projection, produce two things: how to realistically "
    "fund getting it off the ground with little or no capital (whichever "
    "of bootstrapping, pre-sales, grants, crowdfunding, sweat equity, or "
    "revenue-first actually fits this specific goal — not a generic list "
    "of all of them), and a realistic path to grow it from working for one "
    "person to working at real scale. "
    "If this goal is a personal or individual pursuit that doesn't "
    "actually need funding or scaling in the business sense (e.g. a "
    "personal skill, health, or hobby goal), say that plainly instead of "
    "forcing a business framing onto it — do not invent a funding need "
    "that isn't real. Be specific to this goal, not generic startup "
    "advice. "
    "scaling_lead_measures are actions the person takes and controls "
    "regularly that predict growth (outreach conversations had, "
    "partnerships pitched, content published) — never costs or expenses. "
    "scaling_lag_measures are the actual growth outcomes those actions "
    "produce (paying customers, active users, revenue, people helped) — "
    "also never costs or expenses. Costs belong only in funding_strategy "
    "or funding_milestones, nowhere else.\n\n"
    "Respond with ONLY a JSON object, no other text, in this exact shape:\n"
    '{"funding_strategy": "...", "scaling_strategy": "...", '
    '"funding_milestones": ["..."], "scaling_lead_measures": ["..."], '
    '"scaling_lag_measures": ["..."]}'
)


def plan_scaling(dream):
    projection = dream.get("projection")
    projection_summary = (
        f"Time: {projection['time_estimate']}; Cost: {projection['cost_estimate']}"
        if projection
        else "(no projection yet)"
    )
    messages = [
        {"role": "system", "content": SCALING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Goal: {dream['title']}\nDetails: {dream['description']}\n\n"
                f"Plan:\n{plan_summary(dream)}\n\n"
                f"Resources found so far:\n{resource_summary(dream)}\n\n"
                f"Existing time/cost projection: {projection_summary}"
            ),
        },
    ]
    data = chat_json_object(chat, messages)
    scaling = {
        "funding_strategy": as_text(data.get("funding_strategy", "")),
        "scaling_strategy": as_text(data.get("scaling_strategy", "")),
        "funding_milestones": [as_text(m) for m in (data.get("funding_milestones") or [])],
        "scaling_lead_measures": [as_text(m) for m in (data.get("scaling_lead_measures") or [])],
        "scaling_lag_measures": [as_text(m) for m in (data.get("scaling_lag_measures") or [])],
        "generated_at": store.now(),
    }
    dream["scaling"] = scaling
    store.update_dream(dream)
    return scaling
