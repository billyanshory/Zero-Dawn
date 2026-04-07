import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'id="modal-terapi-log".*?<div class="flex justify-between items-center mb-6">.*?<h4 class="text-sm font-bold text-gray-800 mb-4', content, re.DOTALL)
if m:
    print(m.group(0)[:1000])
