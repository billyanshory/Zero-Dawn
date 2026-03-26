import re
with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

tarawih_regex = r"(<!-- 4\. JADWAL TARAWIH.*?<button onclick=\"openModal\('modal-tarawih'\)\")"
content = re.sub(tarawih_regex, r"\1 style=\"display:none;\"", content)

zakat_regex = r"(<!-- 5\. ZAKAT CALCULATOR.*?<button onclick=\"openModal\('modal-zakat-menu'\)\")"
content = re.sub(zakat_regex, r"\1 style=\"display:none;\"", content)

amalan_regex = r"(<!-- 6\. AMALAN CHECKLIST.*?<button onclick=\"openModal\('modal-amalan'\)\")"
content = re.sub(amalan_regex, r"\1 style=\"display:none;\"", content)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
