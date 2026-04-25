import requests
import json

try:
    res = requests.post('http://127.0.0.1:5001/qurban/pembagian/cek', json={"nik": "Ahmad Fauzi", "coupon_number": "TESTING"})
    print("Status:", res.status_code)
    print("Headers:", res.headers)
    print("Content:", res.text)
except Exception as e:
    print(e)
