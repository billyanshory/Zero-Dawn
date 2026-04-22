import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

# First we need to make sure secrets is imported
if "import secrets" not in content:
    content = content.replace("import pytz", "import pytz\nimport secrets")

html_content = """

IDUL_ADHA_HEWAN_ADMIN_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20">
    <!-- Header -->
    <div class="bg-[#1B4332] text-white py-8 px-5 md:px-8 shadow-xl relative overflow-hidden">
        <div class="max-w-4xl mx-auto relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <a href="/idul-adha" class="inline-flex items-center gap-2 text-white/80 hover:text-white mb-4 text-sm font-bold bg-white/10 px-4 py-2 rounded-full w-max backdrop-blur-sm transition-colors border border-white/20">
                    <i class="fas fa-arrow-left"></i> Kembali ke Dashboard
                </a>
                <h1 class="text-3xl font-bold mb-2 tracking-tight text-[#D4A017]">Manajemen Daftar Shohibul</h1>
                <p class="text-[#F5F0E8]/80 text-sm max-w-xl">
                    Registrasi hewan qurban dan update status pemotongan secara real-time.
                </p>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-4xl mx-auto px-5 md:px-8 mt-6 relative z-20 space-y-8">

        <!-- Registration Form -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100">
            <h3 class="text-lg font-bold text-[#1B4332] mb-4 border-b border-gray-100 pb-3">Registrasi Hewan Baru</h3>
            <form action="/admin/qurban/hewan/tambah" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Nama Shohibul (Pewakif)</label>
                        <input type="text" name="sohibul_name" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Nomor WhatsApp</label>
                        <input type="text" name="wa_number" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Jenis Hewan</label>
                        <select name="animal_type" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                            <option value="Sapi">Sapi</option>
                            <option value="Kambing">Kambing</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Nomor Antrean Potong</label>
                        <input type="number" name="queue_number" required min="1" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                </div>

                <button type="submit" class="w-full bg-[#D4A017] text-[#1B4332] font-bold py-4 mt-2 rounded-xl hover:bg-[#b58812] transition shadow-lg flex items-center justify-center gap-2">
                    <i class="fas fa-plus-circle"></i> Daftarkan Hewan & Generate PIN
                </button>
            </form>
        </div>

        <!-- Animal List / Status Updater -->
        <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100">
            <h3 class="text-lg font-bold text-[#1B4332] mb-4 border-b border-gray-100 pb-3">Daftar Hewan & Update Status</h3>

            <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                {% for animal in animals %}
                <div class="border border-gray-200 rounded-2xl p-4 hover:border-[#D4A017] transition-colors relative">
                    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                        <div>
                            <div class="flex items-center gap-2 mb-1">
                                <span class="bg-[#1B4332] text-white text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wider">{{ animal.animal_type }} No. {{ animal.queue_number }}</span>
                                <span class="bg-gray-100 text-gray-600 text-[10px] px-2 py-1 rounded font-mono font-bold">PIN: {{ animal.pin }}</span>
                            </div>
                            <h4 class="font-bold text-gray-800">{{ animal.sohibul_name }}</h4>
                            <p class="text-xs text-gray-500"><i class="fab fa-whatsapp"></i> {{ animal.wa_number }}</p>
                        </div>

                        <!-- Track URL display -->
                        <div class="bg-gray-50 p-2 rounded-lg border border-gray-200 flex items-center gap-2 text-xs">
                            <span class="text-gray-500 font-mono truncate max-w-[150px] md:max-w-[200px]" id="url-{{ animal.id }}">{{ request.url_root }}qurban/lacak?pin={{ animal.pin }}</span>
                            <button onclick="navigator.clipboard.writeText(document.getElementById('url-{{ animal.id }}').innerText); alert('URL tersalin!')" class="text-[#D4A017] hover:text-[#b58812] p-1"><i class="fas fa-copy"></i></button>
                            <a href="https://wa.me/{{ animal.wa_number|replace('+','')|replace(' ','') }}?text=Assalamualaikum%20Bpk/Ibu%20{{ animal.sohibul_name }},%20ini%20adalah%20link%20untuk%20melacak%20status%20pemotongan%20qurban%20Anda:%20{{ request.url_root }}qurban/lacak?pin={{ animal.pin }}" target="_blank" class="text-green-500 hover:text-green-600 p-1"><i class="fab fa-whatsapp text-sm"></i></a>
                        </div>
                    </div>

                    <!-- Status Updater -->
                    <div class="bg-gray-50 rounded-xl p-2 border border-gray-100">
                        <form action="/admin/qurban/hewan/update-status/{{ animal.id }}" method="POST" class="grid grid-cols-2 md:grid-cols-4 gap-2">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <button type="submit" name="status" value="menunggu_giliran" class="text-[10px] font-bold py-2 px-1 rounded-lg transition-colors border {{ 'bg-[#F5F0E8] text-gray-600 border-[#D4A017] ring-1 ring-[#D4A017]' if animal.status == 'menunggu_giliran' else 'bg-white text-gray-400 border-gray-200 hover:bg-gray-50' }}">Menunggu</button>
                            <button type="submit" name="status" value="sedang_disembelih" class="text-[10px] font-bold py-2 px-1 rounded-lg transition-colors border {{ 'bg-[#8B2635] text-white border-[#8B2635]' if animal.status == 'sedang_disembelih' else 'bg-white text-gray-400 border-gray-200 hover:bg-gray-50' }}">Disembelih</button>
                            <button type="submit" name="status" value="proses_pencacahan" class="text-[10px] font-bold py-2 px-1 rounded-lg transition-colors border {{ 'bg-[#D4A017] text-white border-[#D4A017]' if animal.status == 'proses_pencacahan' else 'bg-white text-gray-400 border-gray-200 hover:bg-gray-50' }}">Pencacahan</button>
                            <button type="submit" name="status" value="siap_diambil" class="text-[10px] font-bold py-2 px-1 rounded-lg transition-colors border {{ 'bg-[#1B4332] text-white border-[#1B4332]' if animal.status == 'siap_diambil' else 'bg-white text-gray-400 border-gray-200 hover:bg-gray-50' }}">Siap Diambil</button>
                        </form>
                    </div>
                </div>
                {% else %}
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-box-open text-3xl mb-2 text-gray-300"></i>
                    <p>Belum ada data hewan qurban yang didaftarkan.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
'''

"""

