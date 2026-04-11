import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """    try:
        hari = request.form.get('hari')
        jam = request.form.get('jam')
        mata_pelajaran = request.form.get('mata_pelajaran')
        guru = request.form.get('guru')
        ruangan = request.form.get('ruangan')

        new_jadwal = JadwalKelas(hari=hari, jam=jam, mata_pelajaran=mata_pelajaran, guru=guru, ruangan=ruangan)
        db.session.add(new_jadwal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return redirect(url_for('jadwal_kelas'))"""

replacement = """    try:
        hari = validate_str(request.form.get('hari'), 50)
        jam = validate_str(request.form.get('jam'), 50)
        mata_pelajaran = validate_str(request.form.get('mata_pelajaran'), 255)
        guru = validate_str(request.form.get('guru'), 255)
        ruangan = validate_str(request.form.get('ruangan'), 255)

        if not all([hari, jam, mata_pelajaran, guru, ruangan]):
            from flask import flash
            flash('Semua field harus diisi.', 'error')
            return redirect(url_for('jadwal_kelas'))

        new_jadwal = JadwalKelas(hari=hari, jam=jam, mata_pelajaran=mata_pelajaran, guru=guru, ruangan=ruangan)
        db.session.add(new_jadwal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error('Failed to add jadwal', exc_info=True)
        from flask import flash
        flash('Gagal menambahkan jadwal. Silakan coba lagi.', 'error')

    return redirect(url_for('jadwal_kelas'))"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
