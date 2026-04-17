import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# 1. Define exception and helper near the top
helper_code = """
class UploadValidationError(Exception):
    pass

def _save_uploaded_media(file, upload_folder, video_extensions=frozenset({'mp4'})):
    if not file or file.filename == '':
        raise UploadValidationError("File tidak valid atau kosong.")
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    file_bytes = file.read()
    file.seek(0)

    kind = filetype.guess(file_bytes)
    if not kind:
        if ext == 'svg':
            raise UploadValidationError("File SVG tidak diperbolehkan demi keamanan.")
        raise UploadValidationError("Tipe file tidak dikenali.")

    if kind.extension in video_extensions:
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(file_bytes)
        return filename

    if kind.extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        raise UploadValidationError("Format file tidak didukung.")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail((800, 800))
        compressed_bytes = eventlet.tpool.execute(_compress_image_to_bytes, img, 500*1024)
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(compressed_bytes)
        return filename
    except Exception as e:
        raise UploadValidationError("Gagal memproses gambar.")
"""

# Insert after constants block
idx = content.find("ALL_STATUSES = frozenset({STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK})")
if idx != -1:
    end_line = content.find("\n", idx)
    content = content[:end_line+1] + "\n" + helper_code + "\n" + content[end_line+1:]

# We need to extract the existing behavior and replace upload_portfolio & upload_karya.
# Rather than parsing the huge methods, it is safer to regex replace their entire bodies.

def replace_method(name, code, text):
    pattern = r"def " + name + r"\(.*?\):\n(?:(?:\s+.*?\n)|\n)+"
    # We find the definition and replace it up to the next non-indented def
    # Regex is tricky. Let's do it line by line.
    lines = text.split("\n")
    i = 0
    start = -1
    while i < len(lines):
        if lines[i].startswith("def " + name + "("):
            start = i
            break
        i += 1

    if start == -1:
        return text

    i = start + 1
    while i < len(lines):
        if lines[i].strip() == "" or lines[i].startswith(" ") or lines[i].startswith("\t"):
            i += 1
        else:
            break

    end = i

    return "\n".join(lines[:start]) + "\n" + code + "\n" + "\n".join(lines[end:])

portfolio_code = """def upload_portfolio(anak_id):
    student = Siswa.query.get(anak_id)
    if not student:
        flash("Siswa tidak ditemukan.", "error")
        return redirect(url_for('orang_tua_dashboard'))

    if 'file' not in request.files:
        flash("Tidak ada file yang dipilih.", "error")
        return redirect(url_for('orang_tua_dashboard'))

    file = request.files['file']
    # upload_portfolio uses a broader set of video extensions
    # (preserve this intentional difference)
    try:
        filename = _save_uploaded_media(file, app.config['UPLOAD_FOLDER'], video_extensions=frozenset({'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp'}))

        new_portfolio = PortofolioSiswa(
            siswa_id=anak_id,
            judul=validate_str(request.form.get('judul', 'Karya Tanpa Judul')),
            deskripsi=validate_str(request.form.get('deskripsi', '')),
            file_url=filename,
            uploaded_by=session.get('user_id')
        )
        db.session.add(new_portfolio)
        db.session.commit()
        flash("Karya berhasil diunggah!", "success")
    except UploadValidationError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        app.logger.error("Error saving portfolio", exc_info=True)
        flash("Terjadi kesalahan sistem.", "error")

    return redirect(url_for('orang_tua_dashboard'))"""

karya_code = """def upload_karya():
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file'}), 400

    file = request.files['file']
    # upload_karya defaults to mp4 only
    # (preserve this intentional difference)
    try:
        filename = _save_uploaded_media(file, app.config['UPLOAD_FOLDER'])

        new_karya = KaryaSiswa(
            judul=validate_str(request.form.get('judul', 'Tanpa Judul')),
            file_url=filename,
            uploaded_by=session.get('user_id')
        )
        db.session.add(new_karya)
        db.session.commit()
        return jsonify({'message': 'Berhasil diunggah', 'file_url': filename})
    except UploadValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error("Error saving karya", exc_info=True)
        return jsonify({'error': 'Terjadi kesalahan sistem'}), 500"""

content = replace_method("upload_portfolio", portfolio_code, content)
content = replace_method("upload_karya", karya_code, content)

with open(fname, 'w') as f:
    f.write(content)
