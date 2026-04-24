import ast
try:
    with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
        ast.parse(f.read())
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError: {e}")
