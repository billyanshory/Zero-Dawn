import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

content = re.sub(r'csrf_token=csrf_token, peran=', r'csrf_token=lambda: "", peran=', content)

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'w') as f:
    f.write(content)
