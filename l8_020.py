import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Replace any sequence of 4 or more newlines (which means 3 or more blank lines)
# with exactly 3 newlines (which means 2 blank lines)
# \n\n\n\n+ means 3+ blank lines
new_content = re.sub(r'\n{4,}', '\n\n\n', content)

with open(fname, 'w') as f:
    f.write(new_content)
