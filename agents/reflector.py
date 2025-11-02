def reflect_on_results(plan: str, code: str, test_results: str) -> str:
    reflections = []

    if "FAIL" in test_results:
        reflections.append("❌ Some tests failed. Suggest reviewing logic.")

    if len(code.splitlines()) > 80:
        reflections.append("⚠️ Code is a bit long. Could be refactored for modularity.")

    if "input(" not in code:
        reflections.append("⚠️ No user input found. CLI interface may be missing.")

    if not reflections:
        reflections.append("✅ All components seem aligned with vision and canon.")

    return "\n".join(reflections)
