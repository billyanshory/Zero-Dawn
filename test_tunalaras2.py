import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'SLB_TUNALARAS_HTML = .*?class="mt-12">.*?Riwayat Perasaan.*?</div>\n        </div>', content, re.DOTALL)
if m:
    print(m.group(0)[-1000:])
