import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Replace Form Submission with AJAX in IDUL_ADHA_PETA_DISTRIBUSI_HTML for Adding RT
old_peta_html_form = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Tambah Data RT Baru</h2>
            <form action="/idul-adha/peta-distribusi/add" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

new_peta_html_form = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Tambah Data RT Baru</h2>
            <form id="addRtForm" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

content = content.replace(old_peta_html_form, new_peta_html_form)

old_peta_html_btn = """                </div>
                <div class="md:col-span-4 mt-2">
                    <button type="submit" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Tambah Data RT</button>
                </div>
            </form>
        </div>"""

new_peta_html_btn = """                </div>
                <div class="md:col-span-4 mt-2">
                    <button type="submit" id="addRtBtn" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md transition-all">Tambah Data RT</button>
                </div>
            </form>
        </div>

        <!-- SUCCESS MODAL ANIMATION FOR TAMBAH RT -->
        <div id="generateRTAnim" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 opacity-0 pointer-events-none transition-opacity duration-300">
            <div class="bg-white rounded-3xl p-8 transform scale-90 transition-transform duration-300 flex flex-col items-center shadow-2xl" id="rtModalContent">
                <div class="w-48 h-32 relative mb-6 overflow-hidden flex items-center justify-center" id="rtCarCont">
                    <div class="absolute bottom-0 w-full h-1 bg-gray-300"></div>
                    <div class="animate-bounce" style="animation: bounce 0.5s infinite alternate;">
                        <i class="fas fa-truck text-6xl text-[#8B2635]"></i>
                    </div>
                    <div class="absolute bottom-0 left-10 flex gap-8">
                        <i class="fas fa-circle-notch text-xl text-gray-800 animate-spin" style="animation: spin 0.5s linear infinite;"></i>
                        <i class="fas fa-circle-notch text-xl text-gray-800 animate-spin" style="animation: spin 0.5s linear infinite;"></i>
                    </div>
                    <!-- Moving Road Lines -->
                    <div class="absolute bottom-[-2px] w-full flex overflow-hidden">
                        <div class="w-full flex justify-between animate-road" style="animation: roadMove 1s linear infinite;">
                            <div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div>
                        </div>
                    </div>
                </div>
                <h3 class="text-2xl font-bold text-gray-800 opacity-0 transition-opacity duration-500 delay-300" id="rtText1">Data RT Ditambahkan!</h3>
                <p class="text-gray-500 mt-2 opacity-0 transition-opacity duration-500 delay-500 text-center" id="rtText2">Card status RT telah aktif dan siap dipantau.</p>
            </div>
        </div>

        <style>
        @keyframes roadMove {
            from { transform: translateX(0); }
            to { transform: translateX(-100%); }
        }
        </style>
        """

content = content.replace(old_peta_html_btn, new_peta_html_btn)


