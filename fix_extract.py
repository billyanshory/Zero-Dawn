with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

def inject_after(content, after_str, new_code):
    idx = content.find(after_str)
    if idx == -1: return content
    idx += len(after_str)
    return content[:idx] + "\n" + new_code + content[idx:]

# Extract logic
dosen_helper = """
def _fetch_dosen_data(dosen_name):
    jadwal_dosen = []
    krs_perwalian = []
    unique_npms = set()
    mahasiswa_perwalian = []
    kelas_list = []
    try:
        jadwal_dosen = JadwalKuliah.query.filter_by(dosen=dosen_name).all()
        krs_raw = KRSMahasiswa.query.options(joinedload(KRSMahasiswa.user_krs)).filter_by(dosen=dosen_name).order_by(KRSMahasiswa.id.desc()).all()
        npms_in_krs = [k.npm for k in krs_raw]
        all_tagihan = TagihanKuliah.query.filter(TagihanKuliah.npm.in_(npms_in_krs)).all() if npms_in_krs else []
        tagihan_map = {}
        for t in all_tagihan: tagihan_map.setdefault(t.npm, []).append(t)
        for krs in krs_raw:
            tagihan = tagihan_map.get(krs.npm, [])
            if not tagihan or all(t.status == 'Lunas' for t in tagihan): krs_perwalian.append(krs)
            unique_npms.add(krs.npm)

        if jadwal_dosen:
            jadwal_ids = [j.id for j in jadwal_dosen]
            mata_kuliah_list = [j.mata_kuliah for j in jadwal_dosen]
            all_status_nilai = StatusNilai.query.filter(StatusNilai.jadwal_id.in_(jadwal_ids)).all()
            status_nilai_map = {sn.jadwal_id: sn for sn in all_status_nilai}
            all_krs_class = KRSMahasiswa.query.filter(KRSMahasiswa.mata_kuliah.in_(mata_kuliah_list), KRSMahasiswa.status=='Disetujui Dosen').all()
            krs_class_map = {}
            all_npm_class = set()
            for krs in all_krs_class:
                krs_class_map.setdefault(krs.mata_kuliah, []).append(krs)
                all_npm_class.add(krs.npm)
            all_users_class = User.query.filter(User.username.in_(list(all_npm_class))).all() if all_npm_class else []
            user_class_map = {u.username: u for u in all_users_class}
            all_jurnal = JurnalMengajar.query.filter(JurnalMengajar.jadwal_id.in_(jadwal_ids)).all()
            jurnal_map = {}
            for j in all_jurnal: jurnal_map[j.jadwal_id] = jurnal_map.get(j.jadwal_id, 0) + 1
            all_kehadiran = KehadiranKelas.query.filter(KehadiranKelas.jadwal_id.in_(jadwal_ids), KehadiranKelas.status=='Hadir').all()
            kehadiran_map = {}
            for k in all_kehadiran:
                kehadiran_map.setdefault(k.jadwal_id, {})
                kehadiran_map[k.jadwal_id][k.npm] = kehadiran_map[k.jadwal_id].get(k.npm, 0) + 1

        for jadwal in jadwal_dosen:
            status_nilai = status_nilai_map.get(jadwal.id)
            is_published = status_nilai.is_published if status_nilai else False
            krs_class = krs_class_map.get(jadwal.mata_kuliah, [])
            student_data = []
            if krs_class:
                total_sessions = jurnal_map.get(jadwal.id, 0)
                hadir_map = kehadiran_map.get(jadwal.id, {})
                for student_krs in krs_class:
                    if total_sessions == 0: attendance_pct = 100
                    else: attendance_pct = (hadir_map.get(student_krs.npm, 0) / total_sessions) * 100
                    user_obj = user_class_map.get(student_krs.npm)
                    student_data.append({'npm': student_krs.npm, 'nama': user_obj.nama if user_obj else 'Unknown', 'attendance_pct': attendance_pct})
            kelas_list.append({'jadwal': jadwal, 'is_published': is_published, 'students': student_data})

        if unique_npms:
            npm_list = list(unique_npms)
            users = User.query.filter(User.username.in_(npm_list)).all()
            all_nilai = NilaiMahasiswa.query.filter(NilaiMahasiswa.npm.in_(npm_list)).all()
            all_arsip = LaciArsip.query.filter(LaciArsip.npm.in_(npm_list)).all()
            user_map = {u.username: u for u in users}
            nilai_map = {}
            for n in all_nilai: nilai_map.setdefault(n.npm, []).append(n)
            arsip_map = {}
            for a in all_arsip: arsip_map.setdefault(a.npm, []).append(a)
            for npm in unique_npms:
                user = user_map.get(npm)
                if user:
                    nilai_list = nilai_map.get(npm, [])
                    total_sks = sum(n.sks for n in nilai_list)
                    total_bobot = sum((n.sks * ({'A':4.0,'A-':3.7,'B+':3.3,'B':3.0,'B-':2.7,'C+':2.3,'C':2.0,'D':1.0}.get(n.nilai_huruf, 0.0))) for n in nilai_list)
                    ipk = (total_bobot / total_sks) if total_sks > 0 else 0
                    mahasiswa_perwalian.append({'npm': npm, 'nama': user.nama, 'status': user.status_akademik, 'ipk': ipk, 'transkrip': nilai_list, 'arsip': arsip_map.get(npm, [])})
    except Exception as e:
        db.session.rollback()
        print(f"Error loading Dosen Dashboard: {e}")
    return jadwal_dosen, krs_perwalian, kelas_list, mahasiswa_perwalian
"""
content = content.replace("def render_page", dosen_helper + "\ndef render_page")

