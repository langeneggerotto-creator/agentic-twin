def run_tests_on_code() -> str:
    from io import StringIO
    import contextlib

    results = []
    try:
        with open("outputs/generated_code.py") as f:
            code = f.read()
        exec(code, globals())

        def test_add(): assert add(2, 3) == 5
        def test_subtract(): assert subtract(5, 2) == 3
        def test_multiply(): assert multiply(3, 4) == 12
        def test_divide(): assert divide(10, 2) == 5
        def test_divide_by_zero(): assert divide(10, 0) == "Error: Division by zero"

        test_funcs = [test_add, test_subtract, test_multiply, test_divide, test_divide_by_zero]
        for test in test_funcs:
            try:
                test()
                results.append(f"{test.__name__}: ✅ PASS")
            except AssertionError:
                results.append(f"{test.__name__}: ❌ FAIL")

    except Exception as e:
        results.append(f"❌ Test runner error: {e}")

    return "\n".join(results)
