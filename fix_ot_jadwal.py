import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """        try:
            data = request.json
            db.session.add(OrangTuaJadwal(
                anak_id=session.get('anak_id'),
                schedule_time=data.get('time'),
                medication_name=data.get('medication_name')
            ))
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500"""

replacement = """        try:
            data = request.json
            anak_id = session.get('anak_id')
            if anak_id and not db.session.get(Siswa, anak_id):
                return jsonify({'error': 'Data siswa tidak ditemukan'}), 404

            time_str = data.get('time', '')
            try:
                parts = time_str.split(':')
                schedule_time = dt_time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError, AttributeError):
                return jsonify({'error': 'Format waktu tidak valid (HH:MM)'}), 400

            med_name = validate_str(data.get('medication_name'), 255)
            if not med_name:
                return jsonify({'error': 'Nama obat harus diisi'}), 400

            db.session.add(OrangTuaJadwal(
                anak_id=anak_id,
                schedule_time=schedule_time,
                medication_name=med_name
            ))
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            app.logger.error('Failed to handle OT jadwal', exc_info=True)
            return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
