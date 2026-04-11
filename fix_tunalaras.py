import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """        try:
            emotion = request.form['emotion']
            anak_id = session.get('anak_id') if session.get('peran') == 'orang_tua' else None
            db.session.add(EmotionJournal(emotion=emotion, anak_id=anak_id))
            db.session.commit()
            return redirect(url_for('slb_tunalaras'))"""

replacement = """        try:
            emotion = validate_str(request.form.get('emotion'), 50)
            if not emotion:
                return "Emosi harus dipilih.", 400

            anak_id = session.get('anak_id') if session.get('peran') == 'orang_tua' else None
            if anak_id and not db.session.get(Siswa, anak_id):
                return "Data siswa tidak ditemukan.", 404

            db.session.add(EmotionJournal(emotion=emotion, anak_id=anak_id))
            db.session.commit()
            return redirect(url_for('slb_tunalaras'))"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
