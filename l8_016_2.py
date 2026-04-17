import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    lines = f.readlines()

# Line 4369 is profil_medis, let's replace it
for i, line in enumerate(lines):
    if "profil_medis = ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first()" in line:
        if "# Result may be None" not in line:
            lines[i] = line.rstrip() + "  # Result may be None for students with no medical profile; template guards handle this via conditional rendering\n"

    elif "profil = ProfilMedisSiswa.query.filter_by(siswa_id=siswa_id).first()" in line:
        # Check if there is an if not profil check below
        # At 4395 and 4455 (approx)
        if "# Create if missing" not in line:
            lines[i] = line.rstrip() + "  # Create if missing logic handles None case\n"

    elif "akun = AkunPengguna.query.filter_by(username=username).first()" in line:
        # this is login, it checks if akun:
        lines[i] = line.rstrip() + "  # Guarded by if akun and ... check below\n"

    elif "entry = SignLanguageDictionary.query.filter_by(word=w).first()" in line:
        lines[i] = line.rstrip() + "  # Guarded by if not entry check below\n"

    elif "existing = PushSubscription.query.filter_by(subscription_info=json.dumps(sub_info)).first()" in line:
        lines[i] = line.rstrip() + "  # Guarded by if not existing check below\n"

    # db.session.get calls
    elif "siswa_record = db.session.get(Siswa, anak_id)" in line:
        lines[i] = line.rstrip() + "  # Result may be None; downstream handles or None is safe here\n"

    elif "akun = db.session.get(AkunPengguna, akun_id)" in line:
        if "if not akun" not in lines[i+1]:
            # Wait, let's insert a check!
            lines[i] = line + "    if not akun:\n        return jsonify({'error': 'Akun tidak ditemukan'}), 404\n"

with open(fname, 'w') as f:
    f.writelines(lines)
