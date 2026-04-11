import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """class Siswa(db.Model):
    __tablename__ = 'siswa'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    kelas = db.Column(db.String(255))
    diagnosis = db.Column(db.String(255))"""

replacement = """class Siswa(db.Model):
    __tablename__ = 'siswa'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    kelas = db.Column(db.String(255))
    diagnosis = db.Column(db.String(255))
    profil_medis = db.relationship('ProfilMedisSiswa', backref='siswa', cascade='all, delete-orphan', uselist=False)
    emotion_journals = db.relationship('EmotionJournal', backref='siswa', cascade='all, delete-orphan')
    epilepsi_logs = db.relationship('EpilepsiLog', backref='siswa', cascade='all, delete-orphan')
    buku_entries = db.relationship('OrangTuaBuku', backref='siswa', cascade='all, delete-orphan')
    tantrum_entries = db.relationship('OrangTuaTantrum', backref='siswa', cascade='all, delete-orphan')
    jadwal_entries = db.relationship('OrangTuaJadwal', backref='siswa', cascade='all, delete-orphan')
    nutrisi_entries = db.relationship('OrangTuaNutrisi', backref='siswa', cascade='all, delete-orphan')
    burnout_entries = db.relationship('OrangTuaBurnout', backref='siswa', cascade='all, delete-orphan')"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
