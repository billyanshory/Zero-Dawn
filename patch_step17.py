with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    subscription_info: Mapped[str] = mapped_column(EncryptedType(db.Text, _PRIMARY_FIELD_KEY, AesGcmEngine, 'pkcs5'), nullable=False)
    endpoint_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)

class IEPDownloadAudit(db.Model):
    __tablename__ = 'iep_download_audit'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    downloaded_by: Mapped[int | None] = mapped_column(db.Integer, db.ForeignKey('akun_pengguna.id'), nullable=True)
    student_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    downloaded_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    request_id: Mapped[str | None] = mapped_column(db.String(100))
    ip: Mapped[str | None] = mapped_column(db.String(100))

    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    last_used = db.Column(db.DateTime, server_default=func.now())"""

replace = """class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    subscription_info: Mapped[str] = mapped_column(EncryptedType(db.Text, _PRIMARY_FIELD_KEY, AesGcmEngine, 'pkcs5'), nullable=False)
    endpoint_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    last_used = db.Column(db.DateTime, server_default=func.now())

class IEPDownloadAudit(db.Model):
    __tablename__ = 'iep_download_audit'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    downloaded_by: Mapped[int | None] = mapped_column(db.Integer, db.ForeignKey('akun_pengguna.id'), nullable=True)
    student_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    downloaded_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    request_id: Mapped[str | None] = mapped_column(db.String(100))
    ip: Mapped[str | None] = mapped_column(db.String(100))"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
