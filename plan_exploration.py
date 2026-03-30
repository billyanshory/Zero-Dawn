import re

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# Find major sections
def print_matches(pattern, name):
    matches = re.finditer(pattern, content, re.MULTILINE)
    print(f"--- {name} ---")
    for m in matches:
        # get line number
        lineno = content.count('\n', 0, m.start()) + 1
        print(f"Line {lineno}: {m.group(0).strip()[:100]}")

print_matches(r"^def \w+\(.*\):$", "Functions")
print_matches(r"^class \w+\(?.*\)?:$", "Classes")
print_matches(r"^@app\.route.*$", "Routes")
