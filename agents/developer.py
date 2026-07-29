import os
import re

CALCULATOR_TEMPLATE = '''"""
Offline demo template: CLI calculator (add, subtract, multiply, divide).
"""

def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b): return a / b if b != 0 else "Error: Division by zero"


def test_add(): assert add(2, 3) == 5
def test_subtract(): assert subtract(5, 2) == 3
def test_multiply(): assert multiply(3, 4) == 12
def test_divide(): assert divide(10, 2) == 5
def test_divide_by_zero(): assert divide(10, 0) == "Error: Division by zero"


def main():
    while True:
        op = input("Operation (+, -, *, / or q): ")
        if op == "q": break
        try:
            a = float(input("First number: "))
            b = float(input("Second number: "))
            ops = {"+": add, "-": subtract, "*": multiply, "/": divide}
            print("Result:", ops.get(op, lambda x, y: "Invalid")(a, b))
        except Exception as e:
            print("Error:", str(e))


if __name__ == "__main__":
    main()
'''


def _is_calculator_plan(plan: str) -> bool:
    lower = plan.lower()
    return "calculator" in lower and "add" in lower


def _extract_tasks(plan: str) -> list[str]:
    return [line.strip() for line in plan.splitlines() if re.match(r"^\d+\.\s", line.strip())]


def _slugify_task(task: str, max_words: int = 6) -> str:
    text = re.sub(r"^\d+\.\s*", "", task).strip().rstrip(".")
    words = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_").split("_")
    slug = "_".join(words[:max_words])
    return slug or "task"


def _dedupe_names(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        result.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return result


def _generic_scaffold(plan: str, tasks: list[str]) -> str:
    step_names = _dedupe_names([f"step_{_slugify_task(task)}" for task in tasks]) or ["step_review_plan"]

    lines = [
        '"""',
        "Auto-generated scaffold. No LLM was available, so each plan step below",
        "is stubbed out and needs a human (or a later LLM pass) to implement it.",
        '"""',
        "",
        f"STEP_NAMES = {step_names!r}",
        "",
    ]

    for name, task in zip(step_names, tasks or ["Review the plan."]):
        safe_task = task.replace('"', '\\"')
        lines += [
            f"def {name}():",
            f'    """TODO: implement - {safe_task}"""',
            f'    raise NotImplementedError("{safe_task}")',
            "",
        ]

    lines += [
        "def main():",
        '    print("Scaffold only - implement the step_* functions above.")',
        "",
        "",
        "def test_scaffold_steps_defined():",
        "    for name in STEP_NAMES:",
        '        assert name in globals(), f"missing step function {name}"',
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ]

    return "\n".join(lines)


def _call_openai(plan: str, canon_rules: list[str] | None) -> str | None:
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    rules_text = "\n".join(f"- {rule}" for rule in (canon_rules or []))
    prompt = (
        "Write a single self-contained Python module that implements the plan below.\n"
        "Include at least one function named test_<something> per behavior, using plain "
        "assert statements, so an external test runner can discover and execute them.\n"
        "Return only Python code - no markdown fences, no commentary.\n\n"
        f"Plan:\n{plan}\n\nRules:\n{rules_text}"
    )

    try:
        client = OpenAI()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception:
        return None


def _label(code: str, mode: str) -> str:
    return f"# Generation mode: {mode}\n{code}"


def generate_code_from_plan(plan: str, vision: dict | None = None, canon_rules: list[str] | None = None) -> str:
    llm_code = _call_openai(plan, canon_rules)
    if llm_code:
        return _label(llm_code, "LLM_GENERATED (OpenAI)")

    reason = (
        "OPENAI_API_KEY not set"
        if not os.environ.get("OPENAI_API_KEY")
        else "OpenAI call failed or SDK unavailable"
    )

    if _is_calculator_plan(plan):
        return _label(CALCULATOR_TEMPLATE, f"OFFLINE_DEMO_TEMPLATE ({reason})")

    tasks = _extract_tasks(plan)
    return _label(
        _generic_scaffold(plan, tasks),
        f"OFFLINE_GENERIC_SCAFFOLD ({reason}); human/LLM completion required",
    )
