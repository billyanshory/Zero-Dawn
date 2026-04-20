with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """class AkunPengguna(db.Model):
    __tablename__ = 'akun_pengguna'
    __table_args__ = (
        # Index('idx_akun_pengguna_status_akun', 'status_akun'), Index('idx_akun_pengguna_anak_id', 'anak_id'),
        )
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    is_deleted: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

class ConsentRecord(db.Model):
    __tablename__ = 'consent_record'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    akun_id: Mapped[int | None] = mapped_column(db.Integer, db.ForeignKey('akun_pengguna.id'), nullable=True, index=True)
    policy_version: Mapped[str] = mapped_column(db.String(32), nullable=False)
    granted_at = db.Column(db.DateTime, server_default=func.now())
    withdrawn_at = db.Column(db.DateTime, nullable=True)
    consent_ip: Mapped[str | None] = mapped_column(db.String(100))
    scope: Mapped[str] = mapped_column(db.String(128), nullable=False)
    nik: Mapped[str] = mapped_column(EncryptedType(db.String(128), _PRIMARY_FIELD_KEY, AesGcmEngine, 'pkcs5'), nullable=False)
    nik_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
    tanggal_lahir: Mapped[datetime.date | None] = mapped_column(db.Date, nullable=True)
    nama_lengkap: Mapped[str] = mapped_column(db.String(255), nullable=False)
    username: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    peran = db.Column(db.Enum(ROLE_ORANG_TUA, ROLE_GURU, ROLE_KEPALA_SEKOLAH, name='peran_akun_enum'), nullable=False)
    status_akun = db.Column(db.Enum(STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK, name='status_akun_enum'), default=STATUS_MENUNGGU, index=True)
    anak_id: Mapped[int | None] = mapped_column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)"""

replace = """class AkunPengguna(db.Model):
    __tablename__ = 'akun_pengguna'
    __table_args__ = (
        Index('idx_akun_pengguna_status_akun', 'status_akun'), Index('idx_akun_pengguna_anak_id', 'anak_id'),
    )
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    nik: Mapped[str] = mapped_column(EncryptedType(db.String(128), _PRIMARY_FIELD_KEY, AesGcmEngine, 'pkcs5'), nullable=False)
    nik_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
    tanggal_lahir: Mapped[datetime.date | None] = mapped_column(db.Date, nullable=True)
    nama_lengkap: Mapped[str] = mapped_column(db.String(255), nullable=False)
    username: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    peran = db.Column(db.Enum(ROLE_ORANG_TUA, ROLE_GURU, ROLE_KEPALA_SEKOLAH, name='peran_akun_enum'), nullable=False)
    status_akun = db.Column(db.Enum(STATUS_MENUNGGU, STATUS_DISETUJUI, STATUS_DITOLAK, name='status_akun_enum'), default=STATUS_MENUNGGU, index=True)
    anak_id: Mapped[int | None] = mapped_column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

class ConsentRecord(db.Model):
    __tablename__ = 'consent_record'
    __table_args__ = (Index('idx_consent_akun', 'akun_id'),)
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    akun_id: Mapped[int | None] = mapped_column(db.Integer, db.ForeignKey('akun_pengguna.id'), nullable=True, index=True)
    policy_version: Mapped[str] = mapped_column(db.String(32), nullable=False)
    granted_at = db.Column(db.DateTime, server_default=func.now())
    withdrawn_at = db.Column(db.DateTime, nullable=True)
    consent_ip: Mapped[str | None] = mapped_column(db.String(100))
    scope: Mapped[str] = mapped_column(db.String(128), nullable=False)"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Not found")
