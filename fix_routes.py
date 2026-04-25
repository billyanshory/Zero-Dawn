import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Fix 1: idul-adha/absen
absen_old = """@app.route('/idul-adha/absen', methods=['POST'])
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

        flash('Berhasil absen.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error absen: {e}")
        flash('Gagal absen.', 'error')

    return redirect(url_for('idul_adha_dashboard'))"""

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

if absen_old in content:
    content = content.replace(absen_old, absen_new)
else:
    print("Could not find old absen route")

# Fix 2: Peta Distribusi route (public and admin changes)
peta_old = """@app.route('/admin/qurban/peta', methods=['GET', 'POST'])
def admin_qurban_peta():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:"""

peta_new = """@app.route('/idul-adha/peta', methods=['GET'])
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

@app.route('/admin/qurban/peta', methods=['GET', 'POST'])
def admin_qurban_peta():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:"""

if peta_old in content:
    content = content.replace(peta_old, peta_new)
else:
    print("Could not find old peta route")

peta_err_old = """    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in peta distribusi: {e}")
        return "Internal Server Error", 500"""

peta_err_new = """    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in admin peta distribusi: {e}")
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content="<div class='min-h-screen flex items-center justify-center p-4'><div class='bg-white p-8 rounded-3xl shadow-xl max-w-md text-center'><i class='fas fa-exclamation-triangle text-4xl text-red-500 mb-4'></i><h3 class='text-xl font-bold text-gray-800 mb-2'>Kesalahan Sistem</h3><p class='text-gray-600 mb-4'>Data peta distribusi belum dikonfigurasi atau terjadi kesalahan database.</p><a href='/idul-adha' class='inline-block bg-[#1B4332] text-white px-6 py-2 rounded-xl font-bold'>Kembali ke Dashboard</a></div></div>", is_admin=True, settings=get_settings())"""

if peta_err_old in content:
    content = content.replace(peta_err_old, peta_err_new)
else:
    print("Could not find old peta error block")

# Make sure IDUL_ADHA_DASHBOARD_HTML is fixed too (Feature 1 and 5)
dash_absen_old = """                    <form action="/idul-adha/absen" method="POST" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-amber-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-amber-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300 relative cursor-pointer" onclick="this.submit()">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <div class="bg-amber-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-amber-700 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                            <i class="fas fa-clipboard-check text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#78350f] group-hover:text-amber-700">Absen Panitia</span>
                        <span class="text-[10px] text-amber-600 font-medium absolute bottom-3">Batas: 08:30 AM</span>
                    </form>"""

dash_absen_new = """                    <a href="/idul-adha/absen" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-amber-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-amber-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300 relative cursor-pointer block">
                        <div class="bg-amber-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-amber-700 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                            <i class="fas fa-clipboard-check text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#78350f] group-hover:text-amber-700">Absen Panitia</span>
                        <span class="text-[10px] text-amber-600 font-medium absolute bottom-3">Manajemen Absensi</span>
                    </a>"""

if dash_absen_old in content:
    content = content.replace(dash_absen_old, dash_absen_new)

dash_peta_old = """                    <a href="/admin/qurban/peta" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-[#1B4332]/10 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-[#1B4332]/5 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-blue-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-700 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                            <i class="fas fa-map-marked-alt text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#1B4332] group-hover:text-blue-700">Peta Distribusi</span>
                        <span class="text-[10px] text-gray-400 font-medium absolute bottom-3">Monitoring RT</span>
                    </a>"""

dash_peta_new = """                    <a href="/idul-adha/peta" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-[#1B4332]/10 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-[#1B4332]/5 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-blue-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-700 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                            <i class="fas fa-map-marked-alt text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#1B4332] group-hover:text-blue-700">Peta Distribusi</span>
                        <span class="text-[10px] text-gray-400 font-medium absolute bottom-3">Monitoring RT</span>
                    </a>"""

if dash_peta_old in content:
    content = content.replace(dash_peta_old, dash_peta_new)

