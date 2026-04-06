import requests

s = requests.Session()
r = s.get('http://127.0.0.1:5000/')
token = r.text.split('<meta name="csrf-token" content="')[1].split('"')[0]

r2 = s.post('http://127.0.0.1:5000/login', data={'username': 'admin', 'password': 'takmirmasjid', 'csrf_token': token})
r3 = s.get('http://127.0.0.1:5000/orang-tua')

print("Profil Medis Anak" in r3.text)
print("Data Personal Anak" in r3.text)
print(r3.text[:100])