routes = """
@app.route('/admin/qurban/hewan')
def admin_qurban_hewan():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    animals = QurbanAnimal.query.order_by(QurbanAnimal.id.desc()).all()
    rendered_content = render_template_string(IDUL_ADHA_HEWAN_ADMIN_HTML, animals=animals, is_admin=True)
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=True, settings=get_settings())

@app.route('/admin/qurban/hewan/tambah', methods=['POST'])
def admin_qurban_hewan_tambah():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Generate secure random alphanumeric PIN (6-8 chars)
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" # removed confusing chars like I,1,O,0
        pin = ''.join(secrets.choice(alphabet) for i in range(6))

        animal = QurbanAnimal(
            animal_type=request.form.get('animal_type', ''),
            queue_number=int(request.form.get('queue_number', 0)),
            sohibul_name=request.form.get('sohibul_name', ''),
            wa_number=request.form.get('wa_number', ''),
            pin=pin,
            status='menunggu_giliran'
        )
        db.session.add(animal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving animal: {e}")
        return jsonify({'error': 'Database error'}), 500

    return redirect(url_for('admin_qurban_hewan'))

@app.route('/admin/qurban/hewan/update-status/<int:animal_id>', methods=['POST'])
def admin_qurban_hewan_update_status(animal_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        animal = QurbanAnimal.query.get(animal_id)
        if not animal:
            return jsonify({'error': 'Animal not found'}), 404

        status = request.form.get('status', 'menunggu_giliran')
        valid_statuses = ['menunggu_giliran', 'sedang_disembelih', 'proses_pencacahan', 'siap_diambil']
        if status in valid_statuses:
            animal.status = status
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating animal status: {e}")
        return jsonify({'error': 'Database error'}), 500

    return redirect(url_for('admin_qurban_hewan'))
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

print("Injected hewan admin")
