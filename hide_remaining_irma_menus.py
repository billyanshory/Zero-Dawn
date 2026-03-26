import re

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "r") as f:
    content = f.read()

mading_regex = r"(<!-- 4\. MADING KREATIF.*?<button onclick=\"openModal\('modal-wall'\)\")"
content = re.sub(mading_regex, r"\1 style=\"display:none;\"", content)

proker_regex = r"(<!-- 5\. PROKER EVENT.*?<button onclick=\"openModal\('modal-events'\)\")"
content = re.sub(proker_regex, r"\1 style=\"display:none;\"", content)

curhat_regex = r"(<!-- 6\. CURHAT ISLAMI.*?<button onclick=\"openModal\('modal-qa'\)\")"
content = re.sub(curhat_regex, r"\1 style=\"display:none;\"", content)

with open("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat ).py", "w") as f:
    f.write(content)
