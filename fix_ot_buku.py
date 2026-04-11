import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """        data = request.json
        db.session.add(OrangTuaBuku(
            anak_id=session.get('anak_id'),
            mood=validate_str(data.get('mood'), 100),
            sleep_duration=int(data.get('sleep_duration', 0)),
            morning_behavior=validate_str(data.get('morning_behavior'), 500)
        ))
        db.session.commit()
        return jsonify({"status": "success"})"""

replacement = """        data = request.json
        anak_id = session.get('anak_id')
        if anak_id and not db.session.get(Siswa, anak_id):
            return jsonify({'error': 'Data siswa tidak ditemukan'}), 404

        sleep_dur = int(data.get('sleep_duration', 0))
        sleep_dur = max(0, min(24, sleep_dur))

        db.session.add(OrangTuaBuku(
            anak_id=anak_id,
            mood=validate_str(data.get('mood'), 100),
            sleep_duration=sleep_dur,
            morning_behavior=validate_str(data.get('morning_behavior'), 500)
        ))
        db.session.commit()
        return jsonify({"status": "success"})"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced ot_buku successfully")
else:
    print("Target ot_buku not found")
