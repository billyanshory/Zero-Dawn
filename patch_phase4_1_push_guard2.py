import re

with open("app.py", "r") as f:
    content = f.read()

subscribe_pattern = r"def subscribe\(\) -> Response \| str \| tuple\[Response, int\]:\n\s+\"\"\"Handles requests to the subscribe endpoint\.\"\"\""
subscribe_replacement = """def subscribe() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the subscribe endpoint.\"\"\"
    if not PUSH_NOTIFICATIONS_ENABLED:
        return jsonify({'error': 'Push not configured'}), 503"""
content = re.sub(subscribe_pattern, subscribe_replacement, content)

with open("app.py", "w") as f:
    f.write(content)
