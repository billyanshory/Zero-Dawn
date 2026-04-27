import re

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# 1. Update Laporan HTML & Route
new_laporan_html = """IDUL_ADHA_LAPORAN_HTML = '''
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800">
    <div class="max-w-4xl mx-auto">
        <div class="flex items-center gap-4 mb-8">
            <a href="/idul-adha" class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 shadow-md hover:bg-[#8B2635] hover:text-white transition-colors">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div>
                <h1 class="text-3xl font-bold text-[#8B2635]">Laporan Qurban</h1>
                <p class="text-gray-500 mt-1">Papan Skor Transparansi Publik Masjid Al Hijrah</p>
            </div>
        </div>

        {% if is_admin %}
        <div class="bg-white rounded-3xl shadow-xl border border-[#8B2635] p-6 mb-8 relative">
            <div class="absolute top-0 right-0 bg-[#8B2635] text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-lock mr-1"></i> Panel Admin</div>
            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Edit Data Laporan Qurban</h2>
            <form action="/idul-adha/laporan" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Total Sapi</label>
                    <input type="number" name="total_sapi" value="{{ report.total_sapi }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Total Kambing</label>
                    <input type="number" name="total_kambing" value="{{ report.total_kambing }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Estimasi Daging (Kg)</label>
                    <input type="number" name="estimasi_daging" value="{{ report.estimasi_daging }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Terdistribusi</label>
                        <input type="number" name="paket_terdistribusi" value="{{ report.paket_terdistribusi }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Total Paket</label>
                        <input type="number" name="paket_total" value="{{ report.paket_total }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                    </div>
                </div>
                <div class="md:col-span-2 mt-2">
                    <button type="submit" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Save / Update Data</button>
                </div>
            </form>
        </div>
        {% endif %}

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-6 flex items-center gap-6">
                <div class="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center text-[#8B2635] text-3xl">
                    <i class="fas fa-cow"></i>
                </div>
                <div>
                    <p class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Total Hewan</p>
                    <div class="flex items-baseline gap-2 mt-1">
                        <span class="text-3xl font-bold text-gray-800">{{ report.total_sapi if report else 12 }}</span><span class="text-gray-500">Sapi</span>
                    </div>
                    <div class="flex items-baseline gap-2 mt-1">
                        <span class="text-3xl font-bold text-gray-800">{{ report.total_kambing if report else 20 }}</span><span class="text-gray-500">Kambing</span>
                    </div>
                </div>
            </div>
            <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-6 flex items-center gap-6">
                <div class="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center text-[#D4A017] text-3xl">
                    <i class="fas fa-weight-hanging"></i>
                </div>
                <div>
                    <p class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Estimasi Daging</p>
                    <div class="flex items-baseline gap-2 mt-1">
                        <span class="text-4xl font-bold text-gray-800">{{ '{:,}'.format(report.estimasi_daging).replace(',', '.') if report else '1.500' }}</span>
                        <span class="text-xl text-gray-500 font-medium">Kg</span>
                    </div>
                </div>
            </div>
            <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-6 flex items-center gap-6">
                <div class="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center text-[#1B4332] text-3xl">
                    <i class="fas fa-box-open"></i>
                </div>
                <div>
                    <p class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Paket Terdistribusi</p>
                    <div class="flex items-baseline gap-2 mt-1">
                        <span class="text-4xl font-bold text-gray-800">{{ '{:,}'.format(report.paket_terdistribusi).replace(',', '.') if report else '450' }}</span>
                        <span class="text-xl text-gray-500 font-medium">/ {{ '{:,}'.format(report.paket_total).replace(',', '.') if report else '1.000' }}</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 text-center">
            <div class="inline-flex items-center justify-center w-20 h-20 bg-green-50 rounded-full text-green-500 mb-4">
                <i class="fas fa-check-circle text-4xl"></i>
            </div>
            <h2 class="text-2xl font-bold text-gray-800 mb-2">Transparansi Penyaluran</h2>
            <p class="text-gray-600 leading-relaxed max-w-2xl mx-auto">
                Alhamdulillah, proses penyembelihan dan penyaluran daging qurban Masjid Al Hijrah dilakukan secara profesional, jujur, dan amanah. Seluruh donasi dan daging dikelola dan disalurkan tepat sasaran kepada yang berhak.
            </p>
        </div>
    </div>
</div>
'''"""
content = re.sub(r'IDUL_ADHA_LAPORAN_HTML = """(.*?)"""', new_laporan_html, content, flags=re.DOTALL, count=1)

