1. **Remove modal-infaq and related JS:**
   - Delete HTML block from `<div id="modal-infaq"` to its closing `</div>`.
   - Delete `switchInfaqTab()`, `adjustInfaqTheme()`, `triggerInfaqWA()`.
   - Remove `modal-infaq` specific logic in `openModal()`.
2. **Remove specific routes:**
   - `/donate` and `donate()`
   - `/donate/update` and `donate_update()`
   - `/darurat` and `darurat()`
   - `/ramadhan` and `ramadhan_dashboard()`
3. **Remove Ramadhan and IRMA dashboards:**
   - Delete `RAMADHAN_STYLES`, `RAMADHAN_DASHBOARD_HTML`, and references to `IRMA_STYLES`.
   - Delete Ramadhan banner link on home page.
   - Delete Ramadhan mode CSS class from `body` tag and CSS rule `RAMADHAN MODE UTILS`.
4. **Remove Hijri date system in base layout:**
   - Delete `id="hijri-date"` element.
   - Delete `fetchHijri()` JS function and its initialization call.
5. **Remove Prayer Time card:**
   - Delete the prayer card section under `<!-- RIGHT COLUMN: PRAYER CARD & RAMADHAN BANNER -->` but ensure the SLB clock remains.
6. **Fix Calculator IDs:**
   - Rename `result-waris` -> `result-imt` in HTML and JS.
   - Rename `result-zakat` -> `result-sensory` in HTML and JS.
   - Rename `result-tahajjud` -> `result-auditori` in HTML and JS.
   - Rename `result-khatam` -> `result-iq` in HTML and JS.
   - Rename `result-fidyah` -> `result-motorik` in HTML and JS.
   - Rename `result-hijri` -> `result-diet` in HTML and JS.
7. **Update `calculator_data` dictionary:**
   - Rename `waris`, `zakat`, `tahajjud`, `khatam`, `fidyah`, `hijri` to `imt`, `sensory`, `auditori`, `iq`, `motorik`, `diet`.
8. **Update PWA manifest and service worker branding:**
   - Replace "Masjid Al Hijrah" with "Sekolah Luar Biasa".
   - Replace "Al Hijrah" with "SLB".
   - Replace cache name `al-hijrah-v1` with `slb-v1`.
   - Replace `/static/logomasjidalhijrah.png` with `/static/logoslb.png`.
9. **Update emergency WhatsApp message:**
   - Remove "Assalamualaikum" and make it SLB specific.
10. **Pre commit instructions**
   - Run verification checks as required.
11. **Submit.**
