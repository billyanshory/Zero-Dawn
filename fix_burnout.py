import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """    try:
        data = request.json
        db.session.add(OrangTuaBurnout(
            anak_id=session.get('anak_id'),
            stress_level=int(data.get('stress_level', 5)),
            recorded_date=datetime.date.today()
        ))
        db.session.commit()
        return jsonify({"status": "success"})"""

replacement = """    try:
        data = request.json
        anak_id = session.get('anak_id')
        if anak_id and not db.session.get(Siswa, anak_id):
            return jsonify({'error': 'Data siswa tidak ditemukan'}), 404

        stress = int(data.get('stress_level', 5))
        stress = max(1, min(10, stress))

        db.session.add(OrangTuaBurnout(
            anak_id=anak_id,
            stress_level=stress,
            recorded_date=datetime.date.today()
        ))
        db.session.commit()
        return jsonify({"status": "success"})"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced burnout successfully")
else:
    print("Target burnout not found")
