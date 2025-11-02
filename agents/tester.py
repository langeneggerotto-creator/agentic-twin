def run_tests_on_code() -> str:
    return '''
def test_add(): assert add(2, 3) == 5
def test_subtract(): assert subtract(5, 2) == 3
def test_multiply(): assert multiply(3, 4) == 12
def test_divide(): assert divide(10, 2) == 5
def test_divide_by_zero(): assert divide(10, 0) == "Error: Division by zero"
'''
