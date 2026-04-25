import os
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

from importlib import import_module
app_module = import_module("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban )")

with app_module.app.app_context():
    app_module.db.create_all()
    # Test api_qurban_generate_pin custom PIN format
    with app_module.app.test_client() as client:
        with client.session_transaction() as sess:
            sess['is_admin'] = True
        resp = client.post('/api/qurban/shohibul/generate_pin', json={'name': 'Budi', 'type': 'Sapi'})
        print("PIN Generate Code:", resp.status_code)
        data = resp.json
        print("PIN Generate Data:", data)
        assert data['success'] == True
        # verify no O, 0, 1, I
        for c in data['pin']:
            assert c not in ['O', '0', '1', 'I']

        print("PIN validation passed!")
