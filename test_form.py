import requests

s = requests.Session()
r = s.get('http://127.0.0.1:5000/')
token = r.text.split('<meta name="csrf-token" content="')[1].split('"')[0]

s.post('http://127.0.0.1:5000/login', data={'username': 'admin', 'password': 'takmirmasjid', 'csrf_token': token})
r3 = s.get('http://127.0.0.1:5000/orang-tua')

print("Lengkapi Profil Medis Anak" in r3.text)

token3 = r3.text.split('<meta name="csrf-token" content="')[1].split('"')[0]
r4 = s.post('http://127.0.0.1:5000/orang-tua/api/medical-data', data={
    'medical_history': 'history',
    'daily_habits': 'habits',
    'medication_schedules': 'meds',
    'csrf_token': token3
})

print(r4.status_code)