new_laporan_route = """@app.route('/idul-adha/laporan', methods=['GET', 'POST'])
def idul_adha_laporan():
    report = QurbanReport.query.first()
    if not report:
        report = QurbanReport(total_sapi=12, total_kambing=20, estimasi_daging=1500, paket_terdistribusi=450, paket_total=1000)
        db.session.add(report)
        db.session.commit()

    if request.method == 'POST' and session.get('is_admin'):
        report.total_sapi = int(request.form.get('total_sapi', 0))
        report.total_kambing = int(request.form.get('total_kambing', 0))
        report.estimasi_daging = int(request.form.get('estimasi_daging', 0))
        report.paket_terdistribusi = int(request.form.get('paket_terdistribusi', 0))
        report.paket_total = int(request.form.get('paket_total', 0))
        try:
            db.session.commit()
            flash("Data berhasil disimpan", "success")
        except:
            db.session.rollback()
        return redirect(url_for('idul_adha_laporan'))

    rendered_content = render_template_string(IDUL_ADHA_LAPORAN_HTML, report=report, is_admin=session.get('is_admin', False), settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())"""

content = re.sub(r"@app\.route\('/idul-adha/laporan'\)\ndef idul_adha_laporan\(\):\n    return render_template_string\(BASE_LAYOUT, \n                                  styles=STYLES_HTML, \n                                  active_page='idul-adha', \n                                  content=IDUL_ADHA_LAPORAN_HTML,\n                                  is_admin=session\.get\('is_admin', False\),\n                                  settings=get_settings\(\)\)", new_laporan_route, content, flags=re.DOTALL, count=1)


