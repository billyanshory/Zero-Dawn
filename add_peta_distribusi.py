import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

html_content = """

IDUL_ADHA_PETA_DISTRIBUSI_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20">
    <!-- Header -->
    <div class="bg-[#1B4332] text-white py-8 px-5 md:px-8 shadow-xl relative overflow-hidden">
        <div class="max-w-6xl mx-auto relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <a href="/idul-adha" class="inline-flex items-center gap-2 text-white/80 hover:text-white mb-4 text-sm font-bold bg-white/10 px-4 py-2 rounded-full w-max backdrop-blur-sm transition-colors border border-white/20">
                    <i class="fas fa-arrow-left"></i> Kembali ke Dashboard
                </a>
                <h1 class="text-3xl font-bold mb-2 tracking-tight text-[#D4A017]">Peta Distribusi & Serah Terima</h1>
                <p class="text-[#F5F0E8]/80 text-sm max-w-xl">
                    Sistem kendali anti double-claim. Rekam penyerahan paket daging ke RT dan kunci slot secara instan.
                </p>
            </div>
            <div class="flex gap-2">
                <button onclick="window.location.reload()" class="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-xl font-bold text-sm transition-colors border border-white/20 backdrop-blur-sm">
                    <i class="fas fa-sync-alt mr-2"></i>Segarkan Data
                </button>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-6xl mx-auto px-5 md:px-8 mt-6 relative z-20 space-y-6">

        <!-- Summary Board -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex flex-col justify-center">
                <p class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Total RT Dilayani</p>
                <h3 class="text-2xl font-bold text-[#1B4332] font-mono">{{ total_rt }}</h3>
            </div>
            <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex flex-col justify-center">
                <p class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Paket Dialokasikan</p>
                <h3 class="text-2xl font-bold text-gray-800 font-mono">{{ total_quota }}</h3>
            </div>
            <div class="bg-[#1B4332]/10 rounded-2xl p-5 shadow-sm border border-[#1B4332]/20 flex flex-col justify-center">
                <p class="text-xs font-bold text-[#1B4332] uppercase tracking-wider mb-1">Paket Tersalurkan</p>
                <h3 class="text-2xl font-bold text-[#1B4332] font-mono">{{ total_distributed }}</h3>
            </div>
            <div class="bg-[#8B2635]/10 rounded-2xl p-5 shadow-sm border border-[#8B2635]/20 flex flex-col justify-center">
                <p class="text-xs font-bold text-[#8B2635] uppercase tracking-wider mb-1">Paket Sisa</p>
                <h3 class="text-2xl font-bold text-[#8B2635] font-mono">{{ total_quota - total_distributed }}</h3>
            </div>
        </div>

        <!-- Warning Log -->
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="p-4 rounded-xl text-sm font-bold shadow-md {{ 'bg-green-100 text-green-700 border border-green-200' if category == 'success' else 'bg-[#8B2635]/10 text-[#8B2635] border border-[#8B2635]/20' }}">
                  {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <!-- Missing RTs -->
        {% if missing_rts %}
        <div class="bg-[#D4A017]/10 rounded-2xl p-5 border border-[#D4A017]/30 flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-[#D4A017]/20 text-[#D4A017] flex items-center justify-center flex-shrink-0">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div>
                <h4 class="text-sm font-bold text-[#D4A017] mb-1 uppercase tracking-widest">RT Belum Terlayani</h4>
                <p class="text-sm text-gray-800 font-bold">{{ missing_rts|join(', ') }}</p>
            </div>
        </div>
        {% endif %}

        <!-- RT List Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {% for slot in slots %}
            <div class="bg-white rounded-2xl p-5 shadow-sm border {{ 'border-[#1B4332] ring-1 ring-[#1B4332] bg-[#1B4332]/5' if slot.is_locked else 'border-gray-200 hover:border-[#D4A017]' }} relative transition-colors">

                <div class="flex justify-between items-start mb-4 border-b border-gray-100 pb-3">
                    <div>
                        <h4 class="text-xl font-bold text-gray-800">{{ slot.rt_identifier }}</h4>
                        <p class="text-xs text-gray-500 font-mono mt-1">Sesi: {{ slot.time_start }} - {{ slot.time_end }}</p>
                    </div>
                    {% if slot.is_locked %}
                    <span class="bg-[#1B4332] text-white text-[10px] px-3 py-1 rounded-full font-bold uppercase tracking-widest shadow-sm flex items-center gap-1">
                        <i class="fas fa-check-circle"></i> Selesai
                    </span>
                    {% else %}
                    <span class="bg-[#D4A017]/20 text-[#D4A017] text-[10px] px-3 py-1 rounded-full font-bold uppercase tracking-widest shadow-sm flex items-center gap-1">
                        <i class="fas fa-clock"></i> Belum
                    </span>
                    {% endif %}
                </div>

                <div class="grid grid-cols-2 gap-2 mb-4">
                    <div class="bg-gray-50 p-2 rounded-lg border border-gray-100">
                        <p class="text-[10px] text-gray-500 uppercase font-bold">Kuota RT</p>
                        <p class="font-bold font-mono text-gray-800 text-lg">{{ slot.total_quota }}</p>
                    </div>
                    <div class="bg-gray-50 p-2 rounded-lg border border-gray-100">
                        <p class="text-[10px] text-gray-500 uppercase font-bold">Telah Diambil</p>
                        <p class="font-bold font-mono text-gray-800 text-lg">{{ slot.distributed_count }}</p>
                    </div>
                </div>

                {% if slot.is_locked %}
                <!-- Locked State -->
                <div class="bg-white border border-gray-200 rounded-xl p-3 text-sm text-gray-600 mb-3">
                    <p><i class="fas fa-user-check text-[#1B4332] mr-2"></i> Diserahkan ke: <strong>{{ slot.handler_name }}</strong></p>
                    <p class="mt-1"><i class="fas fa-calendar-check text-[#1B4332] mr-2"></i> Pada: <strong>{{ slot.handover_time.strftime('%H:%M WIB, %d %b') if slot.handover_time else '-' }}</strong></p>
                </div>

                <!-- Unlock Action (Requires Confirmation) -->
                <form action="/admin/qurban/distribusi/unlock/{{ slot.id }}" method="POST" onsubmit="return confirm('Peringatan: Anda akan membuka kunci RT ini. Lanjutkan?');">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <button type="submit" class="w-full bg-[#8B2635]/10 text-[#8B2635] text-xs font-bold py-2 rounded-xl hover:bg-[#8B2635] hover:text-white transition-colors border border-[#8B2635]/20">
                        <i class="fas fa-unlock-alt mr-1"></i> Buka Kunci (Admin Override)
                    </button>
                </form>

                {% else %}
                <!-- Handover Form -->
                <form action="/admin/qurban/distribusi/handover/{{ slot.id }}" method="POST" class="mt-2 border-t border-gray-100 pt-3">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <label class="block text-[10px] font-bold text-gray-500 mb-1 uppercase">Nama Penerima / Perwakilan RT</label>
                    <input type="text" name="handler_name" required placeholder="Cth: Bpk Budi (Ketua RT)" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017] mb-2">

                    <button type="submit" class="w-full bg-[#1B4332] text-white text-sm font-bold py-3 rounded-xl hover:bg-[#153426] transition shadow-md flex justify-center items-center gap-2">
                        <i class="fas fa-lock"></i> Rekam Serah Terima & Kunci
                    </button>
                </form>
                {% endif %}
            </div>
            {% else %}
            <div class="col-span-1 md:col-span-2 lg:col-span-3 text-center py-12">
                <i class="fas fa-map text-4xl text-gray-300 mb-3"></i>
                <p class="text-gray-500 font-bold">Belum ada data RT yang dialokasikan.</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
'''

"""

