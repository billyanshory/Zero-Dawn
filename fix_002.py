import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Let's see what the line looks like that fails the regex
lines = content.split('\n')
for line in lines:
    if "session.get('peran') not in" in line and "def require_auth" not in line:
        match = re.search(r"not in \[(.*?)\]", line)
        if not match:
            print("Failed match on line:", line)