# 2. Update Shohibul HTML & Route
new_shohibul_html = """IDUL_ADHA_SHOHIBUL_HTML = '''
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800">
    <div class="max-w-2xl mx-auto">
        <div class="flex items-center gap-4 mb-8">
            <a href="/idul-adha" class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 shadow-md hover:bg-[#8B2635] hover:text-white transition-colors">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div>
                <h1 class="text-3xl font-bold text-[#8B2635]">Pelacak Status Qurban</h1>
                <p class="text-gray-500 mt-1">Daftar Shohibul & Tracker Hewan</p>
            </div>
        </div>

        {% if is_admin %}
        <div class="bg-white rounded-3xl shadow-xl border border-[#8B2635] p-6 mb-8 relative">
            <div class="absolute top-0 right-0 bg-[#8B2635] text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-lock mr-1"></i> Panel Admin</div>
            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Generate PIN Shohibul</h2>
            <form action="/idul-adha/shohibul/generate" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Jenis Hewan</label>
                    <select name="jenis_hewan" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                        <option value="Sapi">Sapi (SQ)</option>
                        <option value="Kambing">Kambing (KQ)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Nama Shohibul (1 atau lebih)</label>
                    <textarea name="nama_shohibul" rows="2" placeholder="Bapak Abdullah, Ibu Siti, dsb" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required></textarea>
                </div>
                <button type="submit" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Generate & Save</button>
            </form>
        </div>
        {% endif %}

        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 mb-8">
            <h2 class="text-xl font-bold text-gray-800 mb-4">Lacak Status Sapi / Kambing Anda</h2>
            <p class="text-gray-600 mb-6">Masukkan PIN unik yang telah dikirimkan melalui WhatsApp untuk melihat status penyembelihan secara real-time. Tidak perlu repot datang ke masjid untuk bertanya.</p>
            <form action="/idul-adha/shohibul" method="GET" class="flex gap-4">
                <input type="text" name="pin" value="{{ request.args.get('pin', '') }}" placeholder="Masukkan PIN Anda (contoh: SQ-001)" class="w-full px-5 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#8B2635] focus:border-transparent text-gray-700 font-medium">
                <button type="submit" class="bg-[#8B2635] text-white px-8 py-3 rounded-xl font-bold hover:bg-red-800 transition-colors shadow-md whitespace-nowrap">Lacak</button>
            </form>
        </div>

        {% if shohibul %}
        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8">
            <div class="flex items-center justify-between mb-8 pb-6 border-b border-gray-100">
                <div>
                    <h3 class="text-lg font-bold text-gray-800">{{ shohibul.jenis_hewan }} ({{ shohibul.nama_shohibul }})</h3>
                    <p class="text-sm text-gray-500">PIN: {{ shohibul.pin }}</p>
                </div>
                <span class="bg-amber-100 text-amber-700 px-4 py-1.5 rounded-full text-sm font-bold shadow-sm">{{ shohibul.status }}</span>
            </div>

            <div class="space-y-6 relative">
                {% set states = [
                    ('Menunggu Giliran', 'Hewan qurban telah tiba dan sedang diistirahatkan.', 'fas fa-hourglass-half'),
                    ('Sedang Disembelih', 'Alhamdulillah, proses penyembelihan sedang berlangsung sesuai syariat.', 'fas fa-knife'),
                    ('Proses Pencacahan', 'Daging sedang dicacah dan ditimbang oleh panitia.', 'fas fa-drumstick-bite'),
                    ('Jatah Sohibul Siap Diambil', 'Sepertiga bagian Anda telah siap. Silakan ambil di pos panitia.', 'fas fa-box-open')
                ] %}

                {% for state, desc, icon in states %}
                    {% set is_active = shohibul.status == state %}

                    {% if is_admin %}
                    <form action="/idul-adha/shohibul/update_status" method="POST" class="cursor-pointer">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="pin" value="{{ shohibul.pin }}">
                        <input type="hidden" name="status" value="{{ state }}">
                        <button type="submit" class="w-full text-left">
                    {% endif %}

                    <div class="flex items-start gap-4 {{ '' if is_active else 'opacity-40 grayscale' }} hover:opacity-100 hover:grayscale-0 transition-all duration-300">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center mt-1 {{ 'bg-amber-100 text-amber-600 ring-4 ring-amber-50' if is_active else 'bg-gray-100 text-gray-400' }}">
                            <i class="{{ icon }}"></i>
                        </div>
                        <div>
                            <h4 class="font-bold {{ 'text-[#8B2635]' if is_active else 'text-gray-500' }}">{{ state }}</h4>
                            <p class="text-sm {{ 'text-gray-600' if is_active else 'text-gray-400' }}">{{ desc }}</p>
                            {% if is_active and state == 'Menunggu Giliran' %}<span class="text-xs text-amber-600 mt-1 block font-medium">Selesai: 08:30 WITA</span>{% endif %}
                            {% if is_active and state == 'Sedang Disembelih' %}<span class="text-xs text-amber-600 mt-1 block font-medium">Sedang Berlangsung...</span>{% endif %}
                        </div>
                    </div>

                    {% if is_admin %}
                        </button>
                    </form>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        {% elif request.args.get('pin') %}
        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 text-center">
             <p class="text-red-500 font-bold">Data dengan PIN tersebut tidak ditemukan.</p>
        </div>
        {% endif %}
    </div>
</div>
'''"""
content = re.sub(r'IDUL_ADHA_SHOHIBUL_HTML = """(.*?)"""', new_shohibul_html, content, flags=re.DOTALL, count=1)