# Update Status & Edit Buttons in Cards to use AJAX
old_peta_html_card = """                    <div class="p-4 bg-gray-50 flex justify-between items-center border-t border-gray-100">
                        {% if is_admin %}
                        <form action="/idul-adha/peta-distribusi/update_status" method="POST" class="w-full flex gap-2">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="rt_id" value="{{ rt.id }}">
                            {% if rt.status == 'Menunggu' %}
                            <button type="submit" name="status" value="Diserahkan" class="flex-1 bg-emerald-100 text-emerald-700 py-2 rounded-lg font-bold text-sm hover:bg-emerald-200">Serahkan Jatah</button>
                            {% else %}
                            <button type="submit" name="status" value="Menunggu" class="flex-1 bg-red-100 text-red-700 py-2 rounded-lg font-bold text-sm hover:bg-red-200">Batal Serahkan</button>
                            {% endif %}
                            <button type="button" onclick="document.getElementById('editModal{{ rt.id }}').classList.remove('hidden')" class="px-3 bg-gray-200 text-gray-600 rounded-lg hover:bg-gray-300"><i class="fas fa-pen"></i></button>
                        </form>
                        {% else %}
                        <div class="w-full text-center text-xs text-gray-500 font-medium">Update Terakhir: Hari ini</div>
                        {% endif %}
                    </div>
                </div>

                {% if is_admin %}
                <!-- Edit Modal -->
                <div id="editModal{{ rt.id }}" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div class="bg-white rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-xl font-bold text-[#8B2635]">Edit Data RT</h3>
                            <button onclick="document.getElementById('editModal{{ rt.id }}').classList.add('hidden')" class="text-gray-400 hover:text-gray-600"><i class="fas fa-times text-xl"></i></button>
                        </div>
                        <form action="/idul-adha/peta-distribusi/edit" method="POST" class="flex flex-col gap-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="rt_id" value="{{ rt.id }}">
                            <div>
                                <label class="block text-sm font-bold text-gray-600 mb-1">Nomor Card</label>
                                <input type="text" name="nomor_card" value="{{ rt.nomor_card }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                            </div>
                            <div>
                                <label class="block text-sm font-bold text-gray-600 mb-1">Nama RT (Wilayah)</label>
                                <input type="text" name="rt_name" value="{{ rt.rt_name }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                            </div>
                            <div>
                                <label class="block text-sm font-bold text-gray-600 mb-1">Nama Ketua RT / PIC</label>
                                <input type="text" name="nama_ketua_rt" value="{{ rt.nama_ketua_rt }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-bold text-gray-600 mb-1">Alokasi (Bungkus)</label>
                                    <input type="number" name="alokasi" value="{{ rt.alokasi }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                                </div>
                                <div>
                                    <label class="block text-sm font-bold text-gray-600 mb-1">Status</label>
                                    <select name="status" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                                        <option value="Menunggu" {{ 'selected' if rt.status == 'Menunggu' else '' }}>Menunggu</option>
                                        <option value="Diserahkan" {{ 'selected' if rt.status == 'Diserahkan' else '' }}>Diserahkan</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" class="mt-4 w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Save</button>
                        </form>
                    </div>
                </div>
                {% endif %}"""

new_peta_html_card = """                    <div class="p-4 bg-gray-50 flex justify-between items-center border-t border-gray-100">
                        {% if is_admin %}
                        <div class="w-full flex gap-2">
                            {% if rt.status == 'Menunggu' %}
                            <button onclick="updateRTStatus({{ rt.id }}, 'Diserahkan')" class="flex-1 bg-emerald-100 text-emerald-700 py-2 rounded-lg font-bold text-sm hover:bg-emerald-200 transition-colors">Serahkan Jatah</button>
                            {% else %}
                            <button onclick="updateRTStatus({{ rt.id }}, 'Menunggu')" class="flex-1 bg-red-100 text-red-700 py-2 rounded-lg font-bold text-sm hover:bg-red-200 transition-colors">Batal Serahkan</button>
                            {% endif %}
                            <button type="button" onclick="document.getElementById('editModal{{ rt.id }}').classList.remove('hidden')" class="px-3 bg-gray-200 text-gray-600 rounded-lg hover:bg-gray-300"><i class="fas fa-pen"></i></button>
                        </div>
                        {% else %}
                        <div class="w-full text-center text-xs text-gray-500 font-medium">Update Terakhir: Hari ini</div>
                        {% endif %}
                    </div>
                </div>

                {% if is_admin %}
                <!-- Edit Modal -->
                <div id="editModal{{ rt.id }}" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div class="bg-white rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-xl font-bold text-[#8B2635]">Edit Data RT</h3>
                            <button onclick="document.getElementById('editModal{{ rt.id }}').classList.add('hidden')" class="text-gray-400 hover:text-gray-600"><i class="fas fa-times text-xl"></i></button>
                        </div>
                        <form id="editRtForm{{ rt.id }}" onsubmit="submitEditRT(event, {{ rt.id }})" class="flex flex-col gap-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="rt_id" value="{{ rt.id }}">
                            <div>
                                <label class="block text-sm font-bold text-gray-600 mb-1">Nomor Card</label>
                                <input type="text" name="nomor_card" value="{{ rt.nomor_card }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                            </div>
                            <div>
                                <label class="block text-sm font-bold text-gray-600 mb-1">Nama RT (Wilayah)</label>
                                <input type="text" name="rt_name" value="{{ rt.rt_name }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                            </div>
                            <div>
                                <label class="block text-sm font-bold text-gray-600 mb-1">Nama Ketua RT / PIC</label>
                                <input type="text" name="nama_ketua_rt" value="{{ rt.nama_ketua_rt }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-bold text-gray-600 mb-1">Alokasi (Bungkus)</label>
                                    <input type="number" name="alokasi" value="{{ rt.alokasi }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]" required>
                                </div>
                                <div>
                                    <label class="block text-sm font-bold text-gray-600 mb-1">Status</label>
                                    <select name="status" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-[#8B2635]">
                                        <option value="Menunggu" {{ 'selected' if rt.status == 'Menunggu' else '' }}>Menunggu</option>
                                        <option value="Diserahkan" {{ 'selected' if rt.status == 'Diserahkan' else '' }}>Diserahkan</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" class="mt-4 w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md transition-all">Save</button>
                        </form>
                    </div>
                </div>
                {% endif %}"""

