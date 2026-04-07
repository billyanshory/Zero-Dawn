import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'function initAudio\(\) \{.*?\}', content, re.DOTALL)
if m:
    print("initAudio", m.group(0))

m2 = re.search(r'function toggleAudio\(type\) \{.*?\}', content, re.DOTALL)
if m2:
    print("toggleAudio", m2.group(0))

m3 = re.search(r'function createOscillator.*?\}', content, re.DOTALL)
if m3:
    print("createOscillator", m3.group(0))
