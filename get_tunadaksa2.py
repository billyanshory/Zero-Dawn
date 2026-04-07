import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'function toggleAudio\(type\).*?\}', content, re.DOTALL)
if m:
    print(m.group(0))

m2 = re.search(r'<!-- Audio 1.*?<!-- Akhir Audio', content, re.DOTALL)
if m2:
    print(m2.group(0))
