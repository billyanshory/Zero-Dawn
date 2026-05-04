import sys
from app import app, db

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

with app.app_context():
    db.create_all()

client = app.test_client()

res = client.get('/fitur-masjid')
print(res.status_code)
if res.status_code != 200:
    print(res.data.decode('utf-8'))