content = content.replace(old_peta_html_card, new_peta_html_card)

# Add Peta JS scripts and polling
old_peta_html_end = """    </div>
</div>
'''"""

new_peta_html_end = """    </div>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {
    // 1. Add RT Form AJAX
    const form = document.getElementById('addRtForm');
    if(form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('addRtBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menambah...';

            const formData = new FormData(form);
            const jsonData = Object.fromEntries(formData.entries());
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;

            try {
                const response = await fetch('/idul-adha/peta-distribusi/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify(jsonData)
                });

                const data = await response.json();
                if(response.ok && data.success) {
                    const modal = document.getElementById('generateRTAnim');
                    const content = document.getElementById('rtModalContent');
                    const text1 = document.getElementById('rtText1');
                    const text2 = document.getElementById('rtText2');

                    modal.classList.remove('opacity-0', 'pointer-events-none');
                    content.classList.remove('scale-90');
                    content.classList.add('scale-100');

                    setTimeout(() => { text1.classList.remove('opacity-0'); text1.classList.add('opacity-100'); }, 1000);
                    setTimeout(() => { text2.classList.remove('opacity-0'); text2.classList.add('opacity-100'); }, 1300);

                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                } else {
                    alert(data.message || 'Gagal menambah RT');
                    btn.disabled = false;
                    btn.innerHTML = 'Tambah Data RT';
                }
            } catch(e) {
                alert('Kesalahan Jaringan');
                btn.disabled = false;
                btn.innerHTML = 'Tambah Data RT';
            }
        });
    }
});

// 2. Update Status RT AJAX
async function updateRTStatus(rtId, newStatus) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || document.querySelector('input[name="csrf_token"]')?.value;
    try {
        const response = await fetch('/idul-adha/peta-distribusi/update_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ rt_id: rtId, status: newStatus })
        });
        if(response.ok) {
            // Re-fetch data or rely on polling/reload. For immediate sync across UI:
            window.location.reload();
        }
    } catch(e) {
        console.error("Error updating RT status", e);
    }
}

// 3. Edit RT AJAX
async function submitEditRT(e, rtId) {
    e.preventDefault();
    const form = document.getElementById('editRtForm' + rtId);
    const formData = new FormData(form);
    const jsonData = Object.fromEntries(formData.entries());
    const csrfToken = formData.get('csrf_token');

    try {
        const response = await fetch('/idul-adha/peta-distribusi/edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify(jsonData)
        });
        if(response.ok) {
            window.location.reload();
        }
    } catch(e) {
        console.error("Error editing RT", e);
    }
}

// 4. Polling for live RT updates (for all users)
setInterval(async () => {
    try {
        const response = await fetch('/idul-adha/peta-distribusi/data');
        if(response.ok) {
            const data = await response.json();
            if(data.success) {
                // Update Progress Bar
                const progBar = document.getElementById('rtProgressBar');
                const progText = document.getElementById('rtProgressText');
                if(progBar && progText) {
                    progBar.style.width = data.progress_percentage + '%';
                    progText.innerHTML = data.diserahkan_count + ' / ' + data.total_rt + ' RT Selesai';
                }

                // Update Cards UI
                data.rt_list.forEach(rt => {
                    const statusBadgeCont = document.getElementById('rt-status-' + rt.id);
                    if(statusBadgeCont) {
                        if(rt.status === 'Diserahkan') {
                            statusBadgeCont.innerHTML = '<span class="bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-check-circle mr-1"></i> Diserahkan</span>';
                            // also update border color if needed
                            const cardRoot = document.getElementById('rt-card-' + rt.id);
                            if(cardRoot) cardRoot.className = "bg-white rounded-2xl shadow-lg border-2 border-emerald-500 overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1";
                        } else {
                            statusBadgeCont.innerHTML = '<span class="bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-clock mr-1"></i> Menunggu</span>';
                            const cardRoot = document.getElementById('rt-card-' + rt.id);
                            if(cardRoot) cardRoot.className = "bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1";
                        }
                    }
                    // For admin, we ideally wouldn't rebuild buttons here to avoid interrupting clicks, but reload on action handles it.
                });
            }
        }
    } catch(e) {
        console.error("Polling error", e);
    }
}, 5000); // Poll every 5 seconds
</script>
'''"""

