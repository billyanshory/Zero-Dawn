import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'function snapBack\(element\) \{.*?\}', content, re.DOTALL)
if m:
    print("snapBack:", m.group(0))

m2 = re.search(r'function snapBack.*?\}.*?\}', content, re.DOTALL)
if m2:
    print("snapBack2:", m2.group(0))
