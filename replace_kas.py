import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

# Replace <a href="/finance" ... Laporan Kas</a> with PMB modal button
finance_regex = r"<a href=\"/finance\" class=\"bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300\">\s*<div class=\"bg-emerald-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors\">\s*<i class=\"fas fa-wallet text-2xl md:text-3xl\"></i>\s*</div>\s*<span class=\"text-sm md:text-base font-semibold text-gray-700 group-hover:text-emerald-600\">Laporan Kas</span>\s*</a>"

new_pmb_button = """<a href="javascript:void(0)" onclick="openModal('modal-pmb')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-emerald-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                <i class="fas fa-user-graduate text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-emerald-600 leading-tight">Penerimaan Mahasiswa Baru</span>
        </a>"""

content = re.sub(finance_regex, new_pmb_button, content, flags=re.DOTALL)

# Add PMB Modal at the end of HOME_HTML
pmb_modal = """
    <!-- MODAL PENERIMAAN MAHASISWA BARU (PMB) -->
    <div id="modal-pmb" class="fixed inset-0 z-[150] hidden flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <div class="bg-white rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-[slideUp_0.3s_ease-out]">
            <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-emerald-50">
                <h3 class="text-xl font-bold text-emerald-800"><i class="fas fa-user-graduate mr-2 text-emerald-600"></i>Pendaftaran Mahasiswa Baru</h3>
                <button onclick="closeModal('modal-pmb')" class="w-8 h-8 rounded-full bg-white text-gray-500 hover:text-red-500 flex items-center justify-center shadow-sm">&times;</button>
            </div>

            <div class="p-6 overflow-y-auto">
                <p class="text-sm text-gray-600 mb-6">Silakan unggah berkas pendaftaran Anda. Staf tata usaha akan memverifikasi dan mengirimkan Nomor Pokok Mahasiswa (NPM) Anda melalui pesan WhatsApp otomatis.</p>

                <form onsubmit="event.preventDefault(); alert('Berkas berhasil diunggah! Staf kami sedang memverifikasi data Anda. Harap tunggu pesan WA konfirmasi berisi NPM Anda.'); closeModal('modal-pmb');" class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nama Lengkap Sesuai Ijazah</label>
                        <input type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nomor WhatsApp Aktif (08xx...)</label>
                        <input type="number" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Program Studi Pilihan</label>
                        <select class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                            <option value="">Pilih Program Studi...</option>
                            <option value="S1 Manajemen">S1 Manajemen</option>
                            <option value="S1 Akuntansi">S1 Akuntansi</option>
                            <option value="S2 Magister Manajemen">S2 Magister Manajemen</option>
                        </select>
                    </div>

                    <div class="pt-2">
                        <label class="block text-xs font-bold text-gray-500 mb-2">Unggah Dokumen Persyaratan</label>
                        <div class="space-y-3">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center shrink-0"><i class="fas fa-id-card"></i></div>
                                <input type="file" accept="image/*,.pdf" class="text-xs w-full file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100" required>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-lg bg-orange-50 text-orange-500 flex items-center justify-center shrink-0"><i class="fas fa-file-alt"></i></div>
                                <input type="file" accept="image/*,.pdf" class="text-xs w-full file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100" required>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-lg bg-green-50 text-green-500 flex items-center justify-center shrink-0"><i class="fas fa-receipt"></i></div>
                                <input type="file" accept="image/*,.pdf" class="text-xs w-full file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100" required>
                            </div>
                        </div>
                    </div>

                    <button type="submit" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl mt-6 hover:bg-emerald-600 transition shadow-lg">Kirim Berkas Pendaftaran</button>
                </form>
            </div>
        </div>
    </div>
"""

# Insert the modal right before the closing </div> of HOME_HTML
last_div_index = content.rfind("</div>", 0, content.find("HOME_HTML ="))
if last_div_index == -1: # It means it's finding within the string
    end_index = content.find('"""', content.find('HOME_HTML = ') + 15)
    content = content[:end_index] + pmb_modal + content[end_index:]

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
