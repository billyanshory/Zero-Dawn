with open("app.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if "from werkzeug.security import generate_password_hash, check_password_hash" in line:
        new_lines.append("from werkzeug.middleware.proxy_fix import ProxyFix\n")
    if "app = Flask(__name__)" in line:
        new_lines.append("app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)\n")

with open("app.py", "w") as f:
    f.writelines(new_lines)
