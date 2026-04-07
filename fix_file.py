import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

# Fix Zikir Button etc
content = re.sub(r'<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Zikir Penenang \(EQuran\)</h3>.*?</svg>\n            </div>',
r'''<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Zikir Penenang (EQuran)</h3>
            <button onclick="toggleAudio('zikir')" id="btn-zikir"
                    onmouseenter="startDwell('zikir')" onmouseleave="stopDwell('zikir')" onmousedown="startDwell('zikir')" onmouseup="stopDwell('zikir')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-quran pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-zikir">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
            </div>''', content, flags=re.DOTALL)

content = re.sub(r'<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Pink Noise \(Sensorik\)</h3>.*?</svg>\n        </div>',
r'''<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Pink Noise (Sensorik)</h3>
            <button onclick="toggleAudio('pink')" id="btn-pink"
                    onmouseenter="startDwell('pink')" onmouseleave="stopDwell('pink')" onmousedown="startDwell('pink')" onmouseup="stopDwell('pink')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-water pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-pink">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
        </div>''', content, flags=re.DOTALL)

content = re.sub(r'<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Relaksasi Delta \(Tidur\)</h3>.*?</div>',
r'''<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Relaksasi Delta (Tidur)</h3>
            <button onclick="toggleAudio('delta')" id="btn-delta"
                    onmouseenter="startDwell('delta')" onmouseleave="stopDwell('delta')" onmousedown="startDwell('delta')" onmouseup="stopDwell('delta')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-play pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-delta">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
        </div>''', content, flags=re.DOTALL)

content = re.sub(r'<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Fokus Theta \(Tenang\)</h3>.*?</div>',
r'''<h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Fokus Theta (Tenang)</h3>
            <button onclick="toggleAudio('theta')" id="btn-theta"
                    onmouseenter="startDwell('theta')" onmouseleave="stopDwell('theta')" onmousedown="startDwell('theta')" onmouseup="stopDwell('theta')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-play pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-theta">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
        </div>''', content, flags=re.DOTALL)

# Fix Form Jurnal Kambuh
content = re.sub(r'<form action="/therapy/log".*?{% endfor %}\n            </div>',
r'''{% if peran == 'guru' or peran == 'kepala_sekolah' %}
            <div id="guru-kambuh-monitor">
                <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-blue-500">Monitor Jurnal Kambuh Siswa</h4>
                <div class="flex gap-2 mb-4">
                    <input type="text" id="guru-kambuh-search" placeholder="Cari..." class="flex-1 border border-blue-100 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-blue-50/50">
                    <button onclick="fetchGuruKambuh()" class="bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-blue-600 transition">Muat Data</button>
                </div>
                <div id="guru-kambuh-results" class="space-y-3 overflow-y-auto max-h-64"></div>
            </div>
            <script>
            function fetchGuruKambuh(page=1) {
                fetch('/api/jurnal-kambuh/guru-view?page=' + page)
                    .then(res => res.json())
                    .then(data => {
                        const container = document.getElementById('guru-kambuh-results');
                        if(page === 1) container.innerHTML = '';
                        if(data.items.length === 0 && page === 1) {
                            container.innerHTML = '<p class="text-center text-gray-500 text-xs py-4">Belum ada data rekaman.</p>';
                            return;
                        }

                        // remove old button
                        const oldBtn = document.getElementById('btn-more-kambuh');
                        if (oldBtn) oldBtn.remove();

                        data.items.forEach(log => {
                            container.innerHTML += `
                            <div class="bg-white p-4 rounded-2xl shadow-sm border border-blue-100 flex justify-between items-start">
                                <div>
                                    <h4 class="font-bold text-blue-800 text-sm mb-1">${log.siswa_nama}</h4>
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">${log.date}</span>
                                        <span class="text-xs text-gray-500">${log.time}</span>
                                    </div>
                                    <p class="text-sm font-bold text-gray-800">${log.trigger}</p>
                                    ${log.notes ? `<p class="text-xs text-gray-500 mt-1 italic">"${log.notes}"</p>` : ''}
                                </div>
                            </div>`;
                        });
                        if (data.has_next) {
                            container.innerHTML += `<button id="btn-more-kambuh" onclick="fetchGuruKambuh(${data.page + 1})" class="w-full text-xs font-bold text-blue-500 py-2 hover:bg-blue-50 rounded-xl transition mt-2">Muat Lebih Banyak</button>`;
                        }
                    });
            }
            document.addEventListener('DOMContentLoaded', () => fetchGuruKambuh(1));
            </script>
            {% else %}
            <form action="/therapy/log" method="POST" class="space-y-4 mb-8 bg-blue-50 p-4 rounded-2xl border border-blue-100">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Tanggal</label>
                        <input type="date" name="date" class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Jam</label>
                        <input type="time" name="time" class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm" required>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Pemicu</label>
                    <select name="trigger" class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm">
                        <option value="Stres">Stres / Cemas</option>
                        <option value="Kurang Tidur">Kurang Tidur</option>
                        <option value="Lupa Obat">Lupa Minum Obat</option>
                        <option value="Silau">Cahaya Silau / Berkedip</option>
                        <option value="Kelelahan">Kelelahan Fisik</option>
                        <option value="Lainnya">Lainnya</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Catatan Tambahan</label>
                    <input type="text" name="notes" placeholder="Durasi, kondisi setelahnya..." class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm">
                </div>
                <button type="submit" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-600 transition">Simpan Laporan</button>
            </form>

            <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-blue-500">Riwayat Terakhir</h4>
            <div class="space-y-3">
                {% for log in epilepsi_logs %}
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex justify-between items-start">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">{{ log['date'] }}</span>
                            <span class="text-xs text-gray-500">{{ log['time'] }}</span>
                        </div>
                        <p class="text-sm font-bold text-gray-800">{{ log['trigger'] }}</p>
                        {% if log['notes'] %}<p class="text-xs text-gray-500 mt-1 italic">"{{ log['notes'] }}"</p>{% endif %}
                    </div>
                </div>
                {% else %}
                <p class="text-center text-gray-500 text-xs py-4">Belum ada data rekaman.</p>
                {% endfor %}
            </div>
            {% endif %}''', content, flags=re.DOTALL)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
