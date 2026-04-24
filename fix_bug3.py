import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()


admin_kupon_html = """
            <!-- ADMIN KUPON PANEL -->
            {% if is_admin %}
            <div class="bg-white rounded-3xl p-6 shadow-xl border border-yellow-500/20 mb-8 w-full max-w-md mx-auto relative z-20">
                <div class="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
                    <h3 class="text-lg font-bold text-[#D4A017]"><i class="fas fa-lock mr-2"></i>Panel Admin: Manajemen Kupon</h3>
                    <button onclick="openKuponListModal()" class="bg-[#1B4332] text-white text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-[#153426] transition">
                        <i class="fas fa-list mr-1"></i> Daftar Kupon
                    </button>
                </div>

                <form id="generate-kupon-form" class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">NIK Warga</label>
                        <input type="text" id="warga_nik" required pattern="[0-9]{16}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Slot RT / Waktu</label>
                        <select id="slot_id" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                            <option value="">Memuat slot...</option>
                        </select>
                    </div>
                    <button type="button" onclick="generateKupon()" class="w-full bg-[#D4A017] text-[#1B4332] font-bold py-3 mt-2 rounded-xl hover:bg-[#b8860b] transition shadow-lg">
                        Generate Kupon Baru
                    </button>
                </form>

                <div id="new-kupon-display" class="hidden mt-6 p-4 bg-yellow-50 rounded-xl border border-yellow-200 text-center">
                    <p class="text-xs text-[#D4A017] font-bold mb-1">Kupon Berhasil Dibuat!</p>
                    <div class="text-3xl font-mono font-bold text-[#1B4332] tracking-widest uppercase" id="generated-kupon-text"></div>
                    <p class="text-sm mt-2 text-gray-600">NIK: <strong id="generated-nik-text"></strong></p>
                </div>
            </div>

            <!-- KUPON LIST MODAL -->
            <div id="modal-kupon-list" class="hidden fixed inset-0 z-[100] flex items-center justify-center p-4">
                <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeKuponListModal()"></div>
                <div class="bg-white rounded-3xl w-full max-w-3xl relative z-10 shadow-2xl flex flex-col max-h-[80vh]">
                    <div class="p-6 border-b border-gray-100 flex items-center justify-between">
                        <h2 class="text-xl font-bold text-gray-800">Daftar Kupon Distribusi</h2>
                        <button onclick="closeKuponListModal()" class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="p-6 overflow-y-auto">
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm whitespace-nowrap">
                                <thead class="bg-gray-50 text-gray-600 font-bold">
                                    <tr>
                                        <th class="p-3 rounded-tl-lg">Kupon</th>
                                        <th class="p-3">NIK</th>
                                        <th class="p-3">RT / Waktu</th>
                                        <th class="p-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody id="kupon-list-tbody" class="divide-y divide-gray-100 text-gray-700">
                                    <tr><td colspan="4" class="p-4 text-center">Memuat data...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                async function loadSlots() {
                    try {
                        const res = await fetch('/api/qurban/pembagian/slots');
                        const data = await res.json();
                        if(res.ok && data.success) {
                            const select = document.getElementById('slot_id');
                            if(data.slots.length === 0) {
                                select.innerHTML = '<option value="">Belum ada slot dikonfigurasi</option>';
                            } else {
                                select.innerHTML = data.slots.map(s => `<option value="${s.id}">${s.rt} (${s.time})</option>`).join('');
                            }
                        }
                    } catch(e) {
                        console.error('Failed to load slots', e);
                    }
                }

                async function generateKupon() {
                    const nik = document.getElementById('warga_nik').value;
                    const slot_id = document.getElementById('slot_id').value;
                    if(!nik || nik.length !== 16) { alert("NIK harus 16 digit angka"); return; }
                    if(!slot_id) { alert("Pilih slot RT"); return; }

                    try {
                        const res = await fetch('/api/qurban/pembagian/generate_kupon', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({nik: nik, slot_id: slot_id})
                        });
                        const data = await res.json();
                        if(res.ok && data.success) {
                            document.getElementById('generated-kupon-text').innerText = data.kupon;
                            document.getElementById('generated-nik-text').innerText = nik;
                            document.getElementById('new-kupon-display').classList.remove('hidden');
                            document.getElementById('warga_nik').value = '';
                        } else {
                            throw new Error(data.error || "Gagal membuat Kupon");
                        }
                    } catch(e) {
                        alert(e.message);
                    }
                }

                function closeKuponListModal() {
                    document.getElementById('modal-kupon-list').classList.add('hidden');
                }

                async function openKuponListModal() {
                    document.getElementById('modal-kupon-list').classList.remove('hidden');
                    const tbody = document.getElementById('kupon-list-tbody');
                    tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center">Memuat data...</td></tr>';

                    try {
                        const res = await fetch('/api/qurban/pembagian/list_kupons');
                        const data = await res.json();
                        if(res.ok && data.success) {
                            if(data.kupons.length === 0) {
                                tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-gray-500">Belum ada Kupon.</td></tr>';
                                return;
                            }
                            tbody.innerHTML = data.kupons.map(k => `
                                <tr class="hover:bg-gray-50">
                                    <td class="p-3 font-mono font-bold text-[#D4A017] uppercase">${k.kupon}</td>
                                    <td class="p-3">${k.nik}</td>
                                    <td class="p-3">${k.slot}</td>
                                    <td class="p-3"><span class="bg-gray-100 px-2 py-1 rounded text-xs">${k.status}</span></td>
                                </tr>
                            `).join('');
                        } else {
                            throw new Error(data.error || "Gagal memuat data");
                        }
                    } catch(e) {
                        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-red-500">${e.message}</td></tr>`;
                    }
                }

                // Load slots if admin
                if(document.getElementById('slot_id')) {
                    loadSlots();
                }
            </script>
            {% endif %}
"""

