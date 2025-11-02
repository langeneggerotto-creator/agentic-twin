import json

def plan_from_vision(vision_path: str, canon_path: str) -> str:
    with open(vision_path) as f:
        vision = json.load(f)
    with open(canon_path) as f:
        canon = json.load(f)

    plan = [
        f"# Plan for {vision['project_name']}",
        f"**Goal:** {vision['goal']}",
        "## Tasks:",
        "1. Design CLI interface.",
        "2. Implement calculator functions.",
        "3. Handle CLI I/O.",
        "4. Write unit tests.",
        "5. Validate Canon rules."
    ]

    return "\n".join(plan)
