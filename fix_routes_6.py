import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'def index\(\).*?return render_template_string\(BASE_LAYOUT', content, re.DOTALL)
if m:
    print(m.group(0))