new_shohibul_route = """@app.route('/idul-adha/shohibul')
def idul_adha_shohibul():
    pin = request.args.get('pin', '')
    shohibul = None
    if pin:
        shohibul = QurbanShohibul.query.filter_by(pin=pin).first()

    rendered_content = render_template_string(IDUL_ADHA_SHOHIBUL_HTML, shohibul=shohibul, is_admin=session.get('is_admin', False), settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/idul-adha/shohibul/generate', methods=['POST'])
def idul_adha_shohibul_generate():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_shohibul'))
    jenis = request.form.get('jenis_hewan')
    nama = request.form.get('nama_shohibul')
    prefix = 'SQ' if jenis == 'Sapi' else 'KQ'
    last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
    if last_record:
        last_num = int(last_record.pin.split('-')[1])
        next_num = last_num + 1
    else:
        next_num = 1
    new_pin = f"{prefix}-{next_num:03d}"
    shohibul = QurbanShohibul(pin=new_pin, jenis_hewan=jenis, nama_shohibul=nama)
    try:
        db.session.add(shohibul)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for('idul_adha_shohibul', pin=new_pin))

@app.route('/idul-adha/shohibul/update_status', methods=['POST'])
def idul_adha_shohibul_update_status():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_shohibul'))
    pin = request.form.get('pin')
    status = request.form.get('status')
    shohibul = QurbanShohibul.query.filter_by(pin=pin).first()
    if shohibul:
        shohibul.status = status
        try:
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('idul_adha_shohibul', pin=pin))"""
content = re.sub(r"@app\.route\('/idul-adha/shohibul'\)\ndef idul_adha_shohibul\(\):\n    return render_template_string\(BASE_LAYOUT, \n                                  styles=STYLES_HTML, \n                                  active_page='idul-adha', \n                                  content=IDUL_ADHA_SHOHIBUL_HTML,\n                                  is_admin=session\.get\('is_admin', False\),\n                                  settings=get_settings\(\)\)", new_shohibul_route, content, flags=re.DOTALL, count=1)


