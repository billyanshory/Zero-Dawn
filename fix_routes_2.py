import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"

with open(filename, "r") as f:
    content = f.read()

# Fix irma routes (schedule, join, kas, proker, curhat)
content = content.replace("""@app.route('/irma/schedule', methods=['POST'])
def irma_schedule():
    if 'delete_id' in request.form:
        IrmaSchedule.query.filter_by(id=request.form.get('delete_id', '')).delete()
    else:
        item = IrmaSchedule(
            name=request.form.get('name', ''),
            role=request.form.get('role', ''),
            date=request.form.get('date', '')
        )
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-duty'))""", """@app.route('/irma/schedule', methods=['POST'])
def irma_schedule():
    try:
        if 'delete_id' in request.form:
            IrmaSchedule.query.filter_by(id=request.form.get('delete_id', '')).delete()
        else:
            item = IrmaSchedule(
                name=request.form.get('name', ''),
                role=request.form.get('role', ''),
                date=request.form.get('date', '')
            )
            db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
    return redirect(url_for('irma_dashboard', open='modal-duty'))""")

content = content.replace("""@app.route('/irma/join', methods=['GET', 'POST'])
def irma_join():
    if request.method == 'GET':
        return redirect(url_for('irma_dashboard', open='modal-join', check_wa=request.args.get('check_wa')))

    action = request.form.get('action')
    if action in ['approve', 'reject']:
        member = IrmaMember.query.get(request.form.get('member_id', ''))
        if member:
            member.status = 'Approved' if action == 'approve' else 'Rejected'
    else:
        item = IrmaMember(
            name=request.form.get('name', ''),
            age=request.form.get('age', ''),
            hobbies=request.form.get('hobbies', ''),
            instagram=request.form.get('instagram', ''),
            wa_number=request.form.get('wa_number', '')
        )
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-join'))""", """@app.route('/irma/join', methods=['GET', 'POST'])
def irma_join():
    if request.method == 'GET':
        return redirect(url_for('irma_dashboard', open='modal-join', check_wa=request.args.get('check_wa')))

    try:
        action = request.form.get('action')
        if action in ['approve', 'reject']:
            member = IrmaMember.query.get(request.form.get('member_id', ''))
            if member:
                member.status = 'Approved' if action == 'approve' else 'Rejected'
        else:
            item = IrmaMember(
                name=request.form.get('name', ''),
                age=request.form.get('age', ''),
                hobbies=request.form.get('hobbies', ''),
                instagram=request.form.get('instagram', ''),
                wa_number=request.form.get('wa_number', '')
            )
            db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
    return redirect(url_for('irma_dashboard', open='modal-join'))""")

content = content.replace("""@app.route('/irma/kas', methods=['POST'])
def irma_kas():
    item = IrmaKas(
        date=request.form.get('date', ''),
        type=request.form.get('type', ''),
        description=request.form.get('description', ''),
        amount=int(request.form.get('amount', 0))
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-finance'))""", """@app.route('/irma/kas', methods=['POST'])
def irma_kas():
    try:
        item = IrmaKas(
            date=request.form.get('date', ''),
            type=request.form.get('type', ''),
            description=request.form.get('description', ''),
            amount=int(request.form.get('amount', 0))
        )
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
    return redirect(url_for('irma_dashboard', open='modal-finance'))""")

content = content.replace("""@app.route('/irma/proker', methods=['POST'])
def irma_proker():
    item = IrmaProker(
        title=request.form.get('title', ''),
        status=request.form.get('status', ''),
        description=request.form.get('description', ''),
        date=request.form.get('date', '')
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-events'))""", """@app.route('/irma/proker', methods=['POST'])
def irma_proker():
    try:
        item = IrmaProker(
            title=request.form.get('title', ''),
            status=request.form.get('status', ''),
            description=request.form.get('description', ''),
            date=request.form.get('date', '')
        )
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
    return redirect(url_for('irma_dashboard', open='modal-events'))""")

content = content.replace("""@app.route('/irma/curhat', methods=['POST'])
def irma_curhat():
    if 'answer' in request.form:
        item = IrmaCurhat.query.get(request.form.get('answer_id', ''))
        if item:
            item.answer = request.form.get('answer', '')
            item.answered_at = datetime.datetime.now()
    else:
        item = IrmaCurhat(question=request.form.get('question', ''))
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-qa'))""", """@app.route('/irma/curhat', methods=['POST'])
def irma_curhat():
    try:
        if 'answer' in request.form:
            item = IrmaCurhat.query.get(request.form.get('answer_id', ''))
            if item:
                item.answer = request.form.get('answer', '')
                item.answered_at = datetime.datetime.now()
        else:
            item = IrmaCurhat(question=request.form.get('question', ''))
            db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
    return redirect(url_for('irma_dashboard', open='modal-qa'))""")

