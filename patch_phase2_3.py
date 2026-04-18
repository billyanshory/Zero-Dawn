with open("app.py", "r") as f:
    content = f.read()

# We want to replace the current add_security_headers with the new implementation.
old_func_start = "def add_security_headers(response: Response) -> Response:\n    if hasattr(g, 'request_id'):\n        response.headers['X-Request-ID'] = g.request_id"

import re

# Need to accurately match the rest of the old function.
match = re.search(r"def add_security_headers\(response: Response\) -> Response:.*?return response", content, re.DOTALL)
if match:
    old_func = match.group(0)

new_func = """_CSP_HTML = "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: blob: https://cdnjs.cloudflare.com; connect-src 'self' wss: ws:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
_CSP_JSON = "default-src 'none'; frame-ancestors 'none'"
_PERMISSIONS_POLICY = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=(), interest-cohort=()"

@app.after_request
def add_security_headers(response: Response) -> Response:
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id

    content_type = response.headers.get('Content-Type', '').lower()
    is_html = 'text/html' in content_type
    is_json = 'application/json' in content_type

    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = _PERMISSIONS_POLICY
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'

    if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

    response.headers.pop('Server', None)
    response.headers.pop('X-Powered-By', None)

    if is_html:
        response.headers['Content-Security-Policy'] = _CSP_HTML
    elif is_json:
        response.headers['Content-Security-Policy'] = _CSP_JSON

    return response"""

# Replace @app.after_request before the match if it exists.
if "@app.after_request\n" + old_func in content:
    content = content.replace("@app.after_request\n" + old_func, new_func)
else:
    content = content.replace(old_func, new_func)
    if "@app.after_request" not in new_func:
       pass # the pattern might not be perfect.

with open("app.py", "w") as f:
    f.write(content)
