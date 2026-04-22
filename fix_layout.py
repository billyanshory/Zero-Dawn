import re

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Since the prompt said "On the left panel, craft a spiritually resonant welcoming interface ... To the right of this greeting panel, you will integrate the established digital prayer times card ... Below this primary header layer ... you must meticulously organize the primary functional buttons: 'Menu Qurban'..."
# My previous regex replaced the HERO section correctly but I ALSO added a prayer card there, meaning we now have TWO prayer cards, one in the new header and one in the "RIGHT COLUMN" of the MAIN CONTENT section!

# And the "MAIN CONTENT" grid had:
# `grid grid-cols-1 lg:grid-cols-3`
# Left column (`lg:col-span-2`) is "Menu Qurban".
# Right column is the OLD PRAYER CARD.

# The prompt asks for:
# TOP LAYER (Split Header):
# - Left: Welcome Greeting
# - Right (Top on Mobile): Prayer Card
# BELOW TOP LAYER:
# - Menu Qurban Grid. The menu grid shouldn't be split 2/3 and 1/3 anymore because the prayer card moved to the top layer. It should probably just be a standard grid.

# Let's remove the old RIGHT COLUMN: PRAYER CARD block from MAIN CONTENT,
# and change the grid from `grid-cols-1 lg:grid-cols-3` to just something that takes full width (or keep the same `lg:col-span-2` but remove the column entirely, so it's centered or full width).

old_main_content = """    <!-- MAIN CONTENT -->
    <div class="container mx-auto px-4 md:px-8 max-w-6xl mb-12">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

            <!-- LEFT COLUMN: MENU GRID -->
            <div class="lg:col-span-2">"""

new_main_content = """    <!-- MAIN CONTENT -->
    <div class="container mx-auto px-4 md:px-8 max-w-6xl mb-12">
        <div class="w-full">

            <!-- MENU GRID -->
            <div class="w-full">"""

old_right_column = """            <!-- RIGHT COLUMN: PRAYER CARD -->
            <div class="flex flex-col gap-6">
                <!-- PRAYER CARD -->
                <div class="bg-gradient-to-br from-[#78350f] to-[#451a03] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-[#fcd34d]/30">
                    <a href="{{ url_for('fitur_masjid') }}" class="absolute top-4 right-4 bg-white/10 hover:bg-white text-white hover:text-[#78350f] px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] z-20 flex items-center gap-1 backdrop-blur-sm">
                        <i class="fas fa-mosque"></i> Fitur Lainnya
                    </a>
                    <div class="absolute top-0 right-0 opacity-5 transform translate-x-4 -translate-y-4">
                        <i class="fas fa-mosque text-9xl"></i>
                    </div>
                    <div class="relative z-10">
                        <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase text-[#fcd34d]">Waktu Sholat Berikutnya</p>
                        <h2 class="text-4xl font-bold mb-3" id="next-prayer-name">--:--</h2>
                        <div class="bg-black/30 backdrop-blur-md rounded-xl px-4 py-2 inline-block mb-6 border border-white/10">
                            <span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">--:--:--</span>
                        </div>

                        <div class="grid grid-cols-5 gap-1 text-center text-xs opacity-90 border-t border-[#fcd34d]/20 pt-4">
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Subuh</div>
                                <div id="fajr-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Dzuhur</div>
                                <div id="dhuhr-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Ashar</div>
                                <div id="asr-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Maghrib</div>
                                <div id="maghrib-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Isya</div>
                                <div id="isha-time" class="font-mono">--:--</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
"""

new_right_column = """        </div>
    </div>
</div>
"""

content = content.replace(old_main_content, new_main_content)
if old_right_column in content:
    content = content.replace(old_right_column, new_right_column)
else:
    print("WARNING: old_right_column not found perfectly")

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
