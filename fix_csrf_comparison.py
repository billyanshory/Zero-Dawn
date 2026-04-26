import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# Let's inspect api_scan
old_api_scan = """async def api_scan(request: Request):
    client_csrf = request.headers.get("X-CSRF-Token")
    cookie_csrf = request.cookies.get("csrf_token")
    if not client_csrf or not cookie_csrf or not hmac.compare_digest(client_csrf, cookie_csrf):
        return response.json({"error": "Invalid CSRF token."}, status=403)"""

# I suspect `requests` python library didn't send the cookie properly. The issue is with my trigger_scan.py script.
# Let's fix trigger_scan.py!
