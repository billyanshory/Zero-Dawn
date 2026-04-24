import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Add missing 'admin_panel_html' placement in 'IDUL_ADHA_LACAK_HTML'
if "<!-- ADMIN PIN PANEL -->" not in content:
    content = content.replace(
        '<!-- Main Content -->\n    <div class="max-w-xl mx-auto px-5 md:px-8 mt-[-2rem] relative z-20">',
        '<!-- Main Content -->\n    <div class="max-w-xl mx-auto px-5 md:px-8 mt-[-2rem] relative z-20">\n' + """
            <!-- ADMIN PIN PANEL -->
            {% if is_admin %}
            <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-red-100 mb-8" id="admin-pin-panel">
                <div class="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
                    <h3 class="text-lg font-bold text-red-700"><i class="fas fa-lock mr-2"></i>Panel Admin: Manajemen PIN Shohibul</h3>
                    <button onclick="openPinListModal()" class="bg-[#1B4332] text-white text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-[#153426] transition">
                        <i class="fas fa-list mr-1"></i> Daftar PIN
                    </button>
                </div>

                <form id="generate-pin-form" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-600 mb-1">Nama Shohibul</label>
                            <input type="text" id="shohibul_name" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-red-500 focus:ring-1 focus:ring-red-500">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-600 mb-1">Jenis Hewan</label>
                            <select id="animal_type" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-red-500 focus:ring-1 focus:ring-red-500">
                                <option value="Sapi">Sapi</option>
                                <option value="Kambing">Kambing</option>
                            </select>
                        </div>
                    </div>
                    <button type="button" onclick="generatePin()" class="w-full bg-red-700 text-white font-bold py-3 mt-2 rounded-xl hover:bg-red-800 transition shadow-lg">
                        Generate PIN Baru
                    </button>
                </form>

                <div id="new-pin-display" class="hidden mt-6 p-4 bg-green-50 rounded-xl border border-green-200 text-center">
                    <p class="text-xs text-green-700 font-bold mb-1">PIN Berhasil Dibuat!</p>
                    <div class="text-3xl font-mono font-bold text-green-800 tracking-widest" id="generated-pin-text"></div>
                    <p class="text-sm mt-2 text-gray-600">Untuk Shohibul: <strong id="generated-name-text"></strong></p>
                </div>
            </div>

            <!-- PIN LIST MODAL -->
            <div id="modal-pin-list" class="hidden fixed inset-0 z-[100] flex items-center justify-center p-4">
                <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closePinListModal()"></div>
                <div class="bg-white rounded-3xl w-full max-w-3xl relative z-10 shadow-2xl flex flex-col max-h-[80vh]">
                    <div class="p-6 border-b border-gray-100 flex items-center justify-between">
                        <h2 class="text-xl font-bold text-gray-800">Daftar PIN Shohibul</h2>
                        <button onclick="closePinListModal()" class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="p-6 overflow-y-auto">
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm whitespace-nowrap">
                                <thead class="bg-gray-50 text-gray-600 font-bold">
                                    <tr>
                                        <th class="p-3 rounded-tl-lg">PIN</th>
                                        <th class="p-3">Nama</th>
                                        <th class="p-3">Hewan</th>
                                        <th class="p-3">Status</th>
                                        <th class="p-3 rounded-tr-lg">Dibuat</th>
                                    </tr>
                                </thead>
                                <tbody id="pin-list-tbody" class="divide-y divide-gray-100 text-gray-700">
                                    <tr><td colspan="5" class="p-4 text-center">Memuat data...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                async function generatePin() {
                    const name = document.getElementById('shohibul_name').value;
                    const type = document.getElementById('animal_type').value;
                    if(!name) { alert("Nama Shohibul harus diisi"); return; }

                    try {
                        const res = await fetch('/api/qurban/shohibul/generate_pin', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({name: name, type: type})
                        });
                        const data = await res.json();
                        if(res.ok && data.success) {
                            document.getElementById('generated-pin-text').innerText = data.pin;
                            document.getElementById('generated-name-text').innerText = name;
                            document.getElementById('new-pin-display').classList.remove('hidden');
                            document.getElementById('shohibul_name').value = '';
                        } else {
                            throw new Error(data.error || "Gagal membuat PIN");
                        }
                    } catch(e) {
                        alert(e.message);
                    }
                }

                function closePinListModal() {
                    document.getElementById('modal-pin-list').classList.add('hidden');
                }

                async function openPinListModal() {
                    document.getElementById('modal-pin-list').classList.remove('hidden');
                    const tbody = document.getElementById('pin-list-tbody');
                    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center">Memuat data...</td></tr>';

                    try {
                        const res = await fetch('/api/qurban/shohibul/list_pins');
                        const data = await res.json();
                        if(res.ok && data.success) {
                            if(data.pins.length === 0) {
                                tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">Belum ada PIN.</td></tr>';
                                return;
                            }
                            tbody.innerHTML = data.pins.map(p => `
                                <tr class="hover:bg-gray-50">
                                    <td class="p-3 font-mono font-bold text-red-700">${p.pin}</td>
                                    <td class="p-3">${p.name}</td>
                                    <td class="p-3">${p.type}</td>
                                    <td class="p-3"><span class="bg-gray-100 px-2 py-1 rounded text-xs">${p.status}</span></td>
                                    <td class="p-3 text-xs text-gray-500">${p.created_at}</td>
                                </tr>
                            `).join('');
                        } else {
                            throw new Error(data.error || "Gagal memuat data");
                        }
                    } catch(e) {
                        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-red-500">${e.message}</td></tr>`;
                    }
                }
            </script>
            {% endif %}

"""
    )
    with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
        f.write(content)