# 3. Update Pembagian HTML & Route
new_pembagian_html = """IDUL_ADHA_PEMBAGIAN_HTML = '''
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800">
    <div class="max-w-2xl mx-auto">
        <div class="flex items-center gap-4 mb-8">
            <a href="/idul-adha" class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 shadow-md hover:bg-[#1B4332] hover:text-white transition-colors">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div>
                <h1 class="text-3xl font-bold text-[#1B4332]">Antrean Distribusi Daging</h1>
                <p class="text-gray-500 mt-1">Sistem Kupon Digital & Penjadwalan Warga</p>
            </div>
        </div>

        {% if is_admin %}
        <div class="bg-white rounded-3xl shadow-xl border border-[#1B4332] p-6 mb-8 relative">
            <div class="absolute top-0 right-0 bg-[#1B4332] text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-lock mr-1"></i> Panel Admin</div>
            <h2 class="text-xl font-bold text-[#1B4332] mb-4">Generate E-Kupon Qurban</h2>
            <form action="/idul-adha/pembagian/generate" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Nama Penerima</label>
                    <input type="text" name="nama_penerima" placeholder="Bapak Budi Santoso" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#1B4332]" required>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">RT</label>
                        <input type="text" name="rt" placeholder="RT 02" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#1B4332]" required>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Waktu Pengambilan</label>
                        <input type="text" name="waktu_pengambilan" placeholder="13.30 - 14.00 WITA" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#1B4332]" required>
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Lokasi Pengambilan (Teks)</label>
                    <textarea name="lokasi_pengambilan" rows="2" placeholder="di Rumah Pak RT sama Pak RT" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#1B4332]" required></textarea>
                </div>
                <button type="submit" class="w-full bg-[#1B4332] text-white font-bold py-3 rounded-xl hover:bg-green-900 shadow-md">Generate & Save Kupon</button>
            </form>
        </div>
        {% endif %}

        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 mb-8">
            <div class="flex items-center justify-center w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full mb-6 mx-auto">
                <i class="fas fa-ticket-alt text-3xl"></i>
            </div>
            <h2 class="text-2xl font-bold text-center text-gray-800 mb-2">Cek Jam Pengambilan</h2>
            <p class="text-center text-gray-600 mb-8 max-w-md mx-auto">
                Masukkan Nama Lengkap Anda atau Nomor Kupon yang diberikan oleh RT. Sistem akan menampilkan jadwal pengambilan untuk menghindari kerumunan.
            </p>
            <form action="/idul-adha/distribution" method="GET" class="space-y-5">
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Nama Lengkap / No. Kupon</label>
                    <input type="text" name="q" value="{{ request.args.get('q', '') }}" placeholder="Cth: Budi Santoso atau KPN-001" class="w-full px-5 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-gray-700 font-medium">
                </div>
                <button type="submit" class="w-full bg-emerald-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-emerald-700 transition-colors shadow-md">
                    Cek Jadwal Saya
                </button>
            </form>
        </div>

        {% if kupon %}
        <div id="hasil-kupon" class="bg-[#1B4332] rounded-3xl shadow-2xl p-8 text-white relative overflow-hidden">
            <div class="absolute -right-10 -top-10 text-emerald-800 opacity-20">
                <i class="fas fa-qrcode text-9xl"></i>
            </div>
            <div class="relative z-10">
                <div class="flex justify-between items-start mb-6 border-b border-emerald-700 pb-6">
                    <div>
                        <p class="text-emerald-200 text-sm font-medium uppercase tracking-wider mb-1">E-Kupon Valid</p>
                        <h3 class="text-2xl font-bold">{{ kupon.nomor_kupon }}</h3>
                    </div>
                    <div class="bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase">
                        {{ kupon.rt }}
                    </div>
                </div>
                <div class="mb-8">
                    <p class="text-emerald-200 text-sm mb-1">Nama Penerima</p>
                    <p class="font-bold text-xl">{{ kupon.nama_penerima }}</p>
                </div>
                <div class="bg-white/10 rounded-2xl p-5 backdrop-blur-sm border border-white/20">
                    <div class="flex items-center gap-4 text-amber-300 mb-2">
                        <i class="far fa-clock text-2xl"></i>
                        <span class="font-bold text-lg">Waktu Pengambilan:</span>
                    </div>
                    <p class="text-3xl font-black text-white ml-10">{{ kupon.waktu_pengambilan }}</p>

                    <div class="flex items-center gap-4 text-amber-300 mt-4 mb-2">
                        <i class="fas fa-map-marker-alt text-2xl ml-1"></i>
                        <span class="font-bold text-lg">Lokasi Pengambilan:</span>
                    </div>
                    <p class="text-xl font-bold text-white ml-10">{{ kupon.lokasi_pengambilan }}</p>

                    <p class="text-sm text-emerald-100 mt-4 ml-10 flex items-start gap-2 border-t border-white/10 pt-4">
                        <i class="fas fa-exclamation-circle mt-0.5"></i>
                        Mohon datang tepat waktu sesuai jadwal agar tidak terjadi antrean panjang di lokasi.
                    </p>
                </div>
            </div>
        </div>
        {% elif request.args.get('q') %}
        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 text-center">
             <p class="text-red-500 font-bold">Data kupon tidak ditemukan.</p>
        </div>
        {% endif %}
    </div>
</div>
'''"""
content = re.sub(r'IDUL_ADHA_PEMBAGIAN_HTML = """(.*?)"""', new_pembagian_html, content, flags=re.DOTALL, count=1)

new_pembagian_route = """@app.route('/idul-adha/distribution')
def idul_adha_distribution():
    q = request.args.get('q', '')
    kupon = None
    if q:
        kupon = QurbanKupon.query.filter((QurbanKupon.nomor_kupon == q) | (QurbanKupon.nama_penerima.like(f"%{q}%"))).first()

    rendered_content = render_template_string(IDUL_ADHA_PEMBAGIAN_HTML, kupon=kupon, is_admin=session.get('is_admin', False), settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/idul-adha/pembagian/generate', methods=['POST'])
def idul_adha_pembagian_generate():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_distribution'))
    nama = request.form.get('nama_penerima')
    rt = request.form.get('rt')
    waktu = request.form.get('waktu_pengambilan')
    lokasi = request.form.get('lokasi_pengambilan')
    last_record = QurbanKupon.query.filter(QurbanKupon.nomor_kupon.like("KPN-%")).order_by(QurbanKupon.id.desc()).first()
    if last_record:
        last_num = int(last_record.nomor_kupon.split('-')[1])
        next_num = last_num + 1
    else:
        next_num = 1
    new_kupon = f"KPN-{next_num:03d}"
    kupon_entry = QurbanKupon(nomor_kupon=new_kupon, nama_penerima=nama, rt=rt, waktu_pengambilan=waktu, lokasi_pengambilan=lokasi)
    try:
        db.session.add(kupon_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for('idul_adha_distribution', q=new_kupon))"""
