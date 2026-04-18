with open("app.py", "r") as f:
    content = f.read()

# We need to move @app.after_request to sit immediately above def add_security_headers
# The current broken state is:
broken_pattern = """@app.after_request

@app.route('/healthz', methods=['GET'])"""

fixed_pattern = """@app.route('/healthz', methods=['GET'])"""

content = content.replace(broken_pattern, fixed_pattern)

# Now find def add_security_headers and ensure it has the @app.after_request above it.
security_headers_pattern = """def add_security_headers(response: Response) -> Response:"""
fixed_security_headers_pattern = """@app.after_request
def add_security_headers(response: Response) -> Response:"""

content = content.replace(security_headers_pattern, fixed_security_headers_pattern)

with open("app.py", "w") as f:
    f.write(content)
