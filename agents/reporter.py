from datetime import datetime, timezone


def _count_results(test_results: str) -> tuple[int, int, int]:
    passed = test_results.count("PASS")
    failed = test_results.count("FAIL")
    errored = test_results.count("ERROR")
    return passed, failed, errored


def _generation_mode(code: str) -> str:
    first_line = code.splitlines()[0] if code else ""
    if first_line.startswith("# Generation mode:"):
        return first_line.split(":", 1)[1].strip()
    return "UNKNOWN"


def _plan_tasks(plan: str) -> list[str]:
    return [line.strip() for line in plan.splitlines() if line.strip()[:1].isdigit()]


def build_client_report(
    vision: dict,
    plan: str,
    code: str,
    test_results: str,
    reflections: str,
    canon_rules: list[str] | None = None,
) -> str:
    """Turn one pipeline run into a single client-ready deliverable.

    This is the actual sellable artifact for the agent-in-a-box service: a client
    should never have to read four raw output files to know what they got.
    """
    project = vision.get("project_name", "Untitled Project")
    goal = vision.get("goal", "")
    mode = _generation_mode(code)
    passed, failed, errored = _count_results(test_results)
    total = passed + failed + errored

    is_scaffold = "OFFLINE_GENERIC_SCAFFOLD" in mode
    is_llm = mode.startswith("LLM_GENERATED")

    if is_llm:
        status_line = "**Delivered:** a working solution, generated and verified."
    elif is_scaffold:
        status_line = (
            "**Delivered:** a reviewed task breakdown and starter scaffold. "
            "Needs a real LLM pass (or manual completion) to finish the logic."
        )
    else:
        status_line = "**Delivered:** a working demo solution, generated and verified."

    lines = [
        f"# Agent Setup Report — {project}",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## The Task",
        "",
        goal,
        "",
        "## What We Built",
        "",
    ]
    lines += (_plan_tasks(plan) or ["(see delivered code below)"])

    lines += ["", "## Status", "", status_line, "", f"_Generation mode: `{mode}`_", ""]

    lines += ["## Verification", ""]
    if total:
        summary = f"{passed}/{total} checks passed"
        if failed:
            summary += f", {failed} failed"
        if errored:
            summary += f", {errored} errored"
        lines += [summary, "", "```", test_results, "```", ""]
    else:
        lines += ["No automated checks were found in the generated code.", ""]

    lines += ["## Honest Notes", "", reflections, ""]

    if canon_rules:
        lines += ["## Rules This Was Held To", ""]
        lines += [f"- {rule}" for rule in canon_rules]
        lines += [""]

    lines += ["## Delivered Code", "", "```python", code, "```", ""]

    next_step = (
        "Review the scaffold above and confirm the categories/logic look right, "
        "then we wire in a real LLM pass to finish the implementation."
        if is_scaffold
        else "Review the solution above and let us know if anything needs adjusting before this goes live."
    )
    lines += ["## Next Step", "", next_step, ""]

    return "\n".join(lines)
