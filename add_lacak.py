import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

html_content = """

IDUL_ADHA_LACAK_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20 flex flex-col items-center justify-center p-4">
    <!-- Card Container -->
    <div class="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden relative">
        <!-- Header -->
        <div class="bg-[#1B4332] text-white p-6 relative">
            <a href="/idul-adha" class="absolute top-4 left-4 bg-white/20 hover:bg-white text-white hover:text-[#1B4332] w-8 h-8 rounded-full flex items-center justify-center text-xs transition-colors backdrop-blur-sm">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div class="absolute right-0 top-0 opacity-20 transform translate-x-4 -translate-y-4">
                <i class="fas fa-search-location text-[80px] text-[#D4A017]"></i>
            </div>
            <div class="text-center mt-6 relative z-10">
                <h2 class="text-xl font-bold text-[#D4A017] mb-1">Live Tracking Qurban</h2>
                <p class="text-xs text-[#F5F0E8]/80">Masjid Al-Hijrah Samarinda</p>
            </div>
        </div>

        <div class="p-6 md:p-8">
            {% if error %}
            <div class="text-center">
                <div class="w-20 h-20 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-times text-4xl"></i>
                </div>
                <h3 class="text-xl font-bold text-gray-800 mb-2">PIN Tidak Ditemukan</h3>
                <p class="text-sm text-gray-500 mb-6">{{ error }}</p>
                <form action="/qurban/lacak" method="GET" class="flex gap-2">
                    <input type="text" name="pin" placeholder="Masukkan PIN 6 karakter" class="flex-1 bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm font-mono font-bold uppercase text-center focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]">
                    <button type="submit" class="bg-[#1B4332] text-white px-6 rounded-xl font-bold text-sm shadow-md hover:bg-[#153426] transition">Cari</button>
                </form>
            </div>
            {% elif animal %}
            <!-- Identity -->
            <div class="text-center mb-8 border-b border-gray-100 pb-6">
                <div class="inline-flex items-center gap-2 bg-[#D4A017]/10 text-[#D4A017] px-4 py-2 rounded-full mb-3">
                    <i class="fas {{ 'fa-cow' if animal.animal_type == 'Sapi' else 'fa-sheep' }}"></i>
                    <span class="font-bold text-sm uppercase tracking-wider">{{ animal.animal_type }} No. {{ animal.queue_number }}</span>
                </div>
                <h3 class="text-2xl font-bold text-gray-800">{{ animal.sohibul_name }}</h3>
            </div>

            <!-- Progress Tracker -->
            <div class="relative pl-6 space-y-8">
                <!-- Line connection -->
                <div class="absolute left-[35px] top-4 bottom-4 w-1 bg-gray-100 rounded-full"></div>

                <!-- Step 1: Menunggu -->
                <div class="relative flex items-center gap-4">
                    <div class="w-6 h-6 rounded-full flex items-center justify-center z-10
                        {{ 'bg-[#1B4332] text-white shadow-[0_0_10px_rgba(27,67,50,0.5)]' if animal.status in ['menunggu_giliran', 'sedang_disembelih', 'proses_pencacahan', 'siap_diambil'] else 'bg-gray-200 text-gray-400' }}">
                        <i class="fas fa-check text-[10px]"></i>
                    </div>
                    <div class="flex-1 bg-white p-3 rounded-xl border {{ 'border-[#D4A017] shadow-lg ring-1 ring-[#D4A017]' if animal.status == 'menunggu_giliran' else 'border-gray-100 opacity-60' }}">
                        <p class="text-sm font-bold {{ 'text-[#D4A017]' if animal.status == 'menunggu_giliran' else 'text-gray-800' }}">⏳ Menunggu Giliran</p>
                        <p class="text-[10px] text-gray-500 mt-1">Hewan sedang dalam antrean pemotongan.</p>
                    </div>
                </div>

                <!-- Step 2: Disembelih -->
                <div class="relative flex items-center gap-4">
                    <div class="w-6 h-6 rounded-full flex items-center justify-center z-10
                        {{ 'bg-[#1B4332] text-white shadow-[0_0_10px_rgba(27,67,50,0.5)]' if animal.status in ['sedang_disembelih', 'proses_pencacahan', 'siap_diambil'] else 'bg-gray-200 text-gray-400' }}">
                        <i class="fas {{ 'fa-check text-[10px]' if animal.status in ['proses_pencacahan', 'siap_diambil'] else 'fa-circle text-[8px]' }}"></i>
                    </div>
                    <div class="flex-1 bg-white p-3 rounded-xl border {{ 'border-[#D4A017] shadow-lg ring-1 ring-[#D4A017]' if animal.status == 'sedang_disembelih' else 'border-gray-100 opacity-60' }}">
                        <p class="text-sm font-bold {{ 'text-[#D4A017]' if animal.status == 'sedang_disembelih' else 'text-gray-800' }}">🔪 Sedang Disembelih</p>
                        <p class="text-[10px] text-gray-500 mt-1">Panitia sedang melakukan proses penyembelihan.</p>
                    </div>
                </div>

                <!-- Step 3: Pencacahan -->
                <div class="relative flex items-center gap-4">
                    <div class="w-6 h-6 rounded-full flex items-center justify-center z-10
                        {{ 'bg-[#1B4332] text-white shadow-[0_0_10px_rgba(27,67,50,0.5)]' if animal.status in ['proses_pencacahan', 'siap_diambil'] else 'bg-gray-200 text-gray-400' }}">
                        <i class="fas {{ 'fa-check text-[10px]' if animal.status == 'siap_diambil' else 'fa-circle text-[8px]' }}"></i>
                    </div>
                    <div class="flex-1 bg-white p-3 rounded-xl border {{ 'border-[#D4A017] shadow-lg ring-1 ring-[#D4A017]' if animal.status == 'proses_pencacahan' else 'border-gray-100 opacity-60' }}">
                        <p class="text-sm font-bold {{ 'text-[#D4A017]' if animal.status == 'proses_pencacahan' else 'text-gray-800' }}">🥩 Proses Pencacahan & Penimbangan</p>
                        <p class="text-[10px] text-gray-500 mt-1">Daging sedang dicacah dan ditimbang.</p>
                    </div>
                </div>

                <!-- Step 4: Selesai -->
                <div class="relative flex items-center gap-4">
                    <div class="w-6 h-6 rounded-full flex items-center justify-center z-10
                        {{ 'bg-[#1B4332] text-white shadow-[0_0_10px_rgba(27,67,50,0.5)]' if animal.status == 'siap_diambil' else 'bg-gray-200 text-gray-400' }}">
                        <i class="fas fa-check text-[10px]"></i>
                    </div>
                    <div class="flex-1 bg-white p-3 rounded-xl border {{ 'border-[#D4A017] shadow-lg ring-1 ring-[#D4A017] bg-[#D4A017]/5' if animal.status == 'siap_diambil' else 'border-gray-100 opacity-60' }}">
                        <p class="text-sm font-bold {{ 'text-[#D4A017]' if animal.status == 'siap_diambil' else 'text-gray-800' }}">✅ Jatah Sohibul Siap Diambil</p>
                        <p class="text-[10px] text-gray-500 mt-1">Silakan menuju masjid untuk mengambil jatah qurban Anda.</p>
                    </div>
                </div>
            </div>

            <div class="mt-8 text-center">
                <button onclick="window.location.reload()" class="bg-gray-100 hover:bg-gray-200 text-gray-600 px-6 py-2 rounded-full font-bold text-xs transition-colors border border-gray-200">
                    <i class="fas fa-sync-alt mr-1"></i> Segarkan Status
                </button>
                <p class="text-[10px] text-gray-400 mt-3">Halaman ini diperbarui sesuai dengan ketukan panitia di lapangan.</p>
            </div>
            {% else %}
            <!-- Initial Search Form -->
            <div class="text-center py-6">
                <i class="fas fa-qrcode text-5xl text-gray-300 mb-4"></i>
                <h3 class="text-lg font-bold text-gray-800 mb-2">Lacak Hewan Qurban Anda</h3>
                <p class="text-xs text-gray-500 mb-6">Masukkan PIN yang diberikan oleh panitia untuk melacak status hewan secara real-time.</p>
                <form action="/qurban/lacak" method="GET" class="flex flex-col gap-3">
                    <input type="text" name="pin" required placeholder="Masukkan PIN 6 karakter" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-center font-mono font-bold text-lg uppercase focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017] tracking-widest">
                    <button type="submit" class="w-full bg-[#1B4332] text-white py-4 rounded-xl font-bold shadow-lg hover:bg-[#153426] transition text-sm">Lacak Sekarang</button>
                </form>
            </div>
            {% endif %}
        </div>
    </div>
</div>
'''

"""

routes = """
@app.route('/qurban/lacak', methods=['GET'])
def qurban_lacak():
    pin = request.args.get('pin', '').strip().upper()
    animal = None
    error = None

    try:
        if pin:
            animal = QurbanAnimal.query.filter_by(pin=pin).first()
            if not animal:
                error = "Silakan periksa kembali PIN Anda. Pastikan tidak ada salah ketik."
    except Exception as e:
        app.logger.error(f"Error looking up PIN: {e}")
        error = "Terjadi kesalahan sistem saat mencari data."

    rendered_content = render_template_string(IDUL_ADHA_LACAK_HTML, animal=animal, error=error, settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())
"""

insert_target = 'HOME_HTML = """'
if insert_target in content:
    content = content.replace(insert_target, html_content + insert_target)

# Routes
insert_target_r = "if __name__ == '__main__':"
if insert_target_r in content:
    content = content.replace(insert_target_r, routes + "\n" + insert_target_r)

with open(filename, "w") as f:
    f.write(content)

print("Injected lacak public")
