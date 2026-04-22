1. **Remove the old hero banner from `IDUL_ADHA_DASHBOARD_HTML`**:
   The banner containing "Idul Adha Mode" and "Kembali ke Beranda" starting with `<div class="relative w-full bg-[#451a03]...` up to `</div>` before `<!-- MAIN CONTENT -->` will be removed.

2. **Add Responsive Desktop/Mobile layout to `IDUL_ADHA_DASHBOARD_HTML`**:
   Insert the new desktop split header structure, adopting the same style from `HOME_HTML`:
   ```html
   <!-- DESKTOP SPLIT HEADER -->
   <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-8 md:mb-12">

       <!-- LEFT COLUMN: WELCOME (Desktop Only) -->
       <div class="hidden md:block pl-2">
           <p class="text-xl text-gray-500 font-medium mb-2">Assalamualaikum Warahmatullahi Wabarakatuh</p>
           <h1 class="text-3xl md:text-5xl font-bold text-[#451a03] leading-tight mb-6">Selamat Datang di<br>Portal Qurban Masjid Al Hijrah</h1>
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
           <div class="bg-gradient-to-br from-[#78350f] to-[#451a03] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500">
                <a href="/" class="absolute top-4 right-4 bg-white/20 hover:bg-white text-white hover:text-[#451a03] px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-[0_0_15px_rgba(255,255,255,0.3)] hover:shadow-[0_0_20px_rgba(255,255,255,0.6)] z-20 flex items-center gap-1 backdrop-blur-sm">
                    <i class="fas fa-arrow-left"></i> Kembali
                </a>
               <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
               <div class="absolute right-[-10%] top-0 opacity-10 transform translate-x-4 -translate-y-4 pointer-events-none">
                   <i class="fas fa-kaaba text-[150px] text-[#fcd34d]"></i>
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
   </div>
   ```

3. **Remove "Idul Adha Mode" Banner Flipper from `HOME_HTML`**:
   The prompt specifies: "Transitioning to our mobile, Android, and iOS users, your directive is to execute a clean, permanent removal of that same redundant 'Idul Adha Mode Portal' banner, as screen real estate on mobile devices is a critical priority."
   This refers to the `Idul Adha Banner (Back Face)` block in `HOME_HTML`? Wait, `HOME_HTML` has a front face (Ramadhan) and a back face (Idul Adha) flip banner. The user says: "permanent removal of that same redundant 'Idul Adha Mode Portal' banner". If I remove the back face from `HOME_HTML`, the flip button on the Ramadhan front face will break or point nowhere, meaning I might need to remove the flip feature and just leave the Ramadhan banner, or remove the entire DUAL BANNER CONTAINER. The user says: "eliminate the redundant and structurally awkward banner card that was previously added—the one labeled 'Idul Adha Mode Portal Khusus Informasi & Kegiatan Qurban Masjid Al-Hijrah Kembali ke Beranda'". This exact string appears in `IDUL_ADHA_DASHBOARD_HTML`! "Idul Adha Mode Portal Khusus Informasi & Kegiatan Qurban Masjid Al-Hijrah Kembali ke Beranda" is precisely the text in the hero section I am removing.
   "Transitioning to our mobile, Android, and iOS users, your directive is to execute a clean, permanent removal of that same redundant 'Idul Adha Mode Portal' banner... In its place, at the very zenith of the mobile viewport, you must position the dynamic prayer times card as the primary focal point." So they are purely talking about the `IDUL_ADHA_DASHBOARD_HTML` layout. The previous hero banner pushed the menu down. Replacing the hero banner with the prayer times card on mobile solves this. I don't strictly need to modify `HOME_HTML` flip banner unless it says "Idul Adha Mode Portal Khusus...". The `HOME_HTML` flip banner just says "Idul Adha Mode" "Akses Dashboard Khusus Qurban", which is the entry point! So I must *not* remove the entry point from `HOME_HTML`.

4. **Detailed Action Plan**:
   - `replace_with_git_merge_diff` on `masjid-al-hijrah-61...py` to replace the existing `IDUL_ADHA_DASHBOARD_HTML` hero section and layout structure up to the menu grid.
   - Run `python3 verify.py` to ensure no syntax errors.

Let's do this directly.