# Dosen Replacement
dosen_old = """    jadwal_dosen = []
    krs_perwalian = []
    unique_npms = set()
    mahasiswa_perwalian = []
    kelas_list = []

    try:
        # 1. Jadwal Kuliah (Cermin dari TU)
        jadwal_dosen = JadwalKuliah.query.filter_by(dosen=dosen_name).all()

        # 2. KRS Perwalian (Filter Lunas)
        krs_raw = KRSMahasiswa.query.options(joinedload(KRSMahasiswa.user_krs)).filter_by(dosen=dosen_name).order_by(KRSMahasiswa.id.desc()).all()

        # Optimization: Fetch all tagihan in one go to prevent N+1
        npms_in_krs = [k.npm for k in krs_raw]
        all_tagihan = TagihanKuliah.query.filter(TagihanKuliah.npm.in_(npms_in_krs)).all() if npms_in_krs else []
        tagihan_map = {}
        for t in all_tagihan:
            tagihan_map.setdefault(t.npm, []).append(t)

        for krs in krs_raw:
            tagihan = tagihan_map.get(krs.npm, [])
            # Ensure either there are no bills, or all bills are 'Lunas'
            if not tagihan or all(t.status == 'Lunas' for t in tagihan):
                krs_perwalian.append(krs)

            unique_npms.add(krs.npm)

        # 3. Masukan Nilai Akhir (Kelas) - OPTIMIZED O(1) Queries
        if jadwal_dosen:
            jadwal_ids = [j.id for j in jadwal_dosen]
            mata_kuliah_list = [j.mata_kuliah for j in jadwal_dosen]

            all_status_nilai = StatusNilai.query.filter(StatusNilai.jadwal_id.in_(jadwal_ids)).all()
            status_nilai_map = {sn.jadwal_id: sn for sn in all_status_nilai}

            all_krs_class = KRSMahasiswa.query.filter(KRSMahasiswa.mata_kuliah.in_(mata_kuliah_list), KRSMahasiswa.status=='Disetujui Dosen').all()
            krs_class_map = {}
            all_npm_class = set()
            for krs in all_krs_class:
                krs_class_map.setdefault(krs.mata_kuliah, []).append(krs)
                all_npm_class.add(krs.npm)

            all_users_class = User.query.filter(User.username.in_(list(all_npm_class))).all() if all_npm_class else []
            user_class_map = {u.username: u for u in all_users_class}

            all_jurnal = JurnalMengajar.query.filter(JurnalMengajar.jadwal_id.in_(jadwal_ids)).all()
            jurnal_map = {}
            for j in all_jurnal:
                jurnal_map[j.jadwal_id] = jurnal_map.get(j.jadwal_id, 0) + 1

            all_kehadiran = KehadiranKelas.query.filter(KehadiranKelas.jadwal_id.in_(jadwal_ids), KehadiranKelas.status=='Hadir').all()
            kehadiran_map = {}
            for k in all_kehadiran:
                kehadiran_map.setdefault(k.jadwal_id, {})
                kehadiran_map[k.jadwal_id][k.npm] = kehadiran_map[k.jadwal_id].get(k.npm, 0) + 1

        for jadwal in jadwal_dosen:
            status_nilai = status_nilai_map.get(jadwal.id)
            is_published = status_nilai.is_published if status_nilai else False

            # Determine students taking this class
            krs_class = krs_class_map.get(jadwal.mata_kuliah, [])

            student_data = []
            if krs_class:
                total_sessions = jurnal_map.get(jadwal.id, 0)
                hadir_map = kehadiran_map.get(jadwal.id, {})

                for student_krs in krs_class:
                    if total_sessions == 0:
                        attendance_pct = 100
                    else:
                        present_count = hadir_map.get(student_krs.npm, 0)
                        attendance_pct = (present_count / total_sessions) * 100

                    user_obj = user_class_map.get(student_krs.npm)
                    student_data.append({
                        'npm': student_krs.npm,
                        'nama': user_obj.nama if user_obj else 'Unknown',
                        'attendance_pct': attendance_pct
                    })

            kelas_list.append({
                'jadwal': jadwal,
                'is_published': is_published,
                'students': student_data
            })

        # 4. Mahasiswa Perwalian (Details, IPK, Transkrip) - OPTIMIZED O(1) Queries
        if unique_npms:
            npm_list = list(unique_npms)
            users = User.query.filter(User.username.in_(npm_list)).all()
            all_nilai = NilaiMahasiswa.query.filter(NilaiMahasiswa.npm.in_(npm_list)).all()
            all_arsip = LaciArsip.query.filter(LaciArsip.npm.in_(npm_list)).all()

            user_map = {u.username: u for u in users}
            nilai_map = {}
            for n in all_nilai:
                nilai_map.setdefault(n.npm, []).append(n)
            arsip_map = {}
            for a in all_arsip:
                arsip_map.setdefault(a.npm, []).append(a)

            for npm in unique_npms:
                user = user_map.get(npm)
                if user:
                    nilai_list = nilai_map.get(npm, [])
                    total_sks = 0
                    total_bobot = 0
                    for n in nilai_list:
                        nilai_angka = 4.0
                        if n.nilai_huruf == 'A': nilai_angka = 4.0
                        elif n.nilai_huruf == 'A-': nilai_angka = 3.7
                        elif n.nilai_huruf == 'B+': nilai_angka = 3.3
                        elif n.nilai_huruf == 'B': nilai_angka = 3.0
                        elif n.nilai_huruf == 'B-': nilai_angka = 2.7
                        elif n.nilai_huruf == 'C+': nilai_angka = 2.3
                        elif n.nilai_huruf == 'C': nilai_angka = 2.0
                        elif n.nilai_huruf == 'D': nilai_angka = 1.0
                        else: nilai_angka = 0.0
                        total_sks += n.sks
                        total_bobot += (n.sks * nilai_angka)

                    ipk = (total_bobot / total_sks) if total_sks > 0 else 0
                    arsip = arsip_map.get(npm, [])

                    mahasiswa_perwalian.append({
                        'npm': npm,
                        'nama': user.nama,
                        'status': user.status_akademik,
                        'ipk': ipk,
                        'transkrip': nilai_list,
                        'arsip': arsip
                    })
    except Exception as e:
        db.session.rollback()
        print(f"Error loading Dosen Dashboard: {e}")
        flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")"""

