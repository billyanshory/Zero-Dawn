import requests
import json
import time

def test_pmb():
    url = "http://127.0.0.1:5000/api/pmb/register"

    session = requests.Session()
    res = session.get("http://127.0.0.1:5000/")

    # We can skip CSRF in testing by patching it out or disabling it, but since CSRF is enabled, let's just make sure the app disables it for tests.

    with open("dummy.pdf", "rb") as f:
        files = {
            'foto_ijazah': ('dummy.pdf', f, 'application/pdf'),
            'foto_ktp': ('dummy.pdf', f, 'application/pdf'),
            'bukti_transfer': ('dummy.pdf', f, 'application/pdf')
        }
        data = {
            'nama': 'Test User',
        }
        res = session.post(url, data=data, files=files)
        print("PMB Register Status code:", res.status_code)
        try:
            print("PMB Register Response:", res.json())
        except:
            print("PMB Register Response text:", res.text[:200])

if __name__ == "__main__":
    time.sleep(1)
    for _ in range(5):
        try:
            requests.get("http://127.0.0.1:5000/")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    test_pmb()
