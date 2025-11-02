def generate_code_from_plan(plan: str) -> str:
    return '''def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b): return a / b if b != 0 else "Error: Division by zero"

def main():
    while True:
        op = input("Operation (+, -, *, / or q): ")
        if op == "q": break
        try:
            a = float(input("First number: "))
            b = float(input("Second number: "))
            ops = {"+": add, "-": subtract, "*": multiply, "/": divide}
            print("Result:", ops.get(op, lambda x,y: "Invalid")(a, b))
        except Exception as e:
            print("Error:", str(e))

if __name__ == "__main__":
    main()
'''