# Add IDUL_ADHA_ABSEN_HTML
template_html = '''
IDUL_ADHA_ABSEN_HTML = """
<div class="min-h-screen bg-[#F5F0E8] font-sans pt-20 md:pt-24 pb-20">
    <div class="max-w-4xl mx-auto px-4 relative z-10">
        <!-- Header -->
        <div class="bg-[#1B4332] text-white py-6 px-6 md:px-8 rounded-3xl shadow-xl mb-8 relative overflow-hidden">
            <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <a href="/idul-adha" class="inline-flex items-center gap-2 text-white/80 hover:text-white mb-4 text-sm font-bold bg-white/10 px-4 py-2 rounded-full w-max backdrop-blur-sm transition-colors border border-white/20">
                        <i class="fas fa-arrow-left"></i> Kembali ke Dashboard
                    </a>
                    <h1 class="text-3xl font-bold mb-2 tracking-tight text-[#D4A017]">Absen Panitia</h1>
                    <p class="text-[#F5F0E8]/80 text-sm max-w-xl">
                        Kehadiran panitia Qurban Idul Adha Masjid Al-Hijrah.
                    </p>
                </div>
            </div>
            <!-- Decorative Elements -->
            <div class="absolute right-0 top-0 w-64 h-64 bg-[#D4A017] rounded-full mix-blend-multiply filter blur-3xl opacity-20 transform translate-x-1/2 -translate-y-1/2"></div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="mb-8">
                    {% for category, message in messages %}
                        <div class="p-4 rounded-xl shadow-md border-l-4 {% if category == 'success' %}bg-green-50 border-green-500 text-green-700{% elif category == 'error' %}bg-red-50 border-red-500 text-red-700{% else %}bg-blue-50 border-blue-500 text-blue-700{% endif %}">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        {% if is_admin %}
        <!-- ADMIN PANEL -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-yellow-500/20 mb-8 w-full">
            <h3 class="text-lg font-bold text-[#D4A017] mb-4 border-b border-gray-100 pb-3"><i class="fas fa-lock mr-2"></i>Panel Admin: Konfigurasi Waktu Absen</h3>
            <form action="/idul-adha/absen" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="hidden" name="action" value="update_settings"/>

                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Mulai Absen (HH:MM)</label>
                    <input type="time" name="absen_start" value="{{ settings.get('absen_start', '06:30') }}" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Batas Akhir (HH:MM)</label>
                    <input type="time" name="absen_end" value="{{ settings.get('absen_end', '08:30') }}" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                </div>

                <div class="md:col-span-2">
                    <button type="submit" class="w-full bg-[#1B4332] text-white font-bold py-3 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">
                        <i class="fas fa-save"></i> Simpan Konfigurasi
                    </button>
                </div>
            </form>
        </div>
        {% endif %}

        {% if not is_admin %}
        <!-- PUBLIC PANEL -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100 mb-8 w-full text-center">
            {% if is_open %}
                <h3 class="text-2xl font-bold text-[#1B4332] mb-2">Absensi Dibuka</h3>
                <p class="text-gray-600 mb-6">Waktu Absensi: {{ settings.get('absen_start', '06:30') }} - {{ settings.get('absen_end', '08:30') }} WITA</p>
                <form action="/idul-adha/absen" method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input type="hidden" name="action" value="check_in"/>
                    <button type="submit" class="w-full bg-[#D4A017] text-[#1B4332] font-bold py-4 rounded-xl hover:bg-[#b8860b] transition shadow-xl text-lg flex items-center justify-center gap-2">
                        <i class="fas fa-check-circle"></i> Check In Sekarang
                    </button>
                </form>
            {% else %}
                <div class="text-red-600 mb-2"><i class="fas fa-times-circle text-5xl"></i></div>
                <h3 class="text-2xl font-bold text-red-700 mb-2">Absensi Ditutup</h3>
                <p class="text-gray-600">Waktu Absensi: {{ settings.get('absen_start', '06:30') }} - {{ settings.get('absen_end', '08:30') }} WITA</p>
            {% endif %}
        </div>
        {% endif %}

        <!-- DATA LIST -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100 w-full">
            <h3 class="text-lg font-bold text-[#1B4332] mb-4 border-b border-gray-100 pb-3">Daftar Hadir Panitia</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm whitespace-nowrap">
                    <thead class="bg-gray-50 text-gray-600">
                        <tr>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px] rounded-tl-lg">Nama</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px]">Waktu</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px]">Status</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px] rounded-tr-lg">Verifikasi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 text-gray-700">
                        {% for a in attendances %}
                        <tr class="hover:bg-gray-50 transition">
                            <td class="p-4 font-bold text-gray-900">{{ a.name }}</td>
                            <td class="p-4">{{ a.check_in_time.strftime('%H:%M:%S') }}</td>
                            <td class="p-4">
                                <span class="px-2 py-1 text-xs font-bold rounded-lg {% if a.status == 'Hadir Pagi' %}bg-green-100 text-green-700{% else %}bg-red-100 text-red-700{% endif %}">
                                    {{ a.status }}
                                </span>
                            </td>
                            <td class="p-4">
                                {% if a.verified_by_admin %}
                                    <span class="inline-flex items-center gap-1 text-green-600 font-bold text-xs"><i class="fas fa-check-double"></i> Terverifikasi</span>
                                {% else %}
                                    {% if is_admin %}
                                    <form action="/admin/qurban/absen/verify/{{ a.id }}" method="POST" class="inline">
                                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                        <button type="submit" class="bg-green-600 text-white text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-green-700 transition">Verifikasi</button>
                                    </form>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 text-amber-600 font-bold text-xs"><i class="fas fa-hourglass-half"></i> Menunggu Verifikasi</span>
                                    {% endif %}
                                {% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" class="p-4 text-center text-gray-500 text-sm">Belum ada data absensi.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
"""
'''

if 'IDUL_ADHA_ABSEN_HTML =' not in content:
    content = content.replace("IDUL_ADHA_DASHBOARD_HTML = \"\"\"", template_html + "\n\nIDUL_ADHA_DASHBOARD_HTML = \"\"\"")

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