content = content.replace(old_peta_html_end, new_peta_html_end)

# Add IDs to the cards and progress bar for polling updates
progress_old = """                    <div class="h-2 bg-white/20 rounded-full overflow-hidden">
                        <div class="h-full bg-white transition-all duration-1000" style="width: {{ progress_percentage }}%"></div>
                    </div>
                    <p class="text-xs mt-2 text-white/80 font-medium text-right">{{ diserahkan_count }} / {{ total_rt }} RT Selesai</p>"""

progress_new = """                    <div class="h-2 bg-white/20 rounded-full overflow-hidden">
                        <div id="rtProgressBar" class="h-full bg-white transition-all duration-1000" style="width: {{ progress_percentage }}%"></div>
                    </div>
                    <p id="rtProgressText" class="text-xs mt-2 text-white/80 font-medium text-right">{{ diserahkan_count }} / {{ total_rt }} RT Selesai</p>"""

content = content.replace(progress_old, progress_new)


card_root_old = """            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for rt in rt_list %}
                <div class="bg-white rounded-2xl shadow-lg {{ 'border-2 border-emerald-500' if rt.status == 'Diserahkan' else 'border border-gray-100' }} overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1">"""

card_root_new = """            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for rt in rt_list %}
                <div id="rt-card-{{ rt.id }}" class="bg-white rounded-2xl shadow-lg {{ 'border-2 border-emerald-500' if rt.status == 'Diserahkan' else 'border border-gray-100' }} overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1">"""

content = content.replace(card_root_old, card_root_new)

card_status_old = """                        <div class="flex justify-between items-start mb-4">
                            <span class="text-sm font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-lg">Card {{ rt.nomor_card }}</span>
                            {% if rt.status == 'Diserahkan' %}
                            <span class="bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-check-circle mr-1"></i> Diserahkan</span>
                            {% else %}
                            <span class="bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-clock mr-1"></i> Menunggu</span>
                            {% endif %}
                        </div>"""

card_status_new = """                        <div class="flex justify-between items-start mb-4">
                            <span class="text-sm font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-lg">Card {{ rt.nomor_card }}</span>
                            <div id="rt-status-{{ rt.id }}">
                                {% if rt.status == 'Diserahkan' %}
                                <span class="bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-check-circle mr-1"></i> Diserahkan</span>
                                {% else %}
                                <span class="bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-clock mr-1"></i> Menunggu</span>
                                {% endif %}
                            </div>
                        </div>"""

content = content.replace(card_status_old, card_status_new)


# Update Backend Routes
old_peta_routes = """@app.route('/idul-adha/peta-distribusi/add', methods=['POST'])
def idul_adha_peta_distribusi_add():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_peta_distribusi'))
    rt = QurbanRT(nomor_card=request.form.get('nomor_card'), rt_name=request.form.get('rt_name'), nama_ketua_rt=request.form.get('nama_ketua_rt'), alokasi=int(request.form.get('alokasi', 0)))
    db.session.add(rt)
    try:
        db.session.commit()
        flash("Data RT berhasil ditambahkan.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Gagal menambahkan data RT.", "error")
        app.logger.error(f"Error in idul_adha_peta_distribusi_add: {e}", exc_info=True)
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
            flash("Data RT berhasil diupdate.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Gagal mengupdate data RT.", "error")
            app.logger.error(f"Error in idul_adha_peta_distribusi_edit: {e}", exc_info=True)
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
            flash("Status RT berhasil diupdate.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Gagal mengupdate status RT.", "error")
            app.logger.error(f"Error in idul_adha_peta_distribusi_update_status: {e}", exc_info=True)
    return redirect(url_for('idul_adha_peta_distribusi'))"""

