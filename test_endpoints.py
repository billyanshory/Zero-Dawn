import threading
import time
import requests
import os
import sqlite3

# Set environment variable to force in-memory DB for testing
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret'

from app import app, db

def run_app():
    with app.app_context():
        db.create_all()
    app.run(port=5000, use_reloader=False)

thread = threading.Thread(target=run_app)
thread.daemon = True
thread.start()

time.sleep(2) # wait for server to start

try:
    urls = [
        "/idul-adha/laporan",
        "/api/qurban/stats",
        "/qurban/lacak",
        "/qurban/pembagian/cek",
        "/idul-adha/panduan",
        "/admin/qurban/peta", # should 302 redirect to / without login
        "/admin/qurban/hewan", # should 302 redirect
    ]
    for url in urls:
        r = requests.get("http://localhost:5000" + url, allow_redirects=False)
        print(f"GET {url}: Status {r.status_code}")
except Exception as e:
    print(f"Error during testing: {e}")
