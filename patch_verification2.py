with open("app.py", "r") as f:
    content = f.read()

content = content.replace("app.config['SESSION_COOKIE_SECURE'] = not _is_dev_env", "app.config['SESSION_COOKIE_SECURE'] = not _is_dev_env\napp.config['REMEMBER_COOKIE_SECURE'] = not _is_dev_env\napp.config['REMEMBER_COOKIE_HTTPONLY'] = True")

with open("app.py", "w") as f:
    f.write(content)
