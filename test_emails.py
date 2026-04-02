import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

print("Has tagihan > 0:", "int(jumlah) <= 0:" in code)
print("Has has_unpaid empty fix:", "has_unpaid = True if not tagihan_list else any" in code)
print("Has email on lunas:", "send_email_notification(user_pmb.email" in code)
print("Has dosen krs logic:", "krs.dosen == current_user.nama" in code)
print("Has krs npm validation:", "krs_check = KRSMahasiswa.query.filter_by(npm=npm, mata_kuliah=mata_kuliah, status='Disetujui Dosen').first()" in code)
print("Has presensi IntegrityError:", "except db.exc.IntegrityError:" in code)
print("Has surat nama_lengkap:", "user_obj = User.query.filter_by(username=surat.npm).first()" in code)
