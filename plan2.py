import re

with open('kampus-stie-samarinda-4 ( idcloudhost - dashboard home utama - debugging & 6 fitur utama home ).py', 'r') as f:
    content = f.read()

# I need to create the UI for the 6 main buttons and the 12 tools.
# The user wants all 6 main buttons in one group called "Menu Utama" with 6 buttons total.
# Then below it, two groups of 6 buttons each.

# Right now, there are 2 groups for the main buttons:
# 1. Layanan Penerimaan (Profil & Program Studi, Pendaftaran Mahasiswa Baru, Cek Status Kelulusan)
# 2. Dinamika Akademik (Berita & Agenda Kampus, Perpustakaan & Karya Ilmiah, Tracer Study & Jejak Alumni)

# We need to unite them under "Menu Utama". The layout should be "sejajar, simetris, dan sangat ergonomis memanjakan mata"

# The 6 buttons for Terapi Bantuan Kesehatan dan Epilepsi:
# 1. Terapi Suara -> modal-terapi-audio -> music icon
# 2. Latihan Napas -> modal-terapi-napas -> lungs/wind icon
# 3. Pelacak Tidur -> modal-terapi-tidur -> bed icon
# 4. Jurnal Kambuh -> modal-terapi-log -> file-medical icon
# 5. Alarm Obat -> modal-terapi-alarm -> capsules icon
# 6. Diet Keton -> modal-terapi-diet -> apple-alt icon

# The 6 buttons for Kalkulator Islam:
# 1. Perhitungan Waris -> modal-waris -> users icon
# 2. Zakat Maal -> modal-zakat -> hand-holding-usd icon
# 3. Pengingat Tahajjud -> modal-tahajjud -> moon icon
# 4. Target Khatam -> modal-khatam -> quran icon
# 5. Fidyah -> modal-fidyah -> utensils icon
# 6. Konverter Hijriah -> modal-hijri -> calendar-alt icon
