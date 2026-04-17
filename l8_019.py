import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# The tuples are currently inside seed_slb_data
# Let's find seed_slb_data
start = content.find("def seed_slb_data():")
if start != -1:
    # Find the hardcoded list: `seed_data = [...]` or similar
    match = re.search(r"seed_data\s*=\s*\[([\s\S]*?)\]\n", content[start:])
    if match:
        list_content = match.group(0)

        # We need to extract this and create _SIGN_LANGUAGE_SEED_ENTRIES
        constant_def = """# Hardcoded sign-language seed data compiled into the module to preserve zero-disk-IO design philosophy.
_SIGN_LANGUAGE_SEED_ENTRIES = (
""" + match.group(1) + "\n)\n"

        # insert right before def seed_slb_data
        content = content[:start] + constant_def + "\n" + content[start:]

        # replace the list with the constant inside the function
        content = content.replace(list_content, "seed_data = _SIGN_LANGUAGE_SEED_ENTRIES\n")

with open(fname, 'w') as f:
    f.write(content)
