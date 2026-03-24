import sys
sys.path.append(".")
mod = __import__("klinik-delima-dalam-48 ( IdCloudHost - Tampilan Interface UI-UX - Tab Atas & Card Hard Digital )")

app = mod.app
app.config['SESSION_COOKIE_SECURE'] = False # For local testing

with app.test_client() as client:
    response = client.post('/login', data={'userid': 'admin', 'password': 'admin123'}, follow_redirects=True)
    print("Login Status:", response.status_code)

    response = client.get('/booking-list')
    print("Booking List Status:", response.status_code)
    if "DAFTAR PASIEN PEMESAN" in response.text:
        print("Success! UI updated.")
    else:
        print("UI not found.")
