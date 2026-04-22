filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

# We'll insert it right after IDUL_ADHA_DASHBOARD_HTML definition ends, before HOME_HTML
html_content = """

IDUL_ADHA_LAPORAN_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20">
    <!-- Header -->
    <div class="bg-[#1B4332] text-white py-8 px-5 md:px-8 shadow-xl relative overflow-hidden">
        <div class="absolute right-0 top-0 opacity-10 transform translate-x-4 -translate-y-4">
            <i class="fas fa-chart-line text-[120px] text-[#D4A017]"></i>
        </div>
        <div class="max-w-4xl mx-auto relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <a href="/idul-adha" class="inline-flex items-center gap-2 text-white/80 hover:text-white mb-4 text-sm font-bold bg-white/10 px-4 py-2 rounded-full w-max backdrop-blur-sm transition-colors border border-white/20">
                    <i class="fas fa-arrow-left"></i> Kembali ke Dashboard
                </a>
                <h1 class="text-3xl md:text-4xl font-bold mb-2 tracking-tight text-[#D4A017]">Laporan Transparansi Qurban</h1>
                <p class="text-[#F5F0E8]/80 text-sm md:text-base max-w-xl">
                    Pantau progres pemotongan dan distribusi daging qurban di Masjid Al-Hijrah secara real-time. Transparansi demi kemaslahatan umat.
                </p>
            </div>

            <div class="bg-[#8B2635] p-3 rounded-xl border border-[#8B2635]/50 shadow-lg text-center w-max mt-4 md:mt-0 self-start md:self-center">
                <p class="text-[10px] uppercase font-bold text-white/70 mb-1 tracking-wider">Status Pembaruan</p>
                <div class="flex items-center gap-2">
                    <span class="relative flex h-3 w-3">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                    </span>
                    <span class="font-mono font-bold text-white text-sm" id="last-updated">LIVE</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-4xl mx-auto px-5 md:px-8 mt-[-2rem] relative z-20">

        <!-- Error/Loading State -->
        <div id="loading-state" class="bg-white rounded-2xl shadow-xl p-10 text-center border border-gray-100 mb-8">
            <i class="fas fa-circle-notch fa-spin text-4xl text-[#D4A017] mb-4"></i>
            <h3 class="text-lg font-bold text-[#1B4332]">Mengambil data terbaru...</h3>
            <p class="text-sm text-gray-500">Mohon tunggu sebentar.</p>
        </div>

        <div id="error-state" class="hidden bg-[#8B2635]/10 rounded-2xl shadow-xl p-8 text-center border border-[#8B2635]/30 mb-8">
            <i class="fas fa-exclamation-triangle text-4xl text-[#8B2635] mb-4"></i>
            <h3 class="text-lg font-bold text-[#8B2635]">Gagal Memuat Data</h3>
            <p class="text-sm text-[#8B2635]/80">Terjadi kesalahan saat menghubungi server. Mencoba kembali...</p>
        </div>

        <!-- Dashboard Grid (Hidden initially) -->
        <div id="dashboard-grid" class="hidden">
            <!-- Top Stats: Animals -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-6">

                <!-- Sapi -->
                <div class="bg-white rounded-3xl p-6 shadow-xl border border-gray-100 flex items-center justify-between group hover:-translate-y-1 transition-transform">
                    <div>
                        <p class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Total Sapi</p>
                        <h2 class="text-4xl font-bold text-[#1B4332] font-mono" id="val-sapi">0</h2>
                    </div>
                    <div class="w-16 h-16 rounded-2xl bg-[#1B4332]/10 text-[#1B4332] flex items-center justify-center text-3xl group-hover:bg-[#1B4332] group-hover:text-white transition-colors">
                        <i class="fas fa-cow"></i>
                    </div>
                </div>

                <!-- Kambing -->
                <div class="bg-white rounded-3xl p-6 shadow-xl border border-gray-100 flex items-center justify-between group hover:-translate-y-1 transition-transform">
                    <div>
                        <p class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Total Kambing</p>
                        <h2 class="text-4xl font-bold text-[#1B4332] font-mono" id="val-kambing">0</h2>
                    </div>
                    <div class="w-16 h-16 rounded-2xl bg-[#1B4332]/10 text-[#1B4332] flex items-center justify-center text-3xl group-hover:bg-[#1B4332] group-hover:text-white transition-colors">
                        <i class="fas fa-sheep"></i>
                    </div>
                </div>
            </div>

            <!-- Main Metric: Meat & Packages -->
            <div class="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-gray-100 mb-6">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <!-- Meat Est -->
                    <div class="text-center md:text-left border-b md:border-b-0 md:border-r border-gray-100 pb-6 md:pb-0 md:pr-6">
                        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#D4A017]/10 text-[#D4A017] mb-4">
                            <i class="fas fa-weight-hanging text-xl"></i>
                        </div>
                        <p class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Estimasi Daging</p>
                        <div class="flex items-baseline justify-center md:justify-start gap-1">
                            <h2 class="text-4xl font-bold text-[#8B2635] font-mono" id="val-meat">0.0</h2>
                            <span class="text-gray-500 font-bold">Kg</span>
                        </div>
                    </div>

                    <!-- Packages -->
                    <div class="text-center border-b md:border-b-0 md:border-r border-gray-100 pb-6 md:pb-0 md:px-6">
                        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#D4A017]/10 text-[#D4A017] mb-4">
                            <i class="fas fa-box-open text-xl"></i>
                        </div>
                        <p class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Total Paket</p>
                        <div class="flex items-baseline justify-center gap-1">
                            <h2 class="text-4xl font-bold text-[#D4A017] font-mono" id="val-packages-prepared">0</h2>
                            <span class="text-gray-500 font-bold">Bungkus</span>
                        </div>
                    </div>

                    <!-- Distributed -->
                    <div class="text-center md:text-right md:pl-6">
                        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#1B4332]/10 text-[#1B4332] mb-4">
                            <i class="fas fa-hands-helping text-xl"></i>
                        </div>
                        <p class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Telah Dibagikan</p>
                        <div class="flex items-baseline justify-center md:justify-end gap-1">
                            <h2 class="text-4xl font-bold text-[#1B4332] font-mono" id="val-packages-distributed">0</h2>
                            <span class="text-gray-500 font-bold">Bungkus</span>
                        </div>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="mt-8">
                    <div class="flex justify-between text-xs font-bold mb-2">
                        <span class="text-[#8B2635] uppercase tracking-wider">Progres Distribusi</span>
                        <span class="text-[#8B2635] font-mono" id="val-progress-pct">0%</span>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-4 overflow-hidden border border-gray-200">
                        <div id="progress-bar" class="bg-gradient-to-r from-[#D4A017] to-[#8B2635] h-full rounded-full transition-all duration-1000 ease-out" style="width: 0%"></div>
                    </div>
                </div>
            </div>

            <p class="text-center text-xs text-gray-500 font-medium">
                Pembaruan otomatis setiap 30 detik. <br class="md:hidden">
                Terakhir disinkronisasi: <span id="sync-time" class="font-mono">--:--:--</span>
            </p>
        </div>

        <!-- ADMIN FORM (Only visible to admin) -->
        {% if is_admin %}
        <div class="mt-12 bg-white rounded-3xl p-6 md:p-8 shadow-xl border-2 border-[#1B4332]/20">
            <div class="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
                <div class="w-10 h-10 rounded-full bg-[#1B4332] text-white flex items-center justify-center">
                    <i class="fas fa-lock"></i>
                </div>
                <div>
                    <h3 class="text-lg font-bold text-[#1B4332]">Panel Admin Panitia</h3>
                    <p class="text-xs text-gray-500 uppercase tracking-widest">Update Data Transparansi</p>
                </div>
            </div>

            <form action="/admin/qurban/stats" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Total Sapi</label>
                        <input type="number" name="total_cattle" id="input-cattle" value="0" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Total Kambing</label>
                        <input type="number" name="total_goat" id="input-goat" value="0" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Estimasi Daging (Kg)</label>
                        <input type="number" step="0.1" name="total_meat_weight_kg" id="input-meat" value="0" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Total Paket Dibuat</label>
                        <input type="number" name="total_packages_prepared" id="input-packages-prep" value="0" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Paket Didistribusikan</label>
                        <input type="number" name="total_packages_distributed" id="input-packages-dist" value="0" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    </div>
                </div>

                <button type="submit" class="w-full bg-[#1B4332] text-white font-bold py-4 mt-2 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">
                    <i class="fas fa-save"></i> Simpan Data Real-time
                </button>
            </form>
        </div>
        {% endif %}
    </div>
</div>

<script>
    async function fetchStats() {
        try {
            const res = await fetch('/api/qurban/stats');
            if(!res.ok) throw new Error('Network response was not ok');
            const data = await res.json();

            // Hide loading/error, show grid
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('error-state').classList.add('hidden');
            document.getElementById('dashboard-grid').classList.remove('hidden');

            // Update stats
            document.getElementById('val-sapi').innerText = data.total_cattle;
            document.getElementById('val-kambing').innerText = data.total_goat;
            document.getElementById('val-meat').innerText = parseFloat(data.total_meat_weight_kg).toLocaleString('id-ID');
            document.getElementById('val-packages-prepared').innerText = data.total_packages_prepared.toLocaleString('id-ID');
            document.getElementById('val-packages-distributed').innerText = data.total_packages_distributed.toLocaleString('id-ID');

            // Update admin inputs if they exist
            const inCattle = document.getElementById('input-cattle');
            if(inCattle && document.activeElement !== inCattle) inCattle.value = data.total_cattle;

            const inGoat = document.getElementById('input-goat');
            if(inGoat && document.activeElement !== inGoat) inGoat.value = data.total_goat;

            const inMeat = document.getElementById('input-meat');
            if(inMeat && document.activeElement !== inMeat) inMeat.value = data.total_meat_weight_kg;

            const inPrep = document.getElementById('input-packages-prep');
            if(inPrep && document.activeElement !== inPrep) inPrep.value = data.total_packages_prepared;

            const inDist = document.getElementById('input-packages-dist');
            if(inDist && document.activeElement !== inDist) inDist.value = data.total_packages_distributed;

            // Progress Bar Logic
            let pct = 0;
            if (data.total_packages_prepared > 0) {
                pct = Math.round((data.total_packages_distributed / data.total_packages_prepared) * 100);
            }
            if (pct > 100) pct = 100;

            document.getElementById('progress-bar').style.width = pct + '%';
            document.getElementById('val-progress-pct').innerText = pct + '%';

            // Sync time
            const now = new Date();
            document.getElementById('sync-time').innerText = now.toLocaleTimeString('id-ID', {hour12: false});

        } catch(e) {
            console.error('Fetch error:', e);
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('dashboard-grid').classList.add('hidden');
            document.getElementById('error-state').classList.remove('hidden');
        }
    }

    // Initial fetch
    fetchStats();

    // Auto refresh every 30 seconds
    setInterval(fetchStats, 30000);
</script>
'''

"""

# Insert string into python file
insert_target = 'HOME_HTML = """'
if insert_target in content:
    content = content.replace(insert_target, html_content + insert_target)
    with open(filename, "w") as f:
        f.write(content)
    print("Injected UI variables")
else:
    print("Could not inject")
