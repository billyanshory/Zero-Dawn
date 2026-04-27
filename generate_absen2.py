import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# 2. Add New HTML Template for Absen Panitia
# Put it right before IDUL_ADHA_DASHBOARD_HTML

absen_html_template = """
IDUL_ADHA_ABSEN_PANITIA_HTML = '''
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800">
    <div class="max-w-6xl mx-auto mb-12">
        <div class="flex items-center gap-4 mb-8">
            <a href="/idul-adha" class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 shadow-md hover:bg-[#8B2635] hover:text-white transition-colors">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div>
                <h1 class="text-3xl font-bold text-[#8B2635]">Sistem Absensi Panitia</h1>
                <p class="text-gray-500 mt-1">Portal Pendaftaran & Kehadiran Qurban</p>
            </div>
        </div>

        <!-- Panel 1: Top Banner / Notifikasi (User & Admin) -->
        <div id="statusBanner" class="rounded-3xl shadow-lg p-6 mb-8 text-white transition-colors duration-500 {{ 'bg-gradient-to-r from-emerald-500 to-teal-600' if is_valid_window else 'bg-gradient-to-r from-red-600 to-[#8B2635]' }}">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center text-3xl">
                        <i id="bannerIcon" class="{{ 'fas fa-door-open' if is_valid_window else 'fas fa-door-closed' }}"></i>
                    </div>
                    <div>
                        <h2 id="bannerTitle" class="text-2xl font-bold">{{ 'Absensi Sedang Dibuka' if is_valid_window else 'LATE: Terlambat, Absensi Ditutup' }}</h2>
                        <p id="bannerDesc" class="text-white/80 text-sm mt-1">Silakan mengisi absensi kehadiran Anda sebelum waktu habis.</p>
                    </div>
                </div>
                <div class="text-center bg-black/20 px-6 py-3 rounded-2xl border border-white/20">
                    <p class="text-xs uppercase font-bold text-white/60 mb-1">Sisa Waktu</p>
                    <p id="absenCountdownTimer" class="font-mono text-2xl font-bold tracking-wider">--:--:--</p>
                </div>
            </div>
        </div>

        {% if is_admin %}
        <!-- ADMIN AREA -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">

            <!-- Admin Panel 1: Setting Absent Time -->
            <div class="bg-white rounded-3xl shadow-xl border border-orange-200 p-6 relative col-span-1 h-fit">
                <div class="absolute top-0 right-0 bg-orange-600 text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-lock mr-1"></i> Panel 1</div>
                <h3 class="text-lg font-bold text-orange-600 mb-4 border-b border-orange-100 pb-2">Setting Waktu Absen</h3>
                <form id="settingWaktuForm" class="space-y-4">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Mulai Jam</label>
                            <input type="time" name="absen_start" value="{{ settings.get('absen_start_time', '06:30') }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Tutup Jam</label>
                            <input type="time" name="absen_end" value="{{ settings.get('absen_end_time', '08:30') }}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600">
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Status Manual</label>
                        <select name="absen_status" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm focus:outline-none focus:border-orange-600">
                            <option value="auto" {{ 'selected' if settings.get('absen_status', 'auto') == 'auto' else '' }}>Otomatis Mengikuti Jam</option>
                            <option value="open" {{ 'selected' if settings.get('absen_status', 'auto') == 'open' else '' }}>Buka Paksa (Bypass LATE)</option>
                            <option value="closed" {{ 'selected' if settings.get('absen_status', 'auto') == 'closed' else '' }}>Tutup Paksa</option>
                        </select>
                    </div>
                    <button type="submit" id="saveSettingBtn" class="w-full bg-orange-600 text-white font-bold py-2 rounded-xl hover:bg-orange-700 shadow-sm transition-colors text-sm">Save Settings</button>
                </form>
            </div>

            <!-- Admin Panel 3: Live Analytics -->
            <div class="bg-white rounded-3xl shadow-xl border border-blue-200 p-6 relative lg:col-span-2">
                <div class="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-chart-pie mr-1"></i> Panel 3</div>
                <div class="flex justify-between items-center mb-4 border-b border-blue-100 pb-2">
                    <h3 class="text-lg font-bold text-blue-600">Live Analytics</h3>
                    <a href="/idul-adha/absen-panitia/export" target="_blank" class="text-xs bg-green-100 text-green-700 px-3 py-1.5 rounded-full font-bold hover:bg-green-200 transition-colors"><i class="fas fa-file-excel mr-1"></i> Export Excel</a>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-gray-50 rounded-2xl p-4 border border-gray-100 text-center">
                        <p class="text-xs text-gray-500 font-bold uppercase mb-1">Terdaftar</p>
                        <p id="statTotal" class="text-3xl font-bold text-gray-800">0</p>
                    </div>
                    <div class="bg-green-50 rounded-2xl p-4 border border-green-100 text-center">
                        <p class="text-xs text-green-600 font-bold uppercase mb-1">Hadir Pagi</p>
                        <p id="statHadir" class="text-3xl font-bold text-green-700">0</p>
                    </div>
                    <div class="bg-amber-50 rounded-2xl p-4 border border-amber-100 text-center">
                        <p class="text-xs text-amber-600 font-bold uppercase mb-1">Menunggu</p>
                        <p id="statMenunggu" class="text-3xl font-bold text-amber-700">0</p>
                    </div>
                    <div class="bg-red-50 rounded-2xl p-4 border border-red-100 text-center">
                        <p class="text-xs text-red-600 font-bold uppercase mb-1">Terlambat/Bolos</p>
                        <p id="statTerlambat" class="text-3xl font-bold text-red-700">0</p>
                    </div>
                </div>
            </div>

        </div>

        <!-- Admin Panel 2: List Panitia & Role Assignment -->
        <div class="bg-white rounded-3xl shadow-xl border border-emerald-200 p-6 relative mb-8">
            <div class="absolute top-0 right-0 bg-emerald-600 text-white px-3 py-1 rounded-bl-xl rounded-tr-3xl text-xs font-bold"><i class="fas fa-users mr-1"></i> Panel 2</div>
            <h3 class="text-lg font-bold text-emerald-600 mb-4 border-b border-emerald-100 pb-2">List Panitia & Assign Role</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 text-gray-600">
                        <tr>
                            <th class="p-3 rounded-l-xl">Nama & No HP</th>
                            <th class="p-3">Waktu Datang</th>
                            <th class="p-3">Approval</th>
                            <th class="p-3 rounded-r-xl">Role / Pos Tugas</th>
                        </tr>
                    </thead>
                    <tbody id="panitiaListBody">
                        <tr><td colspan="4" class="text-center py-4 text-gray-400">Memuat data...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}


        <!-- USER AREA -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">

            <!-- Core Interaction Module -->
            <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 flex flex-col justify-center min-h-[300px]">
                <h3 class="text-xl font-bold text-[#8B2635] mb-6 border-b border-gray-100 pb-2">Modul Kehadiran Anda</h3>

                <div id="userStateContainer">
                    <div class="text-center py-8"><i class="fas fa-circle-notch fa-spin text-4xl text-gray-300"></i></div>
                </div>
            </div>

            <!-- Digital ID Card -->
            <div class="relative rounded-3xl shadow-xl overflow-hidden min-h-[300px] border border-gray-200 bg-gray-100" id="idCardWrapper">
                <!-- Blurred overlay if not present -->
                <div id="idCardOverlay" class="absolute inset-0 z-20 backdrop-blur-md bg-white/60 flex flex-col items-center justify-center">
                    <div class="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4 text-gray-400">
                        <i class="fas fa-lock text-2xl"></i>
                    </div>
                    <p class="font-bold text-gray-500 text-center px-6">ID Card Digital akan terbuka setelah Anda absen "Hadir".</p>
                </div>

                <!-- The ID Card -->
                <div class="absolute inset-0 bg-white">
                    <div class="h-24 bg-[#1B4332] w-full absolute top-0 flex items-center justify-center">
                        <p class="text-white font-bold tracking-widest text-sm uppercase opacity-50">Panitia Qurban Al Hijrah</p>
                    </div>
                    <div class="relative z-10 pt-16 flex flex-col items-center">
                        <div class="w-24 h-24 bg-white rounded-full p-1 shadow-lg mb-4">
                            <div class="w-full h-full bg-gray-200 rounded-full flex items-center justify-center text-4xl text-gray-400 overflow-hidden">
                                <i class="fas fa-user"></i>
                            </div>
                        </div>
                        <h2 id="cardName" class="text-2xl font-bold text-gray-800 mb-1">-</h2>
                        <p class="text-xs text-gray-400 font-mono mb-4">ID: <span id="cardId">-</span></p>

                        <div class="w-11/12 bg-amber-50 rounded-2xl p-4 border border-amber-200 text-center shadow-inner">
                            <p class="text-xs text-amber-700 font-bold uppercase tracking-wider mb-1">Tugas Anda Hari Ini</p>
                            <p id="cardPos" class="text-lg font-bold text-amber-900">-</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>

<!-- SCRIPTS FOR ABSEN PANITIA -->
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Inject CSRF Token globally for fetches
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
    const isAdmin = {{ 'true' if is_admin else 'false' }};

    // Polling Data
    async function fetchAbsenData() {
        try {
            const res = await fetch('/idul-adha/absen-panitia/data');
            if(res.ok) {
                const data = await res.json();
                if(data.success) {
                    renderUserArea(data.user_data, data.is_window_open);
                    renderBanner(data.is_window_open, data.countdown_str);
                    if(isAdmin) {
                        renderAdminArea(data.all_data);
                        renderAnalytics(data.analytics);
                    }
                }
            }
        } catch(e) { console.error("Poll error", e); }
    }

    function renderBanner(isOpen, timerStr) {
        const banner = document.getElementById('statusBanner');
        const icon = document.getElementById('bannerIcon');
        const title = document.getElementById('bannerTitle');
        const timer = document.getElementById('absenCountdownTimer');

        timer.innerText = timerStr;
        if(isOpen) {
            banner.className = "rounded-3xl shadow-lg p-6 mb-8 text-white transition-colors duration-500 bg-gradient-to-r from-emerald-500 to-teal-600";
            icon.className = "fas fa-door-open";
            title.innerText = "Absensi Sedang Dibuka";
        } else {
            banner.className = "rounded-3xl shadow-lg p-6 mb-8 text-white transition-colors duration-500 bg-gradient-to-r from-red-600 to-[#8B2635]";
            icon.className = "fas fa-door-closed";
            title.innerText = "LATE: Terlambat, Absensi Ditutup";
        }
    }

    function renderUserArea(user, isOpen) {
        const cont = document.getElementById('userStateContainer');
        const overlay = document.getElementById('idCardOverlay');
        const cardName = document.getElementById('cardName');
        const cardId = document.getElementById('cardId');
        const cardPos = document.getElementById('cardPos');

        if(!user) {
            // Condition A: Belum Terdaftar
            cont.innerHTML = `
                <form id="joinPanitiaForm" class="space-y-4">
                    <input type="text" id="j_name" placeholder="Nama Lengkap" class="w-full p-3 rounded-xl border focus:border-[#8B2635] outline-none" required>
                    <input type="text" id="j_hp" placeholder="Nomor HP / WhatsApp" class="w-full p-3 rounded-xl border focus:border-[#8B2635] outline-none" required>
                    <select id="j_tugas" class="w-full p-3 rounded-xl border focus:border-[#8B2635] outline-none" required>
                        <option value="" disabled selected>Pilih Tugas yang Diinginkan</option>
                        <option value="Pemotongan">Pemotongan</option>
                        <option value="Penimbangan">Penimbangan</option>
                        <option value="Pencacahan Tulang">Pencacahan Tulang</option>
                        <option value="Distribusi Daging">Distribusi Daging</option>
                        <option value="Kebersihan">Kebersihan</option>
                    </select>
                    <button type="button" onclick="submitJoinForm()" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md transition-colors">Ajukan Diri Sebagai Panitia</button>
                </form>
            `;
            overlay.classList.remove('hidden');
            return;
        }

        if(user.approval_status === 'Menunggu') {
            // Condition B: Menunggu
            cont.innerHTML = `
                <div class="text-center p-6 bg-amber-50 rounded-2xl border border-amber-100">
                    <div class="w-20 h-20 bg-amber-100 text-amber-500 rounded-full flex items-center justify-center mx-auto mb-4 text-4xl">
                        <i class="fas fa-hourglass-half animate-pulse"></i>
                    </div>
                    <h4 class="font-bold text-amber-800 text-lg">Menunggu Persetujuan Admin</h4>
                    <p class="text-sm text-amber-700 mt-2">Pendaftaran Anda telah masuk. Silakan tunggu DKM menyetujui Anda.</p>
                </div>
            `;
            overlay.classList.remove('hidden');
            return;
        }

        if(user.approval_status === 'Approved') {
            if(!user.is_present) {
                if(isOpen) {
                    // Condition C1: Approved & Open -> SAYA HADIR
                    cont.innerHTML = `
                        <button onclick="submitHadir()" class="w-full h-40 bg-gradient-to-b from-emerald-400 to-emerald-600 rounded-3xl shadow-xl shadow-emerald-200 text-white flex flex-col items-center justify-center transform hover:scale-105 transition-all duration-300">
                            <i class="fas fa-fingerprint text-5xl mb-2"></i>
                            <span class="text-2xl font-black tracking-widest">SAYA HADIR</span>
                        </button>
                    `;
                } else {
                    // Condition D: LATE
                    cont.innerHTML = `
                        <div class="text-center p-6 bg-red-50 rounded-2xl border border-red-100">
                            <div class="w-20 h-20 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4 text-4xl">
                                <i class="fas fa-ban"></i>
                            </div>
                            <h4 class="font-bold text-red-800 text-lg">Waktu Telah Habis</h4>
                            <p class="text-sm text-red-700 mt-2">Maaf, Anda tidak dapat melakukan absensi. Silakan hubungi Admin di lapangan.</p>
                        </div>
                    `;
                }
                overlay.classList.remove('hidden');
            } else {
                // Condition C2: Already Present
                cont.innerHTML = `
                    <div class="w-full h-40 bg-green-50 rounded-3xl border-2 border-green-500 flex flex-col items-center justify-center">
                        <i class="fas fa-check-circle text-5xl text-green-500 mb-2"></i>
                        <span class="text-xl font-bold text-green-700">Telah Hadir</span>
                        <span class="text-xs text-green-600">pukul ${user.check_in_time}</span>
                    </div>
                `;
                // Unlock ID Card
                overlay.classList.add('hidden');
                cardName.innerText = user.name;
                cardId.innerText = 'PAN-' + String(user.id).padStart(4, '0');
                cardPos.innerText = user.pos_tugas || "Menunggu Instruksi Lapangan";
            }
        }
    }

    function renderAdminArea(list) {
        const body = document.getElementById('panitiaListBody');
        if(!body) return;
        let html = '';
        if(list.length === 0) {
            html = `<tr><td colspan="4" class="text-center py-4 text-gray-400">Belum ada panitia</td></tr>`;
        } else {
            list.forEach(p => {
                let btnApprove = p.approval_status === 'Menunggu' ? `<button onclick="actionAdmin('approve', ${p.id})" class="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded hover:bg-emerald-200">Setujui</button>` : `<span class="text-xs text-green-600 font-bold"><i class="fas fa-check"></i> ${p.approval_status}</span>`;
                let selectRole = `<select onchange="actionAdmin('assign', ${p.id}, this.value)" class="text-xs border rounded p-1 w-full focus:outline-none">
                    <option value="" disabled ${!p.pos_tugas ? 'selected' : ''}>Pilih Pos</option>
                    <option value="Pos Pemotongan" ${p.pos_tugas === 'Pos Pemotongan' ? 'selected' : ''}>Pos Pemotongan</option>
                    <option value="Pos Penimbangan" ${p.pos_tugas === 'Pos Penimbangan' ? 'selected' : ''}>Pos Penimbangan</option>
                    <option value="Pos Cacah Tulang" ${p.pos_tugas === 'Pos Cacah Tulang' ? 'selected' : ''}>Pos Cacah Tulang</option>
                    <option value="Pos Distribusi Daging" ${p.pos_tugas === 'Pos Distribusi Daging' ? 'selected' : ''}>Pos Distribusi</option>
                </select>`;

                html += `
                <tr class="border-b border-gray-100 hover:bg-gray-50">
                    <td class="p-3">
                        <div class="font-bold text-gray-800">${p.name}</div>
                        <div class="text-xs text-gray-400">${p.no_hp || '-'}</div>
                    </td>
                    <td class="p-3">
                        <div class="text-sm font-medium ${p.is_present ? 'text-green-600' : 'text-red-500'}">${p.is_present ? 'Hadir' : 'Belum Hadir'}</div>
                        <div class="text-xs text-gray-400">${p.check_in_time || '-'}</div>
                    </td>
                    <td class="p-3">${btnApprove}</td>
                    <td class="p-3">${selectRole}</td>
                </tr>
                `;
            });
        }
        body.innerHTML = html;
    }

    function renderAnalytics(a) {
        if(document.getElementById('statTotal')) {
            document.getElementById('statTotal').innerText = a.total;
            document.getElementById('statHadir').innerText = a.hadir;
            document.getElementById('statMenunggu').innerText = a.menunggu;
            document.getElementById('statTerlambat').innerText = a.terlambat;
        }
    }

    // Window Functions for Forms & Actions
    window.submitJoinForm = async function() {
        const name = document.getElementById('j_name').value;
        const hp = document.getElementById('j_hp').value;
        const tugas = document.getElementById('j_tugas').value;
        if(!name || !hp || !tugas) return alert('Lengkapi data');

        try {
            const res = await fetch('/idul-adha/absen-panitia/register', {
                method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken':csrfToken},
                body: JSON.stringify({name, hp, tugas})
            });
            if(res.ok) fetchAbsenData();
        } catch(e) { console.error(e); }
    }

    window.submitHadir = async function() {
        try {
            const res = await fetch('/idul-adha/absen-panitia/checkin', {
                method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken':csrfToken}
            });
            const data = await res.json();
            if(res.ok && data.success) fetchAbsenData();
            else alert(data.message || 'Gagal absen');
        } catch(e) { console.error(e); }
    }

    window.actionAdmin = async function(action, id, val='') {
        try {
            const url = action === 'approve' ? '/idul-adha/absen-panitia/approve' : '/idul-adha/absen-panitia/assign';
            const payload = { id: id };
            if(val) payload.pos_tugas = val;

            const res = await fetch(url, {
                method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken':csrfToken},
                body: JSON.stringify(payload)
            });
            if(res.ok) fetchAbsenData();
        } catch(e) { console.error(e); }
    }

    // Admin Setting Form Submit
    const settingForm = document.getElementById('settingWaktuForm');
    if(settingForm) {
        settingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('saveSettingBtn');
            btn.innerHTML = 'Saving...';
            const fd = new FormData(settingForm);
            const jsonData = Object.fromEntries(fd.entries());
            try {
                await fetch('/idul-adha/absen-panitia/settings', {
                    method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken':csrfToken},
                    body: JSON.stringify(jsonData)
                });
                btn.innerHTML = 'Save Settings';
                fetchAbsenData();
            } catch(e) { console.error(e); }
        });
    }

    // Start Polling
    fetchAbsenData();
    setInterval(fetchAbsenData, 3000);
});
</script>
'''
"""
content = content.replace("IDUL_ADHA_DASHBOARD_HTML =", absen_html_template + "\nIDUL_ADHA_DASHBOARD_HTML =")

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
