import requests
import re
import time

# We must manually set the cookie for requests to bypass the HTTP vs secure=True limitation during this local unit test
s = requests.Session()
r = s.get("http://127.0.0.1:8000/")
match = re.search(r'<meta name="csrf-token" content="([^"]+)">', r.text)
csrf_token = match.group(1) if match else ""

# Force the cookie into the session manually
s.cookies.set("csrf_token", csrf_token, domain="127.0.0.1", path="/")

headers = {"X-CSRF-Token": csrf_token}
json_data = {"url": "https://example.com"}

r2 = s.post("http://127.0.0.1:8000/api/scan", headers=headers, json=json_data, timeout=30)
print(f"Scan status: {r2.status_code}")
print(r2.text)
