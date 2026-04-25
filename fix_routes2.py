import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# 1. Absen Route
absen_pattern = r"@app\.route\('/idul-adha/absen',\s*methods=\['POST'\]\)\ndef idul_adha_absen\(\):.*?return redirect\(url_for\('idul_adha_dashboard'\)\)"

absen_new = """@app.route('/idul-adha/absen', methods=['GET', 'POST'])
def idul_adha_absen():
    settings = get_settings()
    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)

    absen_start_str = settings.get('absen_start', '06:30')
    absen_end_str = settings.get('absen_end', '08:30')

    try:
        start_h, start_m = map(int, absen_start_str.split(':'))
        end_h, end_m = map(int, absen_end_str.split(':'))
    except:
        start_h, start_m = 6, 30
        end_h, end_m = 8, 30

    start_time = current_time.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    is_open = start_time <= current_time <= cutoff_time
    is_admin = session.get('is_admin', False)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_settings' and is_admin:
            try:
                start_val = request.form.get('absen_start')
                end_val = request.form.get('absen_end')

                start_setting = AppSettings.query.filter_by(key='absen_start').first()
                if not start_setting:
                    start_setting = AppSettings(key='absen_start', value=start_val)
                    db.session.add(start_setting)
                else:
                    start_setting.value = start_val

                end_setting = AppSettings.query.filter_by(key='absen_end').first()
                if not end_setting:
                    end_setting = AppSettings(key='absen_end', value=end_val)
                    db.session.add(end_setting)
                else:
                    end_setting.value = end_val

                db.session.commit()
                flash('Konfigurasi waktu absen berhasil disimpan.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Gagal menyimpan konfigurasi.', 'error')
            return redirect(url_for('idul_adha_absen'))

        elif action == 'check_in':
            if not is_open:
                flash('Waktu absensi sudah ditutup.', 'error')
                return redirect(url_for('idul_adha_absen'))

            username = session.get('username', 'Unknown/Guest')
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            existing = QurbanAttendance.query.filter(QurbanAttendance.name == username, QurbanAttendance.check_in_time >= today_start).first()
            if existing:
                flash('Anda sudah melakukan absensi hari ini.', 'error')
                return redirect(url_for('idul_adha_absen'))

            try:
                attendance = QurbanAttendance(
                    name=username,
                    check_in_time=current_time,
                    status='Hadir Pagi'
                )
                db.session.add(attendance)
                db.session.commit()
                flash('Berhasil melakukan check in absensi.', 'success')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error absen: {e}")
                flash('Gagal melakukan absensi.', 'error')
            return redirect(url_for('idul_adha_absen'))

    attendances = QurbanAttendance.query.order_by(QurbanAttendance.check_in_time.desc()).all()

    rendered_content = render_template_string(IDUL_ADHA_ABSEN_HTML,
                                              is_admin=is_admin,
                                              is_open=is_open,
                                              settings=settings,
                                              attendances=attendances)
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=is_admin, settings=settings)

@app.route('/admin/qurban/absen/verify/<int:attendance_id>', methods=['POST'])
def admin_qurban_absen_verify(attendance_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        attendance = QurbanAttendance.query.get_or_404(attendance_id)
        attendance.verified_by_admin = True
        makassar_tz = pytz.timezone('Asia/Makassar')
        attendance.verified_at = datetime.datetime.now(makassar_tz)
        db.session.commit()
        flash('Absensi berhasil diverifikasi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Gagal memverifikasi absensi.', 'error')
    return redirect(url_for('idul_adha_absen'))"""

content = re.sub(absen_pattern, absen_new, content, flags=re.DOTALL)

# 2. Peta Route
peta_err_pattern = r"app\.logger\.error\(f\"Error in peta distribusi: \{e\}\"\)\n        return \"Internal Server Error\", 500"
peta_err_new = """app.logger.error(f"Error in admin peta distribusi: {e}")
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content="<div class='min-h-screen flex items-center justify-center p-4'><div class='bg-white p-8 rounded-3xl shadow-xl max-w-md text-center'><i class='fas fa-exclamation-triangle text-4xl text-red-500 mb-4'></i><h3 class='text-xl font-bold text-gray-800 mb-2'>Kesalahan Sistem</h3><p class='text-gray-600 mb-4'>Data peta distribusi belum dikonfigurasi atau terjadi kesalahan database.</p><a href='/idul-adha' class='inline-block bg-[#1B4332] text-white px-6 py-2 rounded-xl font-bold'>Kembali ke Dashboard</a></div></div>", is_admin=True, settings=get_settings())"""
content = re.sub(peta_err_pattern, peta_err_new, content)


public_peta_route = """@app.route('/idul-adha/peta', methods=['GET'])
def public_qurban_peta():
    try:
        slots = DistribusiSlot.query.order_by(DistribusiSlot.time_start.asc()).all()

        total_rt = len(slots)
        total_quota = sum(s.total_quota for s in slots)
        total_distributed = sum(s.distributed_count for s in slots)

        missing_rts = [s.rt_identifier for s in slots if not s.is_locked]

        rendered_content = render_template_string(IDUL_ADHA_PETA_DISTRIBUSI_HTML,
                                                  slots=slots,
                                                  total_rt=total_rt,
                                                  total_quota=total_quota,
                                                  total_distributed=total_distributed,
                                                  missing_rts=missing_rts,
                                                  is_admin=session.get('is_admin', False),
                                                  settings=get_settings())
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

    except Exception as e:
        app.logger.error(f"Error in public peta distribusi: {e}")
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content="<div class='min-h-screen flex items-center justify-center p-4'><div class='bg-white p-8 rounded-3xl shadow-xl max-w-md text-center'><i class='fas fa-exclamation-triangle text-4xl text-amber-500 mb-4'></i><h3 class='text-xl font-bold text-gray-800 mb-2'>Sedang Menyiapkan Peta</h3><p class='text-gray-600 mb-4'>Data peta distribusi belum tersedia atau sedang dalam pembaruan.</p><a href='/idul-adha' class='inline-block bg-[#1B4332] text-white px-6 py-2 rounded-xl font-bold'>Kembali</a></div></div>", is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/admin/qurban/peta'"""

if "def public_qurban_peta():" not in content:
    content = content.replace("@app.route('/admin/qurban/peta'", public_peta_route)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