routes = """
@app.route('/admin/qurban/peta')
def admin_qurban_peta():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:
        slots = DistribusiSlot.query.all()
        total_rt = len(slots)
        total_quota = sum([s.total_quota for s in slots])
        total_distributed = sum([s.distributed_count for s in slots])
        missing_rts = [s.rt_identifier for s in slots if not s.is_locked]

        rendered_content = render_template_string(IDUL_ADHA_PETA_DISTRIBUSI_HTML,
                                                  slots=slots,
                                                  total_rt=total_rt,
                                                  total_quota=total_quota,
                                                  total_distributed=total_distributed,
                                                  missing_rts=missing_rts,
                                                  is_admin=True,
                                                  settings=get_settings())
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=True, settings=get_settings())
    except Exception as e:
        app.logger.error(f"Error loading peta: {e}")
        return "Internal Server Error", 500

@app.route('/admin/qurban/distribusi/handover/<int:slot_id>', methods=['POST'])
def admin_qurban_distribusi_handover(slot_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        slot = DistribusiSlot.query.get(slot_id)
        if not slot:
            flash('Slot tidak ditemukan.', 'error')
            return redirect(url_for('admin_qurban_peta'))

        if slot.is_locked:
            flash('Gagal: Slot RT ini sudah dikunci sebelumnya (Double Claim Attempt).', 'error')
            return redirect(url_for('admin_qurban_peta'))

        handler_name = request.form.get('handler_name', '').strip()
        if not handler_name:
            flash('Nama penerima harus diisi.', 'error')
            return redirect(url_for('admin_qurban_peta'))

        slot.handler_name = handler_name
        slot.handover_time = datetime.datetime.now()
        slot.is_locked = True

        db.session.commit()
        flash(f'Serah terima {slot.rt_identifier} berhasil dicatat dan dikunci.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in handover: {e}")
        flash('Terjadi kesalahan sistem saat menyimpan serah terima.', 'error')

    return redirect(url_for('admin_qurban_peta'))

@app.route('/admin/qurban/distribusi/unlock/<int:slot_id>', methods=['POST'])
def admin_qurban_distribusi_unlock(slot_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        slot = DistribusiSlot.query.get(slot_id)
        if not slot:
            flash('Slot tidak ditemukan.', 'error')
            return redirect(url_for('admin_qurban_peta'))

        if not slot.is_locked:
            flash('Slot sudah dalam keadaan terbuka.', 'error')
            return redirect(url_for('admin_qurban_peta'))

        # Audit logging can be done here via app.logger
        app.logger.warning(f"ADMIN OVERRIDE: Unlock performed on slot {slot.id} (RT {slot.rt_identifier}) by session admin.")

        slot.is_locked = False
        slot.handler_name = None
        slot.handover_time = None

        db.session.commit()
        flash(f'Kunci {slot.rt_identifier} berhasil dibuka.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in unlock override: {e}")
        flash('Terjadi kesalahan sistem saat membuka kunci.', 'error')

    return redirect(url_for('admin_qurban_peta'))
"""

insert_target = 'HOME_HTML = """'
if insert_target in content:
    content = content.replace(insert_target, html_content + insert_target)

# Routes
insert_target_r = "if __name__ == '__main__':"
if insert_target_r in content:
    content = content.replace(insert_target_r, routes + "\n" + insert_target_r)

with open(filename, "w") as f:
    f.write(content)

print("Injected peta distribusi routes and templates.")
