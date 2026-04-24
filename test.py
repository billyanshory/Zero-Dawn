import urllib.request
import json
try:
    with urllib.request.urlopen("http://localhost:5001/api/qurban/stats") as response:
       data = response.read()
       print(data)
except Exception as e:
    print(e)
