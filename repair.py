import re
import os

with open("sekolah_luar_biasa.py", "r") as f:
    content = f.read()

# 1. Guards
content = content.replace(
"""def save_reaction():
    data = request.json""",
"""def save_reaction():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json"""
)

content = content.replace(
"""def save_kognitif_emosi():
    data = request.json""",
"""def save_kognitif_emosi():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json"""
)

content = content.replace(
"""def save_kognitif_bentuk():
    data = request.json""",
"""def save_kognitif_bentuk():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json"""
)

content = content.replace(
"""def get_reaction_data():
    logs = ReactionTimeLog.query""",
"""def get_reaction_data():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    logs = ReactionTimeLog.query"""
)

content = content.replace(
"""def get_tantrum_data():
    # Fetch all logs""",
"""def get_tantrum_data():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    # Fetch all logs"""
)

content = content.replace(
"""def therapy_log():
    try:""",
"""def therapy_log():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    try:"""
)

content = content.replace(
"""def api_jurnal_harian():
    try:""",
"""def api_jurnal_harian():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:"""
)

content = content.replace(
"""def get_ot_chart_data():
    q_buku = OrangTuaBuku.query""",
"""def get_ot_chart_data():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    q_buku = OrangTuaBuku.query"""
)

content = content.replace(
"""def check_burnout():
    q = OrangTuaBurnout.query""",
"""def check_burnout():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    q = OrangTuaBurnout.query"""
)


# 2. Production Entrypoint
content = content.replace(
"""    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)""",
"""    is_dev = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, debug=is_dev, port=5000, allow_unsafe_werkzeug=is_dev)"""
)

# 3. Information Leakage
content = content.replace(
"""        return f"Terjadi kesalahan: {str(e)}", 500""",
"""        app.logger.error(f"Registration error", exc_info=True)
        return "Terjadi kesalahan saat mendaftar. Silakan coba lagi.", 500"""
)

content = re.sub(r'        return jsonify\(\{"error": str\(e\)\}\), 400',
r'''        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400''', content)

content = content.replace(
"""        return jsonify({"error": str(e)}), 500
""",
"""        app.logger.error("API error", exc_info=True)
        return jsonify({"error": "Gagal mengambil data. Coba lagi nanti."}), 500
""", 1) # First 500 is yasin

content = content.replace(
"""        return jsonify({'error': str(e)}), 500""",
"""        app.logger.error("Journal API error", exc_info=True)
        return jsonify({'error': "Gagal memuat data jurnal."}), 500"""
)

content = re.sub(r'        return jsonify\(\{"error": str\(e\)\}\), 500',
r'''        app.logger.error("Nutrition dictionary error", exc_info=True)
        return jsonify({"error": "Gagal memuat kamus nutrisi."}), 500''', content)

# 4. Session Fixation & Open Redirect

is_safe_redirect_code = """
import urllib.parse
def is_safe_redirect(url):
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc == '' or parsed.netloc == request.host
    except Exception:
        return False
"""
content = content.replace("app = Flask(__name__)\n", "app = Flask(__name__)\n" + is_safe_redirect_code)


content = content.replace(
"""        if akun.status_akun == 'disetujui':
            session['user_id'] = akun.id""",
"""        if akun.status_akun == 'disetujui':
            session.clear()
            session['user_id'] = akun.id"""
)

content = content.replace(
"""            if akun.peran == 'kepala_sekolah':
                session['is_admin'] = True
            return redirect(request.referrer or url_for('index'))""",
"""            if akun.peran == 'kepala_sekolah':
                session['is_admin'] = True
            session.permanent = True
            next_url = request.referrer
            if not next_url or not is_safe_redirect(next_url):
                next_url = url_for('index')
            return redirect(next_url)"""
)

content = content.replace(
"""    if data.get('kode') == brankas_kode:
        # Kunci dewa - Verifikasi kode kombinasi dilewati frontend, disahkan backend
        session['user_id'] = 1""",
"""    if data.get('kode') == brankas_kode:
        # Kunci dewa - Verifikasi kode kombinasi dilewati frontend, disahkan backend
        session.clear()
        session['user_id'] = 1"""
)
content = content.replace(
"""        session['peran'] = 'kepala_sekolah'
        session['is_admin'] = True
        return jsonify({'status': 'success', 'redirect_url': url_for('dashboard_validator')})""",
"""        session['peran'] = 'kepala_sekolah'
        session['is_admin'] = True
        session.permanent = True
        return jsonify({'status': 'success', 'redirect_url': url_for('dashboard_validator')})"""
)


# 5. Password Policy
content = content.replace(
"""        # Check if username or nik already exists""",
"""        if not password or len(password) < 8:
            return "Password harus minimal 8 karakter.", 400
        if not nik or len(nik) < 5:
            return "NIK harus minimal 5 karakter.", 400
        if not username or len(username) < 3:
            return "Username harus minimal 3 karakter.", 400
        if not nama_lengkap or len(nama_lengkap.strip()) < 2:
            return "Nama lengkap harus minimal 2 karakter.", 400
        if peran not in ['orang_tua', 'guru', 'kepala_sekolah']:
            return "Peran tidak valid.", 400

        # Check if username or nik already exists"""
)

