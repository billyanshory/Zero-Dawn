import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

# Replace JADWAL PIKET with RENCANA STUDI
piket_regex = r"<!-- 1\. JADWAL PIKET -->.*?Jadwal Piket</span>\s*</button>"
new_krs = """<!-- 1. RENCANA STUDI -->
        <button onclick="openModal('modal-rencana-studi')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-file-signature text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Rencana Studi</span>
        </button>"""
content = re.sub(piket_regex, new_krs, content, flags=re.DOTALL)

# Replace JOIN IRMA with KARTU HASIL STUDI
join_regex = r"<!-- 2\. JOIN IRMA -->.*?Join IRMA</span>\s*</button>"
new_khs = """<!-- 2. KARTU HASIL STUDI -->
        <button onclick="openModal('modal-kartu-hasil-studi')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-graduation-cap text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Kartu Hasil Studi</span>
        </button>"""
content = re.sub(join_regex, new_khs, content, flags=re.DOTALL)

# Replace KAS REMAJA with PUSAT TAGIHAN
kas_regex = r"<!-- 3\. KAS REMAJA -->.*?Kas Remaja</span>\s*</button>"
new_tagihan = """<!-- 3. PUSAT TAGIHAN -->
        <button onclick="openModal('modal-pusat-tagihan')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-money-check-alt text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Pusat Tagihan</span>
        </button>"""
content = re.sub(kas_regex, new_tagihan, content, flags=re.DOTALL)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
