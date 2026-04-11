import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """@app.route('/galeri/upload', methods=['POST'])
@limiter.limit('10 per minute')
def upload_karya():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('galeri_karya'))

    title = request.form.get('title')
    student_name = request.form.get('student_name')
    file = request.files.get('image')

    if file and allowed_file(file.filename):
        try:"""

replacement = """@app.route('/galeri/upload', methods=['POST'])
@limiter.limit('10 per minute')
def upload_karya():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('galeri_karya'))

    title = validate_str(request.form.get('title'), 255)
    student_name = validate_str(request.form.get('student_name'), 255)
    file = request.files.get('image')

    if not title or not student_name:
        from flask import flash
        flash('Judul dan nama siswa harus diisi.', 'error')
        return redirect(url_for('galeri_karya'))

    if file and allowed_file(file.filename):
        try:"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced upload_karya top successfully")
else:
    print("Target top not found")

with open(file_path, "r") as f:
    content = f.read()

target2 = """            new_karya = GaleriKarya(image_filename=filename, title=title, student_name=student_name)
            db.session.add(new_karya)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

    return redirect(url_for('galeri_karya'))"""

replacement2 = """            new_karya = GaleriKarya(image_filename=filename, title=title, student_name=student_name)
            db.session.add(new_karya)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Gallery upload failed', exc_info=True)
            from flask import flash
            flash('Gagal mengunggah karya. Silakan coba lagi.', 'error')

    return redirect(url_for('galeri_karya'))"""

if target2 in content:
    content = content.replace(target2, replacement2)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced upload_karya bottom successfully")
else:
    print("Target bottom not found")
