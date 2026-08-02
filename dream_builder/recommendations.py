from . import store
from .llm_client import chat
from .util import as_text, extract_json_array, plan_summary, resource_summary

RECOMMEND_SYSTEM_PROMPT = (
    "You are a decisive practical advisor. Given a person's goal, the "
    "resource hints and resources already found for it, and their current "
    "plan (if any), synthesize everything gathered into exactly 3 distinct, "
    "complete, actionable approaches for reaching this goal. Each approach "
    "needs its own concrete step-by-step plan and a short list of which "
    "gathered resources/hints it relies on. "
    "Make the 3 approaches genuinely different in strategy, not "
    "re-orderings of the same plan — for example one might favor the "
    "cheapest/slowest path and another the fastest/most direct path. "
    "Exactly one of the three must always be a novel approach that "
    "creatively combines or reinterprets the gathered resources/hints in a "
    "way not already suggested elsewhere — mark only that one "
    "is_synthesized: true. Be honest: if the gathered information doesn't "
    "actually support 3 meaningfully different approaches, say so plainly "
    "in the summaries rather than inventing false distinctions.\n\n"
    "Respond with ONLY a JSON array of exactly 3 objects, no other text, "
    "in this exact shape:\n"
    '[{"title": "...", "summary": "...", "is_synthesized": false, '
    '"plan": [{"step": "...", "needs_internet": false}], '
    '"resources_used": ["..."]}]'
)


def _hints_summary(dream):
    hints = dream.get("resource_hints") or []
    if not hints:
        return "(none)"
    return "\n".join(f"- {h}" for h in hints)


def generate_recommendations(dream):
    messages = [
        {"role": "system", "content": RECOMMEND_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Goal: {dream['title']}\nDetails: {dream['description']}\n\n"
                f"Resource hints:\n{_hints_summary(dream)}\n\n"
                f"Resources found so far:\n{resource_summary(dream)}\n\n"
                f"Current plan:\n{plan_summary(dream)}"
            ),
        },
    ]
    raw = chat(messages)
    try:
        data = extract_json_array(raw)
    except ValueError:
        # LLM output is occasionally malformed JSON; one retry clears most
        # of those without making callers deal with the failure themselves.
        raw = chat(messages)
        data = extract_json_array(raw)

    recommendations = []
    for rec in data[:3]:
        recommendations.append(
            {
                "title": as_text(rec.get("title", "")),
                "summary": as_text(rec.get("summary", "")),
                "is_synthesized": bool(rec.get("is_synthesized", False)),
                "plan": [
                    {
                        "step": as_text(s.get("step", "")),
                        "needs_internet": bool(s.get("needs_internet", False)),
                        "done": False,
                        "notes": "",
                    }
                    for s in (rec.get("plan") or [])
                ],
                "resources_used": [as_text(r) for r in (rec.get("resources_used") or [])],
            }
        )
    dream["recommendations"] = recommendations
    store.update_dream(dream)
    return recommendations


def adopt_recommendation(dream, index):
    """index is 0-based. Applies the chosen recommendation's plan as the
    dream's actual plan — the "let the AI decide" path, as opposed to
    manually running `plan`/`resources` yourself."""
    recs = dream.get("recommendations") or []
    if index < 0 or index >= len(recs):
        raise ValueError("No recommendation at that index.")
    chosen = recs[index]
    dream["plan"] = chosen["plan"]
    dream["status"] = "in_progress"
    dream["adopted_recommendation"] = {"title": chosen["title"], "summary": chosen["summary"]}
    store.update_dream(dream)
    return dream
