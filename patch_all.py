import re

filename = "sekolah-luar-biasa-71 ( idcloudhost - cleaning code - pembersihan sisa code masa lalu - masjid al-hijrah - second effort ).py"

with open(filename, 'r') as f:
    content = f.read()

# 1. Imports
search_imports = "from flask_wtf.csrf import CSRFProtect"
replace_imports = "from flask_wtf.csrf import CSRFProtect, generate_csrf\nimport uuid"
content = content.replace(search_imports, replace_imports)

# 2. Add Authentication Guard to /slb/tunalaras
search_tunalaras = """@app.route('/slb/tunalaras', methods=['GET', 'POST'])
def slb_tunalaras():
    if request.method == 'POST':
        try:"""
replace_tunalaras = """@app.route('/slb/tunalaras', methods=['GET', 'POST'])
def slb_tunalaras():
    if request.method == 'POST':
        if not session.get('user_id') or session.get('peran') not in ['orang_tua', 'guru', 'kepala_sekolah']:
            return redirect(url_for('index'))
        try:"""
content = content.replace(search_tunalaras, replace_tunalaras)

# 3. Fix CSRF token in /slb/tunalaras
content = content.replace('csrf_token=lambda: "",', 'csrf_token=generate_csrf,')

# 4. Guard /guru/iep endpoint
search_iep = """@app.route('/guru/iep', methods=['POST'])
@limiter.limit("10 per hour")
def generate_iep():
    student_name = request.form.get('student_name')"""
replace_iep = """@app.route('/guru/iep', methods=['POST'])
@limiter.limit("10 per hour")
def generate_iep():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return "Unauthorized", 403
    student_name = request.form.get('student_name')"""
content = content.replace(search_iep, replace_iep)

# 5. Update /therapy/log
search_therapy_log = """@app.route('/therapy/log', methods=['POST'])
def therapy_log():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    try:
        req_date = request.form['date']
        req_time = request.form['time']
        from datetime import datetime as dt_module
        try:
            occurred_at_val = dt_module.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            occurred_at_val = dt_module.now()

        log = EpilepsiLog(
            occurred_at=occurred_at_val,
            trigger=request.form['trigger'],
            notes=request.form['notes'],
            anak_id=session.get('anak_id') if session.get('peran') == 'orang_tua' else None
        )"""
replace_therapy_log = """@app.route('/therapy/log', methods=['POST'])
@limiter.limit('10 per minute')
def therapy_log():
    if not session.get('user_id'):
        return redirect(url_for('index'))

    peran = session.get('peran')
    if peran not in ['orang_tua', 'guru', 'kepala_sekolah']:
        return "Unauthorized", 403

    if peran == 'orang_tua':
        anak_id = session.get('anak_id')
    else:
        anak_id = request.form.get('anak_id_guru') or request.form.get('anak_id')

    if not anak_id:
        return "anak_id is required", 400

    try:
        req_date = request.form['date']
        req_time = request.form['time']
        from datetime import datetime as dt_module
        try:
            occurred_at_val = dt_module.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            occurred_at_val = dt_module.now()

        log = EpilepsiLog(
            occurred_at=occurred_at_val,
            trigger=validate_str(request.form.get('trigger'), 500),
            notes=validate_str(request.form.get('notes'), 1000),
            anak_id=anak_id
        )"""
content = content.replace(search_therapy_log, replace_therapy_log)

# 6. Fix filename collisions
# Already done mostly in uploads and karya, let's do search replace
content = content.replace('filename = secure_filename(file.filename)', 'filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"')

# 7. Fix update_profil_medis logic
search_profil = """@app.route('/api/profil-medis/<int:siswa_id>', methods=['POST'])
def update_profil_medis(siswa_id):
    if session.get('peran') != 'orang_tua' or str(session.get('anak_id')) != str(siswa_id):
        return jsonify({'error': 'Unauthorized'}), 403"""
replace_profil = """@app.route('/api/profil-medis/<int:siswa_id>', methods=['POST'])
def update_profil_medis(siswa_id):
    peran = session.get('peran')
    if peran == 'orang_tua':
        if str(session.get('anak_id')) != str(siswa_id):
            return jsonify({'error': 'Unauthorized'}), 403
    elif peran in ['guru', 'kepala_sekolah'] or session.get('is_admin'):
        pass
    else:
        return jsonify({'error': 'Unauthorized'}), 403"""
content = content.replace(search_profil, replace_profil)

# 8. Fix download_modul boolean logic
search_modul = """@app.route('/orang-tua/modul/download')
def download_modul():
    if not session.get('peran') and not session.get('is_admin'):
        return "Unauthorized", 403"""
