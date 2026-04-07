import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'function toggleAudio\(type\).*?function ', content, re.DOTALL)
if m:
    print(m.group(0)[:1000])

m2 = re.search(r'<div class="grid grid-cols-1 md:grid-cols-2 gap-4">.*?Terapi Frekuensi', content, re.DOTALL)
if m2:
    print(m2.group(0)[-1000:])
