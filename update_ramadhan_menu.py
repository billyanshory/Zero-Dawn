import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

# Replace 1. JADWAL TAKJIL -> PABRIK SURAT OTOMATIS
takjil_block_regex = r"<!-- 1\. JADWAL TAKJIL -->.*?Jadwal Takjil</span>\s*</button>"
new_pabrik_surat = """<!-- 1. PABRIK SURAT OTOMATIS -->
            <button onclick="openModal('modal-pabrik-surat')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-file-signature text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Pabrik Surat Otomatis</span>
            </button>"""
content = re.sub(takjil_block_regex, new_pabrik_surat, content, flags=re.DOTALL)

# Replace 2. IMSAKIYAH -> LACI ARSIP DIGITAL
imsakiyah_block_regex = r"<!-- 2\. IMSAKIYAH -->.*?Imsakiyah</span>\s*</button>"
new_arsip = """<!-- 2. LACI ARSIP DIGITAL -->
            <button onclick="openModal('modal-arsip-digital')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-blue-400 mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-archive text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-blue-400 transition-colors">Laci Arsip Digital</span>
            </button>"""
content = re.sub(imsakiyah_block_regex, new_arsip, content, flags=re.DOTALL)

# Remove 3. KAS RAMADHAN
kas_ramadhan_block_regex = r"<!-- 3\. KAS RAMADHAN -->.*?Kas Ramadhan</span>\s*</button>"
content = re.sub(kas_ramadhan_block_regex, "", content, flags=re.DOTALL)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
