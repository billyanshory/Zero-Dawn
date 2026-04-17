import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == "# --- DATA SUMBER HUKUM (DALIL) ---":
        # Look ahead to see if it's the start of the block
        if "DALIL_DATA" in "".join(lines[i:i+15]):
            skip = True

    if not skip:
        new_lines.append(line)

    if skip and line.strip() == "}":
        skip = False

with open(fname, 'w') as f:
    f.writelines(new_lines)
