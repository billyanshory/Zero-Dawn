import re

with open("app.py", "r") as f:
    content = f.read()

# TEST 1
match_fstring = re.search(r'content\s*=\s*f"""(.*?)"""', content, re.DOTALL)
if match_fstring:
    print("Found f-string block")

# TEST 2
match_irma = re.search(r'IRMA_STYLES\s*=\s*""".*?"""', content, re.DOTALL)
if match_irma:
    print("Found IRMA_STYLES")
