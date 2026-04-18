import re

with open("app.py", "r") as f:
    content = f.read()

vapid_pattern = r"def vapid_public_key\(\) -> Response \| str \| tuple\[Response, int\]:\n\s+\"\"\"Handles requests to the vapid_public_key endpoint\.\"\"\"\n\s+if not VAPID_PUBLIC_KEY:\n\s+return jsonify\(\{'error': 'Push notifications not configured'\}\), 503"
vapid_replacement = """def vapid_public_key() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the vapid_public_key endpoint.\"\"\"
    if not PUSH_NOTIFICATIONS_ENABLED:
        return jsonify({'error': 'Push not configured'}), 503"""
content = re.sub(vapid_pattern, vapid_replacement, content)

with open("app.py", "w") as f:
    f.write(content)
