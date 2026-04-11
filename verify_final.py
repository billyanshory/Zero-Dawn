import sys

filename = "sekolah-luar-biasa-69 ( idcloudhost - debugging - waktu, save data, warna tab, jadwal medis error, tambah kamus, json file kamus, api modul  - Opus 4.6 ).py"

with open(filename, 'r') as f:
    text = f.read()

assert "modal-infaq" not in text, "modal-infaq still exists!"
assert "function adjustInfaqTheme()" not in text, "adjustInfaqTheme still exists!"
assert "RAMADHAN_DASHBOARD_HTML" not in text, "RAMADHAN_DASHBOARD_HTML still exists!"
assert "@app.route('/donate'" not in text, "/donate route still exists!"
assert "@app.route('/emergency')" not in text, "/emergency route still exists!"
assert "result-waris" not in text, "result-waris still exists!"
assert "result-imt" in text, "result-imt NOT found!"
assert "logoslb.png" in text, "logoslb.png NOT found!"
assert "logomasjidalhijrah.png" not in text, "logomasjidalhijrah.png still exists!"
assert "Masjid Al Hijrah" not in text, "Masjid Al Hijrah still exists!"
assert "Sekolah Luar Biasa" in text, "Sekolah Luar Biasa NOT found!"

print("All verifications passed successfully!")
