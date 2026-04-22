import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

html_content = """

IDUL_ADHA_PEMBAGIAN_CEK_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20 flex flex-col items-center justify-center p-4">
    <div class="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden relative">
        <!-- Header -->
        <div class="bg-[#D4A017] text-[#1B4332] p-6 relative">
            <a href="/idul-adha" class="absolute top-4 left-4 bg-white/20 hover:bg-white text-[#1B4332] hover:text-[#1B4332] w-8 h-8 rounded-full flex items-center justify-center text-xs transition-colors backdrop-blur-sm">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div class="absolute right-0 top-0 opacity-20 transform translate-x-4 -translate-y-4">
                <i class="fas fa-ticket-alt text-[80px] text-[#1B4332]"></i>
            </div>
            <div class="text-center mt-6 relative z-10">
                <h2 class="text-xl font-bold mb-1">E-Kupon Pengambilan</h2>
                <p class="text-xs font-bold opacity-80">Distribusi Daging Qurban</p>
            </div>
        </div>

        <div class="p-6 md:p-8">
            {% if error %}
            <div class="bg-[#8B2635]/10 border border-[#8B2635]/20 text-[#8B2635] p-4 rounded-xl text-sm font-bold text-center mb-6">
                {{ error }}
            </div>
            {% endif %}

            {% if kupon %}
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
            {% endif %}
        </div>
    </div>
</div>
'''

"""

routes = """
@app.route('/qurban/pembagian/cek', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def qurban_pembagian_cek():
    kupon = None
    slot = None
    error = None

    try:
        if request.method == 'POST':
            nik = request.form.get('nik', '').strip()
            coupon_number = request.form.get('coupon_number', '').strip().upper()

            if not nik.isdigit() or len(nik) != 16:
                error = "Format NIK tidak valid. Harus 16 digit angka."
            else:
                kupon = DistribusiKupon.query.filter_by(nik=nik, coupon_number=coupon_number).first()
                if kupon:
                    slot = DistribusiSlot.query.get(kupon.slot_id)
                else:
                    error = "Kombinasi NIK dan Nomor Kupon tidak ditemukan."
    except Exception as e:
        app.logger.error(f"Error checking coupon: {e}")
        error = "Terjadi kesalahan sistem."

    rendered_content = render_template_string(IDUL_ADHA_PEMBAGIAN_CEK_HTML, kupon=kupon, slot=slot, error=error, settings=get_settings())
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

print("Injected pembagian cek public")