replace_modul = """@app.route('/orang-tua/modul/download')
def download_modul():
    if session.get('peran') not in ['guru', 'kepala_sekolah', 'orang_tua'] and not session.get('is_admin'):
        return "Unauthorized", 403"""
content = content.replace(search_modul, replace_modul)

# 9. Reject SVG uploads
search_svg_port = """            ext = filename.rsplit('.', 1)[1].lower()
            video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpeg'}

            if ext in video_extensions or ext == 'svg':
                file.save(filepath)"""
replace_svg_port = """            ext = filename.rsplit('.', 1)[1].lower()
            if ext == 'svg':
                return 'SVG uploads not permitted', 400

            video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpeg'}

            if ext in video_extensions:
                file.save(filepath)"""
content = content.replace(search_svg_port, replace_svg_port)

search_svg_karya = """            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if filename.rsplit('.', 1)[1].lower() == 'mp4':"""
replace_svg_karya = """            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            ext = filename.rsplit('.', 1)[1].lower()
            if ext == 'svg':
                return 'SVG uploads not permitted', 400

            if ext == 'mp4':"""
content = content.replace(search_svg_karya, replace_svg_karya)

# 10. Fix path traversal in /uploads/<path:filename>
search_uploads = """@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if secure_filename(os.path.basename(filename)) != os.path.basename(filename):
        return "Invalid filename", 400
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)"""
replace_uploads = """@app.route('/uploads/<filename>')
def uploaded_file(filename):
    secure_name = secure_filename(filename)
    if not secure_name or secure_name != filename:
        return "Invalid filename", 400
    response = send_from_directory(app.config['UPLOAD_FOLDER'], secure_name, max_age=31536000)"""
content = content.replace(search_uploads, replace_uploads)

# 11. Implement validate_str(value, max_len=500) utility
utility = """
def validate_str(value, max_len=500):
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    return val_str[:max_len]
"""
import_end = content.find("from flask_wtf.csrf import CSRFProtect")
import_end = content.find("\n", import_end)
content = content[:import_end+1] + utility + content[import_end+1:]

search_update_profil = """    profil.nama_lengkap = data.get('nama_lengkap', profil.nama_lengkap)
    profil.nama_panggilan = data.get('nama_panggilan', profil.nama_panggilan)

    usia_val = data.get('usia')
    if usia_val is not None and usia_val != '':
        try:
            profil.usia = int(usia_val)
        except ValueError:
            pass

    profil.kelas = data.get('kelas', profil.kelas)
    profil.jenis_slb = data.get('jenis_slb', profil.jenis_slb)
    profil.kategori_hambatan = data.get('kategori_hambatan', profil.kategori_hambatan)
    profil.diagnosis_utama = data.get('diagnosis_utama', profil.diagnosis_utama)
    profil.tingkat_hambatan = data.get('tingkat_hambatan', profil.tingkat_hambatan)
    profil.alergi_kritis = data.get('alergi_kritis', profil.alergi_kritis)
    profil.pemicu_tantrum = data.get('pemicu_tantrum', profil.pemicu_tantrum)
    profil.strategi_penenangan = data.get('strategi_penenangan', profil.strategi_penenangan)
    profil.kemampuan_komunikasi = data.get('kemampuan_komunikasi', profil.kemampuan_komunikasi)
    profil.hotline_darurat_nama = data.get('hotline_darurat_nama', profil.hotline_darurat_nama)
    profil.hotline_darurat_nomor = data.get('hotline_darurat_nomor', profil.hotline_darurat_nomor)
    profil.kondisi_terkini = data.get('kondisi_terkini', profil.kondisi_terkini)
    profil.kondisi_warna = data.get('kondisi_warna', profil.kondisi_warna)"""
