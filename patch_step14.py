with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

# Fix encryption
search_cols = """    kelas: Mapped[str | None] = mapped_column(db.String(50))
    jenis_slb: Mapped[str | None] = mapped_column(db.String(100))"""
replace_cols = """    kelas: Mapped[str | None] = mapped_column(EncryptedType(db.String(128), _PRIMARY_FIELD_KEY, AesGcmEngine, 'pkcs5'))
    jenis_slb: Mapped[str | None] = mapped_column(EncryptedType(db.String(256), _PRIMARY_FIELD_KEY, AesGcmEngine, 'pkcs5'))"""

# Fix keys logic
search_keys = """def _load_field_keys():
    keys_str = os.getenv('FIELD_ENCRYPTION_KEYS')
    if not keys_str:
        raise RuntimeError("FIELD_ENCRYPTION_KEYS environment variable is missing or empty.")
    return keys_str.split(',')

_PRIMARY_FIELD_KEY = _load_field_keys()[0]"""

replace_keys = """def _load_field_keys():
    keys_str = os.getenv('FIELD_ENCRYPTION_KEYS', '')
    if not keys_str:
        raise RuntimeError("FIELD_ENCRYPTION_KEYS environment variable is missing or empty.")
    return [k.strip().encode() for k in keys_str.split(',')]

_FIELD_KEYS = _load_field_keys()
_PRIMARY_FIELD_KEY = _FIELD_KEYS[0]
# Note: _FIELD_KEYS can be wrapped in MultiFernet(_FIELD_KEYS) by manual re-encryption scripts when rotation is performed."""

if search_cols in text and search_keys in text:
    text = text.replace(search_cols, replace_cols)
    text = text.replace(search_keys, replace_keys)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
