import re
with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

m = re.search(r'function toggleAudio\(type\)(.*?)^        function ', content, re.DOTALL | re.MULTILINE)
if m:
    print("ToggleAudio:", m.group(0))

m2 = re.search(r'Zikir Penenang \(EQuran\).*?</div>.*?</div>', content, re.DOTALL)
if m2:
    print("Zikir:", m2.group(0))
