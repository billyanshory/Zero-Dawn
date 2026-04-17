import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

encapsulation_code = """
class _ConnectedClientsHolder:
    \"\"\"In-memory connected-client tracker. Assumes single-worker eventlet semantics. For multi-worker WSGI, replace with Redis-backed implementation using Flask-SocketIO message_queue.\"\"\"
    def __init__(self):
        self._clients: dict[str, str] = {}

    def add(self, sid: str, device_id: str) -> None:
        self._clients[sid] = device_id

    def remove(self, sid: str) -> None:
        self._clients.pop(sid, None)

    def snapshot(self) -> dict[str, str]:
        return dict(self._clients)

    def count(self) -> int:
        return len(self._clients)

_connected_clients = _ConnectedClientsHolder()
"""

# Replace the bare dictionary with the class
# It might be `connected_clients_dict = {}` or something similar with comments.
content = re.sub(
    r"#*\s*connected_clients_dict\s*=\s*{}[ \t]*[^\n]*\n",
    encapsulation_code + "\n",
    content
)

# Update handle_connect
# Remove `global connected_clients_dict`
content = re.sub(r"^[ \t]*global connected_clients_dict[ \t]*\n", "", content, flags=re.MULTILINE)

# Replace dictionary access
# `connected_clients_dict[request.sid] = device_id` -> `_connected_clients.add(request.sid, device_id)`
content = re.sub(
    r"connected_clients_dict\[request\.sid\]\s*=\s*([a-zA-Z0-9_.]+)",
    r"_connected_clients.add(request.sid, \1)",
    content
)

# `connected_clients_dict.pop(request.sid, None)` -> `_connected_clients.remove(request.sid)`
content = content.replace("connected_clients_dict.pop(request.sid, None)", "_connected_clients.remove(request.sid)")

# There might also be `del connected_clients_dict[request.sid]`
content = re.sub(
    r"del connected_clients_dict\[request\.sid\]",
    r"_connected_clients.remove(request.sid)",
    content
)

# `len(connected_clients_dict)` -> `_connected_clients.count()`
content = content.replace("len(connected_clients_dict)", "_connected_clients.count()")

# `list(connected_clients_dict.values())` -> `list(_connected_clients.snapshot().values())`
content = content.replace("list(connected_clients_dict.values())", "list(_connected_clients.snapshot().values())")

# `connected_clients_dict` general usage to `_connected_clients.snapshot()` (just in case there are others)
content = content.replace("connected_clients_dict.values()", "_connected_clients.snapshot().values()")

# wait, verify we didn't leave any connected_clients_dict
with open(fname, 'w') as f:
    f.write(content)
