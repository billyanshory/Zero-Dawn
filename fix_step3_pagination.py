import re

file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update _fetch_tu_data()
target_func = """def _fetch_tu_data():
    try:
        from flask import request
        page = request.args.get('page', 1, type=int)
        pending_users = User.query.filter_by(status_akademik='Menunggu Verifikasi').order_by(User.id.desc()).all()
        return (
            SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all(),
            PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).paginate(page=page, per_page=50),
            TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).paginate(page=page, per_page=50),
            JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all(),
            User.query.order_by(User.id.desc()).paginate(page=page, per_page=50),
            LaciArsip.query.order_by(LaciArsip.id.desc()).all(),
            TracerStudy.query.order_by(TracerStudy.id.desc()).all(),
            TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all(),
            pending_users
        )"""

replacement_func = """def _fetch_tu_data():
    try:
        from flask import request
        pmb_page = request.args.get('pmb_page', 1, type=int)
        tagihan_page = request.args.get('tagihan_page', 1, type=int)
        akun_page = request.args.get('akun_page', 1, type=int)
        pending_users = User.query.filter_by(status_akademik='Menunggu Verifikasi').order_by(User.id.desc()).all()
        return (
            SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all(),
            PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).paginate(page=pmb_page, per_page=50),
            TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).paginate(page=tagihan_page, per_page=50),
            JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all(),
            User.query.order_by(User.id.desc()).paginate(page=akun_page, per_page=50),
            LaciArsip.query.order_by(LaciArsip.id.desc()).all(),
            TracerStudy.query.order_by(TracerStudy.id.desc()).all(),
            TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all(),
            pending_users
        )"""

content = content.replace(target_func, replacement_func)

# 2. Update the HTML parameters for links
# PMB
content = content.replace("page={{ pmb_list.prev_num }}", "pmb_page={{ pmb_list.prev_num }}")
content = content.replace("page={{ pmb_list.next_num }}", "pmb_page={{ pmb_list.next_num }}")

# Tagihan
content = content.replace("page={{ tagihan_list.prev_num }}", "tagihan_page={{ tagihan_list.prev_num }}")
content = content.replace("page={{ tagihan_list.next_num }}", "tagihan_page={{ tagihan_list.next_num }}")

# Akun
content = content.replace("page={{ akun_list.prev_num }}", "akun_page={{ akun_list.prev_num }}")
content = content.replace("page={{ akun_list.next_num }}", "akun_page={{ akun_list.next_num }}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
