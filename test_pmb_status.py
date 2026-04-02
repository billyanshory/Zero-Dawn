import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

print("Has api_pmb_status:", "def api_pmb_status()" in code)
print("Has api_pmb_check:", "def api_pmb_check()" in code)
print("Has gatekeeper update:", "api_pmb_status" in code and "global_gatekeeper" in code)
print("Has HTML check updated:", "fetch('/api/pmb/status?nama='" in code)
