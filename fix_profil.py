import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """    profil.kondisi_warna = validate_str(data.get('kondisi_warna'), 20) or profil.kondisi_warna

    db.session.commit()
    return jsonify({'status': 'success'})"""

replacement = """    profil.kondisi_warna = validate_str(data.get('kondisi_warna'), 20) or profil.kondisi_warna

    try:
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        app.logger.error('Medical profile update failed', exc_info=True)
        return jsonify({'error': 'Gagal menyimpan data medis.'}), 500"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
