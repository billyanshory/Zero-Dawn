import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m2 = re.search(r'function snapBack\(element\) \{.*?\}, 400\);.*?\}', content, re.DOTALL)
if m2:
    print("snapBack full:", m2.group(0))
