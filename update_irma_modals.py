import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

# Replace MODAL DUTY with MODAL RENCANA STUDI
duty_regex = r"<!-- 1\. MODAL DUTY -->.*?</div>\s*</div>\s*</div>"
new_krs_modal = """<!-- 1. MODAL RENCANA STUDI -->
    <div id="modal-rencana-studi" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Pengisian Rencana Studi (KRS)</h3>
                <button onclick="closeModal('modal-rencana-studi')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#A0B391]/20">
                <p class="text-sm text-gray-600 mb-4">Pengisian KRS digital tanpa kertas. Silakan pilih mata kuliah yang ditawarkan untuk semester ini.</p>
                <div class="space-y-3 mb-4">
                    <label class="flex items-center p-3 border border-gray-100 rounded-xl hover:bg-gray-50 transition cursor-pointer">
                        <input type="checkbox" class="accent-[#A0B391] w-4 h-4 mr-3" checked>
                        <div class="flex-1">
                            <p class="font-bold text-sm text-gray-800">Manajemen Keuangan Lanjutan</p>
                            <p class="text-xs text-gray-500">MKK-301 • 3 SKS • Dosen: Dr. Budi Santoso</p>
                        </div>
                    </label>
                    <label class="flex items-center p-3 border border-gray-100 rounded-xl hover:bg-gray-50 transition cursor-pointer">
                        <input type="checkbox" class="accent-[#A0B391] w-4 h-4 mr-3" checked>
                        <div class="flex-1">
                            <p class="font-bold text-sm text-gray-800">Akuntansi Biaya</p>
                            <p class="text-xs text-gray-500">MKB-302 • 3 SKS • Dosen: Sri Rahayu, S.E., M.Ak.</p>
                        </div>
                    </label>
                </div>
                <button onclick="alert('KRS berhasil diajukan ke Dosen Pembimbing Akademik untuk disetujui.'); closeModal('modal-rencana-studi');" class="w-full bg-[#A0B391] text-white font-bold py-3 rounded-xl hover:bg-[#FFB6C1] transition">Ajukan KRS</button>
            </div>
        </div>
    </div>"""
content = re.sub(duty_regex, new_krs_modal, content, flags=re.DOTALL)

# Replace MODAL JOIN with MODAL KARTU HASIL STUDI
join_regex = r"<!-- 2\. MODAL JOIN -->.*?</div>\s*</div>\s*</div>"
new_khs_modal = """<!-- 2. MODAL KARTU HASIL STUDI -->
    <div id="modal-kartu-hasil-studi" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Kartu Hasil Studi (KHS)</h3>
                <button onclick="closeModal('modal-kartu-hasil-studi')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#A0B391]/20">
                <div class="flex justify-between items-end mb-6 border-b border-gray-100 pb-4">
                    <div>
                        <h4 class="text-lg font-bold text-gray-800">Semester Ganjil 2024/2025</h4>
                        <p class="text-xs text-gray-500">IPK Sementara: 3.85</p>
                    </div>
                    <button class="text-xs font-bold text-[#A0B391] bg-[#A0B391]/10 px-3 py-1.5 rounded-lg"><i class="fas fa-download mr-1"></i> PDF</button>
                </div>
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="p-3 text-xs font-bold text-gray-600 rounded-l-lg">Mata Kuliah</th>
                            <th class="p-3 text-xs font-bold text-gray-600 text-center">SKS</th>
                            <th class="p-3 text-xs font-bold text-gray-600 text-center rounded-r-lg">Nilai</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        <tr>
                            <td class="p-3 text-sm text-gray-800 font-medium">Manajemen Pemasaran</td>
                            <td class="p-3 text-sm text-gray-600 text-center">3</td>
                            <td class="p-3 text-sm font-bold text-[#A0B391] text-center">A</td>
                        </tr>
                        <tr>
                            <td class="p-3 text-sm text-gray-800 font-medium">Statistika Bisnis</td>
                            <td class="p-3 text-sm text-gray-600 text-center">3</td>
                            <td class="p-3 text-sm font-bold text-[#A0B391] text-center">A-</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>"""
content = re.sub(join_regex, new_khs_modal, content, flags=re.DOTALL)

# Replace MODAL FINANCE with MODAL PUSAT TAGIHAN
finance_regex = r"<!-- 3\. MODAL FINANCE -->.*?</div>\s*</div>\s*</div>"
new_tagihan_modal = """<!-- 3. MODAL PUSAT TAGIHAN -->
    <div id="modal-pusat-tagihan" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Pusat Tagihan & Pembayaran</h3>
                <button onclick="closeModal('modal-pusat-tagihan')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>

            <div class="bg-gradient-to-r from-red-400 to-orange-400 text-white p-6 rounded-3xl shadow-lg mb-6 relative overflow-hidden">
                <div class="absolute right-0 top-0 p-4 opacity-20"><i class="fas fa-file-invoice-dollar text-6xl"></i></div>
                <p class="text-xs opacity-90 mb-1">Total Tagihan Belum Dibayar</p>
                <h2 class="text-3xl font-bold font-mono">Rp 3,500,000</h2>
                <p class="text-xs font-bold mt-2 bg-white/20 inline-block px-3 py-1 rounded-full"><i class="fas fa-exclamation-circle mr-1"></i> SPP Semester Ganjil</p>
            </div>

            <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#A0B391]/20">
                <h4 class="text-sm font-bold text-gray-800 mb-4 border-b border-gray-100 pb-2">Upload Bukti Transfer</h4>
                <form onsubmit="event.preventDefault(); alert('Bukti transfer berhasil diunggah! Lonceng notifikasi di dasbor Tata Usaha telah berbunyi untuk diverifikasi.'); closeModal('modal-pusat-tagihan');" class="space-y-4">
                    <select class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#A0B391]" required>
                        <option value="">Pilih Jenis Pembayaran...</option>
                        <option value="spp">SPP Tetap / Variabel</option>
                        <option value="sks">SKS Semester</option>
                        <option value="ujian">Ujian (UTS/UAS/Skripsi)</option>
                    </select>
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-500 flex items-center justify-center shrink-0"><i class="fas fa-cloud-upload-alt text-xl"></i></div>
                        <input type="file" accept="image/*,.pdf" class="text-xs w-full file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" required>
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl mt-2 hover:bg-blue-600 transition shadow-lg shadow-blue-500/30">Kirim Bukti Pembayaran</button>
                </form>
            </div>
        </div>
    </div>"""
content = re.sub(finance_regex, new_tagihan_modal, content, flags=re.DOTALL)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