content = re.sub(r"@app\.route\('/idul-adha/distribution'\)\ndef idul_adha_distribution\(\):\n    # Segregate committee members based on attendance status\n    hadir_pagi = QurbanAttendance\.query\.filter_by\(status='Hadir Pagi'\)\.all\(\)\n    terlambat = QurbanAttendance\.query\.filter\(QurbanAttendance\.status\.in_\(\['Terlambat', 'Siluman'\]\)\)\.all\(\)\n    \n    return render_template_string\(BASE_LAYOUT, \n                                  styles=STYLES_HTML, \n                                  active_page='idul-adha', \n                                  content=IDUL_ADHA_PEMBAGIAN_HTML,\n                                  is_admin=session\.get\('is_admin', False\),\n                                  settings=get_settings\(\)\)", new_pembagian_route, content, flags=re.DOTALL, count=1)


# 4. Update Peta HTML & Route
new_peta_html = """IDUL_ADHA_PETA_DISTRIBUSI_HTML = '''
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800">
    <div class="max-w-4xl mx-auto">
        <div class="flex items-center gap-4 mb-8">
            <a href="/idul-adha" class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 shadow-md hover:bg-orange-600 hover:text-white transition-colors">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div>
                <h1 class="text-3xl font-bold text-orange-600">Peta Distribusi</h1>
                <p class="text-gray-500 mt-1">Log Penyaluran Daging Berbasis Wilayah RT</p>
            </div>
        </div>

        {% if is_admin %}
        <div class="bg-white rounded-3xl shadow-xl border border-orange-600 p-6 mb-8 relative">
            <div class="absolute top-0 right-0 bg-orange-600 text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-lock mr-1"></i> Panel Admin</div>
            <h2 class="text-xl font-bold text-orange-600 mb-4">Tambah Data RT Baru</h2>
            <form action="/idul-adha/peta-distribusi/add" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Nomor Card</label>
                        <input type="text" name="nomor_card" placeholder="01" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Nama RT</label>
                        <input type="text" name="rt_name" placeholder="RT 01" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Ketua RT</label>
                        <input type="text" name="nama_ketua_rt" placeholder="Bpk. Haryanto" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-1">Alokasi (Kantong)</label>
                        <input type="number" name="alokasi" placeholder="50" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                    </div>
                </div>
                <button type="submit" class="w-full bg-orange-600 text-white font-bold py-3 rounded-xl hover:bg-orange-700 shadow-md">Tambah Data RT</button>
            </form>
        </div>
        {% endif %}

        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 mb-8">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-4">Pemetaan Mustahik</h2>
                    <p class="text-gray-600 mb-6">
                        Sistem ini memastikan tidak ada tumpang tindih alokasi. Saat Ketua RT menerima jatah paket daging, sistem akan mengunci status RT tersebut untuk mencegah klaim ganda, menjamin distribusi merata dan adil.
                    </p>
                    <div class="flex gap-4">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                            <span class="text-sm font-medium text-gray-600">Sudah Menerima</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-gray-300"></span>
                            <span class="text-sm font-medium text-gray-600">Belum Menerima</span>
                        </div>
                    </div>
                </div>
                <div class="bg-orange-50 rounded-2xl p-6 text-center border border-orange-100">
                    <p class="text-orange-800 font-bold mb-2">Total Progres Wilayah</p>
                    <div class="flex items-end justify-center gap-2">
                        <span class="text-5xl font-black text-orange-600">{{ diserahkan_count }}</span>
                        <span class="text-xl text-orange-400 font-bold mb-1">/ {{ total_rt }} RT</span>
                    </div>
                    <div class="w-full bg-orange-200 rounded-full h-2 mt-4">
                        <div class="bg-orange-500 h-2 rounded-full" style="width: {{ progress_percentage }}%"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
            {% for rt in rt_list %}
            <div class="bg-white rounded-2xl border-2 {{ 'border-emerald-100' if rt.status == 'Diserahkan' else 'border-gray-200' }} p-5 shadow-sm relative overflow-hidden group">
                {% if rt.status == 'Diserahkan' %}
                <div class="absolute top-0 right-0 bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-bl-xl">Terkunci</div>
                {% endif %}

                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 {{ 'bg-emerald-50 text-emerald-600' if rt.status == 'Diserahkan' else 'bg-gray-100 text-gray-500' }} rounded-xl flex items-center justify-center text-xl font-bold">{{ rt.nomor_card }}</div>
                        <div>
                            <h3 class="font-bold text-gray-800">{{ rt.rt_name }}</h3>
                            <p class="text-xs text-gray-500">{{ rt.nama_ketua_rt }}</p>
                        </div>
                    </div>
                    {% if is_admin %}
                    <button onclick="openEditRTModal('{{ rt.id }}', '{{ rt.nomor_card }}', '{{ rt.rt_name }}', '{{ rt.nama_ketua_rt }}', '{{ rt.alokasi }}', '{{ rt.status }}')" class="text-gray-400 hover:text-orange-600 transition"><i class="fas fa-pencil-alt"></i></button>
                    {% endif %}
                </div>

                <div class="bg-gray-50 rounded-lg p-3 mt-4">
                    <div class="flex justify-between items-center text-sm">
                        <span class="text-gray-600">Alokasi:</span>
                        <span class="font-bold text-gray-800">{{ rt.alokasi }} Kantong</span>
                    </div>
                    <div class="flex justify-between items-center text-sm mt-1">
                        <span class="text-gray-600">Status:</span>
                        {% if rt.status == 'Diserahkan' %}
                        <span class="font-bold text-emerald-600"><i class="fas fa-check-circle mr-1"></i> Diserahkan</span>
                        {% else %}
                        <span class="font-bold text-orange-500"><i class="fas fa-clock mr-1"></i> Menunggu</span>
                        {% endif %}
                    </div>
                </div>

                {% if is_admin %}
                    {% if rt.status == 'Menunggu' %}
                    <form action="/idul-adha/peta-distribusi/update_status" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="rt_id" value="{{ rt.id }}">
                        <input type="hidden" name="status" value="Diserahkan">
                        <button type="submit" class="w-full mt-3 bg-orange-100 text-orange-700 hover:bg-orange-600 hover:text-white py-2 rounded-lg text-sm font-bold transition-colors">
                            Serahkan Jatah
                        </button>
                    </form>
                    {% else %}
                    <form action="/idul-adha/peta-distribusi/update_status" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="rt_id" value="{{ rt.id }}">
                        <input type="hidden" name="status" value="Menunggu">
                        <button type="submit" class="w-full mt-3 bg-red-100 text-red-700 hover:bg-red-600 hover:text-white py-2 rounded-lg text-sm font-bold transition-colors">
                            Batal Serahkan
                        </button>
                    </form>
                    {% endif %}
                {% endif %}
            </div>
            {% else %}
            <div class="col-span-1 md:col-span-3 text-center p-8 bg-white rounded-2xl border border-gray-100 text-gray-500">
                Belum ada data RT.
            </div>
            {% endfor %}
        </div>
    </div>

    {% if is_admin %}
    <!-- Modal Edit RT -->
    <div id="modal-edit-rt" class="hidden fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 relative">
            <button onclick="document.getElementById('modal-edit-rt').classList.add('hidden')" class="absolute top-4 right-4 bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center">&times;</button>
            <h3 class="text-xl font-bold text-orange-600 mb-4 border-b border-gray-100 pb-2">Edit Data RT</h3>
            <form action="/idul-adha/peta-distribusi/edit" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="rt_id" id="edit_rt_id">

                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Nomor Card</label>
                    <input type="text" name="nomor_card" id="edit_nomor_card" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Nama RT</label>
                    <input type="text" name="rt_name" id="edit_rt_name" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Ketua RT</label>
                    <input type="text" name="nama_ketua_rt" id="edit_nama_ketua_rt" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Alokasi (Kantong)</label>
                    <input type="number" name="alokasi" id="edit_alokasi" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Status</label>
                    <select name="status" id="edit_status" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600" required>
                        <option value="Menunggu">Menunggu</option>
                        <option value="Diserahkan">Diserahkan</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-orange-600 text-white font-bold py-2 rounded-xl hover:bg-orange-700 shadow-md mt-2">Save</button>
            </form>
        </div>
    </div>
    <script>
        function openEditRTModal(id, no, rt, ketua, alokasi, status) {
            document.getElementById('edit_rt_id').value = id;
            document.getElementById('edit_nomor_card').value = no;
            document.getElementById('edit_rt_name').value = rt;
            document.getElementById('edit_nama_ketua_rt').value = ketua;
            document.getElementById('edit_alokasi').value = alokasi;
            document.getElementById('edit_status').value = status;
            document.getElementById('modal-edit-rt').classList.remove('hidden');
        }
    </script>
    {% endif %}
</div>
'''"""
content = re.sub(r'IDUL_ADHA_PETA_DISTRIBUSI_HTML = """(.*?)"""', new_peta_html, content, flags=re.DOTALL, count=1)