new_peta_routes = """@app.route('/idul-adha/peta-distribusi/add', methods=['POST'])
def idul_adha_peta_distribusi_add():
    if not session.get('is_admin'): return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        req_data = request.get_json(silent=True) or request.form
        rt = QurbanRT(
            nomor_card=req_data.get('nomor_card'),
            rt_name=req_data.get('rt_name'),
            nama_ketua_rt=req_data.get('nama_ketua_rt'),
            alokasi=int(req_data.get('alokasi', 0))
        )
        db.session.add(rt)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'message': 'Data RT berhasil ditambahkan.'})
        else:
            flash("Data RT berhasil ditambahkan.", "success")
            return redirect(url_for('idul_adha_peta_distribusi'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in idul_adha_peta_distribusi_add: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'message': 'Gagal menambahkan data RT.'}), 500
        else:
            flash("Gagal menambahkan data RT.", "error")
            return redirect(url_for('idul_adha_peta_distribusi'))

@app.route('/idul-adha/peta-distribusi/edit', methods=['POST'])
def idul_adha_peta_distribusi_edit():
    if not session.get('is_admin'): return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        req_data = request.get_json(silent=True) or request.form
        rt_id = req_data.get('rt_id')
        rt = QurbanRT.query.get(rt_id)
        if rt:
            rt.nomor_card = req_data.get('nomor_card')
            rt.rt_name = req_data.get('rt_name')
            rt.nama_ketua_rt = req_data.get('nama_ketua_rt')
            rt.alokasi = int(req_data.get('alokasi', 0))
            rt.status = req_data.get('status')
            db.session.commit()
            if request.is_json: return jsonify({'success': True, 'message': 'Data RT diupdate.'})
            else:
                flash("Data RT berhasil diupdate.", "success")
                return redirect(url_for('idul_adha_peta_distribusi'))
        return jsonify({'success': False, 'message': 'Not found'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in idul_adha_peta_distribusi_edit: {e}", exc_info=True)
        if request.is_json: return jsonify({'success': False, 'message': 'Gagal mengupdate.'}), 500
        return redirect(url_for('idul_adha_peta_distribusi'))

@app.route('/idul-adha/peta-distribusi/update_status', methods=['POST'])
@csrf.exempt
def idul_adha_peta_distribusi_update_status():
    if not session.get('is_admin'): return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        req_data = request.get_json(silent=True) or request.form
        rt_id = req_data.get('rt_id')
        status = req_data.get('status')
        rt = QurbanRT.query.get(rt_id)
        if rt:
            rt.status = status
            db.session.commit()
            if request.is_json: return jsonify({'success': True, 'message': 'Status diupdate.'})
            else:
                flash("Status RT berhasil diupdate.", "success")
                return redirect(url_for('idul_adha_peta_distribusi'))
        return jsonify({'success': False, 'message': 'Not found'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in idul_adha_peta_distribusi_update_status: {e}", exc_info=True)
        if request.is_json: return jsonify({'success': False, 'message': 'Gagal mengupdate.'}), 500
        return redirect(url_for('idul_adha_peta_distribusi'))

@app.route('/idul-adha/peta-distribusi/data', methods=['GET'])
def idul_adha_peta_distribusi_data():
    rt_list = QurbanRT.query.order_by(QurbanRT.id.asc()).all()
    total_rt = len(rt_list)
    diserahkan_count = len([rt for rt in rt_list if rt.status == 'Diserahkan'])
    progress_percentage = (diserahkan_count / total_rt * 100) if total_rt > 0 else 0
    rt_data = [{'id': rt.id, 'status': rt.status} for rt in rt_list]
    return jsonify({
        'success': True,
        'total_rt': total_rt,
        'diserahkan_count': diserahkan_count,
        'progress_percentage': progress_percentage,
        'rt_list': rt_data
    })"""

content = content.replace(old_peta_routes, new_peta_routes)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
