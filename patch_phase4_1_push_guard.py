import re

with open("app.py", "r") as f:
    content = f.read()

# Make sure all API endpoints around push subscriptions also have the guard.
# We will just look for `def vapid_public_key` and any push-related endpoint.
# The user specified: audit every route in the file that calls webpush, currently the route at line 12349 (and related sibling routes)
# We will do this via a simple regex for the /api/push and /api/vapid routes
def add_guard(match):
    return match.group(0) + "\n    if not PUSH_NOTIFICATIONS_ENABLED:\n        return jsonify({'error': 'Push not configured'}), 503"

# Look for `@app.route('/api/push/subscribe'` or similar routes. Let's see what exists.
