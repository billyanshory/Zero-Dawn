import re

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Define the old block to be removed
old_hero = """    <!-- HERO SECTION: IDUL ADHA -->
    <div class="relative w-full bg-[#451a03] overflow-hidden pt-6 pb-12 mb-8 shadow-2xl rounded-[2.5rem] md:rounded-[4rem] border-b-4 border-[#78350f]">
        <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
        <div class="absolute right-[-10%] top-0 opacity-10 transform rotate-12 pointer-events-none">
            <i class="fas fa-kaaba text-[250px] md:text-[400px] text-[#fcd34d]"></i>
        </div>

        <div class="container mx-auto px-4 md:px-8 relative z-10 text-center mt-4">
            <h1 class="text-4xl md:text-6xl font-bold text-[#fcd34d] mb-4 font-sans tracking-tight drop-shadow-lg">
                Idul Adha Mode
            </h1>
            <p class="text-white/80 text-lg md:text-xl font-medium max-w-2xl mx-auto mb-8">
                Portal Khusus Informasi & Kegiatan Qurban Masjid Al-Hijrah
            </p>
            <a href="/" class="inline-block bg-white/10 hover:bg-white/20 text-[#fcd34d] border border-[#fcd34d]/30 px-6 py-2.5 rounded-full font-bold transition backdrop-blur-sm">
                <i class="fas fa-arrow-left mr-2"></i> Kembali ke Beranda
            </a>
        </div>
    </div>"""

# Define the new header layout block
new_hero = """    <!-- DESKTOP SPLIT HEADER -->
    <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-8 md:mb-12">

        <!-- LEFT COLUMN: WELCOME (Desktop Only) -->
        <div class="hidden md:block pl-2">
            <p class="text-xl text-gray-500 font-medium mb-2">Assalamualaikum Warahmatullahi Wabarakatuh</p>
            <h1 class="text-5xl font-bold text-[#451a03] leading-tight mb-6">Selamat Datang di<br>Portal Qurban<br>Masjid Al Hijrah</h1>
            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                Mari kita teladani ketaatan Nabi Ibrahim AS dan keikhlasan Nabi Ismail AS melalui ibadah Qurban yang penuh berkah. Salurkan hewan Qurban terbaik Anda dan mari makmurkan masjid demi kemaslahatan umat di Samarinda.
            </p>
            <div class="flex gap-4">
                <a href="/agenda" class="bg-[#78350f] text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-[#451a03] transition transform hover:scale-105">Lihat Agenda</a>
                <a href="/donate" class="bg-white text-[#78350f] border-2 border-[#78350f]/20 px-8 py-3 rounded-full font-bold hover:border-[#78350f] hover:text-[#451a03] transition transform hover:scale-105">Infaq Sekarang</a>
            </div>
        </div>

        <!-- RIGHT COLUMN: PRAYER CARD (Mobile: Top, Desktop: Right) -->
        <div class="flex flex-col gap-6">

            <!-- PRAYER CARD -->
            <div class="bg-gradient-to-br from-[#78350f] to-[#451a03] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-white/10">
                <a href="/" class="absolute top-4 right-4 bg-white/20 hover:bg-white text-white hover:text-[#451a03] px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-[0_0_15px_rgba(255,255,255,0.3)] hover:shadow-[0_0_20px_rgba(255,255,255,0.6)] z-20 flex items-center gap-1 backdrop-blur-sm">
                    <i class="fas fa-arrow-left"></i> Kembali
                </a>
                <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                <div class="absolute right-[-10%] top-0 opacity-10 transform translate-x-4 -translate-y-4 pointer-events-none">
                    <i class="fas fa-kaaba text-9xl md:text-[150px] text-[#fcd34d]"></i>
                </div>
                <div class="relative z-10">
                    <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase">Waktu Sholat Berikutnya</p>
                    <h2 class="text-4xl font-bold mb-3" id="next-prayer-name">--:--</h2>
                    <div class="bg-white/20 backdrop-blur-md rounded-xl px-4 py-2 inline-block mb-6 border border-white/10">
                        <span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">--:--:--</span>
                    </div>

                    <div class="grid grid-cols-5 gap-1 text-center text-xs opacity-90 border-t border-white/20 pt-4">
                        <div><div class="font-semibold mb-1">Subuh</div><div id="fajr-time" class="font-mono">--:--</div></div>
                        <div><div class="font-semibold mb-1">Dzuhur</div><div id="dhuhr-time" class="font-mono">--:--</div></div>
                        <div><div class="font-semibold mb-1">Ashar</div><div id="asr-time" class="font-mono">--:--</div></div>
                        <div><div class="font-semibold mb-1">Maghrib</div><div id="maghrib-time" class="font-mono">--:--</div></div>
                        <div><div class="font-semibold mb-1">Isya</div><div id="isha-time" class="font-mono">--:--</div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>"""

new_content = content.replace(old_hero, new_hero)

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(new_content)

print("Replacement successful." if old_hero in content else "Old block not found.")
