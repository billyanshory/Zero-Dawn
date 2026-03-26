import re

with open('kampus-stie-samarinda-4 ( idcloudhost - dashboard home utama - debugging & 6 fitur utama home ).py', 'r') as f:
    content = f.read()

# We need to replace the two blocks of the 6 features with a single united block "Menu Utama".
# Find the start of the first group:
# "<!-- Kelompok 1: Etalase Pendaftaran -->"

start_idx = content.find('<!-- MAIN GRID MENU: 6 FITUR KAMPUS STIESAM -->')
end_idx = content.find('<!-- STATIC PWA INSTALL BUTTON (NEW) -->')

original_block = content[start_idx:end_idx]
print(len(original_block))

# I will replace the block from "<!-- Kelompok 1: Etalase Pendaftaran -->" to just before "<!-- STATIC PWA INSTALL BUTTON (NEW) -->"

new_block = """<!-- MAIN GRID MENU: 6 FITUR KAMPUS STIESAM -->

    <!-- Menu Utama -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-sky-500 leading-none py-1 ml-1 md:text-2xl md:mb-6">&nbsp;Menu Utama</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
        <a href="javascript:void(0)" onclick="openModal('modal-profil-kampus')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-indigo-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-indigo-600 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                <i class="fas fa-university text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-indigo-600 leading-tight">Profil & Program Studi</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-pmb')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-sky-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-sky-600 group-hover:bg-sky-500 group-hover:text-white transition-colors">
                <i class="fas fa-user-graduate text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-sky-600 leading-tight">Pendaftaran Digital</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-cek-status')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-emerald-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                <i class="fas fa-search text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-emerald-600 leading-tight">Status Kelulusan</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-agenda-berita')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-orange-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-orange-600 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                <i class="fas fa-newspaper text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-orange-600 leading-tight">Berita & Agenda</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-jurnal-karya')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-purple-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-purple-600 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-book-open text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-purple-600 leading-tight">Galeri Jurnal Ilmiah</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-tracer-study')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-teal-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-teal-600 group-hover:bg-teal-500 group-hover:text-white transition-colors">
                <i class="fas fa-chart-line text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-teal-600 leading-tight">Pelacak Karir Alumni</span>
        </a>
    </div>

    <!-- Kelompok Terapi Kesehatan & Epilepsi -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-blue-500 leading-none py-1 ml-1 md:text-2xl md:mb-6">&nbsp;Terapi Bantuan Kesehatan dan Epilepsi</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
        <a href="javascript:void(0)" onclick="openModal('modal-terapi-audio')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-blue-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-blue-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-blue-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="fas fa-music text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-blue-600 leading-tight">Terapi Suara</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-terapi-napas')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-blue-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-blue-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-cyan-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-cyan-600 group-hover:bg-cyan-500 group-hover:text-white transition-colors">
                <i class="fas fa-lungs text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-cyan-600 leading-tight">Latihan Napas</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-terapi-tidur')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-blue-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-blue-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-indigo-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-indigo-600 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                <i class="fas fa-bed text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-indigo-600 leading-tight">Pelacak Tidur</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-terapi-log')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-blue-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-blue-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-rose-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-rose-600 group-hover:bg-rose-500 group-hover:text-white transition-colors">
                <i class="fas fa-file-medical text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-rose-600 leading-tight">Jurnal Kambuh</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-terapi-alarm')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-blue-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-blue-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-amber-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-amber-600 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                <i class="fas fa-capsules text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-amber-600 leading-tight">Alarm Obat</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-terapi-diet')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-blue-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-blue-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-lime-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-lime-600 group-hover:bg-lime-500 group-hover:text-white transition-colors">
                <i class="fas fa-apple-alt text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-lime-600 leading-tight">Diet Keton</span>
        </a>
    </div>

    <!-- Kelompok Kalkulator Islam -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-emerald-500 leading-none py-1 ml-1 md:text-2xl md:mb-6">&nbsp;Kalkulator Islam</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
        <a href="javascript:void(0)" onclick="openModal('modal-waris')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-emerald-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-emerald-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-sky-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-sky-600 group-hover:bg-sky-500 group-hover:text-white transition-colors">
                <i class="fas fa-users text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-sky-600 leading-tight">Perhitungan Waris</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-zakat')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-emerald-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-emerald-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-blue-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="fas fa-hand-holding-usd text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-blue-600 leading-tight">Zakat Maal</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-tahajjud')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-emerald-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-emerald-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-indigo-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-indigo-600 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                <i class="fas fa-moon text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-indigo-600 leading-tight">Pengingat Tahajjud</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-khatam')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-emerald-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-emerald-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-teal-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-teal-600 group-hover:bg-teal-500 group-hover:text-white transition-colors">
                <i class="fas fa-quran text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-teal-600 leading-tight">Target Khatam</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-fidyah')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-emerald-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-emerald-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-orange-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-orange-600 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                <i class="fas fa-utensils text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-orange-600 leading-tight">Fidyah</span>
        </a>
        <a href="javascript:void(0)" onclick="openModal('modal-hijri')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-emerald-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-emerald-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-emerald-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                <i class="fas fa-calendar-alt text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-emerald-600 leading-tight">Konverter Kalender Hijriah</span>
        </a>
    </div>

    """

content = content.replace(original_block, new_block)

with open('kampus-stie-samarinda-4 ( idcloudhost - dashboard home utama - debugging & 6 fitur utama home ).py', 'w') as f:
    f.write(content)
