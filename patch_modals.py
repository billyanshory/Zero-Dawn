import sys

filepath = "kampus-stie-samarinda-0 ( idcloudhost - 3 dashboard utama - tu, mahasiswa dan dosen ).py"

with open(filepath, 'r') as f:
    content = f.read()

# Grab everything from "<!-- 1. MODAL PABRIK SURAT OTOMATIS -->" up to right before "</div>\n\n<script>" which ends the RAMADHAN_DASHBOARD_HTML

start_marker = "<!-- 1. MODAL PABRIK SURAT OTOMATIS -->"
end_marker = "</div>\n\n<script>"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx != -1 and end_idx != -1:

    new_modals = """<!-- 1. MODAL PABRIK SURAT OTOMATIS -->
    <div id="modal-pabrik-surat" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Pabrik Surat Otomatis</h3>
                <button onclick="closeModal('modal-pabrik-surat')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <h4 class="text-sm font-bold text-gray-400 mb-3">Daftar Antrean Permohonan</h4>
            <div class="overflow-hidden rounded-xl border border-white/10">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gold/10 text-gold backdrop-blur-md">
                        <tr>
                            <th class="p-4 text-xs font-bold uppercase">Tanggal</th>
                            <th class="p-4 text-xs font-bold uppercase">NPM / Jenis</th>
                            <th class="p-4 text-xs font-bold uppercase text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        {% for item in surat_list %}
                        <tr class="hover:bg-white/5 transition">
                            <td class="p-4 text-sm text-gray-300">{{ item['tanggal'] }}</td>
                            <td class="p-4">
                                <p class="font-bold text-white">{{ item['jenis_surat'] }}</p>
                                <p class="text-xs text-gray-400">NPM: {{ item['npm'] }}</p>
                            </td>
                            <td class="p-4 text-right">
                                {% if item['status'] == 'Menunggu Acc' %}
                                <form action="/tu/surat/acc" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                    <input type="hidden" name="id" value="{{ item['id'] }}">
                                    <button type="submit" class="bg-gold text-midnight px-3 py-1 rounded-lg text-xs font-bold hover:bg-white transition">Setujui</button>
                                </form>
                                {% else %}
                                <span class="text-xs text-green-400 font-bold"><i class="fas fa-check-circle"></i> Selesai</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="3" class="p-4 text-center text-gray-500">Tidak ada antrean</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 2. MODAL VERIFIKASI PMB DIGITAL -->
    <div id="modal-verifikasi-pmb" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Verifikasi PMB Digital</h3>
                <button onclick="closeModal('modal-verifikasi-pmb')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {% for item in pmb_list %}
                <div class="bg-white/5 border border-white/10 p-4 rounded-xl">
                    <p class="font-bold text-white mb-2">{{ item['nama'] }}</p>
                    <div class="flex gap-2 mb-4">
                        {% if item['foto_ijazah'] %}
                        <a href="/uploads/{{ item['foto_ijazah'] }}" target="_blank" class="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Lihat Ijazah</a>
                        {% endif %}
                        {% if item['foto_ktp'] %}
                        <a href="/uploads/{{ item['foto_ktp'] }}" target="_blank" class="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Lihat KTP</a>
                        {% endif %}
                        {% if item['bukti_transfer'] %}
                        <a href="/uploads/{{ item['bukti_transfer'] }}" target="_blank" class="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">Lihat Transfer</a>
                        {% endif %}
                    </div>
                    {% if item['status'] == 'Pending' %}
                    <form action="/tu/pmb/verifikasi" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        <input type="hidden" name="id" value="{{ item['id'] }}">
                        <button type="submit" class="w-full bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">Verifikasi & Buat Akun</button>
                    </form>
                    {% else %}
                    <a href="https://wa.me/?text=Selamat! Anda telah diterima. NPM: {{ item['npm_generated'] }}" target="_blank" class="block w-full text-center bg-green-500 text-white font-bold py-2 rounded-lg hover:bg-green-600 transition"><i class="fab fa-whatsapp"></i> Kirim Akses</a>
                    {% endif %}
                </div>
                {% else %}
                <p class="text-gray-500">Belum ada pendaftar.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 3. MODAL LACI ARSIP ANTI RAYAP -->
    <div id="modal-laci-arsip" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Laci Arsip Anti Rayap</h3>
                <button onclick="closeModal('modal-laci-arsip')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="flex gap-2 mb-6">
                <input type="text" id="arsip-search-npm" placeholder="Ketik NPM Mahasiswa..." class="flex-1 bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold">
                <button onclick="searchArsip()" class="bg-blue-500 text-white px-6 rounded-xl font-bold hover:bg-blue-600 transition"><i class="fas fa-search"></i></button>
            </div>

            <div id="arsip-result" class="text-white">
                <p class="text-gray-500 text-center">Gunakan fitur pencarian di atas.</p>
            </div>

            <script>
                async function searchArsip() {
                    const npm = document.getElementById('arsip-search-npm').value;
                    if(!npm) return;
                    document.getElementById('arsip-result').innerHTML = '<p class="text-center">Mencari...</p>';
                    try {
                        const res = await fetch('/tu/arsip/search?npm=' + npm);
                        const data = await res.json();
                        if(data.error) {
                             document.getElementById('arsip-result').innerHTML = `<p class="text-red-400 text-center">${data.error}</p>`;
                             return;
                        }
                        let html = `
                        <div class="bg-white/5 p-4 rounded-xl border border-white/10 mb-4">
                            <h4 class="font-bold text-gold text-lg">${data.user.nama} (${data.user.username})</h4>
                            <p class="text-sm text-gray-300">Status: ${data.user.status_akademik}</p>
                        </div>
                        <h5 class="font-bold text-gray-400 mb-2">Riwayat Tagihan</h5>
                        <ul class="mb-4 space-y-2">`;
                        data.tagihan.forEach(t => {
                            html += `<li class="bg-white/5 p-2 rounded text-sm flex justify-between"><span>${t.jenis_tagihan}</span> <span class="${t.status=='Lunas' ? 'text-green-400' : 'text-red-400'}">${t.status}</span></li>`;
                        });
                        html += `</ul><h5 class="font-bold text-gray-400 mb-2">Dokumen Digital</h5><ul class="space-y-2">`;
                        data.dokumen.forEach(d => {
                            html += `<li class="bg-white/5 p-2 rounded text-sm flex justify-between"><span>${d.nama_dokumen}</span> <a href="/uploads/${d.file_path}" target="_blank" class="text-blue-400"><i class="fas fa-download"></i> Unduh</a></li>`;
                        });
                        html += `</ul>`;
                        document.getElementById('arsip-result').innerHTML = html;
                    } catch(e) {
                        document.getElementById('arsip-result').innerHTML = '<p class="text-red-500">Error fetching data.</p>';
                    }
                }
            </script>
        </div>
    </div>

    <!-- 4. MODAL VERIFIKASI PEMBAYARAN -->
    <div id="modal-verifikasi-pembayaran" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Verifikasi Pembayaran</h3>
                <button onclick="closeModal('modal-verifikasi-pembayaran')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="space-y-3">
                {% for item in tagihan_list %}
                <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center">
                    <div>
                        <p class="font-bold text-white">{{ item['jenis_tagihan'] }}</p>
                        <p class="text-xs text-gray-400">NPM: {{ item['npm'] }} • Rp {{ item['jumlah'] }}</p>
                        {% if item['bukti_transfer'] %}
                        <a href="/uploads/{{ item['bukti_transfer'] }}" target="_blank" class="text-xs text-blue-400 underline mt-1 block">Lihat Bukti Transfer</a>
                        {% endif %}
                    </div>
                    {% if item['status'] != 'Lunas' %}
                    <form action="/tu/tagihan/lunas" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        <input type="hidden" name="id" value="{{ item['id'] }}">
                        <button type="submit" class="bg-green-500 text-white px-4 py-2 rounded-lg font-bold hover:bg-green-600 transition">Lunas</button>
                    </form>
                    {% else %}
                    <span class="text-green-400 font-bold"><i class="fas fa-check-circle"></i> Lunas</span>
                    {% endif %}
                </div>
                {% else %}
                <p class="text-gray-500 text-center">Tidak ada tagihan tercatat.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 5. MODAL KELOLA JADWAL -->
    <div id="modal-kelola-jadwal" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Kelola Jadwal Perkuliahan</h3>
                <button onclick="closeModal('modal-kelola-jadwal')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <form action="/tu/jadwal" method="POST" class="bg-white/5 p-4 border border-white/10 rounded-xl mb-6 space-y-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                <div class="grid grid-cols-2 gap-3">
                    <input type="text" name="hari" placeholder="Hari (e.g. Senin)" required class="bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                    <input type="text" name="jam" placeholder="Jam (e.g. 08:00 - 10:30)" required class="bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                </div>
                <input type="text" name="mata_kuliah" placeholder="Nama Mata Kuliah" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <input type="text" name="dosen" placeholder="Nama Dosen Pengampu" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <input type="text" name="ruangan" placeholder="Ruangan" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <button type="submit" class="w-full bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">+ Tambah Jadwal</button>
            </form>

            <div class="space-y-3">
                {% for item in jadwal_list %}
                <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center">
                    <div>
                        <p class="font-bold text-white">{{ item['mata_kuliah'] }}</p>
                        <p class="text-xs text-gray-400">{{ item['hari'] }}, {{ item['jam'] }} • Ruang: {{ item['ruangan'] }}</p>
                        <p class="text-xs text-gold">{{ item['dosen'] }}</p>
                    </div>
                </div>
                {% else %}
                <p class="text-gray-500 text-center">Jadwal kosong.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 6. MODAL MANAJEMEN SIVITAS -->
    <div id="modal-manajemen-sivitas" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Manajemen Sivitas Akademika</h3>
                <button onclick="closeModal('modal-manajemen-sivitas')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="overflow-x-auto rounded-xl border border-white/10">
                <table class="w-full text-left border-collapse min-w-[600px]">
                    <thead class="bg-gold/10 text-gold">
                        <tr>
                            <th class="p-3 text-xs font-bold uppercase">User</th>
                            <th class="p-3 text-xs font-bold uppercase">Role</th>
                            <th class="p-3 text-xs font-bold uppercase">Status</th>
                            <th class="p-3 text-xs font-bold uppercase">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        {% for item in akun_list %}
                        <tr class="hover:bg-white/5 transition">
                            <td class="p-3">
                                <p class="font-bold text-white">{{ item['nama'] }}</p>
                                <p class="text-[10px] text-gray-400">{{ item['username'] }}</p>
                            </td>
                            <td class="p-3 text-xs text-gray-300">{{ item['role'] }}</td>
                            <td class="p-3">
                                <span class="px-2 py-1 rounded text-[10px] font-bold {{ 'bg-green-500/20 text-green-400' if item['status_akademik'] == 'Aktif' else 'bg-red-500/20 text-red-400' }}">{{ item['status_akademik'] }}</span>
                            </td>
                            <td class="p-3 text-xs">
                                <form action="/tu/akun/update" method="POST" class="flex gap-2">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                    <input type="hidden" name="id" value="{{ item['id'] }}">
                                    <select name="status_akademik" class="bg-[#0b1026] text-white border border-gold/30 rounded p-1">
                                        <option value="Aktif" {{ 'selected' if item['status_akademik'] == 'Aktif' else '' }}>Aktif</option>
                                        <option value="Cuti" {{ 'selected' if item['status_akademik'] == 'Cuti' else '' }}>Cuti</option>
                                        <option value="Keluar" {{ 'selected' if item['status_akademik'] == 'Keluar' else '' }}>Keluar</option>
                                        <option value="Lulus" {{ 'selected' if item['status_akademik'] == 'Lulus' else '' }}>Lulus</option>
                                    </select>
                                    <button type="submit" class="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">Simpan</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="p-3 text-center text-gray-500">Tidak ada data pengguna</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    """

    new_content = content[:start_idx] + new_modals + "\n" + content[end_idx:]
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("Modals replaced.")
else:
    print("Modal markers not found.")
