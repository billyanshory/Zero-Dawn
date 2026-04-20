with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """        if akun and check_password_hash(akun.password_hash, password):
            if akun.status_akun == STATUS_DISETUJUI:"""

replace = """        if akun and check_password_hash(akun.password_hash, password):
            if not akun.password_hash.startswith('scrypt:'):
                try:
                    akun.password_hash = generate_password_hash(password, method='scrypt:32768:8:1')
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    app.logger.warning(f"Failed to transparently re-hash password for user {akun.id}")

            if akun.status_akun == STATUS_DISETUJUI:"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
