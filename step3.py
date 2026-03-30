with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Update Cache
content = content.replace(
    "cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 86400})",
    "cache = Cache(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'), 'CACHE_DEFAULT_TIMEOUT': 86400})"
)

# 2. Add Relationships
user_model_end = "    created_at = db.Column(db.DateTime, server_default=func.now())"
rel_code = """    created_at = db.Column(db.DateTime, server_default=func.now())

    krs_rel = db.relationship('KRSMahasiswa', backref='user_krs', primaryjoin="User.username == foreign(KRSMahasiswa.npm)")
    tagihan_rel = db.relationship('TagihanKuliah', backref='user_tagihan', primaryjoin="User.username == foreign(TagihanKuliah.npm)")"""
content = content.replace(user_model_end, rel_code, 1)

# 3. Update Joinedload
content = content.replace(
    "krs_raw = KRSMahasiswa.query.filter_by(dosen=dosen_name).order_by(KRSMahasiswa.id.desc()).all()",
    "krs_raw = KRSMahasiswa.query.options(joinedload(KRSMahasiswa.user_krs)).filter_by(dosen=dosen_name).order_by(KRSMahasiswa.id.desc()).all()"
)

# 4. Add Caching to tu/arsip/search
content = content.replace(
    "@app.route('/tu/arsip/search', methods=['GET'])\ndef tu_arsip_search():",
    "@app.route('/tu/arsip/search', methods=['GET'])\n@cache.cached(timeout=60, query_string=True)\ndef tu_arsip_search():"
)

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
