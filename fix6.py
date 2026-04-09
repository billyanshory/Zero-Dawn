import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 6. Eager loading
    # AkunPengguna relationships
    if "anak = db.relationship('Siswa', lazy='select')" not in content:
        # Actually let's check what is in AkunPengguna
        pass

    content = content.replace(
        "AkunPengguna.query.filter_by(status_akun='menunggu_verifikasi').all()",
        "AkunPengguna.query.options(joinedload(AkunPengguna.anak)).filter_by(status_akun='menunggu_verifikasi').limit(200).all()"
    )
    content = content.replace(
        "AkunPengguna.query.filter_by(status_akun='disetujui').all()",
        "AkunPengguna.query.options(joinedload(AkunPengguna.anak)).filter_by(status_akun='disetujui').limit(200).all()"
    )

    # 8. Font Awesome
    content = content.replace(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"',
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/solid.min.css"'
    )

    # 9. Google Fonts
    content = content.replace(
        'family=Poppins:wght@300;400;500;600;700&family=Amiri:wght@400;700&display=swap',
        'family=Poppins:wght@400;600;700&display=swap'
    )

    # Needs to dynamically add Amiri back in the Ramadhan dashboard template
    # Let's check RAMADHAN_DASHBOARD_HTML or similar

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
