import re

with open('sekolah-luar-biasa-59 ( idcloudhost - 3 Dunia untuk Papan Data Diri Siswa SLB ).py', 'r') as f:
    content = f.read()

print("EmotionJournal:")
print(re.search(r'class EmotionJournal.*?id = db\.Column.*?id\)', content, re.DOTALL | re.IGNORECASE))
print("EpilepsiLog:")
print(re.search(r'class EpilepsiLog.*?date = db\.Column', content, re.DOTALL | re.IGNORECASE))

print("tunagrahita:")
tunagrahita_match = re.search(r'SLB_TUNAGRAHITA_HTML = .*?bindDragEvents\(\).*?}', content, re.DOTALL)
if tunagrahita_match:
    print(tunagrahita_match.group(0)[:100])
else:
    print("Not found")
