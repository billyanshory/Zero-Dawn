import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

match = re.search(r'return (\'\'\'|""")([\s\S]*?)\1\s*,\s*500', content)
if match:
    literal = match.group(0)
    html_content = match.group(2)
    quote = match.group(1)

    constant_def = f"# ============================================================\n# TEMPLATE: ERROR_500_HTML\n# CONSUMED BY: handle_exception\n# ============================================================\nERROR_500_HTML = {quote}{html_content}{quote}\n"

    handler_decorator = content.rfind("@app.errorhandler(500)", 0, match.start())
    content = content[:handler_decorator] + constant_def + "\n" + content[handler_decorator:]

    content = content.replace(literal, "return ERROR_500_HTML, 500")

    with open(fname, 'w') as f:
        f.write(content)
else:
    print("Match not found.")
    # let's look for what's actually there
    idx = content.find("def handle_exception(e):")
    if idx != -1:
        end = content.find("def ", idx + 10)
        print(content[idx:end])
