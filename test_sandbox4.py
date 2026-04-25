import os
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

from importlib import import_module
app_module = import_module("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban )")

with app_module.app.app_context():
    app_module.db.create_all()
    # Test qurban_pembagian_cek endpoint
    with app_module.app.test_client() as client:
        # Invalid payload
        resp = client.post('/qurban/pembagian/cek', json={'nik': '', 'coupon_number': '123'})
        print("Cek Invalid Nama Code:", resp.status_code, resp.json)
        assert resp.status_code == 400

        # valid request but no data
        resp = client.post('/qurban/pembagian/cek', json={'nik': 'Budi', 'coupon_number': '123'})
        print("Cek No Data Code:", resp.status_code, resp.json)
        assert resp.status_code == 200
        assert resp.json['found'] == False

        print("Cek validation passed!")
