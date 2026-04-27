import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    text = f.read()

new_peta_html = """
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800">
    <div class="max-w-6xl mx-auto mb-12">
        <div class="flex items-center gap-4 mb-8">
            <a href="/idul-adha" class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 shadow-md hover:bg-[#8B2635] hover:text-white transition-colors">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div>
                <h1 class="text-3xl font-bold text-[#8B2635]">Peta Distribusi</h1>
                <p class="text-gray-500 mt-1">Live Tracking Penyaluran Daging Qurban per RT</p>
            </div>
        </div>

        {% if is_admin %}
        <div class="bg-white rounded-3xl shadow-xl border border-orange-200 p-6 mb-8 relative">
            <div class="absolute top-0 right-0 bg-orange-600 text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-lock mr-1"></i> Panel Admin</div>
            <h2 class="text-xl font-bold text-orange-600 mb-4 border-b border-orange-100 pb-2">Tambah Data RT Baru</h2>
            <form id="addRtForm" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Nomor Card</label>
                    <input type="text" name="nomor_card" placeholder="Contoh: RT01" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Nama RT (Wilayah)</label>
                    <input type="text" name="rt_name" placeholder="Contoh: RT 01 Delima" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Nama Ketua RT / PIC</label>
                    <input type="text" name="nama_ketua_rt" placeholder="Contoh: Bpk. Supriadi" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Alokasi (Bungkus)</label>
                    <input type="number" name="alokasi" placeholder="Contoh: 45" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:border-orange-600" required>
                </div>
                <div class="md:col-span-4 mt-2">
                    <button type="submit" id="addRtBtn" class="w-full bg-orange-600 text-white font-bold py-3 rounded-xl hover:bg-orange-700 shadow-md transition-all">Tambah Data RT</button>
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
        @keyframes bounce {
            from { transform: translateY(0); }
            to { transform: translateY(-5px); }
        }
        </style>
        {% endif %}

        <div class="bg-gradient-to-r from-orange-600 to-[#8B2635] rounded-3xl shadow-xl p-8 mb-8 text-white">
            <div class="flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                    <h2 class="text-2xl font-bold mb-2">Progress Distribusi RT</h2>
                    <p class="text-white/80">Pantau secara live RT mana saja yang telah menerima jatah qurban.</p>
                </div>
                <div class="w-full md:w-1/2">
                    <div class="h-2 bg-white/20 rounded-full overflow-hidden">
                        <div id="rtProgressBar" class="h-full bg-white transition-all duration-1000" style="width: {{ progress_percentage }}%"></div>
                    </div>
                    <p id="rtProgressText" class="text-xs mt-2 text-white/80 font-medium text-right">{{ diserahkan_count }} / {{ total_rt }} RT Selesai</p>
                </div>
            </div>
        </div>

        <div class="mb-6 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-800">Daftar Status RT</h2>
            <div class="flex gap-2">
                <span class="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100"><i class="fas fa-check-circle"></i> Selesai</span>
                <span class="flex items-center gap-1 text-xs font-bold text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-100"><i class="fas fa-clock"></i> Menunggu</span>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% for rt in rt_list %}
            <div id="rt-card-{{ rt.id }}" class="bg-white rounded-2xl shadow-lg {{ 'border-2 border-emerald-500' if rt.status == 'Diserahkan' else 'border border-gray-100' }} overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1">
                <div class="p-6">
                    <div class="flex justify-between items-start mb-4">
                        <span class="text-sm font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-lg">Card {{ rt.nomor_card }}</span>
                        <div id="rt-status-{{ rt.id }}">
                            {% if rt.status == 'Diserahkan' %}
                            <span class="bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-check-circle mr-1"></i> Diserahkan</span>
                            {% else %}
                            <span class="bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-clock mr-1"></i> Menunggu</span>
                            {% endif %}
                        </div>
                    </div>

                    <h3 class="text-xl font-bold text-gray-800 mb-1">{{ rt.rt_name }}</h3>
                    <div class="flex items-center gap-2 text-gray-500 mb-4 text-sm">
                        <i class="fas fa-user-tie w-4 text-center"></i> <span>PIC: {{ rt.nama_ketua_rt }}</span>
                    </div>

                    <div class="bg-orange-50 rounded-xl p-3 flex justify-between items-center border border-orange-100">
                        <span class="text-xs font-bold text-orange-800 uppercase">Alokasi Daging</span>
                        <span class="font-bold text-orange-600 text-lg">{{ rt.alokasi }} <span class="text-xs text-orange-400 font-normal">Bungkus</span></span>
                    </div>
                </div>

                <div class="p-4 bg-gray-50 flex justify-between items-center border-t border-gray-100">
                    {% if is_admin %}
                    <div class="w-full flex gap-2">
                        {% if rt.status == 'Menunggu' %}
                        <button onclick="updateRTStatus({{ rt.id }}, 'Diserahkan')" class="flex-1 bg-emerald-100 text-emerald-700 py-2 rounded-lg font-bold text-sm hover:bg-emerald-200 transition-colors">Serahkan Jatah</button>
                        {% else %}
                        <button onclick="updateRTStatus({{ rt.id }}, 'Menunggu')" class="flex-1 bg-red-100 text-red-700 py-2 rounded-lg font-bold text-sm hover:bg-red-200 transition-colors">Batal Serahkan</button>
                        {% endif %}
                        <button type="button" onclick="openEditRTModal({{ rt.id }}, '{{ rt.nomor_card }}', '{{ rt.rt_name }}', '{{ rt.nama_ketua_rt }}', {{ rt.alokasi }}, '{{ rt.status }}')" class="px-3 bg-gray-200 text-gray-600 rounded-lg hover:bg-gray-300"><i class="fas fa-pen"></i></button>
                    </div>
                    {% else %}
                    <div class="w-full text-center text-xs text-gray-500 font-medium">Update Terakhir: Hari ini</div>
                    {% endif %}
                </div>
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
            <form id="editRtForm" class="space-y-4">
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
                <button type="submit" id="editRtBtn" class="w-full bg-orange-600 text-white font-bold py-2 rounded-xl hover:bg-orange-700 shadow-md mt-2 transition-all">Save</button>
            </form>
        </div>
    </div>
    {% endif %}
</div>

<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Add RT Form AJAX
        const addForm = document.getElementById('addRtForm');
        if(addForm) {
            addForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('addRtBtn');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menambah...';

                const formData = new FormData(addForm);
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

        // Edit RT AJAX
        const editForm = document.getElementById('editRtForm');
        if(editForm) {
            editForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('editRtBtn');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';

                const formData = new FormData(editForm);
                const jsonData = Object.fromEntries(formData.entries());
                const csrfToken = document.querySelector('input[name="csrf_token"]').value;

                try {
                    const response = await fetch('/idul-adha/peta-distribusi/edit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                        body: JSON.stringify(jsonData)
                    });
                    const data = await response.json();
                    if(response.ok && data.success) {
                        window.location.reload();
                    } else {
                        alert(data.message || 'Gagal Edit RT');
                        btn.disabled = false;
                        btn.innerHTML = 'Save';
                    }
                } catch(e) {
                    alert('Kesalahan Jaringan');
                    btn.disabled = false;
                    btn.innerHTML = 'Save';
                }
            });
        }
    });

    // Update Status RT AJAX
    async function updateRTStatus(rtId, newStatus) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || document.querySelector('input[name="csrf_token"]')?.value;
        try {
            const response = await fetch('/idul-adha/peta-distribusi/update_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ rt_id: rtId, status: newStatus })
            });
            if(response.ok) {
                window.location.reload();
            }
        } catch(e) {
            console.error("Error updating RT status", e);
        }
    }

    function openEditRTModal(id, no, rt, ketua, alokasi, status) {
        document.getElementById('edit_rt_id').value = id;
        document.getElementById('edit_nomor_card').value = no;
        document.getElementById('edit_rt_name').value = rt;
        document.getElementById('edit_nama_ketua_rt').value = ketua;
        document.getElementById('edit_alokasi').value = alokasi;
        document.getElementById('edit_status').value = status;
        document.getElementById('modal-edit-rt').classList.remove('hidden');
    }

    // Polling for live RT updates (for all users)
    setInterval(async () => {
        try {
            const response = await fetch('/idul-adha/peta-distribusi/data');
            if(response.ok) {
                const data = await response.json();
                if(data.success) {
                    const progBar = document.getElementById('rtProgressBar');
                    const progText = document.getElementById('rtProgressText');
                    if(progBar && progText) {
                        progBar.style.width = data.progress_percentage + '%';
                        progText.innerHTML = data.diserahkan_count + ' / ' + data.total_rt + ' RT Selesai';
                    }

                    data.rt_list.forEach(rt => {
                        const statusBadgeCont = document.getElementById('rt-status-' + rt.id);
                        if(statusBadgeCont) {
                            if(rt.status === 'Diserahkan') {
                                statusBadgeCont.innerHTML = '<span class="bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-check-circle mr-1"></i> Diserahkan</span>';
                                const cardRoot = document.getElementById('rt-card-' + rt.id);
                                if(cardRoot) cardRoot.className = "bg-white rounded-2xl shadow-lg border-2 border-emerald-500 overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1";
                            } else {
                                statusBadgeCont.innerHTML = '<span class="bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full"><i class="fas fa-clock mr-1"></i> Menunggu</span>';
                                const cardRoot = document.getElementById('rt-card-' + rt.id);
                                if(cardRoot) cardRoot.className = "bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden relative transition-all duration-300 transform hover:-translate-y-1";
                            }
                        }
                    });
                }
            }
        } catch(e) {
            console.error("Polling error", e);
        }
    }, 5000);
</script>
"""

# Replace the specific old template with the new one
text = re.sub(r'IDUL_ADHA_PETA_DISTRIBUSI_HTML = \'\'\'.*?\'\'\'', f"IDUL_ADHA_PETA_DISTRIBUSI_HTML = '''{new_peta_html}'''", text, flags=re.DOTALL)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(text)