dosen_new = """    jadwal_dosen, krs_perwalian, kelas_list, mahasiswa_perwalian = _fetch_dosen_data(dosen_name)"""
content = content.replace(dosen_old, dosen_new)

# Mahasiswa Helper
mhs_helper = """
def _fetch_mahasiswa_data(npm, is_admin):
    user = None
    tagihan_list = []
    krs_list = []
    nilai_list = []
    jadwal_list = []
    surat_list = []
    arsip_list = []
    has_unpaid = False
    try:
        user = User.query.filter_by(username=npm).first()
        if npm:
            tagihan_list = TagihanKuliah.query.filter_by(npm=npm).order_by(TagihanKuliah.id.desc()).all()
            has_unpaid = any(t.status != 'Lunas' for t in tagihan_list)
            krs_list = KRSMahasiswa.query.filter_by(npm=npm).order_by(KRSMahasiswa.id.desc()).all()
            nilai_list = NilaiMahasiswa.query.filter_by(npm=npm).order_by(NilaiMahasiswa.semester.desc(), NilaiMahasiswa.id.desc()).all()
            jadwal_list = JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all()
            surat_list = SuratOtomatis.query.filter_by(npm=npm).order_by(SuratOtomatis.id.desc()).all()
            arsip_list = LaciArsip.query.filter_by(npm=npm).order_by(LaciArsip.id.desc()).all()
    except Exception as e:
        print(f"Error fetch mhs: {e}")
    return user, tagihan_list, krs_list, nilai_list, jadwal_list, surat_list, arsip_list, has_unpaid
"""
content = content.replace("def render_page", mhs_helper + "\ndef render_page")

