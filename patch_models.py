import sys

filepath = "kampus-stie-samarinda-0 ( idcloudhost - 3 dashboard utama - tu, mahasiswa dan dosen ).py"

with open(filepath, 'r') as f:
    content = f.read()

models_code = """
class SuratOtomatis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), nullable=False)
    jenis_surat = db.Column(db.String(255), nullable=False)
    keterangan = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Menunggu Acc')
    tanggal = db.Column(db.String(255), default=lambda: str(datetime.date.today()))
    qr_code = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())

class PendaftaranPMB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    foto_ijazah = db.Column(db.String(255))
    foto_ktp = db.Column(db.String(255))
    bukti_transfer = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Pending')
    npm_generated = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())

class TagihanKuliah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), nullable=False)
    jenis_tagihan = db.Column(db.String(255), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    bukti_transfer = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Belum Lunas')
    created_at = db.Column(db.DateTime, server_default=func.now())

class JadwalKuliah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hari = db.Column(db.String(50), nullable=False)
    jam = db.Column(db.String(50), nullable=False)
    mata_kuliah = db.Column(db.String(255), nullable=False)
    dosen = db.Column(db.String(255), nullable=False)
    ruangan = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    nama = db.Column(db.String(255))
    status_akademik = db.Column(db.String(50), default='Aktif')
    created_at = db.Column(db.DateTime, server_default=func.now())

class LaciArsip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), nullable=False)
    nama_dokumen = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    ukuran = db.Column(db.String(50))
    tanggal = db.Column(db.String(255), default=lambda: str(datetime.date.today()))
"""

# Insert right before AppSettings
target = "class AppSettings(db.Model):"
if target in content and "class SuratOtomatis" not in content:
    new_content = content.replace(target, models_code + "\n" + target)
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("Models inserted.")
else:
    print("Target not found or models already inserted.")
