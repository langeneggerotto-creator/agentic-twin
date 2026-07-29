def run_tests_on_code() -> str:
    results = []
    try:
        with open("outputs/generated_code.py") as f:
            code = f.read()

        namespace: dict = {}
        exec(code, namespace)

        test_names = sorted(
            name for name, value in namespace.items()
            if name.startswith("test_") and callable(value)
        )

        if not test_names:
            results.append("⚠️ No test_ functions found in generated code.")
            return "\n".join(results)

        for name in test_names:
            try:
                namespace[name]()
                results.append(f"{name}: ✅ PASS")
            except AssertionError as e:
                detail = f" ({e})" if str(e) else ""
                results.append(f"{name}: ❌ FAIL{detail}")
            except Exception as e:
                results.append(f"{name}: ❌ ERROR ({type(e).__name__}: {e})")

    except Exception as e:
        results.append(f"❌ Test runner error: {e}")

    return "\n".join(results)
