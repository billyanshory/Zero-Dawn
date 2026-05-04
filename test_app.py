import sys
from app import app, db

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

with app.app_context():
    db.create_all()

client = app.test_client()

def test_routes():
    print("Testing Home page...")
    res = client.get('/')
    assert res.status_code == 200

    print("Testing Donate page...")
    res = client.get('/donate')
    assert res.status_code == 200

    print("Testing Ramadhan page...")
    res = client.get('/ramadhan')
    assert res.status_code == 200

    print("Testing IRMA page...")
    res = client.get('/irma')
    assert res.status_code == 200

    print("Testing Idul Adha pages...")
    res = client.get('/idul-adha/absen-panitia')
    assert res.status_code == 200

    res = client.get('/idul-adha')
    assert res.status_code == 200

    res = client.get('/idul-adha/laporan')
    assert res.status_code == 200

    res = client.get('/idul-adha/shohibul')
    assert res.status_code == 200

    res = client.get('/idul-adha/peta-distribusi')
    assert res.status_code == 200

    res = client.get('/idul-adha/panduan')
    assert res.status_code == 200

    res = client.get('/idul-adha/distribution')
    assert res.status_code == 200

    print("Testing Fitur Masjid page...")
    res = client.get('/fitur-masjid')
    assert res.status_code == 200

    print("All basic routes pass.")

test_routes()
