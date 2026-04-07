import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

print("Models starting at Siswa:")
m = re.search(r'class Siswa\(db\.Model\).*?class EpilepsiLog', content, re.DOTALL)
if m:
    print(m.group(0))
