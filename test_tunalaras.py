import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'SLB_TUNALARAS_HTML = .*?Riwayat Perasaan.*?</div>', content, re.DOTALL)
if m:
    print(m.group(0)[-1000:])

m2 = re.search(r'def slb_tunalaras.*?\}', content, re.DOTALL)
if m2:
    print("def slb_tunalaras:", m2.group(0))
