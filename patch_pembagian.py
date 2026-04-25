import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# IDUL_ADHA_PEMBAGIAN_CEK_HTML adjustments
# 1. Padding and justify-center
content = content.replace(
    '<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20 flex flex-col items-center justify-center p-4">',
    '<div class="min-h-screen bg-[#F5F0E8] font-sans pt-24 md:pt-28 pb-20 flex flex-col items-center p-4">'
)

# 2. Labels and IDs replacement
content = content.replace(
    '<label class="block text-xs font-bold text-gray-600 mb-1">NIK Warga</label>\n                        <input type="text" id="warga_nik" required pattern="[0-9]{16}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">',
    '<label class="block text-xs font-bold text-gray-600 mb-1">Nama Lengkap Kepala Keluarga</label>\n                        <input type="text" id="warga_nama" required placeholder="Contoh: Ahmad Fauzi" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">'
)

content = content.replace(
    '<label class="block text-xs font-bold text-gray-600 mb-1">NIK (Nomor Induk Kependudukan)</label>\n                        <input type="text" id="cek_nik" required pattern="[0-9]{16}" title="Masukkan 16 digit angka NIK" placeholder="Contoh: 6472010000000001" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm font-mono focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017] tracking-widest text-center">',
    '<label class="block text-xs font-bold text-gray-600 mb-1">Nama Lengkap Kepala Keluarga</label>\n                        <input type="text" id="cek_nama" required placeholder="Contoh: Ahmad Fauzi" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017] text-center">'
)

content = content.replace(
    '<th class="p-3">NIK</th>',
    '<th class="p-3">Nama KK</th>'
)

# Replace Javascript logic for generateKupon
content = content.replace(
    "const nik = document.getElementById('warga_nik').value;",
    "const nik = document.getElementById('warga_nama').value;"
)
content = content.replace(
    "if(!nik || nik.length !== 16) { alert(\"NIK harus 16 digit angka\"); return; }",
    "if(!nik) { alert(\"Nama Lengkap Kepala Keluarga harus diisi\"); return; }"
)

# Replace ID in new-kupon-display
content = content.replace(
    '<p class="text-sm mt-2 text-gray-600">NIK: <strong id="generated-nik-text"></strong></p>',
    '<p class="text-sm mt-2 text-gray-600">Nama: <strong id="generated-nik-text"></strong></p>'
)

# JS in showPembagianResult
content = content.replace(
    "document.getElementById('res-kupon-nik').innerText = data.nik.substring(0, 4) + '********' + data.nik.substring(12, 16);",
    "document.getElementById('res-kupon-nik').innerText = data.nik;"
)

# JS for public form
content = content.replace(
    "const nik = document.getElementById('cek_nik').value;",
    "const nik = document.getElementById('cek_nama').value;"
)

# Jinja duplications in CEK HTML
jinja_form_block = """            {% if kupon %}
            <!-- Result Display -->
            <div class="text-center mb-6">
                <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Status Kupon</p>
                {% if kupon.is_claimed %}
                <div class="inline-flex items-center gap-2 bg-[#8B2635]/10 text-[#8B2635] px-4 py-2 rounded-full mb-3 border border-[#8B2635]/20">
                    <i class="fas fa-check-circle"></i>
                    <span class="font-bold text-sm uppercase">Sudah Diambil</span>
                </div>
                {% else %}
                <div class="inline-flex items-center gap-2 bg-[#1B4332]/10 text-[#1B4332] px-4 py-2 rounded-full mb-3 border border-[#1B4332]/20">
                    <i class="fas fa-clock"></i>
                    <span class="font-bold text-sm uppercase">Belum Diambil</span>
                </div>
                {% endif %}
            </div>

            <!-- Ticket -->
            <div class="bg-gradient-to-br from-[#1B4332] to-[#153426] rounded-2xl p-6 text-white shadow-xl relative overflow-hidden border border-white/10 mb-6">
                <!-- Ticket Notch -->
                <div class="absolute -left-4 top-1/2 transform -translate-y-1/2 w-8 h-8 bg-white rounded-full"></div>
                <div class="absolute -right-4 top-1/2 transform -translate-y-1/2 w-8 h-8 bg-white rounded-full"></div>

                <div class="text-center border-b border-white/20 pb-4 mb-4 border-dashed relative z-10">
                    <p class="text-xs text-[#D4A017] font-bold uppercase tracking-wider mb-1">Area Distribusi</p>
                    <h3 class="text-4xl font-bold text-white">{{ slot.rt_identifier }}</h3>
                </div>

                <div class="text-center relative z-10">
                    <p class="text-[10px] text-gray-300 font-bold uppercase tracking-wider mb-2">Jadwal Pengambilan Anda</p>
                    <div class="bg-[#D4A017] text-[#1B4332] rounded-xl py-3 px-4 inline-block font-mono font-bold text-2xl shadow-inner border border-white/20">
                        {{ slot.time_start }} - {{ slot.time_end }} WIB
                    </div>
                </div>
            </div>

            <div class="bg-gray-50 rounded-xl p-4 border border-gray-100 text-center">
                <p class="text-xs text-gray-600 mb-1">Kupon: <strong class="font-mono">{{ kupon.coupon_number }}</strong></p>
                <p class="text-xs text-gray-500">Sisa Kuota Sesi Ini: <strong>{{ slot.total_quota - slot.distributed_count }}</strong> paket</p>
            </div>

            <div class="mt-6">
                <a href="/qurban/pembagian/cek" class="block w-full text-center text-xs font-bold text-gray-500 hover:text-[#1B4332] transition">Cek NIK Lainnya</a>
            </div>
            {% else %}
            <!-- Form -->
            <div class="text-center mb-6">
                <p class="text-sm text-gray-600">Hindari antrean panjang. Cek jadwal pengambilan daging qurban RT Anda di sini.</p>
            </div>
            <form action="/qurban/pembagian/cek" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">NIK (Nomor Induk Kependudukan)</label>
                    <input type="text" name="nik" required pattern="[0-9]{16}" title="Masukkan 16 digit angka NIK" placeholder="Contoh: 6472010000000001" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm font-mono focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017] tracking-widest text-center">
                </div>

                <div>
                    <label class="block text-xs font-bold text-gray-600 mb-1">Nomor Kupon (2FA)</label>
                    <input type="text" name="coupon_number" required placeholder="Sesuai yang diberikan RT" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm font-mono focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017] tracking-widest text-center uppercase">
                </div>

                <button type="submit" class="w-full bg-[#1B4332] text-white py-4 rounded-xl font-bold shadow-lg hover:bg-[#153426] transition mt-2">Cek Jadwal Saya</button>
            </form>
            {% endif %}"""

content = content.replace(jinja_form_block, "")

# IDUL_ADHA_PEMBAGIAN_ADMIN_HTML replacements
content = content.replace(
    '<label class="block text-xs font-bold text-gray-600 mb-1">NIK Warga (16 digit)</label>\n                        <input type="text" name="nik" required pattern="[0-9]{16}" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">',
    '<label class="block text-xs font-bold text-gray-600 mb-1">Nama Lengkap Kepala Keluarga</label>\n                        <input type="text" name="nik" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]" placeholder="Contoh: Ahmad Fauzi">'
)

# Backend logic replacements (only the ones not done yet or verify)
content = content.replace(
    "'nik': k.nik[:4] + '********' + k.nik[-4:],",
    "'nik': k.nik,"
)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
