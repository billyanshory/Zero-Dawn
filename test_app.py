import subprocess
import time
import requests
import sys

def check_server():
    for _ in range(30):
        try:
            r = requests.get('http://127.0.0.1:5000/health')
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

# Start server
server = subprocess.Popen([sys.executable, 'klinik-delima-dalam-47 ( IdCloudHost - Tampilan Interface UI-UX - Dashboard Admin & Dokter ).py'])
if not check_server():
    print("Server failed to start")
    server.kill()
    sys.exit(1)
print("Server started successfully")

import os
with open("server.pid", "w") as f:
    f.write(str(server.pid))
