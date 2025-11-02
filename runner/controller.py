from agents import planner, developer, tester
from governance.gatekeeper import enforce_canon

vision = "vault/vision.json"
canon = "vault/canon.json"

plan = planner.plan_from_vision(vision, canon)
with open("outputs/plan.md", "w") as f:
    f.write(plan)

code = developer.generate_code_from_plan(plan)
with open("outputs/generated_code.py", "w") as f:
    f.write(code)

tests = tester.run_tests_on_code()
with open("outputs/test_results.txt", "w") as f:
    f.write(tests)

violations = enforce_canon(code, canon)
if violations:
    print("❌ Canon Violations:")
    for v in violations:
        print("-", v)
else:
    print("✅ Canon compliance passed.")
