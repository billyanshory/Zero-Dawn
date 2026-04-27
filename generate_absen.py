import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# 1. Update the Dashboard Button to be a regular link with a late state UI
old_absen_btn = """                    <!-- ABSEN PANITIA (Time-Gated) -->
                    {% if not is_valid_window %}
                    <!-- DISABLED LATE STATE -->
                    <div class="bg-red-50 p-5 md:p-8 rounded-3xl shadow-lg flex flex-col items-center justify-center h-36 md:h-48 border-2 border-red-500 opacity-80 relative overflow-hidden">
                        <div class="absolute -right-4 -top-4 w-16 h-16 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold transform rotate-12 shadow-lg">LATE</div>
                        <div class="bg-red-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-red-600">
                            <i class="fas fa-times-circle text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-red-700">Terlambat</span>
                        <span class="text-[10px] text-red-500 text-center mt-1">Absensi Ditutup</span>
                    </div>
                    {% else %}
                    <!-- ACTIVE FORM -->
                    <form action="/idul-adha/absen" method="POST" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-amber-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-amber-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300 relative cursor-pointer" onclick="this.submit()">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <div class="bg-amber-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-amber-700 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                            <i class="fas fa-clipboard-check text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#78350f] group-hover:text-amber-700">Absen Panitia</span>
                        <span class="text-[10px] text-amber-600 font-medium absolute bottom-3">Batas: 08:30 AM</span>
                    </form>
                    {% endif %}"""

new_absen_btn = """                    <!-- ABSEN PANITIA -->
                    <a href="/idul-adha/absen-panitia" class="p-5 md:p-8 rounded-3xl shadow-lg flex flex-col items-center justify-center h-36 md:h-48 border group hover:scale-105 hover:shadow-2xl transition-all duration-300 relative overflow-hidden {{ 'bg-red-50 border-red-500 opacity-90 cursor-pointer' if not is_valid_window else 'bg-white shadow-amber-200/50 border-amber-50 card-hover cursor-pointer' }}">
                        {% if not is_valid_window %}
                        <div class="absolute -right-4 -top-4 w-16 h-16 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold transform rotate-12 shadow-lg">LATE</div>
                        <div class="bg-red-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-red-600 group-hover:bg-red-500 group-hover:text-white transition-colors">
                            <i class="fas fa-times-circle text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-red-700">Absen Panitia</span>
                        <span class="text-[10px] text-red-500 text-center mt-1">Terlambat / Ditutup</span>
                        {% else %}
                        <div class="bg-amber-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-amber-700 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                            <i class="fas fa-clipboard-check text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#78350f] group-hover:text-amber-700">Absen Panitia</span>
                        <span class="text-[10px] text-amber-600 font-medium absolute bottom-3">Aktif</span>
                        {% endif %}
                    </a>"""

content = content.replace(old_absen_btn, new_absen_btn)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
