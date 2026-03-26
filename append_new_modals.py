import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

# Replace MODAL TAKJIL and MODAL IMSAKIYAH with the new modals
new_modals = """<!-- 1. MODAL PABRIK SURAT OTOMATIS -->
    <div id="modal-pabrik-surat" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Pabrik Surat Otomatis</h3>
                <button onclick="closeModal('modal-pabrik-surat')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="p-4 bg-white/5 border border-gold/30 rounded-xl mb-4">
                <p class="text-gray-300 text-sm mb-4">Silakan buat draf dokumen elektronik. Staf TU akan menyetujui dan membubuhkan tanda tangan elektronik (QR Code pelacak keaslian).</p>
                <form onsubmit="event.preventDefault(); alert('Draf surat berhasil dibuat dan dikirim ke Tata Usaha untuk persetujuan.'); closeModal('modal-pabrik-surat');" class="space-y-4">
                    <select class="w-full bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold" required>
                        <option value="">Pilih Jenis Surat...</option>
                        <option value="aktif_kuliah">Surat Keterangan Aktif Kuliah</option>
                        <option value="pengantar_magang">Surat Pengantar Magang</option>
                        <option value="bebas_pustaka">Surat Keterangan Bebas Pustaka</option>
                    </select>
                    <input type="text" placeholder="NPM Mahasiswa" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold" required>
                    <textarea placeholder="Keterangan / Tujuan Surat" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold" required></textarea>
                    <button type="submit" class="w-full bg-gold text-[#0b1026] font-bold py-3 rounded-xl hover:bg-white transition">Buat Draf Surat</button>
                </form>
            </div>

            <h4 class="text-sm font-bold text-gray-400 mb-3 mt-8">Riwayat Pengajuan Surat</h4>
            <div class="overflow-hidden rounded-xl border border-white/10">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gold/10 text-gold backdrop-blur-md">
                        <tr>
                            <th class="p-4 text-xs font-bold uppercase">Tanggal</th>
                            <th class="p-4 text-xs font-bold uppercase">Jenis Surat</th>
                            <th class="p-4 text-xs font-bold uppercase text-right">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        <tr class="hover:bg-white/5 transition">
                            <td class="p-4 text-sm text-gray-300">Hari ini</td>
                            <td class="p-4 font-bold text-white">Surat Pengantar Magang</td>
                            <td class="p-4 text-sm text-yellow-400 text-right">Menunggu Acc</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 2. MODAL LACI ARSIP DIGITAL -->
    <div id="modal-arsip-digital" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Laci Arsip Digital</h3>
                <button onclick="closeModal('modal-arsip-digital')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="p-4 bg-white/5 border border-white/10 rounded-xl mb-6">
                <p class="text-gray-400 text-sm mb-3">Pangkalan Data Awan STIESAM. Cari riwayat hidup, nilai, ijazah, dan pembayaran.</p>
                <div class="flex gap-2">
                    <input type="text" placeholder="Ketik NPM / Nama Mahasiswa..." class="flex-1 bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold">
                    <button onclick="alert('Mencari arsip dari pangkalan data awan...');" class="bg-blue-500 text-white px-6 rounded-xl font-bold hover:bg-blue-600 transition"><i class="fas fa-search"></i></button>
                </div>
            </div>

            <div class="grid grid-cols-1 gap-4">
                <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center hover:border-blue-400 transition cursor-pointer" onclick="alert('Mengunduh dokumen Ijazah...')">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 bg-blue-500/20 text-blue-400 rounded-lg flex items-center justify-center">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <div>
                            <p class="font-bold text-white">Ijazah_SMA_192831.pdf</p>
                            <p class="text-[10px] text-gray-500">1.2 MB • Diunggah 12 Jan 2024</p>
                        </div>
                    </div>
                    <i class="fas fa-download text-gray-400 hover:text-gold"></i>
                </div>
                <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center hover:border-blue-400 transition cursor-pointer" onclick="alert('Mengunduh KHS...')">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 bg-green-500/20 text-green-400 rounded-lg flex items-center justify-center">
                            <i class="fas fa-file-excel"></i>
                        </div>
                        <div>
                            <p class="font-bold text-white">KHS_Semester_3_192831.pdf</p>
                            <p class="text-[10px] text-gray-500">800 KB • Diunggah 05 Feb 2025</p>
                        </div>
                    </div>
                    <i class="fas fa-download text-gray-400 hover:text-gold"></i>
                </div>
            </div>
        </div>
    </div>"""

takjil_regex = r"<!-- 1\. MODAL TAKJIL -->.*?</div>\s*</div>\s*</div>"
imsakiyah_regex = r"<!-- 2\. MODAL IMSAKIYAH -->.*?</div>\s*</div>\s*</div>"
kas_ramadhan_regex = r"<!-- 3\. MODAL KAS RAMADHAN -->.*?</div>\s*</div>\s*</div>"

content = re.sub(takjil_regex, new_modals, content, flags=re.DOTALL)
content = re.sub(imsakiyah_regex, "", content, flags=re.DOTALL)
content = re.sub(kas_ramadhan_regex, "", content, flags=re.DOTALL)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
