fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Make sure we add the specific comment required for `profil_medis` query exactly where it is used in `orang_tua_dashboard`.
lines = content.split('\n')
for i, line in enumerate(lines):
    if "profil_medis = ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first()" in line:
        if "# Result may be None" not in line:
            lines[i] = line + "  # Result may be None for students with no medical profile; template guards handle this via conditional rendering"

with open(fname, 'w') as f:
    f.write("\n".join(lines))
