import argparse
import json

from agents import planner, developer, tester, reflector, reporter
from governance.gatekeeper import enforce_canon


def main():
    parser = argparse.ArgumentParser(
        description="Run the Agentic Twin planner -> developer -> tester -> reflector loop against a vision/canon pair."
    )
    parser.add_argument("--vision", default="vault/vision.json", help="Path to a vision.json describing the project goal.")
    parser.add_argument("--canon", default="vault/canon.json", help="Path to a canon.json describing the project rules.")
    args = parser.parse_args()

    with open(args.vision) as f:
        vision = json.load(f)
    with open(args.canon) as f:
        canon = json.load(f)

    # Plan
    plan = planner.plan_from_vision(args.vision, args.canon)
    with open("outputs/plan.md", "w") as f:
        f.write(plan)

    # Code
    code = developer.generate_code_from_plan(plan, vision=vision, canon_rules=canon.get("rules"))
    with open("outputs/generated_code.py", "w") as f:
        f.write(code)

    # Tests
    test_results = tester.run_tests_on_code()
    with open("outputs/test_results.txt", "w") as f:
        f.write(test_results)

    # Reflect
    reflections = reflector.reflect_on_results(plan, code, test_results, vision=vision)
    with open("outputs/reflection.txt", "w") as f:
        f.write(reflections)

    # Canon
    violations = enforce_canon(code, args.canon)
    if violations:
        print("❌ Canon Violations:", violations)
    else:
        print("✅ Canon Compliance Passed")

    print("🪞 Reflections:")
    print(reflections)

    # Client-ready deliverable
    report = reporter.build_client_report(
        vision, plan, code, test_results, reflections, canon_rules=canon.get("rules")
    )
    with open("outputs/client_report.md", "w") as f:
        f.write(report)
    print("\n📄 Client report written to outputs/client_report.md")


if __name__ == "__main__":
    main()
