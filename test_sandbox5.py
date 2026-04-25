import os
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

from importlib import import_module
app_module = import_module("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban )")

with app_module.app.app_context():
    app_module.db.create_all()
    # Test qurban_stats API
    with app_module.app.test_client() as client:
        with client.session_transaction() as sess:
            sess['is_admin'] = True
        resp = client.post('/admin/qurban/stats', json={
            'total_cattle': 10,
            'total_goat': 20,
            'total_meat_kg': 30,
            'total_packages_prepared': 40,
            'total_packages_distributed': 50
        })
        assert resp.status_code == 200
        print("Stats update successful!")
