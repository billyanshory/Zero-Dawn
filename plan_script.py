import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

print("File length:", len(content))

# Look for db = SQLAlchemy(app)
idx = content.find('db = SQLAlchemy(app)')
if idx != -1:
    print("Found db = SQLAlchemy(app) at line", content.count('\n', 0, idx) + 1)

# L8-010: DALIL_DATA
idx = content.find('DALIL_DATA')
if idx != -1:
    print("Found DALIL_DATA at line", content.count('\n', 0, idx) + 1)

# L8-002: session.get('peran') not in
matches = re.finditer(r"session\.get\('peran'\) not in", content)
print("Found session.get('peran') not in:", len(list(matches)))

# L8-008 & 009: imports
matches = re.finditer(r"from flask import flash", content)
print("Found 'from flask import flash':", len(list(matches)))

# L8-003: upload_portfolio / upload_karya
idx1 = content.find('def upload_portfolio')
idx2 = content.find('def upload_karya')
print("upload_portfolio at", content.count('\n', 0, idx1) + 1)
print("upload_karya at", content.count('\n', 0, idx2) + 1)

# L8-005: api_kamus_nutrisi
idx1 = content.find('def api_kamus_nutrisi()')
idx2 = content.find('def api_kamus_nutrisi_underscore()')
print("api_kamus_nutrisi at", content.count('\n', 0, idx1) + 1)
print("api_kamus_nutrisi_underscore at", content.count('\n', 0, idx2) + 1)

# L8-007: connected_clients_dict
idx = content.find('connected_clients_dict = {}')
print("connected_clients_dict at", content.count('\n', 0, idx) + 1)

# L8-013: Siswa
idx = content.find('class Siswa(db.Model):')
print("class Siswa at", content.count('\n', 0, idx) + 1)
