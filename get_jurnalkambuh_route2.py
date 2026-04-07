import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'@app\.route\(\'/therapy/log\'.*?return redirect\(url_for\(\'index\', open=\'modal-terapi-log\'\)\)', content, re.DOTALL)
if m:
    print(m.group(0))