# 6. CSRF Exemption
content = content.replace(
"""@app.route('/api/profil-medis/<int:siswa_id>', methods=['POST'])
@csrf.exempt
def update_profil_medis""",
"""@app.route('/api/profil-medis/<int:siswa_id>', methods=['POST'])
def update_profil_medis"""
)

# 7. try/except/rollback
def wrap_commit(func_snippet, error_handler):
    global content
    content = content.replace(
        func_snippet + "\n    db.session.commit()",
        func_snippet + "\n    try:\n        db.session.commit()\n    except Exception as e:\n        db.session.rollback()\n        app.logger.error('Database commit error', exc_info=True)\n" + "        " + error_handler
    )

wrap_commit("profil.tambahan_info = data.get('tambahan_info', profil.tambahan_info)", "return jsonify({'error': 'Database error'}), 500")
wrap_commit("akun.status_akun = 'disetujui'", "return redirect(url_for('dashboard_validator'))")
wrap_commit("akun.status_akun = 'ditolak'", "return redirect(url_for('dashboard_validator'))")
wrap_commit("db.session.add(log)", "return jsonify({'error': 'Database error'}), 500") # for save_reaction, save_kognitif_emosi, save_kognitif_bentuk (same snippet, applying to all)

content = content.replace(
"""        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error logging therapy: {e}")""",
"""        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error("Error logging therapy commit", exc_info=True)
            return redirect(url_for('index'))
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error logging therapy: {e}", exc_info=True)"""
)

# 8. Unbounded Queries
content = content.replace("StudentPortfolio.query.order_by", "StudentPortfolio.query.limit(100).order_by")
content = content.replace("ReactionTimeLog.query.order_by(ReactionTimeLog.created_at.asc()).all()", "ReactionTimeLog.query.order_by(ReactionTimeLog.created_at.desc()).limit(100).all()")
content = content.replace("TantrumLog.query.order_by(TantrumLog.created_at.desc()).all()", "TantrumLog.query.filter(TantrumLog.created_at >= datetime.datetime.now() - datetime.timedelta(days=30)).order_by(TantrumLog.created_at.desc()).all()")

# 9. Logging replaces print
content = content.replace("print(f\"Error seeding SLB data: {e}\")", "app.logger.error(f\"Error seeding SLB data: {e}\", exc_info=True)")

# 10. Bare Excepts
content = content.replace(
"""        return settings
    except:
        settings = {}""",
"""        return settings
    except Exception:
        app.logger.warning("Failed to load app settings", exc_info=True)
        settings = {}"""
)
content = content.replace(
"""        db.session.close()
    except:
        epilepsi_logs = []""",
"""        db.session.close()
    except Exception:
        app.logger.warning("Failed to load epilepsi logs", exc_info=True)
        epilepsi_logs = []"""
)
content = content.replace("except: pass", "except (ValueError, TypeError): pass", 1) # first is in tantrum
content = content.replace("except: pass", "except (json.JSONDecodeError, TypeError): pass", 1) # second in check_medications

# 11. N+1 Query
content = content.replace(
"""    for siswa in siswa_list:
        profil_exists = ProfilMedisSiswa.query.filter_by(siswa_id=siswa.id).first() is not None
        results.append({
            'id': siswa.id,""",
"""    siswa_ids = [s.id for s in siswa_list]
    existing_profiles = {p.siswa_id for p in db.session.query(ProfilMedisSiswa.siswa_id).filter(ProfilMedisSiswa.siswa_id.in_(siswa_ids)).all()}

    for siswa in siswa_list:
        profil_exists = siswa.id in existing_profiles
        results.append({
            'id': siswa.id,"""
)

# 12. query.get()
content = re.sub(r'([A-Za-z0-9_]+)\.query\.get\(([^)]+)\)', r'db.session.get(\1, \2)', content)

# 13. Duplicate Imports
content = re.sub(r'^from flask import current_app\n', '', content, flags=re.MULTILINE, count=1) # keep first
content = re.sub(r'^import urllib\.request\n', '', content, flags=re.MULTILINE, count=1)
content = re.sub(r'^import io\n', '', content, flags=re.MULTILINE, count=1)
content = re.sub(r'^from PIL import Image\n', '', content, flags=re.MULTILINE, count=1)

# 14. Add Comments
content = content.replace(
"""        db.create_all()""",
"""        # TODO: Migrate to Flask-Migrate/Alembic for schema management. db.create_all() only creates new tables; it does NOT alter existing ones.
        db.create_all()"""
)
content = content.replace(
"""        with urllib.request.urlopen(req, timeout=8) as response:""",
"""        # Note: urllib.request may not be fully patched by eventlet. Result is cached for 24h so impact is minimal. Consider using the requests library if blocking becomes an issue.
        with urllib.request.urlopen(req, timeout=8) as response:"""
)

with open("sekolah_luar_biasa.py", "w") as f:
    f.write(content)
