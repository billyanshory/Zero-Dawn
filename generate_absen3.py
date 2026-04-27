import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# 3. Add Backend Routes for Absen Panitia
# Find a good spot to insert routes, before idul_adha_dashboard
routes_code = """
import csv
from io import StringIO
from flask import make_response

@app.route('/idul-adha/absen-panitia')
def idul_adha_absen_panitia():
    # Make sure session has a unique identifier for regular users
    if not session.get('is_admin') and not session.get('user_session_id'):
        import uuid
        session['user_session_id'] = str(uuid.uuid4())
        session.permanent = True

    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)
    settings = get_settings()

    start_str = settings.get('absen_start_time', '06:30')
    end_str = settings.get('absen_end_time', '08:30')
    status_override = settings.get('absen_status', 'auto')

    sh, sm = map(int, start_str.split(':'))
    eh, em = map(int, end_str.split(':'))

    start_time = current_time.replace(hour=sh, minute=sm, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=eh, minute=em, second=0, microsecond=0)

    if status_override == 'open':
        is_valid_window = True
    elif status_override == 'closed':
        is_valid_window = False
    else:
        is_valid_window = start_time <= current_time <= cutoff_time

    rendered_content = render_template_string(IDUL_ADHA_ABSEN_PANITIA_HTML,
                                              is_valid_window=is_valid_window,
                                              settings=settings,
                                              is_admin=session.get('is_admin', False))

    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=settings)

@app.route('/idul-adha/absen-panitia/data')
def idul_adha_absen_data():
    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)
    settings = get_settings()

    start_str = settings.get('absen_start_time', '06:30')
    end_str = settings.get('absen_end_time', '08:30')
    status_override = settings.get('absen_status', 'auto')

    sh, sm = map(int, start_str.split(':'))
    eh, em = map(int, end_str.split(':'))

    start_time = current_time.replace(hour=sh, minute=sm, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=eh, minute=em, second=0, microsecond=0)

    if status_override == 'open':
        is_valid_window = True
    elif status_override == 'closed':
        is_valid_window = False
    else:
        is_valid_window = start_time <= current_time <= cutoff_time

    # Calculate Countdown String
    countdown_str = "--:--:--"
    if is_valid_window and status_override != 'open':
        diff = cutoff_time - current_time
        if diff.total_seconds() > 0:
            h, rem = divmod(diff.seconds, 3600)
            m, s = divmod(rem, 60)
            countdown_str = f"{h:02d}:{m:02d}:{s:02d}"

    # Get User Data
    user_data = None
    if session.get('user_session_id'):
        u = QurbanAttendance.query.filter_by(session_id=session.get('user_session_id')).first()
        if u:
            user_data = {
                'id': u.id, 'name': u.name, 'approval_status': u.approval_status,
                'is_present': u.is_present, 'pos_tugas': u.pos_tugas,
                'check_in_time': u.check_in_time.strftime("%H:%M") if u.check_in_time else None
            }

    # Get Admin Data
    all_data = []
    analytics = {'total': 0, 'hadir': 0, 'menunggu': 0, 'terlambat': 0}
    if session.get('is_admin'):
        all_panitia = QurbanAttendance.query.all()
        for p in all_panitia:
            all_data.append({
                'id': p.id, 'name': p.name, 'no_hp': p.no_hp,
                'approval_status': p.approval_status, 'is_present': p.is_present,
                'pos_tugas': p.pos_tugas,
                'check_in_time': p.check_in_time.strftime("%H:%M") if p.check_in_time else None
            })
            analytics['total'] += 1
            if p.is_present: analytics['hadir'] += 1
            if p.approval_status == 'Menunggu': analytics['menunggu'] += 1
            if not p.is_present and not is_valid_window: analytics['terlambat'] += 1

    return jsonify({
        'success': True,
        'is_window_open': is_valid_window,
        'countdown_str': countdown_str,
        'user_data': user_data,
        'all_data': all_data,
        'analytics': analytics
    })

@app.route('/idul-adha/absen-panitia/settings', methods=['POST'])
def idul_adha_absen_settings():
    if not session.get('is_admin'): return jsonify({'success': False}), 403
    req = request.get_json(silent=True) or {}
    for k in ['absen_start', 'absen_end', 'absen_status']:
        if k in req:
            key_name = f"{k}_time" if k != 'absen_status' else k
            s = AppSettings.query.get(key_name)
            if not s:
                s = AppSettings(key=key_name, value=req[k])
                db.session.add(s)
            else:
                s.value = req[k]
    try:
        db.session.commit()
        return jsonify({'success': True})
    except:
        db.session.rollback()
        return jsonify({'success': False})

@app.route('/idul-adha/absen-panitia/register', methods=['POST'])
def idul_adha_absen_register():
    req = request.get_json(silent=True) or {}
    if not req.get('name'): return jsonify({'success': False})

    sid = session.get('user_session_id')
    if not sid:
        import uuid
        sid = str(uuid.uuid4())
        session['user_session_id'] = sid
        session.permanent = True

    u = QurbanAttendance(
        name=req.get('name'), no_hp=req.get('hp'), tugas_diinginkan=req.get('tugas'),
        session_id=sid, approval_status='Menunggu'
    )
    db.session.add(u)
    try:
        db.session.commit()
        return jsonify({'success': True})
    except:
        db.session.rollback()
        return jsonify({'success': False})

@app.route('/idul-adha/absen-panitia/approve', methods=['POST'])
def idul_adha_absen_approve():
    if not session.get('is_admin'): return jsonify({'success': False}), 403
    req = request.get_json(silent=True) or {}
    u = QurbanAttendance.query.get(req.get('id'))
    if u:
        u.approval_status = 'Approved'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/idul-adha/absen-panitia/assign', methods=['POST'])
def idul_adha_absen_assign():
    if not session.get('is_admin'): return jsonify({'success': False}), 403
    req = request.get_json(silent=True) or {}
    u = QurbanAttendance.query.get(req.get('id'))
    if u:
        u.pos_tugas = req.get('pos_tugas')
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/idul-adha/absen-panitia/checkin', methods=['POST'])
def idul_adha_absen_checkin():
    sid = session.get('user_session_id')
    if not sid: return jsonify({'success': False, 'message': 'Session expired'})

    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)

    u = QurbanAttendance.query.filter_by(session_id=sid).first()
    if u and u.approval_status == 'Approved' and not u.is_present:
        u.is_present = True
        u.check_in_time = current_time
        u.status = 'Hadir Pagi'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Gagal check-in'})

@app.route('/idul-adha/absen-panitia/export')
def idul_adha_absen_export():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_dashboard'))

    panitia = QurbanAttendance.query.all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Nama Lengkap', 'No HP', 'Waktu Hadir', 'Status Approval', 'Pos Tugas', 'Status Kehadiran'])

    for p in panitia:
        cw.writerow([
            p.id, p.name, p.no_hp, p.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if p.check_in_time else '-',
            p.approval_status, p.pos_tugas or '-', 'Hadir' if p.is_present else 'Belum/Terlambat'
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=Laporan_Absensi_Panitia_Qurban.csv"
    output.headers["Content-type"] = "text/csv"
    return output

"""

content = content.replace("def idul_adha_dashboard():", routes_code + "\ndef idul_adha_dashboard():")

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
