with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

import re
m = re.search(r'function bindDragEvents.*?}', content, re.DOTALL)
if m:
    print(m.group(0))

m2 = re.search(r'onStart.*?\}', content, re.DOTALL)
if m2:
    print(m2.group(0))
