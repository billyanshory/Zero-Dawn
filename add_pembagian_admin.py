import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

html_content = """

IDUL_ADHA_PEMBAGIAN_ADMIN_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20">
    <!-- Header -->
    <div class="bg-[#1B4332] text-white py-8 px-5 md:px-8 shadow-xl relative overflow-hidden">
        <div class="max-w-4xl mx-auto relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <a href="/idul-adha" class="inline-flex items-center gap-2 text-white/80 hover:text-white mb-4 text-sm font-bold bg-white/10 px-4 py-2 rounded-full w-max backdrop-blur-sm transition-colors border border-white/20">
                    <i class="fas fa-arrow-left"></i> Kembali ke Dashboard
                </a>
                <h1 class="text-3xl font-bold mb-2 tracking-tight text-[#D4A017]">Admin Smart Digital Queue</h1>
                <p class="text-[#F5F0E8]/80 text-sm max-w-xl">
                    Manajemen alokasi waktu dan kuota distribusi daging qurban untuk setiap RT.
                </p>
            </div>
        </div>
    </div>

    <div class="max-w-4xl mx-auto px-5 md:px-8 mt-6 relative z-20 space-y-8">

        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="p-4 rounded-xl text-sm font-bold {{ 'bg-green-100 text-green-700 border border-green-200' if category == 'success' else 'bg-red-100 text-red-700 border border-red-200' }}">
                  {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <!-- Allocation Form -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100">
            <h3 class="text-lg font-bold text-[#1B4332] mb-4 border-b border-gray-100 pb-3">Alokasi Waktu RT Baru</h3>
            <form action="/admin/qurban/distribusi" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="hidden" name="action" value="create_slot"/>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Identitas RT</label>
                        <input type="text" name="rt_identifier" required placeholder="ex: RT 01" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Mulai (HH:MM)</label>
                        <input type="time" name="time_start" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Selesai (HH:MM)</label>
                        <input type="time" name="time_end" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Total Kuota</label>
                        <input type="number" name="total_quota" required min="1" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                </div>

                <button type="submit" class="w-full bg-[#1B4332] text-white font-bold py-4 mt-2 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">
                    <i class="fas fa-plus"></i> Buat Slot Alokasi
                </button>
            </form>
        </div>

        <!-- Kupon Generator -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100">
            <h3 class="text-lg font-bold text-[#D4A017] mb-4 border-b border-gray-100 pb-3">Input Kupon Warga</h3>
            <form action="/admin/qurban/distribusi" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="hidden" name="action" value="add_kupon"/>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Pilih Slot RT</label>
                        <select name="slot_id" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                            <option value="">-- Pilih Slot --</option>
                            {% for slot in slots %}
                            <option value="{{ slot.id }}">{{ slot.rt_identifier }} ({{ slot.time_start }}-{{ slot.time_end }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">NIK Warga (16 digit)</label>
                        <input type="text" name="nik" required pattern="[0-9]{16}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Nomor Kupon</label>
                        <input type="text" name="coupon_number" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm uppercase focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                </div>

                <button type="submit" class="w-full bg-[#D4A017] text-[#1B4332] font-bold py-3 mt-2 rounded-xl hover:bg-[#b58812] transition shadow-md">
                    <i class="fas fa-ticket-alt mr-1"></i> Daftarkan Kupon
                </button>
            </form>
        </div>

        <!-- Slot Overview -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100">
            <h3 class="text-lg font-bold text-[#1B4332] mb-4 border-b border-gray-100 pb-3">Ringkasan Alokasi</h3>

            <div class="overflow-hidden rounded-xl border border-gray-200">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 text-gray-600">
                        <tr>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px]">RT</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px]">Waktu</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px]">Kuota</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px]">Diambil</th>
                            <th class="p-4 font-bold uppercase tracking-wider text-[10px] text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        {% for slot in slots %}
                        <tr class="hover:bg-gray-50 transition">
                            <td class="p-4 font-bold text-[#1B4332]">{{ slot.rt_identifier }}</td>
                            <td class="p-4 text-gray-600 font-mono">{{ slot.time_start }} - {{ slot.time_end }}</td>
                            <td class="p-4 font-bold text-gray-800">{{ slot.total_quota }}</td>
                            <td class="p-4">
                                <span class="bg-{{ 'green' if slot.distributed_count == slot.total_quota else 'yellow' }}-100 text-{{ 'green' if slot.distributed_count == slot.total_quota else 'yellow' }}-800 font-bold px-2 py-1 rounded text-xs">
                                    {{ slot.distributed_count }}
                                </span>
                            </td>
                            <td class="p-4 text-right">
                                <!-- Example claim action for demo purposes (usually done via Peta Distribusi or scanner) -->
                                <span class="text-[10px] text-gray-400 italic">Lihat Detail ></span>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" class="p-6 text-center text-gray-500">Belum ada slot alokasi.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>
'''

"""

routes = """
@app.route('/admin/qurban/distribusi', methods=['GET', 'POST'])
def admin_qurban_distribusi():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'create_slot':
                slot = DistribusiSlot(
                    rt_identifier=request.form.get('rt_identifier', ''),
                    time_start=request.form.get('time_start', ''),
                    time_end=request.form.get('time_end', ''),
                    total_quota=int(request.form.get('total_quota', 0))
                )
                db.session.add(slot)
                db.session.commit()
                flash('Slot distribusi berhasil dibuat.', 'success')
            elif action == 'add_kupon':
                kupon = DistribusiKupon(
                    slot_id=int(request.form.get('slot_id', 0)),
                    nik=request.form.get('nik', ''),
                    coupon_number=request.form.get('coupon_number', '').upper()
                )
                db.session.add(kupon)
                db.session.commit()
                flash('Kupon berhasil didaftarkan.', 'success')
            return redirect(url_for('admin_qurban_distribusi'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in admin distribusi: {e}")
        flash('Terjadi kesalahan pada database.', 'error')

    slots = DistribusiSlot.query.order_by(DistribusiSlot.time_start.asc()).all()
    rendered_content = render_template_string(IDUL_ADHA_PEMBAGIAN_ADMIN_HTML, slots=slots, is_admin=True, settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=True, settings=get_settings())
"""

# Note: flash requires secret key setup, which is already present.
# We also need to make sure we inject before `if __name__ == '__main__':`

insert_target = 'HOME_HTML = """'
if insert_target in content:
    content = content.replace(insert_target, html_content + insert_target)

# Routes
insert_target_r = "if __name__ == '__main__':"
if insert_target_r in content:
    content = content.replace(insert_target_r, routes + "\n" + insert_target_r)

with open(filename, "w") as f:
    f.write(content)

print("Injected pembagian admin")
