import re

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "r") as f:
    code = f.read()

# Original string from previous run:
# response.headers['Content-Security-Policy'] = "default-src 'self' https: data:; script-src 'self' https:; style-src 'self' https:;"
# But earlier I might have replaced it with:
# response.headers['Content-Security-Policy'] = "default-src 'self' https: data:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:;"
# Let's check what's actually in there.
print("Current CSP:")
for line in code.split('\n'):
    if 'Content-Security-Policy' in line:
        print(line)

csp_search = re.search(r'response\.headers\[\'Content-Security-Policy\'\].*', code)
if csp_search:
    code = code.replace(csp_search.group(0), "response.headers['Content-Security-Policy'] = \"default-src 'self' https: data:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:;\"")

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "w") as f:
    f.write(code)
