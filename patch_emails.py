import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

# 1. Modify /tu/pmb/verifikasi email sending code
# It is already present based on the original codebase:
# email_body = f"Halo {pmb.nama},\n\nSelamat! Pendaftaran Anda di STIESAM telah disetujui.\nNPM: {npm_manual}\nPassword Sementara: {password_awal}\n\nHarap login dan segera mengganti password Anda.\nTerima kasih."
# if pmb.email and pmb.email != '-':
#     send_email_notification(pmb.email, "Pendaftaran PMB STIESAM Disetujui", email_body)
# We just need to check if we need to modify anything for uniqueness of email and nomor_hp
# It's already checked in API route with: if PendaftaranPMB.query.filter_by(email=email, nomor_hp=nomor_hp).first():

# 2. Modify /mahasiswa/tagihan/upload to check nominal > 0
# Actually, nominal > 0 should be in /tu/tagihan/tambah. Let's look.
tagihan_tambah_search = """        if not npm.isdigit() or not jumlah.isdigit():
            flash("Format input tidak valid. Pastikan NPM dan Nominal hanya berisi angka presisi tanpa karakter asing.", "error")
            return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))"""

tagihan_tambah_replace = """        if not npm.isdigit() or not jumlah.isdigit():
            flash("Format input tidak valid. Pastikan NPM dan Nominal hanya berisi angka presisi tanpa karakter asing.", "error")
            return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))

        if int(jumlah) <= 0:
            flash("Nominal tagihan harus lebih besar dari 0.", "error")
            return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))"""

code = code.replace(tagihan_tambah_search, tagihan_tambah_replace)

# Modify /mahasiswa/tagihan/upload to check empty tagihan_list properly? The prompt said "memperdalam logika has_unpaid di irma_dashboard dan _fetch_mahasiswa_data agar benar-benar menolak jika tagihan_list kosong".
# Ah, if tagihan_list is empty, reject KRS.
# In _fetch_mahasiswa_data:
# has_unpaid = any(t.status != 'Lunas' for t in tagihan_list)
# Wait, if tagihan_list is empty, has_unpaid is False. But the logic says "reject if tagihan_list is empty".

fetch_mahasiswa_search = """            tagihan_list = TagihanKuliah.query.filter_by(npm=npm).order_by(TagihanKuliah.id.desc()).all()
            has_unpaid = any(t.status != 'Lunas' for t in tagihan_list)"""

fetch_mahasiswa_replace = """            tagihan_list = TagihanKuliah.query.filter_by(npm=npm).order_by(TagihanKuliah.id.desc()).all()
            has_unpaid = True if not tagihan_list else any(t.status != 'Lunas' for t in tagihan_list)"""

code = code.replace(fetch_mahasiswa_search, fetch_mahasiswa_replace)


# 3. Send email to mahasiswa when tu_tagihan_lunas
# Note: we need the email sending function from /tu/pmb/verifikasi. It's locally defined inside tu_pmb_verifikasi.
# I'll define it globally or duplicate it.
tu_tagihan_lunas_search = """            tagihan.status = 'Lunas'
            db.session.add(Notification(npm=tagihan.npm, message=f"Pembayaran {tagihan.jenis_tagihan} telah dikonfirmasi LUNAS."))
            db.session.commit()
            flash("Tagihan berhasil dilunaskan.", "success")"""

tu_tagihan_lunas_replace = """            tagihan.status = 'Lunas'
            db.session.add(Notification(npm=tagihan.npm, message=f"Pembayaran {tagihan.jenis_tagihan} telah dikonfirmasi LUNAS."))
            db.session.commit()

            # Send email
            import smtplib
            from email.mime.text import MIMEText

            def send_email_notification(to_email, subject, body):
                mail_server = os.environ.get('MAIL_SERVER')
                mail_port = int(os.environ.get('MAIL_PORT', 587))
                mail_username = os.environ.get('MAIL_USERNAME')
                mail_password = os.environ.get('MAIL_PASSWORD')
                use_tls = os.environ.get('MAIL_USE_TLS')

                if not all([mail_server, mail_username, mail_password, to_email]):
                    return

                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = mail_username
                msg['To'] = to_email

                try:
                    server = smtplib.SMTP(mail_server, mail_port)
                    if use_tls:
                        server.starttls()
                    server.login(mail_username, mail_password)
                    server.send_message(msg)
                    server.quit()
                except Exception as e:
                    app.logger.error(f"Failed to send email to {to_email}: {e}")

            user_pmb = PendaftaranPMB.query.filter_by(npm_generated=tagihan.npm).first()
            if user_pmb and user_pmb.email and user_pmb.email != '-':
                email_body = f"Halo {user_pmb.nama},\n\nPembayaran {tagihan.jenis_tagihan} sebesar Rp {tagihan.jumlah} telah dikonfirmasi LUNAS.\n\nTerima kasih."
                send_email_notification(user_pmb.email, "Konfirmasi Pembayaran Lunas STIESAM", email_body)

            flash("Tagihan berhasil dilunaskan.", "success")"""

code = code.replace(tu_tagihan_lunas_search, tu_tagihan_lunas_replace)

# 4. Check jadwal.dosen == current_user.nama tightly in /dosen/krs/action
# Wait, /dosen/krs/action does NOT check jadwal.dosen right now. It gets KRSMahasiswa.
krs_action_search = """        krs = db.session.get(KRSMahasiswa, krs_id)
        if krs and status in ['Disetujui Dosen', 'Ditolak Dosen']:
            krs.status = status"""

krs_action_replace = """        krs = db.session.get(KRSMahasiswa, krs_id)
        if krs and krs.dosen == current_user.nama and status in ['Disetujui Dosen', 'Ditolak Dosen']:
            krs.status = status"""

