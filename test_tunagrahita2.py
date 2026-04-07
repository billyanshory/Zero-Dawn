import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'const draggables = document.querySelectorAll\(\'\.draggable-item\'\).*?draggable\.addEventListener\(\'touchstart\', onStart, \{passive: false\}\);', content, re.DOTALL)
if m:
    print(m.group(0))
