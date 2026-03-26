import sys

filepath = "kampus-stie-samarinda-0 ( idcloudhost - 3 dashboard utama - tu, mahasiswa dan dosen ).py"

with open(filepath, 'r') as f:
    content = f.read()

target = "@app.route('/')\ndef index():"

replacement = """@app.before_request
def global_gatekeeper():
    if request.endpoint in ['index', 'login', 'logout', 'static']:
        return

    user_id = session.get('user_id')
    if user_id:
        try:
            user = db.session.get(User, user_id)
            if user and user.status_akademik != 'Aktif':
                session.clear()
                return "Akses Ditolak: Status Akademik Anda tidak Aktif.", 403
        except Exception as e:
            print(f"Error in gatekeeper: {e}")

@app.route('/')
def index():"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("Gatekeeper injected.")
else:
    print("Target for gatekeeper not found.")
