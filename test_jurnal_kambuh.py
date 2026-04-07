import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'Jurnal Kambuh.*?modal-terapi-log.*?</form>', content, re.DOTALL)
if m:
    print(m.group(0)[:1000])

m2 = re.search(r'Terapi, Bantuan Kesehatan & Epilepsi', content, re.DOTALL)
if m2:
    print("Found Terapi")

m3 = re.search(r'@app\.route\(\'/therapy/log\'', content, re.DOTALL)
if m3:
    print("Found /therapy/log")

m4 = re.search(r'class EpilepsiLog', content, re.DOTALL)
if m4:
    print("Found EpilepsiLog")
