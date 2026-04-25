import sys
import threading
import time
import requests
import os

# Fix sqlite pool size error
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
os.environ['SECRET_KEY'] = 'test_secret_key'

# remove old db
if os.path.exists('/tmp/test.db'):
    os.remove('/tmp/test.db')

def run_app():
    import app
    app.app.run(port=5001)

sys.path.append('.')
try:
    with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
        content = f.read()

    # We remove pooling args completely for sqlite to avoid exceptions
    import re
    content = re.sub(r"app\.config\['SQLALCHEMY_POOL_SIZE'\]\s*=\s*\d+", "", content)
    content = re.sub(r"app\.config\['SQLALCHEMY_MAX_OVERFLOW'\]\s*=\s*\d+", "", content)
    content = re.sub(r"app\.config\['SQLALCHEMY_POOL_TIMEOUT'\]\s*=\s*\d+", "", content)
    content = re.sub(r"app\.config\['SQLALCHEMY_POOL_RECYCLE'\]\s*=\s*\d+", "", content)

    with open("test_app.py", "w") as f:
        f.write(content)

    sys.modules['app'] = __import__('test_app')

    # Initialize DB specifically
    with sys.modules['app'].app.app_context():
        sys.modules['app'].db.create_all()

    t = threading.Thread(target=run_app)
    t.daemon = True
    t.start()

    time.sleep(3)

    # Test some routes
    try:
        res1 = requests.get('http://127.0.0.1:5001/idul-adha/absen')
        print("Absen GET:", res1.status_code)

        res2 = requests.get('http://127.0.0.1:5001/idul-adha/peta')
        print("Peta GET:", res2.status_code)

        res3 = requests.post('http://127.0.0.1:5001/qurban/pembagian/cek', json={"nik": "test", "coupon_number": "test"})
        print("Cek POST:", res3.status_code)
    except Exception as e:
        print("Error requests:", e)
except Exception as e:
    print("Error:", e)
