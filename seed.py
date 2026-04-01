import sys; import importlib.util; spec = importlib.util.spec_from_file_location("app", "kampus-stie-samarinda-28 ( idcloudhost - siklus 1 - ingat saya, warna status, batasan login akun, file di laci arsip ).py"); app_mod = importlib.util.module_from_spec(spec); sys.modules["app"] = app_mod; spec.loader.exec_module(app_mod); app = app_mod.app; db = app_mod.db; User = app_mod.User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='2401234').first():
        db.session.add(User(username='2401234', password_hash=generate_password_hash('pass'), role='Mahasiswa', nama='Mahasiswa Test', status_akademik='Aktif'))
    if not User.query.filter_by(username='112233').first():
        db.session.add(User(username='112233', password_hash=generate_password_hash('pass'), role='Dosen', nama='Dosen Test', status_akademik='Aktif'))
    db.session.commit()