code = code.replace(krs_action_search, krs_action_replace)

# Verify npm in KRS in /dosen/nilai/submit
# Currently loops: for key, val in request.form.items(): if key.startswith('nilai_') and val: npm = key.replace('nilai_', '')
# Need to verify npm is registered in KRS for that class.

nilai_submit_search = """                    if attendance_pct < 75:
                        val = 'E' # Force E if attendance is below 75%

                    # Prevent duplicate logic or overwrite existing if needed. We assume one grade per semester per class."""

nilai_submit_replace = """                    # Validasi npm terdaftar di KRS
                    krs_check = KRSMahasiswa.query.filter_by(npm=npm, mata_kuliah=mata_kuliah, status='Disetujui Dosen').first()
                    if not krs_check:
                        continue

                    if attendance_pct < 75:
                        val = 'E' # Force E if attendance is below 75%

                    # Prevent duplicate logic or overwrite existing if needed. We assume one grade per semester per class."""

code = code.replace(nilai_submit_search, nilai_submit_replace)

# Add try-except for IntegrityError on presensi duplikat in /dosen/presensi/submit
presensi_submit_search = """        # Insert Jurnal
        new_jurnal = JurnalMengajar(
            jadwal_id=jadwal_id,
            tanggal=tanggal,
            materi=materi
        )
        db.session.add(new_jurnal)

        # Insert Kehadiran
        for key, val in request.form.items():
            if key.startswith('kehadiran_'):
                npm = key.replace('kehadiran_', '')
                new_kehadiran = KehadiranKelas(
                    jadwal_id=jadwal_id,
                    npm=npm,
                    tanggal=tanggal,
                    status=val
                )
                db.session.add(new_kehadiran)
                if val == 'Hadir':
                    db.session.add(Notification(npm=npm, message=f"Presensi {tanggal} dicatat: Hadir."))
                else:
                    db.session.add(Notification(npm=npm, message=f"Presensi {tanggal} dicatat: {val}."))

        db.session.commit()
        pass
        flash("Presensi dan jurnal berhasil disimpan.", "success")

    except Exception as e:"""

presensi_submit_replace = """        try:
            # Insert Jurnal
            new_jurnal = JurnalMengajar(
                jadwal_id=jadwal_id,
                tanggal=tanggal,
                materi=materi
            )
            db.session.add(new_jurnal)

            # Insert Kehadiran
            for key, val in request.form.items():
                if key.startswith('kehadiran_'):
                    npm = key.replace('kehadiran_', '')
                    new_kehadiran = KehadiranKelas(
                        jadwal_id=jadwal_id,
                        npm=npm,
                        tanggal=tanggal,
                        status=val
                    )
                    db.session.add(new_kehadiran)
                    if val == 'Hadir':
                        db.session.add(Notification(npm=npm, message=f"Presensi {tanggal} dicatat: Hadir."))
                    else:
                        db.session.add(Notification(npm=npm, message=f"Presensi {tanggal} dicatat: {val}."))

            db.session.commit()
            flash("Presensi dan jurnal berhasil disimpan.", "success")
        except db.exc.IntegrityError:
            db.session.rollback()
            flash("Gagal menyimpan presensi. Presensi untuk tanggal ini sudah pernah diisi.", "error")
            return redirect(url_for('dosen_dashboard', open='modal-presensi-jurnal'))

    except Exception as e:"""

code = code.replace(presensi_submit_search, presensi_submit_replace)


# Generate PDF with full student name from User table in /tu/surat/acc
surat_acc_search = """            c.drawString(50, 640, "Yang bertanda tangan di bawah ini menerangkan bahwa:")
            c.drawString(50, 610, f"NPM             : {surat.npm}")
            c.drawString(50, 580, f"Keperluan       : {surat.jenis_surat}")"""

surat_acc_replace = """            user_obj = User.query.filter_by(username=surat.npm).first()
            nama_lengkap = user_obj.nama if user_obj else "Mahasiswa"

            c.drawString(50, 640, "Yang bertanda tangan di bawah ini menerangkan bahwa:")
            c.drawString(50, 610, f"Nama Lengkap    : {nama_lengkap}")
            c.drawString(50, 580, f"NPM             : {surat.npm}")
            c.drawString(50, 550, f"Keperluan       : {surat.jenis_surat}")"""

code = code.replace(surat_acc_search, surat_acc_replace)

surat_acc_text_y_search = """            text_y = 550
            c.drawString(50, text_y, "Keterangan:")"""

surat_acc_text_y_replace = """            text_y = 520
            c.drawString(50, text_y, "Keterangan:")"""

code = code.replace(surat_acc_text_y_search, surat_acc_text_y_replace)


# Validate jenis_surat from whitelist in /tu/surat/acc
surat_acc_validate_search = """        surat = SuratOtomatis.query.get(surat_id)
        if surat:
            surat.status = 'Disetujui'"""

surat_acc_validate_replace = """        surat = SuratOtomatis.query.get(surat_id)
        if surat:
            valid_surat = [
                "Surat Keterangan Aktif Kuliah",
                "Surat Pengantar Magang",
                "Surat Pengantar Riset",
                "Surat Cuti Akademik"
            ]
            if surat.jenis_surat not in valid_surat:
                flash("Jenis surat tidak valid.", "error")
                return redirect(url_for('ramadhan_dashboard', open='modal-pabrik-surat'))

            surat.status = 'Disetujui'"""

code = code.replace(surat_acc_validate_search, surat_acc_validate_replace)

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'w') as f:
    f.write(code)

print("Patch applied for emails and validation.")