content = content.replace("""@app.route('/donate/update', methods=['POST'])
def donate_update():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    keys = ['infaq_rekening_masjid', 'infaq_rekening_qurban', 'infaq_rekening_zakat']
    for k in keys:
        val = request.form.get(k)
        if val:
            s = AppSettings.query.get(k)
            if s: s.value = val
            else: db.session.add(AppSettings(key=k, value=val))

    if 'qris_image' in request.files:
        file = request.files['qris_image']
        if file and allowed_file(file.filename):
            saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
            s = AppSettings.query.get('infaq_qris_image')
            if s: s.value = saved_filename
            else: db.session.add(AppSettings(key='infaq_qris_image', value=saved_filename))

    db.session.commit()
    return redirect(request.referrer)""", """@app.route('/donate/update', methods=['POST'])
def donate_update():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:
        keys = ['infaq_rekening_masjid', 'infaq_rekening_qurban', 'infaq_rekening_zakat']
        for k in keys:
            val = request.form.get(k)
            if val:
                s = AppSettings.query.get(k)
                if s: s.value = val
                else: db.session.add(AppSettings(key=k, value=val))

        if 'qris_image' in request.files:
            file = request.files['qris_image']
            if file and allowed_file(file.filename):
                saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                s = AppSettings.query.get('infaq_qris_image')
                if s: s.value = saved_filename
                else: db.session.add(AppSettings(key='infaq_qris_image', value=saved_filename))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
    return redirect(request.referrer)""")

content = content.replace("""@app.route('/idul-adha/absen', methods=['POST'])
def idul_adha_absen():
    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)

    # 06:30 AM to 08:30 AM
    start_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=8, minute=30, second=0, microsecond=0)

    if start_time <= current_time <= cutoff_time:
        status = 'Hadir Pagi'
    else:
        status = 'Terlambat'

    username = session.get('username', 'Unknown/Guest')

    attendance = QurbanAttendance(
        name=username,
        check_in_time=current_time,
        status=status
    )
    db.session.add(attendance)
    db.session.commit()

    if status == 'Hadir Pagi':
        flash('Berhasil absen. Anda tercatat Hadir Pagi.', 'success')
    else:
        flash('Absen gagal atau terlambat. Anda tercatat Terlambat.', 'error')

    return redirect(url_for('idul_adha_dashboard'))""", """@app.route('/idul-adha/absen', methods=['POST'])
def idul_adha_absen():
    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)

    # 06:30 AM to 08:30 AM
    start_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=8, minute=30, second=0, microsecond=0)

    if start_time <= current_time <= cutoff_time:
        status = 'Hadir Pagi'
    else:
        status = 'Terlambat'

    username = session.get('username', 'Unknown/Guest')

    try:
        attendance = QurbanAttendance(
            name=username,
            check_in_time=current_time,
            status=status
        )
        db.session.add(attendance)
        db.session.commit()

        if status == 'Hadir Pagi':
            flash('Berhasil absen. Anda tercatat Hadir Pagi.', 'success')
        else:
            flash('Absen gagal atau terlambat. Anda tercatat Terlambat.', 'error')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"DB Error: {e}")
        flash('Terjadi kesalahan sistem saat absensi.', 'error')

    return redirect(url_for('idul_adha_dashboard'))""")

content = content.replace("""@app.route('/idul-adha/distribution')
def idul_adha_distribution():
    # Segregate committee members based on attendance status
    hadir_pagi = QurbanAttendance.query.filter_by(status='Hadir Pagi').all()
    terlambat = QurbanAttendance.query.filter(QurbanAttendance.status.in_(['Terlambat', 'Siluman'])).all()

    # In a real scenario, this would render a specific distribution dashboard template.
    # For now, we return JSON to fulfill the logic requirement.
    return jsonify({
        'hadir_pagi_count': len(hadir_pagi),
        'terlambat_count': len(terlambat),
        'hadir_pagi_members': [a.name for a in hadir_pagi],
        'terlambat_members': [a.name for a in terlambat],
        'allocation_policy': {
            'Hadir Pagi': 'Full Meat Allocation',
            'Terlambat / Siluman': 'Leftover / Denied'
        }
    })""", """@app.route('/idul-adha/distribution')
def idul_adha_distribution():
    try:
        # Segregate committee members based on attendance status
        hadir_pagi = QurbanAttendance.query.filter_by(status='Hadir Pagi').all()
        terlambat = QurbanAttendance.query.filter(QurbanAttendance.status.in_(['Terlambat', 'Siluman'])).all()

        return jsonify({
            'hadir_pagi_count': len(hadir_pagi),
            'terlambat_count': len(terlambat),
            'hadir_pagi_members': [a.name for a in hadir_pagi],
            'terlambat_members': [a.name for a in terlambat],
            'allocation_policy': {
                'Hadir Pagi': 'Full Meat Allocation',
                'Terlambat / Siluman': 'Leftover / Denied'
            }
        })
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        return jsonify({'error': 'Terjadi kesalahan sistem'}), 500""")

with open(filename, "w") as f:
    f.write(content)
