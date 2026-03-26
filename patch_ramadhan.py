import sys

filepath = "kampus-stie-samarinda-0 ( idcloudhost - 3 dashboard utama - tu, mahasiswa dan dosen ).py"

with open(filepath, 'r') as f:
    content = f.read()

target = """def ramadhan_dashboard():
    # 1. Takjil Data
    takjil_data = get_takjil_data()

    # 2. Imsakiyah Data
    imsakiyah_data = get_imsakiyah_schedule()

    # 3. Kas Ramadhan Data
    ramadhan_kas_items = RamadhanKas.query.order_by(RamadhanKas.date.desc()).all()
    kas_in = db.session.query(func.sum(RamadhanKas.amount)).filter_by(type='Pemasukan').scalar() or 0
    kas_out = db.session.query(func.sum(RamadhanKas.amount)).filter_by(type='Pengeluaran').scalar() or 0

    # 4. Tarawih Schedule
    seed_ramadhan_schedule()
    tarawih_schedule = TarawihSchedule.query.order_by(TarawihSchedule.night_index.asc()).all()

    # Render CONTENT first
    rendered_content = render_template_string(RAMADHAN_DASHBOARD_HTML,
                                              takjil_data=takjil_data,
                                              imsakiyah_data=imsakiyah_data,
                                              ramadhan_kas_items=ramadhan_kas_items,
                                              ramadhan_kas_summary={'income': kas_in, 'out': kas_out, 'balance': kas_in - kas_out},
                                              tarawih_schedule=tarawih_schedule,
                                              open_modal=request.args.get('open'),
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())"""

replacement = """def ramadhan_dashboard():
    surat_list = []
    pmb_list = []
    tagihan_list = []
    jadwal_list = []
    akun_list = []
    arsip_list = []

    try:
        surat_list = SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all()
        pmb_list = PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).all()
        tagihan_list = TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).all()
        jadwal_list = JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all()
        akun_list = User.query.order_by(User.id.desc()).all()
        arsip_list = LaciArsip.query.order_by(LaciArsip.id.desc()).all()
    except Exception as e:
        print(f"Error fetching TU Dashboard data: {e}")

    # Render CONTENT first
    rendered_content = render_template_string(RAMADHAN_DASHBOARD_HTML,
                                              surat_list=surat_list,
                                              pmb_list=pmb_list,
                                              tagihan_list=tagihan_list,
                                              jadwal_list=jadwal_list,
                                              akun_list=akun_list,
                                              arsip_list=arsip_list,
                                              open_modal=request.args.get('open'),
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("ramadhan_dashboard route updated.")
else:
    print("Target not found.")
