import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """        akun = AkunPengguna(
            nik=nik,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=hashed_password,
            peran=peran,
            status_akun='menunggu_verifikasi',
            anak_id=anak_id
        )
        db.session.add(akun)
        db.session.commit()
        return "Pendaftaran berhasil. Silakan tunggu verifikasi dari Kepala Sekolah. <a href='/'>Kembali ke Beranda</a>"
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Registration error", exc_info=True)
        return "Terjadi kesalahan saat mendaftar. Silakan coba lagi.", 500"""

replacement = """        akun = AkunPengguna(
            nik=nik,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=hashed_password,
            peran=peran,
            status_akun='menunggu_verifikasi',
            anak_id=anak_id
        )
        db.session.add(akun)
        db.session.commit()
        return "Pendaftaran berhasil. Silakan tunggu verifikasi dari Kepala Sekolah. <a href='/'>Kembali ke Beranda</a>"
    except IntegrityError:
        db.session.rollback()
        return "Username atau NIK sudah terdaftar. Silakan gunakan yang lain.", 400
    except Exception as e:
        db.session.rollback()
        app.logger.error("Registration error", exc_info=True)
        return "Terjadi kesalahan saat mendaftar. Silakan coba lagi.", 500"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
