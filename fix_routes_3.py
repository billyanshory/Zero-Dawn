import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"

with open(filename, "r") as f:
    content = f.read()

content = content.replace("""@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        pass
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='donate', content=render_template_string(DONATE_HTML, is_admin=session.get('is_admin', False)), is_admin=session.get('is_admin', False), settings=get_settings())""", """@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        pass
    try:
        settings_data = get_settings()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        settings_data = {}
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='donate', content=render_template_string(DONATE_HTML, is_admin=session.get('is_admin', False), settings=settings_data), is_admin=session.get('is_admin', False), settings=settings_data)""")

content = content.replace("""@app.route('/ramadhan')
def ramadhan_dashboard():
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
                                              settings=get_settings())

    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML + RAMADHAN_STYLES,
                                  active_page='ramadhan',
                                  content=rendered_content,
                                  hide_nav=True,
                                  full_width=True,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())""", """@app.route('/ramadhan')
def ramadhan_dashboard():
    # 1. Takjil Data
    takjil_data = get_takjil_data()

    # 2. Imsakiyah Data
    imsakiyah_data = get_imsakiyah_schedule()

    # 3. Kas Ramadhan Data
    try:
        ramadhan_kas_items = RamadhanKas.query.order_by(RamadhanKas.date.desc()).all()
        kas_in = db.session.query(func.sum(RamadhanKas.amount)).filter_by(type='Pemasukan').scalar() or 0
        kas_out = db.session.query(func.sum(RamadhanKas.amount)).filter_by(type='Pengeluaran').scalar() or 0
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        ramadhan_kas_items = []
        kas_in = kas_out = 0

    # 4. Tarawih Schedule
    try:
        seed_ramadhan_schedule()
        tarawih_schedule = TarawihSchedule.query.order_by(TarawihSchedule.night_index.asc()).all()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        tarawih_schedule = []

    # Render CONTENT first
    rendered_content = render_template_string(RAMADHAN_DASHBOARD_HTML,
                                              takjil_data=takjil_data,
                                              imsakiyah_data=imsakiyah_data,
                                              ramadhan_kas_items=ramadhan_kas_items,
                                              ramadhan_kas_summary={'income': kas_in, 'out': kas_out, 'balance': kas_in - kas_out},
                                              tarawih_schedule=tarawih_schedule,
                                              open_modal=request.args.get('open'),
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())

    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML + RAMADHAN_STYLES,
                                  active_page='ramadhan',
                                  content=rendered_content,
                                  hide_nav=True,
                                  full_width=True,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())""")

content = content.replace("""@app.route('/admin/qurban/hewan')
def admin_qurban_hewan():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    animals = QurbanAnimal.query.order_by(QurbanAnimal.id.desc()).all()
    rendered_content = render_template_string(IDUL_ADHA_HEWAN_ADMIN_HTML, animals=animals, is_admin=True)
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=True, settings=get_settings())""", """@app.route('/admin/qurban/hewan')
def admin_qurban_hewan():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    try:
        animals = QurbanAnimal.query.order_by(QurbanAnimal.id.desc()).all()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        animals = []
    rendered_content = render_template_string(IDUL_ADHA_HEWAN_ADMIN_HTML, animals=animals, is_admin=True)
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=True, settings=get_settings())""")

with open(filename, "w") as f:
    f.write(content)
