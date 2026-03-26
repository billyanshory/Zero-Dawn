import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

dosen_route = """
@app.route('/dosen')
def dosen_dashboard():
    # DOSEN THEME
    dosen_theme = {
        'nav_bg': 'bg-[#FDFBF7]/90 backdrop-blur-md border-b border-[#E8C5A8]/20',
        'icon_bg': 'bg-[#E8C5A8]/20',
        'icon_text': 'text-[#A05D4A]',
        'title_text': 'text-[#A05D4A]',
        'link_hover': 'hover:text-[#A05D4A]',
        'link_active': 'text-[#A05D4A] font-bold',
        'btn_primary': 'bg-[#E8C5A8] text-[#A05D4A] font-bold hover:bg-[#A05D4A] hover:text-white',
        'bottom_nav_bg': 'bg-[#FDFBF7]',
        'bottom_active': 'text-[#A05D4A]',
        'bottom_btn_bg': 'bg-[#E8C5A8]',
        'bottom_btn_text': 'text-[#A05D4A]',
        'bottom_text_inactive': 'text-gray-400'
    }

    dosen_html = '''
    <div class="pt-24 pb-32 px-5 md:px-8 bg-[#FDFBF7] min-h-screen">
        <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-10">
            <div class="hidden md:block pl-2">
                <p class="text-xl text-[#A05D4A]/70 font-medium mb-2">Salam Sejahtera Bapak/Ibu Dosen</p>
                <h1 class="text-5xl font-bold text-[#A05D4A] leading-tight mb-6">Portal Dosen<br>STIESAM</h1>
                <p class="text-[#A05D4A]/80 text-lg leading-relaxed mb-8">
                    Terima kasih atas dedikasi luar biasa Anda dalam mendidik dan membimbing para mahasiswa STIESAM. Mari wujudkan akademik yang tertata rapi.
                </p>
            </div>
            <div>
                <div class="bg-gradient-to-br from-[#E8C5A8] to-[#D5A78B] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-white/20">
                    <div class="absolute top-0 right-0 opacity-10 transform translate-x-4 -translate-y-4">
                        <i class="fas fa-chalkboard-teacher text-9xl"></i>
                    </div>
                    <div class="relative z-10">
                        <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase text-[#5D3425]">Pengingat Akademik</p>
                        <h2 class="text-2xl font-bold mb-3 text-[#5D3425]">Batas Input Nilai UAS</h2>
                        <div class="bg-white/20 backdrop-blur-md rounded-xl px-4 py-2 inline-block mb-6 border border-white/10 text-[#5D3425]">
                            <span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">Tinggal 3 Hari</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h3 class="text-[#A05D4A] font-bold text-lg mb-4 pl-3 border-l-4 border-[#E8C5A8]">Menu Utama (Dosen)</h3>
        <div class="grid grid-cols-2 gap-4 mb-24 max-w-2xl">
            <button onclick="alert('Memuat daftar KRS Mahasiswa Perwalian...')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-file-signature text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Persetujuan<br>Rencana Studi</span>
            </button>
            <button onclick="alert('Membuka form Input Nilai Akhir yang langsung tembus ke akun mahasiswa...')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-marker text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Input<br>Nilai Akhir</span>
            </button>
        </div>
    </div>
    '''
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML + IRMA_STYLES,
                                  active_page='irma',
                                  theme=dosen_theme,
                                  content=dosen_html,
                                  full_width=True,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())
"""

# Insert the dosen route right before def manifest()
insert_pos = content.find("def manifest():")
content = content[:insert_pos] + dosen_route + "\n" + content[insert_pos:]

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
