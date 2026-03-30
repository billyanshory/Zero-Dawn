import re

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Fix relationships placement. Move from where they are (probably around EpilepsiLog) to User.
content = content.replace("    krs_rel = db.relationship('KRSMahasiswa', backref='user_krs', primaryjoin=\"User.username == foreign(KRSMahasiswa.npm)\")\n    tagihan_rel = db.relationship('TagihanKuliah', backref='user_tagihan', primaryjoin=\"User.username == foreign(TagihanKuliah.npm)\")", "")

user_end_str = "    status_akademik = db.Column(db.String(50), default='Aktif', index=True)\n    created_at = db.Column(db.DateTime, server_default=func.now())"
user_end_replace = "    status_akademik = db.Column(db.String(50), default='Aktif', index=True)\n    created_at = db.Column(db.DateTime, server_default=func.now())\n    krs_rel = db.relationship('KRSMahasiswa', backref='user_krs', primaryjoin=\"User.username == foreign(KRSMahasiswa.npm)\")\n    tagihan_rel = db.relationship('TagihanKuliah', backref='user_tagihan', primaryjoin=\"User.username == foreign(TagihanKuliah.npm)\")"

content = content.replace(user_end_str, user_end_replace, 1)

# 2. Create Notifications on events.
# PMB Verifikasi -> Notification to User
tu_pmb = """            new_user = User(username=new_npm, password_hash=generate_password_hash("mahasiswa123"), role='Mahasiswa', nama=pmb.nama, status_akademik='Aktif')
            db.session.add(new_user)
            db.session.add(Notification(npm=new_npm, message="Selamat, pendaftaran Anda disetujui. Akun berhasil dibuat."))
"""
content = content.replace('            new_user = User(username=new_npm, password_hash=generate_password_hash("mahasiswa123"), role=\'Mahasiswa\', nama=pmb.nama, status_akademik=\'Aktif\')\n            db.session.add(new_user)', tu_pmb)

# Tagihan Lunas -> Notification
tu_lunas = """        if tagihan:
            tagihan.status = 'Lunas'
            db.session.add(Notification(npm=tagihan.npm, message=f"Pembayaran {tagihan.jenis_tagihan} telah dikonfirmasi LUNAS."))
"""
content = content.replace("        if tagihan:\n            tagihan.status = 'Lunas'", tu_lunas)

# 3. Apply render_page to tu_dashboard, dosen, mahasiswa
content = content.replace("    rendered_content = render_template_string(RAMADHAN_DASHBOARD_HTML,\n                                              surat_list=surat_list,\n                                              pmb_list=pmb_list,\n                                              tagihan_list=tagihan_list,\n                                              jadwal_list=jadwal_list,\n                                              akun_list=akun_list,\n                                              arsip_list=arsip_list,\n                                              tracer_list=tracer_list,\n                                              verified_alumni_list=verified_alumni_list,\n                                              open_modal=request.args.get('open'),\n                                              is_admin=session.get('is_admin', False),\n                                              settings=get_settings())\n\n    return render_template_string(BASE_LAYOUT, \n                                  styles=STYLES_HTML + RAMADHAN_STYLES, \n                                  active_page='ramadhan', \n                                  content=rendered_content,\n                                  hide_nav=True,\n                                  full_width=True,\n                                  is_admin=session.get('is_admin', False),\n                                  settings=get_settings())",
"""    return render_page(RAMADHAN_DASHBOARD_HTML, 'ramadhan', content_kwargs={
        'surat_list': surat_list, 'pmb_list': pmb_list, 'tagihan_list': tagihan_list,
        'jadwal_list': jadwal_list, 'akun_list': akun_list, 'arsip_list': arsip_list,
        'tracer_list': tracer_list, 'verified_alumni_list': verified_alumni_list
    }, hide_nav=True, full_width=True)""")


dosen_return = """    return render_template_string(BASE_LAYOUT, \n                                  styles=STYLES_HTML + IRMA_STYLES, \n                                  active_page='irma', \n                                  theme=dosen_theme,\n                                  content=render_template_string(dosen_html, \n                                                                 dosen_name=dosen_name,\n                                                                 jadwal_dosen=jadwal_dosen,\n                                                                 krs_perwalian=krs_perwalian,\n                                                                 kelas_list=kelas_list,\n                                                                 mahasiswa_perwalian=mahasiswa_perwalian),\n                                  full_width=True,\n                                  is_admin=session.get('is_admin', False),\n                                  settings=get_settings())"""

dosen_replace = """    return render_page(dosen_html, 'irma', theme=dosen_theme, content_kwargs={
        'dosen_name': dosen_name, 'jadwal_dosen': jadwal_dosen, 'krs_perwalian': krs_perwalian,
        'kelas_list': kelas_list, 'mahasiswa_perwalian': mahasiswa_perwalian
    }, full_width=True)"""
content = content.replace(dosen_return, dosen_replace)

irma_return = """    return render_template_string(BASE_LAYOUT, \n                                  styles=STYLES_HTML + IRMA_STYLES, \n                                  active_page='irma', \n                                  theme=irma_theme,\n                                  content=render_template_string(IRMA_DASHBOARD_HTML,\n                                                                 user=user,\n                                                                 tagihan_list=tagihan_list,\n                                                                 krs_list=krs_list,\n                                                                 nilai_list=nilai_list,\n                                                                 jadwal_list=jadwal_list,\n                                                                 surat_list=surat_list,\n                                                                 arsip_list=arsip_list,\n                                                                 has_unpaid=has_unpaid,\n                                                                 open_modal=open_modal,\n                                                                 is_admin=is_admin, settings=settings_data),\n                                  full_width=True,\n                                  is_admin=is_admin,\n                                  settings=settings_data)"""

irma_replace = """    return render_page(IRMA_DASHBOARD_HTML, 'irma', theme=irma_theme, content_kwargs={
        'user': user, 'tagihan_list': tagihan_list, 'krs_list': krs_list, 'nilai_list': nilai_list,
        'jadwal_list': jadwal_list, 'surat_list': surat_list, 'arsip_list': arsip_list, 'has_unpaid': has_unpaid
    }, full_width=True)"""
content = content.replace(irma_return, irma_replace)


with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
