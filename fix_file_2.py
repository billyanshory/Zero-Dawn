import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

content = re.sub(r'class EmotionJournal\(db\.Model\):.*?notes = db\.Column\(db\.Text\)',
r'''class EmotionJournal(db.Model):
    __tablename__ = 'emotion_journal'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, server_default=func.now())
    emotion = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)''', content, flags=re.DOTALL)

content = re.sub(r'class EpilepsiLog\(db\.Model\):.*?created_at = db\.Column\(db\.DateTime, server_default=func\.now\(\), index=True\)',
r'''class EpilepsiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(255), nullable=False)
    trigger = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)''', content, flags=re.DOTALL)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
