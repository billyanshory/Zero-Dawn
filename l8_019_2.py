import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

start = content.find("def seed_slb_data():")
if start != -1:
    match = re.search(r"data\s*=\s*\[([\s\S]*?)\]", content[start:])
    if match:
        list_content = match.group(0)

        constant_def = """# Hardcoded sign-language seed data compiled into the module to preserve zero-disk-IO design philosophy.
_SIGN_LANGUAGE_SEED_ENTRIES = (
""" + match.group(1) + "\n)\n"

        content = content[:start] + constant_def + "\n" + content[start:]

        content = content.replace(list_content, "data = _SIGN_LANGUAGE_SEED_ENTRIES")

with open(fname, 'w') as f:
    f.write(content)
