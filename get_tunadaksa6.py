import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'Relaksasi Delta.*?</div>.*?</div>', content, re.DOTALL)
if m:
    print("Delta:", m.group(0))

m2 = re.search(r'<audio.*?</audio>', content, re.DOTALL)
if m2:
    print("Audios:", m2.group(0))

m3 = re.search(r'Terapi Frekuensi.*?</svg>.*?</div>', content, re.DOTALL)
if m3:
    print("Terapi Frekuensi:", m3.group(0))
