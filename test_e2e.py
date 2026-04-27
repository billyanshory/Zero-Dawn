import os
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test_secret'

import sys
import importlib.util

spec = importlib.util.spec_from_file_location("app_module", "masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

app = app_module.app
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

with app.app_context():
    app_module.db.create_all()

client = app.test_client()
with client.session_transaction() as sess:
    sess['is_admin'] = True

print("Testing Shohibul Generate...")
resp = client.post('/idul-adha/shohibul/generate', data={
    'jenis_hewan': 'Sapi',
    'nama_shohibul': 'Test Bapak Sapi'
}, follow_redirects=True)
print(f"Status: {resp.status_code}")
with app.app_context():
    shohibul = app_module.QurbanShohibul.query.first()
    assert shohibul.pin == 'SQ-001'
    assert shohibul.nama_shohibul == 'Test Bapak Sapi'
    assert shohibul.jenis_hewan == 'Sapi'

print("Testing Shohibul Update Status...")
resp = client.post('/idul-adha/shohibul/update_status', data={
    'pin': 'SQ-001',
    'status': 'Sedang Disembelih'
}, follow_redirects=True)
print(f"Status: {resp.status_code}")
with app.app_context():
    shohibul = app_module.QurbanShohibul.query.first()
    assert shohibul.status == 'Sedang Disembelih'

print("Testing Kupon Generate...")
resp = client.post('/idul-adha/pembagian/generate', data={
    'nama_penerima': 'Bapak Kupon',
    'rt': 'RT 02',
    'waktu_pengambilan': '14:00 WITA',
    'lokasi_pengambilan': 'Rumah Pak RT'
}, follow_redirects=True)
print(f"Status: {resp.status_code}")
with app.app_context():
    kupon = app_module.QurbanKupon.query.first()
    assert kupon.nomor_kupon == 'KPN-001'
    assert kupon.nama_penerima == 'Bapak Kupon'

print("Testing Peta RT Add...")
resp = client.post('/idul-adha/peta-distribusi/add', data={
    'nomor_card': '05',
    'rt_name': 'RT 05',
    'nama_ketua_rt': 'Bapak RT',
    'alokasi': 30
}, follow_redirects=True)
print(f"Status: {resp.status_code}")
with app.app_context():
    rt = app_module.QurbanRT.query.first()
    assert rt.nomor_card == '05'
    assert rt.status == 'Menunggu'
    rt_id = rt.id

print("Testing Peta RT Update Status...")
resp = client.post('/idul-adha/peta-distribusi/update_status', data={
    'rt_id': rt_id,
    'status': 'Diserahkan'
}, follow_redirects=True)
print(f"Status: {resp.status_code}")
with app.app_context():
    rt = app_module.QurbanRT.query.first()
    assert rt.status == 'Diserahkan'

print("Testing Peta RT Edit...")
resp = client.post('/idul-adha/peta-distribusi/edit', data={
    'rt_id': rt_id,
    'nomor_card': '05',
    'rt_name': 'RT 05 Baru',
    'nama_ketua_rt': 'Bapak RT Baru',
    'alokasi': 40,
    'status': 'Menunggu'
}, follow_redirects=True)
print(f"Status: {resp.status_code}")
with app.app_context():
    rt = app_module.QurbanRT.query.first()
    assert rt.rt_name == 'RT 05 Baru'
    assert rt.status == 'Menunggu'
    assert rt.alokasi == 40

print("All tests passed.")
