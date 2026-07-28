from . import store
from .llm_client import chat
from .util import extract_json_array
from .web_lookup import search

RESOURCE_SYSTEM_PROMPT = (
    "You help find what a person needs to achieve a goal: tools, services, "
    "courses, equipment, funding, communities, or people. For each resource, "
    "say why it's needed and give ONE short web search query that would find "
    "current, real options for it. Prefer free or low-cost options where "
    "they would genuinely work as well as paid ones — only suggest looking "
    "for paid options when they would clearly beat free ones for this goal.\n\n"
    "Respond with ONLY a JSON array, no other text, in this exact shape:\n"
    '[{"resource": "...", "why": "...", "search_query": "..."}]'
)

RANK_SYSTEM_PROMPT = (
    "You are a frugal, practical resource advisor. Given a resource someone "
    "needs and a list of real search results for it, recommend the option(s) "
    "that give the highest value for the lowest cost. Be specific — name "
    "actual options from the results, not generic advice. If none of the "
    "results are actually useful, say so plainly instead of forcing a pick. "
    "Keep it to 2-4 sentences."
)


def _rank_options(need, options):
    if not options:
        return (
            "No search results found for this — try a manual search or "
            "refine the query."
        )
    listing = "\n".join(
        f"- {o['title']}: {o['snippet']} ({o['url']})" for o in options
    )
    messages = [
        {"role": "system", "content": RANK_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Resource needed: {need.get('resource', '')}\n"
                f"Why: {need.get('why', '')}\n\n"
                f"Search results:\n{listing}"
            ),
        },
    ]
    return chat(messages)


def find_resources(dream, max_results=5):
    messages = [
        {"role": "system", "content": RESOURCE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Goal: {dream['title']}\nDetails: {dream['description']}",
        },
    ]
    raw = chat(messages)
    needs = extract_json_array(raw)

    resources = []
    for need in needs:
        query = need.get("search_query", "")
        options = search(query, max_results=max_results) if query else []
        resources.append(
            {
                "resource": need.get("resource", ""),
                "why": need.get("why", ""),
                "search_query": query,
                "options": options,
                "recommendation": _rank_options(need, options),
            }
        )

    dream["resources"] = resources
    store.update_dream(dream)
    return resources