replace_update_profil = """    profil.nama_lengkap = validate_str(data.get('nama_lengkap'), 255) or profil.nama_lengkap
    profil.nama_panggilan = validate_str(data.get('nama_panggilan'), 100) or profil.nama_panggilan

    usia_val = data.get('usia')
    if usia_val is not None and usia_val != '':
        try:
            profil.usia = int(usia_val)
        except ValueError:
            pass

    profil.kelas = validate_str(data.get('kelas'), 50) or profil.kelas
    profil.jenis_slb = validate_str(data.get('jenis_slb'), 100) or profil.jenis_slb
    profil.kategori_hambatan = validate_str(data.get('kategori_hambatan'), 100) or profil.kategori_hambatan
    profil.diagnosis_utama = validate_str(data.get('diagnosis_utama'), 1000) or profil.diagnosis_utama
    profil.tingkat_hambatan = validate_str(data.get('tingkat_hambatan'), 100) or profil.tingkat_hambatan
    profil.alergi_kritis = validate_str(data.get('alergi_kritis'), 500) or profil.alergi_kritis
    profil.pemicu_tantrum = validate_str(data.get('pemicu_tantrum'), 500) or profil.pemicu_tantrum
    profil.strategi_penenangan = validate_str(data.get('strategi_penenangan'), 1000) or profil.strategi_penenangan
    profil.kemampuan_komunikasi = validate_str(data.get('kemampuan_komunikasi'), 500) or profil.kemampuan_komunikasi
    profil.hotline_darurat_nama = validate_str(data.get('hotline_darurat_nama'), 255) or profil.hotline_darurat_nama
    profil.hotline_darurat_nomor = validate_str(data.get('hotline_darurat_nomor'), 50) or profil.hotline_darurat_nomor
    profil.kondisi_terkini = validate_str(data.get('kondisi_terkini'), 1000) or profil.kondisi_terkini
    profil.kondisi_warna = validate_str(data.get('kondisi_warna'), 20) or profil.kondisi_warna"""
content = content.replace(search_update_profil, replace_update_profil)

search_buku = """        db.session.add(OrangTuaBuku(
            anak_id=session.get('anak_id'),
            mood=data.get('mood'),
            sleep_duration=int(data.get('sleep_duration', 0)),
            morning_behavior=data.get('morning_behavior')
        ))"""
replace_buku = """        db.session.add(OrangTuaBuku(
            anak_id=session.get('anak_id'),
            mood=validate_str(data.get('mood'), 100),
            sleep_duration=int(data.get('sleep_duration', 0)),
            morning_behavior=validate_str(data.get('morning_behavior'), 500)
        ))"""
content = content.replace(search_buku, replace_buku)

search_nutrisi = """            db.session.add(OrangTuaNutrisi(
                anak_id=session.get('anak_id'),
                food_name=data.get('food_name'),
                has_allergen=data.get('has_allergen', False)
            ))"""
replace_nutrisi = """            db.session.add(OrangTuaNutrisi(
                anak_id=session.get('anak_id'),
                food_name=validate_str(data.get('food_name'), 255),
                has_allergen=data.get('has_allergen', False)
            ))"""
content = content.replace(search_nutrisi, replace_nutrisi)

# 12. Fix IDOR in upload_portfolio
search_idor = """            port = StudentPortfolio(
                student_id=request.form.get('student_id'),
                semester=request.form.get('semester'),
                filename=filename
            )
            db.session.add(port)"""
replace_idor = """            student_id = request.form.get('student_id')
            if not db.session.get(Siswa, student_id):
                return "Student not found", 404
            port = StudentPortfolio(
                student_id=student_id,
                semester=request.form.get('semester'),
                filename=filename
            )
            db.session.add(port)"""
content = content.replace(search_idor, replace_idor)

# 13. Replace bare except:
# 252
search_1 = """@cache.memoize(timeout=600)
def get_settings():
    try:
        settings = {item.key: item.value for item in AppSettings.query.all()}
    except:
        settings = {}
    return settings"""
replace_1 = """@cache.memoize(timeout=600)
def get_settings():
    try:
        settings = {item.key: item.value for item in AppSettings.query.all()}
    except Exception as e:
        app.logger.warning("Failed to fetch settings", exc_info=True)
        settings = {}
    return settings"""
content = content.replace(search_1, replace_1)

# 4109
search_2 = """    try:
        if session.get('peran') == 'orang_tua' and session.get('anak_id'):
            epilepsi_logs = EpilepsiLog.query.filter_by(anak_id=session.get('anak_id')).order_by(EpilepsiLog.created_at.desc()).limit(10).all()
        else:
            epilepsi_logs = EpilepsiLog.query.order_by(EpilepsiLog.created_at.desc()).limit(5).all()
    except:
        epilepsi_logs = []"""
replace_2 = """    try:
        if session.get('peran') == 'orang_tua' and session.get('anak_id'):
            epilepsi_logs = EpilepsiLog.query.filter_by(anak_id=session.get('anak_id')).order_by(EpilepsiLog.created_at.desc()).limit(10).all()
        else:
            epilepsi_logs = EpilepsiLog.query.order_by(EpilepsiLog.created_at.desc()).limit(5).all()
    except Exception as e:
        app.logger.warning("Failed to fetch epilepsi logs", exc_info=True)
        epilepsi_logs = []"""
content = content.replace(search_2, replace_2)

