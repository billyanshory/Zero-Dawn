import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

# ProfilMedisSiswa.updated_at
content = content.replace(
    "updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=datetime.datetime.now)",
    "updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())"
)

# EpilepsiLog.occurred_at
content = content.replace(
    "occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)",
    "occurred_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), index=True)"
)

# TantrumLog.start_time & duration_ms
content = content.replace(
    "start_time = db.Column(db.DateTime, nullable=True, default=datetime.datetime.now)",
    "start_time = db.Column(db.DateTime, nullable=True, server_default=func.now())"
)
content = content.replace(
    "duration_ms = db.Column(db.Integer)",
    "duration_ms = db.Column(db.Integer, nullable=False, default=0) # TODO: Add nullable=False after data migration"
)

# OrangTuaBuku.mood
content = content.replace(
    "mood = db.Column(db.String(255))",
    "mood = db.Column(db.String(255), nullable=False) # TODO: Add nullable=False after data migration"
)

# OrangTuaTantrum.trigger
content = content.replace(
    "trigger = db.Column(db.String(255))",
    "trigger = db.Column(db.String(255), nullable=False) # TODO: Add nullable=False after data migration"
)

# StudentPortfolio.student_id
content = content.replace(
    "student_id = db.Column(db.String(255), nullable=False, index=True)",
    "student_id = db.Column(db.String(255), nullable=False, index=True) # TODO L1-020: Migrate student_id from String(255) to Integer with ForeignKey('siswa.id')"
)

with open(file_path, "w") as f:
    f.write(content)
print("Replaced model constraints successfully")
