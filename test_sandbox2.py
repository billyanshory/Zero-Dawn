import os
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

from importlib import import_module
app_module = import_module("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban )")

with app_module.app.app_context():
    app_module.db.create_all()
    # Test creation of QurbanAttendance
    att = app_module.QurbanAttendance(name="Test", status="Hadir Pagi", verified_by_admin=True)
    app_module.db.session.add(att)
    app_module.db.session.commit()
    print("Database test passed!")

    # Test API Generate Kupon format NIK -> Nama validation
    with app_module.app.test_client() as client:
        with client.session_transaction() as sess:
            sess['is_admin'] = True
        # valid nama
        resp = client.post('/api/qurban/pembagian/generate_kupon', json={'nik': 'Bapak Budi', 'slot_id': 9999})
        print("Valid nama code:", resp.status_code, resp.json) # Expected 400 with 'Slot tidak valid'

        # invalid nama (empty)
        resp2 = client.post('/api/qurban/pembagian/generate_kupon', json={'nik': '', 'slot_id': 9999})
        print("Invalid nama code:", resp2.status_code, resp2.json) # Expected 400 with 'Nama tidak valid'
