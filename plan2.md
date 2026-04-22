1. Verify `HOME_HTML` DUAL BANNER structure: The user said "Transitioning to our mobile, Android, and iOS users, your directive is to execute a clean, permanent removal of that same redundant 'Idul Adha Mode Portal' banner, as screen real estate on mobile devices is a critical priority." Since the `HOME_HTML` flip-banner includes "Idul Adha Mode", and on mobile it takes up vertical space, we should probably remove the "Idul Adha Mode" entirely from `HOME_HTML`? Wait, if we do that, users cannot access the portal from the home page.
The text the user specifically wanted to eliminate was:
> the one labeled 'Idul Adha Mode Portal Khusus Informasi & Kegiatan Qurban Masjid Al-Hijrah Kembali ke Beranda'
This strictly references the HERO banner at the top of the `IDUL_ADHA_DASHBOARD_HTML`, which I have successfully removed and replaced.

2. Double check the Prayer Card functionality inside the new `IDUL_ADHA_DASHBOARD_HTML`. Ensure the JS hooks (IDs: `next-prayer-name`, `countdown-timer`, `fajr-time`, etc) are present and correct.
In my `modify.py` replacement string:
```html
<h2 class="text-4xl font-bold mb-3" id="next-prayer-name">--:--</h2>
<span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">--:--:--</span>
<div id="fajr-time" class="font-mono">--:--</div>
...
```
These IDs are exactly the ones used by the client-side JS. Since I just moved the HTML from the old `RIGHT COLUMN` to the new `RIGHT COLUMN (Top on Mobile)`, the JS will hook onto them as expected. The only caveat is if `HOME_HTML` and `IDUL_ADHA_DASHBOARD_HTML` both load in the same DOM. They do not; they are rendered on different routes (`/` vs `/idul-adha`).

3. Grid responsive behavior:
```html
<div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-8 md:mb-12">
    <!-- LEFT COLUMN -->
    <div class="hidden md:block pl-2"> ... </div>
    <!-- RIGHT COLUMN -->
    <div class="flex flex-col gap-6"> ... </div>
</div>
```
On mobile (no `md:` prefix), `md:grid` degrades to a standard `block` layout.
The `LEFT COLUMN` is `hidden md:block`, meaning on mobile it has `display: none;`.
The `RIGHT COLUMN` has no mobile-hiding classes. Therefore, on mobile, the right column (Prayer Card) shows up as the ONLY element in this header, effectively making it the "primary focal point" at the "very zenith of the mobile viewport" exactly as requested!

4. Check `Menu Qurban` structure:
```html
<div class="w-full">
    <div class="w-full">
        <h2 class="text-2xl font-bold text-[#451a03] mb-6 flex items-center border-l-4 border-[#78350f] pl-4">
            <i class="fas fa-th-large text-[#78350f] mr-3"></i>Menu Qurban
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
            <!-- Items ... -->
        </div>
    </div>
</div>
```
The grid is 2 cols on mobile, 3 cols on desktop. This perfectly satisfies "Below this primary header layer, for both desktop and mobile views, you must meticulously organize the primary functional buttons: 'Menu Qurban', the time-gated 'Absen Panitia' ... Pay exhaustive attention to the CSS flexbox and grid definitions... ensuring that the transition between the desktop’s side-by-side layout and the mobile’s vertical stack is flawless."

5. Final step is to `pre_commit_instructions` and then `submit`.