if "<!-- ADMIN KUPON PANEL -->" not in content:
    content = content.replace(
        '<div class="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden relative">',
        admin_kupon_html + '\n    <div class="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden relative">'
    )

route_update = """
@app.route('/qurban/pembagian/cek', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def qurban_pembagian_cek():
    kupon = None
    slot = None
    error = None

    try:
        if request.method == 'POST':
            nik = request.form.get('nik', '').strip()
            coupon_number = request.form.get('coupon_number', '').strip().upper()

            if not nik.isdigit() or len(nik) != 16:
                error = "Format NIK tidak valid. Harus 16 digit angka."
            else:
                kupon = DistribusiKupon.query.filter_by(nik=nik, coupon_number=coupon_number).first()
                if kupon:
                    slot = DistribusiSlot.query.get(kupon.slot_id)
                else:
                    error = "Kombinasi NIK dan Nomor Kupon tidak ditemukan."
    except Exception as e:
        app.logger.error(f"Error checking kupon: {e}", exc_info=True)
        error = "Terjadi kesalahan sistem saat mencari data."

    rendered_content = render_template_string(IDUL_ADHA_PEMBAGIAN_CEK_HTML, kupon=kupon, slot=slot, error=error, is_admin=session.get('is_admin', False))
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/api/qurban/pembagian/slots', methods=['GET'])
def api_qurban_pembagian_slots():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        # Default initialization if empty
        if DistribusiSlot.query.count() == 0:
            default_slots = [
                DistribusiSlot(rt_identifier='RT 01', time_start='08:00', time_end='10:00', total_quota=100),
                DistribusiSlot(rt_identifier='RT 02', time_start='10:00', time_end='12:00', total_quota=100)
            ]
            db.session.bulk_save_objects(default_slots)
            db.session.commit()

        slots = DistribusiSlot.query.all()
        slots_data = [{'id': s.id, 'rt': s.rt_identifier, 'time': f"{s.time_start} - {s.time_end}"} for s in slots]
        return jsonify({'success': True, 'slots': slots_data})
    except Exception as e:
        app.logger.error(f"Error loading slots: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan sistem'}), 500

@app.route('/api/qurban/pembagian/generate_kupon', methods=['POST'])
def api_qurban_generate_kupon():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

        nik = data.get('nik', '').strip()
        slot_id = data.get('slot_id')

        if not nik or len(nik) != 16 or not nik.isdigit():
            return jsonify({'success': False, 'error': 'NIK tidak valid'}), 400

        slot = DistribusiSlot.query.get(slot_id)
        if not slot:
            return jsonify({'success': False, 'error': 'Slot tidak valid'}), 400

        # check existing nik
        if DistribusiKupon.query.filter_by(nik=nik).first():
             return jsonify({'success': False, 'error': 'NIK sudah terdaftar'}), 400

        kupon_number = None
        for _ in range(10):
            candidate = secrets.token_hex(4).upper()
            if not DistribusiKupon.query.filter_by(coupon_number=candidate).first():
                kupon_number = candidate
                break

        if not kupon_number:
            return jsonify({'success': False, 'error': 'Gagal generate kupon unik'}), 500

        new_kupon = DistribusiKupon(
            slot_id=slot.id,
            nik=nik,
            coupon_number=kupon_number,
            is_claimed=False
        )
        db.session.add(new_kupon)
        db.session.commit()
        return jsonify({'success': True, 'kupon': kupon_number})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error generating kupon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan sistem'}), 500

@app.route('/api/qurban/pembagian/list_kupons', methods=['GET'])
def api_qurban_list_kupons():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        kupons = DistribusiKupon.query.order_by(DistribusiKupon.id.desc()).all()
        kupons_data = []
        for k in kupons:
            slot = DistribusiSlot.query.get(k.slot_id)
            kupons_data.append({
                'kupon': k.coupon_number,
                'nik': k.nik[:4] + '********' + k.nik[-4:],
                'slot': f"{slot.rt_identifier} ({slot.time_start}-{slot.time_end})" if slot else "N/A",
                'status': 'Diambil' if k.is_claimed else 'Belum Diambil'
            })
        return jsonify({'success': True, 'kupons': kupons_data})
    except Exception as e:
        app.logger.error(f"Error listing kupons: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan sistem'}), 500
"""

content = re.sub(r"@app\.route\('/qurban/pembagian/cek'.*?def qurban_pembagian_cek\(\):.*?return render_template_string\(BASE_LAYOUT.*?\)", route_update.strip(), content, flags=re.DOTALL)


with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
