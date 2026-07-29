def reflect_on_results(plan: str, code: str, test_results: str, vision: dict | None = None) -> str:
    reflections = []

    if "FAIL" in test_results or "ERROR" in test_results:
        reflections.append("❌ Some tests failed. Suggest reviewing logic.")

    if len(code.splitlines()) > 80:
        reflections.append("⚠️ Code is a bit long. Could be refactored for modularity.")

    interface = (vision or {}).get("constraints", {}).get("interface")
    if interface == "CLI" and "input(" not in code:
        reflections.append("⚠️ No user input found. CLI interface may be missing.")

    if "NotImplementedError" in code or "TODO" in code:
        reflections.append(
            "⚠️ Generated code is a scaffold - steps still need implementation "
            "(likely no LLM key was configured)."
        )

    if not reflections:
        reflections.append("✅ All components seem aligned with vision and canon.")

    return "\n".join(reflections)
