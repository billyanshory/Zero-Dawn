import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'@app\.route\(\'\/\'\)\ndef index\(\):', content)
if m:
    print("found")
else:
    print("missing route")