mhs_old = """    try:
        is_admin = session.get('is_admin', False)
        settings_data = get_settings()

        # Fetch User Session Data
        user = User.query.filter_by(username=npm).first()

        if npm:
            tagihan_list = TagihanKuliah.query.filter_by(npm=npm).order_by(TagihanKuliah.id.desc()).all()
            has_unpaid = any(t.status != 'Lunas' for t in tagihan_list)

            krs_list = KRSMahasiswa.query.filter_by(npm=npm).order_by(KRSMahasiswa.id.desc()).all()
            nilai_list = NilaiMahasiswa.query.filter_by(npm=npm).order_by(NilaiMahasiswa.semester.desc(), NilaiMahasiswa.id.desc()).all()

            jadwal_list = JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all()

            surat_list = SuratOtomatis.query.filter_by(npm=npm).order_by(SuratOtomatis.id.desc()).all()
            arsip_list = LaciArsip.query.filter_by(npm=npm).order_by(LaciArsip.id.desc()).all()

        # 1. Schedule List (Legacy)
        try:
            schedule_list = IrmaSchedule.query.order_by(IrmaSchedule.date.desc(), IrmaSchedule.id.desc()).all()
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching Schedule: {e}")
            flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")

        # 2. Kas (Finance - Legacy)
        try:
            kas_list = IrmaKas.query.order_by(IrmaKas.date.desc()).all()
            fin_in = db.session.query(func.sum(IrmaKas.amount)).filter_by(type='Pemasukan').scalar() or 0
            fin_out = db.session.query(func.sum(IrmaKas.amount)).filter_by(type='Pengeluaran').scalar() or 0
            kas_summary = {'income': fin_in, 'out': fin_out, 'balance': fin_in - fin_out}
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching Kas: {e}")
            flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")

        # 3. Gallery (Mading - Legacy)
        try:
            gallery_list = IrmaGallery.query.order_by(IrmaGallery.created_at.desc()).all()
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching Gallery: {e}")
            flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")

        # 4. Proker (Events - Legacy)
        try:
            proker_list = IrmaProker.query.order_by(IrmaProker.date.asc()).all()
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching Proker: {e}")
            flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")

        # 5. Curhat (Q&A - Legacy)
        try:
            curhat_list = IrmaCurhat.query.order_by(IrmaCurhat.created_at.desc()).all()
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching Curhat: {e}")
            flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")

        # 6. Members (Legacy)
        try:
            if is_admin:
                members_list = IrmaMember.query.order_by(IrmaMember.joined_at.desc()).all()

            check_wa = request.args.get('check_wa')
            if check_wa:
                check_status = IrmaMember.query.filter_by(wa_number=check_wa).first()
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching Members: {e}")
            flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")

    except Exception as e:
        print(f"Critical Error in Dashboard: {e}")"""

mhs_new = """    is_admin = session.get('is_admin', False)
    settings_data = get_settings()
    user, tagihan_list, krs_list, nilai_list, jadwal_list, surat_list, arsip_list, has_unpaid = _fetch_mahasiswa_data(npm, is_admin)
"""
content = content.replace(mhs_old, mhs_new)


# TU Helper
tu_helper = """
def _fetch_tu_data():
    try:
        return (
            SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all(),
            PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).all(),
            TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).all(),
            JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all(),
            User.query.order_by(User.id.desc()).all(),
            LaciArsip.query.order_by(LaciArsip.id.desc()).all(),
            TracerStudy.query.order_by(TracerStudy.id.desc()).all(),
            TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all()
        )
    except Exception as e:
        print(e)
        return [], [], [], [], [], [], [], []
"""
content = content.replace("def render_page", tu_helper + "\ndef render_page")

tu_old = """    try:
        surat_list = SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all()
        pmb_list = PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).all()
        tagihan_list = TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).all()
        jadwal_list = JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all()
        akun_list = User.query.order_by(User.id.desc()).all()
        arsip_list = LaciArsip.query.order_by(LaciArsip.id.desc()).all()
        tracer_list = TracerStudy.query.order_by(TracerStudy.id.desc()).all()
        verified_alumni_list = TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all()
    except Exception as e:
        db.session.rollback()
        print(f"Error fetching TU Dashboard data: {e}")
        flash(f"Terjadi kesalahan sistem saat memproses permintaan: {e}", "error")"""

tu_new = """    surat_list, pmb_list, tagihan_list, jadwal_list, akun_list, arsip_list, tracer_list, verified_alumni_list = _fetch_tu_data()"""
content = content.replace(tu_old, tu_new)

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
