from agents import planner, developer, tester, reflector
from governance.gatekeeper import enforce_canon

# Plan
plan = planner.plan_from_vision("vault/vision.json", "vault/canon.json")
with open("outputs/plan.md", "w") as f: f.write(plan)

# Code
code = developer.generate_code_from_plan(plan)
with open("outputs/generated_code.py", "w") as f: f.write(code)

# Tests
test_results = tester.run_tests_on_code()
with open("outputs/test_results.txt", "w") as f: f.write(test_results)

# Reflect
reflections = reflector.reflect_on_results(plan, code, test_results)
with open("outputs/reflection.txt", "w") as f: f.write(reflections)

# Canon
violations = enforce_canon(code, "vault/canon.json")
if violations:
    print("❌ Canon Violations:", violations)
else:
    print("✅ Canon Compliance Passed")

print("🪞 Reflections:")
print(reflections)
