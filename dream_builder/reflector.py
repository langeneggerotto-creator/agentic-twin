from . import store
from .llm_client import chat

REFLECT_SYSTEM_PROMPT = (
    "You are a candid, supportive planning coach. You will be shown a "
    "person's goal, their plan, and which steps are done. Give a short, "
    "honest reflection: what's working, what's stalled, and one concrete "
    "next action. Do not be vague or inspirational-poster generic. If the "
    "plan looks wrong given what's happened, say so and suggest a specific "
    "change."
)


def reflect(dream):
    plan_summary = "\n".join(
        f"- [{'x' if s['done'] else ' '}] {s['step']}" for s in dream["plan"]
    ) or "(no plan yet)"
    messages = [
        {"role": "system", "content": REFLECT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Goal: {dream['title']}\nDetails: {dream['description']}\n\n"
                f"Plan:\n{plan_summary}"
            ),
        },
    ]
    text = chat(messages)
    dream["reflections"].append({"date": store.now(), "text": text})
    store.update_dream(dream)
    return text
