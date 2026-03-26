import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

old_banner_regex = r"<!-- IRMA BANNER -->.*?</a>"

new_split_banner = """<!-- PORTAL MAHASISWA & DOSEN -->
            <div class="relative floating-card overflow-hidden rounded-3xl shadow-xl border border-gray-200 mt-4 flex h-32 md:h-40">
                <!-- Zona Kiri: Mahasiswa -->
                <a href="/mahasiswa" class="w-1/2 relative group hover:z-10 transition-all duration-300">
                    <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-blue-400 group-hover:scale-105 transition-transform duration-300"></div>
                    <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                    <div class="absolute -right-8 top-1/2 transform -translate-y-1/2 opacity-20 text-white pointer-events-none group-hover:scale-110 transition-transform duration-300">
                        <i class="fas fa-user-graduate text-7xl md:text-8xl"></i>
                    </div>
                    <div class="relative h-full flex flex-col justify-center px-4 md:px-6 z-10">
                        <h2 class="text-xl md:text-2xl font-bold text-white mb-1 font-sans tracking-wide leading-none">Portal Mahasiswa</h2>
                        <p class="text-white/80 text-[10px] md:text-xs font-medium">Akademik & Keuangan</p>
                    </div>
                </a>

                <!-- Garis Pembatas Diagonal -->
                <div class="absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-4 z-20 pointer-events-none" style="background: linear-gradient(135deg, transparent 45%, white 45%, white 55%, transparent 55%);"></div>

                <!-- Zona Kanan: Dosen -->
                <a href="/dosen" class="w-1/2 relative group hover:z-10 transition-all duration-300">
                    <div class="absolute inset-0 bg-gradient-to-r from-orange-400 to-orange-500 group-hover:scale-105 transition-transform duration-300"></div>
                    <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                    <div class="absolute right-2 md:right-4 top-1/2 transform -translate-y-1/2 opacity-20 text-white pointer-events-none group-hover:scale-110 transition-transform duration-300">
                        <i class="fas fa-chalkboard-teacher text-7xl md:text-8xl"></i>
                    </div>
                    <div class="relative h-full flex flex-col justify-center px-4 md:px-6 items-end text-right z-10 pl-8">
                        <h2 class="text-xl md:text-2xl font-bold text-white mb-1 font-sans tracking-wide leading-none">Portal Dosen</h2>
                        <p class="text-white/80 text-[10px] md:text-xs font-medium">Persetujuan & Nilai</p>
                    </div>
                </a>
            </div>"""

content = re.sub(old_banner_regex, new_split_banner, content, flags=re.DOTALL)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