# 4965
search_3 = """        try:
            if log.start_time:
                dt = datetime.datetime.fromtimestamp(int(log.start_time) / 1000.0)
                display_time = dt.strftime("%H:%M")
        except:
            pass"""
replace_3 = """        try:
            if log.start_time:
                dt = datetime.datetime.fromtimestamp(int(log.start_time) / 1000.0)
                display_time = dt.strftime("%H:%M")
        except Exception as e:
            app.logger.warning("Failed to format date in report", exc_info=True)
            pass"""
content = content.replace(search_3, replace_3)

# 10260 (might be slightly different line number)
search_4 = """        subscriptions_data = []
        for sub in subscriptions:
            try:
                subscriptions_data.append(json.loads(sub.subscription_info))
            except:
                pass"""
replace_4 = """        subscriptions_data = []
        for sub in subscriptions:
            try:
                subscriptions_data.append(json.loads(sub.subscription_info))
            except Exception as e:
                app.logger.warning("Failed to parse subscription_info", exc_info=True)
                pass"""
content = content.replace(search_4, replace_4)

# 14. Protect /orang-tua/api/tantrum-profile
search_tantrum = """@app.route('/orang-tua/api/tantrum-profile')
def get_tantrum_profile():
    # In a real app, fetch based on student ID.
    # Here we return a static mock protocol written by a teacher."""
replace_tantrum = """@app.route('/orang-tua/api/tantrum-profile')
def get_tantrum_profile():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    # In a real app, fetch based on student ID.
    # Here we return a static mock protocol written by a teacher."""
content = content.replace(search_tantrum, replace_tantrum)

# 15. Filter data by anak_id in get_ot_chart_data
search_chart = """@app.route('/orang-tua/api/chart-data')
def get_ot_chart_data():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    q_buku = OrangTuaBuku.query
    if session.get('peran') == 'orang_tua':
        q_buku = q_buku.filter_by(anak_id=session.get('anak_id'))
    buku_logs = q_buku.order_by(OrangTuaBuku.created_at.desc()).limit(7).all()
    reaction_logs = ReactionTimeLog.query.order_by(ReactionTimeLog.created_at.desc()).limit(7).all()"""
replace_chart = """@app.route('/orang-tua/api/chart-data')
def get_ot_chart_data():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    q_buku = OrangTuaBuku.query
    q_reaction = ReactionTimeLog.query

    peran = session.get('peran')
    if peran == 'orang_tua':
        q_buku = q_buku.filter_by(anak_id=session.get('anak_id'))
        q_reaction = q_reaction.filter_by(anak_id=session.get('anak_id'))
    elif peran in ['guru', 'kepala_sekolah'] and request.args.get('anak_id'):
        q_buku = q_buku.filter_by(anak_id=request.args.get('anak_id'))
        q_reaction = q_reaction.filter_by(anak_id=request.args.get('anak_id'))

    buku_logs = q_buku.order_by(OrangTuaBuku.created_at.desc()).limit(7).all()
    reaction_logs = q_reaction.order_by(ReactionTimeLog.created_at.desc()).limit(7).all()"""
content = content.replace(search_chart, replace_chart)

# 16. Fix logout session cleanup
search_logout = """@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    session.pop('user_id', None)
    session.pop('peran', None)
    session.pop('anak_id', None)
    return redirect(url_for('index'))"""
replace_logout = """@app.route('/logout')
def logout():
    session.clear()
    session.modified = True
    return redirect(url_for('index'))"""
content = content.replace(search_logout, replace_logout)

# 17. Add rate-limit decorators
search_add_jadwal = """@app.route('/jadwal/add', methods=['POST'])
def add_jadwal():"""
replace_add_jadwal = """@app.route('/jadwal/add', methods=['POST'])
@limiter.limit('20 per minute')
def add_jadwal():"""
content = content.replace(search_add_jadwal, replace_add_jadwal)

search_galeri_upload = """@app.route('/galeri/upload', methods=['POST'])
def upload_karya():"""
replace_galeri_upload = """@app.route('/galeri/upload', methods=['POST'])
@limiter.limit('10 per minute')
def upload_karya():"""
content = content.replace(search_galeri_upload, replace_galeri_upload)

search_port_upload = """@app.route('/guru/portofolio/upload', methods=['POST'])
def upload_portfolio():"""
replace_port_upload = """@app.route('/guru/portofolio/upload', methods=['POST'])
@limiter.limit('10 per minute')
def upload_portfolio():"""
content = content.replace(search_port_upload, replace_port_upload)


with open(filename, 'w') as f:
    f.write(content)
