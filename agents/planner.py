import json

def plan_from_vision(vision_path: str, canon_path: str) -> str:
    with open(vision_path) as f:
        vision = json.load(f)
    with open(canon_path) as f:
        canon = json.load(f)

    interface = vision.get("constraints", {}).get("interface", "the")

    plan = [
        f"# Plan for {vision['project_name']}",
        f"**Goal:** {vision['goal']}",
        "## Tasks:",
        f"1. Design {interface} interface.",
        f"2. Implement core logic for: {vision['goal']}",
        f"3. Handle {interface} I/O.",
        "4. Write unit tests.",
        "5. Validate Canon rules."
    ]

    return "\n".join(plan)