new_peta_route = """@app.route('/idul-adha/peta-distribusi')
def idul_adha_peta_distribusi():
    rt_list = QurbanRT.query.order_by(QurbanRT.id.asc()).all()
    total_rt = len(rt_list)
    diserahkan_count = len([rt for rt in rt_list if rt.status == 'Diserahkan'])
    progress_percentage = (diserahkan_count / total_rt * 100) if total_rt > 0 else 0

    rendered_content = render_template_string(IDUL_ADHA_PETA_DISTRIBUSI_HTML, rt_list=rt_list, total_rt=total_rt, diserahkan_count=diserahkan_count, progress_percentage=progress_percentage, is_admin=session.get('is_admin', False), settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/idul-adha/peta-distribusi/add', methods=['POST'])
def idul_adha_peta_distribusi_add():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_peta_distribusi'))
    rt = QurbanRT(nomor_card=request.form.get('nomor_card'), rt_name=request.form.get('rt_name'), nama_ketua_rt=request.form.get('nama_ketua_rt'), alokasi=int(request.form.get('alokasi', 0)))
    db.session.add(rt)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('idul_adha_peta_distribusi'))

@app.route('/idul-adha/peta-distribusi/edit', methods=['POST'])
def idul_adha_peta_distribusi_edit():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_peta_distribusi'))
    rt_id = request.form.get('rt_id')
    rt = QurbanRT.query.get(rt_id)
    if rt:
        rt.nomor_card = request.form.get('nomor_card')
        rt.rt_name = request.form.get('rt_name')
        rt.nama_ketua_rt = request.form.get('nama_ketua_rt')
        rt.alokasi = int(request.form.get('alokasi', 0))
        rt.status = request.form.get('status')
        try:
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('idul_adha_peta_distribusi'))

@app.route('/idul-adha/peta-distribusi/update_status', methods=['POST'])
def idul_adha_peta_distribusi_update_status():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_peta_distribusi'))
    rt_id = request.form.get('rt_id')
    status = request.form.get('status')
    rt = QurbanRT.query.get(rt_id)
    if rt:
        rt.status = status
        try:
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('idul_adha_peta_distribusi'))"""
content = re.sub(r"@app\.route\('/idul-adha/peta-distribusi'\)\ndef idul_adha_peta_distribusi\(\):\n    return render_template_string\(BASE_LAYOUT, \n                                  styles=STYLES_HTML, \n                                  active_page='idul-adha', \n                                  content=IDUL_ADHA_PETA_DISTRIBUSI_HTML,\n                                  is_admin=session\.get\('is_admin', False\),\n                                  settings=get_settings\(\)\)", new_peta_route, content, flags=re.DOTALL, count=1)


with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
