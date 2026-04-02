import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

print("Has expected_captcha:", "expected_captcha =" in code)
print("Has user.nama.lower():", "user.nama.lower() !=" in code)
print("Has cache.clear():", "cache.clear()" in code)
