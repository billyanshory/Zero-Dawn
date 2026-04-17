fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Ah! The constant declarations themselves got replaced.
# Let's fix the declarations.
# In constants_block, we had ROLE_ORANG_TUA = 'orang_tua'
# Which got replaced to ROLE_ORANG_TUA = ROLE_ORANG_TUA

replacements = [
    ("ROLE_ORANG_TUA = ROLE_ORANG_TUA", "ROLE_ORANG_TUA = 'orang_tua'"),
    ("ROLE_GURU = ROLE_GURU", "ROLE_GURU = 'guru'"),
    ("ROLE_KEPALA_SEKOLAH = ROLE_KEPALA_SEKOLAH", "ROLE_KEPALA_SEKOLAH = 'kepala_sekolah'"),
    ("STATUS_MENUNGGU = STATUS_MENUNGGU", "STATUS_MENUNGGU = 'menunggu_verifikasi'"),
    ("STATUS_DISETUJUI = STATUS_DISETUJUI", "STATUS_DISETUJUI = 'disetujui'"),
    ("STATUS_DITOLAK = STATUS_DITOLAK", "STATUS_DITOLAK = 'ditolak'")
]

for old, new in replacements:
    content = content.replace(old, new)

with open(fname, 'w') as f:
    f.write(content)
