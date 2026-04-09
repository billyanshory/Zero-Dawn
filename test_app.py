import sys
try:
    import py_compile
    py_compile.compile('app.py', doraise=True)
    print("Syntax OK")
except Exception as e:
    print(f"Syntax error: {e}")
    sys.exit(1)
