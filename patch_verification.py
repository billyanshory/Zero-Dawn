import re

with open("app.py", "r") as f:
    content = f.read()

# 1. 30-10-50 inside JS block
content = content.replace("body: JSON.stringify({ kode: '30-10-50' })", "body: JSON.stringify({ kode: 'your-vault-code' })")

# 2. SESSION_COOKIE_SECURE inside app.py (was not fully updated during Phase 1 for some reason)
cookie_old = "app.config['SESSION_COOKIE_SECURE'] = True"
cookie_new = "_is_dev_env = os.getenv('FLASK_ENV', 'production').lower() == 'development'\napp.config['SESSION_COOKIE_SECURE'] = not _is_dev_env"
content = content.replace(cookie_old, cookie_new)

with open("app.py", "w") as f:
    f.write(content)
