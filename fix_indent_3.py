fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# I see what happened. `_ConnectedClientsHolder` was injected incorrectly or mangled by `replace`.
# Let's just fix the indentation around it.
# Wait, where is `class _ConnectedClientsHolder:`? It seems missing from the snippet!
# Ah! `class _ConnectedClientsHolder:` might have been overwritten if it was replaced poorly.

# Let's completely recreate the `connected_clients_dict` encapsulation by starting fresh from the git repo for just that section, OR just manually fixing the lines.
import re

content = re.sub(r'def __init__\(self\):\n        self\._clients: dict\[str, str\] = \{\}', r'class _ConnectedClientsHolder:\n    def __init__(self):\n        self._clients: dict[str, str] = {}', content)

with open(fname, 'w') as f:
    f.write(content)
